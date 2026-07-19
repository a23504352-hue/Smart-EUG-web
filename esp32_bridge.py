"""
ESP32 Bridge for malaika_v2
=============================
Auto-detects ESP32 on any COM port. Provides:
  - WebSocket /ws/live -> live samples to browser
  - REST endpoints for start/stop/status/quality/contact
  - Auto-saves recordings as .mat + .txt + .csv

Runs as a background thread inside api.py - no separate process.
"""
from __future__ import annotations

import asyncio
import csv
import json
import logging
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

import numpy as np
import serial
import serial.tools.list_ports
from scipy.io import savemat

log = logging.getLogger("esp32_bridge")

ROOT = Path(__file__).parent
RECORDINGS_DIR = ROOT / "recordings"
RECORDINGS_DIR.mkdir(parents=True, exist_ok=True)

# ESP32 ADC: 12-bit (0-4095) over 0-3.3V. EUG PCB has gain ~100x,
# so ADC 1mV diff = ~10 uV at electrode. We store raw uV scale.
ADC_MAX = 4095
ADC_VREF = 3.3
AMP_GAIN = 100.0  # adjust if PCB gain differs


def adc_to_uv(raw: int) -> float:
    """Convert raw 12-bit ADC reading to uV at electrode."""
    volts = (raw / ADC_MAX) * ADC_VREF
    centered = volts - (ADC_VREF / 2.0)
    uv_at_electrode = (centered / AMP_GAIN) * 1_000_000.0
    return uv_at_electrode


@dataclass
class BridgeState:
    connected: bool = False
    port: Optional[str] = None
    fw_version: Optional[str] = None
    chip: Optional[str] = None
    streaming: bool = False
    samples_received: int = 0
    last_sample_ms: int = 0
    quality: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0])
    contact_ok: List[bool] = field(default_factory=lambda: [True, True, True])
    last_error: Optional[str] = None
    # current recording buffer
    rec_t: List[int] = field(default_factory=list)
    rec_ch1: List[float] = field(default_factory=list)
    rec_ch2: List[float] = field(default_factory=list)
    rec_ch3: List[float] = field(default_factory=list)
    rec_started_at: Optional[float] = None
    last_filename: Optional[str] = None


class ESP32Bridge:
    """Manages serial connection + reading thread + websocket subscribers."""
    def __init__(self):
        self.state = BridgeState()
        self.serial: Optional[serial.Serial] = None
        self._read_thread: Optional[threading.Thread] = None
        self._stop_thread = False
        self._lock = threading.Lock()
        self._ws_subscribers: List[asyncio.Queue] = []
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    # ===================================================================
    # AUTO-DETECT
    # ===================================================================
    def auto_detect(self) -> Optional[str]:
        """Scan all COM ports, return first one that responds with PONG."""
        for port_info in serial.tools.list_ports.comports():
            port = port_info.device
            # CP2102 / CH340 / Silicon Labs are typical ESP32 USB-UART chips
            description = (port_info.description or "").lower()
            hwid = (port_info.hwid or "").lower()
            likely_esp = any(s in description + hwid for s in
                             ["cp210", "ch340", "ch9102", "silicon labs",
                              "wch", "ftdi", "esp32"])
            try:
                ser = serial.Serial(port, 115200, timeout=2)
                time.sleep(2.0)  # ESP32 boot
                ser.reset_input_buffer()
                ser.write(b"PING\n")
                ser.flush()
                start = time.time()
                while time.time() - start < 3.0:
                    line = ser.readline().decode("utf-8", errors="ignore").strip()
                    if line.startswith("PONG"):
                        log.info(f"Found ESP32 on {port}: {line}")
                        # Parse fw + chip
                        fw = chip = None
                        for tok in line.split():
                            if tok.startswith("fw="): fw = tok[3:]
                            if tok.startswith("chip="): chip = tok[5:]
                        ser.close()
                        with self._lock:
                            self.state.fw_version = fw
                            self.state.chip = chip
                        return port
                ser.close()
            except Exception as e:
                log.debug(f"Port {port} skipped: {e}")
                continue
        return None

    # ===================================================================
    # CONNECT / DISCONNECT
    # ===================================================================
    def connect(self, port: Optional[str] = None) -> bool:
        if not port:
            port = self.auto_detect()
        if not port:
            with self._lock:
                self.state.last_error = "No ESP32 found on any COM port"
            return False
        try:
            self.serial = serial.Serial(port, 115200, timeout=0.5)
            time.sleep(0.5)
            with self._lock:
                self.state.connected = True
                self.state.port = port
                self.state.last_error = None
            self._stop_thread = False
            self._read_thread = threading.Thread(target=self._reader_loop, daemon=True)
            self._read_thread.start()
            log.info(f"Bridge connected on {port}")
            return True
        except Exception as e:
            with self._lock:
                self.state.last_error = str(e)
                self.state.connected = False
            return False

    def disconnect(self):
        self._stop_thread = True
        if self.serial:
            try: self.serial.close()
            except Exception: pass
            self.serial = None
        with self._lock:
            self.state.connected = False
            self.state.streaming = False

    # ===================================================================
    # COMMANDS
    # ===================================================================
    def _send(self, cmd: str):
        if not self.serial: return
        try:
            self.serial.write((cmd + "\n").encode("ascii"))
            self.serial.flush()
        except Exception as e:
            log.error(f"Write failed: {e}")

    def start_recording(self) -> bool:
        if not self.state.connected: return False
        with self._lock:
            self.state.streaming = True
            self.state.samples_received = 0
            self.state.rec_t.clear()
            self.state.rec_ch1.clear()
            self.state.rec_ch2.clear()
            self.state.rec_ch3.clear()
            self.state.rec_started_at = time.time()
        self._send("START")
        return True

    def stop_recording(self) -> Optional[Path]:
        """Stop and auto-save recording in 3 formats."""
        if not self.state.streaming: return None
        self._send("STOP")
        time.sleep(0.3)
        with self._lock:
            self.state.streaming = False
            n = len(self.state.rec_t)
        if n < 20:
            log.warning(f"Recording too short ({n} samples), not saving")
            return None
        return self._save_recording()

    def _save_recording(self) -> Optional[Path]:
        with self._lock:
            t = np.array(self.state.rec_t, dtype=np.float64) / 1000.0  # ms -> s
            ch1 = np.array(self.state.rec_ch1, dtype=np.float64)
            ch2 = np.array(self.state.rec_ch2, dtype=np.float64)
            ch3 = np.array(self.state.rec_ch3, dtype=np.float64)

        timestamp = time.strftime("%Y%m%d_%H%M%S")
        base = RECORDINGS_DIR / f"REC_{timestamp}_3channel"

        # 1. .mat (for AI model + matlab compatibility)
        # data shape: (N, 3) in mV (model expects mV for downstream conversion)
        data_mv = np.column_stack([ch1, ch2, ch3]) / 1000.0  # uV -> mV
        savemat(str(base) + ".mat", {"data": data_mv})

        # 2. .csv (for Excel / sharing)
        with open(str(base) + ".csv", "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["time_s", "ch1_uv", "ch2_uv", "ch3_uv"])
            for i in range(len(t)):
                w.writerow([round(t[i], 4), round(ch1[i], 2),
                            round(ch2[i], 2), round(ch3[i], 2)])

        # 3. .txt (BIOPAC-style for legacy tools)
        with open(str(base) + ".txt", "w", encoding="utf-8") as f:
            f.write("EUG_v2 ESP32 Recording\n")
            f.write("0.5 msec/sample\n")
            f.write("3 channels\n")
            f.write("EUG (.1 - 3 Hz)\n")
            f.write("uV\n")
            f.write("EUG (.1 - 3 Hz)\n")
            f.write("uV\n")
            f.write("EUG (.1 - 3 Hz)\n")
            f.write("uV\n")
            f.write("min\tCH1\tCH2\tCH3\t\n")
            f.write(f"\t{len(t)}\t{len(t)}\t{len(t)}\t\n")
            for i in range(len(t)):
                tm = t[i] / 60.0
                f.write(f"{tm:.4f}\t{ch1[i]/1000:.7f}\t"
                        f"{ch2[i]/1000:.7f}\t{ch3[i]/1000:.7f}\t\n")

        with self._lock:
            self.state.last_filename = base.name + ".mat"

        log.info(f"Saved recording: {base.name}.{{mat,csv,txt}} ({len(t)} samples)")
        return Path(str(base) + ".mat")

    # ===================================================================
    # WEBSOCKET SUBSCRIBERS
    # ===================================================================
    def subscribe(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue(maxsize=100)
        self._ws_subscribers.append(q)
        return q

    def unsubscribe(self, q: asyncio.Queue):
        if q in self._ws_subscribers:
            self._ws_subscribers.remove(q)

    def set_loop(self, loop):
        self._loop = loop

    def _push_to_ws(self, msg: dict):
        if not self._loop or not self._ws_subscribers:
            return
        for q in list(self._ws_subscribers):
            try:
                self._loop.call_soon_threadsafe(q.put_nowait, msg)
            except Exception:
                pass

    # ===================================================================
    # READER THREAD
    # ===================================================================
    def _reader_loop(self):
        last_ws_push = 0.0
        ws_buffer = {"t": [], "ch1": [], "ch2": [], "ch3": []}
        last_quality_request = 0
        last_contact_request = 0

        while not self._stop_thread:
            try:
                if not self.serial: break
                line = self.serial.readline().decode("utf-8", errors="ignore").strip()
                if not line:
                    # Periodic quality / contact polls during streaming
                    now = time.time()
                    if self.state.streaming:
                        if now - last_quality_request > 1.0:
                            self._send("QUALITY")
                            last_quality_request = now
                        if now - last_contact_request > 2.0:
                            self._send("CONTACT")
                            last_contact_request = now
                    continue

                if line.startswith("# STREAM_START"):
                    self._push_to_ws({"type": "started"})
                    continue
                if line.startswith("# STREAM_STOP"):
                    self._push_to_ws({"type": "stopped"})
                    continue
                if line.startswith("# AUTO_STOP"):
                    self._push_to_ws({"type": "auto_stopped"})
                    with self._lock:
                        self.state.streaming = False
                    continue
                if line.startswith("PONG"):
                    continue
                if line.startswith("STATUS"):
                    continue
                if line.startswith("QUALITY"):
                    parts = line.split()
                    q = [0.0, 0.0, 0.0]
                    for p in parts[1:]:
                        if p.startswith("ch1="): q[0] = float(p[4:])
                        if p.startswith("ch2="): q[1] = float(p[4:])
                        if p.startswith("ch3="): q[2] = float(p[4:])
                    with self._lock:
                        self.state.quality = q
                    self._push_to_ws({"type": "quality", "values": q})
                    continue
                if line.startswith("CONTACT"):
                    parts = line.split()
                    c = [True, True, True]
                    for p in parts[1:]:
                        if p.startswith("ch1="): c[0] = (p[4:] == "OK")
                        if p.startswith("ch2="): c[1] = (p[4:] == "OK")
                        if p.startswith("ch3="): c[2] = (p[4:] == "OK")
                    with self._lock:
                        self.state.contact_ok = c
                    self._push_to_ws({"type": "contact", "values": c})
                    continue

                if line.startswith("#") or line.startswith("BOOT"):
                    continue

                # CSV sample
                parts = line.split(",")
                if len(parts) != 4:
                    continue
                try:
                    t_ms = int(parts[0])
                    raw1 = int(parts[1])
                    raw2 = int(parts[2])
                    raw3 = int(parts[3])
                except ValueError:
                    continue

                ch1_uv = adc_to_uv(raw1)
                ch2_uv = adc_to_uv(raw2)
                ch3_uv = adc_to_uv(raw3)

                with self._lock:
                    self.state.rec_t.append(t_ms)
                    self.state.rec_ch1.append(ch1_uv)
                    self.state.rec_ch2.append(ch2_uv)
                    self.state.rec_ch3.append(ch3_uv)
                    self.state.samples_received += 1
                    self.state.last_sample_ms = t_ms

                # Buffer samples for WebSocket batches (50 ms = 100 samples at 2 kHz)
                ws_buffer["t"].append(t_ms)
                ws_buffer["ch1"].append(round(ch1_uv, 1))
                ws_buffer["ch2"].append(round(ch2_uv, 1))
                ws_buffer["ch3"].append(round(ch3_uv, 1))

                if (time.time() - last_ws_push) > 0.05 and ws_buffer["t"]:
                    self._push_to_ws({"type": "samples", **ws_buffer})
                    ws_buffer = {"t": [], "ch1": [], "ch2": [], "ch3": []}
                    last_ws_push = time.time()

            except Exception as e:
                log.warning(f"Reader loop hiccup: {e}")
                time.sleep(0.1)

    # ===================================================================
    # PUBLIC SNAPSHOT
    # ===================================================================
    def snapshot(self) -> dict:
        with self._lock:
            return {
                "connected": self.state.connected,
                "port": self.state.port,
                "fw": self.state.fw_version,
                "chip": self.state.chip,
                "streaming": self.state.streaming,
                "samples": self.state.samples_received,
                "last_sample_ms": self.state.last_sample_ms,
                "quality": self.state.quality,
                "contact_ok": self.state.contact_ok,
                "last_filename": self.state.last_filename,
                "last_error": self.state.last_error,
                "duration_sec": (
                    (time.time() - self.state.rec_started_at)
                    if self.state.streaming and self.state.rec_started_at else 0
                ),
            }


# Singleton
bridge = ESP32Bridge()

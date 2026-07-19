"""
Demo replay - fakes the ESP32 bridge by replaying a saved .mat file
as if it were a live stream. Used for video demos when no hardware.

Same WebSocket interface as the real bridge, so the website doesn't
know the difference.
"""
from __future__ import annotations
import asyncio
import logging
import threading
import time
from pathlib import Path
from typing import List, Optional

import numpy as np
from scipy.io import loadmat

log = logging.getLogger("demo_replay")
ROOT = Path(__file__).parent
RECORDINGS_DIR = ROOT / "recordings"


class DemoReplayBridge:
    """Drop-in replacement for ESP32Bridge that replays a saved .mat file."""

    def __init__(self):
        self.connected = False
        self.streaming = False
        self.demo_mode = True
        self.port = "DEMO"
        self.fw_version = "DEMO-FW v2.0"
        self.chip = "Demo-Replay"
        self.current_file: Optional[Path] = None
        self.samples_received = 0
        self.last_sample_ms = 0
        self.quality = [85.0, 88.0, 82.0]
        self.contact_ok = [True, True, True]
        self.last_filename: Optional[str] = None
        self.last_error: Optional[str] = None

        # Replay state
        self._stop = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self._ws_subscribers: List[asyncio.Queue] = []
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._rec_buffer = {"t": [], "ch1": [], "ch2": [], "ch3": []}
        self.rec_started_at: Optional[float] = None

    # === Auto-detect ===
    def auto_detect(self) -> Optional[str]:
        """In demo mode, always 'find' a fake ESP32."""
        return "DEMO"

    def connect(self, port=None) -> bool:
        # Pick first .mat file from recordings
        files = sorted(RECORDINGS_DIR.glob("*.mat"))
        if not files:
            self.last_error = "No demo recordings in recordings/ folder"
            return False
        # Prefer 'period_demo' for an interesting demo
        preferred = [f for f in files if "period_demo" in f.name.lower()]
        self.current_file = preferred[0] if preferred else files[0]
        self.connected = True
        log.info(f"Demo bridge connected. Will replay: {self.current_file.name}")
        return True

    def disconnect(self):
        self._stop = True
        self.connected = False
        self.streaming = False

    # === WebSocket subscribers ===
    def subscribe(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue(maxsize=200)
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

    # === Recording control ===
    def start_recording(self) -> bool:
        if not self.connected: self.connect()
        if not self.current_file or not self.current_file.exists():
            return False
        with self._lock:
            self.streaming = True
            self.samples_received = 0
            self.rec_started_at = time.time()
            self._rec_buffer = {"t": [], "ch1": [], "ch2": [], "ch3": []}
        self._stop = False
        self._thread = threading.Thread(target=self._replay_loop, daemon=True)
        self._thread.start()
        self._push_to_ws({"type": "started"})
        return True

    def stop_recording(self) -> Optional[Path]:
        if not self.streaming:
            return None
        self._stop = True
        time.sleep(0.2)
        with self._lock:
            self.streaming = False
        # Save the buffer as a normal recording so the analyze step works.
        return self._save_recording()

    def _save_recording(self) -> Optional[Path]:
        from scipy.io import savemat
        import csv
        with self._lock:
            t = np.array(self._rec_buffer["t"], dtype=np.float64) / 1000.0
            ch1 = np.array(self._rec_buffer["ch1"], dtype=np.float64)
            ch2 = np.array(self._rec_buffer["ch2"], dtype=np.float64)
            ch3 = np.array(self._rec_buffer["ch3"], dtype=np.float64)

        if len(t) < 20:
            # If too short, just return the SOURCE file - still produces a valid analysis
            self.last_filename = self.current_file.name
            return self.current_file

        ts = time.strftime("%Y%m%d_%H%M%S")
        base = RECORDINGS_DIR / f"REC_{ts}_demo_3channel"

        data_mv = np.column_stack([ch1, ch2, ch3]) / 1000.0
        savemat(str(base) + ".mat", {"data": data_mv})

        with open(str(base) + ".csv", "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["time_s", "ch1_uv", "ch2_uv", "ch3_uv"])
            for i in range(len(t)):
                w.writerow([round(t[i], 4), round(ch1[i], 2),
                            round(ch2[i], 2), round(ch3[i], 2)])

        self.last_filename = base.name + ".mat"
        log.info(f"Saved demo recording: {self.last_filename} ({len(t)} samples)")
        return Path(str(base) + ".mat")

    # === The replay engine ===
    def _replay_loop(self):
        """Read the .mat file and stream samples at realistic rate."""
        try:
            m = loadmat(self.current_file, squeeze_me=True)
            arr = m.get("data")
            if arr is None:
                # find largest 2D array
                cands = [(k, np.asarray(v)) for k, v in m.items()
                         if not k.startswith("__") and np.asarray(v).ndim == 2]
                arr = max(cands, key=lambda kv: max(kv[1].shape))[1]
            arr = np.asarray(arr, dtype=float)
            if arr.shape[0] < arr.shape[1]:
                arr = arr.T
            # arr is (N, 3) in mV. Convert to uV for streaming.
            arr_uv = arr * 1000.0
            n_total = arr_uv.shape[0]
            log.info(f"Replaying {n_total} samples from {self.current_file.name}")
        except Exception as e:
            log.error(f"Replay load failed: {e}")
            self.last_error = str(e)
            return

        # Replay rate: send a chunk every ~50 ms (matches real bridge cadence)
        # The .mat is sampled at 2 kHz, so 50ms = 100 samples per chunk
        chunk_size = 100
        chunk_period = 0.05  # 50 ms
        idx = 0
        t_start_ms = 0
        last_quality_push = time.time()
        last_contact_push = time.time()

        while not self._stop and idx < n_total:
            chunk_end = min(idx + chunk_size, n_total)
            chunk_t = []
            chunk_c1, chunk_c2, chunk_c3 = [], [], []
            for i in range(idx, chunk_end):
                t_ms = t_start_ms + int((i - 0) * 0.5)  # 0.5 ms per sample at 2kHz
                v1 = float(arr_uv[i, 0])
                v2 = float(arr_uv[i, 1])
                v3 = float(arr_uv[i, 2]) if arr_uv.shape[1] >= 3 else 0.0
                chunk_t.append(t_ms)
                chunk_c1.append(round(v1, 1))
                chunk_c2.append(round(v2, 1))
                chunk_c3.append(round(v3, 1))

                with self._lock:
                    self._rec_buffer["t"].append(t_ms)
                    self._rec_buffer["ch1"].append(v1)
                    self._rec_buffer["ch2"].append(v2)
                    self._rec_buffer["ch3"].append(v3)
                    self.samples_received += 1
                    self.last_sample_ms = t_ms

            # Push to WebSocket
            self._push_to_ws({
                "type": "samples",
                "t": chunk_t,
                "ch1": chunk_c1,
                "ch2": chunk_c2,
                "ch3": chunk_c3,
            })

            # Periodic quality + contact updates (look real)
            now = time.time()
            if now - last_quality_push > 1.0:
                # Slightly varying quality for realism
                q = [80 + np.random.uniform(-5, 8), 82 + np.random.uniform(-5, 8),
                     78 + np.random.uniform(-5, 8)]
                self.quality = q
                self._push_to_ws({"type": "quality", "values": q})
                last_quality_push = now
            if now - last_contact_push > 2.0:
                self._push_to_ws({"type": "contact", "values": self.contact_ok})
                last_contact_push = now

            idx = chunk_end
            time.sleep(chunk_period)

        # End of file - notify
        if idx >= n_total:
            self._push_to_ws({"type": "samples_end", "n": self.samples_received})

    # === Snapshot ===
    def snapshot(self) -> dict:
        with self._lock:
            return {
                "connected": self.connected,
                "port": self.port,
                "fw": self.fw_version,
                "chip": self.chip,
                "streaming": self.streaming,
                "samples": self.samples_received,
                "last_sample_ms": self.last_sample_ms,
                "quality": self.quality,
                "contact_ok": self.contact_ok,
                "last_filename": self.last_filename,
                "last_error": self.last_error,
                "demo_mode": True,
                "demo_file": self.current_file.name if self.current_file else None,
                "duration_sec": (
                    (time.time() - self.rec_started_at) if self.streaming and self.rec_started_at else 0
                ),
            }


# Singleton
demo_bridge = DemoReplayBridge()

"""
malaika_v2 main FastAPI server.

Endpoints:
  GET  /                  -> home
  GET  /<page>            -> all HTML pages (live, dashboard, chat, ...)
  GET  /api/esp32/status  -> bridge state
  POST /api/esp32/connect -> auto-detect & connect
  POST /api/esp32/start   -> start recording
  POST /api/esp32/stop    -> stop and analyze
  GET  /api/esp32/recordings -> list saved recordings
  GET  /api/analyze/{name} -> reanalyze saved file
  POST /api/chat          -> AI chat
  WS   /ws/live           -> live samples streaming
"""
from __future__ import annotations
import asyncio
import json
import logging
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import List, Optional

import numpy as np
from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import esp32_bridge
import ai_brain
import feature_engine

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("api")

ROOT = Path(__file__).parent
TEMPLATES = ROOT / "templates"
STATIC = ROOT / "static"
RECORDINGS = ROOT / "recordings"
DB = ROOT / "db"
DB.mkdir(exist_ok=True)

app = FastAPI(title="malaika v2")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])
app.mount("/static", StaticFiles(directory=str(STATIC)), name="static")


def page(name: str) -> HTMLResponse:
    fp = TEMPLATES / name
    if not fp.exists():
        raise HTTPException(404, detail=f"Page not found: {name}")
    return HTMLResponse(content=fp.read_text(encoding="utf-8"))


# -------------------- PAGES --------------------
@app.get("/", response_class=HTMLResponse)
async def home(): return page("index.html")

@app.get("/live", response_class=HTMLResponse)
async def live(): return page("live.html")

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(): return page("dashboard.html")

@app.get("/result", response_class=HTMLResponse)
async def result(): return page("result.html")

@app.get("/chat", response_class=HTMLResponse)
async def chat(): return page("chat.html")

@app.get("/anatomy", response_class=HTMLResponse)
async def anatomy(): return page("anatomy.html")

@app.get("/wellness", response_class=HTMLResponse)
async def wellness(): return page("wellness.html")

@app.get("/diary", response_class=HTMLResponse)
async def diary(): return page("diary.html")

@app.get("/calendar_view", response_class=HTMLResponse)
async def calendar_view(): return page("calendar.html")

@app.get("/history", response_class=HTMLResponse)
async def history(): return page("history.html")

@app.get("/results", response_class=HTMLResponse)
async def results_page(): return page("results.html")

@app.get("/science", response_class=HTMLResponse)
async def science(): return page("science.html")

@app.get("/about", response_class=HTMLResponse)
async def about(): return page("about.html")

@app.get("/onboarding", response_class=HTMLResponse)
async def onboarding(): return page("onboarding.html")


# -------------------- ESP32 BRIDGE API --------------------
@app.get("/api/esp32/status")
async def esp32_status():
    return esp32_bridge.bridge.snapshot()


@app.post("/api/esp32/connect")
async def esp32_connect():
    if esp32_bridge.bridge.state.connected:
        return {"ok": True, "already": True, "state": esp32_bridge.bridge.snapshot()}
    ok = esp32_bridge.bridge.connect()
    return {"ok": ok, "state": esp32_bridge.bridge.snapshot()}


@app.post("/api/esp32/disconnect")
async def esp32_disconnect():
    esp32_bridge.bridge.disconnect()
    return {"ok": True}


@app.post("/api/esp32/start")
async def esp32_start():
    if not esp32_bridge.bridge.state.connected:
        esp32_bridge.bridge.connect()
    if not esp32_bridge.bridge.state.connected:
        raise HTTPException(503, detail="ESP32 not connected")
    ok = esp32_bridge.bridge.start_recording()
    return {"ok": ok}


@app.post("/api/esp32/stop")
async def esp32_stop():
    saved_path = esp32_bridge.bridge.stop_recording()
    if not saved_path:
        return {"ok": False, "reason": "Recording too short or not active"}
    # Auto-analyze
    try:
        analysis = analyze_file(saved_path)
        analysis["filename"] = saved_path.name
        save_history(analysis, saved_path.name)
        return {"ok": True, "filename": saved_path.name, "analysis": analysis}
    except Exception as e:
        log.exception("Auto-analyze failed")
        return {"ok": True, "filename": saved_path.name,
                "analysis_error": str(e)}


@app.get("/api/esp32/recordings")
async def list_recordings():
    files = []
    for f in sorted(RECORDINGS.glob("*.mat"), key=lambda x: x.stat().st_mtime, reverse=True):
        files.append({
            "name": f.name,
            "size_kb": round(f.stat().st_size / 1024, 1),
            "mtime": f.stat().st_mtime,
        })
    return {"files": files}


@app.get("/api/analyze/{filename}")
async def analyze_recording(filename: str):
    fp = RECORDINGS / filename
    if not fp.exists():
        raise HTTPException(404, detail=f"Not found: {filename}")
    try:
        result = analyze_file(fp)
        result["filename"] = filename
        save_history(result, filename)
        return result
    except Exception as e:
        log.exception("Analyze failed")
        raise HTTPException(500, detail=str(e))


def analyze_file(path: Path) -> dict:
    """Full pipeline on a saved recording file."""
    eug = feature_engine.load_recording(path)
    if len(eug) < 2:
        raise ValueError("Need at least 2 EUG channels")
    fs = feature_engine.FS

    # Filter
    eug_filtered = {}
    for ch, sig in eug.items():
        x = feature_engine.notch_filter(sig, fs)
        x = feature_engine.bandpass(x, fs)
        eug_filtered[ch] = x

    # Envelope
    envelopes_uv = {}
    eug_clean_mat = []
    chan_keys = list(eug_filtered.keys())
    for ch in chan_keys:
        env = feature_engine.rms_envelope(eug_filtered[ch], fs)
        envelopes_uv[ch] = env * 1000.0
        eug_clean_mat.append(eug_filtered[ch])
    eug_clean_mat = np.array(eug_clean_mat).T  # (N, channels)

    # Detect contractions
    contractions = feature_engine.detect_contractions(envelopes_uv, fs=fs)

    # Extract 14 features per contraction
    features = feature_engine.extract_features(eug_clean_mat, envelopes_uv, contractions,
                                               hr_during=70.0, hr_rise=0.0, fs=fs)
    # Predict
    features = feature_engine.predict(features)

    # Per-feature phase analysis
    per_feature = feature_engine.per_feature_phase_analysis(features)

    # Verdict
    verdict_data = feature_engine.overall_verdict(features, per_feature)

    # Quality
    duration_min = eug_clean_mat.shape[0] / fs / 60.0
    scorecard = feature_engine.quality_scorecard(features, duration_min, verdict_data["mean_p"])

    # AI explanations
    patient_explanation = feature_engine.ai_explanation(verdict_data, features, per_feature, view="patient")
    doctor_explanation = feature_engine.ai_explanation(verdict_data, features, per_feature, view="doctor")

    # Build downsampled signal payload for plots
    n = eug_clean_mat.shape[0]
    step = max(1, n // 3000)
    idx = np.arange(0, n, step)
    t = (idx / fs).tolist()
    signal_payload = {
        "fs": fs, "duration_sec": n / fs,
        "time": [round(x, 3) for x in t],
        "channels": {ch: [round(float(eug_filtered[ch][i]), 5) for i in idx] for ch in chan_keys},
        "rms_envelopes": {ch: [round(float(envelopes_uv[ch][i] / 1000.0), 5) for i in idx] for ch in chan_keys},
        "contractions": [{
            "start_sec": round(s / fs, 2),
            "end_sec": round(e / fs, 2),
            "index": i + 1,
            "period_probability": features[i].get("period_probability", 0),
            "prediction": features[i].get("prediction", "?"),
        } for i, (s, e) in enumerate(contractions)],
    }

    return {
        "verdict": verdict_data["verdict"],
        "verdict_reason": verdict_data["reason"],
        "mean_period_probability": verdict_data["mean_p"],
        "n_period": verdict_data["n_period"],
        "n_total": verdict_data["n_total"],
        "most_likely_phase": verdict_data.get("most_likely_phase"),
        "phase_votes": verdict_data.get("phase_votes", {}),
        "duration_min": round(duration_min, 2),
        "patient_explanation": patient_explanation,
        "doctor_explanation": doctor_explanation,
        "per_feature_analysis": per_feature,
        "contractions": features,
        "signal": signal_payload,
        "scorecard": scorecard,
    }


def save_history(analysis: dict, filename: str):
    h_path = DB / "history.jsonl"
    rec = {
        "ts": datetime.now().isoformat(),
        "filename": filename,
        "verdict": analysis.get("verdict"),
        "mean_period_probability": analysis.get("mean_period_probability"),
        "n_total": analysis.get("n_total"),
        "duration_min": analysis.get("duration_min"),
        "scorecard_score": analysis.get("scorecard", {}).get("score"),
        "most_likely_phase": analysis.get("most_likely_phase"),
    }
    with h_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")


@app.get("/api/history")
async def api_history():
    h_path = DB / "history.jsonl"
    if not h_path.exists(): return {"records": []}
    records = []
    for line in h_path.read_text(encoding="utf-8").splitlines():
        try:
            records.append(json.loads(line))
        except Exception:
            pass
    return {"records": list(reversed(records[-50:]))}


# -------------------- AI CHAT --------------------
class ChatMsg(BaseModel):
    message: str
    history: List[dict] = []


@app.post("/api/chat")
async def chat_endpoint(req: ChatMsg):
    return ai_brain.chat(req.message, req.history)


@app.get("/api/chat/status")
async def chat_status():
    return {"ollama_available": ai_brain.is_ollama_available(),
            "fallback_ready": True}


# -------------------- MODEL INFO --------------------
@app.get("/api/model_info")
async def model_info():
    bundle = feature_engine.MODEL_BUNDLE
    feat_imp = []
    if bundle is not None and "importances" in bundle:
        names = bundle.get("feature_names", [])
        imps = list(bundle["importances"])
        feat_imp = [{"feature": n, "importance": round(float(i), 4)}
                    for n, i in sorted(zip(names, imps), key=lambda x: -x[1])]
    return {
        "metrics": feature_engine.METRICS,
        "model_type": bundle.get("model_type") if bundle else None,
        "version": bundle.get("version") if bundle else None,
        "n_features": len(feature_engine.FEATURE_NAMES_MODEL),
        "feature_importance": feat_imp,
        "thresholds": feature_engine.THRESHOLDS,
    }


@app.get("/api/training_image/{name}")
async def training_image(name: str):
    allowed = {"roc_curve.png", "feature_importance.png", "confusion_matrix.png"}
    if name not in allowed:
        raise HTTPException(404)
    fp = ROOT / "model" / name
    if not fp.exists():
        raise HTTPException(404)
    return FileResponse(fp)


# -------------------- CALENDAR --------------------
@app.get("/api/cycle_phase")
async def cycle_phase(last_period_date: str):
    try:
        lp = datetime.fromisoformat(last_period_date).date()
    except Exception:
        raise HTTPException(400, detail="Invalid date")
    today = date.today()
    cd = (today - lp).days % 28 + 1
    if 1 <= cd <= 5: phase = "MENSTRUAL"
    elif 6 <= cd <= 13: phase = "FOLLICULAR"
    elif cd == 14: phase = "OVULATION"
    else: phase = "LUTEAL"
    return {"cycle_day": cd, "phase": phase}


@app.get("/api/calendar")
async def calendar(last_period_date: str, weeks: int = 12):
    try:
        lp = datetime.fromisoformat(last_period_date).date()
    except Exception:
        raise HTTPException(400, detail="Invalid date")
    today = date.today()
    days = []
    start = today - timedelta(days=weeks * 7 // 2)
    for i in range(weeks * 7):
        d = start + timedelta(days=i)
        cd = (d - lp).days % 28 + 1
        if 1 <= cd <= 5: ph = "MENSTRUAL"
        elif 6 <= cd <= 13: ph = "FOLLICULAR"
        elif cd == 14: ph = "OVULATION"
        else: ph = "LUTEAL"
        days.append({"date": d.isoformat(), "cycle_day": cd, "phase": ph,
                     "is_today": d == today})
    return {"days": days}


# -------------------- WEBSOCKET LIVE STREAM --------------------
@app.websocket("/ws/live")
async def ws_live(ws: WebSocket):
    await ws.accept()
    queue = esp32_bridge.bridge.subscribe()
    esp32_bridge.bridge.set_loop(asyncio.get_running_loop())
    try:
        # send hello
        await ws.send_json({"type": "hello", "state": esp32_bridge.bridge.snapshot()})
        while True:
            msg = await asyncio.wait_for(queue.get(), timeout=30.0)
            await ws.send_json(msg)
    except (WebSocketDisconnect, asyncio.TimeoutError):
        pass
    except Exception as e:
        log.error(f"WS error: {e}")
    finally:
        esp32_bridge.bridge.unsubscribe(queue)


# -------------------- STARTUP --------------------
@app.on_event("startup")
async def startup_event():
    esp32_bridge.bridge.set_loop(asyncio.get_running_loop())
    # Auto-detect ESP32 in background (non-blocking)
    def _try_connect():
        try:
            esp32_bridge.bridge.connect()
        except Exception as e:
            log.info(f"ESP32 not found at startup: {e}")
    import threading
    threading.Thread(target=_try_connect, daemon=True).start()
    log.info("Startup: bridge auto-detect in background")


@app.on_event("shutdown")
async def shutdown_event():
    esp32_bridge.bridge.disconnect()




# =============================================================
# DEMO MODE + UPLOAD + EXTRA DASHBOARDS
# =============================================================
import demo_replay

DEMO_MODE = {"on": False}


@app.get("/upload", response_class=HTMLResponse)
async def upload_page(): return page("upload.html")

@app.get("/insights", response_class=HTMLResponse)
async def insights_page(): return page("insights.html")

@app.get("/comparison", response_class=HTMLResponse)
async def comparison_page(): return page("comparison.html")


@app.post("/api/demo/start")
async def demo_start():
    """Start a fake live recording from a saved .mat file."""
    DEMO_MODE["on"] = True
    demo_replay.demo_bridge.set_loop(asyncio.get_running_loop())
    if not demo_replay.demo_bridge.connected:
        demo_replay.demo_bridge.connect()
    ok = demo_replay.demo_bridge.start_recording()
    return {"ok": ok, "demo": True, "state": demo_replay.demo_bridge.snapshot()}


@app.post("/api/demo/stop")
async def demo_stop():
    """Stop fake live recording and analyze."""
    saved = demo_replay.demo_bridge.stop_recording()
    DEMO_MODE["on"] = False
    if not saved:
        return {"ok": False, "reason": "Demo recording too short"}
    try:
        analysis = analyze_file(saved)
        analysis["filename"] = saved.name
        save_history(analysis, saved.name)
        return {"ok": True, "filename": saved.name, "analysis": analysis,
                "demo": True}
    except Exception as e:
        return {"ok": True, "filename": saved.name, "analysis_error": str(e)}


@app.get("/api/demo/status")
async def demo_status():
    return {"demo_mode": DEMO_MODE["on"], "state": demo_replay.demo_bridge.snapshot()}


# Override the live-list endpoint when in demo mode
@app.websocket("/ws/demo")
async def ws_demo(ws: WebSocket):
    await ws.accept()
    queue = demo_replay.demo_bridge.subscribe()
    demo_replay.demo_bridge.set_loop(asyncio.get_running_loop())
    try:
        await ws.send_json({"type": "hello", "demo": True,
                            "state": demo_replay.demo_bridge.snapshot()})
        while True:
            msg = await asyncio.wait_for(queue.get(), timeout=120.0)
            await ws.send_json(msg)
    except (WebSocketDisconnect, asyncio.TimeoutError):
        pass
    except Exception as e:
        log.error(f"Demo WS error: {e}")
    finally:
        demo_replay.demo_bridge.unsubscribe(queue)


# =============================================================
# UPLOAD ENDPOINT
# =============================================================
from fastapi import UploadFile, File
import shutil

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """Accept .mat / .txt / .csv upload, run analysis, return result."""
    if not file.filename.lower().endswith((".mat", ".txt", ".csv")):
        raise HTTPException(400, detail="Only .mat / .txt / .csv supported")
    dest = RECORDINGS / file.filename
    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)
    try:
        analysis = analyze_file(dest)
        analysis["filename"] = file.filename
        save_history(analysis, file.filename)
        return {"ok": True, "filename": file.filename, "analysis": analysis}
    except Exception as e:
        log.exception("Upload analyze failed")
        raise HTTPException(500, detail=str(e))


# =============================================================
# EXTRA EUG INSIGHTS ENDPOINT
# =============================================================
@app.get("/api/eug_insights")
async def eug_insights():
    """Aggregate stats across all recordings - for the Insights page."""
    h_path = DB / "history.jsonl"
    if not h_path.exists():
        return {"records": [], "summary": {}}
    records = []
    for line in h_path.read_text(encoding="utf-8").splitlines():
        try:
            records.append(json.loads(line))
        except Exception:
            pass
    if not records:
        return {"records": [], "summary": {}}

    n = len(records)
    n_period = sum(1 for r in records if r.get("verdict") == "PERIOD LIKELY")
    n_nonperiod = sum(1 for r in records if r.get("verdict") == "NON-PERIOD LIKELY")
    n_amb = sum(1 for r in records if r.get("verdict") == "AMBIGUOUS")
    avg_p = sum(r.get("mean_period_probability") or 0 for r in records) / n
    avg_quality = sum(r.get("scorecard_score") or 0 for r in records) / n
    avg_dur = sum(r.get("duration_min") or 0 for r in records) / n

    phase_counts = {}
    for r in records:
        ph = r.get("most_likely_phase") or "UNKNOWN"
        phase_counts[ph] = phase_counts.get(ph, 0) + 1

    return {
        "records": records,
        "summary": {
            "total": n,
            "period_likely": n_period,
            "non_period_likely": n_nonperiod,
            "ambiguous": n_amb,
            "avg_period_probability": round(avg_p, 3),
            "avg_quality_score": round(avg_quality, 1),
            "avg_duration_min": round(avg_dur, 2),
            "phase_distribution": phase_counts,
        }
    }


if __name__ == "__main__":
    import uvicorn, os
    port = int(os.environ.get("PORT", 8000))
    print()
    print("=" * 60)
    print("  MALAIKA v2 - EUG AI Health Assistant")
    print("=" * 60)
    print(f"  Open in browser: http://localhost:{port}")
    print("=" * 60)
    uvicorn.run(app, host="127.0.0.1", port=port)

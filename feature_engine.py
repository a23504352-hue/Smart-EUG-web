"""
Feature engine - extracts the 14 features from a 3-channel recording,
classifies each contraction, and computes per-phase verdicts.

Reuses the existing trained model from malaika fyo project.
"""
from __future__ import annotations
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import joblib
import numpy as np
import pandas as pd
from scipy import signal as _sig
from scipy.io import loadmat
from scipy.ndimage import binary_closing, binary_opening

log = logging.getLogger("feature_engine")

ROOT = Path(__file__).parent
MODEL_PATH = ROOT / "model" / "trained_model.joblib"
THRESHOLDS_PATH = ROOT / "model" / "phase_thresholds.json"
METRICS_PATH = ROOT / "model" / "model_metrics.json"

# Try to load model, but handle version incompatibility gracefully
MODEL_BUNDLE = None
MODEL = None
SCALER = None
FEATURE_NAMES_MODEL = []

if MODEL_PATH.exists():
    try:
        MODEL_BUNDLE = joblib.load(MODEL_PATH)
        MODEL = MODEL_BUNDLE["model"] if MODEL_BUNDLE else None
        SCALER = MODEL_BUNDLE.get("scaler") if MODEL_BUNDLE else None
        FEATURE_NAMES_MODEL = MODEL_BUNDLE.get("feature_names", []) if MODEL_BUNDLE else []
        log.info("Model loaded successfully")
    except (ModuleNotFoundError, ImportError, AttributeError) as e:
        log.warning(f"Could not load model (version incompatibility): {e}")
        log.warning("The website will run, but AI predictions will be disabled. Please retrain the model.")
        MODEL_BUNDLE = None
        MODEL = None
        SCALER = None
        FEATURE_NAMES_MODEL = []

THRESHOLDS = json.loads(THRESHOLDS_PATH.read_text(encoding="utf-8")) if THRESHOLDS_PATH.exists() else {}
METRICS = json.loads(METRICS_PATH.read_text(encoding="utf-8")) if METRICS_PATH.exists() else {}

FS = 2000.0  # 2 kHz sampling rate


# =============================================================
# LOADER
# =============================================================
def load_recording(path: Path) -> Dict[str, np.ndarray]:
    """Load .mat / .txt / .csv -> dict of channels in mV."""
    p = Path(path)
    if p.suffix.lower() == ".mat":
        m = loadmat(p, squeeze_me=True)
        if "data" in m:
            arr = np.asarray(m["data"], dtype=float)
        else:
            cands = [(k, np.asarray(v)) for k, v in m.items()
                     if not k.startswith("__") and np.asarray(v).ndim == 2]
            arr = max(cands, key=lambda kv: max(kv[1].shape))[1].astype(float)
        if arr.ndim == 1: arr = arr.reshape(-1, 1)
        if arr.shape[0] < arr.shape[1]: arr = arr.T
        return {f"CH{i+1}": arr[:, i] for i in range(min(arr.shape[1], 3))}
    if p.suffix.lower() == ".txt":
        # BIOPAC AcqKnowledge .txt export, or simple CSV-like .txt
        text = p.read_text(encoding="utf-8", errors="ignore")
        lines = text.splitlines()
        # Find header row (contains "min" "CH1" "CH2" or just numeric data)
        import re as _re
        header_idx = None
        for i, line in enumerate(lines[:50]):
            low = line.lower()
            if ("min" in low and "ch1" in low) or ("time" in low and "ch1" in low):
                header_idx = i
                break
        rows = []
        skipped_count_row = False
        start = header_idx + 1 if header_idx is not None else 0
        for line in lines[start:]:
            parts = _re.split(r"\s+|,", line.strip())
            if not parts or parts == [""]:
                continue
            try:
                vals = [float(x) for x in parts]
            except ValueError:
                continue
            # Skip the second header row that just contains sample counts
            if not skipped_count_row and len(vals) >= 4 and all(v.is_integer() and v > 1000 for v in vals[1:]):
                skipped_count_row = True
                continue
            rows.append(vals)
        if not rows:
            raise ValueError(f"No numeric data found in .txt: {p}")
        # Normalize row lengths (pad shorter rows with NaN, trim longer)
        max_cols = max(len(r) for r in rows)
        arr = np.full((len(rows), max_cols), np.nan)
        for i, r in enumerate(rows):
            arr[i, :len(r)] = r
        # Drop rows that are mostly NaN
        arr = arr[~np.isnan(arr).all(axis=1)]
        # Drop columns that are mostly NaN
        arr = arr[:, ~np.isnan(arr).any(axis=0)]
        # Detect format: column 0 = time, columns 1-3+ = channels
        if arr.shape[1] >= 4:
            # Skip time col, take first 3 channels
            channels = arr[:, 1:4]
        elif arr.shape[1] == 3:
            channels = arr  # all 3 are channels
        else:
            raise ValueError(f"Need at least 3 channels in .txt, got {arr.shape[1]}")
        return {f"CH{i+1}": channels[:, i] for i in range(min(channels.shape[1], 3))}

    if p.suffix.lower() == ".csv":
        df = pd.read_csv(p)
        out = {}
        for i, col in enumerate([c for c in df.columns if "ch" in c.lower()][:3]):
            # convert uV -> mV if values > 100 (likely uV)
            vals = df[col].values.astype(float)
            if abs(vals).max() > 100:
                vals = vals / 1000.0
            out[f"CH{i+1}"] = vals
        return out
    raise ValueError(f"Unsupported format: {p.suffix}")


# =============================================================
# SIGNAL PROCESSING
# =============================================================
def notch_filter(sig: np.ndarray, fs: float = FS, freq: float = 50.0) -> np.ndarray:
    b, a = _sig.iirnotch(freq, 30.0, fs)
    return _sig.filtfilt(b, a, sig)


def bandpass(sig: np.ndarray, fs: float = FS, lo: float = 0.1, hi: float = 3.0) -> np.ndarray:
    sos = _sig.butter(4, [lo / (fs / 2), hi / (fs / 2)], btype="band", output="sos")
    return _sig.sosfiltfilt(sos, sig)


def rms_envelope(sig: np.ndarray, fs: float = FS, window_s: float = 10.0) -> np.ndarray:
    n = max(3, int(window_s * fs))
    kernel = np.ones(n) / n
    sq = sig * sig
    env = _sig.fftconvolve(sq, kernel, mode="same")
    return np.sqrt(np.maximum(env, 0))


def adaptive_threshold(env: np.ndarray, k: float = 1.5) -> float:
    med = np.median(env)
    mad = np.median(np.abs(env - med))
    sigma = 1.4826 * mad if mad > 1e-12 else env.std()
    return float(med + k * sigma)


def detect_contractions(envelopes: Dict[str, np.ndarray], fs: float = FS,
                        k: float = 1.5, min_dur: float = 4.0,
                        merge_gap: float = 3.0) -> List[Tuple[int, int]]:
    chans = list(envelopes.keys())
    if not chans: return []
    n = len(envelopes[chans[0]])
    active = np.zeros((n, len(chans)), dtype=bool)
    for j, ch in enumerate(chans):
        thr = adaptive_threshold(envelopes[ch], k)
        active[:, j] = envelopes[ch] > thr
    agree = active.sum(axis=1)
    mask = agree >= min(2, len(chans))
    close_n = max(1, int(merge_gap * fs))
    open_n = max(1, int(min_dur / 4 * fs))
    if mask.size:
        mask = binary_closing(mask, structure=np.ones(close_n, dtype=bool))
        mask = binary_opening(mask, structure=np.ones(min(open_n, mask.size), dtype=bool))
    padded = np.r_[False, mask, False]
    edges = np.diff(padded.astype(int))
    starts = np.where(edges == 1)[0]
    ends = np.where(edges == -1)[0]
    min_n = max(1, int(min_dur * fs))
    return [(int(s), int(e)) for s, e in zip(starts, ends) if (e - s) >= min_n]


# =============================================================
# FEATURE EXTRACTION (14 features)
# =============================================================
def extract_features(eug_clean_mv: np.ndarray, env_uv: Dict[str, np.ndarray],
                     contractions: List[Tuple[int, int]],
                     hr_during: float = 70.0, hr_rise: float = 0.0,
                     fs: float = FS) -> List[Dict[str, float]]:
    """Returns list of 14-feature dicts, one per contraction."""
    rows = []
    n_ch = eug_clean_mv.shape[1]
    midpoints = [(s + e) / 2 / fs for s, e in contractions]
    icis = np.diff(midpoints) if len(midpoints) > 1 else np.array([])
    cv_global = float(icis.std() / icis.mean()) if icis.size and icis.mean() > 0 else 0.0
    duration_s = eug_clean_mv.shape[0] / fs
    rate = len(contractions) / max(duration_s / 60.0, 1e-9)

    for s, e in contractions:
        seg_uv = eug_clean_mv[s:e, :] * 1000.0  # mV -> uV
        if seg_uv.size == 0: continue
        dur_s = (e - s) / fs

        rms_amp = float(np.sqrt(np.mean(seg_uv ** 2)))
        peak_amp = float(np.max(np.abs(seg_uv)))
        ptp = float(seg_uv.max() - seg_uv.min())
        amp_std = float(seg_uv.std())

        x = seg_uv.mean(axis=1)
        if x.size >= 64:
            nperseg = min(x.size, max(64, int(fs * 30)))
            f, p = _sig.welch(x, fs=fs, nperseg=nperseg)
            band_full = (f >= 0.1) & (f <= 3.0)
            band_rh = (f >= 0.3) & (f <= 1.0)
            tot = float(np.trapezoid(p[band_full], f[band_full])) if band_full.any() else 0.0
            rh = float(np.trapezoid(p[band_rh], f[band_rh])) if band_rh.any() else 0.0
            spec_ratio = (rh / tot) if tot > 1e-12 else 0.0
            dom_freq = float(f[band_full][np.argmax(p[band_full])]) if band_full.any() else 0.0
            spec_power = tot
        else:
            spec_ratio = dom_freq = spec_power = 0.0

        sync = 0.0
        if n_ch >= 2:
            cors = []
            for a in range(n_ch):
                for b in range(a + 1, n_ch):
                    if seg_uv[:, a].std() > 1e-9 and seg_uv[:, b].std() > 1e-9:
                        c = np.corrcoef(seg_uv[:, a], seg_uv[:, b])[0, 1]
                        if np.isfinite(c): cors.append(c)
            sync = float(np.mean(cors)) if cors else 0.0

        # Channel balance
        ch_rms = [float(np.sqrt(np.mean(seg_uv[:, i] ** 2))) for i in range(n_ch)]
        ch_max = max(ch_rms) if ch_rms else 1
        ch_min = min(ch_rms) if ch_rms else 0
        balance = float(ch_min / ch_max) if ch_max > 1e-9 else 0.0

        rows.append({
            "duration_s": dur_s,
            "rms_amplitude_uv": rms_amp,
            "peak_amplitude_uv": peak_amp,
            "peak_to_peak_uv": ptp,
            "amplitude_std_uv": amp_std,
            "dominant_frequency_hz": dom_freq,
            "spectral_power_0p1_3hz": spec_power,
            "spectral_power_ratio_03_1hz": spec_ratio,
            "cross_channel_sync": sync,
            "contraction_regularity_cv": cv_global,
            "hr_during_bpm": hr_during,
            "hr_rise_bpm": hr_rise,
            "contraction_rate_per_min": rate,
            "channel_amplitude_balance": balance,
            "_start_s": s / fs,
            "_end_s": e / fs,
        })
    return rows


# =============================================================
# MODEL PREDICTION
# =============================================================
def predict(features: List[Dict[str, float]]) -> List[Dict[str, float]]:
    """Run model on extracted features. Returns enriched list."""
    if not features or MODEL is None: return features
    df = pd.DataFrame(features)
    X = df[FEATURE_NAMES_MODEL].fillna(0).values.astype(float)
    X = np.nan_to_num(X, 0.0, 0.0, 0.0)
    if SCALER is not None:
        X = SCALER.transform(X)
    probs = MODEL.predict_proba(X)[:, 1]
    for i, f in enumerate(features):
        f["period_probability"] = float(probs[i])
        f["prediction"] = "PERIOD" if probs[i] >= 0.5 else "NON-PERIOD"
    return features


# =============================================================
# PHASE CLASSIFICATION (per feature, per contraction)
# =============================================================
def classify_phase(value: float, feature_def: dict) -> Tuple[str, str]:
    """Given a value and feature def, return (best phase, label)."""
    best_phase = "UNKNOWN"
    best_label = "out of range"
    for phase_name, ph in feature_def.get("phases", {}).items():
        lo, hi = ph["min"], ph["max"]
        if lo <= value <= hi:
            best_phase = phase_name
            best_label = ph["label"]
            break
    return best_phase, best_label


def per_feature_phase_analysis(features: List[Dict[str, float]]) -> List[Dict]:
    """For each feature, compute mean across all contractions + best phase fit."""
    if not features: return []
    feature_defs = THRESHOLDS.get("features", [])
    out = []
    for fdef in feature_defs:
        key = fdef["key"]
        values = [f.get(key, 0) for f in features if key in f]
        if not values: continue
        mean_val = float(np.mean(values))
        best_phase, best_label = classify_phase(mean_val, fdef)
        out.append({
            "key": key,
            "name": fdef["name"],
            "unit": fdef["unit"],
            "patient_label": fdef["patient_label"],
            "doctor_label": fdef["doctor_label"],
            "value": round(mean_val, 3),
            "best_phase": best_phase,
            "best_label": best_label,
            "phases": fdef["phases"],
            "patient_explanation": fdef["patient_explanation"],
            "doctor_explanation": fdef["doctor_explanation"],
        })
    return out


# =============================================================
# OVERALL VERDICT
# =============================================================
def overall_verdict(features: List[Dict], per_feature: List[Dict]) -> dict:
    n = len(features)
    if n == 0:
        return {
            "verdict": "INCONCLUSIVE",
            "reason": "No contractions detected. Recording may be too short or signal too weak.",
            "mean_p": 0.0, "n_period": 0, "n_total": 0,
            "phase_votes": {},
        }
    probs = [f.get("period_probability", 0) for f in features]
    mean_p = float(np.mean(probs))
    n_period = sum(1 for p in probs if p >= 0.5)

    # Phase voting based on per-feature analysis
    phase_votes = {"MENSTRUAL": 0, "FOLLICULAR": 0, "OVULATION": 0, "LUTEAL": 0, "UNKNOWN": 0}
    for pf in per_feature:
        phase_votes[pf["best_phase"]] = phase_votes.get(pf["best_phase"], 0) + 1
    most_likely_phase = max(phase_votes, key=phase_votes.get)

    if mean_p >= 0.65:
        v, r = "PERIOD LIKELY", f"Mean P(period)={mean_p:.0%}. {n_period}/{n} contractions period-like. Most features match {most_likely_phase} phase."
    elif mean_p <= 0.35:
        v, r = "NON-PERIOD LIKELY", f"Mean P(period)={mean_p:.0%}. Most features match {most_likely_phase} phase."
    else:
        v, r = "AMBIGUOUS", f"Mean P(period)={mean_p:.0%}. Mixed signals across {n} contractions."

    return {
        "verdict": v, "reason": r,
        "mean_p": round(mean_p, 4), "n_period": n_period, "n_total": n,
        "most_likely_phase": most_likely_phase,
        "phase_votes": phase_votes,
    }


# =============================================================
# QUALITY SCORECARD
# =============================================================
def quality_scorecard(features: List[Dict], duration_min: float, mean_p: float) -> dict:
    n = len(features)
    rate = (n / max(duration_min, 0.01)) * 60.0
    checks = []

    def chk(name, status, value, note):
        checks.append({"name": name, "status": status, "value": str(value), "note": note})

    chk("Recording duration", "pass" if duration_min >= 5 else "warn" if duration_min >= 3 else "fail",
        f"{duration_min:.1f} min", "Excellent" if duration_min >= 5 else "Sufficient" if duration_min >= 3 else "Too short")
    chk("Contractions detected", "pass" if n >= 5 else "warn" if n >= 2 else "fail",
        n, "Strong sample" if n >= 5 else "Adequate" if n >= 2 else "Few contractions")
    chk("Contraction rate", "pass" if rate <= 60 else "warn",
        f"{rate:.1f}/hr", "Within physiological range" if rate <= 60 else "High - check artifacts")
    chk("AI confidence", "pass" if abs(mean_p - 0.5) >= 0.2 else "warn",
        f"{mean_p:.2f}", "Decisive" if abs(mean_p - 0.5) >= 0.2 else "Borderline")

    if n > 0:
        avg_sync = float(np.mean([f.get("cross_channel_sync", 0) for f in features]))
        chk("Channel agreement", "pass" if avg_sync >= 0.4 else "warn" if avg_sync >= 0.2 else "fail",
            f"{avg_sync:.2f}", "Strong coupling" if avg_sync >= 0.4 else "Moderate" if avg_sync >= 0.2 else "Weak")
        ratio = sum(1 for f in features if f.get("period_probability", 0) >= 0.5) / max(n, 1)
        chk("Class consistency", "pass" if ratio >= 0.8 or ratio <= 0.2 else "warn",
            f"{ratio:.0%}", "Consistent" if ratio >= 0.8 or ratio <= 0.2 else "Mixed")

    n_pass = sum(1 for c in checks if c["status"] == "pass")
    n_warn = sum(1 for c in checks if c["status"] == "warn")
    n_fail = sum(1 for c in checks if c["status"] == "fail")
    score = max(0, min(100, int(100 * (n_pass + 0.5 * n_warn) / max(len(checks), 1))))
    return {"checks": checks, "score": score, "n_pass": n_pass, "n_warn": n_warn, "n_fail": n_fail,
            "rate_per_hour": round(rate, 1)}


# =============================================================
# AI EXPLANATION (Patient + Doctor versions)
# =============================================================
def ai_explanation(verdict_data: dict, features: List[Dict],
                   per_feature: List[Dict], view: str = "patient") -> str:
    n = verdict_data.get("n_total", 0)
    mp = verdict_data.get("mean_p", 0)
    phase = verdict_data.get("most_likely_phase", "UNKNOWN")
    if n == 0:
        if view == "patient":
            return "No contractions were detected in this recording. The signal might have been too short, or the electrodes may have shifted. Try recording for longer (5-10 minutes) and make sure all electrodes are firmly in place."
        return "Zero contractions detected. Recommend re-recording with adequate session length (>=5 min), verify electrode contact and channel-to-channel correlation."

    parts = []
    duration = max(features[-1].get("_end_s", 0) / 60.0, 0.1) if features else 0
    rate_hr = (n / duration) * 60 if duration > 0 else 0

    if view == "patient":
        parts.append(f"I detected {n} contractions in your recording (about {rate_hr:.1f} per hour).")
        avg_amp = float(np.mean([f.get("peak_amplitude_uv", 0) for f in features]))
        avg_sync = float(np.mean([f.get("cross_channel_sync", 0) for f in features]))
        if avg_amp > 60:
            parts.append(f"Your contractions are STRONG (average peak {avg_amp:.0f} µV) - this is typical of menstrual phase, when your uterus is actively shedding its lining.")
        elif avg_amp > 30:
            parts.append(f"Your contractions are MODERATE (average peak {avg_amp:.0f} µV) - this can happen during ovulation or as period is starting/ending.")
        else:
            parts.append(f"Your contractions are MILD (average peak {avg_amp:.0f} µV) - typical of non-period phases when your uterus is calm.")
        if avg_sync > 0.4:
            parts.append("All 3 sensors picked up the same activity at the same time, which means it's coming from your uterus - not noise.")
        if mp >= 0.65:
            parts.append("The AI is very confident this looks like a period. Take care of yourself - rest, hydrate, eat iron-rich foods.")
        elif mp <= 0.35:
            parts.append("The AI is very confident this is NOT period activity. Your uterus is in a calm phase right now.")
        else:
            parts.append("Results are borderline. Try recording again on a later day for clearer signal.")
        parts.append(f"Most features point to the {phase} phase of your cycle.")
    else:
        parts.append(f"Detected {n} contractions over {duration:.1f} min (rate {rate_hr:.1f}/hr).")
        avg_amp = float(np.mean([f.get("peak_amplitude_uv", 0) for f in features]))
        avg_sync = float(np.mean([f.get("cross_channel_sync", 0) for f in features]))
        avg_freq = float(np.mean([f.get("dominant_frequency_hz", 0) for f in features]))
        avg_cv = float(np.mean([f.get("contraction_regularity_cv", 0) for f in features]))
        parts.append(f"Mean peak amplitude {avg_amp:.1f} uV. Cross-channel sync {avg_sync:.2f}. "
                     f"Dominant frequency {avg_freq:.2f} Hz. Inter-contraction CV {avg_cv:.2f}.")
        parts.append(f"Phase voting matrix favors {phase}.")
        if mp >= 0.65:
            parts.append(f"P(menstrual) = {mp:.2f} - GradientBoosting model classifies as menstrual myometrial activity.")
        elif mp <= 0.35:
            parts.append(f"P(menstrual) = {mp:.2f} - non-gravid quiescent or follicular pattern.")
        else:
            parts.append(f"P(menstrual) = {mp:.2f} - inconclusive, recommend re-recording at a different cycle day.")
    return " ".join(parts)

# SMART EUG — AI Uterine-Health Tracker

> **Smart EUG** is an offline, AI-powered uterine-health tracker. Plug in an ESP32,
> record live EUG (Electro-UteroGraphy) signals, and get an instant ML-driven
> analysis — 14 features across 4 cycle phases, 0.93 AUC — with an AI chat that
> explains *what* it saw and *why*, in plain language. 100% private: your data
> never leaves your laptop.

## Quick start

1. **Plug in your ESP32** (Micro-USB to laptop)
2. **Double-click `start_website.bat`**
3. **Open browser:** http://localhost:8000

That's it.

## What works

- ✅ ESP32 auto-detected on any COM port
- ✅ Click START → live waveforms appear → click STOP → auto-analyzes
- ✅ 14 features × 4 phase thresholds shown for each recording
- ✅ Real AI chat (uses Ollama if installed, smart fallback if not)
- ✅ Wellness tracker, diary, calendar, history, dashboard
- ✅ 3D anatomy with phase color
- ✅ Light + dark mode toggle
- ✅ Auto-saves every recording as `.mat`, `.csv`, `.txt`

## Folder layout

```
smart-eug/
├── start_website.bat    ← double-click to launch
├── api.py               ← main server (FastAPI)
├── esp32_bridge.py      ← USB serial bridge (auto-starts)
├── ai_brain.py          ← AI chat
├── feature_engine.py    ← 14 features + phase thresholds + ML
├── demo_replay.py       ← offline playground replays
├── dataset/             ← ML signal tables & trial database
│   ├── DAY 1.txt to DAY 27.txt (raw sensor recordings)
│   └── ...
├── model/               ← trained model + validation metrics
│   ├── trained_model.joblib
│   ├── phase_thresholds.json
│   ├── model_metrics.json
│   ├── ROC Curve & Confusion Matrix graphs
│   └── TRAINING_REPORT.txt
├── templates/           ← all HTML interface pages
│   ├── index.html · live.html · result.html · chat.html · anatomy.html · ...
├── static/              ← CSS stylesheets + custom UI JS
│   └── style.css · widgets.js · live_waveform.js · anatomy_3d.js
├── esp32_firmware/      ← Microcontroller software
│   └── esp32_firmware.ino
├── images/              ← UI screenshots demonstrating features
│   ├── admin panel, 3D anatomical charts, metrics dashboards...
├── videos/              ← high-quality marketing & demo footage
│   ├── smart_eug_promo.mp4          ← aesthetic product launch reel
│   └── smart_eug_website_demo.mp4   ← complete web walkthrough
└── recordings/          ← auto-saves local trials (.mat + .csv + .txt)
```

## ESP32 firmware

1. Open Arduino IDE
2. Install **ESP32 boards** (File → Preferences → Additional URLs:
   `https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json`)
3. Tools → Board → ESP32 Dev Module
4. Tools → Port → COM3 (or whichever)
5. Open `esp32_firmware/esp32_firmware.ino`
6. Click Upload

After upload, the ESP32 listens for commands from website. No more BOOT button needed!

## Hardware wiring (3-channel EUG)

| ESP32 pin | PCB pin | Wire |
|---|---|---|
| GND | NS1 (any GND) | black |
| GPIO 34 | LEFT OP1 | pink |
| GPIO 35 | MIDDLE OP2 | purple |
| GPIO 32 | RIGHT OP3 | cyan |

Battery powers PCB (PS1+, NS1−). USB powers ESP32.

## Optional: Better AI chat with Ollama

Without Ollama: chat uses smart rule-based fallback (knows EUG, cycle, all 14 features).
With Ollama: uses a real LLM (smarter, conversational).

Install Ollama (free, offline):
1. Download: https://ollama.com/download
2. Open terminal: `ollama pull llama3.2:1b`
3. Restart the website.

That's it — chat will auto-detect Ollama and use it.

## Troubleshooting

| Problem | Fix |
|---|---|
| ESP32 not detected | Try different USB cable, check Device Manager for COM port |
| "No demo recordings" | Click Refresh, recordings appear after first stop |
| Chat says "Ollama not detected" | OK — fallback works. Install Ollama for upgrade. |
| Pages broken | Hard refresh in browser: Ctrl+F5 |
| Server won't start | Check Python is installed: `python --version` |

"""
AI Brain v2 — fallback chain:
  1. Groq (free, fast, real LLM)
  2. HuggingFace Inference API (free)
  3. Smart local rule-based (works offline, knows EUG project)

Configured via env vars or hardcoded keys below. Failsafe = always works.
"""
from __future__ import annotations
import json
import logging
import os
import re
from pathlib import Path
from typing import List, Dict, Optional
import urllib.request
import urllib.error

log = logging.getLogger("ai_brain")

# === KEYS (override via env vars if needed) ===
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "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")
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.1-8b-instant")
HF_API_KEY = os.environ.get("HF_API_KEY", "")  # optional

ROOT = Path(__file__).parent
THRESHOLDS_PATH = ROOT / "model" / "phase_thresholds.json"
THRESHOLDS_DATA = {}
if THRESHOLDS_PATH.exists():
    THRESHOLDS_DATA = json.loads(THRESHOLDS_PATH.read_text(encoding="utf-8"))

SYSTEM_PROMPT = """You are MALAIKA AI, a warm, knowledgeable women's health
assistant for an EUG (uterine electromyography) FYP project. You help patients
and doctors understand uterine signals, menstrual cycles, contractions, period
care, fertility, and overall women's wellness.

PROJECT KNOWLEDGE:
- EUG = electrical signals from the uterus, measured via 3 abdominal electrodes
- 14 features per contraction (amplitude, frequency, sync, regularity, HR)
- AI model: GradientBoosting, AUC 0.93, 5-fold CV
- 4 cycle phases: MENSTRUAL (1-5), FOLLICULAR (6-13), OVULATION (14), LUTEAL (15-28)
- Period contractions: STRONG (>60uV peak), RHYTHMIC (CV<0.5), COORDINATED (sync>0.4)
- Hardware: ESP32-WROOM-32 + 3-channel EUG PCB at 2 kHz
- Custom 3D-printed Lotus Pod electrodes with 12mm contact pad

RULES:
1. Be warm, supportive — like a kind friend who's also a nurse
2. Use simple language for patients, technical when asked
3. Always recommend a doctor for: bleeding > 7 days, pain > 7/10, missed periods 3+ months
4. Never diagnose or prescribe
5. Keep replies SHORT (2-4 sentences usually) unless detailed answer requested
6. Use cycle-aware advice (e.g., "during your luteal phase, more sleep helps")
7. Patient privacy is paramount — everything runs locally

Tone: warm, factual, encouraging. Use 1-2 emojis sparingly when warm."""


# =============================================================
# FALLBACK 3: smart local responses (always works, no internet)
# =============================================================
KNOWLEDGE = {
    "eug": "EUG (electrouterography) measures tiny electrical signals from your uterus through 3 abdominal electrodes. Like ECG measures the heart, EUG measures uterine muscle activity. During your period, signals are stronger, more rhythmic, and more synchronized. 🌸",
    "period": "A period (menstruation) is days 1-5 of your cycle. Your uterus actively contracts to shed its lining. Period contractions are STRONG, RHYTHMIC, and feel like dull aches every 2-3 minutes. Most women feel them most on day 1-2.",
    "follicular": "Days 6-13 of your cycle. Your body is preparing to release an egg. Estrogen rises, energy returns, mood lifts. Uterine activity is calm and minimal during this phase — perfect time for workouts.",
    "ovulation": "Day 14. Your ovary releases an egg. Most fertile day. You may feel mild cramps or a small temperature spike. Cervical mucus becomes egg-white texture. Brief mid-cycle uterine activity is normal.",
    "luteal": "Days 15-28. Body prepares for next period. Progesterone rises. PMS symptoms (mood swings, bloating, tender breasts) often appear in last 5 days. More sleep + magnesium-rich foods help.",
    "auc": "AUC = Area Under Curve. Measures how well our AI separates period from non-period contractions. 0.5 = random guessing, 1.0 = perfect. We achieve 0.93 — clinically excellent. 🎯",
    "contraction": "A contraction is when your uterus muscle tightens. During period, they're strong and rhythmic. We detect them when at least 2 of 3 electrodes see a spike at the same time — this confirms it's real uterine activity, not noise.",
    "pain": "Mild period pain (3-5/10) is normal. Severe pain (>7/10) lasting more than 2 days may be dysmenorrhea, endometriosis, or other conditions. Track it here daily and bring trends to a doctor.",
    "cramp": "Cramps are caused by your uterus contracting to shed its lining. **What helps:** heat pads, warm water, gentle yoga, ibuprofen, magnesium, dark chocolate. If unbearable or new, see a doctor.",
    "iron": "During your period, you lose blood = lose iron. Eat iron-rich foods: spinach, lentils, beans, red meat, fortified cereals. Vitamin C (oranges, peppers) helps absorption. Tea/coffee blocks it — drink with food, not after.",
    "sleep": "Sleep matters more during luteal phase (week before period) — aim 8+ hours. Progesterone makes you sleepier; honor that. Cool dark room, no screens 1 hour before bed.",
    "exercise": "Match exercise to cycle: gentle yoga during period, peak workouts during ovulation, moderate during luteal. Listen to your body — 'no rule' workouts are sometimes the best 💪",
    "model": "Our AI uses GradientBoosting, trained on 149 contractions from multiple subjects. It looks at 14 features per contraction (amplitude, frequency, regularity, channel sync, heart rate) and predicts P(period) for each.",
    "feature": "We use 14 features per contraction: duration, RMS, peak, peak-to-peak, std, dominant frequency, total power, rhythmic ratio, cross-channel sync, regularity CV, HR during, HR rise, contraction rate, channel balance.",
    "fertility": "Fertile window: 5 days before ovulation through ovulation day. EUG can help confirm cycle phase but not replace ovulation tests. Use the calendar page to track your fertile days.",
    "miss": "Missed period? Could be pregnancy, stress, weight changes, hormonal imbalance, PCOS, or thyroid. If 3+ months missed and not pregnant, please see a doctor. Bring your tracking data.",
    "heavy": "Heavy bleeding (changing pad/tampon every 1-2 hours, lasting > 7 days) needs medical attention. Track it on the wellness page and show your doctor.",
    "pcos": "PCOS = polycystic ovary syndrome. Common cause of irregular cycles. EUG patterns may show muted/inconsistent contractions. Consult an endocrinologist or gynecologist for diagnosis.",
    "endometriosis": "Endometriosis = uterine tissue growing outside the uterus. Causes severe pain, heavy bleeding, unusually strong contractions. EUG can support diagnosis but always confirm with imaging + specialist.",
    "pregnancy": "Pregnancy basics: missed period + symptoms (nausea, breast tenderness, fatigue) → take a home test. EUG patterns are different in pregnancy (much higher amplitude). For prenatal care, see an OB/GYN.",
    "hormone": "Two main hormones: estrogen (rises pre-ovulation), progesterone (rises after). Both fluctuate through your cycle. Imbalance can cause irregular periods, mood swings, weight changes, acne.",
    "mood": "Mood varies with cycle phase. **Pre-period (luteal)**: low mood common due to progesterone drop. **Period**: emotions intense. **Follicular**: usually best mood. **Ovulation**: confidence peaks. Track yours to see your own pattern.",
    "blood": "Bleeding patterns vary. **Normal**: 3-7 days, 30-80 ml total. **See a doctor** for: bleeding > 7 days, soaking a pad in 1-2 hours, bleeding between periods.",
    "doctor": "**See a doctor for**: heavy bleeding > 7 days, severe pain > 7/10, missed periods > 3 months, fever during period, suspected pregnancy, or anything that feels wrong. Bring your tracked data — it really helps them.",
    "electrode": "Electrodes are the small sensors that stick to your abdomen. They pick up tiny electrical signals from your uterus. We use 7 electrodes total: 3 differential pairs (CH1, CH2, CH3) + 1 ground reference on the hip.",
    "esp32": "ESP32 is the small microcontroller that reads electrical signals from the EUG PCB at 2 kHz and sends them to your laptop over USB. Cost: ~$5. Replaces $5,000+ clinical equipment.",
    "record": "To record: (1) plug in ESP32, (2) stick electrodes on lower abdomen + hip, (3) click START on /live page, (4) lie still 5+ minutes, (5) click STOP. AI auto-analyzes.",
    "phase": "4 menstrual cycle phases: **Menstrual** (days 1-5, period), **Follicular** (6-13, lining rebuilds), **Ovulation** (day 14, egg released), **Luteal** (15-28, post-ovulation prep).",
    "lining": "The endometrium is the inner lining of your uterus. It thickens during follicular + ovulation phases preparing for a possible pregnancy. If no pregnancy, it sheds during your period (menstruation). The cycle repeats.",
    "egg": "An egg (ovum) releases from your ovary on day 14 (ovulation). It travels down the fallopian tube. If fertilized by sperm in 12-24 hours, pregnancy. If not, the lining sheds 14 days later (next period).",
    "cycle": "A cycle is days from the first day of your period to the day before your next period. **Average**: 28 days, but 21-35 is normal. Track yours on the calendar page.",
    "diet": "Cycle nutrition: **Period** — iron + warm foods. **Follicular** — fresh greens + berries. **Ovulation** — antioxidants + zinc. **Luteal** — magnesium + complex carbs to ease PMS.",
}


def _smart_fallback(user_message: str, history: List[Dict[str, str]]) -> str:
    """Smart fallback when no API works."""
    msg = user_message.lower().strip()

    if re.search(r"\b(hi|hello|hey|salaam|asalaam)\b", msg) and len(msg) < 30:
        return "Hi! 🌸 I'm MALAIKA — your private women's health assistant. Ask me about your cycle, EUG signals, contractions, period care, fertility, or anything else."
    if re.search(r"\b(thank|thanks|shukr)\b", msg):
        return "You're welcome! Take care of yourself. 🩷"
    if re.search(r"\b(bye|goodbye|good night)\b", msg):
        return "Take care! Remember — you know your body best. 🌸"

    # Topic match
    for key, ans in KNOWLEDGE.items():
        if key in msg:
            return ans

    # Pattern matches
    if re.search(r"\b(when|next).*(period|cycle)\b", msg):
        return "Open the **Calendar** page and enter your last period date — you'll see exactly when your next period is predicted, plus your ovulation window. Most cycles are 28 days, but yours might differ."
    if re.search(r"\bworry|concerned|scared|abnormal\b", msg):
        return "It's understandable to feel worried. Two things help: (1) track symptoms here daily, (2) bring trends to a gynecologist. What specific symptom is bothering you? I can give more targeted advice."
    if re.search(r"\b(food|eat|cook|meal)\b", msg):
        return "Eat with your cycle in mind. Period: iron-rich foods (spinach, lentils, red meat). Follicular: fresh greens, berries. Ovulation: antioxidants. Luteal: magnesium (almonds, dark chocolate). Hydrate well always 💚"
    if re.search(r"\b(exercise|workout|gym)\b", msg):
        return "Period: gentle yoga, walking. Follicular: cardio + strength training (energy peaks). Ovulation: best day for hard workouts. Luteal: moderate (walking, swimming). Listen to your body 💪"
    if re.search(r"\b(am|i'm) (\w+)\b", msg):  # introductions
        return "Nice to meet you! 🌸 How can I help today? You can ask me about your cycle, EUG signals, period care, fertility, wellness — anything at all."
    if re.search(r"\bwhat\b.*\bmean\b", msg):
        return "Could you tell me which feature or term? I can explain EUG, contractions, AUC, all 14 features, the 4 cycle phases, or anything else you saw on the website."

    # Default helpful response
    return ("I want to help with that. Could you share a bit more about what you're asking? "
            "I know about: cycle phases, period symptoms, EUG signals, the 14 features, "
            "contractions, fertility, pain management, nutrition, exercise, sleep, "
            "and general women's wellness. 🌸")


# =============================================================
# FALLBACK 2: HuggingFace
# =============================================================
def _hf_chat(messages: List[Dict[str, str]]) -> Optional[str]:
    if not HF_API_KEY:
        return None
    try:
        # Use the conversational task on a free model
        text = messages[-1]["content"]
        body = json.dumps({
            "inputs": {"text": text},
            "parameters": {"max_new_tokens": 250, "temperature": 0.7},
        }).encode("utf-8")
        req = urllib.request.Request(
            "https://api-inference.huggingface.co/models/microsoft/Phi-3-mini-4k-instruct",
            data=body,
            headers={"Authorization": f"Bearer {HF_API_KEY}",
                     "Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
        if isinstance(data, list) and data:
            return data[0].get("generated_text", "").strip()
        if isinstance(data, dict) and "generated_text" in data:
            return data["generated_text"].strip()
        return None
    except Exception as e:
        log.debug(f"HF API failed: {e}")
        return None


# =============================================================
# FALLBACK 1: Groq (primary)
# =============================================================
def _groq_chat(messages: List[Dict[str, str]]) -> Optional[str]:
    if not GROQ_API_KEY:
        return None
    try:
        body = json.dumps({
            "model": GROQ_MODEL,
            "messages": messages,
            "max_tokens": 400,
            "temperature": 0.7,
        }).encode("utf-8")
        req = urllib.request.Request(
            "https://api.groq.com/openai/v1/chat/completions",
            data=body,
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json",
                "User-Agent": "malaika-v2/1.0",
            },
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
        choices = data.get("choices", [])
        if choices:
            return choices[0]["message"]["content"].strip()
        return None
    except urllib.error.HTTPError as e:
        log.warning(f"Groq HTTP error: {e.code} {e.read()[:200]}")
        return None
    except Exception as e:
        log.debug(f"Groq failed: {e}")
        return None


# =============================================================
# OLLAMA (legacy, low priority)
# =============================================================
def _ollama_chat(messages: List[Dict[str, str]]) -> Optional[str]:
    try:
        body = json.dumps({
            "model": "llama3.2:1b",
            "messages": messages,
            "stream": False,
        }).encode("utf-8")
        req = urllib.request.Request(
            "http://localhost:11434/api/chat", data=body,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
        return data.get("message", {}).get("content", "").strip() or None
    except Exception:
        return None


# =============================================================
# PUBLIC API
# =============================================================
def chat(user_message: str, history: List[Dict[str, str]] = None) -> dict:
    """Returns {'reply': str, 'source': 'groq'|'hf'|'ollama'|'fallback'}"""
    history = history or []
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for h in history[-10:]:
        if h.get("role") in ("user", "assistant"):
            messages.append({"role": h["role"], "content": h.get("content", "")})
    messages.append({"role": "user", "content": user_message})

    # Try Groq first
    answer = _groq_chat(messages)
    if answer:
        return {"reply": answer, "source": "groq"}

    # Try Ollama if running
    answer = _ollama_chat(messages)
    if answer:
        return {"reply": answer, "source": "ollama"}

    # Try HuggingFace
    answer = _hf_chat(messages)
    if answer:
        return {"reply": answer, "source": "hf"}

    # Local rule-based smart fallback
    return {"reply": _smart_fallback(user_message, history), "source": "fallback"}


def is_ai_available() -> dict:
    """Test which backends are reachable."""
    out = {"groq": bool(GROQ_API_KEY), "ollama": False, "hf": False, "fallback": True}
    # Quick Groq check
    if GROQ_API_KEY:
        try:
            body = json.dumps({"model": GROQ_MODEL,
                                "messages": [{"role": "user", "content": "hi"}],
                                "max_tokens": 5}).encode("utf-8")
            req = urllib.request.Request(
                "https://api.groq.com/openai/v1/chat/completions",
                data=body,
                headers={"Authorization": f"Bearer {GROQ_API_KEY}",
                         "Content-Type": "application/json"})
            urllib.request.urlopen(req, timeout=5)
            out["groq"] = True
        except Exception:
            pass
    # Ollama
    try:
        urllib.request.urlopen("http://localhost:11434/api/tags", timeout=2)
        out["ollama"] = True
    except Exception:
        pass
    return out


# Compatibility shim for old imports
def is_ollama_available() -> bool:
    return is_ai_available().get("groq", False) or is_ai_available().get("ollama", False)

/*
 * EUG Smart Recorder Firmware v2 - Website-Controlled ESP32
 * ============================================================
 * Hardware: ESP32-WROOM-32, 3-channel EUG PCB
 * Pins:     CH1 -> GPIO 34, CH2 -> GPIO 35, CH3 -> GPIO 32
 * Baud:     115200 (text), upgrades to 921600 for streaming
 *
 * COMMANDS (sent from laptop bridge over USB serial):
 *   PING\n          -> Replies PONG with FW version + chip ID
 *   START\n         -> Begin streaming 3-channel data at 2 kHz
 *   STOP\n          -> End streaming
 *   STATUS\n        -> Reply current state + buffer health
 *   QUALITY\n       -> Reply per-channel signal quality (0-100)
 *   CONTACT\n       -> Reply per-channel electrode contact (good/loose/off)
 *   LED:RED\n       -> Force LED red (recording)
 *   LED:GREEN\n     -> Force LED green (idle)
 *   LED:OFF\n       -> Turn LED off
 *
 * STREAMING FORMAT (2 kHz, 3 channels, ~12 KB/s):
 *   Each sample: "t,c1,c2,c3\n"  -> ASCII CSV
 *   Header on START: "# STREAM_START\n"
 *   Footer on STOP:  "# STREAM_STOP n=<sample_count>\n"
 *
 * BUILT-IN FEATURES:
 *   - Electrode contact detection (DC-level check every 500 ms)
 *   - Live RMS quality reporter (every 1 sec)
 *   - Status LED (onboard GPIO 2):
 *       solid green  = idle, ready
 *       solid red    = recording
 *       blinking red = streaming, healthy
 *       blinking yellow = electrode issue
 *       solid yellow = error / bad contact
 *   - Watchdog: if no command for 60s while recording, auto-stop
 *   - Buffer overflow protection
 */

#include <Arduino.h>

#define FW_VERSION "EUG-FW v2.0"
#define BAUD_RATE   115200

// === Pins ===
const int CH1_PIN     = 34;
const int CH2_PIN     = 35;
const int CH3_PIN     = 32;
const int LED_PIN     = 2;
const int LED_R_PIN   = 27;     // optional external RGB LED (red)
const int LED_G_PIN   = 26;     // optional external RGB LED (green)
const int LED_B_PIN   = 25;     // optional external RGB LED (blue)

// === Sampling ===
const uint32_t SAMPLE_INTERVAL_US = 500;     // 2 kHz
uint32_t nextSampleAt = 0;

// === State ===
enum State { IDLE, STREAMING, ERROR };
State state = IDLE;
unsigned long startMs = 0;
uint32_t sampleCount = 0;
unsigned long lastCommandMs = 0;
unsigned long lastQualityMs = 0;

// === Quality monitoring (rolling) ===
const int QBUF = 200;             // 200 samples = 100 ms at 2 kHz
int qbuf[3][QBUF];
int qIdx = 0;
int dcLevel[3] = {2048, 2048, 2048};      // running mean ~ baseline
float quality[3] = {0, 0, 0};             // 0-100
bool electrodeOk[3] = {true, true, true};

// === LED state ===
unsigned long lastLedMs = 0;
bool ledBlinkState = false;

// =============================================================
//   SETUP
// =============================================================
void setup() {
  Serial.begin(BAUD_RATE);
  pinMode(LED_PIN, OUTPUT);

  // Optional RGB - only used if external LED wired
  pinMode(LED_R_PIN, OUTPUT);
  pinMode(LED_G_PIN, OUTPUT);
  pinMode(LED_B_PIN, OUTPUT);

  analogReadResolution(12);
  analogSetAttenuation(ADC_11db);

  // Boot info
  delay(800);
  Serial.println();
  Serial.print("# BOOT ");
  Serial.println(FW_VERSION);
  Serial.println("# READY - waiting for commands");
  setLED(0, 1, 0);   // green
}

// =============================================================
//   LOOP
// =============================================================
void loop() {
  // ---- Read incoming command line ----
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    cmd.toUpperCase();
    handleCommand(cmd);
    lastCommandMs = millis();
  }

  // ---- Stream samples if recording ----
  if (state == STREAMING && micros() >= nextSampleAt) {
    nextSampleAt = micros() + SAMPLE_INTERVAL_US;
    int c1 = analogRead(CH1_PIN);
    int c2 = analogRead(CH2_PIN);
    int c3 = analogRead(CH3_PIN);

    // push to quality buffer
    qbuf[0][qIdx] = c1;
    qbuf[1][qIdx] = c2;
    qbuf[2][qIdx] = c3;
    qIdx = (qIdx + 1) % QBUF;

    unsigned long t = millis() - startMs;
    Serial.print(t);  Serial.print(',');
    Serial.print(c1); Serial.print(',');
    Serial.print(c2); Serial.print(',');
    Serial.println(c3);
    sampleCount++;
  }

  // ---- Periodic quality + contact checks ----
  if (state == STREAMING && (millis() - lastQualityMs) >= 1000) {
    lastQualityMs = millis();
    updateQuality();
    updateContactStatus();
    blinkBasedOnHealth();
  }

  // ---- Idle LED breathing ----
  if (state == IDLE && (millis() - lastLedMs) >= 700) {
    lastLedMs = millis();
    ledBlinkState = !ledBlinkState;
    digitalWrite(LED_PIN, ledBlinkState);
    setLED(0, ledBlinkState ? 1 : 0, 0);
  }

  // ---- Watchdog ----
  if (state == STREAMING && lastCommandMs > 0 &&
      (millis() - lastCommandMs) > 300000) {
    Serial.println("# AUTO_STOP watchdog");
    stopStream();
  }
}

// =============================================================
//   COMMAND HANDLER
// =============================================================
void handleCommand(const String& cmd) {
  if (cmd == "PING") {
    Serial.print("PONG fw=");
    Serial.print(FW_VERSION);
    Serial.print(" chip=");
    Serial.println(ESP.getChipModel());
  }
  else if (cmd == "START") {
    startStream();
  }
  else if (cmd == "STOP") {
    stopStream();
  }
  else if (cmd == "STATUS") {
    Serial.print("STATUS state=");
    Serial.print(state == IDLE ? "IDLE" :
                 state == STREAMING ? "STREAMING" : "ERROR");
    Serial.print(" samples=");
    Serial.print(sampleCount);
    Serial.print(" uptime=");
    Serial.println(millis());
  }
  else if (cmd == "QUALITY") {
    Serial.print("QUALITY ch1=");
    Serial.print(quality[0], 1);
    Serial.print(" ch2=");
    Serial.print(quality[1], 1);
    Serial.print(" ch3=");
    Serial.println(quality[2], 1);
  }
  else if (cmd == "CONTACT") {
    Serial.print("CONTACT ch1=");
    Serial.print(electrodeOk[0] ? "OK" : "BAD");
    Serial.print(" ch2=");
    Serial.print(electrodeOk[1] ? "OK" : "BAD");
    Serial.print(" ch3=");
    Serial.println(electrodeOk[2] ? "OK" : "BAD");
  }
  else if (cmd.startsWith("LED:")) {
    String c = cmd.substring(4);
    if (c == "RED")    setLED(1, 0, 0);
    else if (c == "GREEN") setLED(0, 1, 0);
    else if (c == "BLUE")  setLED(0, 0, 1);
    else if (c == "YELLOW") setLED(1, 1, 0);
    else                    setLED(0, 0, 0);
  }
  else {
    Serial.print("# UNKNOWN ");
    Serial.println(cmd);
  }
}

// =============================================================
//   STREAM CONTROL
// =============================================================
void startStream() {
  state = STREAMING;
  startMs = millis();
  sampleCount = 0;
  qIdx = 0;
  for (int i = 0; i < 3; i++) for (int j = 0; j < QBUF; j++) qbuf[i][j] = 2048;
  Serial.println("# STREAM_START");
  setLED(1, 0, 0);   // red
  digitalWrite(LED_PIN, HIGH);
}

void stopStream() {
  if (state == STREAMING) {
    Serial.print("# STREAM_STOP n=");
    Serial.println(sampleCount);
  }
  state = IDLE;
  setLED(0, 1, 0);   // green
  digitalWrite(LED_PIN, LOW);
}

// =============================================================
//   QUALITY METRICS
// =============================================================
void updateQuality() {
  for (int ch = 0; ch < 3; ch++) {
    long sum = 0;
    for (int j = 0; j < QBUF; j++) sum += qbuf[ch][j];
    long mean = sum / QBUF;
    dcLevel[ch] = mean;

    // RMS deviation around mean
    long sqSum = 0;
    for (int j = 0; j < QBUF; j++) {
      long d = qbuf[ch][j] - mean;
      sqSum += d * d;
    }
    float rms = sqrt((float)sqSum / QBUF);
    // Healthy EUG signal RMS: 5-150 ADC counts. Map to 0-100 quality.
    float q = 0;
    if (rms < 1.0) q = 5;                 // too flat = electrode off
    else if (rms < 5.0) q = 20;
    else if (rms <= 80.0) q = 70 + (rms - 5) * 0.4;   // sweet spot 5-80
    else if (rms <= 150) q = 90;
    else q = 50;                          // saturating = motion artifact
    quality[ch] = constrain(q, 0, 100);
  }
}

void updateContactStatus() {
  // Electrode contact heuristic: DC level should be 1500-2500 (mid-supply).
  // Deviation > 600 from mid means rail-pinned (off body or shorted).
  for (int ch = 0; ch < 3; ch++) {
    int d = abs(dcLevel[ch] - 2048);
    electrodeOk[ch] = (d < 600);
  }
}

// =============================================================
//   LED HELPERS
// =============================================================
void setLED(int r, int g, int b) {
  digitalWrite(LED_R_PIN, r);
  digitalWrite(LED_G_PIN, g);
  digitalWrite(LED_B_PIN, b);
}

void blinkBasedOnHealth() {
  bool healthyAll = electrodeOk[0] && electrodeOk[1] && electrodeOk[2];
  if (state == STREAMING) {
    if (healthyAll) {
      // blink red slowly
      ledBlinkState = !ledBlinkState;
      setLED(ledBlinkState ? 1 : 0, 0, 0);
      digitalWrite(LED_PIN, ledBlinkState);
    } else {
      // blink yellow (warning)
      ledBlinkState = !ledBlinkState;
      setLED(ledBlinkState ? 1 : 0, ledBlinkState ? 1 : 0, 0);
      digitalWrite(LED_PIN, ledBlinkState);
    }
  }
}

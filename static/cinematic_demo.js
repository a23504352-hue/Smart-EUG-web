/* ============================================================
   🎬 CINEMATIC MALAIKA v2 - INTERACTIVE DEMO PLAYER
   Produces a gorgeous, auto-playing video mockup simulator
   ============================================================ */

function startCinematicDemo() {
  // Prevent duplicate players
  if (document.getElementById('cinemaOver')) return;

  const overlay = document.createElement('div');
  overlay.id = 'cinemaOver';
  overlay.style = `
    position: fixed; inset: 0; background: rgba(8, 4, 15, 0.96);
    z-index: 10000; display: flex; align-items: center; justify-content: center;
    font-family: 'Inter', -apple-system, sans-serif; color: #fce7f3; opacity: 0;
    transition: opacity 0.5s cubic-bezier(0.16, 1, 0.3, 1);
  `;

  overlay.innerHTML = `
    <div id="cinemaWrapper" style="
      width: 90vw; max-width: 1100px; background: #0f0a1d; border-radius: 24px;
      border: 1px solid rgba(236, 72, 153, 0.25); box-shadow: 0 25px 60px rgba(0,0,0,0.8);
      overflow: hidden; display: flex; flex-direction: column; height: 80vh; max-height: 700px;
      transform: scale(0.9) translateY(30px); transition: all 0.5s cubic-bezier(0.16, 1, 0.3, 1);
    ">
      <!-- Header -->
      <div style="padding: 18px 24px; background: #150f29; border-bottom: 1px solid rgba(236,72,153,0.15); display: flex; justify-content: space-between; align-items: center;">
        <div style="display: flex; align-items: center; gap: 10px;">
          <div style="width: 10px; height: 10px; background: #ef4444; border-radius: 50%; animation: redBlink 1.2s infinite;"></div>
          <span style="font-weight: 800; font-size: 0.85rem; letter-spacing: 1px; color:#f472b6;">REC LIVE DEMO</span>
        </div>
        <div style="font-weight: 700; font-size: 1.05rem; letter-spacing: -0.5px; background: linear-gradient(135deg, #f9a8d4 0%, #ec4899 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">SMART EUG · Cinematic Walkthrough</div>
        <button onclick="closeCinematicDemo()" style="background: none; border: none; color: #ec4899; cursor: pointer; transition: transform 0.2s ease;">
          <svg style="width: 24px; height: 24px;" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
        </button>
      </div>

      <!-- TV Screen View Area -->
      <div style="flex: 1; position: relative; background: #07040f; display: flex; align-items: center; justify-content: center; overflow: hidden; padding: 20px;">
        <!-- Interactive Simulated Window Frame -->
        <div id="simulatedScreen" style="
          width: 100%; height: 100%; border-radius: 14px; background: #0b0713; 
          border: 1px solid rgba(255,255,255,0.06); box-shadow: inset 0 2px 20px rgba(0,0,0,0.9);
          position: relative; display: flex; flex-direction: column; overflow: hidden;
        ">
          <!-- Browser Mockup Title Bar -->
          <div style="height: 32px; background: #130d22; border-bottom: 1px solid rgba(255,255,255,0.04); display: flex; align-items: center; padding: 0 16px; gap: 8px;">
            <div style="width: 8px; height: 8px; border-radius: 50%; background: #ef4444; opacity: 0.7;"></div>
            <div style="width: 8px; height: 8px; border-radius: 50%; background: #f59e0b; opacity: 0.7;"></div>
            <div style="width: 8px; height: 8px; border-radius: 50%; background: #10b981; opacity: 0.7;"></div>
            <div id="simulatedURL" style="margin-left: 12px; font-size: 0.74rem; color: #7a6680; font-family: monospace;">http://localhost:8000/live_recording</div>
          </div>

          <!-- Active Simulated Scene Render Container -->
          <div id="activeScene" style="flex: 1; padding: 24px; display: flex; flex-direction: column; justify-content: center; position: relative; overflow-y: auto;">
            <!-- Content will be dynamically animated here -->
          </div>
        </div>

        <!-- Cinema Scanlines Overlay -->
        <div style="position: absolute; inset: 0; pointer-events: none; background: linear-gradient(rgba(18, 16, 26, 0) 50%, rgba(0, 0, 0, 0.15) 50%), linear-gradient(90deg, rgba(236, 72, 153, 0.01), rgba(168, 85, 247, 0.02)); background-size: 100% 4px, 6px 100%;"></div>
      </div>

      <!-- Subtitle Narration Bar -->
      <div style="padding: 24px; background: #0b0713; border-top: 1px solid rgba(236,72,153,0.12); display: flex; flex-direction: column; gap: 8px; align-items: center; text-align: center;">
        <div id="cinemaNarration" style="font-size: 1.15rem; font-weight: 600; line-height: 1.5; min-height: 54px; color: #fdf2f8; text-shadow: 0 2px 8px rgba(236,72,153,0.3); max-width: 820px;">
          Initializing Smart EUG Cinematic Demonstration...
        </div>
        
        <!-- Audio Waves Simulator -->
        <div id="waveVisualizer" style="display: flex; gap: 4px; height: 20px; align-items: center;">
          <div class="audioWaveBar" style="width: 3px; height: 10px; background: #ec4899; border-radius: 2px;"></div>
          <div class="audioWaveBar" style="width: 3px; height: 24px; background: #f9a8d4; border-radius: 2px;"></div>
          <div class="audioWaveBar" style="width: 3px; height: 14px; background: #ec4899; border-radius: 2px;"></div>
          <div class="audioWaveBar" style="width: 3px; height: 28px; background: #fdf2f8; border-radius: 2px;"></div>
          <div class="audioWaveBar" style="width: 3px; height: 16px; background: #be185d; border-radius: 2px;"></div>
          <div class="audioWaveBar" style="width: 3px; height: 8px; background: #ec4899; border-radius: 2px;"></div>
          <div class="audioWaveBar" style="width: 3px; height: 18px; background: #8b5cf6; border-radius: 2px;"></div>
          <div class="audioWaveBar" style="width: 3px; height: 5px; background: #14b8a6; border-radius: 2px;"></div>
        </div>
      </div>

      <!-- Video Control Bar (Timeline + Buttons) -->
      <div style="padding: 12px 24px; background: #0c0817; border-top: 1px solid rgba(236,72,153,0.1); display: flex; gap: 16px; align-items: center;">
        <button id="cinemaPlayBtn" onclick="toggleCinemaPause()" style="background: none; border: none; color: #ec4899; cursor: pointer; display: flex; align-items: center; justify-content: center; width: 32px; height: 32px; border-radius: 50%; hover: background: rgba(255,255,255,0.05)">
          <svg style="width: 20px; height: 20px;" fill="currentColor" viewBox="0 0 24 24"><path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/></svg>
        </button>
        <span id="cinemaTimeCode" style="font-family: monospace; font-size: 0.82rem; color: #a78aa8; min-width: 44px;">0:00</span>
        <div style="flex: 1; height: 6px; background: rgba(255,255,255,0.08); border-radius: 99px; position: relative;">
          <div id="cinemaTimelineFill" style="position: absolute; left: 0; top: 0; bottom: 0; width: 0%; background: linear-gradient(90deg, #ec4899, #f9a8d4); border-radius: 99px; transition: width 0.2s linear;"></div>
        </div>
        <span style="font-family: monospace; font-size: 0.82rem; color: #a78aa8;">0:42</span>
      </div>
    </div>

    <style>
      @keyframes redBlink {
        0%, 100% { opacity: 0.2; transform: scale(0.9); }
        50% { opacity: 1; transform: scale(1.1); box-shadow: 0 0 10px #ef4444; }
      }
      .audioWaveBar {
        animation: wavePulse 0.9s ease-in-out infinite alternate;
      }
      .audioWaveBar:nth-child(2) { animation-delay: 0.15s; }
      .audioWaveBar:nth-child(3) { animation-delay: 0.3s; }
      .audioWaveBar:nth-child(4) { animation-delay: 0.08s; }
      .audioWaveBar:nth-child(5) { animation-delay: 0.45s; }
      .audioWaveBar:nth-child(6) { animation-delay: 0.2s; }
      .audioWaveBar:nth-child(7) { animation-delay: 0.5s; }
      .audioWaveBar:nth-child(8) { animation-delay: 0.1s; }
      @keyframes wavePulse {
        0% { transform: scaleY(0.35); }
        100% { transform: scaleY(1.4); }
      }
    </style>
  `;

  document.body.appendChild(overlay);

  // Trigger animation fade in
  setTimeout(() => {
    overlay.style.opacity = '1';
    document.getElementById('cinemaWrapper').style.transform = 'scale(1) translateY(0)';
  }, 10);

  // Start Cinema Run Loops
  runCinemaSimulator();
}

function closeCinematicDemo() {
  const overlay = document.getElementById('cinemaOver');
  if (!overlay) return;
  
  if (window.cinemaInterval) clearInterval(window.cinemaInterval);
  if (window.cinemaStepTimeout) clearTimeout(window.cinemaStepTimeout);
  if (window.waveformAnimateTimer) cancelAnimationFrame(window.waveformAnimateTimer);

  overlay.style.opacity = '0';
  document.getElementById('cinemaWrapper').style.transform = 'scale(0.9) translateY(20px)';
  setTimeout(() => {
    overlay.remove();
  }, 500);
}

let cinemaIsPaused = false;
function toggleCinemaPause() {
  cinemaIsPaused = !cinemaIsPaused;
  const btn = document.getElementById('cinemaPlayBtn');
  if (cinemaIsPaused) {
    btn.innerHTML = `<svg style="width: 20px; height: 20px;" fill="currentColor" viewBox="0 0 24 24"><polygon points="5 3 19 12 5 21 5 3"/></svg>`;
    const bars = document.querySelectorAll('.audioWaveBar');
    bars.forEach(b => b.style.animationPlayState = 'paused');
  } else {
    btn.innerHTML = `<svg style="width: 20px; height: 20px;" fill="currentColor" viewBox="0 0 24 24"><path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/></svg>`;
    const bars = document.querySelectorAll('.audioWaveBar');
    bars.forEach(b => b.style.animationPlayState = 'running');
  }
}

// Cinematic Scenario Engine
function runCinemaSimulator() {
  let timeInSeconds = 0;
  const duration = 42; // Perfect length: 42 seconds of beautiful action

  window.cinemaInterval = setInterval(() => {
    if (cinemaIsPaused) return;
    timeInSeconds += 1;
    if (timeInSeconds > duration) {
      clearInterval(window.cinemaInterval);
      closeCinematicDemo();
      return;
    }

    const prc = (timeInSeconds / duration) * 100;
    const tf = document.getElementById('cinemaTimelineFill');
    if (tf) tf.style.width = `${prc}%`;

    const tc = document.getElementById('cinemaTimeCode');
    if (tc) {
      const min = Math.floor(timeInSeconds / 60);
      const sec = timeInSeconds % 60;
      tc.innerText = `${min}:${sec < 10 ? '0' + sec : sec}`;
    }
  }, 1000);

  // Scene Configuration Map
  const scenes = [
    {
      time: 0,
      url: 'http://localhost:8000/',
      narrate: "Smart EUG is an AI cycle tracking and Electrouterography (EUG) health assistant designed to secure clinical patient metrics offline.",
      action: () => showIntroScene()
    },
    {
      time: 6,
      url: 'http://localhost:8000/live_recording',
      narrate: "To start streaming signals, Smart EUG executes a Python backend check to discover local maternal sensor boards...",
      action: () => showLoadingHardwareScene()
    },
    {
      time: 12,
      url: 'http://localhost:8000/live_recording',
      narrate: "Bridge setup completed! 3 distinct physical input channels detected on Serial COM3 at 115200 baud.",
      action: () => showHardwareConnectedScene()
    },
    {
      time: 18,
      url: 'http://localhost:8000/live_recording',
      narrate: "Telemetry runs dynamically inside high-performance responsive oscilloscopes. Rhythmic peak parameters are logged with millimeter precision.",
      action: () => showLiveWaveformRecordingScene()
    },
    {
      time: 25,
      url: 'http://localhost:8000/result',
      narrate: "Now calculating! When data stops, scipy signal models decompose curves into 14 biometric variables, assessing uterine contractility phases.",
      action: () => showMLFeatureCalculationScene()
    },
    {
      time: 32,
      url: 'http://localhost:8000/chat',
      narrate: "Let's explore AI. Smart EUG runs offline models locally. A user can write natural medical questions and receive clinical-grade insights securely.",
      action: () => showAIExplanationScene()
    },
    {
      time: 38,
      url: 'http://localhost:8000/dashboard',
      narrate: "And that's Smart EUG. Seamless telemetry calculations, offline AI consultations, and elegant dashboards built for the future.",
      action: () => showAICallbackFinishedScene()
    }
  ];

  function runNextSceneCheck(index) {
    if (index >= scenes.length) return;
    
    const sc = scenes[index];
    const delay = index === 0 ? 0 : (sc.time - scenes[index - 1].time) * 1000;

    window.cinemaStepTimeout = setTimeout(() => {
      // If paused, stall the timeout iteration loop
      if (cinemaIsPaused) {
        clearTimeout(window.cinemaStepTimeout);
        setTimeout(() => runNextSceneCheck(index), 300);
        return;
      }

      // Update URL Mockup
      const urlel = document.getElementById('simulatedURL');
      if (urlel) urlel.innerText = sc.url;

      // Update Subtitle
      const nar = document.getElementById('cinemaNarration');
      if (nar) {
        nar.style.opacity = '0';
        nar.style.transform = 'translateY(5px)';
        setTimeout(() => {
          nar.innerText = sc.narrate;
          nar.style.opacity = '1';
          nar.style.transform = 'translateY(0)';
        }, 150);
      }

      // Trigger Visuals
      sc.action();

      // Recurse next state
      runNextSceneCheck(index + 1);

    }, delay);
  }

  // Kick off first scene immediately
  runNextSceneCheck(0);
}

/* ==============================================
   🎬 VISUAL RENDERS FOR EACH INDIVIDUAL SCENE
   ============================================== */

function showIntroScene() {
  const cn = document.getElementById('activeScene');
  if (!cn) return;
  cn.style.display = 'flex';
  cn.style.justifyContent = 'center';
  cn.style.alignItems = 'center';
  cn.innerHTML = `
    <div style="text-align: center; animation: cdSlideIn .6s cubic-bezier(0.16, 1, 0.3, 1) forwards; max-width: 500px; padding: 20px;">
      <div style="
        width: 90px; height: 90px; border-radius: 24px; background: linear-gradient(135deg, #ec4899, #be185d);
        display: flex; align-items: center; justify-content: center; font-size: 3rem; font-weight: 900;
        color: white; margin: 0 auto 20px; box-shadow: 0 10px 45px rgba(236,72,153,0.35);
        animation: cdBreathLogo 3s infinite ease-in-out;
      ">M</div>
      <h2 style="font-size: 2.1rem; font-weight: 800; letter-spacing: -1.2px; margin-bottom: 8px; color: #fce7f3; font-family: 'SF Pro Display', sans-serif;">SMART <span style="background: linear-gradient(135deg, #f9a8d4, #ec4899); -webkit-background-clip:text; -webkit-text-fill-color:transparent;">EUG</span></h2>
      <p style="font-size: 1.02rem; color: #a78aa8; line-height: 1.5;">Smart EUG AI Health Companion & 3-Channel Telemetry System.</p>
    </div>
    <style>
      @keyframes cdBreathLogo {
        0%, 100% { transform: scale(1); box-shadow: 0 10px 45px rgba(236,72,153,0.35); }
        50% { transform: scale(1.06); box-shadow: 0 15px 50px rgba(236,72,153,0.55); }
      }
      @keyframes cdSlideIn {
        from { opacity: 0; transform: translateY(15px); }
        to { opacity: 1; transform: translateY(0); }
      }
    </style>
  `;
}

function showLoadingHardwareScene() {
  const cn = document.getElementById('activeScene');
  if (!cn) return;
  cn.style.display = 'flex';
  cn.style.justifyContent = 'center';
  cn.style.alignItems = 'center';
  cn.innerHTML = `
    <div style="text-align:center; padding: 20px; animation: cdSlideIn .5s ease forwards;">
      <div style="position:relative; width: 64px; height: 64px; margin: 0 auto 20px;">
        <div style="position:absolute; inset: 0; border: 4px solid rgba(236,72,153,0.1); border-radius: 50%;"></div>
        <div style="position:absolute; inset: 0; border: 4px solid transparent; border-top-color: #ec4899; border-radius: 50%; animation: cdSpin 0.9s linear infinite;"></div>
      </div>
      <h3 style="font-size: 1.15rem; font-weight: 700; margin-bottom: 6px; color: #fdf2f8;">Connecting Hardware Device</h3>
      <p style="font-size:0.8rem; color:#7a6680; font-family:monospace; background: rgba(0,0,0,0.4); padding: 8px 12px; border-radius: 8px; border:1px solid rgba(255,255,255,0.03)">pyserial: Scanning active COM Ports...</p>
    </div>
    <style>
      @keyframes cdSpin { to { transform: rotate(360deg); } }
    </style>
  `;
}

function showHardwareConnectedScene() {
  const cn = document.getElementById('activeScene');
  if (!cn) return;
  cn.style.display = 'flex';
  cn.style.justifyContent = 'center';
  cn.style.alignItems = 'center';
  cn.innerHTML = `
    <div style="text-align:center; padding: 20px; animation: cdSlideIn .5s ease forwards;">
      <div style="
        width: 64px; height: 64px; border-radius: 50%; background: rgba(16, 185, 129, 0.1); border: 2px solid #10b981;
        display: flex; align-items: center; justify-content: center; margin: 0 auto 20px;
        box-shadow: 0 0 20px rgba(16,185,129,0.3); animation: cdPopScale .3s ease;
      ">
        <svg style="width: 28px; height: 28px; color: #10b981;" fill="none" stroke="currentColor" stroke-width="3" viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg>
      </div>
      <h3 style="font-size: 1.15rem; font-weight: 700; margin-bottom: 6px; color: #10b981;">ESP32 Bridge Connected</h3>
      <p style="font-size:0.8rem; color:#a78aa8; font-family:monospace;">Port: COM3 - BaudRate: 115200 - Voltage: 3.3V</p>
    </div>
    <style>
      @keyframes cdPopScale {
        0% { transform: scale(0.6); }
        80% { transform: scale(1.15); }
        100% { transform: scale(1); }
      }
    </style>
  `;
}

function showLiveWaveformRecordingScene() {
  const cn = document.getElementById('activeScene');
  if (!cn) return;
  
  cn.style.display = 'grid';
  cn.style.gridTemplateColumns = '1.3fr 1fr';
  cn.style.gap = '16px';
  cn.style.alignContent = 'center';
  cn.style.alignItems = 'center';
  
  cn.innerHTML = `
    <div style="display:flex; flex-direction:column; gap: 8px;">
      <h3 style="font-size: 0.85rem; font-weight: 800; display:flex; align-items:center; gap:6px; color:#fce7f3; letter-spacing: 0.5px;">
        <span style="display:inline-block; width:8px; height:8px; border-radius:50%; background:#ef4444; animation:redBlink 1s infinite;"></span>
        EUG LIVE CHANNELS
      </h3>
      
      <!-- Oscilloscopes -->
      <div style="display:flex; flex-direction:column; gap: 6px;">
        ${['Channel 1 - L_OP1', 'Channel 2 - M_OP2', 'Channel 3 - R_OP3'].map((ch, idx) => `
          <div style="background:#04020a; border: 1px solid rgba(255,255,255,0.04); border-radius:6px; padding: 6px; position:relative;">
            <div style="font-size:0.62rem; color:#a78aa8; display:flex; justify-content:space-between; margin-bottom:2px; font-family: monospace;">
              <span>${ch}</span>
              <span id="telVal${idx}" style="font-weight:700; color:#cbd5e1;">2100 mV</span>
            </div>
            <canvas id="telCanvas${idx}" style="width:100%; height:32px; background:#010003; border-radius:4px; display:block;"></canvas>
          </div>
        `).join('')}
      </div>
    </div>
    
    <div style="background: #11091e; border: 1px solid rgba(236,72,153,0.15); border-radius: 12px; padding: 14px; display:flex; flex-direction:column; gap: 10px; height:100%; justify-content:space-between;">
      <div style="font-size:0.65rem; color:#f472b6; font-weight:700; letter-spacing:1px; text-transform:uppercase;">Signal Health Monitoring</div>
      
      <div>
        <div style="display:flex; justify-content:space-between; font-size:0.72rem; margin-bottom:2px;">
          <span>Skin impedance score</span>
          <span style="color:#10b981; font-weight:700;">97%</span>
        </div>
        <div style="height:4px; background:rgba(255,255,255,0.06); border-radius:2px; overflow:hidden;">
          <div style="width:97%; height:100%; background:#10b981;"></div>
        </div>
      </div>
      
      <div style="display:flex; justify-content:space-between; align-items:center; border-top:1px solid rgba(255,255,255,0.04); padding-top:8px;">
        <span style="font-size:0.75rem; color:#a78aa8;">Hardware Clock</span>
        <span style="font-family:monospace; font-size:0.75rem; background:rgba(0,0,0,0.3); padding:2px 6px; border-radius:4px;">16.0 MHz</span>
      </div>
      
      <button class="btn btn-record btn-sm" style="background:linear-gradient(135deg,#ef4444,#dc2626); font-weight:700; padding:8px; font-size:0.75rem;">
        STOP SCANNING
      </button>
    </div>
  `;

  const canvases = [
    document.getElementById('telCanvas0'),
    document.getElementById('telCanvas1'),
    document.getElementById('telCanvas2')
  ];
  const contexts = canvases.map(c => c ? c.getContext('2d') : null);
  let frame = 0;
  const history = [Array(160).fill(1000), Array(160).fill(1000), Array(160).fill(1000)];

  function animateWaveforms() {
    if (!document.getElementById('telCanvas0')) return;
    if (cinemaIsPaused) {
      window.waveformAnimateTimer = requestAnimationFrame(animateWaveforms);
      return;
    }
    frame++;
    canvases.forEach((c, idx) => {
      const ctx = contexts[idx];
      if (!ctx || !c) return;
      const w = c.width = c.offsetWidth;
      const h = c.height = c.offsetHeight;
      const pulse = Math.sin(frame * 0.12 - idx*1.5) * 8;
      const noise = (Math.random() - 0.5) * 4;
      const wave = 1200 + pulse + noise;
      const valLabel = document.getElementById(`telVal${idx}`);
      if (valLabel) valLabel.innerText = `${Math.round(wave)} mV`;
      history[idx].unshift(wave);
      if (history[idx].length > w) history[idx].pop();
      ctx.clearRect(0, 0, w, h);
      ctx.strokeStyle = idx === 0 ? 'rgba(236,72,153,0.15)' : idx === 1 ? 'rgba(139,92,246,0.15)' : 'rgba(20,184,166,0.15)';
      ctx.lineWidth = 1;
      for (let i = 0; i < h; i += 8) {
        ctx.beginPath(); ctx.moveTo(0, i); ctx.lineTo(w, i); ctx.stroke();
      }
      ctx.strokeStyle = idx === 0 ? '#ec4899' : idx === 1 ? '#8b5cf6' : '#14b8a6';
      ctx.lineWidth = 1.6;
      ctx.beginPath();
      for (let i = 0; i < history[idx].length; i++) {
        const x = w - i;
        const norm = (history[idx][i] - 900) / 600;
        const y = h - (norm * h);
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      }
      ctx.stroke();
    });
    window.waveformAnimateTimer = requestAnimationFrame(animateWaveforms);
  }
  animateWaveforms();
}

function showMLFeatureCalculationScene() {
  const cn = document.getElementById('activeScene');
  if (!cn) return;
  if (window.waveformAnimateTimer) cancelAnimationFrame(window.waveformAnimateTimer);
  cn.style.display = 'flex';
  cn.style.flexDirection = 'column';
  cn.style.justifyContent = 'center';
  cn.innerHTML = `
    <div style="width:100%; animation: cdSlideIn .4s ease forwards;">
      <h3 style="font-size:1.05rem; font-weight:800; margin-bottom:14px; text-align:center; color:#fdf2f8;">Decomposing Signal Parameters</h3>
      <div style="display:flex; flex-direction:column; gap:8px; max-width:380px; margin: 0 auto; width:100%;">
        ${[
          {name: 'Uterine Power Spectral (PSD)'},
          {name: 'Signal Root Mean Square (RMS)'},
          {name: 'Contraction Waveform Rate'}
        ].map((feat, idx) => `
          <div id="featCard${idx}" style="background:#130d22; border:1px solid rgba(255,255,255,0.03); border-radius:8px; padding:10px 14px; display:flex; justify-content:space-between; align-items:center; transition:all 0.3s ease;">
            <span style="font-weight:600; font-size:0.8rem; color:#e9d5ff;">${feat.name}</span>
            <span id="featVal${idx}" style="font-family:monospace; font-size:0.8rem; font-weight:700; color:#ec4899; display:flex; align-items:center; gap:6px;">
              <span class="loading" style="width:9px; height:9px; border-width:1.5px; margin:0;"></span>
              Wait
            </span>
          </div>
        `).join('')}
      </div>
    </div>
  `;
  const features = ['4.82 dB/Hz', '0.042 mV', '3.12 Hz'];
  features.forEach((f, i) => {
    setTimeout(() => {
      const card = document.getElementById(`featCard${i}`);
      const val = document.getElementById(`featVal${i}`);
      if (card && val) {
        card.style.borderColor = 'rgba(16, 185, 129, 0.2)';
        val.style.color = '#10b981';
        val.innerHTML = f;
      }
    }, (i + 1) * 1600);
  });
}

function showAIExplanationScene() {
  const cn = document.getElementById('activeScene');
  if (!cn) return;
  cn.style.display = 'grid';
  cn.style.gridTemplateColumns = '1fr 1fr';
  cn.style.gap = '14px';
  cn.style.alignContent = 'center';
  
  cn.innerHTML = `
    <div style="display:flex; flex-direction:column; justify-content:center; text-align:center; background:#140d21; border-radius:10px; border:1px solid rgba(239, 68, 68, 0.2); padding:16px; height:100%;">
      <div style="font-size:0.62rem; color:#7a6680; font-weight:700; letter-spacing:1px; text-transform:uppercase;">ML VERDICT OUTPUT</div>
      <div style="font-size:1.8rem; font-weight:900; color:#ef4444; margin:6px 0 2px;">PERIOD LIKELY</div>
      <p style="font-size:0.75rem; color:#a78aa8; line-height:1.45;">Signal parameters match healthy uterine contractions during menstrual phases (93.1% match).</p>
    </div>
    
    <div style="display:flex; flex-direction:column; background:#04020a; border:1px solid rgba(255,255,255,0.05); border-radius:10px; height:100%; justify-content:space-between; overflow:hidden;">
      <div style="padding:6px 12px; background:#120c1e; border-bottom:1px solid rgba(255,255,255,0.04); font-size:0.65rem; font-weight:700; color:#f9a8d4;">OFFLINE MEDICAL CHAT</div>
      <div style="padding:10px; display:flex; flex-direction:column; gap:6px; font-size:0.74rem;">
        <div style="background:#ec4899; color:white; align-self:flex-end; padding:6px 10px; border-radius:8px 8px 1px 8px;">What does this mean for me?</div>
        <div id="typeResp" style="background:#150f24; color:#e9d5ff; align-self:flex-start; padding:6px 10px; border-radius:8px 8px 8px 1px; line-height:1.4; max-height:85px; overflow:hidden;"></div>
      </div>
    </div>
  `;

  const fullText = "Current contractions display high cycles consistent with day 2 of menstruation. Ensure proper mechanical rest, high hydration, and heat pad routines.";
  let curText = "";
  let i = 0;
  function type() {
    const el = document.getElementById('typeResp');
    if (!el) return;
    if (cinemaIsPaused) { setTimeout(type, 100); return; }
    if (i < fullText.length) {
      curText += fullText[i];
      el.innerText = curText;
      i++;
      setTimeout(type, 25);
    }
  }
  setTimeout(type, 800);
}

function showAICallbackFinishedScene() {
  const cn = document.getElementById('activeScene');
  if (!cn) return;
  cn.style.display = 'flex';
  cn.style.justifyContent = 'center';
  cn.style.alignItems = 'center';
  cn.innerHTML = `
    <div style="text-align:center; padding: 20px; animation: cdSlideIn .5s cubic-bezier(0.16, 1, 0.3, 1) forwards;">
      <div style="
        width: 60px; height: 60px; border-radius: 50%; background: rgba(236, 72, 153, 0.1); border: 2px solid #ec4899;
        display: flex; align-items: center; justify-content: center; margin: 0 auto 16px;
        box-shadow: 0 0 20px rgba(236,72,153,0.3); animation: cdFinalBreath 2s infinite ease-in-out;
      ">
        <svg style="width: 28px; height: 28px; color: #ec4899;" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
          <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
        </svg>
      </div>
      <h3 style="font-size: 1.25rem; font-weight: 800; margin-bottom: 4px; color:#fdf2f8;">All systems 100% active</h3>
      <p style="font-size:0.86rem; color:#a78aa8; max-width:380px; margin: 0 auto; line-height:1.45;">Offline database logs completely initialized. Ready to process maternal biometric telemetry!</p>
    </div>
    <style>
      @keyframes cdFinalBreath {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.08); box-shadow: 0 0 30px rgba(236,72,153,0.5); }
      }
    </style>
  `;
}

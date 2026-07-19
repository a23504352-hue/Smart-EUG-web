/* ============================================================
   MALAIKA v2 - widgets.js  (shared across all pages)
   Plotly is loaded via <script> tag in each HTML page.
   ============================================================ */

const ICONS = {
  home:'<svg fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>',
  upload:'<svg fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>',
  activity:'<svg fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>',
  heart:'<svg fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>',
  calendar:'<svg fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>',
  history:'<svg fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/><path d="M12 7v5l4 2"/></svg>',
  clipboard:'<svg fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24"><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><rect x="8" y="2" width="8" height="4" rx="1"/></svg>',
  flask:'<svg fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24"><path d="M9 2v6.4a2.6 2.6 0 0 1-.6 1.7L3 18a2 2 0 0 0 1.6 3.2h14.8A2 2 0 0 0 21 18l-5.4-7.9a2.6 2.6 0 0 1-.6-1.7V2"/><line x1="7" y1="2" x2="17" y2="2"/></svg>',
  info:'<svg fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>',
  check:'<svg fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg>',
  x:'<svg fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>',
  refresh:'<svg fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24"><polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/></svg>',
  play:'<svg fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24"><polygon points="5 3 19 12 5 21 5 3"/></svg>',
  square:'<svg fill="currentColor" viewBox="0 0 24 24"><rect x="6" y="6" width="12" height="12" rx="2"/></svg>',
  circle:'<svg fill="currentColor" viewBox="0 0 24 24"><circle cx="12" cy="12" r="6"/></svg>',
  user:'<svg fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>',
  doctor:'<svg fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24"><path d="M12 2L4 7v10c0 5 8 5 8 5s8 0 8-5V7z"/><path d="M9 10h6M12 7v6"/></svg>',
  brain:'<svg fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24"><path d="M9.5 2A2.5 2.5 0 0 1 12 4.5v15a2.5 2.5 0 0 1-4.96.44 2.5 2.5 0 0 1-2.96-3.08 3 3 0 0 1-.34-5.58 2.5 2.5 0 0 1 1.32-4.24 2.5 2.5 0 0 1 4.44-1.04Z"/><path d="M14.5 2A2.5 2.5 0 0 0 12 4.5v15a2.5 2.5 0 0 0 4.96.44 2.5 2.5 0 0 0 2.96-3.08 3 3 0 0 0 .34-5.58 2.5 2.5 0 0 0-1.32-4.24 2.5 2.5 0 0 0-4.44-1.04Z"/></svg>',
  droplet:'<svg fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24"><path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z"/></svg>',
  moon:'<svg fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>',
  sun:'<svg fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/></svg>',
  apple:'<svg fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24"><path d="M12 20.94c1.5 0 2.75 1.06 4 1.06 3 0 6-8 6-12.22A4.91 4.91 0 0 0 17 5c-2.22 0-4 1.44-5 2-1-.56-2.78-2-5-2a4.9 4.9 0 0 0-5 4.78C2 14 5 22 8 22c1.25 0 2.5-1.06 4-1.06z"/></svg>',
  trending:'<svg fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/></svg>',
  zap:'<svg fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>',
  award:'<svg fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24"><circle cx="12" cy="8" r="7"/><polyline points="8.21 13.89 7 23 12 20 17 23 15.79 13.88"/></svg>',
  book:'<svg fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>',
  message:'<svg fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>',
  layers:'<svg fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24"><polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/></svg>',
  send:'<svg fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>',
  download:'<svg fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>',
  print:'<svg fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24"><polyline points="6 9 6 2 18 2 18 9"/><path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/><rect x="6" y="14" width="12" height="8"/></svg>',
};

function icon(name){return ICONS[name]||'';}

function mountShell(active){
  if (document.querySelector('.app-shell')) return;
  const shell = document.createElement('div');
  shell.className='app-shell';
  shell.innerHTML = `
    <aside class="sidebar">
      <div class="sidebar-brand">
        <div class="logo">M</div>
        <div class="name">SMART EUG<small>AI Uterine Health</small></div>
      </div>
      <!-- CINEMATIC PRESENTATION ACTION -->
      <a href="javascript:void(0)" onclick="startCinematicDemo()" class="nav-item" style="background: linear-gradient(135deg, rgba(236, 72, 153, 0.12) 0%, rgba(139, 92, 246, 0.08) 100%); border: 1px solid rgba(236, 72, 153, 0.3); color: var(--pink-dark); font-weight: 700; margin: 4px 10px 14px; box-shadow: 0 4px 12px rgba(236, 72, 153, 0.08); text-align: center; justify-content: center; border-radius: 12px;">
        <span class="icon" style="margin-right:2px; color:#ec4899;">🎬</span>
        Play Demo Video
      </a>
      <div id="cinemaScriptContainer"></div>
      <script>
        if (!document.getElementById('cinemaDemoScript')) {
          const script = document.createElement('script');
          script.id = 'cinemaDemoScript';
          script.src = '/static/cinematic_demo.js';
          document.body.appendChild(script);
        }
      </script>

      <div class="sidebar-section">Patient</div>
      <a href="/" class="nav-item ${active==='home'?'active':''}"><span class="icon">${icon('home')}</span>Home</a>
      <a href="/live" class="nav-item ${active==='live'?'active':''}"><span class="icon">${icon('activity')}</span>Live recording</a>
      <a href="/upload" class="nav-item ${active==='upload'?'active':''}"><span class="icon">${icon('upload')}</span>Upload file</a>
      <a href="/insights" class="nav-item ${active==='insights'?'active':''}"><span class="icon">${icon('trending')}</span>EUG insights</a>
      <a href="/comparison" class="nav-item ${active==='comparison'?'active':''}"><span class="icon">${icon('layers')}</span>Compare</a>
      <a href="/dashboard" class="nav-item ${active==='dashboard'?'active':''}"><span class="icon">${icon('clipboard')}</span>My dashboard</a>
      <a href="/calendar_view" class="nav-item ${active==='calendar'?'active':''}"><span class="icon">${icon('calendar')}</span>Cycle calendar</a>
      <a href="/wellness" class="nav-item ${active==='wellness'?'active':''}"><span class="icon">${icon('heart')}</span>Wellness</a>
      <a href="/diary" class="nav-item ${active==='diary'?'active':''}"><span class="icon">${icon('book')}</span>Diary</a>
      <a href="/chat" class="nav-item ${active==='chat'?'active':''}"><span class="icon">${icon('message')}</span>AI Chat</a>
      <a href="/history" class="nav-item ${active==='history'?'active':''}"><span class="icon">${icon('history')}</span>History</a>
      <div class="sidebar-section">Doctor</div>
      <a href="/results" class="nav-item ${active==='results'?'active':''}"><span class="icon">${icon('trending')}</span>Model performance</a>
      <a href="/anatomy" class="nav-item ${active==='anatomy'?'active':''}"><span class="icon">${icon('heart')}</span>3D anatomy</a>
      <a href="/science" class="nav-item ${active==='science'?'active':''}"><span class="icon">${icon('flask')}</span>Scientific basis</a>
      <a href="/about" class="nav-item ${active==='about'?'active':''}"><span class="icon">${icon('info')}</span>About</a>
      <div class="sidebar-footer">v2 · GradientBoosting<br>AUC 0.93</div>
    </aside>
    <main class="main" id="main"></main>`;
  document.body.insertBefore(shell, document.body.firstChild);
  const main = document.getElementById('main');
  while (document.body.children.length > 1){
    if (document.body.children[1] === shell) break;
    main.appendChild(document.body.children[1]);
  }
  // Theme toggle button
  if (!document.querySelector('.theme-toggle')){
    const btn = document.createElement('button');
    btn.className='theme-toggle';
    btn.innerHTML = icon('moon');
    btn.title = 'Toggle dark mode';
    btn.onclick = toggleTheme;
    document.body.appendChild(btn);
  }
  applyStoredTheme();
}

function toggleTheme(){
  const cur = document.documentElement.getAttribute('data-theme') || 'light';
  const next = cur === 'light' ? 'dark' : 'light';
  document.documentElement.setAttribute('data-theme', next);
  localStorage.setItem('malaika_theme', next);
  const btn = document.querySelector('.theme-toggle');
  if (btn) btn.innerHTML = icon(next === 'dark' ? 'sun' : 'moon');
}
function applyStoredTheme(){
  const stored = localStorage.getItem('malaika_theme') || 'light';
  document.documentElement.setAttribute('data-theme', stored);
  const btn = document.querySelector('.theme-toggle');
  if (btn) btn.innerHTML = icon(stored === 'dark' ? 'sun' : 'moon');
}

function pageHeader(title, sub, tag){
  return `<div class="page-header">
    <div><h1>${title}</h1><div class="sub">${sub||''}</div></div>
    ${tag?`<span class="page-tag">${tag}</span>`:''}
  </div>`;
}

function kpi(label, num, delta, deltaClass, iconName){
  return `<div class="kpi">
    <div class="kpi-icon">${icon(iconName||'activity')}</div>
    <div class="lbl">${label}</div>
    <div class="num">${num}</div>
    ${delta?`<div class="delta ${deltaClass||''}">${delta}</div>`:''}
  </div>`;
}

function verdictCard(verdict, reason){
  const cls = (verdict||'').replace(/ /g,'-');
  return `<div class="verdict-card verdict-${cls}">
    <div style="font-size:.74rem;color:var(--muted);font-weight:700;letter-spacing:1px;text-transform:uppercase">VERDICT</div>
    <div class="v">${verdict||'PROCESSING'}</div>
    <div class="reason">${reason||''}</div>
  </div>`;
}

function aiExplainCard(patientText, doctorText){
  return `<div class="ai-explain">
    <div class="toggle-view" id="aiViewToggle">
      <button class="active" data-view="patient">${icon('user')} Patient</button>
      <button data-view="doctor">${icon('doctor')} Doctor</button>
    </div>
    <p id="aiExplainText">${patientText||''}</p>
    <p id="aiExplainTextDoc" style="display:none">${doctorText||''}</p>
  </div>`;
}

function setupAiViewToggle(){
  const tg = document.getElementById('aiViewToggle');
  if (!tg) return;
  tg.addEventListener('click', e=>{
    const btn = e.target.closest('button[data-view]');
    if (!btn) return;
    tg.querySelectorAll('button').forEach(b=>b.classList.remove('active'));
    btn.classList.add('active');
    const isPatient = btn.dataset.view === 'patient';
    document.getElementById('aiExplainText').style.display = isPatient ? '' : 'none';
    document.getElementById('aiExplainTextDoc').style.display = isPatient ? 'none' : '';
  });
}

function renderScorecard(elementId, sc){
  const el = document.getElementById(elementId);
  if (!el || !sc) return;
  el.innerHTML = `
    <div style="text-align:center;padding:8px 0 14px;border-bottom:1px solid var(--border);margin-bottom:10px">
      <div style="font-size:2.6rem;font-weight:800;color:var(--pink-dark);letter-spacing:-2px">${sc.score}/100</div>
      <div style="color:var(--muted);font-size:.85rem;font-weight:600">${sc.n_pass} pass · ${sc.n_warn} warn · ${sc.n_fail} fail</div>
    </div>
    <div class="scorecard-checks">
      ${(sc.checks||[]).map(c=>{
        const ic = c.status==='pass'?icon('check'):c.status==='warn'?'!':icon('x');
        return `<div class="check check-${c.status}">
          <div class="check-icon">${ic}</div>
          <div class="check-body"><div class="check-name">${c.name}</div><div class="check-note">${c.note}</div></div>
          <div class="check-value">${c.value}</div>
        </div>`;
      }).join('')}
    </div>`;
}

function timelineStrip(durSec, contractions){
  if (!contractions || !contractions.length) return `<p style="color:var(--muted);padding:14px;text-align:center">No contractions detected.</p>`;
  return `<div class="timeline">
    <div class="timeline-track">
      ${contractions.map(c=>{
        const left=(c.start_sec/durSec)*100;
        const width=((c.end_sec-c.start_sec)/durSec)*100;
        const cls=c.prediction==='PERIOD'?'period':'nonperiod';
        return `<div class="timeline-mark ${cls}" style="left:${left}%;width:${Math.max(width,1.2)}%"
          title="#${c.index} · ${c.prediction} · P=${(c.period_probability*100).toFixed(0)}%">#${c.index}</div>`;
      }).join('')}
    </div>
    <div class="timeline-axis"><span>0:00</span><span>${(durSec/60).toFixed(1)} min</span></div>
  </div>`;
}

function phaseWheel(currentDay){
  currentDay = currentDay || 1;
  const segs = [
    {start:0, end:5, color:'#ef4444'},
    {start:5, end:13, color:'#10b981'},
    {start:13, end:14, color:'#f59e0b'},
    {start:14, end:28, color:'#8b5cf6'},
  ];
  const cx=140, cy=140, r=110, sw=24, ang=360/28;
  let svg = '';
  segs.forEach(s=>{
    const a1=s.start*ang-90, a2=s.end*ang-90;
    const large=(a2-a1)>180?1:0;
    const x1=cx+r*Math.cos(a1*Math.PI/180), y1=cy+r*Math.sin(a1*Math.PI/180);
    const x2=cx+r*Math.cos(a2*Math.PI/180), y2=cy+r*Math.sin(a2*Math.PI/180);
    svg += `<path d="M ${x1} ${y1} A ${r} ${r} 0 ${large} 1 ${x2} ${y2}" stroke="${s.color}" stroke-width="${sw}" fill="none" stroke-linecap="round" opacity="0.85"/>`;
  });
  const ma = currentDay*ang-90;
  const mx = cx+r*Math.cos(ma*Math.PI/180), my = cy+r*Math.sin(ma*Math.PI/180);
  svg += `<circle cx="${mx}" cy="${my}" r="11" fill="white" stroke="var(--pink)" stroke-width="3"/>
          <circle cx="${mx}" cy="${my}" r="5" fill="var(--pink)"/>`;
  let phase='MENSTRUAL';
  if (currentDay>=6 && currentDay<=13) phase='FOLLICULAR';
  else if (currentDay===14) phase='OVULATION';
  else if (currentDay>14) phase='LUTEAL';
  const colors = {MENSTRUAL:'#ef4444',FOLLICULAR:'#10b981',OVULATION:'#f59e0b',LUTEAL:'#8b5cf6'};
  return `<div class="phase-wheel">
    <svg viewBox="0 0 280 280">${svg}</svg>
    <div class="phase-wheel-day">
      <div class="num">${currentDay}</div>
      <div class="lbl">Cycle Day</div>
      <div class="phase" style="color:${colors[phase]}">${phase}</div>
    </div>
  </div>`;
}

function healthRing(elementId, score){
  const el = document.getElementById(elementId);
  if (!el) return;
  score = Math.max(0, Math.min(100, score));
  const r = 80, c = 2*Math.PI*r;
  const offset = c - (score/100)*c;
  const color = score>=80?'#10b981':score>=60?'#f59e0b':score>=40?'#fb923c':'#ef4444';
  el.innerHTML = `
    <div class="health-ring">
      <svg width="200" height="200">
        <circle class="ring-bg" cx="100" cy="100" r="${r}"/>
        <circle class="ring-fg" cx="100" cy="100" r="${r}" stroke="${color}" stroke-dasharray="${c}" stroke-dashoffset="${offset}"/>
      </svg>
      <div class="health-ring-center">
        <div class="score" style="color:${color}">${score}</div>
        <div class="lbl">Health</div>
      </div>
    </div>`;
}

function renderPhaseFeatures(elementId, perFeature, view){
  const el = document.getElementById(elementId);
  if (!el || !perFeature) return;
  const isPatient = (view||'patient') === 'patient';
  el.innerHTML = perFeature.map(pf=>{
    const phaseOrder = ['MENSTRUAL','FOLLICULAR','OVULATION','LUTEAL'];
    return `<div class="phase-feature-card">
      <div class="phase-feature-header">
        <div class="phase-feature-name">${pf.name} <span style="color:var(--muted);font-weight:500;font-size:.82rem">(${isPatient ? pf.patient_label : pf.doctor_label})</span></div>
        <div class="phase-feature-value">${pf.value} ${pf.unit}</div>
      </div>
      <div class="phase-bands">
        ${phaseOrder.map(p=>{
          const ph = pf.phases[p];
          const isMatch = pf.best_phase === p;
          return `<div class="phase-band ${isMatch?'match':''}" style="background:${ph.color}22;color:${ph.color};border-color:${isMatch?ph.color:'transparent'}">
            <span class="ph-name">${p}</span>
            <span class="ph-range">${ph.min} – ${ph.max}</span>
            <small style="opacity:.8">${ph.label}</small>
          </div>`;
        }).join('')}
      </div>
      <div class="phase-feature-explain">
        <strong>${pf.best_phase} match:</strong> ${isPatient ? pf.patient_explanation : pf.doctor_explanation}
      </div>
    </div>`;
  }).join('');
}

/* ----------------- 2D ANATOMICAL UTERUS (canvas) ----------------- */
function drawAnatomicalUterus(canvasId, phase){
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const w = canvas.width = canvas.offsetWidth || 320;
  const h = canvas.height = 320;
  const cx = w/2, cy = h/2 + 20;

  const colors = {
    MENSTRUAL: {body:'#dc2626', glow:'rgba(220,38,38,0.4)'},
    FOLLICULAR:{body:'#10b981', glow:'rgba(16,185,129,0.4)'},
    OVULATION: {body:'#f59e0b', glow:'rgba(245,158,11,0.4)'},
    LUTEAL:    {body:'#8b5cf6', glow:'rgba(139,92,246,0.4)'},
  };
  const c = colors[phase] || colors.MENSTRUAL;

  let breath = 0;
  function draw(){
    breath += 0.05;
    const scale = 1 + Math.sin(breath) * 0.04;
    ctx.clearRect(0,0,w,h);
    ctx.save();
    ctx.translate(cx, cy);
    ctx.scale(scale, scale);

    // glow
    ctx.shadowBlur = 30; ctx.shadowColor = c.glow;

    // uterus body (anatomically shaped pear)
    ctx.beginPath();
    ctx.moveTo(-50, -80);          // top left fundus
    ctx.bezierCurveTo(-60, -60, -68, -30, -65, 0);
    ctx.bezierCurveTo(-62, 30, -45, 55, -25, 65);
    ctx.bezierCurveTo(-15, 75, -10, 90, -8, 100);  // cervix
    ctx.lineTo(8, 100);
    ctx.bezierCurveTo(10, 90, 15, 75, 25, 65);
    ctx.bezierCurveTo(45, 55, 62, 30, 65, 0);
    ctx.bezierCurveTo(68, -30, 60, -60, 50, -80);
    ctx.bezierCurveTo(40, -85, 25, -88, 0, -88);
    ctx.bezierCurveTo(-25, -88, -40, -85, -50, -80);
    ctx.closePath();
    ctx.fillStyle = c.body; ctx.fill();
    ctx.strokeStyle = '#7c2d12'; ctx.lineWidth = 2; ctx.stroke();

    ctx.shadowBlur = 0;

    // fallopian tubes
    for (const side of [-1, 1]){
      ctx.beginPath();
      ctx.moveTo(side*45, -78);
      ctx.bezierCurveTo(side*70, -85, side*100, -75, side*120, -60);
      ctx.lineWidth = 7; ctx.strokeStyle = '#fda4af'; ctx.stroke();
      // ovary
      ctx.beginPath();
      ctx.ellipse(side*125, -55, 14, 10, 0, 0, Math.PI*2);
      ctx.fillStyle = '#fb7185'; ctx.fill();
      ctx.strokeStyle = '#9f1239'; ctx.lineWidth = 1.5; ctx.stroke();
    }

    // cervix
    ctx.beginPath();
    ctx.rect(-10, 95, 20, 25);
    ctx.fillStyle = '#9f1239'; ctx.fill();

    // vaginal canal
    ctx.beginPath();
    ctx.rect(-12, 118, 24, 35);
    ctx.fillStyle = '#fda4af'; ctx.fill();
    ctx.strokeStyle = '#9f1239'; ctx.stroke();

    ctx.restore();

    // phase label
    ctx.font = 'bold 13px Inter, system-ui';
    ctx.fillStyle = c.body;
    ctx.textAlign = 'center';
    ctx.fillText(phase, cx, h - 10);

    requestAnimationFrame(draw);
  }
  draw();
}

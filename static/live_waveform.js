/* ============================================================
   LIVE WAVEFORM SCOPE - 3 channels, scrolling, oscilloscope style
   ============================================================ */
class LiveScope {
  constructor(canvasId, color, label){
    this.canvas = document.getElementById(canvasId);
    if (!this.canvas) return;
    this.ctx = this.canvas.getContext('2d');
    this.color = color || '#ec4899';
    this.label = label || 'CH';
    this.buffer = [];
    this.maxSamples = 1000;   // visible samples
    this.minVal = -200; this.maxVal = 200;  // uV range, auto-adjusts
    this.lastValue = 0;
    this.resize();
    window.addEventListener('resize', () => this.resize());
    this.tick();
  }

  resize(){
    if (!this.canvas) return;
    this.canvas.width = this.canvas.offsetWidth;
    this.canvas.height = 120;
  }

  push(samples){
    for (const s of samples){
      this.buffer.push(s);
      if (this.buffer.length > this.maxSamples) this.buffer.shift();
    }
    if (samples.length) this.lastValue = samples[samples.length - 1];

    // Auto-scale to current data
    if (this.buffer.length > 50){
      const ext = Math.max(...this.buffer.map(Math.abs));
      const target = Math.max(50, ext * 1.3);
      // smooth approach
      this.maxVal = this.maxVal * 0.95 + target * 0.05;
      this.minVal = -this.maxVal;
    }
  }

  setValueLabel(elementId){
    this.valLabelEl = document.getElementById(elementId);
  }

  tick(){
    if (!this.canvas) return;
    const ctx = this.ctx;
    const w = this.canvas.width;
    const h = this.canvas.height;

    ctx.clearRect(0, 0, w, h);

    // grid background
    ctx.fillStyle = '#0a0e1a';
    ctx.fillRect(0, 0, w, h);
    ctx.strokeStyle = 'rgba(34, 197, 94, 0.06)';
    ctx.lineWidth = 1;
    for (let x = 0; x < w; x += 32){
      ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, h); ctx.stroke();
    }
    for (let y = 0; y < h; y += 24){
      ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(w, y); ctx.stroke();
    }
    // mid line
    ctx.strokeStyle = 'rgba(34, 197, 94, 0.15)';
    ctx.beginPath(); ctx.moveTo(0, h/2); ctx.lineTo(w, h/2); ctx.stroke();

    if (this.buffer.length < 2){
      ctx.font = '11px monospace';
      ctx.fillStyle = '#4b5563';
      ctx.textAlign = 'center';
      ctx.fillText('waiting for signal...', w/2, h/2);
      requestAnimationFrame(() => this.tick());
      return;
    }

    // waveform
    const range = this.maxVal - this.minVal;
    ctx.strokeStyle = this.color;
    ctx.lineWidth = 1.6;
    ctx.shadowColor = this.color;
    ctx.shadowBlur = 6;
    ctx.beginPath();
    for (let i = 0; i < this.buffer.length; i++){
      const x = (i / (this.maxSamples - 1)) * w;
      const v = this.buffer[i];
      const y = h - ((v - this.minVal) / range) * h;
      if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    }
    ctx.stroke();
    ctx.shadowBlur = 0;

    // glowing dot at end
    const lastX = ((this.buffer.length - 1) / (this.maxSamples - 1)) * w;
    const lastY = h - ((this.buffer[this.buffer.length - 1] - this.minVal) / range) * h;
    ctx.fillStyle = this.color;
    ctx.shadowColor = this.color; ctx.shadowBlur = 12;
    ctx.beginPath(); ctx.arc(lastX, lastY, 3, 0, Math.PI*2); ctx.fill();
    ctx.shadowBlur = 0;

    if (this.valLabelEl){
      this.valLabelEl.textContent = this.lastValue.toFixed(1) + ' µV';
      this.valLabelEl.style.color = this.color;
    }

    requestAnimationFrame(() => this.tick());
  }
}

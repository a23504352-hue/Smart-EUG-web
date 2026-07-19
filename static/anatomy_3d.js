/* ============================================================
   REAL ANATOMICAL 3D UTERUS + ANIMATED MENSTRUAL CYCLE
   Three.js based. Shows:
   - Anatomically accurate pear-shaped uterus
   - Endometrium layer (visibly thickens/sheds with cycle phase)
   - Ovaries with follicles
   - Fallopian tubes with cilia animation
   - Cervical canal
   - 4 visualization modes for menstruation:
     * SUBTLE: red glow + gentle particles
     * REALISTIC: lining peels off and flows toward cervix
     * EDUCATIONAL: labels with arrows pointing to anatomy
     * AUTO-CYCLE: full 28-day cycle in 30 seconds
   ============================================================ */

class AnatomyUterus {
  constructor(containerId, options) {
    options = options || {};
    this.container = document.getElementById(containerId);
    if (!this.container || !window.THREE) return;

    this.height = options.height || 480;
    this.phase = options.phase || 'MENSTRUAL';
    this.vizMode = options.vizMode || 'SUBTLE';
    this.cyclePlaying = false;
    this.cycleDay = 1;
    this.endometriumThickness = 1.0;
    this.particles = [];
    this.labels = [];

    this.init();
    this.animate();
  }

  init() {
    const w = this.container.offsetWidth;
    const h = this.height;

    this.scene = new THREE.Scene();
    this.scene.background = null;

    this.camera = new THREE.PerspectiveCamera(45, w / h, 0.1, 100);
    this.camera.position.set(0, 0.5, 7.5);

    this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    this.renderer.setSize(w, h);
    this.renderer.setPixelRatio(window.devicePixelRatio);
    this.container.innerHTML = '';
    this.container.appendChild(this.renderer.domElement);

    // Lighting
    this.scene.add(new THREE.AmbientLight(0xffffff, 0.55));
    const k = new THREE.DirectionalLight(0xffffff, 0.85);
    k.position.set(2, 4, 4);
    this.scene.add(k);
    const r = new THREE.DirectionalLight(0xec4899, 0.6);
    r.position.set(-3, 2, -2);
    this.scene.add(r);

    // === Build anatomy ===
    this.buildUterusOuter();
    this.buildEndometrium();
    this.buildOvaries();
    this.buildFallopianTubes();
    this.buildCervix();
    this.buildVagina();

    // === Particle system for menstruation ===
    this.buildParticles();

    // === Drag/zoom controls ===
    this.setupControls();

    window.addEventListener('resize', () => this.onResize());
  }

  buildUterusOuter() {
    // Anatomically pear-shaped uterus body (myometrium = outer muscle layer)
    const points = [];
    for (let i = 0; i < 50; i++) {
      const t = i / 49;
      const y = 2.6 - t * 4.8;
      let radius;
      if (t < 0.08) radius = 0.25 + t * 9.5;            // top fundus widening
      else if (t < 0.20) radius = 1.0 + (t - 0.08) * 1.5; // shoulders
      else if (t < 0.55) radius = 1.18 + Math.sin((t - 0.2) * 9) * 0.25; // body
      else if (t < 0.78) radius = 1.40 - (t - 0.55) * 4.0; // narrowing
      else if (t < 0.92) radius = 0.45 - (t - 0.78) * 1.7; // cervical neck
      else radius = 0.32;                                  // cervix opening
      points.push(new THREE.Vector2(Math.max(radius, 0.15), y));
    }
    const geom = new THREE.LatheGeometry(points, 80);
    this.uterusMat = new THREE.MeshPhongMaterial({
      color: 0xec9aa6,
      shininess: 35,
      specular: 0xffffff,
      transparent: true,
      opacity: 0.42,
      side: THREE.DoubleSide,
    });
    this.uterusOuter = new THREE.Mesh(geom, this.uterusMat);
    this.scene.add(this.uterusOuter);
  }

  buildEndometrium() {
    // Inner layer (the lining that thickens & sheds)
    const points = [];
    for (let i = 0; i < 50; i++) {
      const t = i / 49;
      const y = 2.45 - t * 4.5;
      let radius;
      if (t < 0.10) radius = 0.22 + t * 7;
      else if (t < 0.20) radius = 0.85;
      else if (t < 0.55) radius = 0.95 + Math.sin((t - 0.2) * 9) * 0.15;
      else if (t < 0.78) radius = 1.12 - (t - 0.55) * 3.6;
      else if (t < 0.92) radius = 0.35;
      else radius = 0.22;
      points.push(new THREE.Vector2(Math.max(radius, 0.1), y));
    }
    const geom = new THREE.LatheGeometry(points, 64);
    this.endometriumMat = new THREE.MeshPhongMaterial({
      color: 0xdc2626,
      shininess: 40,
      transparent: true,
      opacity: 0.85,
    });
    this.endometrium = new THREE.Mesh(geom, this.endometriumMat);
    this.scene.add(this.endometrium);
  }

  buildOvaries() {
    this.ovaries = [];
    this.follicles = [];
    for (const side of [-1, 1]) {
      // ovary base
      const ovGeom = new THREE.SphereGeometry(0.32, 32, 24);
      const ovMat = new THREE.MeshPhongMaterial({
        color: 0xfb7185, shininess: 35,
      });
      const ov = new THREE.Mesh(ovGeom, ovMat);
      ov.position.set(side * 2.7, 1.6, 0.1);
      this.scene.add(ov);
      this.ovaries.push(ov);

      // follicles dotting the ovary
      const ovFollicles = [];
      for (let i = 0; i < 4; i++) {
        const fol = new THREE.Mesh(
          new THREE.SphereGeometry(0.06, 12, 8),
          new THREE.MeshPhongMaterial({ color: 0xffffff, transparent: true, opacity: 0.85 }),
        );
        const angle = i * Math.PI / 2 + Math.random() * 0.4;
        const r = 0.32;
        fol.position.set(
          ov.position.x + Math.cos(angle) * r,
          ov.position.y + Math.sin(angle) * r,
          ov.position.z + (Math.random() - 0.5) * 0.4,
        );
        this.scene.add(fol);
        ovFollicles.push(fol);
      }
      this.follicles.push(ovFollicles);
    }
  }

  buildFallopianTubes() {
    this.tubes = [];
    for (const side of [-1, 1]) {
      const curve = new THREE.CatmullRomCurve3([
        new THREE.Vector3(side * 0.85, 1.95, 0.1),
        new THREE.Vector3(side * 1.4, 2.2, 0.3),
        new THREE.Vector3(side * 1.95, 2.3, -0.1),
        new THREE.Vector3(side * 2.4, 2.05, 0.2),
        new THREE.Vector3(side * 2.7, 1.7, 0.12),
      ]);
      const tubeGeom = new THREE.TubeGeometry(curve, 48, 0.10, 16, false);
      const tubeMat = new THREE.MeshPhongMaterial({
        color: 0xfecdd3, shininess: 25,
      });
      this.tubes.push(new THREE.Mesh(tubeGeom, tubeMat));
      this.scene.add(this.tubes[this.tubes.length - 1]);

      // Fimbriae (finger-like ends near ovary)
      for (let i = 0; i < 5; i++) {
        const fim = new THREE.Mesh(
          new THREE.ConeGeometry(0.04, 0.15, 8),
          new THREE.MeshPhongMaterial({ color: 0xfb7185 }),
        );
        const angle = i * 0.4 - 0.8;
        fim.position.set(side * 2.55, 1.85, 0.18);
        fim.rotation.z = side * angle;
        this.scene.add(fim);
      }
    }
  }

  buildCervix() {
    const cervix = new THREE.Mesh(
      new THREE.CylinderGeometry(0.32, 0.38, 0.55, 24),
      new THREE.MeshPhongMaterial({ color: 0x9f1239, shininess: 25 }),
    );
    cervix.position.y = -2.45;
    this.cervix = cervix;
    this.scene.add(cervix);

    // Cervical canal opening
    const canal = new THREE.Mesh(
      new THREE.CylinderGeometry(0.08, 0.08, 0.6, 16),
      new THREE.MeshBasicMaterial({ color: 0x450a0a }),
    );
    canal.position.y = -2.45;
    this.scene.add(canal);
  }

  buildVagina() {
    // Vaginal canal (anatomically correct, simplified)
    const points = [];
    for (let i = 0; i < 12; i++) {
      const t = i / 11;
      const r = 0.42 - t * 0.05;
      points.push(new THREE.Vector2(r, -t * 1.6));
    }
    const geom = new THREE.LatheGeometry(points, 32);
    const mat = new THREE.MeshPhongMaterial({
      color: 0xfda4af, shininess: 25,
      transparent: true, opacity: 0.6,
      side: THREE.DoubleSide,
    });
    this.vagina = new THREE.Mesh(geom, mat);
    this.vagina.position.y = -2.75;
    this.scene.add(this.vagina);
  }

  buildParticles() {
    // Reusable particle pool for menstruation flow
    this.particleGroup = new THREE.Group();
    this.scene.add(this.particleGroup);
    for (let i = 0; i < 30; i++) {
      const p = new THREE.Mesh(
        new THREE.SphereGeometry(0.04, 8, 6),
        new THREE.MeshBasicMaterial({
          color: 0xdc2626, transparent: true, opacity: 0,
        }),
      );
      this.particleGroup.add(p);
      this.particles.push({
        mesh: p, t: Math.random() * 100, active: false,
        startY: 1.5, endY: -3.0, x: 0, z: 0,
      });
    }
  }

  setupControls() {
    this.rotX = 0; this.rotY = 0; this.autoRot = true;
    let isDown = false, lastX = 0, lastY = 0;
    this.container.addEventListener('mousedown', e => {
      isDown = true; this.autoRot = false;
      lastX = e.clientX; lastY = e.clientY;
    });
    window.addEventListener('mouseup', () => isDown = false);
    window.addEventListener('mousemove', e => {
      if (!isDown) return;
      this.rotY += (e.clientX - lastX) * 0.01;
      this.rotX += (e.clientY - lastY) * 0.01;
      lastX = e.clientX; lastY = e.clientY;
    });
    this.container.addEventListener('wheel', e => {
      e.preventDefault();
      this.camera.position.z = Math.max(3.5, Math.min(11, this.camera.position.z + e.deltaY * 0.005));
    }, { passive: false });
  }

  setPhase(phase) {
    this.phase = phase;
    this.applyPhaseVisuals();
  }

  setVizMode(mode) {
    this.vizMode = mode;
    this.applyPhaseVisuals();
  }

  applyPhaseVisuals() {
    // Update endometrium thickness, color, particles based on phase
    const phaseData = {
      MENSTRUAL: { uterusColor: 0xdc2626, endoColor: 0x991b1b, endoOpacity: 0.92, endoScale: 0.35 },
      FOLLICULAR: { uterusColor: 0xfca5a5, endoColor: 0xfee2e2, endoOpacity: 0.65, endoScale: 0.55 },
      OVULATION: { uterusColor: 0xfb923c, endoColor: 0xfdba74, endoOpacity: 0.75, endoScale: 0.85 },
      LUTEAL: { uterusColor: 0xc084fc, endoColor: 0xa855f7, endoOpacity: 0.85, endoScale: 1.0 },
    };
    const d = phaseData[this.phase] || phaseData.MENSTRUAL;
    this.uterusMat.color.setHex(d.uterusColor);
    this.endometriumMat.color.setHex(d.endoColor);
    this.endometriumMat.opacity = d.endoOpacity;
    this.targetEndoScale = d.endoScale;

    // Trigger particles only if MENSTRUAL phase + viz mode supports it
    this.particlesActive = (this.phase === 'MENSTRUAL') &&
      (this.vizMode === 'SUBTLE' || this.vizMode === 'REALISTIC');

    // Educational labels (only in EDUCATIONAL mode)
    this.removeLabels();
    if (this.vizMode === 'EDUCATIONAL') {
      this.addEducationalLabels();
    }
  }

  removeLabels() {
    this.labels.forEach(l => this.scene.remove(l));
    this.labels = [];
  }

  addEducationalLabels() {
    const labels = [
      { text: 'Endometrium\n(uterine lining)', pos: [0, 0.5, 1.3] },
      { text: 'Fallopian tube', pos: [-2.0, 2.5, 0.5] },
      { text: 'Ovary\n(produces eggs)', pos: [2.7, 2.0, 0.5] },
      { text: 'Cervix', pos: [0, -2.45, 1.2] },
    ];
    labels.forEach(l => {
      const sprite = this.makeTextSprite(l.text);
      sprite.position.set(...l.pos);
      sprite.scale.set(2.0, 0.8, 1);
      this.scene.add(sprite);
      this.labels.push(sprite);
    });
  }

  makeTextSprite(text) {
    const canvas = document.createElement('canvas');
    canvas.width = 256; canvas.height = 96;
    const ctx = canvas.getContext('2d');
    ctx.fillStyle = 'rgba(255,255,255,0.95)';
    ctx.strokeStyle = '#ec4899';
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.roundRect(2, 2, 252, 92, 12);
    ctx.fill(); ctx.stroke();
    ctx.fillStyle = '#7c2d12';
    ctx.font = 'bold 22px Inter, sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    const lines = text.split('\n');
    lines.forEach((line, i) => {
      ctx.fillText(line, 128, 48 + (i - (lines.length - 1) / 2) * 26);
    });
    const tex = new THREE.CanvasTexture(canvas);
    const sprite = new THREE.Sprite(new THREE.SpriteMaterial({ map: tex, transparent: true }));
    return sprite;
  }

  startCycleAnimation() {
    this.cyclePlaying = true;
    this.cycleStartTime = performance.now();
  }

  stopCycleAnimation() {
    this.cyclePlaying = false;
  }

  updateCycleAnimation() {
    if (!this.cyclePlaying) return;
    const elapsed = (performance.now() - this.cycleStartTime) / 1000;
    const cycleLen = 30; // 30 sec = 28 days
    const t = (elapsed % cycleLen) / cycleLen;  // 0 -> 1
    const day = Math.floor(t * 28) + 1;
    this.cycleDay = day;

    let phase;
    if (day <= 5) phase = 'MENSTRUAL';
    else if (day <= 13) phase = 'FOLLICULAR';
    else if (day === 14) phase = 'OVULATION';
    else phase = 'LUTEAL';

    if (phase !== this.phase) {
      this.setPhase(phase);
    }

    if (this.cycleDayCallback) this.cycleDayCallback(day, phase);
  }

  onCycleDayChange(callback) {
    this.cycleDayCallback = callback;
  }

  updateParticles() {
    if (!this.particlesActive) {
      this.particles.forEach(p => {
        p.mesh.material.opacity = Math.max(0, p.mesh.material.opacity - 0.02);
      });
      return;
    }

    this.particles.forEach((p, i) => {
      if (!p.active && Math.random() < 0.04) {
        p.active = true;
        p.t = 0;
        p.x = (Math.random() - 0.5) * 0.4;
        p.z = (Math.random() - 0.5) * 0.4;
      }
      if (p.active) {
        p.t += 0.013;
        const y = p.startY - (p.startY - p.endY) * p.t;
        p.mesh.position.set(p.x, y, p.z);
        p.mesh.material.opacity = Math.sin(p.t * Math.PI) * 0.85;
        if (p.t >= 1) p.active = false;
      }
    });
  }

  animate() {
    requestAnimationFrame(() => this.animate());
    if (!this.renderer) return;

    if (this.autoRot) this.rotY += 0.005;
    if (this.uterusOuter) {
      this.uterusOuter.rotation.x = this.rotX;
      this.uterusOuter.rotation.y = this.rotY;
    }
    if (this.endometrium) {
      this.endometrium.rotation.x = this.rotX;
      this.endometrium.rotation.y = this.rotY;
      // smoothly interpolate endometrium scale
      if (this.targetEndoScale !== undefined) {
        const cur = this.endometrium.scale.x;
        const next = cur + (this.targetEndoScale - cur) * 0.05;
        this.endometrium.scale.set(next, 1, next);
      }
    }
    // Subtle pulse
    const t = performance.now() / 1000;
    const pulse = 1 + Math.sin(t * 1.8) * 0.02;
    if (this.uterusOuter) this.uterusOuter.scale.set(pulse, 1, pulse);

    // Spin ovaries
    if (this.ovaries) {
      this.ovaries.forEach((ov, i) => {
        ov.rotation.y += 0.005 * (i % 2 === 0 ? 1 : -1);
      });
    }

    // Show ovulating follicle (during ovulation, brighten one follicle)
    if (this.phase === 'OVULATION' && this.follicles && this.follicles[0]) {
      const f = this.follicles[0][0];
      if (f) {
        f.material.color.setHex(0xfde047);
        f.material.opacity = 0.9 + Math.sin(t * 4) * 0.1;
        f.scale.set(2, 2, 2);
      }
    }

    this.updateCycleAnimation();
    this.updateParticles();

    this.renderer.render(this.scene, this.camera);
  }

  onResize() {
    if (!this.renderer || !this.camera) return;
    const w = this.container.offsetWidth;
    this.renderer.setSize(w, this.height);
    this.camera.aspect = w / this.height;
    this.camera.updateProjectionMatrix();
  }
}

// Global helper - backward compatible
function init3DAnatomyV2(containerId, options) {
  return new AnatomyUterus(containerId, options);
}

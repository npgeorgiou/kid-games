// SECTION: BRUSH CORE -- Krita's pixel brush ("paintbrush" paint op), ported from Krita's source (GPL, see ../README.md), at the commit in tools/get_krita.sh.
// Standard technique: dabs of a brush tip stamped along the stroke (Krita: KisBrushOp::paintAt, KisDistanceInformation).
// The model, in Krita's own parts:
// 1. A preset is numbers: the tip (shape, size, ratio, fades, spacing) and options whose value follows the pen's pressure through a curve.
// 2. Along the stroke a dab is placed each time the distance since the last one reaches the spacing ellipse of that dab's size.
// 3. Each dab is the tip's mask at that size, times opacity and flow, laid on the layer by the preset's composite op (normal or erase).
// Not ported yet (no preset so far turns them on): scatter, rotation and ratio options, textures, spikes, Krita's 1-px rim ramp of the gauss tip.
const KritaBrush = (() => {
  // SECTION: PRESET -- a preset file of krita/presets/ (one "name = value" a line) into the brush's numbers
  function parse(text) {
    const f = {};
    for (const l of text.split('\n')) { const i = l.indexOf(' = '); if (i > 0) f[l.slice(0, i)] = l.slice(i + 3); }
    return f;
  }
  function curveOf(sensor) {  // <params id="pressure"> <curve>x,y;...</curve>: no curve is Krita's straight line
    const m = /<curve>([^<]*)<\/curve>/.exec(sensor || '');
    return m ? m[1].split(';').filter(Boolean).map(p => p.split(',').map(Number)) : [[0, 0], [1, 1]];
  }
  function option(f, name, checkable) {  // Krita's curve option: on when not checkable or checked; the curve is used only with UseCurve
    return { on: !checkable || f['Pressure' + name] === 'true', useCurve: f[name + 'UseCurve'] === 'true', value: +(f[name + 'Value'] ?? 1), curve: curveOf(f[name + 'Sensor']) };
  }
  function fromPreset(text) {
    const f = parse(text), t = {};
    for (const [, k, v] of (f.brush_definition || '').matchAll(/(\w+)="([^"]*)"/g)) t[k] = v;
    const m = /<MaskGenerator([^>]*)>/.exec(f.brush_definition)[1], g = {};
    for (const [, k, v] of m.matchAll(/(\w+)="([^"]*)"/g)) g[k] = v;
    return {
      shape: g.type, fade: g.id,  // circle or rect; default (fade by hfade/vfade) or gauss
      diameter: +g.diameter, ratio: +g.ratio, hfade: +g.hfade, vfade: +g.vfade, antialias: g.antialiasEdges === '1', angle: +t.angle,
      spacing: +t.spacing, useAutoSpacing: t.useAutoSpacing === '1', autoSpacingCoeff: +t.autoSpacingCoeff,
      size: option(f, 'Size', true), opacity: option(f, 'Opacity', false), flow: option(f, 'Flow', false), spacingOption: option(f, 'Spacing', true),
      compositeOp: f.CompositeOp || 'normal',
    };
  }

  // SECTION: CURVE -- Krita's pressure curve: a natural cubic spline through the points, clamped to 0..1 (KisCubicCurve)
  function spline(pts) {
    const n = pts.length - 1, h = [], a = pts.map(p => p[1]), c = new Array(n + 1).fill(0), b = [], d = [];
    for (let i = 0; i < n; i++) h[i] = pts[i + 1][0] - pts[i][0];
    if (n > 1) {  // the tridiagonal system for the second derivatives, natural ends (Thomas algorithm)
      const lo = [], di = [], up = [], r = [];
      for (let i = 0; i < n - 1; i++) { di.push(2 * (h[i] + h[i + 1])); r.push(6 * ((a[i + 2] - a[i + 1]) / h[i + 1] - (a[i + 1] - a[i]) / h[i])); lo.push(h[i]); up.push(h[i + 1]); }
      for (let i = 1; i < n - 1; i++) { const w = lo[i] / di[i - 1]; di[i] -= w * up[i - 1]; r[i] -= w * r[i - 1]; }
      for (let i = n - 2; i >= 0; i--) c[i + 1] = (r[i] - (i < n - 2 ? up[i] * c[i + 2] : 0)) / di[i];
    }
    for (let i = 0; i < n; i++) { d[i] = (c[i + 1] - c[i]) / h[i]; b[i] = -0.5 * c[i] * h[i] - d[i] * h[i] * h[i] / 6 + (a[i + 1] - a[i]) / h[i]; }
    return x => {
      x = Math.min(pts[n][0], Math.max(pts[0][0], x));
      let i = 0; while (i < n - 1 && x > pts[i + 1][0]) i++;
      const u = x - pts[i][0];
      return Math.min(1, Math.max(0, a[i] + b[i] * u + 0.5 * c[i] * u * u + d[i] * u * u * u / 6));
    };
  }
  function optionValue(o, pressure) {  // KisCurveOption::computeSizeLikeValue: strength times the curve's value
    if (!o.on) return 1;
    return o.value * (o.useCurve ? (o.fn ||= spline(o.curve))(pressure) : 1);
  }

  // SECTION: TIP -- the auto brush's mask: 1 = full dab, 0 = nothing (Krita stores 255 - this), x and y from the dab's centre
  function tipMask(s, w, hgt) {
    if (s.fade === 'gauss') {  // KisGaussCircleMaskGenerator
      let fade = 1 - (s.hfade + s.vfade) / 2; if (fade === 0) fade = 1e-6; else if (fade === 1) fade = 1 - 1e-6;
      const center = 2.5 * (6761 * fade - 10000) / (Math.SQRT2 * 6761 * fade), alphaf = 255 / (2 * erf(center));
      const distf = Math.SQRT2 * 12500 / (6761 * fade * w / 2), yc = w / hgt, r = w / 2;
      return (x, y) => { const dist = Math.hypot(x, y * yc); if (dist > r) return 0; return Math.min(255, Math.floor(alphaf * (erf(dist * distf + center) - erf(dist * distf - center)))) / 255; };
    }
    const xc = 2 / w, yc = 2 / hgt, aa = s.antialias ? 1 : 0;
    const fx = (s.hfade === 0 ? 1 : 2 / (s.hfade * w)), fy = (s.vfade === 0 ? 1 : 2 / (s.vfade * hgt));  // the softness option (off in every preset so far) would divide these
    if (s.shape === 'rect') return (x, y) => {  // KisRectangleMaskGenerator
      x = Math.abs(x); y = Math.abs(y);
      const nx = x * xc, ny = y * yc; if (nx > 1 || ny > 1) return 0;
      const fxr = (x + aa) * fx, fyr = (y + aa) * fy, fxn = nx * (fxr - 1) / (fxr - nx), fyn = ny * (fyr - 1) / (fyr - ny);
      let v = 0; if (fxr > 1) v = fxn; if (fxn < fyn && fyr > 1) v = fyn;
      return 1 - Math.floor(v * 255) / 255;
    };
    return (x, y) => {  // KisCircleMaskGenerator (norme is the squared length)
      const n = (x * xc) ** 2 + (y * yc) ** 2; if (n > 1) return 0;
      const nf = ((Math.abs(x) + aa) * fx) ** 2 + ((Math.abs(y) + aa) * fy) ** 2; if (nf < 1) return 1;
      return 1 - Math.floor(255 * n * (nf - 1) / (nf - n)) / 255;
    };
  }
  function erf(x) {  // Abramowitz-Stegun 7.1.26 (Krita uses the C library's erf)
    const s = Math.sign(x); x = Math.abs(x); const t = 1 / (1 + 0.3275911 * x);
    return s * (1 - (((((1.061405429 * t - 1.453152027) * t) + 1.421413741) * t - 0.284496736) * t + 0.254829592) * t * Math.exp(-x * x));
  }

  // SECTION: DAB -- one dab laid on the layer (RGBA bytes), by Krita's composite ops
  function dab(layer, s, x, y, pressure, color) {
    const scale = optionValue(s.size, pressure), w = s.diameter * scale, h = s.diameter * s.ratio * scale;
    if (w < 0.01) return;
    const mask = tipMask(s, w, h), str = optionValue(s.opacity, pressure) * optionValue(s.flow, pressure);
    const ca = Math.cos(-s.angle), sa = Math.sin(-s.angle), R = Math.ceil(Math.hypot(w, h) / 2) + 1, D = layer.data, W = layer.width;
    for (let py = Math.max(0, Math.floor(y - R)); py <= Math.min(layer.height - 1, Math.ceil(y + R)); py++)
      for (let px = Math.max(0, Math.floor(x - R)); px <= Math.min(W - 1, Math.ceil(x + R)); px++) {
        const dx = px + 0.5 - x, dy = py + 0.5 - y, m = mask(dx * ca - dy * sa, dx * sa + dy * ca) * str;
        if (m <= 0) continue;
        const i = (py * W + px) * 4;
        if (s.compositeOp === 'erase') { D[i + 3] = Math.round(D[i + 3] * (1 - m)); continue; }  // KoCompositeOpErase
        const da = D[i + 3] / 255, oa = m + da * (1 - m);  // normal: source over
        for (let k = 0; k < 3; k++) D[i + k] = Math.round((color[k] * m + D[i + k] * da * (1 - m)) / oa);
        D[i + 3] = Math.round(oa * 255);
      }
  }

  // SECTION: STROKE -- dabs along the finger's path (KisDistanceInformation::getNextPointPositionAnisotropic)
  function spacingOf(s, pressure) {  // KisPaintOpUtils::effectiveSpacing, not isotropic
    const scale = optionValue(s.size, pressure), w = s.diameter * scale, h = s.diameter * s.ratio * scale;
    const auto = v => s.autoSpacingCoeff * (v < 1 ? v : Math.sqrt(v)), extra = optionValue(s.spacingOption, pressure);
    return (s.useAutoSpacing ? [auto(w), auto(h)] : [w * s.spacing, h * s.spacing]).map(v => Math.max(0.5, v * extra));
  }
  function stroke(layer, s, color) {
    let last = null, acc = [0, 0], sp;
    return {
      to(x, y, pressure) {
        if (!last) { dab(layer, s, x, y, pressure, color); sp = spacingOf(s, pressure); last = [x, y, pressure]; return; }
        let [x0, y0] = last;
        while (true) {
          const dx = x - x0, dy = y - y0, L = Math.hypot(dx, dy); if (L === 0) break;
          const ax = Math.abs(dx), ay = Math.abs(dy), a = (ax / sp[0]) ** 2 + (ay / sp[1]) ** 2;  // (acc + t·d)/spacing on the ellipse: solve for t
          const b = 2 * (acc[0] * ax / sp[0] ** 2 + acc[1] * ay / sp[1] ** 2), c = (acc[0] / sp[0]) ** 2 + (acc[1] / sp[1]) ** 2 - 1;
          const t = c >= 0 ? 0 : (-b + Math.sqrt(b * b - 4 * a * c)) / (2 * a);
          if (t > 1) { acc = [acc[0] + ax, acc[1] + ay]; break; }
          const nx = x0 + dx * t, ny = y0 + dy * t, f = Math.hypot(nx - last[0], ny - last[1]) / Math.hypot(x - last[0], y - last[1]), np = last[2] + (pressure - last[2]) * f;
          dab(layer, s, nx, ny, np, color); sp = spacingOf(s, np); acc = [0, 0]; [x0, y0] = [nx, ny];
        }
        last = [x, y, pressure];
      },
    };
  }
  return { fromPreset, stroke, optionValue };
})();

// SECTION: BRUSH CORE -- Krita's pixel brush ("paintbrush" paint op), ported from Krita's source (GPL, see ../README.md), at the commit in tools/get_krita.sh.
// Standard technique: dabs of a brush tip stamped along the stroke (Krita: KisBrushOp::paintAt, KisDistanceInformation).
// The model, in Krita's own parts:
// 1. A preset is numbers: the tip (auto shape or picture, size, ratio, fades, spacing) and options (size, opacity, flow, rotation, ratio, scatter,
//    mirror, softness, spacing, texture strength) whose value follows sensors (pressure, tilt, drawing angle, random, time) through curves.
// 2. Along the stroke a dab is placed each time the distance since the last one reaches the spacing ellipse of that dab's size.
// 3. Each dab is the tip's mask at that size and angle, times the paper texture, laid by Krita's painting mode: build-up straight on the layer,
//    or wash into a stroke layer (alpha darken: opacity caps it, flow builds it) that goes on the layer by the preset's composite op.
// 4. Two other Krita engines share the dabs: spray (particles of the tip in a circle) and colour smudge, which takes the paint under the last dab, or its
//    average colour, mixes the paint colour in, and lays that.
// Not ported (no preset of the families uses them): spikes, Krita's 1-px rim ramp of the gauss tip, fan corners and locked drawing angle,
// lightness and gradient tip modes, the average-opacity part of alpha darken.
const KritaBrush = (() => {
  const TAU = 2 * Math.PI, wrap = (v, lo, hi) => { const r = hi - lo; return v - r * Math.floor((v - lo) / r); };
  const attrs = s => { const o = {}; for (const [, k, v] of (s || '').matchAll(/(\w+)="([^"]*)"/g)) o[k] = v; return o; };

  // SECTION: PRESET -- a preset file of krita/presets/ (one "name = value" a line) into the brush's numbers
  function parse(text) {
    const f = {};
    for (const l of text.split('\n')) { const i = l.indexOf(' = '); if (i > 0) f[l.slice(0, i)] = l.slice(i + 3); }
    return f;
  }
  function sensorsOf(xml) {  // one <params id=...> or a sensorslist of <ChildSensor id=...>, each with its curve (none: straight line)
    xml = xml || '<params id="pressure"/>';
    const one = (tag, body) => { const a = attrs(tag), m = /<curve>([^<]*)<\/curve>/.exec(body || ''); return { ...a, curve: m ? m[1].split(';').filter(Boolean).map(p => p.split(',').map(Number)) : null }; };
    if (/id="sensorslist"/.test(xml)) return [...xml.matchAll(/<ChildSensor([^>]*?)(?:\/>|>(.*?)<\/ChildSensor>)/g)].map(m => one(m[1], m[2]));
    const m = /<params([^>]*?)(?:\/>|>(.*?)<\/params>)/.exec(xml); return [one(m[1], m[2])];
  }
  const RANGE = { Scatter: [0, 5], Softness: [0.1, 1], SmudgeRadius: [0, 3] };  // Krita's option ranges; every other option is 0..1
  function option(f, prefix, name, checkable) {  // Krita's curve option: on when not checkable or checked; sensors only with UseCurve
    const k = s => f[prefix + s] ?? f[prefix + name + s];
    return { name, on: !checkable || f['Pressure' + name] === 'true',
      useCurve: k('UseCurve') === 'true', value: +(k('Value') ?? 1), mode: +(k('curveMode') ?? 0), sensors: sensorsOf(k('Sensor')), range: RANGE[name] || [0, 1] };
  }
  function fromPreset(text) {
    const f = parse(text), def = f.brush_definition || '', t = attrs(/<Brush([^>]*)>/.exec(def)[1]), g = attrs((/<MaskGenerator([^>]*)>/.exec(def) || [])[1]);
    const P = 'Texture/Pattern/';
    return {
      tipType: t.type, file: t.filename, scale: +(t.scale ?? 1), angle: +(t.angle ?? 0), colorAsMask: (t.ColorAsMask ?? '1') === '1',
      shape: g.type, fade: g.id, softCurve: g.softness_curve ? g.softness_curve.split(';').filter(Boolean).map(p => p.split(',').map(Number)) : null, diameter: +(g.diameter ?? 0), ratio: +(g.ratio ?? 1), hfade: +(g.hfade ?? 0), vfade: +(g.vfade ?? 0), antialias: g.antialiasEdges === '1',
      randomness: +(t.randomness ?? 0), density: +(t.density ?? 1),
      spacing: +t.spacing, useAutoSpacing: t.useAutoSpacing === '1', autoSpacingCoeff: +t.autoSpacingCoeff, isotropic: f['Spacing/Isotropic'] === 'true',
      size: option(f, '', 'Size', true), opacity: option(f, '', 'Opacity', false), flow: option(f, '', 'Flow', false),
      rotation: option(f, '', 'Rotation', true), ratioOption: option(f, '', 'Ratio', true), scatter: option(f, '', 'Scatter', true),
      mirror: option(f, '', 'Mirror', true), softness: option(f, '', 'Softness', true), spacingOption: option(f, '', 'Spacing', true),
      scatterX: f['Scattering/AxisX'] !== 'false', scatterY: f['Scattering/AxisY'] !== 'false',
      mirrorH: f.HorizontalMirrorEnabled === 'true', mirrorV: f.VerticalMirrorEnabled === 'true',
      wash: f.paintop === 'paintbrush' && (f.PaintOpAction ?? '2') !== '1', compositeOp: f.CompositeOp || 'normal',
      airbrush: f['PaintOpSettings/isAirbrushing'] === 'true' || f['AirbrushOption/isAirbrushing'] === 'true' ? +(f['PaintOpSettings/rate'] ?? f['AirbrushOption/rate'] ?? 50) : 0,
      rateOption: option(f, '', 'Rate', true),
      spray: f.paintop !== 'spraybrush' ? null : {  // Krita's spray engine (KisSprayOpOptionData, shape dynamics, colour options); the particle is the brush tip
        diameter: +f['Spray/diameter'], aspect: +(f['Spray/aspect'] ?? 1), scale: +(f['Spray/scale'] ?? 1), rotation: +(f['Spray/rotation'] ?? 0), spacing: +(f['Spray/spacing'] ?? 0.5),
        jitter: f['Spray/jitterMovement'] === 'true', jitterAmount: +(f['Spray/jitterMoveAmount'] ?? 1), useDensity: f['Spray/useDensity'] === 'true',
        coverage: +(f['Spray/coverage'] ?? 0.1), particleCount: +(f['Spray/particleCount'] ?? 1),
        dyn: { enabled: f['ShapeDynamics/enabled'] === 'true', fixedRotation: f['ShapeDynamics/fixedRotation'] === 'true', fixedAngle: +(f['ShapeDynamics/fixedAngle'] ?? 0),
          randomRotation: f['ShapeDynamics/randomRotation'] === 'true', randomRotationWeight: +(f['ShapeDynamics/randomRotationWeight'] ?? 0),
          followCursor: f['ShapeDynamics/followCursor'] === 'true', followCursorWeight: +(f['ShapeDynamics/followCursorWeigth'] ?? 0),
          followDrawingAngle: f['ShapeDynamics/followDrawingAngle'] === 'true', followDrawingAngleWeight: +(f['ShapeDynamics/followDrawingAngleWeigth'] ?? 0),
          randomSize: f['ShapeDynamics/randomSize'] === 'true' },
        col: { colorPerParticle: f['ColorOption/colorPerParticle'] === 'true', useRandomHSV: f['ColorOption/useRandomHSV'] === 'true', useRandomOpacity: f['ColorOption/useRandomOpacity'] === 'true',
          hue: +(f['ColorOption/hue'] ?? 0), saturation: +(f['ColorOption/saturation'] ?? 0), value: +(f['ColorOption/value'] ?? 0) },
      },
      smudge: f.paintop !== 'colorsmudge' ? null : {  // Krita's colour smudge (legacy engine): smear or dull, then the paint colour by its rate
        mode: +(f.SmudgeRateMode ?? 0), smearAlpha: f.SmudgeRateSmearAlpha !== 'false', rate: option(f, '', 'SmudgeRate', true), colorRate: option(f, '', 'ColorRate', true),
        radius: (o => { if (+(f.SmudgeRadiusVersion ?? 1) < 2) o.value /= 100; return o; })(option(f, '', 'SmudgeRadius', true)),
      },
      texture: f[P + 'Enabled'] !== 'true' ? null : {
        pattern: f[P + 'Name'], scale: +(f[P + 'Scale'] ?? 1), brightness: +(f[P + 'Brightness'] ?? 0), contrast: +(f[P + 'Contrast'] ?? 1),
        neutralPoint: +(f[P + 'NeutralPoint'] ?? 0.5), invert: f[P + 'Invert'] === 'true', cutoffPolicy: +(f[P + 'CutoffPolicy'] ?? 0),
        cutoffLeft: +(f[P + 'CutoffLeft'] ?? 0), cutoffRight: +(f[P + 'CutoffRight'] ?? 255), mode: +(f[P + 'TexturingMode'] ?? 0),
        offsetX: +(f[P + 'OffsetX'] ?? 0), offsetY: +(f[P + 'OffsetY'] ?? 0), randomX: f[P + 'isRandomOffsetX'] === 'true', randomY: f[P + 'isRandomOffsetY'] === 'true',
        strength: option(f, 'Texture/Strength/', 'Strength', false),
      },
    };
  }

  // SECTION: CURVE -- Krita's curve: a natural cubic spline through the points, clamped to 0..1 (KisCubicCurve)
  function spline(pts) {
    const n = pts.length - 1;
    if (n === 0) return () => pts[0][1];
    const h = [], a = pts.map(p => p[1]), c = new Array(n + 1).fill(0), b = [], d = [];
    for (let i = 0; i < n; i++) h[i] = pts[i + 1][0] - pts[i][0];
    if (n > 1) {  // the second derivatives, natural ends (tridiagonal system, Thomas algorithm)
      const di = [], up = [], r = [];
      for (let i = 0; i < n - 1; i++) { di.push(2 * (h[i] + h[i + 1])); r.push(6 * ((a[i + 2] - a[i + 1]) / h[i + 1] - (a[i + 1] - a[i]) / h[i])); up.push(h[i + 1]); }
      for (let i = 1; i < n - 1; i++) { const w = h[i] / di[i - 1]; di[i] -= w * up[i - 1]; r[i] -= w * r[i - 1]; }
      for (let i = n - 2; i >= 0; i--) c[i + 1] = (r[i] - up[i] * c[i + 2]) / di[i];
    }
    for (let i = 0; i < n; i++) { d[i] = (c[i + 1] - c[i]) / h[i]; b[i] = -0.5 * c[i] * h[i] - d[i] * h[i] * h[i] / 6 + (a[i + 1] - a[i]) / h[i]; }
    return x => {
      x = Math.min(pts[n][0], Math.max(pts[0][0], x));
      let i = 0; while (i < n - 1 && x > pts[i + 1][0]) i++;
      const u = x - pts[i][0];
      return Math.min(1, Math.max(0, a[i] + b[i] * u + 0.5 * c[i] * u * u + d[i] * u * u * u / 6));
    };
  }

  // SECTION: SENSORS -- what the pen and the stroke tell each dab (KisDynamicSensor*); ctx: pressure, tiltX/Y in degrees, angle, time
  const ADDITIVE = { fuzzy: 1, fuzzystroke: 1, ascension: 1 }, ABSOLUTE = { drawingangle: 1 };
  function sensorValue(s, ctx) {
    switch (s.id) {
      case 'pressure': return ctx.pressure;
      case 'fuzzy': return 2 * Math.random() - 1;
      case 'fuzzystroke': return ctx.strokeRandom[s.id] ??= 2 * Math.random() - 1;
      case 'drawingangle': return wrap(0.5 + ctx.angle / TAU + +(s.angleOffset ?? 0) / 360, 0, 1);
      case 'ascension': {  // tilt direction; a pen standing straight up points to 3 o'clock
        const d = ctx.tiltX === 0 && ctx.tiltY === 0 ? -Math.PI / 2 : Math.atan2(-ctx.tiltX, ctx.tiltY);
        return 2 * (d / TAU + 0.5) - 1;
      }
      case 'declination': {  // tilt elevation, 60 degrees full tilt
        const x = Math.max(-1, Math.min(1, ctx.tiltX / 60)), y = Math.max(-1, Math.min(1, ctx.tiltY / 60));
        const e = Math.abs(x) > Math.abs(y) ? Math.sqrt(1 + y * y) : Math.sqrt(1 + x * x);
        return Math.acos(Math.hypot(x, y) / e) / (Math.PI / 2);
      }
      case 'xtilt': return 1 - Math.abs(ctx.tiltX) / 60;
      case 'ytilt': return 1 - Math.abs(ctx.tiltY) / 60;
      case 'time': { const dur = +(s.duration ?? 1000), t = ctx.time / dur; return s.periodic === '1' ? t % 1 : Math.min(1, t); }
      default: return 1;  // a sensor no preset of these families uses
    }
  }
  function sensorParameter(s, ctx) {  // KisDynamicSensor::parameter: the value through its curve
    const v = sensorValue(s, ctx);
    if (!s.curve) return v;
    const add = ADDITIVE[s.id], abs = ABSOLUTE[s.id];
    const fn = s.fn ||= spline(s.curve), x = fn(add ? 0.5 * (1 + v) : abs ? wrap(v + 0.5, 0, 1) : v);
    return add ? 2 * x - 1 : abs ? wrap(x + 0.5, 0, 1) : x;
  }
  function components(o, ctx, useStrength = true) {  // KisCurveOption::computeValueComponents
    const c = { constant: useStrength ? o.value : 1, scaling: 1, additive: 0, hasScaling: false, hasAdditive: false, abs: null };
    if (!o.useCurve) return c;
    const scal = [];
    for (const s of o.sensors) {
      const v = sensorParameter(s, ctx);
      if (ADDITIVE[s.id]) { c.additive += v; c.hasAdditive = true; } else if (ABSOLUTE[s.id]) c.abs = v; else scal.push(v);
    }
    if (scal.length) {
      c.hasScaling = true;
      c.scaling = o.mode === 1 ? scal.reduce((a, b) => a + b) : o.mode === 2 ? Math.max(...scal) : o.mode === 3 ? Math.min(...scal)
        : o.mode === 4 ? Math.max(...scal) - Math.min(...scal) : scal.reduce((a, b) => a * b);
    }
    return c;
  }
  function sizeLike(o, ctx, useStrength = true) {
    if (!o.on) return 1;
    const c = components(o, ctx, useStrength);
    return Math.max(o.range[0], Math.min(o.range[1], c.constant * (c.abs ?? 1) * (c.hasScaling ? c.scaling : 1) * (c.hasAdditive ? 0.5 * (1 + c.additive) : 1)));
  }
  function rotationOf(o, ctx) {  // KisRotationOption::apply, canvas not turned
    if (!o.on) return 0;
    const c = components(o, ctx), v = wrap(2 * (c.abs ?? 0) + c.constant * (-(c.hasScaling ? 2 * c.scaling - 1 : 0) + (c.hasAdditive ? c.additive : 0)), -1, 1);
    return wrap((1 - v) * Math.PI, 0, TAU);
  }

  // SECTION: TIPS -- the dab's mask (1 = full): auto shapes computed (Kis*MaskGenerator), pictures sampled (gbr, gih, png, svg)
  function autoMask(s, w, h, soft) {
    const fadeSoft = 1 / Math.max(0.01, soft);
    if (s.fade === 'gauss') {  // KisGaussCircleMaskGenerator
      let fade = 1 - (s.hfade + s.vfade) / 2; if (fade === 0) fade = 1e-6; else if (fade === 1) fade = 1 - 1e-6;
      const center = 2.5 * (6761 * fade - 10000) / (Math.SQRT2 * 6761 * fade), alphaf = 255 / (2 * erf(center));
      const distf = Math.SQRT2 * 12500 / (6761 * fade * w / 2), yc = w / h, r = w / 2;
      return (x, y) => { const dist = Math.hypot(x, y * yc); if (dist > r) return 0; return Math.min(255, Math.floor(alphaf * (erf(dist * distf + center) - erf(dist * distf - center)))) / 255; };
    }
    const xc = 2 / w, yc = 2 / h, aa = s.antialias ? 1 : 0;
    if (s.fade === 'soft') {  // KisCurveCircleMaskGenerator: the soft curve over the squared distance (softness option not ported)
      const fn = s.softFn ||= spline(s.softCurve || [[0, 0], [1, 1]]);
      return (x, y) => { const n = (x * xc) ** 2 + (y * yc) ** 2; return n > 1 ? 0 : fn(n); };
    }
    const fx = (s.hfade === 0 ? 1 : 2 / (s.hfade * w)) * fadeSoft, fy = (s.vfade === 0 ? 1 : 2 / (s.vfade * h)) * fadeSoft;
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
  function hslShift(c, dh, ds, dl) {  // KisHSVAdjustment, HSL in compatibility mode: hue turned, saturation scaled, lightness towards white
    const [r, g, b] = c.map(v => v / 255), M = Math.max(r, g, b), m = Math.min(r, g, b);
    let l = (M + m) / 2, sat = M === m ? 0 : (l > 0.5 ? (M - m) / (2 - M - m) : (M - m) / (M + m)), h = 0;
    if (M !== m) h = 60 * (M === r ? (g - b) / (M - m) + (g < b ? 6 : 0) : M === g ? (b - r) / (M - m) + 2 : (r - g) / (M - m) + 4);
    h = wrap(h + dh * 180, 0, 360); sat = Math.min(1, sat * (ds + 1)); l = dl < 0 ? l * (dl + 1) : l + dl * (1 - l);
    const q = l < 0.5 ? l * (1 + sat) : l + sat - l * sat, p = 2 * l - q;
    const f = t => { t = wrap(t, 0, 1); return t < 1 / 6 ? p + (q - p) * 6 * t : t < 1 / 2 ? q : t < 2 / 3 ? p + (q - p) * (2 / 3 - t) * 6 : p; };
    return [f(h / 360 + 1 / 3), f(h / 360), f(h / 360 - 1 / 3)].map(v => v * 255);
  }
  function halton(i, base) { let f = 1, r = 0; while (i > 0) { f /= base; r += f * (i % base); i = Math.floor(i / base); } return r; }
  function erf(x) {  // Abramowitz-Stegun 7.1.26 (Krita uses the C library's erf)
    const s = Math.sign(x); x = Math.abs(x); const t = 1 / (1 + 0.3275911 * x);
    return s * (1 - (((((1.061405429 * t - 1.453152027) * t) + 1.421413741) * t - 0.284496736) * t + 0.254829592) * t * Math.exp(-x * x));
  }
  // A picture tip is { w, h, mask: Float32Array (0..1), rgb: Uint8Array or null (an image stamp keeps its colours) }; a gih is a list of them.
  function tipFromRGBA(w, h, px, stamp) {  // KisBrush: alpha mask = (255 - grey) * alpha
    const mask = new Float32Array(w * h), rgb = stamp ? new Uint8Array(w * h * 3) : null;
    for (let i = 0; i < w * h; i++) {
      const r = px[i * 4], g = px[i * 4 + 1], b = px[i * 4 + 2], a = px[i * 4 + 3] / 255;
      if (stamp) { mask[i] = a; rgb.set([r, g, b], i * 3); } else mask[i] = (255 - (r * 11 + g * 16 + b * 5) / 32) * a / 255;
    }
    return { w, h, mask, rgb };
  }
  function readGbr(bytes, at = 0) {  // GIMP brush: header (size, version, width, height, bytes per pixel, 'GIMP', spacing, name), then pixels
    const dv = new DataView(bytes.buffer, bytes.byteOffset + at), hs = dv.getUint32(0), w = dv.getUint32(8), h = dv.getUint32(12), bpp = dv.getUint32(16);
    const px = new Uint8Array(w * h * 4), data = bytes.subarray(at + hs, at + hs + w * h * bpp);
    let color = false;
    for (let i = 0; i < w * h; i++) {
      if (bpp === 1) px.set([255 - data[i], 255 - data[i], 255 - data[i], 255], i * 4);
      else { px.set(data.subarray(i * 4, i * 4 + 4), i * 4); if (data[i * 4] !== data[i * 4 + 1] || data[i * 4 + 1] !== data[i * 4 + 2]) color = true; }
    }
    return { px, w, h, color, end: at + hs + w * h * bpp };
  }
  function readGih(bytes) {  // GIMP image pipe: a name line, a parameters line (ncells, sel0), then each cell as a gbr
    let i = 0; const line = () => { const s = i; while (bytes[i] !== 10) i++; return new TextDecoder().decode(bytes.subarray(s, i++)); };
    line(); const params = line(), n = +params.split(' ')[0], cells = [];
    for (let k = 0; k < n && i + 28 < bytes.length; k++) { const c = readGbr(bytes, i); if (c.end > bytes.length) break; cells.push(c); i = c.end; }  // a file may hold fewer cells than it says (fairy-dust)
    return { cells, selection: (/sel0:(\w+)/.exec(params) || [])[1] || 'random' };
  }
  function pictureTip(s, asset) {  // the tip's cells, as KisPredefinedBrushFactory chooses alpha mask or image stamp
    const stampOf = color => color && !s.colorAsMask;
    if (asset.gih) return { cells: asset.gih.cells.map(c => tipFromRGBA(c.w, c.h, c.px, stampOf(c.color))), selection: asset.gih.selection };
    if (asset.gbr) return { cells: [tipFromRGBA(asset.gbr.w, asset.gbr.h, asset.gbr.px, stampOf(asset.gbr.color))], selection: 'random' };
    const { w, h, px } = asset.image; let color = false;
    for (let i = 0; i < w * h && !color; i++) color = px[i * 4] !== px[i * 4 + 1] || px[i * 4 + 1] !== px[i * 4 + 2];
    return { cells: [tipFromRGBA(w, h, px, stampOf(color))], selection: 'random' };
  }
  function sample(t, u, v) {  // bilinear, outside is empty
    const x = u - 0.5, y = v - 0.5, x0 = Math.floor(x), y0 = Math.floor(y), fx = x - x0, fy = y - y0;
    let m = 0, r = 0, g = 0, b = 0;
    for (const [i, j, k] of [[x0, y0, (1 - fx) * (1 - fy)], [x0 + 1, y0, fx * (1 - fy)], [x0, y0 + 1, (1 - fx) * fy], [x0 + 1, y0 + 1, fx * fy]]) {
      if (i < 0 || j < 0 || i >= t.w || j >= t.h) continue;
      const p = j * t.w + i, a = t.mask[p] * k; m += a;
      if (t.rgb) { r += t.rgb[p * 3] * a; g += t.rgb[p * 3 + 1] * a; b += t.rgb[p * 3 + 2] * a; }
    }
    return t.rgb ? [m, m ? [r / m, g / m, b / m] : null] : [m, null];
  }

  // SECTION: TEXTURE -- the paper pattern applied to each dab (KisTextureMaskInfo, KisTextureOption, masking composite ops)
  function textureMask(tx, image) {
    const sc = tx.scale, w = Math.max(2, Math.round(image.w * sc)), h = Math.max(2, Math.round(image.h * sc)), m = new Float32Array(w * h), px = image.px;
    for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
      const p = (Math.min(image.h - 1, Math.floor((y + 0.5) / sc)) * image.w + Math.min(image.w - 1, Math.floor((x + 0.5) / sc))) * 4;
      const a = px[p + 3] / 255, grey = Math.floor((px[p] * 11 + px[p + 1] * 16 + px[p + 2] * 5) / 32);
      let v = grey / 255 * a + (1 - a);
      v = Math.max(0, Math.min(1, ((v - tx.brightness) - 0.5) * tx.contrast + 0.5));
      if (tx.invert) v = 1 - v;
      const np = tx.neutralPoint;
      v = (np === 1 || (np !== 0 && v <= np)) ? v / (2 * np) : 0.5 + (v - np) / (2 - 2 * np);
      if (tx.cutoffPolicy && (v < tx.cutoffLeft / 255 || v > tx.cutoffRight / 255)) v = tx.cutoffPolicy === 1 ? 0 : 1;
      m[y * w + x] = v;
    }
    return { w, h, m };
  }

  // SECTION: DAB AND STROKE -- dabs along the finger's path (KisDistanceInformation::getNextPointPositionAnisotropic), laid by the painting mode
  function stroke(layer, s, color, assets) {
    const W = layer.width, H = layer.height, L = layer.data;
    const pic = s.tipType === 'auto_brush' ? null : (s.pic ||= pictureTip(s, assets[s.file]));
    const tex = s.texture && assets[s.texture.pattern] ? (s.texture.mask ||= textureMask(s.texture, assets[s.texture.pattern].image)) : null;
    const texOff = tex ? [s.texture.randomX ? Math.floor(Math.random() * tex.w) : s.texture.offsetX, s.texture.randomY ? Math.floor(Math.random() * tex.h) : s.texture.offsetY] : null;
    const wash = s.wash ? { a: new Float32Array(W * H), rgb: new Float32Array(W * H * 3) } : null;
    const ctx = { pressure: 1, tiltX: 0, tiltY: 0, angle: 0, time: 0, strokeRandom: {} };
    const t0 = performance.now(), dirty = [W, H, -1, -1];
    let last = null, acc = [0, 0], sp = null, cell = 0;

    function shapeOf() {  // KisDabShape: size, ratio and rotation of this dab
      const scale = sizeLike(s.size, ctx), ratio = sizeLike(s.ratioOption, ctx), rot = rotationOf(s.rotation, ctx);
      const [bw, bh] = baseSize();
      return { scale, ratio, rot, w: bw * scale, h: bh * scale * ratio };
    }
    function spacingOf(d) {  // KisPaintOpUtils::effectiveSpacing (spray: half its diameter times its spacing, the same every way)
      if (s.spray) { const v = s.spray.diameter / 2 > 1 ? s.spray.diameter / 2 * s.spray.spacing : 1; return { x: v, y: v, rot: 0 }; }
      const auto = v => s.autoSpacingCoeff * (v < 1 ? v : Math.sqrt(v)), extra = s.spacingOption.on ? sizeLike(s.spacingOption, ctx) : 1;
      const xy = (s.isotropic ? [Math.max(d.w, d.h), Math.max(d.w, d.h)] : [d.w, d.h]).map(v => (s.useAutoSpacing ? auto(v) : v * s.spacing) * extra);
      return { x: Math.max(0.5, xy[0]), y: Math.max(0.5, xy[1]), rot: s.isotropic ? 0 : d.rot };
    }
    function lay(D, i, a, c) {  // the preset's composite op: erase, or normal (source over)
      if (s.compositeOp === 'erase') { D[i + 3] = Math.round(D[i + 3] * (1 - a)); return; }
      const da = D[i + 3] / 255, oa = a + da * (1 - a); if (oa <= 0) return;
      for (let k = 0; k < 3; k++) D[i + k] = Math.round((c[k] * a + D[i + k] * da * (1 - a)) / oa);
      D[i + 3] = Math.round(oa * 255);
    }
    function tipOf(d, mx, my) {  // the tip's mask at this dab's shape: tipAt(u, v) from the dab's centre gives [mask, picture colour or null]
      const ang = d.rot + s.angle, ca = Math.cos(ang), sa = Math.sin(ang);
      if (pic) {
        const t = pic.cells[pic.selection === 'incremental' ? cell++ % pic.cells.length : Math.floor(Math.random() * pic.cells.length)];
        const sx = s.scale * d.scale, sy = s.scale * d.scale * d.ratio;
        return (u, v) => sample(t, (ca * u - sa * v) * mx / sx + t.w / 2, (sa * u + ca * v) * my / sy + t.h / 2);
      }
      const m = autoMask(s, d.w, d.h, s.softness.on ? sizeLike(s.softness, ctx) : 1), ss = s.antialias && (d.w < 10 || d.h < 10) ? (d.w < 1 || d.h < 1 ? 6 : 3) : 1;
      return (u, v) => {  // KisBrushMaskScalarApplicator: supersampled when small, then randomness and density
        let sum = 0;
        for (let i = 0; i < ss; i++) for (let j = 0; j < ss; j++) { const a = u + (i + 0.5) / ss - 0.5, b = v + (j + 0.5) / ss - 0.5; sum += m((ca * a - sa * b) * mx, (sa * a + ca * b) * my); }
        let val = sum / (ss * ss);
        if (s.randomness) val *= (1 - s.randomness) + s.randomness * Math.random();
        if (s.density < 1 && val > 0 && !(s.density >= Math.random())) val = 0;
        return [val, null];
      };
    }
    function baseSize() { return pic ? [pic.cells[0].w * s.scale, pic.cells[0].h * s.scale] : [s.diameter, s.diameter * s.ratio]; }
    function dab(x, y) {
      if (s.spray) return sprayDab(x, y);
      const d = shapeOf(); if (d.w < 0.01 || d.h < 0.01) return d;
      if (s.scatter.on && (s.scatterX || s.scatterY)) {  // KisScatterOption: jitter by the dab's larger side
        const dia = Math.max(d.w, d.h), v = sizeLike(s.scatter, ctx), j = () => (2 * Math.random() - 1) * dia * v;
        if (s.scatterX && s.scatterY) { x += j(); y += j(); }
        else { const k = j(), c = Math.cos(ctx.angle), sn = Math.sin(ctx.angle); if (s.scatterX) { x += c * k; y += sn * k; } else { x -= sn * k; y += c * k; } }
      }
      let mx = 1, my = 1;  // KisMirrorOption: flip when its value reaches a half
      if (s.mirror.on && sizeLike(s.mirror, ctx) >= 0.5) { if (s.mirrorH) mx = -1; if (s.mirrorV) my = -1; }
      const flow = sizeLike(s.flow, ctx), opacity = sizeLike(s.opacity, ctx, !s.wash), strength = tex ? sizeLike(s.texture.strength, ctx) : 0;
      const tipAt = tipOf(d, mx, my);
      const R = Math.ceil(Math.hypot(d.w, d.h) / 2) + 1, x0 = Math.max(0, Math.floor(x - R)), x1 = Math.min(W - 1, Math.ceil(x + R)), y0 = Math.max(0, Math.floor(y - R)), y1 = Math.min(H - 1, Math.ceil(y + R));
      const maskAt = (px, py) => {  // the tip, then the paper pattern by multiply or subtract with the texture's strength (soft texturing off)
        const r = tipAt(px + 0.5 - x, py + 0.5 - y);
        if (tex && r[0] > 0) {
          const tv = tex.m[wrap(py - texOff[1], 0, tex.h) * tex.w + wrap(px - texOff[0], 0, tex.w)];
          r[0] = s.texture.mode === 1 ? Math.max(0, r[0] - (tv + 1 - strength)) : tv * r[0] * strength;
        }
        return r;
      };
      if (s.smudge) smudgeDab(x0, y0, x1, y1, maskAt);
      else for (let py = y0; py <= y1; py++) for (let px = x0; px <= x1; px++) {
        const [m, rgb] = maskAt(px, py);
        if (m <= 0) continue;
        const c = rgb || color, i = py * W + px;
        if (wash) {  // alpha darken, creamy (KoCompositeOpAlphaDarken): the stroke layer strives to opacity, by flow
          const dA = wash.a[i], src = m * opacity, full = opacity > dA ? dA + (opacity - dA) * m : dA;
          for (let k = 0; k < 3; k++) wash.rgb[i * 3 + k] = dA ? wash.rgb[i * 3 + k] + (c[k] - wash.rgb[i * 3 + k]) * src : c[k];
          wash.a[i] = dA + (full - dA) * flow;
        } else lay(L, i * 4, m * opacity * flow, c);
      }
      dirty[0] = Math.min(dirty[0], x0); dirty[1] = Math.min(dirty[1], y0); dirty[2] = Math.max(dirty[2], x1); dirty[3] = Math.max(dirty[3], y1);
      return d;
    }
    // SprayBrush::paint: particles at random places in a circle, each the tip at a random size, coloured once a dab (or per particle) with random
    // hue, saturation, lightness and opacity; they are gathered on a dab layer that goes on the paper at the opacity option.
    function sprayDab(x, y) {
      const sp = s.spray, radius = sp.diameter / 2 * sizeLike(s.size, ctx), opacity = sizeLike(s.opacity, ctx);
      if (sp.jitter) { x += (2 * radius * Math.random() - radius) * sp.jitterAmount; y += (2 * radius * Math.random() - radius) * sp.jitterAmount; }
      const n = sp.useDensity ? Math.floor(sp.coverage * Math.PI * radius * radius) : sp.particleCount;
      const rot = -rotationOf(s.rotation, ctx) + sp.rotation * Math.PI / 180, cr = Math.cos(rot), sr = Math.sin(rot);
      const [bw, bh] = baseSize(), R = Math.ceil(radius * Math.max(1, sp.aspect) * sp.scale + Math.hypot(bw, bh) / 2) + 2;
      const x0 = Math.max(0, Math.floor(x - R)), x1 = Math.min(W - 1, Math.ceil(x + R)), y0 = Math.max(0, Math.floor(y - R)), y1 = Math.min(H - 1, Math.ceil(y + R));
      if (x1 < x0 || y1 < y0) return null;
      const w = x1 - x0 + 1, buf = new Float32Array(w * (y1 - y0 + 1) * 4);
      let ink = color, inkA = 1;
      for (let k = 0; k < n; k++) {
        const ang = Math.random() * TAU, len = Math.random();
        let rz = 0, ps = 1;
        if (sp.dyn.enabled) {
          if (sp.dyn.fixedRotation) rz = sp.dyn.fixedAngle * Math.PI / 180;
          if (sp.dyn.randomRotation) rz += (TAU * Math.random() - rz) * sp.dyn.randomRotationWeight;
          if (sp.dyn.followCursor) rz += (ang - rz) * sp.dyn.followCursorWeight;
          if (sp.dyn.followDrawingAngle) rz += (ctx.angle - rz) * sp.dyn.followDrawingAngleWeight;
          if (sp.dyn.randomSize) ps = Math.random();
        }
        let nx = radius * Math.cos(ang) * len, ny = radius * Math.sin(ang) * len * sp.aspect;
        [nx, ny] = [(cr * nx - sr * ny) * sp.scale, (sr * nx + cr * ny) * sp.scale];
        if (k === 0 || sp.col.colorPerParticle) {
          ink = color; inkA = 1;
          if (sp.col.useRandomHSV) ink = hslShift(ink, sp.col.hue / 180 * Math.random(), sp.col.saturation / 100 * Math.random(), sp.col.value / 100 * Math.random());
          if (sp.col.useRandomOpacity) inkA = Math.random();
        }
        const d = { scale: ps, ratio: 1, rot: -rz, w: bw * ps, h: bh * ps }, tipAt = tipOf(d, 1, 1), px0 = x + nx, py0 = y + ny, r = Math.ceil(Math.hypot(d.w, d.h) / 2) + 1;
        for (let py = Math.max(y0, Math.floor(py0 - r)); py <= Math.min(y1, Math.ceil(py0 + r)); py++) for (let px = Math.max(x0, Math.floor(px0 - r)); px <= Math.min(x1, Math.ceil(px0 + r)); px++) {
          const [m, rgb] = tipAt(px + 0.5 - px0, py + 0.5 - py0), a = m * inkA; if (a <= 0) continue;
          const i = ((py - y0) * w + px - x0) * 4, c = rgb || ink, da = buf[i + 3], oa = a + da * (1 - a);
          for (let j = 0; j < 3; j++) buf[i + j] = (c[j] * a + buf[i + j] * da * (1 - a)) / oa;
          buf[i + 3] = oa;
        }
      }
      for (let py = y0; py <= y1; py++) for (let px = x0; px <= x1; px++) {
        const i = ((py - y0) * w + px - x0) * 4; if (buf[i + 3] > 0) lay(L, (py * W + px) * 4, buf[i + 3] * opacity, [buf[i], buf[i + 1], buf[i + 2]]);
      }
      dirty[0] = Math.min(dirty[0], x0); dirty[1] = Math.min(dirty[1], y0); dirty[2] = Math.max(dirty[2], x1); dirty[3] = Math.max(dirty[3], y1);
      return null;
    }
    // KisColorSmudgeOp::paintAt with KisColorSmudgeStrategyMaskLegacy: the paint under the last dab (smearing) or its average colour (dulling),
    // the paint colour laid over it by the colour rate, then put down through the dab's mask at smudge rate times opacity.
    let smudgeLast = null;
    function smudgeDab(x0, y0, x1, y1, maskAt) {
      const sm = s.smudge, cx = (x0 + x1 + 1) / 2, cy = (y0 + y1 + 1) / 2, w = x1 - x0 + 1, h = y1 - y0 + 1;
      if (!smudgeLast) { smudgeLast = [cx, cy]; return; }
      const dx = Math.round(smudgeLast[0] - cx), dy = Math.round(smudgeLast[1] - cy); smudgeLast = [cx, cy];
      const opacity = sizeLike(s.opacity, ctx), rate = sm.rate.on ? sizeLike(sm.rate, ctx) : 1, colorRate = sm.colorRate.on ? sizeLike(sm.colorRate, ctx) : 0;
      const crOp = Math.min(1, Math.max(0, Math.max(1 - sm.rate.value, 0.2) * colorRate * opacity)), fin = Math.min(1, Math.max(0, rate * opacity));
      const px = (X, Y) => (X < 0 || Y < 0 || X >= W || Y >= H) ? [0, 0, 0, 0] : [...L.subarray((Y * W + X) * 4, (Y * W + X) * 4 + 4)];
      let dull = null;
      if (sm.mode === 1) {  // dulling: the average colour of the last dab's box, grown or shrunk by the smudge radius (Halton samples)
        const r = sm.radius.on ? sizeLike(sm.radius, ctx) : 0, sx0 = x0 + dx, sy0 = y0 + dy, gx = Math.trunc(w * 0.5 * (r - 1)), gy = Math.trunc(h * 0.5 * (r - 1));
        let rx0 = Math.floor(sx0 + w / 2), ry0 = Math.floor(sy0 + h / 2), rx1 = rx0, ry1 = ry0;
        if (r > 0) { rx0 = Math.min(rx0, sx0 - gx); ry0 = Math.min(ry0, sy0 - gy); rx1 = Math.max(rx1, sx0 + w - 1 + gx); ry1 = Math.max(ry1, sy0 + h - 1 + gy); }
        const n = (rx1 - rx0 + 1) * (ry1 - ry0 + 1), k = Math.min(n, Math.max(64, Math.round(0.02 * n))), sum = [0, 0, 0, 0];
        for (let i = 0; i < k; i++) { const c = px(rx0 + Math.floor(halton(i + 1, 2) * (rx1 - rx0)), ry0 + Math.floor(halton(i + 1, 3) * (ry1 - ry0))); for (let j = 0; j < 3; j++) sum[j] += c[j] * c[3]; sum[3] += c[3]; }
        dull = sum[3] ? [sum[0] / sum[3], sum[1] / sum[3], sum[2] / sum[3], sum[3] / k] : [0, 0, 0, 0];
      }
      const blend = new Float32Array(w * h * 4);
      for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
        const b = dull || px(x0 + x + dx, y0 + y + dy), i = (y * w + x) * 4, ba = b[3] / 255;
        const oa = crOp + ba * (1 - crOp);  // the paint colour over it (source over) at the colour rate's opacity
        for (let c = 0; c < 3; c++) blend[i + c] = oa ? (color[c] * crOp + b[c] * ba * (1 - crOp)) / oa : 0;
        blend[i + 3] = oa * 255;
      }
      for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
        const a = maskAt(x0 + x, y0 + y)[0] * fin; if (a <= 0) continue;
        const i = ((y0 + y) * W + x0 + x) * 4, j = (y * w + x) * 4;
        if (sm.smearAlpha) for (let c = 0; c < 4; c++) L[i + c] = Math.round(L[i + c] + (blend[j + c] - L[i + c]) * a);  // copy, by the mask
        else lay(L, i, a * blend[j + 3] / 255, [blend[j], blend[j + 1], blend[j + 2]]);
      }
    }
    let lastDabAt = 0;
    function place(x, y) { sp = spacingOf(dab(x, y)); acc = [0, 0]; lastDabAt = performance.now(); }
    const washRGB = i => [wash.rgb[i * 3], wash.rgb[i * 3 + 1], wash.rgb[i * 3 + 2]];
    return {
      to(x, y, pen) {  // pen: pressure, tiltX, tiltY
        ctx.pressure = pen.pressure; ctx.tiltX = pen.tiltX; ctx.tiltY = pen.tiltY; ctx.time = performance.now() - t0;
        if (!last) { place(x, y); last = [x, y]; return; }
        if (x === last[0] && y === last[1]) return;
        ctx.angle = Math.atan2(y - last[1], x - last[0]);
        let [x0, y0] = last;
        while (true) {
          let ex = x - x0, ey = y - y0;
          if (sp.rot) { const c = Math.cos(sp.rot), sn = Math.sin(sp.rot); [ex, ey] = [c * ex - sn * ey, sn * ex + c * ey]; }
          const ax = Math.abs(ex), ay = Math.abs(ey), a = (ax / sp.x) ** 2 + (ay / sp.y) ** 2;  // (acc + t·d)/spacing on the ellipse: solve for t
          const b = 2 * (acc[0] * ax / sp.x ** 2 + acc[1] * ay / sp.y ** 2), c = (acc[0] / sp.x) ** 2 + (acc[1] / sp.y) ** 2 - 1;
          const t = c >= 0 ? 0 : (-b + Math.sqrt(b * b - 4 * a * c)) / (2 * a);
          if (t > 1) { acc = [acc[0] + ax, acc[1] + ay]; break; }
          x0 += (x - x0) * t; y0 += (y - y0) * t; place(x0, y0);
        }
        last = [x, y];
      },
      tick() {  // the airbrush: with the finger held still, a dab each 1/rate second (KisPaintOpPluginUtils::effectiveTiming)
        if (!s.airbrush || !last) return;
        const now = performance.now(), every = 1000 / s.airbrush / Math.max(1e-6, sizeLike(s.rateOption, ctx));
        ctx.time = now - t0;
        if (now - lastDabAt >= every) place(last[0], last[1]);
      },
      shown(view) {  // what the paper shows in the box changed since last time: the layer with the stroke layer on it; returns the box
        const [x0, y0, x1, y1] = dirty; if (x1 < 0) return null;
        const V = view.data;
        for (let y = y0; y <= y1; y++) for (let x = x0; x <= x1; x++) {
          const i = y * W + x; for (let c = 0; c < 4; c++) V[i * 4 + c] = L[i * 4 + c];
          if (wash && wash.a[i]) lay(V, i * 4, wash.a[i] * s.opacity.value, washRGB(i));
        }
        dirty[0] = W; dirty[1] = H; dirty[2] = dirty[3] = -1;
        return [x0, y0, x1 - x0 + 1, y1 - y0 + 1];
      },
      end() {  // the stroke layer goes onto the layer at the opacity's strength, by the preset's composite op
        if (wash) for (let i = 0; i < W * H; i++) if (wash.a[i]) lay(L, i * 4, wash.a[i] * s.opacity.value, washRGB(i));
      },
    };
  }
  return { fromPreset, stroke, readGbr, readGih };
})();

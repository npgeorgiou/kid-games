// SECTION: BRUSH CORE -- Krita's brush engines, ported from Krita's source (GPL, see ../README.md) at the commit in tools/get_krita.sh.
// Standard technique: Krita's own freehand tool (KisToolFreehandHelper, basic smoothing) and paint ops (KisBrushOp, KisColorSmudgeOp, KisSprayPaintOp).
// The model, in Krita's own parts:
// 1. A preset is numbers: the tip and options whose value follows sensors (drawing angle, random, time) through curves. No pen: the pressure
//    and tilt sensors are left out, so an option that only had those keeps its strength.
// 2. The stroke: finger moves become Bezier pieces (basic smoothing), cut until flat; along them a dab goes where the spacing ellipse or the
//    airbrush time is reached (KisDistanceInformation); with fan corners extra dabs turn the brush round sharp corners.
// 3. A dab is the tip's 8-bit mask at its size, angle and sub-pixel place (reused while the precision allows, KisDabCache), times the paper
//    texture, laid by the painting mode: build-up straight on the layer, or wash into a stroke layer (alpha darken) that goes on the layer at the
//    end; a masking brush paints its own mask that cuts or adds to the stroke layer's alpha.
// 4. Two other engines share the dabs: spray (particles of the tip in a circle) and colour smudge (the paint under the last dab, or its average,
//    with the paint colour mixed in, worked in a precise copy of the layer).
// Not ported (no preset of these families turns them on): spikes, sharpness, lightness and gradient tips, the darken, mix and HSV colour options,
// spray shapes, the stabiliser and weighted smoothing; overlay mode reads the one layer the page has.
const KritaBrush = (() => {
  // SECTION: MATHS -- angles (kis_global.h, KisAlgebra2D), erf, Krita's 8-bit arithmetic (KoIntegerMaths, KoColorSpaceMaths<quint8>)
  const TAU = 2 * Math.PI, LONG_TIME = 1e12;
  const wrap = (v, lo, hi) => { const r = hi - lo; return v - r * Math.floor((v - lo) / r); };
  const normAngle = a => { if (a < 0) a = TAU + (a % TAU); return a >= TAU ? a % TAU : a; };
  const angularDistance = (a, b) => { const d = Math.abs(a - b) % TAU; return d > Math.PI ? TAU - d : d; };
  const incrementInDirection = (a, inc, dir) => angularDistance(a + inc, dir) < angularDistance(a - inc, dir) ? a + inc : a - inc;
  const samePoint = (p, q) => Math.abs(p[0] - q[0]) <= 1e-12 * Math.max(1, Math.abs(p[0])) && Math.abs(p[1] - q[1]) <= 1e-12 * Math.max(1, Math.abs(p[1]));
  const direction = (p, q, fallback) => samePoint(p, q) ? fallback : Math.atan2(q[1] - p[1], q[0] - p[0]);
  const mul = (a, b) => { const c = a * b + 0x80; return ((c >> 8) + c) >> 8; };
  const mul3 = (a, b, c) => { const t = a * b * c + 0x7F5B; return ((t >> 7) + t) >> 16; };
  const div = (a, b) => Math.floor((a * 255 + (b >> 1)) / b);
  const lerp8 = (a, b, t) => { let c = (b - a) * t + 0x80; c = ((c >> 8) + c) >> 8; return c + a; };
  const u8 = v => Math.round(Math.min(1, Math.max(0, v)) * 255);
  function erf(x) {  // the C library's erf, to double precision: series near 0, continued fraction for erfc further out
    const ax = Math.abs(x); let r;
    if (ax < 3) { let term = ax, sum = ax; for (let n = 1; n < 80; n++) { term *= -ax * ax / n; const d = term / (2 * n + 1); sum += d; if (Math.abs(d) < 1e-17 * Math.abs(sum)) break; } r = sum * 2 / Math.sqrt(Math.PI); }
    else { let f = 0; for (let n = 60; n >= 1; n--) f = n / 2 / (ax + f); r = 1 - Math.exp(-ax * ax) / Math.sqrt(Math.PI) / (ax + f); }
    return x < 0 ? -r : r;
  }
  function erfFast(x) {  // VcExtraMath::erf, what Krita's vectorised masks use (Abramowitz-Stegun 7.1.26, 1 from 9.3 on)
    let xa = Math.abs(x); if (xa >= 9.3) return Math.sign(x) || 1;
    const t = 1 / (1 + 0.3275911 * xa);
    const y = 1 - (((((1.061405429 * t - 1.453152027) * t) + 1.421413741) * t - 0.284496736) * t + 0.254829592) * t * Math.exp(-xa * xa);
    return x < 0 ? -y : y;
  }
  const attrs = s => { const o = {}; for (const [, k, v] of (s || '').matchAll(/(\w+)="([^"]*)"/g)) o[k] = v; return o; };

  // SECTION: CURVE -- KisCubicCurve: a cubic per interval through the points, second derivative 0 at the ends and at corners (KisCubicSpline),
  // clamped to 0..1; sensors and tips read it through a sampled table with linear steps (floatTransfer, interpolateLinear)
  function curvePoints(str) { return (str || '0,0;1,1;').split(';').filter(Boolean).map(p => { const v = p.split(','); return { x: +v[0], y: +v[1], corner: v.slice(2).includes('is_corner') }; }).sort((a, b) => a.x - b.x); }
  function isIdentity(pts) { return pts[0].x === 0 && pts[0].y === 0 && pts.at(-1).x === 1 && pts.at(-1).y === 1 && pts.slice(1, -1).every(p => Math.abs(p.x - p.y) <= 1e-12 * Math.max(Math.abs(p.x), Math.abs(p.y))); }
  function solve(A, b) {  // Gaussian elimination with partial pivoting (Krita uses Eigen's sparse LU)
    const n = b.length;
    for (let c = 0; c < n; c++) {
      let p = c; for (let r = c + 1; r < n; r++) if (Math.abs(A[r][c]) > Math.abs(A[p][c])) p = r;
      [A[c], A[p]] = [A[p], A[c]]; [b[c], b[p]] = [b[p], b[c]];
      for (let r = c + 1; r < n; r++) { const f = A[r][c] / A[c][c]; if (!f) continue; for (let k = c; k < n; k++) A[r][k] -= f * A[c][k]; b[r] -= f * b[c]; }
    }
    const x = new Array(n).fill(0);
    for (let r = n - 1; r >= 0; r--) { let s = b[r]; for (let k = r + 1; k < n; k++) s -= A[r][k] * x[k]; x[r] = s / A[r][r]; }
    return x;
  }
  function spline(pts) {
    const n = pts.length - 1;
    if (n === 0) return () => pts[0].y;
    if (n === 1) { const c = (pts[1].y - pts[0].y) / (pts[1].x - pts[0].x), d = pts[0].y - c * pts[0].x; return x => c * x + d; }
    const N = 4 * n, A = Array.from({ length: N }, () => new Array(N).fill(0)), b = new Array(N).fill(0); let row = 0;
    const pos = (i, X, Y) => { A[row][4 * i] = X ** 3; A[row][4 * i + 1] = X * X; A[row][4 * i + 2] = X; A[row][4 * i + 3] = 1; b[row++] = Y; };
    const second = (i, X, sign = 1) => { A[row][4 * i] += sign * 6 * X; A[row][4 * i + 1] += sign * 2; };
    for (let i = 0; i < n; i++) { pos(i, pts[i].x, pts[i].y); pos(i, pts[i + 1].x, pts[i + 1].y); }
    second(0, pts[0].x); row++; second(n - 1, pts[n].x); row++;
    for (let i = 1; i < n; i++) {
      const X = pts[i].x;
      if (pts[i].corner) { second(i - 1, X); row++; second(i, X); row++; continue; }
      A[row][4 * i - 4] = 3 * X * X; A[row][4 * i - 3] = 2 * X; A[row][4 * i - 2] = 1; A[row][4 * i] = -3 * X * X; A[row][4 * i + 1] = -2 * X; A[row][4 * i + 2] = -1; row++;
      second(i - 1, X); second(i, X, -1); row++;
    }
    const k = solve(A, b);
    return x => { let i = 0; while (i < n - 1 && !(x < pts[i + 1].x)) i++; return k[4 * i] * x ** 3 + k[4 * i + 1] * x * x + k[4 * i + 2] * x + k[4 * i + 3]; };
  }
  function curveValue(pts) { const s = spline(pts); return x => Math.min(1, Math.max(0, s(Math.min(pts.at(-1).x, Math.max(pts[0].x, x))))); }
  function transfer(pts, size) { const v = curveValue(pts), out = new Float64Array(size); for (let i = 0; i < size; i++) out[i] = v(i / (size - 1)); return out; }
  function interpolateLinear(x, t) {
    const max = t.length - 1, bx = Math.min(max, Math.max(0, max * x)), lo = Math.floor(bx), hi = Math.ceil(bx), f = bx - lo;
    const v = f < 1e-6 ? t[lo] : f > 1 - 1e-6 ? t[hi] : t[lo] + f * (t[hi] - t[lo]);
    return Math.sign(x) < 0 || Object.is(x, -0) ? -Math.abs(v) : Math.abs(v);
  }

  // SECTION: PRESET -- a preset file of krita/presets/ (one "name = value" a line) into the brush's settings, as Krita's option data read them
  function parse(text) { const f = {}; for (const l of text.split('\n')) { const i = l.indexOf(' = '); if (i > 0) f[l.slice(0, i)] = l.slice(i + 3); } return f; }
  const PEN = { pressure: 1, pressurein: 1, tangentialpressure: 1, ascension: 1, declination: 1, xtilt: 1, ytilt: 1, rotation: 1, perspective: 1 };  // sensors only a pen has
  function sensorList(def) {  // KisKritaSensorPack::read: the sensors with their curves, and the common curve (the last one listed)
    if (!def) return { list: [{ id: 'pressure', curve: null }], common: null };
    const one = (tag, body) => { const m = /<curve>([^<]*)<\/curve>/.exec(body || ''); return { ...attrs(tag), curve: m ? m[1] : '0,0;1,1;' }; };
    const list = /id="sensorslist"/.test(def) ? [...def.matchAll(/<ChildSensor([^>]*?)(?:\/>|>(.*?)<\/ChildSensor>)/g)].map(m => one(m[1], m[2]))
      : (m => [one(m[1], m[2])])(/<params([^>]*?)(?:\/>|>(.*?)<\/params>)/.exec(def));
    return { list, common: list.length ? list.at(-1).curve : '0,0;1,1;' };
  }
  function option(f, id, checkable, range = [0, 1], pfx = '') {  // KisCurveOptionData: on when not checkable or checked; sensors through their curves
    const k = s => f[pfx + id + s], def = k('Sensor') || '', { list, common } = sensorList(def), same = (k('UseSameCurve') ?? 'true') === 'true';
    let commonCurve = def.includes('curve') ? common : f[pfx + 'Custom' + id] === 'true' ? f[pfx + 'Curve' + id] || '0,0;1,1;' : '0,0;1,1;';
    if (same) commonCurve = k('commonCurve') || commonCurve;
    const sensors = list.filter(s => !PEN[s.id]).map(s => {
      const pts = curvePoints(same ? commonCurve : s.curve);
      return { ...s, table: isIdentity(pts) ? null : transfer(pts, 256), angleOffset: +(s.angleOffset ?? 0), lockedAngleMode: s.lockedAngleMode === '1',
        fanCorners: s.fanCornersEnabled === '1', fanStep: +(s.fanCornersStep ?? 30), periodic: s.periodic === '1', length: +(s.duration ?? 1000) };
    });
    return { id, raw: list, on: !checkable || f[pfx + 'Pressure' + id] === 'true', useCurve: (k('UseCurve') ?? 'true') === 'true', value: +(k('Value') ?? 1), mode: +(k('curveMode') ?? 0), sensors, range };
  }
  function tipOf(f, pfx) {
    const def = f[pfx + 'brush_definition'] || '', t = attrs((/<Brush([^>]*)>/.exec(def) || [])[1]), g = attrs((/<MaskGenerator([^>]*)>/.exec(def) || [])[1]);
    return { type: t.type, file: t.filename, scale: +(t.scale ?? 1), angle: +(t.angle ?? 0), colorAsMask: (t.ColorAsMask ?? '1') === '1',
      spacing: Math.max(0.02, +(t.spacing ?? 0.1)), useAutoSpacing: t.useAutoSpacing === '1', autoSpacingCoeff: +(t.autoSpacingCoeff ?? 1),
      randomness: +(t.randomness ?? 0), density: +(t.density ?? 1),
      gen: { shape: g.type, id: g.id || 'default', diameter: +(g.diameter ?? 0), ratio: +(g.ratio ?? 1), hfade: +(g.hfade ?? 0), vfade: +(g.vfade ?? 0),
        antialias: g.antialiasEdges === '1', softCurve: curvePoints(g.softness_curve || '0,1;1,0;') } };
  }
  function fromPreset(text) { return settingsOf(parse(text), ''); }
  function settingsOf(f, pfx) {
    const g = k => f[pfx + k], P = 'Texture/Pattern/', paintop = g('paintop') || 'paintbrush';
    const s = {
      paintop, tip: tipOf(f, pfx), compositeOp: g('CompositeOp') || 'normal', wash: paintop !== 'colorsmudge' && (g('PaintOpAction') ?? '2') !== '1',
      size: option(f, 'Size', true, [0, 1], pfx), opacity: option(f, 'Opacity', false, [0, 1], pfx), flow: option(f, 'Flow', false, [0, 1], pfx),
      rotation: option(f, 'Rotation', true, [0, 1], pfx), ratio: option(f, 'Ratio', true, [0, 1], pfx), scatter: option(f, 'Scatter', true, [0, 5], pfx),
      mirror: option(f, 'Mirror', true, [0, 1], pfx), softness: option(f, 'Softness', true, [0.1, 1], pfx), spacing: option(f, 'Spacing', true, [0, 1], pfx),
      rate: option(f, 'Rate', true, [0, 1], pfx),
      scatterX: (g('Scattering/AxisX') ?? 'true') === 'true', scatterY: (g('Scattering/AxisY') ?? 'true') === 'true',
      mirrorH: g('HorizontalMirrorEnabled') === 'true', mirrorV: g('VerticalMirrorEnabled') === 'true', isotropic: g('Spacing/Isotropic') === 'true',
      airbrush: g('PaintOpSettings/isAirbrushing') === 'true', airbrushRate: +(g('PaintOpSettings/rate') ?? 20), ignoreSpacing: g('PaintOpSettings/ignoreSpacing') === 'true',
      spacingUpdates: g('PaintOpSettings/updateSpacingBetweenDabs') === 'true',
      precision: { level: +(g('KisPrecisionOption/precisionLevel') ?? 5), auto: g('KisPrecisionOption/AutoPrecisionEnabled') === 'true' },
      texture: g(P + 'Enabled') !== 'true' ? null : {
        pattern: g(P + 'Name'), scale: +(g(P + 'Scale') ?? 1), brightness: +(g(P + 'Brightness') ?? 0), contrast: +(g(P + 'Contrast') ?? 1),
        neutralPoint: +(g(P + 'NeutralPoint') ?? 0.5), invert: g(P + 'Invert') === 'true', autoInvertOnErase: g(P + 'AutoInvertOnErase') === 'true',
        cutoffPolicy: +(g(P + 'CutoffPolicy') ?? 0), cutoffLeft: +(g(P + 'CutoffLeft') ?? 0), cutoffRight: +(g(P + 'CutoffRight') ?? 255),
        mode: +(g(P + 'TexturingMode') ?? 0), soft: g(P + 'UseSoftTexturing') === 'true',
        offsetX: +(g(P + 'OffsetX') ?? 0), offsetY: +(g(P + 'OffsetY') ?? 0), randomX: g(P + 'isRandomOffsetX') === 'true', randomY: g(P + 'isRandomOffsetY') === 'true',
        strength: option(f, 'Texture/Strength/', true, [0, 1], pfx) },
    };
    const angleSensor = s.rotation.on && s.rotation.sensors.find(x => x.id === 'drawingangle');  // KisRotationOption::applyFanCornersInfo
    s.fan = angleSensor && angleSensor.fanCorners && !angleSensor.lockedAngleMode ? angleSensor.fanStep * Math.PI / 180 : 0;
    if (paintop === 'colorsmudge') s.smudge = {
      dulling: +(g('SmudgeRateMode') ?? 0) === 1, smearAlpha: (g('SmudgeRateSmearAlpha') ?? 'true') !== 'false', overlay: g('MergedPaint') === 'true',
      rate: option(f, 'SmudgeRate', true, [0, 1], pfx), colorRate: option(f, 'ColorRate', true, [0, 1], pfx),
      radius: (o => { if (+(g('SmudgeRadiusVersion') ?? 1) < 2) o.value /= 100; return o; })(option(f, 'SmudgeRadius', true, [0, 3], pfx)) };
    if (paintop === 'spraybrush') {
      const old = (g('ShapeDynamicsVersion') ?? '2.2') === '2.2', d = old ? 'SprayShape/' : 'ShapeDynamics/';
      s.spray = {  // KisSprayOpOptionData, KisSprayShapeDynamicsOptionData, KisColorOptionData; the particle is the brush tip (shapes off in every preset)
        diameter: Math.trunc(+(g('Spray/diameter') ?? 0)), aspect: +(g('Spray/aspect') ?? 0), rotation: +(g('Spray/rotation') ?? 0), scale: +(g('Spray/scale') ?? 0),
        spacing: +(g('Spray/spacing') ?? 0), jitter: g('Spray/jitterMovement') === 'true', jitterAmount: +(g('Spray/jitterMoveAmount') ?? 0),
        useDensity: g('Spray/useDensity') === 'true', coverage: +(g('Spray/coverage') ?? 0) / 100, particleCount: +(g('Spray/particleCount') ?? 0),
        angular: g('Spray/angularDistributionType') === 'curveBased' ? { curve: g('Spray/angularDistributionCurve'), repeat: +(g('Spray/angularDistributionCurveRepeat') ?? 1) } : null,
        radial: (t => t === 'uniform' || t === 'gaussian' || t === 'clusterBased' || t === 'curveBased' ? t : g('Spray/gaussianDistribution') === 'true' ? 'gaussian' : 'uniform')(g('Spray/radialDistributionType')),
        stdDev: +(g('Spray/radialDistributionStdDeviation') ?? 0.5), clustering: +(g('Spray/radialDistributionClusteringAmount') ?? 0),
        radialCurve: g('Spray/radialDistributionCurve'), radialRepeat: +(g('Spray/radialDistributionCurveRepeat') ?? 1), centerBiased: (g('Spray/radialDistributionCenterBiased') ?? 'true') === 'true',
        dyn: { enabled: old || g('ShapeDynamics/enabled') === 'true', randomSize: g(d + 'randomSize') === 'true', fixedRotation: g(d + 'fixedRotation') === 'true',
          fixedAngle: Math.trunc(+(g(d + 'fixedAngle') ?? 0)), randomRotation: g(d + 'randomRotation') === 'true', randomRotationWeight: +(g(d + 'randomRotationWeight') ?? 0),
          followCursor: g(d + 'followCursor') === 'true', followCursorWeight: +(g(d + 'followCursorWeigth') ?? 0),
          followDrawingAngle: g(d + 'followDrawingAngle') === 'true', followDrawingAngleWeight: +(g(d + 'followDrawingAngleWeigth') ?? 0) },
        col: { colorPerParticle: g('ColorOption/colorPerParticle') === 'true', useRandomHSV: g('ColorOption/useRandomHSV') === 'true', useRandomOpacity: g('ColorOption/useRandomOpacity') === 'true',
          hue: +(g('ColorOption/hue') ?? 0), saturation: +(g('ColorOption/saturation') ?? 0), value: +(g('ColorOption/value') ?? 0) } };
      const sp = s.spray; s.sprayStep = sp.diameter * 0.5 > 1 ? sp.diameter * 0.5 * sp.spacing : 1;
    }
    if (!pfx && f['MaskingBrush/Enabled'] === 'true') s.masking = {  // KisPaintOpSettings::createMaskingSettings
      settings: settingsOf(f, 'MaskingBrush/Preset/'), op: f['MaskingBrush/MaskingCompositeOp'] || 'multiply',
      useMasterSize: (f['MaskingBrush/UseMasterSize'] ?? 'true') === 'true', coeff: +(f['MaskingBrush/MasterSizeCoeff'] ?? 1) };
    return s;
  }

  // SECTION: SENSORS AND OPTIONS -- what the stroke tells each dab (KisDynamicSensor*), and the options' values (KisCurveOption)
  function sensorValue(s, info) {
    switch (s.id) {
      case 'fuzzy': return 2 * Math.random() - 1;
      case 'fuzzystroke': return info.stroke.random[s.key] ??= 2 * Math.random() - 1;
      case 'drawingangle': { let r = 0.5 + info.drawingAngle / TAU + s.angleOffset / 360; if (r > 1) r -= 1; return r; }
      case 'time': return (s.periodic ? info.time % s.length : Math.min(info.time, s.length)) / s.length;
      default: return 1;
    }
  }
  const ADDITIVE = { fuzzy: 1, fuzzystroke: 1 }, ABSOLUTE = { drawingangle: 1 };
  function sensorParameter(s, info, optionId) {  // KisDynamicSensor::parameter
    s.key ??= optionId + 'FuzzyStroke';
    const v = sensorValue(s, info); if (!s.table) return v;
    const add = ADDITIVE[s.id], abs = ABSOLUTE[s.id];
    const x = interpolateLinear(add ? 0.5 * (1 + v) : abs ? wrap(v + 0.5, 0, 1) : v, s.table);
    return add ? 2 * x - 1 : abs ? wrap(x + 0.5, 0, 1) : x;
  }
  function components(o, info, useStrength = true) {  // KisCurveOption::computeValueComponents
    const c = { constant: useStrength ? o.value : 1, scaling: 1, additive: 0, hasScaling: false, hasAdditive: false, hasAbs: false, abs: 0 };
    if (!o.useCurve) return c;
    const scal = [];
    for (const s of o.sensors) {
      const v = sensorParameter(s, info, o.id);
      if (ADDITIVE[s.id]) { c.additive += v; c.hasAdditive = true; } else if (ABSOLUTE[s.id]) { c.abs = v; c.hasAbs = true; } else { scal.push(v); c.hasScaling = true; }
    }
    if (scal.length === 1) c.scaling = scal[0];
    else if (scal.length > 1) c.scaling = o.mode === 1 ? scal.reduce((a, b) => a + b) : o.mode === 2 ? Math.max(...scal) : o.mode === 3 ? Math.min(...scal)
      : o.mode === 4 ? Math.max(...scal) - Math.min(...scal) : scal.reduce((a, b) => a * b);
    return c;
  }
  function sizeLike(o, info, useStrength = true) {  // computeSizeLikeValue
    const c = components(o, info, useStrength);
    return Math.max(o.range[0], Math.min(o.range[1], c.constant * (c.hasAbs ? c.abs : 1) * (c.hasScaling ? c.scaling : 1) * (c.hasAdditive ? 0.5 * (1 + c.additive) : 1)));
  }
  const checked = (o, info, off = 1) => o.on ? sizeLike(o, info) : off;
  function rotationOf(o, info) {  // KisRotationOption::apply, canvas not turned or mirrored
    if (!o.on) return 0;
    const c = components(o, info), v = wrap(2 * (c.hasAbs ? c.abs : 0) + c.constant * (-1 * (c.hasScaling ? 2 * c.scaling - 1 : 0) + (c.hasAdditive ? c.additive : 0)), -1, 1);
    return normAngle((1 - v) * Math.PI);
  }
  function mirrorOf(s, info) {  // KisMirrorOption::apply
    let h = false, v = false;
    if (s.mirror.on && (s.mirrorH || s.mirrorV)) { const r = sizeLike(s.mirror, info) >= 0.5; h = r && s.mirrorH; v = r && s.mirrorV; }
    return { h, v, flipped: (h || v) && s.mirrorH !== s.mirrorV && h !== v };
  }

  // SECTION: TIPS -- the brush: auto tips computed by Krita's mask generators, picture tips scaled through Krita's image pyramid
  function hslShift(c, dh, ds, dl) {  // KisHSVAdjustment, HSL in compatibility mode: hue turned, saturation scaled, lightness towards white
    const [r, g, b] = c.map(v => v / 255), M = Math.max(r, g, b), m = Math.min(r, g, b);
    let l = (M + m) / 2, sat = M === m ? 0 : (l > 0.5 ? (M - m) / (2 - M - m) : (M - m) / (M + m)), h = 0;
    if (M !== m) h = 60 * (M === r ? (g - b) / (M - m) + (g < b ? 6 : 0) : M === g ? (b - r) / (M - m) + 2 : (r - g) / (M - m) + 4);
    h = wrap(h + dh * 180, 0, 360); sat = Math.min(1, sat * (ds + 1)); l = dl < 0 ? l * (dl + 1) : l + dl * (1 - l);
    const q = l < 0.5 ? l * (1 + sat) : l + sat - l * sat, p = 2 * l - q;
    const fn = t => { t = wrap(t, 0, 1); return t < 1 / 6 ? p + (q - p) * 6 * t : t < 1 / 2 ? q : t < 2 / 3 ? p + (q - p) * (2 / 3 - t) * 6 : p; };
    return [fn(h / 360 + 1 / 3), fn(h / 360), fn(h / 360 - 1 / 3)].map(v => Math.round(v * 255));
  }
  // A picture: { w, h, px: Float32Array premultiplied RGBA 0..255 }. Qt's smooth scaling: box averaging down, bilinear up.
  function scaleImage(img, w, h) {
    const out = new Float32Array(w * h * 4), sx = img.w / w, sy = img.h / h;
    if (sx >= 1 && sy >= 1) for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
      const x0 = x * sx, x1 = x0 + sx, y0 = y * sy, y1 = y0 + sy, o = (y * w + x) * 4;
      for (let j = Math.floor(y0); j < Math.ceil(y1); j++) { const wy = Math.min(y1, j + 1) - Math.max(y0, j);
        for (let i = Math.floor(x0); i < Math.ceil(x1); i++) { const k = wy * (Math.min(x1, i + 1) - Math.max(x0, i)) / (sx * sy), p = (Math.min(img.h - 1, j) * img.w + Math.min(img.w - 1, i)) * 4;
          for (let c = 0; c < 4; c++) out[o + c] += img.px[p + c] * k; } }
    } else for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) bilinear(img, (x + 0.5) * sx, (y + 0.5) * sy, out, (y * w + x) * 4, true);
    return { w, h, px: out };
  }
  function bilinear(img, u, v, out, o, clamp) {  // a sample at (u, v) in pixel units; outside the picture is empty unless clamped to the edge
    const x = u - 0.5, y = v - 0.5, x0 = Math.floor(x), y0 = Math.floor(y), fx = x - x0, fy = y - y0;
    for (let c = 0; c < 4; c++) out[o + c] = 0;
    for (const [i0, j0, k] of [[x0, y0, (1 - fx) * (1 - fy)], [x0 + 1, y0, fx * (1 - fy)], [x0, y0 + 1, (1 - fx) * fy], [x0 + 1, y0 + 1, fx * fy]]) {
      if (!k) continue; let i = i0, j = j0;
      if (clamp) { i = Math.min(img.w - 1, Math.max(0, i)); j = Math.min(img.h - 1, Math.max(0, j)); } else if (i < 0 || j < 0 || i >= img.w || j >= img.h) continue;
      const p = (j * img.w + i) * 4; for (let c = 0; c < 4; c++) out[o + c] += img.px[p + c] * k;
    }
  }
  function pyramid(img) {  // KisQImagePyramid: levels from 8x down to a pixel, with the largest level not past 512 px
    const levels = []; let baseScale = 1, sc = 8;
    for (; sc > 1; sc *= 0.5) { const w = Math.round(img.w * sc), h = Math.round(img.h * sc); if (w <= 512 || h <= 512) { if (!levels.length) baseScale = sc; levels.push(scaleImage(img, w, h)); } }
    levels.push(img);
    for (sc = 0.5; ; sc *= 0.5) { const w = Math.round(img.w * sc), h = Math.round(img.h * sc); if (!w || !h) break; levels.push(scaleImage(img, w, h)); }
    return { levels, baseScale, w: img.w, h: img.h };
  }
  // QTransform as [m11, m12, m21, m22, dx, dy]: a point maps to (m11 x + m21 y + dx, m12 x + m22 y + dy); A then B is mulT(A, B)
  const mulT = (a, b) => [a[0] * b[0] + a[1] * b[2], a[0] * b[1] + a[1] * b[3], a[2] * b[0] + a[3] * b[2], a[2] * b[1] + a[3] * b[3], a[4] * b[0] + a[5] * b[2] + b[4], a[4] * b[1] + a[5] * b[3] + b[5]];
  const mapRect = (t, w, h) => { const xs = [], ys = []; for (const [x, y] of [[0, 0], [w, 0], [0, h], [w, h]]) { xs.push(t[0] * x + t[2] * y + t[4]); ys.push(t[1] * x + t[3] * y + t[5]); }
    const x = Math.min(...xs), y = Math.min(...ys); return { x, y, w: Math.max(...xs) - x, h: Math.max(...ys) - y }; };
  function brushTransform(sx, sy, rot, subX, subY, w, h) {  // baseBrushTransform: scale, turn and move back into positive space, then the sub-pixel shift
    let t = [sx, 0, 0, sy, 0, 0];
    if (rot && !Number.isNaN(rot)) { t = mulT(t, [Math.cos(rot), Math.sin(rot), -Math.sin(rot), Math.cos(rot), 0, 0]); const r = mapRect(t, w, h); t = mulT(t, [1, 0, 0, 1, -r.x, -r.y]); }
    return mulT(t, [1, 0, 0, 1, subX, subY]);
  }
  function imageParams(sx, sy, rot, subX, subY, ow, oh, bw = ow, bh = oh) {  // KisQImagePyramid::calculateParams: the dab's size and the level's transform
    const r = mapRect(brushTransform(sx, sy, rot, subX, subY, ow, oh), ow, oh), t = brushTransform(sx / (bw / ow), sy / (bh / oh), rot, subX, subY, bw, bh);
    if (!(r.w > 0 && r.h > 0)) return { w: 1, h: 1, t };
    let x = r.x, y = r.y, w = r.w, h = r.h;  // roundRect
    if (x < 1e-6) { w += x; x = 0; } if (y < 1e-6) { h += y; y = 0; }
    if (Math.abs(w - Math.round(w)) < 1e-6) w = Math.round(w); if (Math.abs(h - Math.round(h)) < 1e-6) h = Math.round(h);
    return { w: Math.max(1, Math.ceil(x + w)), h: Math.max(1, Math.ceil(y + h)), t };
  }
  function brushOf(s, assets) {  // KisBrush: the tip's size, hot spot, mask sizes and its mask or stamp for a dab
    const tip = s.tip, auto = tip.type === 'auto_brush';
    let cells = null, selection = 'random';
    if (!auto) {
      const a = assets[tip.file], stamp = color => color && !tip.colorAsMask;  // KisPredefinedBrushFactory: a colour picture is a stamp unless used as a mask
      const raw = a.gih ? a.gih.cells : [a.gbr || (im => ({ w: im.w, h: im.h, px: im.px, color: [...Array(im.w * im.h).keys()].some(i => im.px[i * 4] !== im.px[i * 4 + 1] || im.px[i * 4 + 1] !== im.px[i * 4 + 2]) }))(a.image)];
      if (a.gih) selection = a.gih.selection;
      const pictures = a.pictures ||= raw.map(c => { const px = new Float32Array(c.w * c.h * 4);  // premultiplied, with their pyramids made once
        for (let i = 0; i < c.w * c.h; i++) { const al = c.px[i * 4 + 3]; for (let k = 0; k < 3; k++) px[i * 4 + k] = c.px[i * 4 + k] * al / 255; px[i * 4 + 3] = al; }
        return { color: c.color, img: { w: c.w, h: c.h, px }, pyr: null }; });
      cells = pictures.map(c => ({ stamp: stamp(c.color), img: c.img, get pyr() { return c.pyr; }, set pyr(v) { c.pyr = v; } }));
    }
    const g = tip.gen, W = auto ? Math.max(1, Math.trunc(Math.max(1, g.diameter))) : cells[0].img.w, H = auto ? Math.max(1, Math.trunc(Math.max(1, g.diameter * g.ratio))) : cells[0].img.h;
    const softTable = auto && g.id === 'soft' ? { res: Math.round(Math.max(g.diameter, g.diameter * g.ratio) * 4) } : null;
    if (softTable) softTable.base = transfer(g.softCurve, softTable.res + 2);
    const brush = {
      auto, cells, selection, width: W, height: H, scale: auto ? 1 : tip.scale, angle: tip.angle, cell: 0,
      supportsCaching: !auto || (Math.abs(tip.density - 1) < 1e-12 && Math.abs(tip.randomness) < 1e-12),
      characteristic(scale, ratio, rot) { const r = mapRect(brushTransform(scale * this.scale, scale * this.scale * ratio, normAngle(rot + this.angle), 0, 0, W, H), W, H); return [r.w, r.h]; },
      hotSpot(d) { const [w, h] = this.characteristic(d.scale, d.ratio, d.rot); return [Math.max(1, w) / 2, Math.max(1, h) / 2]; },
      maskSize(d, subX, subY) { const p = imageParams(d.scale * this.scale, d.scale * this.scale * d.ratio, normAngle(d.rot + this.angle), subX, subY, W, H); return [p.w, p.h]; },
      prepare(info, seqNo) {  // KisImagePipeBrush::prepareForSeqNo: the cell of this dab
        if (cells) this.cell = cells.length < 2 ? 0 : selection === 'incremental' ? seqNo % cells.length : selection === 'angular' ? Math.floor(normAngle(info.drawingAngle) / TAU * cells.length) % cells.length : Math.floor(Math.random() * cells.length);
      },
      dab(d, subX, subY, softness) {  // the dab: { w, h, a: Uint8Array (opacity 0..255), rgb: Uint8Array or null (a stamp's own colours) }
        return auto ? autoDab(this, d, subX, subY, softness) : pictureDab(this, d, subX, subY);
      },
    };
    function autoDab(b, d, subX, subY, softness) {  // KisAutoBrush::generateMaskAndApplyMaskOrCreateDab with Krita's mask applicators
      const [w, h] = b.maskSize(d, subX, subY), [hx, hy] = b.hotSpot(d), cx = hx - 0.5 + subX, cy = hy - 0.5 + subY, ang = d.rot + b.angle, ca = Math.cos(ang), sa = Math.sin(ang);
      const ew = g.diameter * d.scale, eh = g.diameter * g.ratio * d.scale * d.ratio, a = new Uint8Array(w * h);
      if (!(ew > 0 && eh > 0)) return { w, h, a, rgb: null };
      const superSample = g.antialias && (ew < 10 || eh < 10), ss = superSample ? (ew < 1 || eh < 1 ? 6 : 3) : 1, fade = maskFade(ew, eh, softness, superSample);
      for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
        let v;
        if (ss === 1) {  // vectorised path: a float fade, the opacity rounded once
          const X = x - cx, Y = y - cy; v = Math.round((1 - fade(ca * X - sa * Y, sa * X + ca * Y)) * 255);
        } else {  // scalar path, small antialiased tips: 8-bit fades on an ss x ss grid from the pixel's corner, averaged with integer division
          let sum = 0;
          for (let sy = 0; sy < ss; sy++) for (let sx = 0; sx < ss; sx++) { const X = x + sx / ss - cx, Y = y + sy / ss - cy; sum += fade(ca * X - sa * Y, sa * X + ca * Y); }
          v = 255 - Math.trunc(sum / (ss * ss));
        }
        if (tip.randomness) v = Math.trunc(v * ((1 - tip.randomness) + tip.randomness * Math.random()));
        if (tip.density !== 1 && v !== 0 && !(tip.density >= Math.random())) v = 0;
        a[y * w + x] = Math.max(0, Math.min(255, v));
      }
      return { w, h, a, rgb: null };
    }
    // The generators' fade at a point of the dab (none = full paint): the scalar path gives Krita's 8-bit values 0..255 (valueAt),
    // the vectorised path floats 0..1 (FastRowProcessor); both with their antialiasing fade makers (KisAntialiasingFadeMaker1D).
    function maskFade(ew, eh, softness, scalar) {
      const xc = 2 / ew, yc = 2 / eh, aa = g.antialias ? 1 : 0, top = scalar ? 255 : 1, q = v => scalar ? Math.max(0, Math.min(255, Math.trunc(v * 255))) : v;
      if (g.id === 'gauss') {  // KisGaussCircleMaskGenerator
        let fd = 1 - (g.hfade + g.vfade) / 2; if (fd === 0) fd = 1e-6; else if (fd === 1) fd = 1 - 1e-6;
        const center = 2.5 * (6761 * fd - 10000) / (Math.SQRT2 * 6761 * fd), alphaf = 255 / (2 * erf(center)), distf = Math.SQRT2 * 12500 / (6761 * fd * ew / 2), yr = ew / eh;
        const base = (E, dist) => 255 - Math.max(0, Math.min(255, Math.trunc(alphaf * (E(dist * distf + center) - E(dist * distf - center)))));
        const R = 0.5 * ew, start = Math.max(0, R - 1), startV = base(erf, start), coeff = Math.max(0, 255 - startV) / (R - start);
        return (x, y) => {
          const dist = Math.hypot(x, y * yr);
          if (dist > R) return top;
          if (aa && dist > start) return scalar ? Math.min(255, Math.trunc(startV + (dist - start) * coeff)) : (startV + (dist - start) * coeff) / 255;
          if (scalar) return base(erf, dist);
          const full = alphaf * (erfFast(dist * distf + center) - erfFast(dist * distf - center));
          return (255 - (full < 0 ? 0 : full > 254.974 ? 255 : full)) / 255;
        };
      }
      if (g.id === 'soft') {  // KisCurveCircleMaskGenerator: the softness curve over the squared distance, softened by the softness option
        if (softness !== 1) {  // setSoftness: a softness of 1 keeps the curve last made
          const pts = g.softCurve.map(p => ({ ...p }));
          if (pts.length === 2) pts.splice(1, 0, { x: (pts[0].x + pts[1].x) / 2, y: Math.min(1, Math.max(0, (pts[0].y + pts[1].y) / 2 * softness)), corner: false });  // transformCurveForSoftness
          else for (let i = 1; i < pts.length - 1; i++) pts[i].y = Math.min(1, Math.max(0, pts[i].y * softness));
          softTable.cur = transfer(pts, softTable.res + 2);
        }
        const data = softTable.cur || softTable.base, value = n => { const dd = n * softTable.res, i = Math.trunc(dd), f = dd - i; return (1 - f) * data[i] + f * data[i + 1]; };
        const xf = Math.max(0, (1 / xc - 1) * xc), yf = Math.max(0, (1 / yc - 1) * yc), start = (0.5 * (xf + yf)) ** 2;  // setSquareNormCoeffs
        const startV = Math.trunc((1 - value(start)) * 255), coeff = Math.max(0, 255 - startV) / (1 - start);
        return (x, y) => {
          const n = (x * xc) ** 2 + (y * yc) ** 2;
          if (n > 1) return top;
          if (aa && n > start) return scalar ? Math.min(255, Math.trunc(startV + (n - start) * coeff)) : (startV + (n - start) * coeff) / 255;
          const al = value(n); return scalar ? Math.max(0, Math.min(255, Math.trunc((1 - al) * 255))) : al >= 1 ? 0 : 1 - Math.max(0, al);
        };
      }
      const soft = 1 / Math.max(0.01, softness), fx = (g.hfade === 0 ? 1 : 2 / (g.hfade * ew)) * soft, fy = (g.vfade === 0 ? 1 : 2 / (g.vfade * eh)) * soft;
      if (g.shape === 'rect') return (x, y) => {  // KisRectangleMaskGenerator
        x = Math.abs(x); y = Math.abs(y); const nx = x * xc, ny = y * yc; if (nx > 1 || ny > 1) return top;
        const fxr = (x + aa) * fx, fyr = (y + aa) * fy, fxn = nx * (fxr - 1) / (fxr - nx), fyn = ny * (fyr - 1) / (fyr - ny);
        let v = 0; if (fxr > 1) v = fxn; if (fxn < fyn && fyr > 1) v = fyn; return q(v);
      };
      return (x, y) => {  // KisCircleMaskGenerator
        const n = (x * xc) ** 2 + (y * yc) ** 2; if (n > 1) return top;
        const nf = ((Math.abs(x) + aa) * fx) ** 2 + ((Math.abs(y) + aa) * fy) ** 2; if (nf < 1) return 0;
        return q(n * (nf - 1) / (nf - n));
      };
    }
    function pictureDab(b, d, subX, subY) {  // KisBrush::generateMaskAndApplyMaskOrCreateDab: the pyramid level nearest the scale, drawn smoothly turned and scaled
      const c = cells[b.cell], pyr = c.pyr ||= pyramid(c.img), scale = d.scale * b.scale, rot = -normAngle(d.rot + b.angle);
      let level = 0, ls = pyr.baseScale; while ((0.5 * ls > scale || Math.abs(0.5 * ls - scale) < 1e-6) && level < pyr.levels.length - 1) { ls *= 0.5; level++; }
      const L = pyr.levels[level], p = imageParams(scale, scale * d.ratio, rot, subX, subY, pyr.w, pyr.h, L.w, L.h), t = p.t;
      const det = t[0] * t[3] - t[1] * t[2], inv = [t[3] / det, -t[1] / det, -t[2] / det, t[0] / det];
      const a = new Uint8Array(p.w * p.h), rgb = c.stamp ? new Uint8Array(p.w * p.h * 3) : null, s4 = new Float32Array(4);
      for (let y = 0; y < p.h; y++) for (let x = 0; x < p.w; x++) {
        const X = x + 0.5 - t[4], Y = y + 0.5 - t[5]; bilinear(L, inv[0] * X + inv[2] * Y, inv[1] * X + inv[3] * Y, s4, 0, false);
        const al = Math.round(s4[3]), i = y * p.w + x; if (!al) continue;
        const r = Math.min(255, Math.round(s4[0] * 255 / s4[3]));
        if (rgb) { a[i] = al; rgb[i * 3] = r; rgb[i * 3 + 1] = Math.min(255, Math.round(s4[1] * 255 / s4[3])); rgb[i * 3 + 2] = Math.min(255, Math.round(s4[2] * 255 / s4[3])); }
        else a[i] = mul(255 - Math.round((r * 11 + Math.min(255, Math.round(s4[1] * 255 / s4[3])) * 16 + Math.min(255, Math.round(s4[2] * 255 / s4[3])) * 5) / 32), al);
      }
      return { w: p.w, h: p.h, a, rgb };
    }
    return brush;
  }
  // GIMP brushes (gbr) and image pipes (gih) into pictures { w, h, px RGBA, color }; a grey gbr becomes a grey picture whose darkness is its paint
  function readGbr(bytes, at = 0) {
    const dv = new DataView(bytes.buffer, bytes.byteOffset + at), hs = dv.getUint32(0), w = dv.getUint32(8), h = dv.getUint32(12), bpp = dv.getUint32(16);
    const px = new Uint8Array(w * h * 4), data = bytes.subarray(at + hs, at + hs + w * h * bpp); let color = false;
    for (let i = 0; i < w * h; i++) {
      if (bpp === 1) px.set([255 - data[i], 255 - data[i], 255 - data[i], 255], i * 4);
      else { px.set(data.subarray(i * 4, i * 4 + 4), i * 4); if (data[i * 4] !== data[i * 4 + 1] || data[i * 4 + 1] !== data[i * 4 + 2]) color = true; }
    }
    return { px, w, h, color, end: at + hs + w * h * bpp };
  }
  function readGih(bytes) {  // a name line, a parameters line (ncells, sel0), then each cell as a gbr; a file may hold fewer cells than it says
    let i = 0; const line = () => { const s = i; while (bytes[i] !== 10) i++; return new TextDecoder().decode(bytes.subarray(s, i++)); };
    line(); const params = line(), n = +params.split(' ')[0], cells = [];
    for (let k = 0; k < n && i + 28 < bytes.length; k++) { const c = readGbr(bytes, i); if (c.end > bytes.length) break; cells.push(c); i = c.end; }
    return { cells, selection: (/sel0:(\w+)/.exec(params) || [])[1] || 'random' };
  }

  // SECTION: TEXTURE -- the paper pattern (KisTextureMaskInfo::recalculateMask) and how it cuts each dab (KisTextureOption::apply, masking composite ops)
  function textureMask(tx, image, erasing) {
    let img = { w: image.w, h: image.h, px: Float32Array.from(image.px) };
    if (Math.abs(tx.scale) > 1e-12 && Math.abs(tx.scale - 1) > 1e-12) {
      for (let i = 0; i < img.w * img.h; i++) for (let k = 0; k < 3; k++) img.px[i * 4 + k] *= img.px[i * 4 + 3] / 255;
      const r = mapRect([tx.scale, 0, 0, tx.scale, 0, 0], img.w, img.h), w = Math.max(2, Math.round(r.w)), h = Math.max(2, Math.round(r.h)), k = Math.min(w / img.w, h / img.h);
      img = scaleImage(img, Math.round(img.w * k), Math.round(img.h * k));
      for (let i = 0; i < img.w * img.h; i++) for (let c = 0; c < 3; c++) img.px[i * 4 + c] = img.px[i * 4 + 3] ? img.px[i * 4 + c] * 255 / img.px[i * 4 + 3] : 0;
    }
    const m = new Uint8Array(img.w * img.h), invert = tx.invert !== erasing;  // AutoInvertOnErase inverts once more for the eraser
    for (let i = 0; i < img.w * img.h; i++) {
      const R = Math.round(img.px[i * 4]), G = Math.round(img.px[i * 4 + 1]), B = Math.round(img.px[i * 4 + 2]), a = Math.round(img.px[i * 4 + 3]) / 255;
      let v = Math.trunc((R * 11 + G * 16 + B * 5) / 32) / 255 * a + (1 - a);
      v = Math.min(1, Math.max(0, ((v - tx.brightness) - 0.5) * tx.contrast + 0.5));
      if (invert) v = 1 - v;
      const np = tx.neutralPoint;
      v = (np === 1 || (np !== 0 && v <= np)) ? v / (2 * np) : 0.5 + (v - np) / (2 - 2 * np);
      if (tx.cutoffPolicy && (v < tx.cutoffLeft / 255 || v > tx.cutoffRight / 255)) v = tx.cutoffPolicy === 1 ? 0 : 1;
      m[i] = u8(v);
    }
    return { w: img.w, h: img.h, m };
  }
  function textureOp(mode, soft, strength) {  // KisMaskingBrushCompositeOp with strength: the pattern (src) on the dab's alpha (dst)
    const st = u8(strength), inv = 255 - st;
    switch (mode) {
      case 0: return soft ? (s, d) => mul(unionShape(s, inv), d) : (s, d) => mul3(s, d, st);  // multiply
      case 1: return soft ? (s, d) => Math.max(0, d - mul(s, st)) : (s, d) => Math.max(0, d - (s + inv));  // subtract
      case 2: return soft ? (s, d) => Math.min(unionShape(s, inv), d) : (s, d) => Math.min(s, mul(d, st));  // darken
      default: return (s, d) => d;  // the other texturing modes: no preset of these families uses them
    }
  }
  function unionShape(a, b) { return a + b - mul(a, b); }
  function applyTexture(dab, left, top, tex, s, info, stroke) {
    const tx = s.texture, op = textureOp(tx.mode, tx.soft, checked(tx.strength, info));
    const offX = tx.randomX ? (stroke.texOff[0] ??= Math.floor(Math.random() * tex.w)) : tx.offsetX, offY = tx.randomY ? (stroke.texOff[1] ??= Math.floor(Math.random() * tex.h)) : tx.offsetY;
    const x0 = left % tex.w - offX, y0 = top % tex.h - offY;
    for (let y = 0; y < dab.h; y++) { const row = wrap(y0 + y, 0, tex.h) * tex.w;
      for (let x = 0; x < dab.w; x++) { const i = y * dab.w + x; if (dab.a[i]) dab.a[i] = op(tex.m[row + wrap(x0 + x, 0, tex.w)], dab.a[i]); } }
  }

  // SECTION: COMPOSITE -- Krita's composite ops on 8-bit RGBA with straight alpha (KoCompositeOpOver, Erase, AlphaDarken creamy)
  function over(D, i, c, srcA, opacity) {  // KoCompositeOpAlphaBase<Over>
    const sa = opacity === 255 ? srcA : mul(srcA, opacity); if (!sa) return;
    const da = D[i + 3]; let blend;
    if (da === 255) blend = sa;
    else if (da === 0) { D[i + 3] = sa; blend = 255; }
    else { const na = da + mul(255 - da, sa); D[i + 3] = na; blend = div(sa, na); }
    if (blend === 255) { D[i] = c[0]; D[i + 1] = c[1]; D[i + 2] = c[2]; } else for (let k = 0; k < 3; k++) D[i + k] = lerp8(D[i + k], c[k], blend);
  }
  function erase(D, i, srcA, opacity) { D[i + 3] = mul(D[i + 3], 255 - mul(srcA, opacity)); }
  function layOn(D, i, c, a, opacity, op) { if (op === 'erase') erase(D, i, a, opacity); else over(D, i, c, a, opacity); }
  function alphaDarken(D, i, c, msk, p) {  // KoCompositeOpAlphaDarken with the creamy parameters; p: opacity, flow, average opacity (8-bit) and flow == 1
    const sa = mul(msk, p.opacity), da = D[i + 3];
    if (da) for (let k = 0; k < 3; k++) D[i + k] = lerp8(D[i + k], c[k], sa); else { D[i] = c[0]; D[i + 1] = c[1]; D[i + 2] = c[2]; }
    let full;
    if (p.average > p.opacity) full = p.average > da ? lerp8(sa, p.average, div(da, p.average)) : da;
    else full = p.opacity > da ? lerp8(da, p.opacity, msk) : da;
    D[i + 3] = p.flowOne ? full : lerp8(da, full, p.flow);
  }
  const blendAverage = (opacity, avg) => avg < opacity ? opacity : 0.1 * opacity + 0.9 * avg;  // KisPainter::blendAverageOpacity

  // SECTION: DABS -- KisDabCache: where a dab goes (hot spot, sub-pixel, mirror), reused while the precision allows, then the texture
  const PRECISION = [[Math.PI / 180, 0.05, 1, 0.01, 0.05], [Math.PI / 180, 0.01, 1, 0.01, 0.01], [Math.PI / 180, 0, 1, 0.01, 1e-6], [Math.PI / 180, 0, 0.5, 0.01, 1e-6], [1e-6, 0, 1e-6, 1e-6, 1e-6]];
  function dabCache(s, brush, assets, stroke, noSubPixel) {
    const tex = s.texture && assets[s.texture.pattern] ? (s.texture.mask ||= textureMask(s.texture, assets[s.texture.pattern].image, s.texture.autoInvertOnErase && s.compositeOp === 'erase')) : null;
    let last = null, seqNo = 0;
    const imprecise = s.scatter.on || s.rotation.on || s.airbrush;  // KisBrushOp: hasImprecisePositionOptions
    return function fetch(d, pos, info, softness) {  // d: { scale, ratio, rot }; returns { x, y, dab } or null
      const mir = mirrorOf(s, info), shape = { ...d, rot: mir.flipped ? TAU - d.rot : d.rot };
      brush.prepare(info, seqNo++);
      const [hx, hy] = brush.hotSpot(shape);
      let x = Math.floor(pos[0] - hx), y = Math.floor(pos[1] - hy), sx = noSubPixel ? 0 : pos[0] - hx - x, sy = noSubPixel ? 0 : pos[1] - hy - y;
      let [w, h] = brush.maskSize(shape, sx, sy);
      if (mir.h) { sx = wrap(-(pos[0] + hx), 0, 1); w = brush.maskSize(shape, sx, sy)[0]; x = Math.round(pos[0] + sx + hx) - w; }
      if (mir.v) { sy = wrap(-(pos[1] + hy), 0, 1); h = brush.maskSize(shape, sx, sy)[1]; y = Math.round(pos[1] + sy + hy) - h; }
      const params = { angle: shape.rot, w, h, sx, sy, softness, ratio: shape.ratio, index: brush.cell, mh: mir.h, mv: mir.v };
      const level = (s.precision.auto ? (Math.min(w, h) < 30 || !imprecise ? 5 : 3) : s.precision.level) - 1, pr = PRECISION[Math.max(0, Math.min(4, level))];
      const same = last && brush.supportsCaching && Math.abs(params.angle - last.p.angle) <= pr[0] && Math.abs(w - last.p.w) <= Math.trunc(pr[1] * w) && Math.abs(h - last.p.h) <= Math.trunc(pr[1] * h)
        && Math.abs(sx - last.p.sx) <= pr[2] && Math.abs(sy - last.p.sy) <= pr[2] && Math.abs(softness - last.p.softness) <= pr[3] && Math.abs(params.ratio - last.p.ratio) <= pr[4]
        && params.index === last.p.index && params.mh === last.p.mh && params.mv === last.p.mv;
      if (!same) {
        const dab = brush.dab(shape, sx, sy, softness);
        if (mir.h || mir.v) flip(dab, mir.h, mir.v);
        last = { p: params, dab };
      }
      const dab = tex ? { ...last.dab, a: Uint8Array.from(last.dab.a) } : last.dab;
      if (tex) applyTexture(dab, x, y, tex, s, info, stroke);
      return { x, y, dab };
    };
  }
  function flip(dab, h, v) {
    const a = Uint8Array.from(dab.a), rgb = dab.rgb && Uint8Array.from(dab.rgb);
    for (let y = 0; y < dab.h; y++) for (let x = 0; x < dab.w; x++) {
      const i = y * dab.w + x, j = (v ? dab.h - 1 - y : y) * dab.w + (h ? dab.w - 1 - x : x); dab.a[i] = a[j];
      if (rgb) for (let k = 0; k < 3; k++) dab.rgb[i * 3 + k] = rgb[j * 3 + k];
    }
  }

  // SECTION: PAINT OPS -- what one dab does: the brush op (KisBrushOp), the spray op (KisSprayPaintOp, SprayBrush), the colour smudge op (KisColorSmudgeOp, legacy mask strategy)
  function spacingOf(s, brush, scale, rot, info) {  // KisPaintOpPluginUtils::effectiveSpacing; the dab's ratio and turn do not count, the spacing's turn does
    const extra = s.spacing.on ? sizeLike(s.spacing, info) : 1, [w, h] = brush.characteristic(scale, 1, 0), t = s.tip;
    const auto = v => t.autoSpacingCoeff * (v < 1 ? v : Math.sqrt(v));
    let x, y;
    if (s.isotropic) { const m = Math.max(w, h); x = y = (t.useAutoSpacing ? auto(m) : m * t.spacing) * extra; rot = 0; }
    else { x = (t.useAutoSpacing ? auto(w) : w * t.spacing) * extra; y = (t.useAutoSpacing ? auto(h) : h * t.spacing) * extra; }
    return { enabled: !(s.airbrush && s.ignoreSpacing), x, y, rot };
  }
  const timingOf = (s, info) => s.airbrush ? (r => r <= 0 ? LONG_TIME : 1000 / s.airbrushRate / r)(checked(s.rate, info)) : LONG_TIME;  // effectiveTiming
  function brushOp(s, target, assets, stroke) {  // paints into target: { data, W, H, mode: 'wash' (alpha darken) or the composite op, color, dirty() }
    const brush = brushOf(s, assets), fetch = dabCache(s, brush, assets, stroke, false);
    let average = 0;
    return {
      spacing(info) { return spacingOf(s, brush, checked(s.size, info), rotationOf(s.rotation, info), info); },
      paintAt(info) {
        const scale = checked(s.size, info);
        if (scale * brush.scale * brush.width < 0.01 || scale * brush.scale * brush.height < 0.01) return { enabled: true, x: 0, y: 0, rot: 0 };  // checkSizeTooSmall
        const d = { scale, ratio: checked(s.ratio, info), rot: rotationOf(s.rotation, info) };
        let pos = info.pos;
        if (s.scatter.on && (s.scatterX || s.scatterY)) {  // KisScatterOption::apply, jitter by the dab's larger side
          const [mw, mh] = brush.maskSize(d, 0, 0), dia = Math.max(mw, mh), v = sizeLike(s.scatter, info), j = (2 * Math.random() - 1) * dia * v;
          if (s.scatterX && s.scatterY) pos = [pos[0] + j, pos[1] + (2 * Math.random() - 1) * dia * v];
          else { const c = Math.cos(info.drawingAngle), sn = Math.sin(info.drawingAngle); pos = s.scatterX ? [pos[0] + c * j, pos[1] + sn * j] : [pos[0] - sn * j, pos[1] + c * j]; }
        }
        const opacity = s.wash && target.indirect ? sizeLike(s.opacity, info, false) : sizeLike(s.opacity, info), flow = sizeLike(s.flow, info);
        const softness = s.softness.on ? sizeLike(s.softness, info) : 1;
        const { x, y, dab } = fetch(d, pos, info, softness);
        average = blendAverage(opacity, average);
        const D = target.data, W = target.W, H = target.H, p = { opacity: u8(opacity), flow: u8(flow), flowOne: flow === 1, average: u8(Math.abs(opacity - average) <= 1e-5 * Math.max(opacity, average) ? opacity : average) };
        for (let j = Math.max(0, -y); j < dab.h && y + j < H; j++) for (let i = Math.max(0, -x); i < dab.w && x + i < W; i++) {
          const k = j * dab.w + i, a = dab.a[k], c = dab.rgb ? [dab.rgb[k * 3], dab.rgb[k * 3 + 1], dab.rgb[k * 3 + 2]] : target.color, o = ((y + j) * W + x + i) * 4;
          if (target.mode === 'wash') { if (a || target.data[o + 3]) alphaDarken(D, o, c, a, p); } else if (a) layOn(D, o, c, a, p.opacity, target.mode);
        }
        target.dirty(x, y, x + dab.w - 1, y + dab.h - 1);
        return spacingOf(s, brush, scale, d.rot, info);
      },
    };
  }
  function sprayDistributions(sp) {  // KisSprayRandomDistributions: a uniform one, or a function sampled into a cumulative table
    const table = (n, a, b, fn) => {  // KisSprayFunctionBasedDistribution::initialize
      if (n < 3) return [{ x: a, c: 0, k: 0 }, { x: b, c: 1, k: 1 }];
      const iv = (b - a) / (n - 1); let eff = n;
      for (let i = 0; i < n; i++) { if (fn(a + iv * i) > 0) { if (i > 0) { a += iv * (i - 1); eff -= i - 1; } break; } if (i === n - 1) return null; }
      for (let i = 0; i < n; i++) { if (fn(b - iv * i) > 0) { if (i > 0) { b -= iv * (i - 1); eff -= i - 1; } break; } }
      const S = [{ x: a, c: 0, k: 0 }]; let lastX = a, lastY = fn(a), lastSum = 0, sum = 0, ref = 0, check = false, skipped = 0;
      for (let i = 1; i < eff; i++) {
        const x = a + iv * i, y = fn(x); sum += (x - lastX) * (y + lastY) / 2;
        if (y === 0) { if (lastY === 0) { lastX = x; lastY = y; lastSum = sum; skipped++; continue; } check = false; }
        else if (lastY === 0) { if (skipped > 0) S.push({ x: lastX, c: lastSum, k: 0 }); check = false; }
        if (i > 1 && check && Math.abs(Math.atan2(sum - S[S.length - 2].c, x - S[S.length - 2].x) - ref) <= Math.PI / 1000) { S.at(-1).x = x; S.at(-1).c = sum; continue; }
        S.push({ x, c: sum, k: 0 }); ref = Math.atan2(sum - lastSum, x - lastX); check = true; skipped = 0; lastX = x; lastY = y; lastSum = sum;
      }
      for (let i = 1; i < S.length - 1; i++) { S[i].c /= sum; S[i].k = 1 / (S[i].c - S[i - 1].c); }
      S.at(-1).c = 1; S.at(-1).k = 1 / (1 - S[S.length - 2].c);
      return S;
    };
    const gen = S => () => { const r = Math.random(); let i = S.findIndex(p => p.c > r); if (i < 1) i = S.length - 1; const t = (r - S[i - 1].c) * S[i].k; return S[i - 1].x + t * (S[i].x - S[i - 1].x); };
    const curveFn = (str, rep, polar) => { const v = curveValue(curvePoints(str)); return x => { const sx = x * rep; return (polar ? 2 * x : 1) * v(sx - Math.floor(sx)); }; };
    const curveN = str => ((curvePoints(str).length % 4) + 1) * 1000;
    const angular = sp.angular ? gen(table(curveN(sp.angular.curve) * sp.angular.repeat, 0, 1, curveFn(sp.angular.curve, sp.angular.repeat, false))) : Math.random;
    let radial;
    if (sp.radial === 'uniform') radial = sp.centerBiased ? Math.random : () => Math.sqrt(Math.random());
    else if (sp.radial === 'gaussian') { const sd = sp.stdDev, c1 = 1 / (sd * Math.sqrt(TAU)), c2 = 2 * sd * sd; radial = gen(table(1000, 0, sd * 5, sp.centerBiased ? x => c1 * Math.exp(-x * x / c2) : x => 2 * x * c1 * Math.exp(-x * x / c2))); }
    else if (sp.radial === 'clusterBased') {
      const cl = sp.clustering;
      if (cl === 0) radial = gen(table(1000, 0, 1, x => 2 * x));
      else { const sg = 1 / Math.abs(cl), c1 = 2 * sg * sg; radial = gen(cl < 0 ? table(1000, 1 - Math.min(1, sg * 4), 1, x => 2 * x * Math.exp(-((1 - x) ** 2) / c1)) : table(1000, 0, Math.min(1, sg * 4), x => 2 * x * Math.exp(-x * x / c1))); }
    } else radial = gen(table(curveN(sp.radialCurve) * sp.radialRepeat, 0, 1, curveFn(sp.radialCurve, sp.radialRepeat, true)));
    return { angular, radial };
  }
  function sprayOp(s, target, assets, stroke) {
    const sp = s.spray, brush = brushOf(s, assets), dist = sprayDistributions(sp);
    let painterOpacity = 255, seqNo = 0;  // SprayBrush's own painter keeps the last random opacity
    return {
      spacing() { return { enabled: !(s.airbrush && s.ignoreSpacing), x: s.sprayStep, y: s.sprayStep, rot: 0 }; },
      paintAt(info) {  // SprayBrush::paint: particles on a dab layer that goes on the paper at the opacity option
        const rotation = rotationOf(s.rotation, info), opacity = u8(sizeLike(s.opacity, info)), scale = checked(s.size, info), radius = sp.diameter / 2 * scale;
        let [x, y] = info.pos;
        if (sp.jitter) { x += (2 * radius * Math.random() - radius) * sp.jitterAmount; y += (2 * radius * Math.random() - radius) * sp.jitterAmount; }
        const n = sp.useDensity ? Math.trunc(sp.coverage * Math.PI * radius * radius) : Math.trunc(sp.particleCount);
        const mr = -rotation + sp.rotation * Math.PI / 180, cr = Math.cos(mr), sr = Math.sin(mr), layer = new Map();
        let ink = target.color, inkA = 255, hsv = null, shouldColor = true;
        for (let k = 0; k < n; k++) {
          const ang = dist.angular() * TAU, len = dist.radial(); let rz = 0, ps = 1;
          if (sp.dyn.enabled) {
            if (sp.dyn.fixedRotation) rz = sp.dyn.fixedAngle * Math.PI / 180;
            if (sp.dyn.randomRotation) rz = rz + (TAU * Math.random() - rz) * sp.dyn.randomRotationWeight;
            if (sp.dyn.followCursor) rz = rz + (ang - rz) * sp.dyn.followCursorWeight;
            if (sp.dyn.followDrawingAngle) rz = rz + (info.drawingAngle - rz) * sp.dyn.followDrawingAngleWeight;
            if (sp.dyn.randomSize) ps = Math.random();
          }
          const nx0 = radius * Math.cos(ang) * len, ny0 = radius * Math.sin(ang) * len * sp.aspect;
          const nx = (cr * nx0 - sr * ny0) * sp.scale, ny = (sr * nx0 + cr * ny0) * sp.scale;
          if (shouldColor) {
            if (sp.col.useRandomHSV) { hsv = [sp.col.hue / 180 * Math.random(), sp.col.saturation / 100 * Math.random(), sp.col.value / 100 * Math.random()]; ink = hslShift(ink, ...hsv); }
            if (sp.col.useRandomOpacity) painterOpacity = inkA = u8(Math.random());
            if (!sp.col.colorPerParticle) shouldColor = false;
          }
          const d = { scale: ps, ratio: 1, rot: -rz }, [hx, hy] = brush.hotSpot(d), px0 = nx + x - hx, py0 = ny + y - hy, ix = Math.floor(px0), iy = Math.floor(py0);
          brush.prepare(info, seqNo++);
          const dab = brush.dab(d, px0 - ix, py0 - iy, 1);
          for (let j = 0; j < dab.h; j++) for (let i = 0; i < dab.w; i++) {
            const q = j * dab.w + i, m = dab.a[q]; if (!m) continue;
            const key = (iy + j + 16384) * 65536 + ix + i + 16384; let px = layer.get(key); if (!px) layer.set(key, px = new Uint8Array(4));
            const stampC = dab.rgb && [dab.rgb[q * 3], dab.rgb[q * 3 + 1], dab.rgb[q * 3 + 2]];
            over(px, 0, stampC ? (hsv ? hslShift(stampC, ...hsv) : stampC) : ink, stampC ? m : mul(m, inkA), painterOpacity);
          }
          if (sp.col.colorPerParticle) { ink = target.color; inkA = 255; }
        }
        const D = target.data, W = target.W, H = target.H; let x0 = Infinity, y0 = Infinity, x1 = -1, y1 = -1;
        for (const [key, px] of layer) {
          const ky = Math.floor(key / 65536), qx = key - ky * 65536 - 16384, py = ky - 16384; if (qx < 0 || py < 0 || qx >= W || py >= H || !px[3]) continue;
          layOn(D, (py * W + qx) * 4, px, px[3], opacity, target.mode);
          x0 = Math.min(x0, qx); y0 = Math.min(y0, py); x1 = Math.max(x1, qx); y1 = Math.max(y1, py);
        }
        if (x1 >= 0) target.dirty(x0, y0, x1, y1);
        return this.spacing();
      },
    };
  }
  function smudgeOp(s, target, assets, stroke) {  // KisColorSmudgeOp with KisColorSmudgeStrategyMaskLegacy, worked in a precise (float) copy of the layer
    const sm = s.smudge, brush = brushOf(s, assets), fetch = dabCache(s, brush, assets, stroke, !sm.dulling), W = target.W, H = target.H, D = target.data;
    const P = stroke.precise ||= Float32Array.from(D, v => v / 255);  // KisOverlayPaintDeviceWrapper: the layer in a precise colour space for the stroke
    const paint = target.color.map(v => v / 255);
    let lastCenter = null;
    const read = (X, Y, o) => { if (X < 0 || Y < 0 || X >= W || Y >= H) { o[0] = o[1] = o[2] = o[3] = 0; return o; } const i = (Y * W + X) * 4; o[0] = P[i]; o[1] = P[i + 1]; o[2] = P[i + 2]; o[3] = P[i + 3]; return o; };
    const overF = (dst, src, sa) => { if (sa <= 0) return; const da = dst[3]; if (da >= 1) { for (let k = 0; k < 3; k++) dst[k] += (src[k] - dst[k]) * sa; return; }
      if (da <= 0) { dst[0] = src[0]; dst[1] = src[1]; dst[2] = src[2]; dst[3] = sa; return; } const na = da + (1 - da) * sa, b = sa / na; dst[3] = na; for (let k = 0; k < 3; k++) dst[k] += (src[k] - dst[k]) * b; };
    function dullingColor(rect, radius) {  // KisColorSmudgeSampleUtils::sampleColor with AveragedSampleWrapper (Halton points, until the colour settles)
      const cx = rect.x + ((rect.w - 1) >> 1), cy = rect.y + ((rect.h - 1) >> 1);
      let r = { x: cx, y: cy, w: 1, h: 1 };
      if (radius > 0) { const gw = Math.trunc(rect.w * 0.5 * (radius - 1)), gh = Math.trunc(rect.h * 0.5 * (radius - 1)), b = { x: rect.x - gw, y: rect.y - gh, w: rect.w + 2 * gw, h: rect.h + 2 * gh };
        if (b.w > 0 && b.h > 0) { const x0 = Math.min(b.x, cx), y0 = Math.min(b.y, cy), x1 = Math.max(b.x + b.w, cx + 1), y1 = Math.max(b.y + b.h, cy + 1); r = { x: x0, y: y0, w: x1 - x0, h: y1 - y0 }; } }
      const n = r.w * r.h, hg = halton(2), vg = halton(3), sum = [0, 0, 0, 0], px = [0, 0, 0, 0]; let count = 0;
      const sample = () => { read(r.x + hg(r.w - 1), r.y + vg(r.h - 1), px); for (let k = 0; k < 3; k++) sum[k] += px[k] * px[3]; sum[3] += px[3]; count++; };
      const mixed = () => sum[3] > 0 ? [sum[0] / sum[3], sum[1] / sum[3], sum[2] / sum[3], sum[3] / count] : [0, 0, 0, 0];
      const minSamples = Math.min(n, Math.max(64, Math.round(0.02 * n)));
      for (let i = 0; i < minSamples; i++) sample();
      let col = mixed(), left = n - minSamples;
      while (left > 0) { const batch = Math.min(left, 16); for (let i = 0; i < batch; i++) sample(); const c2 = mixed(); const diff = Math.max(...c2.map((v, k) => Math.abs(v - col[k]))) * 255; col = c2; if (diff <= 2) break; left -= batch; }
      return col;
    }
    return {
      spacing(info) { return spacingOf(s, brush, checked(s.size, info), rotationOf(s.rotation, info), info); },
      paintAt(info) {
        const scale = checked(s.size, info), rot = rotationOf(s.rotation, info);
        if (scale * brush.scale * brush.width < 0.01 || scale * brush.scale * brush.height < 0.01) return { enabled: true, x: 0, y: 0, rot: 0 };
        const d = { scale, ratio: checked(s.ratio, info), rot };
        let pos = info.pos;
        if (s.scatter.on && (s.scatterX || s.scatterY)) {
          const [mw, mh] = brush.maskSize(d, 0, 0), dia = Math.max(mw, mh), v = sizeLike(s.scatter, info), j = (2 * Math.random() - 1) * dia * v;
          if (s.scatterX && s.scatterY) pos = [pos[0] + j, pos[1] + (2 * Math.random() - 1) * dia * v];
          else { const c = Math.cos(info.drawingAngle), sn = Math.sin(info.drawingAngle); pos = s.scatterX ? [pos[0] + c * j, pos[1] + sn * j] : [pos[0] - sn * j, pos[1] + c * j]; }
        }
        const radius = sm.radius.on ? sizeLike(sm.radius, info) : 0, spacing = spacingOf(s, brush, scale, rot, info);
        const { x, y, dab } = fetch(d, pos, info, 1), center = [x + dab.w / 2, y + dab.h / 2];
        if (!lastCenter) { lastCenter = center; return spacing; }
        const src = { x: x + Math.round(lastCenter[0] - center[0]), y: y + Math.round(lastCenter[1] - center[1]) }; lastCenter = center;
        const colorRate = sm.colorRate.on ? sizeLike(sm.colorRate, info) : 0, smudgeRate = sm.rate.on ? sizeLike(sm.rate, info) : 1, maxSmudge = sm.rate.value, opacity = sizeLike(s.opacity, info);
        const crOpacity = Math.min(1, Math.max(0, Math.max(1 - maxSmudge, 0.2) * colorRate * opacity)), finalOpacity = Math.min(1, Math.max(0, smudgeRate * opacity));
        const blend = new Float32Array(dab.w * dab.h * 4), px = [0, 0, 0, 0], paintPx = [...paint, 1];
        if (sm.dulling) {
          const dc = dullingColor({ ...src, w: dab.w, h: dab.h }, radius);
          if (crOpacity > 0) overF(dc, paintPx, crOpacity);  // fused: the paint colour mixed into the dulling colour first
          for (let i = 0; i < dab.w * dab.h; i++) blend.set(dc, i * 4);
        } else {
          for (let j = 0; j < dab.h; j++) for (let i = 0; i < dab.w; i++) blend.set(read(src.x + i, src.y + j, px), (j * dab.w + i) * 4);
          if (crOpacity > 0) for (let i = 0; i < dab.w * dab.h; i++) { const b = blend.subarray(i * 4, i * 4 + 4); overF(b, paintPx, crOpacity); }
        }
        for (let j = 0; j < dab.h; j++) for (let i = 0; i < dab.w; i++) {  // the final painter: copy (smear alpha) or over, through the mask, at smudge rate times opacity
          const X = x + i, Y = y + j; if (X < 0 || Y < 0 || X >= W || Y >= H) continue;
          const m = dab.a[j * dab.w + i] / 255 * finalOpacity; if (m <= 0) continue;
          const o = (Y * W + X) * 4, b = blend.subarray((j * dab.w + i) * 4, (j * dab.w + i) * 4 + 4);
          if (sm.smearAlpha) {  // KoCompositeOpCopy2
            const da = P[o + 3], na = da + (b[3] - da) * m;
            if (m >= 1) { P[o] = b[0]; P[o + 1] = b[1]; P[o + 2] = b[2]; P[o + 3] = b[3]; }
            else if (na > 0) { for (let k = 0; k < 3; k++) P[o + k] = Math.min(1, (P[o + k] * da + (b[k] * b[3] - P[o + k] * da) * m) / na); P[o + 3] = na; }
            else P[o + 3] = 0;
          } else { const dst = P.subarray(o, o + 4); overF(dst, b, b[3] * m); }
          for (let k = 0; k < 4; k++) D[o + k] = Math.round(P[o + k] * 255);
        }
        target.dirty(x, y, x + dab.w - 1, y + dab.h - 1);
        return spacing;
      },
    };
  }
  function halton(base) {  // KisAlgebra2D::HaltonSequenceGenerator
    let n = 0, d = 1;
    return max => { const x = d - n; if (x === 1) { n = 1; d *= base; } else { let y = Math.floor(d / base); while (x <= y) y = Math.floor(y / base); n = (base + 1) * y - x; } return Math.floor((n * max + Math.floor(d / 2)) / d); };
  }

  // SECTION: STROKE -- KisToolFreehandHelper (basic smoothing, airbrush timer), KisPaintOp::paintBezierCurve, KisPaintOpUtils::paintLine and paintFan, KisDistanceInformation
  function painterOf(s, target, assets, stroke) {  // one paint op with its own distance information (KisFreehandStrokeInfo)
    const op = s.spray ? sprayOp(s, target, assets, stroke) : s.smudge ? smudgeOp(s, target, assets, stroke) : brushOp(s, target, assets, stroke);
    const dist = { last: null, lastAngle: 0, spacing: { enabled: true, x: 0, y: 0, rot: 0 }, timing: LONG_TIME, acc: [0, 0], accTime: 0,
      sinceSpacing: 0, sinceTiming: 0, spacingInterval: s.spacingUpdates ? 50 : LONG_TIME, timingInterval: s.airbrush ? 50 : LONG_TIME, lastInfo: null };
    function nextPoint(p1, p2, t1, t2) {  // getNextPointPosition: the part of the piece where the next dab goes, by distance or by time, whichever first
      let fd = -1, ft = -1;
      if (dist.spacing.enabled) fd = dist.spacing.x === dist.spacing.y ? isotropic(p1, p2) : anisotropic(p1, p2);
      if (dist.timing < LONG_TIME) ft = timed(t1, t2);
      const t = fd < 0 ? ft : ft < 0 ? fd : Math.min(fd, ft);
      if (t < 0) { dist.sinceSpacing += t2 - t1; dist.sinceTiming += t2 - t1; } else { dist.sinceSpacing = dist.sinceTiming = 0; }
      return t;
    }
    const reset = () => { dist.acc = [0, 0]; dist.accTime = 0; };
    function isotropic(p1, p2) {
      const sp = Math.max(0.5, dist.spacing.x); if (samePoint(p1, p2)) return -1;
      const len = Math.hypot(p2[0] - p1[0], p2[1] - p1[1]), next = sp - dist.acc[0];
      if (next <= 0) { reset(); return 0; } if (next <= len) { reset(); return next / len; } dist.acc[0] += len; return -1;
    }
    function anisotropic(p1, p2) {
      if (samePoint(p1, p2)) return -1;
      const ar = 1 / Math.max(0.5, dist.spacing.x), br = 1 / Math.max(0.5, dist.spacing.y), [x, y] = dist.acc, gamma = (x * ar) ** 2 + (y * br) ** 2 - 1;
      if (gamma >= 0) { reset(); return 0; }
      let dx = p2[0] - p1[0], dy = p2[1] - p1[1]; const r = dist.spacing.rot;
      if (r > 2e-3) { const c = Math.cos(r), sn = Math.sin(r); [dx, dy] = [c * dx - sn * dy, sn * dx + c * dy]; }
      dx = Math.abs(dx); dy = Math.abs(dy);
      const alpha = (dx * ar) ** 2 + (dy * br) ** 2, beta = x * dx * ar * ar + y * dy * br * br, D4 = beta * beta - alpha * gamma;
      if (D4 >= 0) { const k = (-beta + Math.sqrt(D4)) / alpha; if (k >= 0 && k <= 1) { reset(); return k; } dist.acc = [x + dx, y + dy]; }
      return -1;
    }
    function timed(t1, t2) {
      if (!(t1 < t2)) return -1;
      const next = Math.min(LONG_TIME, Math.max(0.5, dist.timing)) - dist.accTime;
      if (next <= 0) { reset(); return 0; } if (next <= t2 - t1) { reset(); return next / (t2 - t1); } dist.accTime += t2 - t1; return -1;
    }
    function paintAt(pi, angleOverride) {  // KisPaintInformation::paintAt: the drawing angle from the last dab, the dab, then registerPaintedDab
      const info = { ...pi, drawingAngle: angleOverride ?? direction(dist.last, pi.pos, dist.lastAngle) };
      const sp = op.paintAt(info);
      dist.spacing = sp; dist.timing = timingOf(s, info);
      dist.lastInfo = info; dist.lastAngle = info.drawingAngle; dist.last = info.pos;
    }
    const mix = (t, a, b) => ({ ...b, pos: [(1 - t) * a.pos[0] + t * b.pos[0], (1 - t) * a.pos[1] + t * b.pos[1]], time: (1 - t) * a.time + t * b.time });
    function paintLine(pi1, pi2) {
      let pi = pi1, t;
      while ((t = nextPoint(pi.pos, pi2.pos, pi.time, pi2.time)) >= 0) {
        pi = mix(t, pi, pi2);
        if (s.fan && dist.lastInfo) {  // paintFan: dabs turning from the last dab's angle to this one's, a step apart
          const a0 = dist.lastAngle, a1 = direction(dist.last, pi.pos, dist.lastAngle), full = angularDistance(a0, a1), from = dist.lastInfo;
          let la = a0, i = 0;
          while (angularDistance(la, a1) > s.fan) { la = incrementInDirection(la, s.fan, a1); paintAt(mix(s.fan * i++ / full, from, pi), la); }
        }
        paintAt(pi);
      }
      if (dist.sinceSpacing >= dist.spacingInterval) { dist.spacing = op.spacing({ ...pi2, drawingAngle: direction(dist.last, pi2.pos, dist.lastAngle) }); dist.sinceSpacing = 0; }
      if (dist.sinceTiming >= dist.timingInterval) { dist.timing = timingOf(s, pi2); dist.sinceTiming = 0; }
    }
    function bezier(pi1, c1, c2, pi2) {  // KisPaintOp::paintBezierCurve: midpoint subdivision until both controls are within half a pixel of the line
      const [x1, y1] = pi1.pos, [x2, y2] = pi2.pos, len = Math.hypot(x2 - x1, y2 - y1);
      const dl = p => Math.abs((y2 - y1) * p[0] - (x2 - x1) * p[1] + x2 * y1 - y2 * x1) / len;
      const d1 = dl(c1), d2 = dl(c2);
      if ((d1 < 0.5 && d2 < 0.5) || Number.isNaN(d1) || Number.isNaN(d2)) return paintLine(pi1, pi2);
      const m = (a, b) => [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2], l2 = m(pi1.pos, c1), h = m(c1, c2), l3 = m(l2, h), r3 = m(c2, pi2.pos), r2 = m(h, r3), l4 = m(l3, r2);
      const mid = { ...mix(0.5, pi1, pi2), pos: l4 };
      bezier(pi1, l2, l3, mid); bezier(mid, r2, r3, pi2);
    }
    return { paintAt, paintLine, bezier, startAngle: a => { dist.lastAngle = a; } , begin: pi => { dist.last = pi.pos; } };
  }
  function segmentControls(pi1, pi2, t1, t2) {  // KisToolFreehandHelper::paintBezierSegment: the two control points of a curve piece
    if (!(t1[0] || t1[1]) || !(t2[0] || t2[1])) return null;
    const p1 = pi1.pos, p2 = pi2.pos, d1 = [p1[0] + t1[0], p1[1] + t1[1]], d2 = [p2[0] - t2[0], p2[1] - t2[1]];
    const cross = (a, b, c, e) => {  // QLineF::intersects: the point and whether it lies on both segments
      const ax = b[0] - a[0], ay = b[1] - a[1], bx = e[0] - c[0], by = e[1] - c[1], den = ay * bx - ax * by;
      if (!den || !Number.isFinite(den)) return null;
      const cx = a[0] - c[0], cy = a[1] - c[1], na = (by * cx - bx * cy) / den, nb = (ax * cy - ay * cx) / den;
      return { p: [a[0] + ax * na, a[1] + ay * na], bounded: na >= 0 && na <= 1 && nb >= 0 && nb <= 1 };
    };
    let k1, k2;
    const x34 = cross(d1, d2, p1, p2);
    if (x34 && x34.bounded) {
      const L = Math.hypot(p2[0] - p1[0], p2[1] - p1[1]) / 2, at = (p, q) => { const l = Math.hypot(q[0] - p[0], q[1] - p[1]); return l ? [p[0] + (q[0] - p[0]) * L / l, p[1] + (q[1] - p[1]) * L / l] : p; };
      k1 = at(p1, d1); k2 = at(p2, d2);
    } else {
      const x12 = cross(p1, d1, p2, d2); let p = x12 && x12.p;
      if (!p || Math.abs(p[0]) + Math.abs(p[1]) > 1e6) p = [(p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2];
      k1 = k2 = p;
    }
    let coeff = 0.8, v1 = Math.hypot(...t1), v2 = Math.hypot(...t2);
    if (v1 === 0 || v2 === 0) v1 = v2 = 1e-6;
    let sim = Math.max(Math.min(v1 / v2, v2 / v1), 0.5); coeff *= 1 - Math.max(0, sim - 0.8);
    let c1, c2;
    const toward = (p, q, c) => [p[0] * (1 - c) + c * q[0], p[1] * (1 - c) + c * q[1]];
    if (v1 > v2) { c1 = toward(p1, k1, coeff); coeff *= sim; c2 = toward(p2, k2, coeff); } else { c2 = toward(p2, k2, coeff); coeff *= sim; c1 = toward(p1, k1, coeff); }
    return [c1, c2];
  }
  // A stroke: layer is the paper's ImageData; s the brush; color [r, g, b]; assets the decoded tips and textures.
  // down(x, y, t, from) starts it (from: where the mouse hovered before, for the first dab's angle), move(x, y, t) for each finger move,
  // tick(t) each frame (the airbrush and the 100 ms pause that ends a curve), shown(view) draws what changed, end() finishes it.
  function stroke(layer, s, color, assets) {
    const W = layer.width, H = layer.height, L = layer.data, dirty = [W, H, -1, -1];
    const markDirty = (x0, y0, x1, y1) => { dirty[0] = Math.min(dirty[0], x0); dirty[1] = Math.min(dirty[1], y0); dirty[2] = Math.max(dirty[2], x1); dirty[3] = Math.max(dirty[3], y1); };
    const shared = { random: {}, texOff: [], precise: null };
    const wash = s.wash && !s.spray;  // a wash stroke paints on a stroke layer first (indirect painting); spray and smudge paint on the layer
    const strokeLayer = wash ? new Uint8ClampedArray(W * H * 4) : null, maskLayer = wash && s.masking ? new Uint8ClampedArray(W * H * 4) : null;
    const painters = [painterOf(s, { data: wash ? strokeLayer : L, W, H, color, mode: wash ? 'wash' : s.compositeOp, indirect: wash, dirty: markDirty }, assets, shared)];
    if (maskLayer) {  // the masking brush: its own preset, white dabs in wash mode on the mask, sized from the main brush (createMaskingSettings)
      const ms = s.masking.settings, mshared = { random: {}, texOff: [], precise: null };
      if (s.masking.useMasterSize) {
        const main = s.tip.type === 'auto_brush' ? s.tip.gen.diameter : (assets[s.tip.file].gih ? assets[s.tip.file].gih.cells[0].w : (assets[s.tip.file].gbr || assets[s.tip.file].image).w) * s.tip.scale;
        const size = Math.min(1000, s.masking.coeff * main);
        if (ms.tip.type === 'auto_brush') ms.tip.gen.diameter = size; else ms.tip.scale = size / (assets[ms.tip.file].gih ? assets[ms.tip.file].gih.cells[0].w : (assets[ms.tip.file].gbr || assets[ms.tip.file].image).w);
      }
      painters.push(painterOf({ ...ms, wash: true }, { data: maskLayer, W, H, color: [255, 255, 255], mode: 'wash', indirect: false, dirty: markDirty }, assets, mshared));
    }
    const each = fn => painters.forEach(fn);
    // KisToolFreehandHelper, basic smoothing
    let t0 = null, previous = null, older = null, prevTangent = null, haveTangent = false, paintedOnce = false, timeoutAt = Infinity, lastTime = 0;
    const tangent = (a, b) => { const dt = Math.max(1, b.time - a.time); return [(b.pos[0] - a.pos[0]) / dt, (b.pos[1] - a.pos[1]) / dt]; };
    const isNull = v => !v || (v[0] === 0 && v[1] === 0);
    function segment(a, b, ta, tb) { const c = segmentControls(a, b, ta, tb); if (!c) return; paintedOnce = true; each(p => p.bezier(a, c[0], c[1], b)); }
    function paint(info) {  // KisToolFreehandHelper::paint, SIMPLE_SMOOTHING
      if (!haveTangent) { haveTangent = true; prevTangent = tangent(previous, info); }
      else {
        const nt = tangent(older, info);
        if (isNull(nt) || isNull(prevTangent)) { paintedOnce = true; each(p => p.paintLine(previous, info)); }
        else segment(older, previous, prevTangent, nt);
        prevTangent = nt;
      }
      older = previous;
      if (!s.airbrush) timeoutAt = info.time + 100;  // the stroke timeout that finishes the curve after a pause
      previous = info;
    }
    function finish() {  // KisToolFreehandHelper::finishStroke
      if (!haveTangent) return;
      haveTangent = false; segment(older, previous, prevTangent, tangent(older, previous));
    }
    return {
      down(x, y, t, from) {
        t0 = t; lastTime = 0; previous = { pos: [x, y], time: 0, stroke: shared };
        const start = direction(from || [x, y], [x, y], 0);
        each(p => { p.begin(previous); p.startAngle(start); });
      },
      move(x, y, t) {
        if (previous && x === previous.pos[0] && y === previous.pos[1] && t - t0 === previous.time) return;
        lastTime = Math.max(lastTime, t - t0); paint({ pos: [x, y], time: lastTime, stroke: shared });
      },
      tick(t) {
        const now = t - t0;
        if (now >= timeoutAt) { timeoutAt = Infinity; finish(); }
        if (s.airbrush && previous && now > lastTime) { lastTime = now; paint({ pos: previous.pos, time: now, stroke: shared }); }  // doAirbrushing
      },
      shown(view) {  // what the paper shows in the box changed since last time: the layer with the stroke layer on it; returns the box
        const [x0, y0, x1, y1] = [Math.max(0, dirty[0]), Math.max(0, dirty[1]), Math.min(W - 1, dirty[2]), Math.min(H - 1, dirty[3])];
        dirty[0] = W; dirty[1] = H; dirty[2] = dirty[3] = -1;
        if (x1 < x0 || y1 < y0) return null;
        const V = view.data;
        for (let y = y0; y <= y1; y++) for (let x = x0; x <= x1; x++) { const i = (y * W + x) * 4; for (let c = 0; c < 4; c++) V[i + c] = L[i + c]; if (wash) mergePixel(V, i); }
        return [x0, y0, x1 - x0 + 1, y1 - y0 + 1];
      },
      end() {
        if (!paintedOnce) each(p => p.paintAt(previous));  // a tap: one dab where the finger was
        else finish();
        if (wash) for (let i = 0; i < W * H * 4; i += 4) mergePixel(L, i);
      },
    };
    function mergePixel(D, i) {  // the stroke layer, its alpha cut or grown by the mask (KisMaskingBrushRenderer), onto the layer at the preset's opacity and composite op
      let a = strokeLayer[i + 3];
      if (maskLayer) { const m = maskLayer[i + 3]; a = s.masking.op === 'subtract' ? Math.max(0, a - m) : s.masking.op === 'linear_dodge' ? (a ? Math.min(255, a + m) : 0) : mul(m, a); }
      if (a) layOn(D, i, [strokeLayer[i], strokeLayer[i + 1], strokeLayer[i + 2]], a, u8(s.opacity.value), s.compositeOp);
    }
  }
  return { fromPreset, stroke, readGbr, readGih };
})();

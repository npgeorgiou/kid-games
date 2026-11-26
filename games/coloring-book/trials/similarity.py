# The image similarity test (owner 26 Nov: nothing is sent unless it passes): each of his acrylic pictures beside the trial painting a scene like it
# (look_all_refs.py), compared by texture statistics of the paint, the standard way to compare textures that are not the same picture
# (Portilla & Simoncelli: statistics of the image at several scales and directions). His picture is first scaled so its strokes are as wide as the trial's.
# What is measured, on the paint only (everything that differs from the paper):
#   rough   ragged edges: the edge's length against the length of the same edge smoothed
#   blobs   small blobs and bumps on the edges, per 100 px of edge
#   gaps    dry-brush gaps inside the strokes, a share of the stroke area
#   streak  fine streaks: how much the lightness varies over a few px
#   flow    how much those streaks run one way (along the bristles)
#   tone    larger patches of lighter and darker paint inside the strokes (picked-up and mixed paint)
#   shine   share of bright ridges (how strongly the paint is lit as a relief)
# A hint is marked * when the trial is not within TOL of his picture. Also passes(): his 26 Nov rule on passing over wet paint.
# The gate is the deep texture test (Gatys et al. 2015: Gram matrices of a pretrained image network's features, here SqueezeNet 1.1, forresti/SqueezeNet, BSD):
# patches of the trial's paint against patches of his picture, measured against how far one half of his picture is from its other half.
# The trial passes a picture when it is no further from it than SELF times that. The measures above are printed as hints for what differs.
# Needs OpenCV 4 (version 5 cannot read the network): pip install --target <temp>/cv4 "opencv-python-headless<5" "numpy<2.3"; the network is fetched to the temp folder once.
# Usage: similarity.py; prints one line per picture and PASS or FAIL; the pictures compared, side by side: similarity.png in the system temp folder.
import sys
import numpy as np
from PIL import Image
from scipy import ndimage as nd
from skimage import color, measure, morphology
import look_all_refs as L
import pathlib, tempfile, urllib.request
TMP = pathlib.Path(tempfile.gettempdir()); sys.path.insert(0, str(TMP / 'cv4')); import cv2
NET = 'https://raw.githubusercontent.com/forresti/SqueezeNet/master/SqueezeNet_v1.1/'
for f in ('deploy.prototxt', 'squeezenet_v1.1.caffemodel'):
    if not (TMP / f).exists(): urllib.request.urlretrieve(NET + f, TMP / f)
net = cv2.dnn.readNetFromCaffe(str(TMP / 'deploy.prototxt'), str(TMP / 'squeezenet_v1.1.caffemodel'))
LAYERS = ['relu_conv1', 'fire2/concat', 'fire3/concat', 'fire5/concat', 'fire7/concat']; PATCH = 64; SELF = 1.2
def patches(im, rng, cols=None, n=24):  # n squares of PATCH px that are mostly paint; cols: only from these columns
    a = np.asarray(im.convert('RGB')); m, _ = paint_mask(a / 255.0); H, W = m.shape; x0, x1 = cols or (0, W); out = []
    for _ in range(6000):
        if len(out) == n: break
        y, x = rng.integers(0, H - PATCH), rng.integers(x0, max(x0 + 1, min(W, x1) - PATCH))
        if m[y:y + PATCH, x:x + PATCH].mean() >= 0.75: out.append(a[y:y + PATCH, x:x + PATCH])
    return out
def gram(ps):  # the texture: each layer's feature correlations, averaged over the patches
    net.setInput(cv2.dnn.blobFromImages([p[..., ::-1] for p in ps], 1.0, (PATCH, PATCH), (104, 117, 123))); g = []
    for o in net.forward(LAYERS):
        f = o.reshape(o.shape[0], o.shape[1], -1); g.append(np.einsum('nci,ndi->ncd', f, f).mean(0) / f.shape[2])
    return g
def apart(g1, g2): return float(np.mean([np.linalg.norm(a - b) / np.linalg.norm(b) for a, b in zip(g1, g2)]))

TOL = 0.25  # within a quarter of his picture's value
FLOOR = {'gaps': 0.005, 'shine': 0.01}  # or closer than this: a difference of a fraction of a percent of the paint cannot be seen

def paint_mask(rgb):
    lab = color.rgb2lab(rgb); edge = np.concatenate([lab[:6].reshape(-1, 3), lab[-6:].reshape(-1, 3), lab[:, :6].reshape(-1, 3), lab[:, -6:].reshape(-1, 3)])
    bg = np.median(edge, 0); d = np.sqrt(((lab - bg) ** 2).sum(-1))
    return morphology.remove_small_objects(d > 10, max_size=3), lab

# his pictures scaled so their strokes are as wide as the trial's strokes in the same scene (stroke widths measured once on each picture, in px:
# acrylic-1 blobs 170 against the trial's 80; acrylic-2 bands 80 against 50 seen; acrylic-4 bands 64 against 80 seen; blue-strokes 56 against 60)
REF_SCALE = {'acrylic-1': 80 / 170, 'acrylic-2': 50 / 80, 'acrylic-4': 80 / 64, 'acrylic-blue-strokes': 60 / 56}
TRIAL_PART = {'acrylic-2': (300, 250, 700, 480)}  # the same part of the trial's scene as PAINT_ONLY of his picture: the lowest band's edge, paper below it
def scaled(im, f): return im if f == 1 else im.resize((int(im.width * f), int(im.height * f)), Image.LANCZOS)

def stats(im):
    rgb = np.asarray(im) / 255.0; m, lab = paint_mask(rgb); Lc = lab[..., 0]
    sm = morphology.closing(morphology.opening(m, morphology.disk(4)), morphology.disk(4))
    per = lambda x: measure.perimeter(x)
    e_s = max(1.0, per(sm))
    rough = per(m) / e_s
    bumps = m & ~morphology.opening(m, morphology.disk(3)); lb = measure.label(bumps); n_b = sum(1 for r in measure.regionprops(lb) if r.area >= 2)
    lm = measure.label(m); n_s = sum(1 for r in measure.regionprops(lm) if 2 <= r.area < 120)
    blobs = 100 * (n_b + n_s) / e_s
    hull = morphology.closing(m, morphology.disk(6)); gaps = (hull & ~m).sum() / max(1, hull.sum())
    inner = morphology.erosion(m, morphology.disk(5))
    hp = Lc - nd.gaussian_filter(Lc, 6); streak = hp[inner].std()
    gx, gy = nd.sobel(Lc, 1), nd.sobel(Lc, 0); jxx, jyy, jxy = (nd.gaussian_filter(v, 6) for v in (gx * gx, gy * gy, gx * gy))
    flow = np.sqrt((jxx - jyy) ** 2 + 4 * jxy ** 2)[inner].sum() / max(1e-6, (jxx + jyy)[inner].sum())  # weighted by how strong the texture is: flat paint has no direction
    lo = nd.gaussian_filter(Lc, 3); mu = nd.gaussian_filter(lo, 12); tone = np.sqrt(np.maximum(0, nd.gaussian_filter(lo * lo, 12) - mu * mu))[inner].mean()
    shine = ((Lc - nd.gaussian_filter(Lc, 3)) > 6)[inner].mean()
    return dict(rough=rough, blobs=blobs, gaps=gaps, streak=streak, flow=flow, tone=tone, shine=shine)

def miss(k, a, b): return 0.0 if abs(a - b) <= FLOOR.get(k, 0) else max(0.0, abs(a - b) / max(1e-6, abs(b)) - TOL)  # how far past the tolerance
def texture(name, trial):  # how far the trial's paint is from his, and how far his picture's halves are from each other
    R = lambda k: np.random.default_rng(k); r = scaled(L.ref(name), REF_SCALE[name]); W = r.width  # the same patches of his picture every time
    return apart(gram(patches(trial, R(0))), gram(patches(r, R(1)))), apart(gram(patches(r, R(2), (0, W // 2 + PATCH // 2))), gram(patches(r, R(3), (W // 2 - PATCH // 2, W))))
def judge(pics):  # per picture: (passes, how far past the gate, the line printed); the trial beside his pictures, at the scale compared: similarity.png
    out, rows = {}, []
    for name, im in pics.items():
        t, r0 = im.crop(TRIAL_PART[name]) if name in TRIAL_PART else im, scaled(L.ref(name), REF_SCALE[name]); a, b = stats(t), stats(r0); d, d0 = texture(name, t)
        h = max(t.height, r0.height); row = Image.new('RGB', (t.width + r0.width + 10, h), 'white'); row.paste(t, (0, 0)); row.paste(r0, (t.width + 10, 0)); rows.append(row)
        past = max(0.0, d / (SELF * d0) - 1); hints = '  '.join('%s %.3g/%.3g%s' % (k, a[k], b[k], '*' if miss(k, a[k], b[k]) > 0 else '') for k in a)
        out[name] = (past == 0, past + 0.05 * sum(min(3.0, miss(k, a[k], b[k])) for k in a), '%s %s  texture %.3f (his halves %.3f)  hints: %s' % ('PASS' if past == 0 else 'FAIL', name, d, d0, hints))
    sheet = Image.new('RGB', (max(r.width for r in rows), sum(r.height + 10 for r in rows)), 'white'); y = 0
    for r in rows: sheet.paste(r, (0, y)); y += r.height + 10
    sheet.save(L.OUT / 'similarity.png')
    return out
def score(pics): return sum(v[1] for v in judge(pics).values())  # for tune.py: 0 when every picture passes (the hints only steer)
def compare(pics):
    res = judge(pics)
    for v in res.values(): print(v[2])
    return all(v[0] for v in res.values())

def passes():  # owner 26 Nov: paint mixes with the colour under it the more it is passed over, and is never a faint smudge
    # a wet red band, then a full yellow brush passed over it 1, 2 and 4 times (back and forth): the mix gets more even (its streaks fade) and stays rich (no faint smudge)
    from playwright.sync_api import sync_playwright
    def hand(xs, y): return [(x, y, k * 8.0) for k, x in enumerate(xs)]
    res = []
    with sync_playwright() as pw:
        b = pw.chromium.launch(); q = b.new_page(viewport={'width': 1360, 'height': 800}); q.goto('file://' + str(L.H / 'acrylic-trial.html')); q.wait_for_function('()=>window.__ready')
        if L.TUNE: q.evaluate("(t)=>Object.assign(__trial.P, t)", L.TUNE)
        go, back = list(range(100, 901, 4)), list(range(900, 99, -4))
        for k, n in enumerate([1, 2, 4]):
            y = 150 + k * 200; q.evaluate("([p])=>__trial.stroke(4,40,'flat',p)", [hand(go, y)])
            xs = []
            for j in range(n): xs += go if j % 2 == 0 else back
            q.evaluate("([p])=>__trial.stroke(5,40,'flat',p)", [hand(xs, y)])
        q.wait_for_timeout(150); f = L.OUT / 'passes.png'; q.screenshot(path=str(f), clip={'x': 12, 'y': 12, 'width': 1000, 'height': 760}); b.close()
    lab = color.rgb2lab(np.asarray(Image.open(f).convert('RGB')) / 255.0)
    for k in range(3):
        band = lab[150 + k * 200 - 25:150 + k * 200 + 25, 300:700]; hue = np.degrees(np.arctan2(band[..., 2], band[..., 1])); ch = np.hypot(band[..., 1], band[..., 2])
        res.append((hue.std(), hue.mean(), ch.mean()))
    red, yel = color.rgb2lab(np.array([[[200, 30, 30], [245, 190, 20]]]) / 255.0)[0]; full = (np.hypot(red[1], red[2]) + np.hypot(yel[1], yel[2])) / 2
    hr, hy = (np.degrees(np.arctan2(c[2], c[1])) for c in (red, yel))
    lo, hi = hr + 0.15 * (hy - hr), hy - 0.15 * (hy - hr)
    pe = [max(0.0, res[j + 1][0] - 0.9 * res[j][0]) / max(0.1, res[j][0]) for j in range(2)]  # the streaks fade pass by pass
    pm = [max(0.0, lo - m, m - hi) / (hy - hr) for _, m, _ in res]  # a mix: neither colour covers the other
    pr = [max(0.0, 0.7 * full - c) / full for _, _, c in res]  # as colourful as paint, not a faint smudge
    even, mixed, rich = not any(pe), not any(pm), not any(pr)
    print(('PASS' if even and mixed and rich else 'FAIL') + ' passes  streaks %s  hue %s (red %.0f, yellow %.0f)  colourful %s (paint %.0f)' % ('/'.join('%.1f' % r[0] for r in res), '/'.join('%.0f' % r[1] for r in res), hr, hy, '/'.join('%.0f' % r[2] for r in res), full))
    return even and mixed and rich, 3 * (sum(pe) + sum(pm) + sum(pr))

if __name__ == '__main__':
    good = passes()[0] & compare(L.paint()); print('PASS all' if good else 'FAIL'); sys.exit(0 if good else 1)

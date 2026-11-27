# Cut the owner's animal sheets (6 animals x 5 faces) into stickers: each drawing's outline closed and filled, a white margin round it, a black edge round that.
import sys, numpy as np
from PIL import Image
from scipy import ndimage
U = '/mnt/user-data/uploads/'; OUT = sys.argv[1] if len(sys.argv) > 1 else '/home/claude/kid-games/games/oi-apoikoi/art/avatars/'
ANIMALS = ['hamster', 'bunny', 'chick', 'cat', 'dog', 'frog']; FACES = ['neutral', 'happy', 'excited', 'surprised', 'sad']
MAIN, STARS = U + 'b09c492f-image.webp', U + '398ade37-image.webp'  # owner 27 Nov: all faces from the sheet without lines, the excited ones (star eyes) from the other
COLS = [215, 422, 658, 897, 1156, 1376]; ROWS = [62, 195, 310, 422, 535, 645, 768]  # the sheets' cells: names left of 215, titles above 62, column lines at 422, 658, 897, 1156
SIZE, MARGIN, EDGE = 180, 9, 6  # a sticker's longest side, its white margin and black edge, in pixels
def drawings(a):  # every drawing on a sheet: its dark outlines and strong colours, the column lines and the titles left out; each piece goes with the cell its middle lies in
    mx, mn = a.max(2), a.min(2); ink = (a.sum(2) / 3 < 150) | ((mx - mn) / np.maximum(mx, 1) > 0.3); ink[:ROWS[0]] = False; ink[:, :COLS[0]] = False
    for x in COLS[1:-1]: ink[:, x - 4:x + 5] = False
    lab, n = ndimage.label(ink); sizes = ndimage.sum(ink, lab, range(1, n + 1)); mid = ndimage.center_of_mass(ink, lab, range(1, n + 1))
    cell = lambda y, x: (next(r for r in range(6) if y < ROWS[r + 1]), next(c for c in range(5) if x < COLS[c + 1]))
    pieces = {}
    for k in range(n):
        if sizes[k] > 20: pieces.setdefault(cell(*mid[k]), []).append(k + 1)  # paper speckle dropped; sparkles and tears kept
    return {rc: ndimage.binary_fill_holes(ndimage.binary_closing(np.isin(lab, ks), iterations=3)) for rc, ks in pieces.items()}  # each drawing closed and filled on its own, so neighbours never join
def disk(r): y, x = np.ogrid[-r:r + 1, -r:r + 1]; return x * x + y * y <= r * r
def sticker(a, body):
    ys, xs = np.where(body); y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    k = SIZE / max(y1 - y0, x1 - x0); w, h = round((x1 - x0) * k), round((y1 - y0) * k); pad = MARGIN + EDGE + 3
    pic = np.asarray(Image.fromarray(a[y0:y1, x0:x1].astype('uint8')).resize((w, h), Image.LANCZOS))
    m = np.asarray(Image.fromarray((body[y0:y1, x0:x1] * 255).astype('uint8')).resize((w, h), Image.LANCZOS)) > 127
    inner = np.zeros((h + 2 * pad, w + 2 * pad), bool); inner[pad:pad + h, pad:pad + w] = m
    white = ndimage.binary_fill_holes(ndimage.binary_dilation(inner, disk(MARGIN))); black = ndimage.binary_dilation(white, disk(EDGE))
    out = np.zeros(inner.shape + (4,), 'uint8'); out[black] = (20, 16, 14, 255); out[white] = (255, 255, 255, 255)
    out[pad:pad + h, pad:pad + w][m, :3] = pic[m]
    return Image.fromarray(out)
for path in (MAIN, STARS):
    a = np.asarray(Image.open(path).convert('RGB')).astype(int); cells = drawings(a)
    for r, animal in enumerate(ANIMALS):
        for c, face in enumerate(FACES):
            if (path == STARS) != (face == 'excited'): continue
            sticker(a, cells[(r, c)]).quantize(256, method=Image.Quantize.FASTOCTREE).save(OUT + animal + '-' + face + '.png', optimize=True)  # 256 colours: a third of the size
print('stickers', len(ANIMALS) * len(FACES))

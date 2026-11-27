# Cut his pictures out of their cream backgrounds, their soft beige shadows too: background = border-connected colours near the border's, grown into
# shadow-like pixels (beige hue, little saturation) connected to it; also enclosed background regions bigger than `hole` (handle gaps). Soft edge.
import numpy as np, colorsys
from PIL import Image, ImageFilter, ImageEnhance
from scipy import ndimage
def bgmask(im, tol, hole, satmin=0.06):
    a = np.array(im.convert('RGB')).astype(float)
    bg = np.median(np.concatenate([a[0], a[-1], a[:, 0], a[:, -1]]), axis=0)
    near = np.abs(a - bg).sum(-1) < tol * 3
    lab, n = ndimage.label(near); sizes = ndimage.sum(near, lab, range(n + 1))
    edge = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]])))
    seed = np.isin(lab, [k for k in range(1, n + 1) if k in edge or sizes[k] > hole])
    r, g, b = [a[..., k] / 255 for k in range(3)]; mx = np.maximum(np.maximum(r, g), b); mn = np.minimum(np.minimum(r, g), b); sat = (mx - mn) / np.maximum(mx, 1e-6)
    hue = np.where(mx == r, ((g - b) / np.maximum(mx - mn, 1e-6)) % 6, np.where(mx == g, (b - r) / np.maximum(mx - mn, 1e-6) + 2, (r - g) / np.maximum(mx - mn, 1e-6) + 4)) * 60
    shadowy = (hue > 25) & (hue < 60) & (sat > satmin) & (sat < 0.42) & (mx > 0.5)
    return ndimage.binary_propagation(seed, mask=seed | shadowy)
def plainmask(im, tol, hole):  # without growing into shadows (a white picture on white)
    a = np.array(im.convert('RGB')).astype(float); bg = np.median(np.concatenate([a[0], a[-1], a[:, 0], a[:, -1]]), axis=0); near = np.abs(a - bg).sum(-1) < tol * 3
    lab, n = ndimage.label(near); sizes = ndimage.sum(near, lab, range(n + 1)); edge = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]])))
    return np.isin(lab, [k for k in range(1, n + 1) if k in edge or sizes[k] > hole])
def cutout(im, tol, hole, shadows=True, satmin=0.06):
    bg = bgmask(im, tol, hole, satmin) if shadows else plainmask(im, tol, hole)
    alpha = Image.fromarray(((~bg) * 255).astype('uint8')).filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(0.7))
    out = im.convert('RGBA'); out.putalpha(alpha); return out
U = '/mnt/user-data/uploads/'; OUT = '/home/claude/kid-games/games/oi-apoikoi/art/'
jar = cutout(Image.open(U + 'f21e677b-image.jpg'), 16, 2000); jar = jar.crop(jar.getbbox()); jar.thumbnail((300, 460)); jar.save(OUT + 'things/jar.png'); print('jar', jar.size)
sheet = Image.open(U + 'a77502cf-image.png'); m = ~bgmask(sheet, 14, 300); full = cutout(sheet, 14, 300); stonefull = cutout(sheet, 5, 300, False)  # the stone's light face is a pale beige grey: only stronger beige counts as shadow there
lab, n = ndimage.label(m); objs = ndimage.find_objects(lab); sizes = ndimage.sum(m, lab, range(1, n + 1))
boxes = sorted([(s[0].start, s[1].start, s[0].stop, s[1].stop) for s, z in zip(objs, sizes) if z > 800])
GRID = [['grain', 'timber', None], ['stone', None, 'grapes'], ['coin', None, 'meat'], [None, None, None]]  # the sheet's 3 x 4 pictures
H, W = m.shape
for (y0, x0, y1, x1) in boxes:
    name = GRID[min(3, int((y0 + y1) / 2 / (H / 4)))][min(2, int((x0 + x1) / 2 / (W / 3)))]
    if not name: continue
    if name == 'stone': im = stonefull.crop((x0 - 15, y0 - 25, x1 + 15, y1 + 5))  # its own cut: the light face is near the background's colour
    else: im = full.crop((x0, y0, x1, y1)); sub = lab[y0:y1, x0:x1]; big = np.bincount(sub[sub > 0]).argmax(); a = np.array(im); a[..., 3] = np.where(sub == big, a[..., 3], 0); im = Image.fromarray(a)
    if name == 'stone': rgb = ImageEnhance.Brightness(ImageEnhance.Color(im.convert('RGB')).enhance(0.15)).enhance(0.78); rgb.putalpha(im.getchannel('A')); im = rgb  # owner 25 Nov: greyer, darker, against the white statues
    im = im.crop(im.getbbox()); im.thumbnail((128, 128)); im.save(OUT + ('things/' if name == 'coin' else 'materials/') + name + '.png'); print(name, im.size)
b = Image.open(U + '91c2ade3-image.png'); b = cutout(b, 8, 400, False); b = b.crop(b.getbbox()); b.thumbnail((128, 128)); b.save(OUT + 'materials/bust.png')
def solid(im, tol):  # a picture with no holes (a stone slab): background = only what touches the border, warm and near its colour; every enclosed part kept (owner 27 Nov: light cracks are stone, not holes); outline smoothed
    a = np.array(im.convert('RGB')).astype(float); bg = np.median(np.concatenate([a[0], a[-1], a[:, 0], a[:, -1]]), axis=0)
    near = (np.sqrt(((a - bg) ** 2).sum(-1)) < tol) & (a[..., 0] - a[..., 1] >= 1.5)  # the beige background is warm; the slab's light rim is cooler
    lab, n = ndimage.label(near); back = np.isin(lab, list(set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}))
    keep = ~back; lab, n = ndimage.label(keep); keep = lab == 1 + np.argmax(ndimage.sum(keep, lab, range(1, n + 1)))
    keep = ndimage.binary_fill_holes(ndimage.gaussian_filter(ndimage.binary_fill_holes(keep).astype(float), 3) > 0.5)
    out = im.convert('RGBA'); out.putalpha(Image.fromarray((ndimage.gaussian_filter(keep.astype(float), 0.8) * 255).clip(0, 255).astype('uint8'))); return out.crop(out.getbbox())
slab = solid(Image.open(U + '76cb44b6-image.jpg'), 16); slab.resize((900, round(900 * slab.size[1] / slab.size[0])), Image.LANCZOS).save(OUT + 'things/stone-slab-2.png')
def trimmed(im):  # a picture he gave already transparent: stray faint pixels away from it dropped (the apple's file has a faint veil), then trimmed to what is left
    a = np.array(im.convert('RGBA')); solid = a[..., 3] > 128; lab, n = ndimage.label(solid); body = lab == 1 + np.argmax(ndimage.sum(solid, lab, range(1, n + 1)))
    a[..., 3] = np.where(ndimage.binary_dilation(ndimage.binary_fill_holes(body), iterations=4), a[..., 3], 0); out = Image.fromarray(a); return out.crop(out.getbbox())
ruby = trimmed(Image.open(U + 'b14da686-image.png')); ruby.save(OUT + 'things/ruby.png')  # owner 27 Nov: his ruby, given transparent (no shadow of its own)
apple = trimmed(Image.open(U + '7efb9d06-image.png')); apple.thumbnail((300, 300)); apple.save(OUT + 'things/apple.png')  # owner 27 Nov: his bitten apple, given transparent: a jar or a slot face with nothing

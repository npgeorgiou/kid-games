"""Writes src/art/map-ground.png: what a tap on the world map shows, per map pixel (at a quarter of the map size).
Colours: blue = water, green = green land, sand = sand/desert/steppe, brown = mountains.
Water and green come from the map picture's colours; mountains are drawn here by hand as shapes around the
mountains painted on the map (peaks and hatched ranges, owner 17 Nov: "you name many mountains as sand");
the rest of the land is sand. Map coordinates are map.jpg pixels (2176 x 1408). Edit the shapes and rerun."""
import os
from PIL import Image, ImageDraw, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__)); ART = os.path.join(HERE, '..', 'src', 'art')
# mountains: polygons (list of points) and ellipses (centre x, centre y, radius x, radius y)
POLYS = [
    [(0, 0), (290, 0), (290, 50), (110, 110), (0, 140)],                                   # Balkans, north-west hatched hills
    [(130, 220), (230, 230), (245, 420), (170, 405), (140, 300)],               # Pindus
    [(880, 1060), (960, 1050), (1000, 1300), (930, 1310)],                      # hills east of the Nile
    [(1250, 190), (1440, 100), (1460, 0), (2176, 0), (2176, 140), (1980, 180), (1960, 330), (1700, 330),
     (1500, 420), (1300, 470), (1088, 470), (1088, 350), (1250, 330)],          # Caucasus, Armenian highlands, Taurus
    [(1640, 300), (2176, 320), (2176, 880), (2090, 880), (1960, 800), (1860, 640), (1760, 500)],  # Zagros
]
ELLIPSES = [
    (190, 120, 80, 45), (330, 115, 60, 45),   # Balkan peaks
    (860, 230, 55, 30),                       # north-west Anatolia peaks
    (210, 865, 80, 35),                       # Libya peaks
    (1030, 1060, 55, 35),                     # Sinai peaks
    (1315, 1035, 85, 35), (1248, 1120, 80, 35), (1575, 1195, 65, 25), (1608, 1255, 80, 32), (1385, 1322, 80, 28), (1710, 1335, 55, 22),  # Arabia peaks
    (1250, 830, 40, 20),                      # rock outcrop, Syrian desert
]
def main():
    img = Image.open(os.path.join(ART, 'map.jpg')).convert('RGB'); W, H = img.size; w, h = W // 4, H // 4
    col = img.resize((w, h), Image.BOX).filter(ImageFilter.BoxBlur(2))
    land = Image.open(os.path.join(ART, 'map-land.png')).resize((w, h))
    mount = Image.new('L', (w, h), 0); d = ImageDraw.Draw(mount)
    for p in POLYS: d.polygon([(x / 4, y / 4) for x, y in p], fill=255)
    for cx, cy, rx, ry in ELLIPSES: d.ellipse([(cx - rx) / 4, (cy - ry) / 4, (cx + rx) / 4, (cy + ry) / 4], fill=255)
    out = Image.new('RGB', (w, h))
    for y in range(h):
        for x in range(w):
            r, g, b = col.getpixel((x, y))
            if land.getpixel((x, y))[3] < 128 or (b > r + 15 and b >= g): k = (40, 90, 220)
            elif g >= r - 6 and g > b + 25: k = (40, 170, 40)
            elif mount.getpixel((x, y)): k = (120, 80, 60)
            else: k = (250, 220, 120)
            out.putpixel((x, y), k)
    out.save(os.path.join(ART, 'map-ground.png'))
    Image.blend(out.resize((W // 2, H // 2), Image.NEAREST), img.resize((W // 2, H // 2)), 0.45).save('/tmp/ground-check.png')
main()

# How many hues a palette shows (owner 24 Nov 10:32: computed, never hand-set). Model, in plain words:
# 1. Walk the stripes in their order. A stripe starts a new run when the colour family changes from the run's last coloured or grey stripe:
#    grey next to coloured, or two coloured stripes whose hues are far apart (HUE_JUMP degrees, OKLab hue). Very pale or very dark
#    stripes with little colour (the white or black middle of a palette) belong to whichever side they are on.
# 2. A run also ends where its lightness turns round (getting lighter, then darker), so a palette that goes dark-light-dark is two hues.
# 3. Runs = hues: 1 a progression, 2 two hues, 3 three, more is many.
import math
GREY, PALE, HUE_JUMP, TURN = 0.03, 0.06, 50, 0.1  # below GREY a mid-light stripe is grey; below PALE a very light or dark one takes its side; a lightness turn smaller than TURN is a wiggle

def oklch(h):
    r, g, b = [(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4) for c in (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))]
    l, m, s = [x ** (1 / 3) for x in (0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b, 0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b, 0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b)]
    L, a, B = 0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s, 1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s, 0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s
    return L, math.hypot(a, B), math.degrees(math.atan2(B, a)) % 360

def kind(c):  # 'pale' (takes its side), 'grey', or 'col'
    L, C, _ = c
    return 'pale' if (L > 0.85 or L < 0.25) and C < PALE else 'grey' if C < GREY else 'col'

def hues(hexes):
    c = [oklch(h) for h in hexes]; runs, way, peak, fam = 1, 0, c[0][0], None
    for q in c:
        k = kind(q)
        if k != 'pale' and fam is not None and (k != fam[0] or (k == 'col' and min(abs(q[2] - fam[1]), 360 - abs(q[2] - fam[1])) > HUE_JUMP)):
            runs, way, peak = runs + 1, 0, q[0]
        elif way != 0 and (q[0] - peak) * way <= -TURN: runs, way, peak = runs + 1, 0, q[0]
        else:
            if way == 0 and abs(q[0] - peak) >= TURN: way = 1 if q[0] > peak else -1
            if way == 0 or (q[0] - peak) * way > 0: peak = q[0]
        if k != 'pale': fam = (k, q[2])
    return runs

GROUPS = ['progression', 'two', 'three', 'many']
def group(hexes): return GROUPS[min(hues(hexes), 4) - 1]

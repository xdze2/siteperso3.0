# 2D figure: rays as normals of a "sensor" curve. circle -> one point, line -> parallel,
# ellipse -> no common point, the normals envelop a caustic (the evolute).
# python3 + Pillow. Output: ../images/persp_normals.png
import os, math
import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'images') + '/'
SS = 3
PW, PH = 230, 260   # one panel
W, H = 3 * PW, PH

im = Image.new('L', (W * SS, H * SS), 255)
d = ImageDraw.Draw(im)
RAY, CURVE = 120, 0


def line(p, q, c, w=1):
    d.line([(p[0] * SS, p[1] * SS), (q[0] * SS, q[1] * SS)], fill=c, width=w * SS)


def poly(pts, c, w=2):
    d.line([(x * SS, y * SS) for x, y in pts], fill=c, width=w * SS)


def panel(ox, curve, normal, ts, L):
    """curve(t) -> point, normal(t) -> unit normal pointing to the scene (down)"""
    for t in ts:
        p = np.array(curve(t)); n = np.array(normal(t))
        line(p + [ox, 0], p + n * L + [ox, 0], RAY)
    poly([tuple(np.array(curve(t)) + [ox, 0]) for t in np.linspace(ts[0], ts[-1], 200)], CURVE)


# a) circle: all normals through the centre
cx, cy, R = PW / 2, 150, 120
panel(0, lambda t: (cx + R * math.sin(t), cy - R * math.cos(t)),
      lambda t: (-math.sin(t), math.cos(t)), np.linspace(-0.9, 0.9, 15), 2 * R)
# b) line: parallel normals
panel(PW, lambda t: (t, 40), lambda t: (0, 1), np.linspace(25, PW - 25, 15), 200)
# c) ellipse: normals do not meet, they touch the evolute
a, b = 100, 55
ex, ey = PW / 2, 100
def ell(t): return (ex + a * math.sin(t), ey - b * math.cos(t))
def nrm(t):
    n = np.array([b * math.sin(t), -a * math.cos(t)])   # outward, flipped below
    n = -n / np.linalg.norm(n)
    return (n[0], n[1])
panel(2 * PW, ell, nrm, np.linspace(-1.3, 1.3, 27), 200)
# the evolute (caustic) itself, dashed-ish: centres of curvature
ev = []
for t in np.linspace(-1.3, 1.3, 200):
    s, c = math.sin(t), math.cos(t)
    x = (a * a - b * b) / a * s ** 3
    y = -(b * b - a * a) / b * c ** 3
    ev.append((2 * PW + ex + x, ey + y))
for i in range(0, len(ev) - 1, 4):
    poly(ev[i:i + 3], 40, 2)

im = im.reduce(SS)
im.save(OUT + 'persp_normals.png')
print('saved persp_normals.png', im.size)

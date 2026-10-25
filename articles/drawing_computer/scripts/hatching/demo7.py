from common import *
import os; HERE = os.path.dirname(os.path.abspath(__file__))
import pickle
SS = 2
rng = np.random.default_rng(5)
tone = np.where(oid > 0, np.clip(0.05 + 0.95 * dark ** 0.9, 0, 1), dark ** 1.7)
tone[oid == 3] = 0

# ---- LIC ----
Hs, Ws = H * SS, W * SS
fx = np.array(Image.fromarray(Fx).resize((Ws, Hs), Image.NEAREST))
fy = np.array(Image.fromarray(Fy).resize((Ws, Hs), Image.NEAREST))
Oid = np.array(Image.fromarray(oid).resize((Ws, Hs), Image.NEAREST))
Tn = np.array(Image.fromarray(tone.astype(np.float32)).resize((Ws, Hs), Image.BILINEAR))
noise = rng.random((Hs, Ws)).astype(np.float32)
acc = noise.copy(); cnt = np.ones((Hs, Ws), np.float32)
Y0, X0 = np.mgrid[0:Hs, 0:Ws].astype(np.float32)
for sgn in (1, -1):
    x = X0.copy(); y = Y0.copy()
    px, py = fx.copy() * sgn, fy.copy() * sgn
    alive = np.ones((Hs, Ws), bool)
    for k in range(22):
        xi = np.clip(x.astype(int), 0, Ws - 1); yi = np.clip(y.astype(int), 0, Hs - 1)
        ax, ay = fx[yi, xi], fy[yi, xi]
        flip = ax * px + ay * py < 0
        ax = np.where(flip, -ax, ax); ay = np.where(flip, -ay, ay)
        px, py = ax, ay
        x = x + ax; y = y + ay
        xi = np.clip(x.astype(int), 0, Ws - 1); yi = np.clip(y.astype(int), 0, Hs - 1)
        alive &= (Oid[yi, xi] == Oid)
        acc += np.where(alive, noise[yi, xi], 0); cnt += alive
lic = acc / cnt
# rank-normalise per object so ink fraction = tone
ink = np.zeros((Hs, Ws), bool)
for k in (0, 1, 2):
    m = Oid == k
    v = lic[m]
    r = np.argsort(np.argsort(v)) / max(1, len(v) - 1)
    t = Tn[m]
    ink[m] = r < t * 0.75
ink &= Tn > 0.05
img = Image.fromarray(np.where(ink, 0, 255).astype(np.uint8))
save(img.resize((W, H), Image.LANCZOS), 'hatch_lic.png')

# ---- wobbly, interrupted strokes from the streamline set ----
L1, L2 = pickle.load(open(os.path.join(HERE, 'lines.pkl'), 'rb'))
SS2 = 3
img = Image.new('L', (W * SS2, H * SS2), 255)
d = ImageDraw.Draw(img)
for pts in L1 + L2:
    n = len(pts)
    if n < 4: continue
    ph = rng.uniform(0, 6.28, 3)
    P = []
    for i, (x, y) in enumerate(pts):
        i1 = min(i + 1, n - 1); i0 = max(i - 1, 0)
        tx, ty = pts[i1][0] - pts[i0][0], pts[i1][1] - pts[i0][1]
        m = math.hypot(tx, ty) or 1
        nx, ny = -ty / m, tx / m
        w = 0.55 * math.sin(i / 7.0 + ph[0]) + 0.35 * math.sin(i / 3.1 + ph[1])
        P.append((x + nx * w, y + ny * w))
    # break into pieces with gaps, width swells
    i = 0
    while i < n - 1:
        seg = int(rng.integers(12, 45))
        piece = P[i:i + seg + 1]
        wid = rng.uniform(0.8, 1.5)
        for j in range(len(piece) - 1):
            tt = j / max(1, len(piece) - 2)
            ww = wid * (0.45 + 0.55 * math.sin(math.pi * tt) ** 0.5)
            d.line([(piece[j][0] * SS2, piece[j][1] * SS2), (piece[j + 1][0] * SS2, piece[j + 1][1] * SS2)],
                   fill=0, width=max(1, int(round(ww * SS2))))
        i += seg + int(rng.integers(0, 4))
save(downscale(img, SS2), 'hatch_wobble.png')

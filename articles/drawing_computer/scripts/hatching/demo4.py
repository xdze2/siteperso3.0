from common import *
import pickle
SS = 3
rng = np.random.default_rng(3)
tone = np.where(oid > 0, np.clip(0.05 + 0.95 * dark ** 0.9, 0, 1), dark ** 1.7)
tone[oid == 3] = 0

# ---- 4: Salisbury-like dashes, dart throwing, radius by tone ----
def rad(t): return 15.0 - 10.0 * np.clip(t, 0, 1)
pts = []
grid = {}
cell = 6
def near(x, y, r):
    c = int(r // cell) + 1
    for i in range(int(x // cell) - c, int(x // cell) + c + 1):
        for j in range(int(y // cell) - c, int(y // cell) + c + 1):
            for (px, py, pr) in grid.get((i, j), ()):
                rr = 0.5 * (r + pr)
                if (px - x) ** 2 + (py - y) ** 2 < rr * rr: return True
    return False
N = 60000
xs = rng.uniform(0, W, N); ys = rng.uniform(0, H, N)
for x, y in zip(xs, ys):
    xi, yi = int(x), int(y)
    t = tone[yi, xi]
    if t < 0.12: continue
    # keep probability follows tone (lighter = fewer)
    r = rad(t)
    if near(x, y, r): continue
    pts.append((x, y, oid[yi, xi]))
    grid.setdefault((int(x // cell), int(y // cell)), []).append((x, y, r))
print('dashes', len(pts))
img = Image.new('L', (W * SS, H * SS), 255)
d = ImageDraw.Draw(img)
for x, y, o in pts:
    xi, yi = int(x), int(y)
    fx, fy = Fx[yi, xi], Fy[yi, xi]
    a = math.atan2(fy, fx) + rng.normal(0, 0.08)
    L = 4.5
    dx, dy = math.cos(a) * L, math.sin(a) * L
    d.line([((x - dx) * SS, (y - dy) * SS), ((x + dx) * SS, (y + dy) * SS)], fill=0, width=int(1.2 * SS))
save(downscale(img, SS), 'hatch_dashes.png')

# ---- 5: width modulated screen following the form ----
def up_(a): return up(a, SS)
Oid = np.array(Image.fromarray(oid).resize((W * SS, H * SS), Image.NEAREST))
N3 = [up_(nrm[..., i]) for i in range(3)]
D3 = up_(dep)
Tn = up_(tone)
a = np.array([0.45, 1.0, 0.15]); a /= np.linalg.norm(a)
u = np.zeros_like(D3); p = np.ones_like(D3)
sph = Oid == 1
u[sph] = (N3[0] * a[0] + N3[1] * a[1] + N3[2] * a[2])[sph]; p[sph] = 0.075
tor = Oid == 2
u[tor] = N3[1][tor]; p[tor] = 0.11
gr = Oid == 0
yy = (np.mgrid[0:H * SS, 0:W * SS][0].astype(np.float32) / SS)
u[gr] = np.sqrt(np.maximum(yy - 105, 0.01))[gr]; p[gr] = 0.26
f = np.mod(u / p, 1.0) - 0.5
wfrac = np.clip(Tn * 1.0, 0, 0.92)
ink = (np.abs(f) < wfrac / 2) & (Oid != 3) & (Tn > 0.06)
img = Image.fromarray(np.where(ink, 0, 255).astype(np.uint8))
save(downscale(img, SS), 'hatch_engrave.png')

# ---- 6: single spiral, Mellan limit case ----
cx, cy = W / 2 + 10, H / 2 + 20
Y, X = np.mgrid[0:H * SS, 0:W * SS].astype(np.float32) / SS
r = np.hypot(X - cx, Y - cy); th = np.arctan2(Y - cy, X - cx)
pp = 4.6
s = r / pp - th / (2 * math.pi)
f = np.mod(s, 1.0) - 0.5
Tm = up_(np.where(oid == 3, 0, np.clip(dark ** 1.1, 0, 1)))
ink = np.abs(f) < np.clip(Tm * 0.95, 0, 0.95) / 2
img = Image.fromarray(np.where(ink, 0, 255).astype(np.uint8))
save(downscale(img, SS), 'hatch_spiral.png')

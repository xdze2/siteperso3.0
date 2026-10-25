import numpy as np, math, random
from PIL import Image, ImageDraw

import os; HERE = os.path.dirname(os.path.abspath(__file__))
SC = os.path.join(HERE, '..', 'scene') + '/'
OUT = os.path.join(HERE, '..', '..', 'images') + '/'
lum = np.load(SC + 'lum.npy'); nrm = np.load(SC + 'normal.npy')
dep = np.load(SC + 'depth.npy'); oid = np.load(SC + 'oid.npy')
H, W = lum.shape
# darkness 0..1 ; sky = no ink
dark = np.clip((0.97 - lum) / 0.72, 0, 1)
dark[oid == 3] = 0
# 3D-ish direction field on screen (unit vectors, image coords: y down)
def unit(a, b):
    m = np.hypot(a, b); m2 = np.where(m < 1e-6, 1, m)
    return a / m2, b / m2, m

def build_field():
    Fx = np.ones((H, W), np.float32); Fy = np.zeros((H, W), np.float32)
    M = np.ones((H, W), np.float32)
    nx, ny, nz = nrm[..., 0], nrm[..., 1], nrm[..., 2]
    # sphere: latitude lines around a tilted axis, t = a x n
    a = np.array([0.45, 1.0, 0.15]); a /= np.linalg.norm(a)
    tx = a[1] * nz - a[2] * ny
    ty = a[2] * nx - a[0] * nz
    fx, fy, m = unit(tx, -ty)
    s = oid == 1
    Fx[s], Fy[s], M[s] = fx[s], fy[s], m[s]
    # torus: concentric ellipses around the ring centre (approx. ring tangent)
    t = oid == 2
    ys, xs = np.where(t)
    cx, cy = (xs.min() + xs.max()) / 2, (ys.min() + ys.max()) / 2 + 2
    ratio = 0.5
    Y, X = np.mgrid[0:H, 0:W].astype(np.float32)
    fx, fy, m = unit(-(Y - cy) / ratio, (X - cx) * ratio)
    Fx[t], Fy[t], M[t] = fx[t], fy[t], 1
    # ground: horizontal
    return Fx, Fy, M
Fx, Fy, Mag = build_field()

def save(img, name):
    img.save(OUT + name)
    print('saved', name, img.size)

def downscale(img, ss):
    return img.resize((img.width // ss, img.height // ss), Image.LANCZOS)

def up(a, ss, order='bilinear'):
    im = Image.fromarray(a.astype(np.float32), mode='F')
    return np.array(im.resize((a.shape[1] * ss, a.shape[0] * ss),
                              Image.BILINEAR if order == 'bilinear' else Image.NEAREST))

# ---------- evenly spaced streamlines (Jobard & Lefer, variable separation) ----------
def streamlines(region, dsep_map, Fx, Fy, seed=0, dtest_k=0.65, minlen=8, cell=4, flip=False):
    rng = random.Random(seed)
    Hh, Ww = region.shape
    grid = {}
    lines = []
    def ok(x, y):
        xi, yi = int(x), int(y)
        return 0 <= xi < Ww and 0 <= yi < Hh and region[yi, xi] and np.isfinite(dsep_map[yi, xi])
    def near(x, y, r, lid=None, k=None, m=0):
        c = int(r // cell) + 1
        cx, cy = int(x // cell), int(y // cell)
        r2 = r * r
        for i in range(cx - c, cx + c + 1):
            for j in range(cy - c, cy + c + 1):
                for (px, py, l, idx) in grid.get((i, j), ()):
                    if lid is not None and l == lid and abs(idx - k) < m:
                        continue
                    if (px - x) ** 2 + (py - y) ** 2 < r2:
                        return True
        return False
    def field(x, y, prev):
        xi, yi = int(x), int(y)
        fx, fy = Fx[yi, xi], Fy[yi, xi]
        if fx * prev[0] + fy * prev[1] < 0:
            fx, fy = -fx, -fy
        return fx, fy
    def trace(x0, y0, d0, lid, sign):
        pts = []
        x, y = x0, y0
        prev = (d0[0] * sign, d0[1] * sign)
        k = 0
        for step in range(900):
            ds = dsep_map[int(y), int(x)]
            m = int(2.5 * ds) + 2
            if step > 0 and near(x, y, dtest_k * ds, lid, sign * step, m):
                break
            pts.append((x, y))
            k = sign * step
            grid.setdefault((int(x // cell), int(y // cell)), []).append((x, y, lid, k))
            f1 = field(x, y, prev)
            xm, ym = x + 0.5 * f1[0], y + 0.5 * f1[1]
            if not ok(xm, ym): break
            f2 = field(xm, ym, f1)
            xn, yn = x + f2[0], y + f2[1]
            if not ok(xn, yn): break
            prev = f2
            x, y = xn, yn
        return pts
    def new_line(x, y):
        fx, fy = Fx[int(y), int(x)], Fy[int(y), int(x)]
        lid = len(lines)
        fw = trace(x, y, (fx, fy), lid, 1)
        bw = trace(x, y, (fx, fy), lid, -1)
        pts = bw[::-1][:-1] + fw if len(bw) > 1 else fw
        if len(pts) < minlen:
            # remove from grid
            for (px, py) in pts:
                key = (int(px // cell), int(py // cell))
                grid[key] = [e for e in grid.get(key, []) if e[2] != lid]
            lines.append(None)
            return None
        lines.append(pts)
        return pts
    ys, xs = np.where(region & np.isfinite(dsep_map))
    if len(xs) == 0: return []
    cand = list(zip(xs.tolist(), ys.tolist()))
    rng.shuffle(cand)
    stack = []
    ci = 0
    while True:
        if not stack:
            found = False
            while ci < len(cand):
                x, y = cand[ci]; ci += 1
                x += 0.5; y += 0.5
                if not near(x, y, dsep_map[int(y), int(x)] * 0.98):
                    pts = new_line(x, y)
                    if pts:
                        stack.append(pts); found = True; break
            if not found: break
        pts = stack.pop()
        for i in range(0, len(pts), 3):
            x, y = pts[i]
            fx, fy = Fx[int(y), int(x)], Fy[int(y), int(x)]
            ds = dsep_map[int(y), int(x)]
            if not np.isfinite(ds): continue
            for sgn in (1, -1):
                sx, sy = x - sgn * fy * ds, y + sgn * fx * ds
                if ok(sx, sy) and not near(sx, sy, dsep_map[int(sy), int(sx)] * 0.98):
                    p2 = new_line(sx, sy)
                    if p2: stack.append(p2)
    return [l for l in lines if l]

def draw_lines(lines, size, ss, width=1.2, w=None):
    img = Image.new('L', (size[0] * ss, size[1] * ss), 255)
    d = ImageDraw.Draw(img)
    for pts in lines:
        P = [(x * ss, y * ss) for x, y in pts]
        d.line(P, fill=0, width=max(1, int(round(width * ss))), joint='curve')
    return downscale(img, ss)

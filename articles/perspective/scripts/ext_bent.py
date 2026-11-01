# falling rays (render.py 'fall'): outside view of the curved rays, and the morphed world
# where straight rays give the same picture.
# the field: dd/ds = -g (y - (y.d) d). A ray stays in its vertical plane and its angle
# drops linearly with horizontal distance: theta = theta0 - g rho. Hence, closed forms:
#   y(rho) = ln(cos theta / cos theta0) / g,   s(rho) = (F(theta0) - F(theta)) / g,  F = asinh(tan)
# morph: world point -> eye + s * (initial direction of the ray that reaches it).
# Output: ../images/ext_fall.png, persp_fall_morph.png, ext_fall_morph.png
import os, sys, math
import numpy as np
from PIL import Image
import render as R
import extview as X

G = 0.035
EYE = np.array([0, 1.6, -4.0])
YAW, PITCH, FOV = 0, 12, 80
W, H = 700, 380
EW, EH = 360, 250
UP = np.array([0, 1.0, 0])
CACHE = os.path.join(R.HERE, 'cache_fall.npz')


def fall(p, d):
    return np.tile(-G * UP, (len(d), 1))


def F(th):
    return np.arcsinh(np.tan(th))


# ---------------------------------------------------------------- morph, both ways
def morph(P):
    """world -> morphed. bisection on theta0 (the height reached is monotonic in it)"""
    rel = np.atleast_2d(P) - EYE
    rho = np.hypot(rel[:, 0], rel[:, 2])
    y = rel[:, 1]
    lo = np.maximum(-np.pi / 2, G * rho - np.pi / 2) + 1e-9
    hi = np.minimum(np.pi / 2, G * rho + np.pi / 2) - 1e-9
    for _ in range(60):
        th0 = (lo + hi) / 2
        f = np.log(np.cos(th0 - G * rho) / np.cos(th0)) / G - y
        lo = np.where(f < 0, th0, lo); hi = np.where(f < 0, hi, th0)
    th0 = (lo + hi) / 2
    s = (F(th0) - F(th0 - G * rho)) / G
    az = np.stack([rel[:, 0], np.zeros_like(rho), rel[:, 2]], 1) / np.maximum(rho, 1e-12)[:, None]
    return EYE + s[:, None] * (np.cos(th0)[:, None] * az + np.sin(th0)[:, None] * UP)


def unmorph(M):
    """morphed -> world: follow the curved ray of the same initial direction for the same length"""
    rel = M - EYE
    s = np.linalg.norm(rel, axis=1)
    th0 = np.arcsin(np.clip(rel[:, 1] / np.maximum(s, 1e-12), -1, 1))
    th = np.arctan(np.sinh(F(th0) - G * s))
    rho = (th0 - th) / G
    y = np.log(np.cos(th) / np.cos(th0)) / G
    h = np.hypot(rel[:, 0], rel[:, 2])
    az = np.stack([rel[:, 0], np.zeros_like(s), rel[:, 2]], 1) / np.maximum(h, 1e-12)[:, None]
    return EYE + rho[:, None] * az + y[:, None] * UP


# ---------------------------------------------------------------- world as lines
def box_edges(b):
    x0, y0, z0, x1, y1, z1 = b
    c = np.array([[x, y, z] for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)])
    return [(c[i], c[j]) for i in range(8) for j in range(i + 1, 8)
            if (np.abs(c[i] - c[j]) > 0).sum() == 1]


def dense(a, b, step=0.2):
    n = max(2, int(np.linalg.norm(b - a) / step) + 1)
    return a + (b - a) * np.linspace(0, 1, n)[:, None]


def ground_lines(xr, zr, every):
    L = []
    for x in np.arange(xr[0], xr[1] + 1e-9, every):
        L.append((np.array([x, 0, zr[0]]), np.array([x, 0, zr[1]])))
    for z in np.arange(zr[0], zr[1] + 1e-9, every):
        L.append((np.array([xr[0], 0, z]), np.array([xr[1], 0, z])))
    return L


# ---------------------------------------------------------------- curved rays, a few, as paths
def paths(O, D, boxes, h=0.3, nmax=400):
    """same stepping as render.trace_curved, points kept"""
    out = []
    for p, d in zip(O.copy(), D.copy()):
        pts = [p.copy()]
        for _ in range(nmax):
            t, k = R.hit_boxes(p[None], d[None], boxes, h)
            if k[0] > 0:
                pts.append(p + d * t[0]); break
            p = p + d * h
            a = -G * (UP - d[1] * d)
            d = d + h * a; d /= np.linalg.norm(d)
            pts.append(p.copy())
            if abs(p[0]) > 60 or p[2] > 80 or p[1] > 40:
                break
        out.append(np.array(pts))
    return out


def blank(W_, H_, C, target, fov):
    """an Ext without scene: white, nothing hides anything"""
    e = X.Ext.__new__(X.Ext)
    yaw, pitch = X.look_at(C, target)
    e.W, e.H, e.C = W_, H_, np.array(C, float)
    e.f, e.r, e.up = R.frame(yaw, pitch)
    e.k = math.tan(math.radians(fov) / 2)
    e.t = np.full((H_ * R.SS, W_ * R.SS), np.inf)
    e.im = Image.new('RGB', (W_ * R.SS, H_ * R.SS), (255, 255, 255))
    e.d = X.ImageDraw.Draw(e.im)
    return e


# ---------------------------------------------------------------- figures
def ext_fall():
    S = R.street()
    ey, ep = X.look_at((-26, 16, -22), (0, 4, 14))
    ext = X.Ext(EW, EH, (-26, 16, -22), ey, ep, 60, S)
    O, D = X.rays_at(R.pinhole, (W, H, EYE, YAW, PITCH, FOV), X.corners(W, H, 3))
    for p in paths(O, D, S):
        ext.polyline(p, n=1)
    X.pinhole_sheet(ext, EYE, YAW, PITCH, FOV, W, H, 3.0)
    ext.dot(EYE)
    ext.save('ext_fall.png')


def fall_buffers():
    """the 'fall' picture again, keeping key and arc length per pixel (slow, cached)"""
    if os.path.exists(CACHE):
        c = np.load(CACHE)
        return c['key'], c['P'], c['T']
    O, D, _ = R.pinhole(W, H, EYE, YAW, PITCH, FOV)
    key, P, T = R.trace_curved(O, D, R.street(), fall)
    np.savez_compressed(CACHE, key=key, P=P, T=T)
    return key, P, T


def overlay():
    """the falling-rays picture, faded, with the morphed world drawn on it by a plain pinhole"""
    key, P, T = fall_buffers()
    S = R.SS
    g = R.shade(key, P, T, (H * S, W * S))
    g = 255 - (255 - g) * 0.45
    e = blank(W, H, EYE, EYE + R.frame(YAW, PITCH)[0], FOV)
    e.f, e.r, e.up = R.frame(YAW, PITCH)
    e.t = np.where(key > 0, T, np.inf).reshape(H * S, W * S)
    e.im = Image.fromarray(np.clip(g, 0, 255).astype(np.uint8)).convert('RGB')
    e.d = X.ImageDraw.Draw(e.im)
    lines = ground_lines((-10, 10), (-2, 40), 2)
    for a, b in lines:
        e.polyline(morph(dense(a, b)), n=1, width=0.6, hid=None)
    for b in R.street():
        for a, c in box_edges(b):
            e.polyline(morph(dense(a, c)), n=1, width=1.0, hid=None)
    e.save('persp_fall_morph.png')


def ext_morph():
    """the morphed world from outside, ray-traced: march straight rays, unmorph the samples"""
    S = R.street()
    C, target, fov = np.array([-26, 24, 6.0]), np.array([0, 12, 14.0]), 80
    yaw, pitch = X.look_at(C, target)
    O, D, _ = R.pinhole(EW, EH, C, yaw, pitch, fov)
    D = D / np.linalg.norm(D, axis=1, keepdims=True)
    N = len(O)

    def what(M, side0):
        """0 nothing, 1 ground crossed (side of the ground differs from the start), 2+i box i"""
        Pw = unmorph(M)
        k = np.where((Pw[:, 1] >= 0) != side0, 1, 0)
        for i, b in enumerate(S):
            k = np.where((Pw >= b[:3]).all(1) & (Pw <= b[3:]).all(1), 2 + i, k)
        return k, Pw

    # the morphed ground is a bowl, everything outside it is "underground": the ground is
    # treated as a surface, hit when crossed, from either side
    side = unmorph(O)[:, 1] >= 0
    h, tmax = 0.4, 130
    t = np.zeros(N); key = np.zeros(N, np.int64); Pw = np.zeros((N, 3)); act = np.arange(N)
    tt = np.zeros(N)
    while len(act) and tt[act[0]] < tmax:
        tn = tt[act] + h
        k, _ = what(O[act] + D[act] * tn[:, None], side[act])
        hit = k > 0
        if hit.any():
            idx = act[hit]
            a, b = tt[idx], tn[hit]
            for _ in range(10):          # refine the crossing
                m = (a + b) / 2
                km, _ = what(O[idx] + D[idx] * m[:, None], side[idx])
                a = np.where(km > 0, a, m); b = np.where(km > 0, m, b)
            kb, pw = what(O[idx] + D[idx] * b[:, None], side[idx])
            key[idx], Pw[idx], t[idx] = kb, pw, b
        tt[act] = tn
        act = act[~hit]
    # face of the box: nearest side of the world point
    ax = np.zeros(N, np.int64)
    bx = key >= 2
    for j in np.where(bx)[0]:
        b = S[key[j] - 2]
        dd = np.minimum(np.abs(Pw[j] - b[:3]), np.abs(Pw[j] - b[3:]))
        ax[j] = dd.argmin()
    key = np.where(bx, 2 + (key - 2) * 4 + ax, key)
    g = R.shade(key, Pw, np.where(key > 0, 1, 1e9), (EH * R.SS, EW * R.SS))
    g = 255 - (255 - g) * 0.5
    e = blank(EW, EH, C, target, fov)
    e.t = np.where(key > 0, t, np.inf).reshape(EH * R.SS, EW * R.SS)
    e.im = Image.fromarray(np.clip(g, 0, 255).astype(np.uint8)).convert('RGB')
    e.d = X.ImageDraw.Draw(e.im)
    # the same rays as ext_fall, straightened: same start, same length
    Or, Dr = X.rays_at(R.pinhole, (W, H, EYE, YAW, PITCH, FOV), X.corners(W, H, 3))
    for p, d in zip(paths(Or, Dr, S), Dr):
        s = np.linalg.norm(np.diff(p, axis=0), axis=1).sum()
        e.segment(EYE, EYE + d * s)
    e.dot(EYE)
    e.save('ext_fall_morph.png')


if __name__ == '__main__':
    todo = {'ext': ext_fall, 'overlay': overlay, 'morph': ext_morph}
    for k in (sys.argv[1:] or todo):
        todo[k]()

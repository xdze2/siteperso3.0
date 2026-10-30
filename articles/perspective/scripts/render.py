# one street of boxes, many cameras. a camera = a function pixel -> ray (origin, direction).
# straight rays: analytic box/ground intersection. curved rays: small straight segments.
# python3 + numpy + Pillow. Output: ../images/persp_*.png
import os, sys, math, time
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'images') + '/'
os.makedirs(OUT, exist_ok=True)
SS = 2  # supersampling

# luminance per face: sky, ground, x faces, y faces (tops), z faces
SKY, GROUND, XF, TOP, ZF = 244, 255, 150, 232, 200
GRID, EDGE = 200, 25


def street():
    rng = np.random.default_rng(3)
    b = []
    for side in (-1, 1):
        for x0, x1 in [(2, 4.5), (6.5, 9)]:
            for k in range(9):
                z0 = 2 + k * 3.5
                h = rng.uniform(1.5, 6)
                xa, xb = (x0, x1) if side > 0 else (-x1, -x0)
                b.append((xa, 0, z0, xb, h, z0 + 2.5))
    # a tower at the end of the street
    b.append((-1.2, 0, 36, 1.2, 9, 38.4))
    return np.array(b, float)


def cluster():
    return np.array([(-1.5, 0, -1, 1.5, 3, 1), (1.5, 0, -2.5, 3, 1.5, -0.5),
                     (-3, 0, 0.5, -1.5, 5, 2), (-0.5, 0, 1, 0.5, 6.5, 2)], float)


# ---------------------------------------------------------------- intersection
def hit_boxes(O, D, boxes, tmax):
    """first hit within (0, tmax). returns t, key (0 none, 1 ground, 2+.. box*4+axis)"""
    N = len(O)
    t = np.array(tmax, float) * np.ones(N)
    key = np.zeros(N, np.int64)
    Dz = np.where(np.abs(D) < 1e-12, 1e-12, D)
    inv = 1 / Dz
    with np.errstate(divide='ignore', invalid='ignore'):
        tg = -O[:, 1] / Dz[:, 1]
    ok = (D[:, 1] < 0) & (tg > 1e-9) & (tg < t)
    t[ok] = tg[ok]; key[ok] = 1
    for i, bx in enumerate(boxes):
        t1 = (bx[:3] - O) * inv
        t2 = (bx[3:] - O) * inv
        tn = np.minimum(t1, t2); tf = np.maximum(t1, t2)
        tnear = tn.max(1); tfar = tf.min(1)
        h = (tnear <= tfar) & (tnear > 1e-9) & (tnear < t)
        t[h] = tnear[h]
        key[h] = 2 + i * 4 + tn[h].argmax(1)
    return t, key


def trace_straight(O, D, boxes):
    D = D / np.linalg.norm(D, axis=1, keepdims=True)
    t, key = hit_boxes(O, D, boxes, 1e9)
    P = O + D * t[:, None]
    return key, P, t


def trace_curved(O, D, boxes, accel, h=0.3, nstep=260):
    """accel(p, d) -> dd/ds. rays marched in segments of length h."""
    D = D / np.linalg.norm(D, axis=1, keepdims=True)
    N = len(O)
    key = np.zeros(N, np.int64); P = np.zeros((N, 3)); T = np.zeros(N)
    act = np.arange(N)
    p, d = O.copy(), D.copy()
    for s in range(nstep):
        t, k = hit_boxes(p, d, boxes, h)
        done = k > 0
        idx = act[done]
        key[idx] = k[done]; P[idx] = p[done] + d[done] * t[done, None]; T[idx] = s * h + t[done]
        p, d, act = p[~done], d[~done], act[~done]
        p = p + d * h
        a = accel(p, d)
        a = a - (a * d).sum(1, keepdims=True) * d   # keep speed 1
        d = d + h * a
        d /= np.linalg.norm(d, axis=1, keepdims=True)
        far = (np.abs(p[:, 0]) > 60) | (p[:, 2] > 80) | (p[:, 2] < -40) | (p[:, 1] > 40)
        p, d, act = p[~far], d[~far], act[~far]
        if len(act) == 0:
            break
    return key, P, T


# ---------------------------------------------------------------- shading
def shade(key, P, t, shape, mask=None, grid=2.0, tgrid=45):
    H, W = shape
    key = key.reshape(H, W); P = P.reshape(H, W, 3); t = t.reshape(H, W)
    img = np.full((H, W), float(SKY))
    img[key == 1] = GROUND
    ax = (key - 2) % 4
    box = key >= 2
    img[box & (ax == 0)] = XF
    img[box & (ax == 1)] = TOP
    img[box & (ax == 2)] = ZF
    # ground grid: change of cell index between neighbours
    g = key == 1
    cell = np.where(g, np.floor(P[..., 0] / grid) * 1000 + np.floor(P[..., 2] / grid), -1)
    gl = np.zeros((H, W), bool)
    gl[:, 1:] |= cell[:, 1:] != cell[:, :-1]
    gl[1:, :] |= cell[1:, :] != cell[:-1, :]
    gl &= g & (t < tgrid)
    img[gl] = GRID
    if mask is not None:
        key = np.where(mask.reshape(H, W), key, -1)
        img[~mask.reshape(H, W)] = 255
    e = np.zeros((H, W), bool)
    dx = key[:, 1:] != key[:, :-1]; dy = key[1:, :] != key[:-1, :]
    e[:, 1:] |= dx; e[:, :-1] |= dx; e[1:, :] |= dy; e[:-1, :] |= dy
    img[e] = EDGE
    return img


def save(img, name):
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).reduce(SS)
    im.save(OUT + name)
    print('saved', name, im.size)


# ---------------------------------------------------------------- cameras
UV = None  # (u, v) arrays: override the pixel grid, to get a few rays only (extview.py)


def grid(W, H):
    """pixel centres, u in [-1, 1] across the width, v same scale, up positive"""
    if UV is not None:
        return UV
    w, h = W * SS, H * SS
    x = (np.arange(w) + 0.5) / w * 2 - 1
    y = ((np.arange(h) + 0.5) - h / 2) / (w / 2)
    u, v = np.meshgrid(x, -y)
    return u.ravel(), v.ravel()


def frame(yaw, pitch):
    y, p = math.radians(yaw), math.radians(pitch)
    f = np.array([math.sin(y) * math.cos(p), math.sin(p), math.cos(y) * math.cos(p)])
    r = np.array([math.cos(y), 0, -math.sin(y)])
    up = np.cross(f, r)
    return f, r, up


def col(a):
    return a[:, None]


def pinhole(W, H, C, yaw, pitch, hfov):
    u, v = grid(W, H)
    f, r, up = frame(yaw, pitch)
    k = math.tan(math.radians(hfov) / 2)
    D = f + col(u * k) * r + col(v * k) * up
    return np.tile(C, (len(u), 1)).astype(float), D, None


def cylindrical(W, H, C, yaw, span):
    u, v = grid(W, H)
    f, r, up = frame(yaw, 0)
    a = math.radians(span) / 2
    th = u * a
    D = col(np.cos(th)) * f + col(np.sin(th)) * r + col(v * a) * up
    return np.tile(C, (len(u), 1)).astype(float), D, None


def fisheye(W, H, C, yaw, pitch, span):
    """equidistant: distance from centre = angle from the axis"""
    u, v = grid(W, H)
    f, r, up = frame(yaw, pitch)
    rho = np.hypot(u, v)
    a = rho * math.radians(span) / 2
    s = np.sin(a) / np.maximum(rho, 1e-9)
    D = col(np.cos(a)) * f + col(s * u) * r + col(s * v) * up
    return np.tile(C, (len(u), 1)).astype(float), D, rho <= 1


def equirect(W, H, C, yaw):
    u, v = grid(W, H)
    f, r, up = frame(yaw, 0)
    th, ph = u * math.pi, v * math.pi
    D = col(np.cos(ph) * np.cos(th)) * f + col(np.cos(ph) * np.sin(th)) * r + col(np.sin(ph)) * up
    return np.tile(C, (len(u), 1)).astype(float), D, None


def parallel(W, H, C, yaw, pitch, half, shear=(0, 0)):
    """orthographic (shear 0) or oblique: all rays parallel, origins on a plane"""
    u, v = grid(W, H)
    f, r, up = frame(yaw, pitch)
    D = np.tile(f + shear[0] * r + shear[1] * up, (len(u), 1))
    O = C + col(u * half) * r + col(v * half) * up - 200 * D   # start far back, above the ground
    return O, D, None


def pushbroom(W, H, C, z0, z1, k, tilt=0):
    """the eye slides along the street (z), looks to +x. perspective in v only"""
    u, v = grid(W, H)
    O = np.tile(C, (len(u), 1)).astype(float)
    O[:, 2] = z0 + (u + 1) / 2 * (z1 - z0)
    D = np.stack([np.ones_like(u), v * k - tilt, np.zeros_like(u)], 1)
    return O, D, None


def crossed_slits(W, H, C, yaw, pitch, a, b, d1, d2):
    """rays meet a vertical slit at depth d1 and a horizontal slit at depth d2 (along f)"""
    u, v = grid(W, H)
    f, r, up = frame(yaw, pitch)
    D = f + col(u * a) * r + col(v * b) * up
    O = C - col(d1 * u * a) * r - col(d2 * v * b) * up
    return O, D, None


def reverse(W, H, C, yaw, pitch, half, L):
    """origins on a plane, rays converge on a point L in front, beyond the scene"""
    u, v = grid(W, H)
    f, r, up = frame(yaw, pitch)
    O = C + col(u * half) * r + col(v * half) * up
    D = (C + L * f) - O
    return O, D, None


def cylinder_in(W, H, A, R, y0, yspan, tilt):
    """rays normal to a vertical cylinder of radius R, pointing to its axis (tilted down)"""
    u, v = grid(W, H)
    th = u * math.pi
    n = np.stack([np.sin(th), np.zeros_like(th), np.cos(th)], 1)
    O = A + R * n
    O[:, 1] = y0 + v * yspan
    D = -n + np.array([0, -tilt, 0])
    return O, D, None


def render(name, W, H, cam, boxes, curved=None, **kw):
    t0 = time.time()
    O, D, mask = cam
    if curved is None:
        key, P, t = trace_straight(O, D, boxes)
    else:
        key, P, t = trace_curved(O, D, boxes, curved)
    save(shade(key, P, t, (H * SS, W * SS), mask, **kw), name)
    print('  %.1fs' % (time.time() - t0))


# ---------------------------------------------------------------- the pictures
def main(which):
    S = street()
    W, H = 700, 380
    eye = np.array([0, 1.6, -4.0])
    todo = {
        # 1. the pinhole, three poses of the same plane
        'p1': lambda: render('persp_1pt.png', W, H, pinhole(W, H, eye, 0, 0, 80), S),
        'p2': lambda: render('persp_2pt.png', W, H, pinhole(W, H, np.array([-15, 1.6, -9.0]), 33, 0, 70), S),
        'p3': lambda: render('persp_3pt.png', W, H, pinhole(W, H, np.array([-22, 22, -14.0]), 34, -30, 75), S, tgrid=200),
        'wide': lambda: render('persp_wide.png', W, H, pinhole(W, H, np.array([0, 1.6, 6.0]), 0, 0, 150), S),
        # 2. same point, curved receiving surface
        'cyl': lambda: render('persp_cylinder.png', W, H, cylindrical(W, H, np.array([0, 1.6, 6.0]), 0, 220), S),
        'fish': lambda: render('persp_fisheye.png', 460, 460, fisheye(460, 460, np.array([0, 1.6, 6.0]), 0, 0, 180), S),
        'fishup': lambda: render('persp_fisheye_up.png', 460, 460, fisheye(460, 460, np.array([0, 1.6, 14.0]), 0, 90, 180), S),
        'equi': lambda: render('persp_equirect.png', W, 350, equirect(W, 350, np.array([0, 1.6, 14.0]), 0), S),
        # 3. the eye is not a point
        'iso': lambda: render('persp_iso.png', W, H, parallel(W, H, np.array([0, 0, 18.0]), 45, -35.26, 22), S, tgrid=1e9),
        'obl': lambda: render('persp_oblique.png', W, H, parallel(W, H, np.array([0, 3, 18.0]), 0, 0, 22, (0.5, -0.4)), S, tgrid=1e9),
        'push': lambda: render('persp_pushbroom.png', W, 300, pushbroom(W, 300, np.array([0, 3.5, 0]), 0, 34, 5, 0.25), S),
        'slit': lambda: render('persp_crossed_slits.png', W, H,
                               crossed_slits(W, H, np.array([-15, 3.0, -9.0]), 33, 0, 0.7, 0.7 * 25 / 19, 0, 6), S),
        'rev': lambda: render('persp_reverse.png', W, H, reverse(W, H, np.array([0, 8.0, -25.0]), 0, -8, 14, 90), S),
        'cylin': lambda: render('persp_cylinder_in.png', W, 300, cylinder_in(W, 300, np.zeros(3), 14, 4.5, 9, 0.3), cluster(), grid=1.0),
        'cylpin': lambda: render('persp_cluster_pin.png', 360, 300, pinhole(360, 300, np.array([-9, 5, -11.0]), 40, -15, 50), cluster(), grid=1.0),
        # 4. curved rays
        'lens': lambda: render('persp_lens.png', W, H, pinhole(W, H, eye, 0, 0, 80), S,
                               curved=lambda p, d: lens(p, np.array([0, 3.0, 14.0]), 1.6)),
        'twist': lambda: render('persp_twist.png', W, H, pinhole(W, H, eye, 0, 0, 80), S,
                                curved=lambda p, d: np.cross(np.tile([0, 0, 0.035], (len(d), 1)), d) * np.clip(p[:, 2:3], 0, None)),
        'fall': lambda: render('persp_fall.png', W, H, pinhole(W, H, eye, 0, 12, 80), S,
                               curved=lambda p, d: np.tile([0, -0.035, 0], (len(d), 1))),
    }
    for k in (which or todo):
        todo[k]()


def lens(p, c, m):
    r = c - p
    d2 = (r * r).sum(1, keepdims=True)
    return m * r / (d2 * np.sqrt(d2) + 0.05)


if __name__ == '__main__':
    main(sys.argv[1:])

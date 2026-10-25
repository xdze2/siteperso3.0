# chapter 4 demos: light-from-above prior, cast shadow and height, line direction, occlusion/T-junctions.
# python3 + numpy + Pillow. Everything analytic, no dependency on scene/. Output: ../../images/percep_*.png
import os, math
import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', '..', 'images') + '/'
os.makedirs(OUT, exist_ok=True)
SS = 3


def save(arr_ink, name):
    """arr_ink: float 0..1 (1 = ink) at SS resolution -> box downscale -> png"""
    im = Image.fromarray((255 * (1 - np.clip(arr_ink, 0, 1))).astype(np.uint8))
    im = im.reduce(SS)
    im.save(OUT + name)
    print('saved', name, im.size)


def canvas(w, h):
    im = Image.new('L', (w * SS, h * SS), 255)
    return im, ImageDraw.Draw(im)


def ink_of(im):
    return 1 - np.asarray(im, dtype=np.float32) / 255


def hatch(shape, tone, mask, families, lw=0.9):
    """line screens. tone, mask at SS resolution. families: (angle_deg, spacing_px, tone threshold)"""
    H, W = shape
    Y, X = np.mgrid[0:H, 0:W].astype(np.float32) / SS
    ink = np.zeros(shape, np.float32)
    for ang, sp, thr in families:
        a = math.radians(ang)
        u = (X * math.cos(a) + Y * math.sin(a)) / sp
        line = np.abs(((u + 0.5) % 1.0) - 0.5) * sp < lw / 2
        ink = np.maximum(ink, (line & (tone > thr) & mask).astype(np.float32))
    return ink


# ---------------------------------------------------------------- a) light from above
def light_above():
    cols = ['U', 'D', 'U', 'U', 'D', 'U']      # light from Up / Down
    R, gap = 52, 14
    W = len(cols) * (2 * R + gap) + gap
    H = 2 * (2 * R + gap) + gap
    rng = np.random.default_rng(5)
    g = np.full((H * SS, W * SS), 255.0)
    im, d = canvas(W, H)
    Y, X = np.mgrid[0:H * SS, 0:W * SS].astype(np.float32) / SS
    for row in (0, 1):
        for i, c in enumerate(cols):
            cx = gap + R + i * (2 * R + gap)
            cy = gap + R + row * (2 * R + gap)
            nx = (X - cx) / R; ny = (Y - cy) / R
            r2 = nx ** 2 + ny ** 2
            m = r2 < 1
            nz = np.sqrt(np.clip(1 - r2, 0, 1))
            sgn = -1 if c == 'U' else 1                     # image y points down
            L = np.array([-0.25, sgn * 0.6, 0.76]); L /= np.linalg.norm(L)
            lum = np.clip(nx * L[0] + ny * L[1] + nz * L[2], 0, 1) * 0.92 + 0.08
            dark = 1 - lum
            if row == 0:
                g[m] = (255 * lum)[m]
            else:
                # stipple: dots with probability ~ darkness
                n = int(math.pi * R * R * 1.1)
                px = rng.uniform(cx - R, cx + R, n * 3); py = rng.uniform(cy - R, cy + R, n * 3)
                k = 0
                for x, y in zip(px, py):
                    nxx = (x - cx) / R; nyy = (y - cy) / R
                    q = nxx ** 2 + nyy ** 2
                    if q >= 0.98: continue
                    t = 1 - (np.clip(nxx * L[0] + nyy * L[1] + math.sqrt(1 - q) * L[2], 0, 1) * 0.92 + 0.08)
                    if rng.random() < t * 0.45:
                        d.ellipse([(x - 0.7) * SS, (y - 0.7) * SS, (x + 0.7) * SS, (y + 0.7) * SS], fill=0)
                d.ellipse([(cx - R) * SS, (cy - R) * SS, (cx + R) * SS, (cy + R) * SS], outline=0, width=SS)
    ink = np.maximum(ink_of(im), 1 - g / 255)
    save(ink, 'percep_light_above.png')


# ---------------------------------------------------------------- b) ball and cast shadow
def shadow_ball():
    PW, PH = 330, 290
    gap = 20
    W = 2 * PW + gap; H = PH
    im, d = canvas(W, H)
    ink = np.zeros((H * SS, W * SS), np.float32)
    Y, X = np.mgrid[0:H * SS, 0:W * SS].astype(np.float32) / SS

    def line(p, q, w=1.0):
        d.line([(p[0] * SS, p[1] * SS), (q[0] * SS, q[1] * SS)], fill=0, width=max(1, int(w * SS)))

    for k, shadow in enumerate([(185, 198, 32, 9), (235, 242, 32, 9)]):
        ox = k * (PW + gap)
        # box: back wall, floor
        bw = (ox + 40, 50, ox + 290, 150)       # back wall x0,y0,x1,y1
        line((bw[0], bw[1]), (bw[2], bw[1])); line((bw[0], bw[3]), (bw[2], bw[3]))
        line((bw[0], bw[1]), (bw[0], bw[3])); line((bw[2], bw[1]), (bw[2], bw[3]))
        fl = [(ox + 4, 282), (ox + 326, 282)]
        line((bw[0], bw[3]), fl[0]); line((bw[2], bw[3]), fl[1]); line(fl[0], fl[1])
        # floor perspective lines to a vanishing point
        vp = (ox + 165, 10)
        for fx in np.linspace(fl[0][0], fl[1][0], 9)[1:-1]:
            t = (bw[3] - 282) / (vp[1] - 282)
            line((fx, 282), (fx + (vp[0] - fx) * t, bw[3]), 0.5)
        for yy in (172, 200, 232, 282):
            xl = fl[0][0] + (bw[0] - fl[0][0]) * (282 - yy) / (282 - bw[3])
            xr = fl[1][0] + (bw[2] - fl[1][0]) * (282 - yy) / (282 - bw[3])
            line((xl, yy), (xr, yy), 0.4)
        # shadow: ellipse, horizontal hatch
        sx, sy, rx, ry = shadow
        sx += ox
        m = ((X - sx) / rx) ** 2 + ((Y - sy) / ry) ** 2 < 1
        white = m & (((X - sx) / (rx + 3)) ** 2 + ((Y - sy) / (ry + 3)) ** 2 < 1)
        ink[white] = 0
        sh = hatch(ink.shape, np.ones_like(ink), m, [(0, 2.3, 0)], lw=1.0)
        # clear floor lines under the shadow, then draw shadow
        ink_lines = ink_of(im)
        ink_lines[white] = 0
        ink = np.maximum(ink_lines, sh)
        im = Image.fromarray((255 * (1 - ink)).astype(np.uint8)); d = ImageDraw.Draw(im)
        # ball
        bx, by, R = ox + 175, 166, 28
        d.ellipse([(bx - R) * SS, (by - R) * SS, (bx + R) * SS, (by + R) * SS], fill=255)
        nx = (X - bx) / R; ny = (Y - by) / R
        r2 = nx ** 2 + ny ** 2
        mb = r2 < 1
        L = np.array([-0.5, -0.55, 0.67]); L /= np.linalg.norm(L)
        lum = np.clip(nx * L[0] + ny * L[1] + np.sqrt(np.clip(1 - r2, 0, 1)) * L[2], 0, 1)
        T = 1 - lum
        hb = hatch(ink.shape, T, mb, [(55, 2.6, 0.45), (-35, 2.6, 0.72)], lw=0.8)
        cur = ink_of(im)
        cur[mb] = 0
        ink = np.maximum(cur, hb)
        im = Image.fromarray((255 * (1 - ink)).astype(np.uint8)); d = ImageDraw.Draw(im)
        d.ellipse([(bx - R) * SS, (by - R) * SS, (bx + R) * SS, (by + R) * SS], outline=0, width=int(1.3 * SS))
        ink = ink_of(im)
    save(ink[36 * SS:], "percep_shadow_ball.png")


# ---------------------------------------------------------------- c) line direction on a vase
def vase_field(PW, PH, S, e):
    """per pixel (SS res): mask, param y, tone. orthographic view from elevation e, surface of revolution"""
    def prof(y): return 0.20 + 0.23 * np.exp(-((y - 0.33) / 0.2) ** 2) + 0.05 * np.exp(-((y - 0.88) / 0.1) ** 2)
    def dprof(y): return (prof(y + 1e-4) - prof(y - 1e-4)) / 2e-4
    H, W = PH * SS, PW * SS
    Yp, Xp = np.mgrid[0:H, 0:W].astype(np.float32)
    X = (Xp / SS - PW / 2) / S
    Ysc = (PH * 0.86 - Yp / SS) / S              # screen up = positive, y=0 foot at 86% of height
    ce, se = math.cos(e), math.sin(e)
    ys = np.linspace(0, 1, 600).astype(np.float32)
    best = np.full((H, W), np.nan, np.float32)
    prev = None
    for y in ys:
        r = prof(y)
        s = np.clip(X / r, -1, 1)
        z = r * np.sqrt(1 - s * s)
        diff = (y * ce - z * se) - Ysc
        ok = np.abs(X) < r
        if prev is not None:
            cross = ok & prev[1] & (np.sign(diff) != np.sign(prev[0]))
            best = np.where(cross, y, best)
        prev = (diff, ok)
    mask = np.isfinite(best)
    yy = np.where(mask, best, 0.5)
    r = prof(yy); s = np.clip(X / r, -1, 1); c = np.sqrt(1 - s * s)
    n = np.stack([s, -dprof(yy), c], -1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    L = np.array([-0.55, 0.6, 0.6]); L /= np.linalg.norm(L)
    lum = np.clip((n * L).sum(-1), 0, 1) * 0.95 + 0.05
    T = 1 - lum
    return mask, yy, T, X, Ysc


def line_direction():
    PW, PH, S, e = 250, 330, 250, math.radians(24)
    mask, yy, T, X, Ysc = vase_field(PW, PH, S, e)
    shape = mask.shape
    Yp, Xp = np.mgrid[0:shape[0], 0:shape[1]].astype(np.float32) / SS
    sp = 3.4
    lw_max = 2.1

    def screen(u, sp):
        """width modulated line screen: u = coordinate (px); width ~ tone"""
        f = np.abs(((u / sp) + 0.5) % 1.0 - 0.5) * sp         # distance to line centre
        w = lw_max * np.clip(T * 1.25, 0, 1) * 0.5
        return (f < w) & mask

    # 1) along the principal direction (parallels of the vase): u = param y, scaled to px
    p1 = screen(yy * S * math.cos(e), sp).astype(np.float32)
    # 2) fixed angle
    a = math.radians(40)
    p2 = screen(Xp * math.cos(a) + Yp * math.sin(a), sp).astype(np.float32)
    # 3) short strokes, random directions, same amount of ink
    rng = np.random.default_rng(11)
    target = p1.sum() / SS ** 2
    Lseg = 7.0
    imd = Image.new('L', (shape[1], shape[0]), 255); dd = ImageDraw.Draw(imd)
    ink_px = 0.0; last = 0.0
    while ink_px < target * 3:
        x = rng.uniform(0, PW); y = rng.uniform(0, PH)
        xi, yi = int(x * SS), int(y * SS)
        if not mask[yi, xi]: continue
        if rng.random() > T[yi, xi] ** 1.0: continue
        a = rng.uniform(0, math.pi)
        dx, dy = math.cos(a) * Lseg / 2, math.sin(a) * Lseg / 2
        dd.line([((x - dx) * SS, (y - dy) * SS), ((x + dx) * SS, (y + dy) * SS)], fill=0, width=int(1.1 * SS))
        ink_px += Lseg * 1.1 * 0.8
        if int(ink_px) % 400 < 6 and (ink_px - last) > 300:
            last = ink_px
            if (ink_of(imd) * mask).sum() / SS ** 2 >= target: break
    p3 = ink_of(imd) * mask
    # outline: mask boundary
    def outline(m):
        mm = m.astype(np.uint8)
        er = mm.copy()
        k = SS
        for dy_, dx_ in [(-k, 0), (k, 0), (0, -k), (0, k)]:
            er &= np.roll(mm, (dy_, dx_), (0, 1))
        return (mm - er).astype(np.float32)
    ol = outline(mask)
    gap = 18
    W = 3 * PW + 2 * gap
    out = np.ones((PH * SS, W * SS), np.float32) * 0
    for i, p in enumerate((p1, p2, p3)):
        out[:, i * (PW + gap) * SS:(i * (PW + gap) + PW) * SS] = np.maximum(p, ol)
    save(out, 'percep_line_direction.png')
    # tone check
    for nme, p in (('along', p1), ('fixed', p2), ('random', p3)):
        print(nme, 'ink', float(p[mask].mean()))


# ---------------------------------------------------------------- d) occlusion and T-junctions
def occlusion():
    PW, PH, gap = 230, 140, 20
    W = 4 * PW + 3 * gap
    im, d = canvas(W, PH)
    sq = (40, 20, 130, 110)     # square (relative to panel), centre (105,105)
    cc, cr = (130, 80), 48     # circle partly behind/over the square's right side

    def poly_circle():
        return [(cc[0] + cr * math.cos(t), cc[1] + cr * math.sin(t)) for t in np.linspace(0, 2 * math.pi, 721)]

    def inside_sq(p, m=0):
        return sq[0] - m < p[0] < sq[2] + m and sq[1] - m < p[1] < sq[3] + m

    def inside_circ(p, m=0):
        return math.hypot(p[0] - cc[0], p[1] - cc[1]) < cr + m

    def strokes(ox, pts, hide, closed=True):
        seg = []
        for p in pts:
            if hide(p):
                if len(seg) > 1: d.line([((ox + q[0]) * SS, q[1] * SS) for q in seg], fill=0, width=int(1.3 * SS))
                seg = []
            else:
                seg.append(p)
        if len(seg) > 1:
            d.line([((ox + q[0]) * SS, q[1] * SS) for q in seg], fill=0, width=int(1.3 * SS))

    def sq_pts():
        pts = []
        for t in np.linspace(0, 1, 100): pts.append((sq[0] + t * (sq[2] - sq[0]), sq[1]))
        for t in np.linspace(0, 1, 100): pts.append((sq[2], sq[1] + t * (sq[3] - sq[1])))
        for t in np.linspace(0, 1, 100): pts.append((sq[2] - t * (sq[2] - sq[0]), sq[3]))
        for t in np.linspace(0, 1, 100): pts.append((sq[0], sq[3] - t * (sq[3] - sq[1])))
        pts.append(pts[0]); return pts

    # NB: the square is drawn as one polyline broken where hidden
    modes = ['wire', 'sq_front', 'circ_front', 'sq_front_gap']
    for i, mode in enumerate(modes):
        ox = i * (PW + gap)
        if mode == 'wire':
            strokes(ox, sq_pts(), lambda p: False); strokes(ox, poly_circle(), lambda p: False)
        elif mode in ('sq_front', 'sq_front_gap'):
            m = 0 if mode == 'sq_front' else 7
            strokes(ox, sq_pts(), lambda p: False)
            strokes(ox, poly_circle(), lambda p: inside_sq(p, m))
        else:
            strokes(ox, poly_circle(), lambda p: False)
            strokes(ox, sq_pts(), lambda p: inside_circ(p))
    save(ink_of(im), 'percep_occlusion.png')


if __name__ == '__main__':
    import sys
    which = sys.argv[1:] or ['a', 'b', 'c', 'd']
    if 'a' in which: light_above()
    if 'b' in which: shadow_ball()
    if 'c' in which: line_direction()
    if 'd' in which: occlusion()

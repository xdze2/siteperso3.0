# Line simplification demo: same tree landscape drawn naively vs with level of detail.
# python3 + numpy + PIL. Output ../../images/lines_trees_*.png, lines_dp.png
import os, math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__))
O = os.path.join(HERE, '..', '..', 'images', 'lines_')
K = 4                         # supersampling
BG = 244
W, H = 500, 230
HOR = 85                      # horizon row
F = 130                       # ground: y = HOR + F/z
HF = 200                      # tree height: h = HF/z
SX = 200                      # x = W/2 + X*SX/z

try: FONT = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 10); EPS = '\u03b5'
except OSError:
    EPS = 'eps'
    try: FONT = ImageFont.load_default(size=10)
    except TypeError: FONT = ImageFont.load_default()

class Cv:
    def __init__(s, w, h, k=K):
        s.k = k; s.im = Image.new('L', (w*k, h*k), BG); s.d = ImageDraw.Draw(s.im); s.w = w; s.h = h
    def line(s, p, w, g):
        k = s.k; wd = max(1, round(w*k))
        s.d.line([(x*k, y*k) for x, y in p], fill=int(g), width=wd)
        if wd > 2:  # round joints
            for x, y in p[1:-1]: s.d.ellipse([x*k-wd/2, y*k-wd/2, x*k+wd/2, y*k+wd/2], fill=int(g))
    def fill(s, p, g=BG):
        s.d.polygon([(x*s.k, y*s.k) for x, y in p], fill=g)
    def out(s):
        return s.im.resize((s.w, s.h), Image.LANCZOS)

def scan(poly, y):
    xs = []
    n = len(poly)
    for i in range(n):
        (x0, y0), (x1, y1) = poly[i], poly[(i+1) % n]
        if (y0 <= y < y1) or (y1 <= y < y0):
            xs.append(x0 + (x1-x0)*(y-y0)/(y1-y0))
    return (min(xs), max(xs)) if len(xs) >= 2 else None

# ---------------------------------------------------------------- one tree
def geometry(x, base, h, tiers):
    """contour of a conifer: list of right-side points (dx, y), apex first; foliage bottom y; half-widths"""
    top = base - h; fh = 0.80*h; yb = top + fh
    wd = 0.19*h
    if tiers == 1:
        return top, yb, wd, [(0, top), (wd, yb)], None
    ys = [top + fh*k/tiers for k in range(tiers+1)]
    ws = [0]+[wd*(0.55+0.45*k/tiers) for k in range(1, tiers+1)]
    ap = [top]+[ys[k-1]-0.10*fh for k in range(2, tiers+1)]
    ap = [top] + [ys[k-1]-0.12*fh for k in range(2, tiers+1)]
    right = [(0, top)]
    for k in range(1, tiers+1):
        right.append((ws[k], ys[k]))
        if k < tiers:   # notch where tier k+1 slope crosses y_k
            nx = ws[k+1]*(ys[k]-ap[k])/(ys[k+1]-ap[k])
            right.append((nx, ys[k]+0.015*h))
    tri = [(ap[k-1], ys[k], ws[k]) for k in range(1, tiers+1)]   # apex y, bottom y, half-width
    return top, yb, wd, right, tri

def draw_tree(cv, x, base, h, level, g, w, hatch_n=None, shadow=True, rng=None):
    """level: 0 full, 1 simplified, 2 triangle, 3 mark"""
    rng = rng or random
    if level == 3:
        top = base-h; hw = 0.22*h
        cv.fill([(x, top), (x+hw, base-0.1*h), (x-hw, base-0.1*h)])
        cv.line([(x-hw, base-0.1*h), (x, top), (x+hw, base-0.1*h)], w, g)
        return
    tiers = 3 if level == 0 else 1
    top, yb, wd, right, tri = geometry(x, base, h, tiers)
    left = [(-dx, y) for dx, y in right]
    contour = [(x+dx, y) for dx, y in right] + [(x+dx, y) for dx, y in reversed(left)]
    trunk_w = 0.035*h
    sil = contour + [(x-trunk_w, base), (x+trunk_w, base)]
    # cast shadow (light from the left): drawn before, the tree masks it
    if shadow and level <= 2:
        Ls = 0.95*h
        A = (x-0.07*h, base); B = (x+0.07*h, base+0.12*h); T = (x+Ls, base+0.05*h)
        if level == 0:
            poly = [A, T, B]
            n = max(2, int(0.12*h/2.4))
            for i in range(1, n+1):
                yy = A[1] + (B[1]-A[1])*i/(n+1)
                r = scan(poly, yy)
                if r: cv.line([(r[0], yy), (r[1], yy)], w*0.6, g+25)
        elif level == 1:
            cv.line([(x+0.05*h, base+0.04*h), (x+Ls, base+0.035*h)], w*1.3, g)
        else:
            cv.line([(x+0.05*h, base+0.03*h), (x+Ls*0.8, base+0.03*h)], w, min(235, g+50))
    cv.fill(sil)
    # trunk
    if level <= 1:
        cv.line([(x-trunk_w, yb), (x-trunk_w, base)], w, g)
        cv.line([(x+trunk_w, yb), (x+trunk_w, base)], w, g)
        cv.line([(x-0.12*h, base), (x-trunk_w, base)], w, g)
        cv.line([(x+trunk_w, base), (x+0.12*h, base)], w, g)
    elif level == 2:
        cv.line([(x, yb), (x, base)], w, g)
    # contour
    if level == 2:
        cv.line([(x, top), (x+wd, yb), (x-wd, yb), (x, top)], w, g)
    else:
        cv.line(contour + [contour[0]], w, g)
    # hatching on the shadow side (right half), following the tier slope
    if level <= 1:
        if tiers == 3:
            m = hatch_n if hatch_n else max(3, int(h/16))
            for (a, yk, wk) in tri:
                for j in range(m):
                    yy = a + (yk-a)*(0.28+0.62*(j+0.5)/m)
                    half = wk*(yy-a)/(yk-a)
                    x0 = x+0.25*half; x1 = x+0.93*half
                    cv.line([(x0, yy), (x1, yy+0.07*half)], w*0.8, g)
        else:
            m = hatch_n if hatch_n else 4
            for j in range(m):
                yy = top + (yb-top)*(0.3+0.62*(j+0.5)/m)
                half = wd*(yy-top)/(yb-top)
                cv.line([(x+0.2*half, yy), (x+0.9*half, yy+0.06*half)], w*0.85, g)

# ---------------------------------------------------------------- scene
def make_trees():
    R = random.Random(7)
    trees = []
    z0, z1 = 1.25, 70.0
    rho = lambda z: 0.13*(1+(5.0/z)**2)
    rmax = rho(z0)
    while len(trees) < 9000:
        z = math.sqrt(R.uniform(z0*z0, z1*z1))
        if R.random() > rho(z)/rmax: continue
        # visible half-width in world units at depth z, with margin
        hw = (W/2+30)*z/SX
        X = R.uniform(-hw, hw)
        trees.append((z, W/2+X*SX/z))
        # stop when expected count reached
        if len(trees) > 2600: break
    # thin to the expected number: area integral
    return trees

def thin(trees):
    R = random.Random(3)
    out = []
    # keep each candidate with prob so that density per world area = rho(z)
    # candidates were drawn with pdf ~ z * rho(z)/rmax * (1/hw)... simple: take first N
    return trees

def scene(seed=7, n_expected=None):
    R = random.Random(seed)
    rho = lambda z: 0.16*(1+(4.0/z)**2)
    z0, z1 = 1.25, 70.0
    trees = []
    # Poisson count per z-slab
    dz = 0.05; z = z0
    while z < z1:
        hw = (W/2+30)*z/SX
        lam = rho(z)*2*hw*dz
        n = int(lam) + (1 if R.random() < lam-int(lam) else 0)
        for _ in range(n):
            zz = z+R.random()*dz
            X = R.uniform(-hw, hw)
            trees.append((zz, W/2+X*SX/zz))
        z += dz
    trees.sort(reverse=True)
    return trees

def ground_rows(naive):
    rows = []
    if naive:
        z = 1.1
        while z < 90:
            rows.append(HOR+F/z); z += 0.12 if z < 5 else 0.35
        return rows
    y = HOR+F/1.05; 
    while y > HOR+8:
        t = (y-HOR)/(H-HOR)
        rows.append(y)
        y -= 3.5 + 11*(1-t)**1.0
    return rows

def draw_ground(cv, naive, R):
    rows = ground_rows(naive)
    for y in rows:
        t = max(0.0, (y-HOR)/(H-HOR))
        if y > H+2: continue
        if naive:
            scale = 90/max(1e-3, F/(y-HOR+1e-6))*0+ (y-HOR)/F
            x = -R.random()*30
            while x < W:
                L = max(1.0, 22*(y-HOR)/ (F/1.5)) * (0.5+R.random())
                gap = L*(0.4+R.random()*1.2)
                cv.line([(x, y), (x+L, y)], 0.7, 120)
                x += L+gap
        else:
            g = 175 - 50*t; w = 0.45+0.35*t
            p = 0.25+0.5*t
            x = -R.random()*30
            while x < W:
                L = (6+30*t)*(0.5+R.random())
                gap = L*(0.5+R.random()*1.5)
                if R.random() < p+0.2:
                    cv.line([(x, y), (x+L, y)], w, g)
                x += L+gap

LEV = [70, 35, 17, 9]    # screen height thresholds (px) between levels
PAR = {0: (22, 0.95), 1: (45, 0.8), 2: (85, 0.62), 3: (125, 0.5)}

def render(naive, trees, seed=5):
    R = random.Random(seed)
    cv = Cv(W, H)
    draw_ground(cv, naive, R)
    cv.line([(0, HOR), (W, HOR)], 0.7 if naive else 0.5, 40 if naive else 110)
    merged = [(z, x) for z, x in trees if HF/z < LEV[3]]
    if not naive and merged:
        # typification: one ragged line along the top of the forest clump
        env = np.full(W+40, float(HOR))
        zb = min(z for z, x in merged)
        for z, x in merged:
            h = HF/z; base = HOR+F/z
            xi = int(x)+20
            for xx in range(max(0, xi-2), min(W+40, xi+3)):
                env[xx] = min(env[xx], base-h*0.9)
        # smooth by 2-px running min/mean, sawtooth
        sm = np.convolve(np.pad(env, 3, mode='edge'), np.ones(7)/7, 'valid')
        ybot = HOR+F/zb
        pts = []
        for i in range(0, W, 3):
            pts.append((i, sm[i+20]+0.8*(1 if (i//3) % 2 else -1)))
        cv.fill(pts+[(W, ybot), (0, ybot)])
        cv.line(pts, 0.55, 120)
        # sparse base stroke
        x = 0
        while x < W:
            L = 10+R.random()*30
            if R.random() < 0.5: cv.line([(x, ybot), (x+L, ybot)], 0.4, 175)
            x += L+8+R.random()*20
    for z, x in trees:
        h = HF/z; base = HOR+F/z
        if x < -40 or x > W+40: continue
        if naive:
            draw_tree(cv, x, base, h, 0, 25, 0.8, hatch_n=4, rng=R)
            continue
        if h < LEV[3]: continue
        lv = 0 if h >= LEV[0] else 1 if h >= LEV[1] else 2 if h >= LEV[2] else 3
        g, w = PAR[lv]
        draw_tree(cv, x, base, h, lv, g, w, rng=R)
    return cv.out()

# ---------------------------------------------------------------- tone check
def gauss1d(s):
    r = int(3*s); x = np.arange(-r, r+1); k = np.exp(-x*x/(2*s*s)); return k/k.sum()
def blur(a, s):
    k = gauss1d(s); r = len(k)//2
    p = np.pad(a, ((0, 0), (r, r)), mode='edge')
    a = sum(k[i]*p[:, i:i+a.shape[1]] for i in range(len(k)))
    p = np.pad(a, ((r, r), (0, 0)), mode='edge')
    return sum(k[i]*p[i:i+a.shape[0], :] for i in range(len(k)))

def tone(naive_im, lod_im):
    a = np.asarray(naive_im, float); b = np.asarray(lod_im, float)
    sig = 7
    ba = blur(a, sig); bb = blur(b, sig)
    # stretch the blurred images so the difference is visible
    def st(x): return np.clip((x-150)/(BG-150), 0, 1)*255
    PW = 150
    out = Image.new('L', (W+PW, 2*H+4), 255)
    out.paste(Image.fromarray(st(ba).astype(np.uint8)), (0, 0))
    out.paste(Image.fromarray(st(bb).astype(np.uint8)), (0, H+4))
    d = ImageDraw.Draw(out)
    for i, (arr, lab) in enumerate(((a, 'naive'), (b, 'LOD'))):
        y0 = i*(H+4)
        dark = (BG-arr.mean(axis=1))/BG      # ink per row
        xs0 = W+8; wmax = PW-16
        d.rectangle([xs0, y0, xs0+wmax, y0+H-1], outline=200)
        pts = [(xs0+min(1, v/0.5)*wmax, y0+r) for r, v in enumerate(dark)]
        d.line(pts, fill=0, width=1)
        d.line([(xs0, y0+HOR), (xs0+wmax, y0+HOR)], fill=170)
        d.text((xs0+4, y0+4), lab+': ink / row', font=FONT, fill=0)
        d.text((xs0+4, y0+H-14), '0 ... 50%', font=FONT, fill=90)
    d.text((6, 4), 'blurred', font=FONT, fill=0)
    return out, [(BG-a.mean(axis=1))/BG, (BG-b.mean(axis=1))/BG]

# ---------------------------------------------------------------- legend
def levels_strip():
    cw, ch = 100, 150
    names = ['L0 full', 'L1 simple', 'L2 triangle', 'L3 mark', 'L4 merged']
    rule = ['h >= 70 px', '35-70 px', '17-35 px', '9-17 px', '< 9 px']
    desc = ['tiers, trunk, hatch,\nhatched shadow', 'triangle, 4 hatches,\n1-stroke shadow',
            'outline only,\nfaint shadow', 'two strokes,\nno shadow', 'one ragged line\nper clump']
    im = Image.new('L', (cw*5, ch+150), 255)
    R = random.Random(2)
    for i in range(5):
        cv = Cv(cw, ch)
        if i < 4:
            lv = i; g, w = PAR[lv]
            hh = 104 if lv < 3 else 70
            draw_tree(cv, 42, 126, hh, lv, g, w, rng=R)
        else:
            pts = []
            for j in range(34):
                xx = 8+j*2.6; pts.append((xx, 116+3*math.sin(j*1.3)+(-2 if j % 2 else 2)+ 4*math.sin(j*0.2)))
            cv.fill(pts+[(pts[-1][0], 128), (8, 128)])
            cv.line(pts, 0.7, 90)
        im.paste(cv.out(), (i*cw, 0))
        # true size row
        cv2 = Cv(cw, 60)
        hs = [90, 45, 22, 11, 0][i]
        if i < 4:
            draw_tree(cv2, 40, 56, hs, i, PAR[i][0], PAR[i][1], rng=R)
        else:
            pts = [(8+j*2.6, 50+(-1 if j % 2 else 1)*0.8) for j in range(34)]
            cv2.line(pts, 0.55, 120)
        im.paste(cv2.out(), (i*cw, ch+8))
        d = ImageDraw.Draw(im)
        d.text((i*cw+4, ch+74), names[i], font=FONT, fill=0)
        d.text((i*cw+4, ch+88), rule[i], font=FONT, fill=80)
        for q, line in enumerate(desc[i].split('\n')):
            d.text((i*cw+4, ch+104+q*13), line, font=FONT, fill=80)
    return im

# ---------------------------------------------------------------- Douglas-Peucker
def dp(pts, eps):
    if len(pts) < 3: return list(pts)
    (x0, y0), (x1, y1) = pts[0], pts[-1]
    dx, dy = x1-x0, y1-y0; L = math.hypot(dx, dy) or 1e-9
    best, bi = -1, 0
    for i in range(1, len(pts)-1):
        dd = abs(dy*(pts[i][0]-x0) - dx*(pts[i][1]-y0))/L
        if dd > best: best, bi = dd, i
    if best <= eps: return [pts[0], pts[-1]]
    return dp(pts[:bi+1], eps)[:-1] + dp(pts[bi:], eps)

def wiggle():
    R = random.Random(12)
    # midpoint displacement
    n = 256; y = [0.0]*(n+1); amp = 40.0
    y[0] = 6; y[n] = -8
    step = n
    while step > 1:
        for i in range(0, n, step):
            m = i+step//2
            y[m] = (y[i]+y[i+step])/2 + R.uniform(-amp, amp)
        amp *= 0.56; step //= 2
    return [(10+i*480/n, 40+v) for i, v in enumerate(y)]

def dp_fig():
    pts = wiggle()
    eps_list = [None, 1.2, 3.5, 7]
    ph = 92
    cv = Cv(W, ph*4)
    d = cv.d
    for i, e in enumerate(eps_list):
        oy = i*ph - 0
        sh = lambda p: [(x, y+oy+4) for x, y in p]
        if e is None:
            cv.line(sh(pts), 0.8, 20); s = pts; lab = 'original, %d points' % len(pts)
        else:
            s = dp(pts, e)
            cv.line(sh(pts), 0.5, 200)
            cv.line(sh(s), 1.0, 20)
            for x, y in sh(s):
                cv.d.ellipse([(x-2)*K, (y-2)*K, (x+2)*K, (y+2)*K], fill=20)
            lab = 'ε = %g px, %d points' % (e, len(s))
        if i: d.line([(0, oy*K), (W*K, oy*K)], fill=225, width=1)
    im = cv.out()
    dr = ImageDraw.Draw(im)
    for i, e in enumerate(eps_list):
        n = len(pts) if e is None else len(dp(pts, e))
        lab = 'original, %d points' % n if e is None else 'ε = %g px, %d points' % (e, n)
        dr.text((8, i*ph+6), lab, font=FONT, fill=0)
    return im

if __name__ == '__main__':
    trees = scene()
    print('trees', len(trees), 'near', sum(1 for z, x in trees if HF/z >= LEV[0]), 'merged', sum(1 for z, x in trees if HF/z < LEV[3]))
    a = render(True, trees); a.save(O+'trees_naive.png')
    b = render(False, trees); b.save(O+'trees_lod.png')
    t, prof = tone(a, b); t.save(O+'trees_tone.png')
    for nm, p in zip(('naive', 'lod'), prof):
        print(nm, 'ink/row near horizon %.3f mid %.3f near %.3f' % (p[HOR+3:HOR+15].mean(), p[HOR+30:HOR+60].mean(), p[HOR+100:].mean()))
    levels_strip().save(O+'trees_levels.png')
    dp_fig().save(O+'dp.png')

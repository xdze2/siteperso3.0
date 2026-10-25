# black line / white line: constant pen width, tone by spacing, inversion past 50% ink
from common import *
SS = 3
WPX = 1.4 * SS          # pen width, supersampled px
P = 8 * WPX             # base spacing -> 1/8 ink
# ink coverage: black lines at spacing P, P/2, P/4 (nested: entre-taille), then white lines
LEVELS = [0, 1/8, 1/4, 1/2, 3/4, 7/8, 1]
NEST = {1/8: 0, 1/4: 1, 1/2: 2, 3/4: 1, 7/8: 0}

def screen(U, t, invert=True):
    """U: field in px whose level sets are the lines, t: darkness 0..1"""
    if not invert:
        t = np.minimum(t, 0.5)      # one pen, black lines only: stuck at 50%
    lev = np.abs(t[..., None] - np.array(LEVELS)).argmin(-1)
    out = np.zeros(U.shape, bool)
    for i, c in enumerate(LEVELS):
        m = lev == i
        if c in (0, 1):
            out[m] = c == 1
            continue
        sp = P / 2 ** NEST[c]
        ph = U / sp
        line = np.abs(ph - np.round(ph)) * sp < WPX / 2
        out[m] = ~line[m] if c > 0.5 else line[m]
    return out

def to_img(ink):
    return downscale(Image.fromarray(np.where(ink, 0, 255).astype(np.uint8)), SS)

# ---- ramp: black lines only / with inversion ----
rh, rw = 50, 500
Y, X = np.mgrid[0:rh * SS, 0:rw * SS].astype(np.float32)
U = (X + Y) / math.sqrt(2)
t = np.floor(X / (rw * SS) * 7) / 6          # 7 steps, white -> black
img = Image.new('L', (rw, 2 * rh + 8), 255)
for row, inv in enumerate([False, True]):
    img.paste(to_img(screen(U, t, inv)), (0, row * (rh + 8)))
save(img, 'hatch_invert_ramp.png')

# ---- scene: lines along the form (same fields as hatch_engrave) ----
def up_(a): return up(a, SS)
Oid = np.array(Image.fromarray(oid).resize((W * SS, H * SS), Image.NEAREST))
N3 = [up_(nrm[..., i]) for i in range(3)]
Tn = up_(np.where(oid == 3, 0, dark))
a = np.array([0.45, 1.0, 0.15]); a /= np.linalg.norm(a)
sph, tor, gr = Oid == 1, Oid == 2, Oid == 0
uu = np.zeros_like(Tn)
uu[sph] = (N3[0] * a[0] + N3[1] * a[1] + N3[2] * a[2])[sph]
uu[tor] = N3[1][tor]
yy = np.mgrid[0:H * SS, 0:W * SS][0].astype(np.float32) / SS
uu[gr] = np.sqrt(np.maximum(yy - 105, 0.01))[gr]
# u -> px: divide by a smoothed |grad u| per object (lines stay continuous, width ~constant)
gy, gx = np.gradient(uu)
g = np.hypot(gx, gy)
gs = np.zeros_like(g)
for m in (sph, tor, gr):
    med = np.median(g[m])
    gm = np.where(m & (g < 3 * med), g, med).astype(np.float32)
    small = Image.fromarray(gm, 'F').resize((W // 12, H // 12), Image.BILINEAR)
    gs[m] = np.array(small.resize((W * SS, H * SS), Image.BILINEAR))[m]
Us = np.zeros_like(uu)
for m in (sph, tor, gr):
    Us[m] = uu[m] / np.median(gs[m])
for name, inv in [('hatch_invert_off.png', False), ('hatch_invert_on.png', True)]:
    save(to_img(screen(Us, Tn, inv) & (Oid != 3)), name)

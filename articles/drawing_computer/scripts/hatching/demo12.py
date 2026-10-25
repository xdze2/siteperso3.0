from common import *
SS = 3

def lineset(size, dark_fn, theta, period, width, thr):
    """pixel-field line family at angle theta, ink where dark>thr"""
    w_, h_ = size
    Y, X = np.mgrid[0:h_ * SS, 0:w_ * SS].astype(np.float32) / SS
    th = math.radians(theta)
    u = X * math.cos(th) + Y * math.sin(th)
    f = np.mod(u, period)
    near = np.minimum(f, period - f) < width / 2
    return near & (dark_fn > thr)

# ---- demo 1: ramp ----
ramp = 1 - np.array(Image.open(SC + 'ramp.png').convert('L'), np.float32) / 255
rh = 56
img = Image.new('L', (500, 3 * rh + 2 * 6), 255)
# A: spacing
A = Image.new('L', (500 * SS, rh * SS), 255); d = ImageDraw.Draw(A)
x = 3.0
while x < 500:
    dk = ramp[0, int(x)]
    if dk > 0.04:
        d.line([(x * SS, 0), (x * SS, rh * SS)], fill=0, width=int(1.2 * SS))
    s = 14 * (1 - dk) + 3.2 * dk
    x += s if dk > 0.04 else 2
img.paste(downscale(A, SS), (0, 0))
# B: width
Dk = up(np.repeat(ramp[:1], rh, 0), SS)
Y, X = np.mgrid[0:rh * SS, 0:500 * SS].astype(np.float32) / SS
p = 6.0
f = np.mod(X, p) - p / 2
ink = np.abs(f) < (np.clip(Dk * 0.92, 0, 1) * p / 2)
B = Image.fromarray(np.where(ink, 0, 255).astype(np.uint8))
img.paste(downscale(B, SS), (0, rh + 6))
# C: layers
size = (500, rh)
ink = np.zeros((rh * SS, 500 * SS), bool)
for th, thr in [(45, 0.06), (105, 0.3), (15, 0.55), (75, 0.8)]:
    ink |= lineset(size, Dk, th, 6.0, 1.2, thr)
C = Image.fromarray(np.where(ink, 0, 255).astype(np.uint8))
img.paste(downscale(C, SS), (0, 2 * (rh + 6)))
save(img, 'hatch_ramp.png')

# ---- demo 2: threshold layers on scene ----
size = (W, H)
Dk = up(dark ** 1.8, SS)
ink = np.zeros((H * SS, W * SS), bool)
for th, thr in [(45, 0.08), (105, 0.22), (15, 0.38), (75, 0.55)]:
    ink |= lineset(size, Dk, th, 5.5, 1.1, thr)
img = Image.fromarray(np.where(ink, 0, 255).astype(np.uint8))
save(downscale(img, SS), 'hatch_layers.png')

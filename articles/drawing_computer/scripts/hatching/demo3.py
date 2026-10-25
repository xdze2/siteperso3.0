from common import *
import os; HERE = os.path.dirname(os.path.abspath(__file__))
import pickle
SS = 3
tone = np.where(oid > 0, np.clip(0.05 + 0.95 * dark ** 0.9, 0, 1), dark ** 1.7)
tone[oid == 3] = 0

def dsep_from(t, tmin=0.1, smin=3.6, smax=13.0):
    ds = smax - (smax - smin) * np.clip((t - tmin) / (1 - tmin), 0, 1)
    ds = np.where(t < tmin, np.inf, ds)
    return ds.astype(np.float32)

region_all = oid != 3
ds1 = dsep_from(tone)
# first family: along field, per object so lines stop at the contours
L1 = []
for k in (0, 1, 2):
    reg = oid == k
    L1 += streamlines(reg, ds1, Fx, Fy, seed=k + 1)
print('family 1', len(L1))
# second family (contre-taille), perpendicular, only the darkest
ds2 = dsep_from(tone, tmin=0.3, smin=5.0, smax=10.0)
c, sn = math.cos(math.radians(55)), math.sin(math.radians(55))
Gx, Gy = c * Fx - sn * Fy, sn * Fx + c * Fy
obj = (oid > 0)
Gx = np.where(obj, -Fy, Gx); Gy = np.where(obj, Fx, Gy)
L2 = []
for k in (0, 1, 2):
    reg = oid == k
    L2 += streamlines(reg, ds2, Gx, Gy, seed=k + 10)
print('family 2', len(L2))
pickle.dump((L1, L2), open(os.path.join(HERE, 'lines.pkl'), 'wb'))
save(draw_lines(L1 + L2, (W, H), SS, 1.1), 'hatch_flow.png')
save(draw_lines(L1, (W, H), SS, 1.1), 'hatch_flow1.png')

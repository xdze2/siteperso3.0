# external views of the parallel pictures (section 2): isometric, oblique.
# Output: ../images/ext_*.png
import sys
import numpy as np
import render as R
from extview import Ext, rays_at, corners, look_at, SHEET, SHEET_HID

W, H = 700, 380
EW, EH = 360, 250


def view(name, args, ext_eye, ext_target, ext_fov=55, s=35, nx=5, ny=3, k=1.0):
    S = R.street()
    ey, ep = look_at(ext_eye, ext_target)
    ext = Ext(EW, EH, ext_eye, ey, ep, ext_fov, S)
    a = H / W
    uv = [(u, v) for v in np.linspace(a, -a, ny) for u in np.linspace(-1, 1, nx)]
    O, D = rays_at(R.parallel, args, uv + [(-1, a), (1, a), (1, -a), (-1, -a)])
    O = O + (200 * k - s) * D   # k = norm of the raw direction
    ext.rays(O[:-4], D[:-4])
    ext.polyline(list(O[-4:]) + [O[-4]], col=SHEET, hid=SHEET_HID, width=1)
    ext.save(name)


todo = {
    'iso': lambda: view('ext_iso.png', (W, H, np.array([0, 0, 18.0]), 45, -35.26, 22),
                        (-79, 34, 26), (-5, 6, 8), 60),
    'obl': lambda: view('ext_oblique.png', (W, H, np.array([0, 3, 18.0]), 0, 0, 22, (0.5, -0.4)),
                        (70, 30, -35), (-8, 8, 2), 62, s=60, k=1.375),
}

if __name__ == '__main__':
    for k in (sys.argv[1:] or todo):
        todo[k]()

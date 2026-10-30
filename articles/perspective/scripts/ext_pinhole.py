# external views of the pinhole pictures (section 1): 1, 2, 3 points, wide angle.
# Output: ../images/ext_*.png
import sys
import numpy as np
import render as R
from extview import Ext, rays_at, corners, pinhole_sheet, look_at

W, H = 700, 380          # size of the pictures in render.py
EW, EH = 360, 250        # size of the external views


def view(name, C, yaw, pitch, hfov, ext_eye, ext_target, ext_fov=55, dist=3.0, n=3, maxlen=28):
    S = R.street()
    ey, ep = look_at(ext_eye, ext_target)
    ext = Ext(EW, EH, ext_eye, ey, ep, ext_fov, S)
    O, D = rays_at(R.pinhole, (W, H, np.array(C, float), yaw, pitch, hfov), corners(W, H, n))
    ext.rays(O, D, maxlen=maxlen)
    pinhole_sheet(ext, C, yaw, pitch, hfov, W, H, dist)
    ext.dot(C)
    ext.save(name)


todo = {
    'p1': lambda: view('ext_1pt.png', (0, 1.6, -4.0), 0, 0, 80, (-16, 16, -22), (0, 2, 10)),
    'p2': lambda: view('ext_2pt.png', (-15, 1.6, -9.0), 33, 0, 70, (-34, 18, -24), (-4, 2, 8)),
    'p3': lambda: view('ext_3pt.png', (-22, 22, -14.0), 34, -30, 75, (-62, 24, -4), (-8, 9, 6), ext_fov=70, dist=6.0, maxlen=40),
    'wide': lambda: view('ext_wide.png', (0, 1.6, 6.0), 0, 0, 150, (-12, 17, -10), (0, 1, 12), dist=1.0, n=5),
}

if __name__ == '__main__':
    for k in (sys.argv[1:] or todo):
        todo[k]()

# external views of the curved-sheet pictures (section 2): cylinder, fisheye, equirectangular.
# The sheet is drawn as lines of constant (u, v) pushed through the camera function itself.
# Output: ../images/ext_*.png
import sys
import numpy as np
import render as R
from extview import Ext, rays_at, look_at

EW, EH = 360, 250


def curve(cam, args, uv, rad):
    O, D = rays_at(cam, args, uv)
    return O + rad * D


def view(name, cam, args, C, sheet, rays, ext_eye, ext_target, rad=2.5, ext_fov=55, maxlen=45):
    """sheet: list of (u, v) polylines in picture coords; rays: list of (u, v)"""
    S = R.street()
    ey, ep = look_at(ext_eye, ext_target)
    ext = Ext(EW, EH, ext_eye, ey, ep, ext_fov, S)
    O, D = rays_at(cam, args, rays)
    ext.rays(O, D, maxlen=maxlen)
    for c in sheet:
        ext.polyline(curve(cam, args, c, rad), col=(30, 30, 30), hid=(175, 175, 175), width=1, n=1)
    ext.dot(C)
    ext.save(name)


def line(a, b, n=40):
    return [(a[0] + (b[0] - a[0]) * s, a[1] + (b[1] - a[1]) * s) for s in np.linspace(0, 1, n)]


def circle(rho, a0=0, a1=2 * np.pi, n=80):
    return [(rho * np.cos(t), rho * np.sin(t)) for t in np.linspace(a0, a1, n)]


def cylinder():
    C = np.array([0, 1.6, 6.0]); a = 0.543
    sheet = [line((-1, a), (1, a)), line((-1, -a), (1, -a))]
    sheet += [line((u, -a), (u, a), 2) for u in np.linspace(-1, 1, 7)]
    sheet += [line((-1, 0), (1, 0))]
    rays = [(u, v) for u in np.linspace(-1, 1, 7) for v in (0, a)] + [(u, -a) for u in (-1, 0, 1)]
    view('ext_cylinder.png', R.cylindrical, (700, 380, C, 0, 220), C, sheet, rays,
         (-6, 15, -2), (0, 2, 7), rad=4, maxlen=12, ext_fov=45)


def disc_sheet():
    s = [circle(r) for r in (0.33, 0.66, 1.0)]
    s += [line((0, 0), (np.cos(t), np.sin(t)), 30) for t in np.linspace(0, 2 * np.pi, 9)[:-1]]
    return s


def disc_rays():
    return [(0, 0)] + [(r * np.cos(t), r * np.sin(t)) for r in (0.5, 1.0) for t in np.linspace(0, 2 * np.pi, 9)[:-1]]


def fisheye():
    C = np.array([0, 1.6, 6.0])
    view('ext_fisheye.png', R.fisheye, (460, 460, C, 0, 0, 180), C, disc_sheet(), disc_rays(),
         (-6, 15, -2), (0, 2, 7), rad=4, maxlen=12, ext_fov=45)


def fisheye_up():
    C = np.array([0, 1.6, 14.0])
    view('ext_fisheye_up.png', R.fisheye, (460, 460, C, 0, 90, 180), C, disc_sheet(), disc_rays(),
         (-12, 12, 5), (0, 5, 14), rad=5, maxlen=9, ext_fov=45)


def equirect():
    C = np.array([0, 1.6, 14.0]); a = 0.5
    sheet = [line((-1, v), (1, v), 100) for v in (-0.25, 0, 0.25)]
    sheet += [line((u, -a), (u, a), 40) for u in np.linspace(-1, 1, 9)]
    rays = [(u, v) for u in np.linspace(-1, 1, 9)[:-1] for v in (0, 0.25, -0.25)]
    view('ext_equirect.png', R.equirect, (700, 350, C, 0), C, sheet, rays,
         (-12, 14, 6), (0, 2, 14), rad=5, maxlen=9, ext_fov=45)


todo = {'cyl': cylinder, 'fish': fisheye, 'fishup': fisheye_up, 'equi': equirect}

if __name__ == '__main__':
    for k in (sys.argv[1:] or todo):
        todo[k]()

# external views: the scene seen from outside, with the camera of a picture drawn in it:
# the eye, the sheet, and a few of its rays in red. Hidden parts of the red lines are faint.
# The scene itself is ray-traced with render.py (same tracer), then faded.
import math
import numpy as np
from PIL import Image, ImageDraw
import render as R

RED = (200, 20, 10)
RED_HID = (235, 165, 155)
SHEET = (30, 30, 30)
SHEET_HID = (175, 175, 175)


def rays_at(cam, args, uv):
    """the actual rays of a camera function at image coords uv = [(u, v), ...].
    u in [-1, 1] across the picture, v on the same scale (v = +-H/W at top/bottom)."""
    uv = np.array(uv, float)
    R.UV = (uv[:, 0], uv[:, 1])
    try:
        O, D, _ = cam(*args)
    finally:
        R.UV = None
    D = D / np.linalg.norm(D, axis=1, keepdims=True)
    return O, D


def corners(W, H, n=3):
    """n x n points over the picture, edges included, as (u, v)"""
    a = H / W
    return [(u, v) for v in np.linspace(a, -a, n) for u in np.linspace(-1, 1, n)]


class Ext:
    """a pinhole outside the scene. W, H final pixels."""

    def __init__(self, W, H, C, yaw, pitch, hfov, boxes, fade=0.5, **shade_kw):
        self.W, self.H, self.C = W, H, np.array(C, float)
        self.f, self.r, self.up = R.frame(yaw, pitch)
        self.k = math.tan(math.radians(hfov) / 2)
        self.boxes = boxes
        O, D, _ = R.pinhole(W, H, self.C, yaw, pitch, hfov)
        D = D / np.linalg.norm(D, axis=1, keepdims=True)
        key, P, t = R.trace_straight(O, D, boxes)
        S = R.SS
        g = R.shade(key, P, t, (H * S, W * S), **shade_kw)
        g = 255 - (255 - g) * fade
        self.t = t.reshape(H * S, W * S)
        self.im = Image.fromarray(np.clip(g, 0, 255).astype(np.uint8)).convert('RGB')
        self.d = ImageDraw.Draw(self.im)

    def project(self, X):
        """world points (N, 3) -> pixel x, y (SS resolution), distance, in front"""
        X = np.atleast_2d(X) - self.C
        z = X @ self.f
        u = (X @ self.r) / np.where(z > 1e-6, z, 1e-6) / self.k
        v = (X @ self.up) / np.where(z > 1e-6, z, 1e-6) / self.k
        w, h = self.W * R.SS, self.H * R.SS
        return (u + 1) / 2 * w, h / 2 - v * w / 2, np.linalg.norm(X, axis=1), z > 1e-3

    def visible(self, X):
        x, y, dist, front = self.project(X)
        h, w = self.t.shape
        xi = np.clip(x.astype(int), 0, w - 1); yi = np.clip(y.astype(int), 0, h - 1)
        return front & (dist < self.t[yi, xi] * 1.02 + 0.05)

    def polyline(self, pts, col=RED, hid=RED_HID, width=1.5, n=None):
        """3D polyline, each piece sampled finely and drawn visible / hidden"""
        pts = np.asarray(pts, float)
        if n is None:
            n = 60
        fine = [pts[0]]
        for a, b in zip(pts[:-1], pts[1:]):
            s = np.linspace(0, 1, n + 1)[1:, None]
            fine.extend(a + (b - a) * s)
        fine = np.array(fine)
        x, y, _, front = self.project(fine)
        vis = self.visible(fine)
        lw = max(1, int(round(width * R.SS)))
        for i in range(len(fine) - 1):
            if not (front[i] and front[i + 1]):
                continue
            c, wd = (col, lw) if (vis[i] and vis[i + 1]) else (hid, max(1, lw // 2))
            if c is None:
                continue
            self.d.line([(x[i], y[i]), (x[i + 1], y[i + 1])], fill=c, width=wd)

    def segment(self, A, B, **kw):
        self.polyline([A, B], **kw)

    def dot(self, X, rad=3.5, col=RED):
        x, y, _, front = self.project(np.array(X, float))
        if front[0]:
            r = rad * R.SS
            self.d.ellipse([x[0] - r, y[0] - r, x[0] + r, y[0] + r], fill=col)

    def rays(self, O, D, maxlen=45, **kw):
        """draw rays from their origin to the first hit (or maxlen into the sky)"""
        t, _ = R.hit_boxes(O, D, self.boxes, maxlen)
        for o, d, tt in zip(O, D, t):
            self.segment(o, o + d * tt, **kw)
        return O + D * t[:, None]

    def sheet_plane(self, c, a, b, **kw):
        """rectangle centred on c, half-sides a and b (vectors)"""
        c, a, b = (np.array(v, float) for v in (c, a, b))
        kw.setdefault('col', SHEET); kw.setdefault('hid', SHEET_HID); kw.setdefault('width', 1)
        self.polyline([c - a - b, c + a - b, c + a + b, c - a + b, c - a - b], **kw)

    def save(self, name):
        im = self.im.resize((self.W, self.H), Image.LANCZOS)
        im.save(R.OUT + name)
        print('saved', name, im.size)


def pinhole_sheet(ext, C, yaw, pitch, hfov, W, H, dist):
    """draw the picture plane of a pinhole camera at distance dist from the eye"""
    f, r, up = R.frame(yaw, pitch)
    k = math.tan(math.radians(hfov) / 2) * dist
    ext.sheet_plane(np.array(C) + dist * f, k * r, k * H / W * up)


def look_at(C, T):
    """yaw, pitch (degrees) of the eye C looking at the point T, for R.frame"""
    d = np.array(T, float) - np.array(C, float)
    return math.degrees(math.atan2(d[0], d[2])), math.degrees(math.atan2(d[1], math.hypot(d[0], d[2])))

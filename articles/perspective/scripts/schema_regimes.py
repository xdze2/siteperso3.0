"""Schema: one box seen from a fixed direction, at several distances.

A: side view. Eye looking down at ALPHA, the same box at three distances
   along the line of sight.
B: r = apparent height of the top face / of the front face, against
   a/d (box size over distance). Far: constant (parallel projection).
   Closer: linear in a/d. Very close: curved. Above the graph, what the eye
   sees at some of those distances.
Output: ../images/schema_regimes.svg (+ .png via inkscape)
"""
import os, subprocess
from math import cos, sin, tan, radians

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "images", "schema_regimes.svg")

W, H = 680, 800
RED, BLUE, GREY = "#d40000", "#1d3d6b", "#888"
ALPHA = radians(30)
CA, SA = cos(ALPHA), sin(ALPHA)

out = []
def svg(s): out.append(s)
def text(x, y, s, col="#000", anchor="start", size=13):
    svg(f'<text x="{x:.1f}" y="{y:.1f}" fill="{col}" text-anchor="{anchor}" font-size="{size}">{s}</text>')
def line(x1, y1, x2, y2, col="#000", w=1.0, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    svg(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{col}" stroke-width="{w}"{d}/>')
def poly(pts, fill="#eee", col="#000", w=1.3):
    p = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    svg(f'<polygon points="{p}" fill="{fill}" stroke="{col}" stroke-width="{w}"/>')


# --- the camera: eye at 0, looking along (cos a, -sin a) in (Z, Y) ------------
# a cube of size 1, centred on the line of sight at distance d.
def view(d, p):
    """p = (X, Y, Z) relative to the box centre -> (u, v) on the window, f = 1."""
    X, Y, Z = p
    Zw, Yw = d * CA + Z, -d * SA + Y
    depth = Zw * CA - Yw * SA
    up = Zw * SA + Yw * CA
    return X / depth, up / depth

FT = [(-.5, .5, -.5), (.5, .5, -.5)]          # front top edge
FB = [(.5, -.5, -.5), (-.5, -.5, -.5)]        # front bottom edge
BT = [(.5, .5, .5), (-.5, .5, .5)]            # back top edge

def ratio(d):
    v = lambda p: view(d, p)[1]
    return (v(BT[0]) - v(FT[0])) / (v(FT[0]) - v(FB[0]))

R_INF = tan(ALPHA)                             # cube: D/H = 1
K = (cos(2 * ALPHA) / 2) * (1 / SA + 1 / CA)   # r ~ R_INF (1 - K a/d)


# --- A. side view ---------------------------------------------------------------
text(20, 26, "A. One box, one direction (30&#176; down), three distances.")
text(20, 43, "eye aimed at the box. rays to the front face (red), to the back of the top (blue).", GREY, size=12)
EX, EY, U = 500, 70, 34        # eye on the page, px per box size
def side(z, y): return EX - z * U, EY - y * U          # world (Z, Y) -> page
line(*side(0, 0), *side(8.5 * CA, -8.5 * SA), "#aaa", 1, "4 4")
svg(f'<ellipse cx="{EX}" cy="{EY}" rx="3" ry="6" fill="#fff" stroke="#000" stroke-width="1.5"/>')
text(EX - 10, EY - 10, "eye", anchor="end", size=12)
for d, name in ((1.6, "close, d = 1.6 a"), (3.5, "d = 3.5 a"), (7.5, "far, d = 7.5 a")):
    cz, cy = d * CA, -d * SA
    x0, y0 = side(cz - .5, cy + .5)
    svg(f'<rect x="{x0 - U:.1f}" y="{y0:.1f}" width="{U}" height="{U}" fill="#eee" stroke="#000" stroke-width="1.5"/>')
    line(*side(cz + .5, cy + .5), *side(cz - .5, cy + .5), BLUE, 3)       # top face
    line(*side(cz - .5, cy + .5), *side(cz - .5, cy - .5), "#000", 3)     # front face
    for (z, y), col in (((-.5, .5), RED), ((-.5, -.5), RED), ((.5, .5), BLUE)):
        line(*side(cz + z, cy + y), EX, EY, col, 1)
    lx, ly = side(cz - .5, cy - .5)
    text(lx + 4, ly + 16, name, size=12)
text(20, 262, "far: rays to the box almost parallel = parallel projection along the line of sight.", size=12)
text(20, 278, "close: they fan out, the eye sees the top face more and more edge-on.", size=12)


# --- B. r against a/d -------------------------------------------------------------
GX0, GX1, GY0, GY1 = 60, 600, 750, 480         # plot box
E1, R1 = 1.2, 0.7
def gx(e): return GX0 + e / E1 * (GX1 - GX0)
def gy(r): return GY0 - r / R1 * (GY0 - GY1)

text(20, 320, "B. r = top face / front face, as seen, against a/d (box size / distance).")
text(20, 337, "above: what the eye sees, scaled to the same front face.", GREY, size=12)

for e0, e1, col, name in ((0, .06, "#000", "constant"), (.06, .5, BLUE, "linear"),
                          (.5, E1, RED, "curved")):
    svg(f'<rect x="{gx(e0):.1f}" y="{GY1}" width="{gx(e1) - gx(e0):.1f}" height="{GY0 - GY1}" fill="{col}" fill-opacity="0.06"/>')
    text((gx(e0) + gx(e1)) / 2, GY1 + 16, name, col, "middle", 12)

line(GX0, GY0, GX1 + 10, GY0, "#000", 1.5)
line(GX0, GY0, GX0, GY1 - 10, "#000", 1.5)
text(GX1 + 14, GY0 + 4, "a/d")
text(GX0 - 12, GY1 + 4, "r", anchor="end", size=14)
for e, dl in ((0, "&#8734;"), (.25, "4 a"), (.5, "2 a"), (.75, "1.3 a"), (1, "a")):
    line(gx(e), GY0, gx(e), GY0 + 5)
    text(gx(e), GY0 + 18, f"{e:g}", anchor="middle", size=11)
    text(gx(e), GY0 + 32, f"d = {dl}", GREY, "middle", 11)
for r in (.2, .4, .6):
    line(GX0 - 5, gy(r), GX0, gy(r))
    text(GX0 - 8, gy(r) + 4, f"{r:g}", anchor="end", size=11)

# order 0, order 1, the real curve
line(gx(0), gy(R_INF), gx(E1), gy(R_INF), "#000", 1.2, "6 4")
text(gx(.62), gy(R_INF) - 6, "order 0: r&#8734; = tan 30&#176;, parallel projection", size=12)
line(gx(0), gy(R_INF), gx(1 / K), gy(0), BLUE, 1.5)
text(gx(.98), gy(.15), "order 1: r&#8734; (1 &#8722; k a/d)", BLUE, size=12)
pts = " ".join(f"{gx(e):.1f},{gy(ratio(1 / e)):.1f}" for e in [i / 100 for i in range(1, 105)])
svg(f'<polyline points="{pts}" fill="none" stroke="{RED}" stroke-width="2.2"/>')
text(gx(.62), gy(ratio(1 / .62)) + 26, "perspective", RED, size=12)
text(gx(1), gy(0) - 8, "edge-on", RED, "middle", 11)

# what the eye sees, at a few distances
TOP = 365
for d in (1.25, 1.6, 2.5, 4, 10, 1e6):
    e = 1 / d if d < 1e5 else 0
    pv = lambda p: view(d, p)
    ft, fb, bt = [pv(p) for p in FT], [pv(p) for p in FB], [pv(p) for p in BT]
    k = 36 / (ft[0][1] - fb[0][1])        # front face 36 px high
    cx, cy0 = gx(e), TOP + 18             # cy0: front top edge
    P = lambda q: (cx + k * q[0], cy0 - k * (q[1] - ft[0][1]))
    poly([P(q) for q in ft + fb])                          # front face
    poly([P(q) for q in bt + ft], fill="#c9d3e3")    # top face
    line(cx, cy0 + 40, cx, GY1, "#ccc", 1, "2 3")

with open(OUT, "w") as f:
    f.write(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
            f'font-family="\'Liberation Mono\',\'Courier New\',monospace">'
            f'<rect width="{W}" height="{H}" fill="#fff"/>\n' + "\n".join(out) + "</svg>\n")
subprocess.run(["inkscape", OUT, "--export-type=png",
                "--export-filename=" + OUT[:-4] + ".png"], check=True,
               stderr=subprocess.DEVNULL)
print("wrote", OUT, "k =", round(K, 3))

"""Schema: crossed slits, top view and side view on the same depth axis.

A: top view (X). Rays cross at the vertical slit, close to the scene: wide.
B: side view (Y). Rays cross at the horizontal slit, far from the scene:
   narrow, the viewpoint of a long lens. Same scene, same sheet.
C: what a longer focal does alone: same crossing point, sheet further.
   Same rays, the picture is only bigger.
Output: ../images/schema_crossed_slits.svg (+ .png via inkscape)
"""
import os, subprocess
from math import atan, degrees

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "images", "schema_crossed_slits.svg")

W, H = 680, 900
RED, GREY = "#d40000", "#999"
XS, XA, XB, XF = 75, 230, 420, 560    # scene, vertical slit, horizontal slit, sheet

out = []
def svg(s): out.append(s)
def text(x, y, s, col="#000", anchor="start", size=13):
    svg(f'<text x="{x:.1f}" y="{y:.1f}" fill="{col}" text-anchor="{anchor}" font-size="{size}">{s}</text>')
def line(x1, y1, x2, y2, col="#000", w=1.0, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    svg(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{col}" stroke-width="{w}"{d}/>')
def dot(x, y, r=3.5):
    svg(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="#000"/>')
def ray(x0, y0, xc, yc, x1, col=RED, w=1.2, dash=None):
    """from (x0, y0) through (xc, yc), continued to x1"""
    s = (yc - y0) / (xc - x0)
    line(x0, y0, x1, yc + s * (x1 - xc), col, w, dash)
    return yc + s * (x1 - xc)
def image(x, y0, y1):
    line(x, y0, x, y1, RED, 4)

# alignment: the same depth in both views
for x in (XA, XB, XF):
    line(x, 40, x, 650, "#ddd", 1, "2 4")

# --- A: top view ------------------------------------------------------------
A = 205
text(W / 2, 30, "A. top view: X", anchor="middle", size=15)
for dx, dy, r in [(-8, -70, 7), (6, -42, 9), (-14, -12, 5), (2, 16, 8), (12, 44, 6), (-6, 70, 7)]:
    svg(f'<circle cx="{XS + dx}" cy="{A + dy}" r="{r}" fill="#fff" stroke="#000" stroke-width="1.2"/>')
y0 = ray(XS, A - 70, XA, A, XF)
y1 = ray(XS, A + 70, XA, A, XF)
image(XF, y0, y1)
dot(XA, A)
line(XB, A - 150, XB, A + 150, GREY, 1.5, "6 4")      # the horizontal slit, seen from above
line(XF, A - 160, XF, A + 160, "#000", 1.5)
text(XA, A + 26, "vertical slit", anchor="middle", size=12)
text(XB - 6, A + 120, "horizontal slit", GREY, "end", 12)
text(XB - 6, A + 135, "a line: every ray passes it", GREY, "end", 11)
text(XF + 8, A + 4, "sheet", size=12)
text(XA - 90, A - 95, f"wide: {2 * degrees(atan(70 / (XA - XS))):.0f}&#176;", RED, size=12)

# --- B: side view -----------------------------------------------------------
B = 520
text(W / 2, 400, "B. side view: Y, same scene, same sheet", anchor="middle", size=15)
for x0, w, h in [(-20, 14, 70), (-6, 18, 55), (10, 12, 80), (20, 16, 45)]:
    svg(f'<rect x="{XS + x0}" y="{B + 40 - h}" width="{w}" height="{h}" fill="#fff" stroke="#000" stroke-width="1.2"/>')
line(XS - 40, B + 40, XF + 40, B + 40, "#000", 1)       # ground
ray(XS, B - 40, XA, B, XA + 60, GREY, 1, "4 3")          # a pinhole at the vertical slit
ray(XS, B + 40, XA, B, XA + 60, GREY, 1, "4 3")
y0 = ray(XS, B - 40, XB, B, XF)
y1 = ray(XS, B + 40, XB, B, XF)
image(XF, y0, y1)
dot(XB, B)
line(XA, B - 110, XA, B + 30, GREY, 1.5, "6 4")         # the vertical slit, seen from the side
line(XF, B - 110, XF, B + 30, "#000", 1.5)
text(XB, B + 26, "horizontal slit", anchor="middle", size=12)
text(XA - 6, B - 95, "vertical slit", GREY, "end", 12)
text(XA + 10, B + 58, "grey: a pinhole here would see this wide", GREY, size=11)
text(XB - 60, B - 50, f"narrow: {2 * degrees(atan(40 / (XB - XS))):.0f}&#176;", RED, size=12)
text(XF + 8, B + 4, "sheet", size=12)
text(XF + 8, B + 20, "(small)", GREY, size=11)

# --- C: a longer focal alone ------------------------------------------------
C = 790
text(W / 2, 690, "C. not this: same crossing point, sheet further", anchor="middle", size=15)
for x0, w, h in [(-20, 14, 70), (-6, 18, 55), (10, 12, 80), (20, 16, 45)]:
    svg(f'<rect x="{XS + x0}" y="{C + 40 - h}" width="{w}" height="{h}" fill="#fff" stroke="#000" stroke-width="1.2"/>')
y0 = ray(XS, C - 40, XA, C, XF)
y1 = ray(XS, C + 40, XA, C, XF)
dot(XA, C)
for x in (XA + 70, XF):
    s = 40 / (XA - XS) * (x - XA)
    line(x, C - s - 12, x, C + s + 12, "#000", 1.5)
    image(x, C - s, C + s)
text(XA + 70, C + 62, "short f", anchor="middle", size=12)
text(XF + 8, C + 4, "long f", size=12)
text(20, H - 12, "same rays, same picture, only bigger: a scale, not a perspective", size=12)

with open(OUT, "w") as f:
    f.write(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
            f'font-family="\'Liberation Mono\',\'Courier New\',monospace">'
            f'<rect width="{W}" height="{H}" fill="#fff"/>\n' + "\n".join(out) + "</svg>\n")
subprocess.run(["inkscape", OUT, "--export-type=png",
                "--export-filename=" + OUT[:-4] + ".png"], check=True,
               stderr=subprocess.DEVNULL)
print("wrote", OUT)

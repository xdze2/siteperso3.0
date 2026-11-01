"""Schema: ordinary pinhole vs reverse perspective, top view.

Two equal boxes, one near the sheet, one far. Thick: the faces seen.
A: pinhole, the eye behind the sheet. Rays spread out: near is big.
B: reverse. Every point of the sheet is an eye, the rays converge on a
   point beyond the scene. Far is big, the outer sides are seen.
Output: ../images/schema_reverse.svg (+ .png via inkscape)
"""
import os, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "images", "schema_reverse.svg")

W, H = 680, 750
RED, BLUE, GREY = "#d40000", "#1d3d6b", "#999"
XF, XW, XE = 30, 520, 640          # the point beyond, the sheet, the eye (A)
BOXES = [((400, 26), RED, "near"), ((230, -22), BLUE, "far")]   # centre (depth, side)
A = 26                              # half size of a box

out = []
def svg(s): out.append(s)
def text(x, y, s, col="#000", anchor="start", size=13):
    svg(f'<text x="{x:.1f}" y="{y:.1f}" fill="{col}" text-anchor="{anchor}" font-size="{size}">{s}</text>')
def line(x1, y1, x2, y2, col="#000", w=1.0, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    svg(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{col}" stroke-width="{w}"{d}/>')
def dot(x, y, r=3.5):
    svg(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="#000"/>')


def panel(cy, title, reverse):
    """cy: the axis. reverse: rays from the sheet to (XF, cy), else from (XE, cy)."""
    text(W / 2, cy - 165, title, anchor="middle", size=15)
    line(XF - 10, cy, XE + 10, cy, "#ddd", 1, "2 4")
    line(XW, cy - 150, XW, cy + 150, "#000", 1.5)
    P = (XF, cy) if reverse else (XE, cy)

    def on_sheet(x, y):
        return cy + (y - cy) * (XW - P[0]) / (x - P[0])

    for (bx, by), col, name in BOXES:
        x0, x1, y0, y1 = bx - A, bx + A, cy + by - A, cy + by + A
        svg(f'<rect x="{x0}" y="{y0}" width="{2 * A}" height="{2 * A}" fill="#fff" stroke="#000" stroke-width="1"/>')
        # faces: (end points, outward normal)
        faces = [((x1, y0), (x1, y1), (1, 0)), ((x0, y0), (x0, y1), (-1, 0)),
                 ((x0, y0), (x1, y0), (0, -1)), ((x0, y1), (x1, y1), (0, 1))]
        for a, b, n in faces:
            mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
            s = (mx - P[0]) * n[0] + (my - P[1]) * n[1]
            if (s > 0) == reverse:
                line(a[0], a[1], b[0], b[1], col, 4)
        # silhouette: the two corners with the extreme images
        cs = sorted([(x0, y0), (x0, y1), (x1, y0), (x1, y1)], key=lambda c: on_sheet(*c))
        for c in (cs[0], cs[-1]):
            ys = on_sheet(*c)
            if reverse:
                line(XW, ys, c[0], c[1], col, 1.2)
                line(c[0], c[1], P[0], P[1], GREY, 0.8, "3 3")
            else:
                line(P[0], P[1], c[0], c[1], col, 1.2)
        y0s, y1s = on_sheet(*cs[0]), on_sheet(*cs[-1])
        line(XW, y0s, XW, y1s, col, 5)
        text(XW + 10, (y0s + y1s) / 2 + 4 + (14 if col == RED and not reverse else 0), f"{name}: {abs(y1s - y0s):.0f}", col, size=12)
        text(bx, y1 + 18, name, col, "middle", 12)
    dot(*P)


panel(195, "A. pinhole: the eye behind the sheet", False)
text(XE, 195 + 22, "eye", anchor="middle", size=12)
text(XW - 6, 195 + 145, "sheet", anchor="end", size=12)

panel(560, "B. reverse: every point of the sheet an eye", True)
text(XF, 560 + 22, "point beyond", anchor="start", size=12)
text(XF, 560 + 37, "the scene", anchor="start", size=12)
text(XW - 6, 560 + 145, "sheet = plane of eyes", anchor="end", size=12)
text(20, H - 12, "thick: the faces seen. reverse sees the outer side, and the far box bigger", size=12)

with open(OUT, "w") as f:
    f.write(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
            f'font-family="\'Liberation Mono\',\'Courier New\',monospace">'
            f'<rect width="{W}" height="{H}" fill="#fff"/>\n' + "\n".join(out) + "</svg>\n")
subprocess.run(["inkscape", OUT, "--export-type=png",
                "--export-filename=" + OUT[:-4] + ".png"], check=True,
               stderr=subprocess.DEVNULL)
print("wrote", OUT)

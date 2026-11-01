Scripts for the demo images of articles/perspective/.
python3, numpy, Pillow.

render.py    ray tracer, one street of boxes, one function per camera
             (pixel -> origin, direction). straight rays: analytic box tests.
             curved rays: marched in short segments (slow, a few minutes each).
             python3 render.py            all images
             python3 render.py p1 cyl     only some (keys in main())
normals.py   2D figure: normals of a circle, a line, an ellipse (caustic).
extview.py   outside views: the scene from elsewhere, the camera drawn in it
             (eye, sheet, its real rays in red, pale where hidden). library.
ext_pinhole.py   outside views, section 1 (ext_1pt, 2pt, 3pt, wide)
ext_curved.py    outside views, section 2 (ext_cylinder, fisheye, fisheye_up, equirect)
ext_parallel.py  outside views, iso and oblique (ext_iso, ext_oblique)
ext_bent.py      falling rays: outside view (ext_fall), the morphed world where straight
                 rays give the same picture (ext_fall_morph), and the check: morphed
                 wireframe over the curved-ray picture (persp_fall_morph).
                 caches the slow curved render in cache_fall.npz (not in git).

Output: ../images/persp_*.png, ../images/ext_*.png

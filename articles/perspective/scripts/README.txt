Scripts for the demo images of articles/perspective/.
python3, numpy, Pillow.

render.py    ray tracer, one street of boxes, one function per camera
             (pixel -> origin, direction). straight rays: analytic box tests.
             curved rays: marched in short segments (slow, a few minutes each).
             python3 render.py            all images
             python3 render.py p1 cyl     only some (keys in main())
normals.py   2D figure: normals of a circle, a line, an ellipse (caustic).

Output: ../images/persp_*.png

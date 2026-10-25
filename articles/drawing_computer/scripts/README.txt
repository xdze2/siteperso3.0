Scripts for the demo images of articles/drawing_computer/.
python3, numpy, Pillow. No scipy (convolutions etc. by hand).

make_scene.py   ray-marched test scene: sphere + torus on a ground plane.
                writes scene/ : lum, depth, normal, object id (.npy + .png), ramp.png
tone/           chapter 1: threshold, quantization, dithers, halftone, stipple
hatching/       chapter 2: common.py (direction field, streamlines), line screens,
                streamlines, dashes, engraving, spiral, LIC, wobble, inversion
lines/          chapter 3: G-buffers, Sobel, DoG/XDoG, contours, sketchy, depth rules;
                trees_lod.py: tree landscape naive vs level of detail, tone check,
                LOD legend, Douglas-Peucker (lines_trees_*.png, lines_dp.png)

perception/     chapter 4: perception.py: light from above (stipple), cast shadow ball-in-a-box,
                line direction on a vase, occlusion and T-junctions (percep_*.png).
                Self-contained (analytic), does not need scene/.

Output: ../images/, prefixed tone_, hatch_, lines_, percep_.
All at once: ./run_all.sh   (make_scene.py first if running one by one)

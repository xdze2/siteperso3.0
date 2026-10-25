#!/bin/sh
# regenerate all demo images of the course into ../images/
# python3 + numpy + Pillow, no scipy. tone/tone.py (stippling) takes a few minutes.
set -e
cd "$(dirname "$0")"
python3 make_scene.py
python3 tone/tone.py
python3 tone/tone2.py
python3 hatching/demo12.py
python3 hatching/demo3.py
python3 hatching/demo4.py
python3 hatching/demo7.py
python3 hatching/demo_inversion.py
python3 lines/gen.py
python3 lines/gen2.py
python3 lines/trees_lod.py
python3 perception/perception.py

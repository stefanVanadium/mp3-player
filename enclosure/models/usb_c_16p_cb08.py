"""3D model for TYPE-C 16P CB0.8 073 (SHOU HAN, LCSC C2906289), from the datasheet drawing.
The EasyEDA model has a short shell and legs in front of it. Checked against the KiCad STEP export:
front of the receptacle at model -Y (footprint -y), Z away from the board on the component side.
Datasheet: shell 8.34 x 2.56, 6.5 long, front 2.10 ahead of the front leg centre; the shell
sits 0.46 into the 0.8 board cutout. Run: ../.venv/bin/python usb_c_16p_cb08.py
"""
from pathlib import Path

from build123d import Box, Color, Compound, Plane, Pos, Rot, SlotCenterToCenter, export_step, extrude, mirror

OUT = Path(__file__).resolve().parents[2] / "lib" / "mp3_player.3dshapes" / "TYPE-C-16P-CB0.8-073.step"
W, H, LEN, WALL = 8.34, 2.56, 6.5, 0.25
FRONT_Y = 2.61 + 2.10          # front leg centre at model Y 2.61
Z0 = -0.545                     # shell 0.46 into the board (KiCad puts B-side models 0.085 lower)
ZC = Z0 + H / 2


def stadium(w, h, length):
    return Rot(-90, 0, 0) * extrude(SlotCenterToCenter(w - h, h), length)


shell = Pos(0, FRONT_Y - LEN, ZC) * stadium(W, H, LEN)       # stadium() extrudes toward +Y
shell -= Pos(0, FRONT_Y - LEN + 0.3, ZC) * stadium(W - 2 * WALL, H - 2 * WALL, LEN - 0.3 + 0.01)
for x in (-5.6, 5.6):
    for y in (2.61, -1.39):
        shell += Pos(x * 0.97, y, -0.2) * Box(0.3, 1.0, 1.6)                     # through-hole legs
        shell += Pos(x * 0.86, y, 0.05) * Box(abs(x) * 0.25, 1.0, 0.3)           # wing to the shell
tongue = Pos(0, FRONT_Y - 0.6 - (LEN - 1.0) / 2, ZC) * Box(6.69, LEN - 1.0, 0.7)
tongue += Pos(0, FRONT_Y - LEN + 0.2, ZC) * Box(W - 2 * WALL, 0.4, H - 2 * WALL)
pins = None
for i in range(16):
    x = -3.21 + i * (6.42 / 15)
    p = Pos(x, -2.61, 0.05) * Box(0.22, 1.2, 0.1)
    pins = p if pins is None else pins + p
# built with the front at +Y; on this footprint the front is at model -Y
shell, tongue, pins = (mirror(s, about=Plane.XZ) for s in (shell, tongue, pins))
shell.label, shell.color = "shell", Color(0.78, 0.78, 0.8)
tongue.label, tongue.color = "tongue", Color(0.08, 0.08, 0.08)
pins.label, pins.color = "pins", Color(0.85, 0.7, 0.35)
OUT.parent.mkdir(parents=True, exist_ok=True)
export_step(Compound(children=[shell, tongue, pins], label="TYPE-C-16P-CB0.8-073"), OUT)
print(OUT)

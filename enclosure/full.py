"""Full 3D model: the enclosure parts + the real board (out/pcb.step from kicad-cli).
Run: .venv/bin/python full.py  ->  out/mp3_player_full.step
"""
from pathlib import Path

from build123d import Compound, Pos, export_step, import_step

import case

HERE = Path(__file__).parent

pcb = import_step(HERE / "out" / "pcb.step")
pcb = Pos(-149.1, case.Y0B, case.PCB_Z) * pcb
pcb.label = "PCB (mp3_player.kicad_pcb)"
parts = [p[0] for p in case.build()]
full = Compound(children=parts + [pcb], label="mp3_player")
export_step(full, HERE / "out" / "mp3_player_full.step")
print("out/mp3_player_full.step")

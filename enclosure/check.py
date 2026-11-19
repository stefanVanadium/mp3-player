"""Collision check: every enclosure part against the real board (out/pcb.step).

Reports pairs closer than MIN_GAP (overlaps show as distance 0). Board parts are named
by the footprint whose courtyard holds the solid's centre (pcbnew).
Run: .venv/bin/python check.py
"""

import json
import os
import subprocess
import sys
from pathlib import Path

from build123d import Pos, import_step

import case

HERE = Path(__file__).parent
MIN_GAP = 0.04
KICAD = "/mnt/storage/vana/claude_skills/repos/kicad/bin/kicad-cli"
FP_SCRIPT = """
import pcbnew, json
b = pcbnew.LoadBoard('%s')
out = []
for f in b.GetFootprints():
    bb = f.GetBoundingBox(False)
    out.append([f.GetReference(), pcbnew.ToMM(bb.GetLeft()), pcbnew.ToMM(bb.GetTop()),
                pcbnew.ToMM(bb.GetRight()), pcbnew.ToMM(bb.GetBottom())])
print(json.dumps(out))
"""


def footprints():
    pcb = (HERE.parent / "mp3_player.kicad_pcb").resolve()
    script = HERE / "out" / "_fp.py"
    script.write_text(FP_SCRIPT % pcb)
    r = subprocess.run([KICAD, str(script)], env=dict(os.environ, KICAD_PY="1"),
                       capture_output=True, text=True)
    script.unlink()
    return json.loads(r.stdout.strip().splitlines()[-1])


def owner(fps, s):
    bb = s.bounding_box()
    cx, cy = (bb.min.X + bb.max.X) / 2 + 149.1, case.Y0B - (bb.min.Y + bb.max.Y) / 2
    for ref, x0, y0, x1, y1 in fps:
        if x0 - 0.2 <= cx <= x1 + 0.2 and y0 - 0.2 <= cy <= y1 + 0.2:
            return ref
    return "board"


def main():
    pcb = Pos(-149.1, case.Y0B, case.PCB_Z) * import_step(HERE / "out" / "pcb.step")
    board_solids = [s for s in pcb.solids()]
    fps = footprints()
    parts = case.build()
    bad = 0
    for shape, label, _ in parts:
        if label.startswith(("engraving",)):
            continue
        pb = shape.bounding_box()
        hits = {}
        for s in board_solids:
            sb = s.bounding_box()
            if (sb.min.X > pb.max.X + MIN_GAP or sb.max.X < pb.min.X - MIN_GAP or
                    sb.min.Y > pb.max.Y + MIN_GAP or sb.max.Y < pb.min.Y - MIN_GAP or
                    sb.min.Z > pb.max.Z + MIN_GAP or sb.max.Z < pb.min.Z - MIN_GAP):
                continue
            # the board itself (substrate, copper, mask, silk) may touch the lugs, ledges
            # and the cap clamp: those are the supports
            if sb.min.Z > case.PCB_Z - 0.06 and sb.max.Z < case.PCB_TOP + 0.06 and sb.size.X * sb.size.Y > 20:
                continue
            d = shape.distance_to(s)
            if d < MIN_GAP:
                ref = owner(fps, s)
                if d < hits.get(ref, (9,))[0]:
                    p = shape.closest_points(s)[0]
                    hits[ref] = (d, f"({p.X:.1f},{p.Y:.1f},{p.Z:.2f})")
        if hits:
            bad += 1
            print(f"{label}: " + ", ".join(f"{r} {d:.3f} at {p}" for r, (d, p) in sorted(hits.items())))
    # enclosure parts against each other (moving parts need a gap)
    for i, (a, la, _) in enumerate(parts):
        for b, lb, _ in parts[i + 1:]:
            if "engraving" in (la + lb) or "gasket" in (la + lb):
                continue
            d = a.distance_to(b)
            if d < 0.02 and not ({la.split()[0], lb.split()[0]} <= {"body", "back", "screw", "cover", "antenna"}):
                print(f"{la} <-> {lb}: {d:.3f}")
    print("OK" if bad == 0 else f"{bad} part(s) too close to the board")
    return bad


if __name__ == "__main__":
    sys.exit(1 if main() else 0)

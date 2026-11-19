"""Final enclosure for the MP3 player (variant B, milled unibody).

Body: one 6061 tub, milled from the back. Front, sides and both ends in one piece; the
top end is left open and closed by the 3D printed antenna cap, which slides on like a pen
cap. The back is a 0.7 mm aluminium plate (1.0 mm at the two screw pads), held by two
M1.6 countersunk Torx screws in the bottom corners and, at the top, by a pin that drops
into the cap's tab.

Axes (same as concept.py): X = width (centred on the board centre line, board x 149.1),
Y = length (0 = outer bottom face with USB-C + jack), Z = thickness (0 = back face,
T = front face with the display and the click wheel).

Board -> enclosure: x_e = x_b - 149.1, y_e = 155.9 - y_b, z_e = z_step + 5.0
(board back face at z 5.0, board outline 130..168.2 x 55.4..155.0).

Run: .venv/bin/python case.py  ->  out/case_*.step / .stl / .glb
"""

import math
import re
from pathlib import Path

from build123d import (
    Axis, Box, Color, Compound, Cone, Cylinder, Face, Plane, Pos, RectangleRounded, Rot,
    SlotCenterToCenter, Text, Vector, Wire, chamfer, export_gltf, export_step, export_stl,
    extrude, fillet, mirror,
)
from shapely.geometry import LineString, Polygon as SPolygon
from shapely.ops import unary_union

HERE = Path(__file__).parent
OUT = HERE / "out"
LOGO_SVG = Path.home() / "Documents/logo-vanadium/final/vanadium-logo-mono-negru.svg"
FONT = str(Path.home() / ".local/share/fonts/Inter/InterVariable.ttf")

# --- outer shape -------------------------------------------------------------------
W, T = 41.0, 8.0
CORNER_R = 5.0          # plan view
FRONT_CHAMFER = 0.3     # polished diamond cut on the front edge
BACK_R = 0.5            # back edge rounding
WALL_SIDE, WALL_END, WALL_FRONT = 1.2, 1.2, 0.8
# Bottom end: thinner wall and a smaller gap to the board, so the USB-C and jack faces
# (both flush with the board edge) sit only 0.9 mm behind the outer face
BOTTOM_WALL, BOTTOM_GAP = 0.8, 0.1
BOARD_L = 99.6
L = BOTTOM_WALL + BOTTOM_GAP + BOARD_L + 0.2 + WALL_END   # 101.9
CAP_H = 9.0             # plastic antenna cap at the top end
SPLIT_Y = L - CAP_H     # 93.4, body / cap joint

# --- back plate -----------------------------------------------------------------------
PLATE_T = 0.7
PAD_T = 1.1             # plate inner face at the screw pads (1.0 thick + gasket under the rim)
PLATE_RIM = 0.6         # body rim left around the plate
PLATE_GAP = 0.05
GASKET = 0.1            # die-cut adhesive gasket on the 0.6 mm ledge: dust / splash seal
REBATE = PLATE_T + GASKET
# M1.6 countersunk Torx, 3.0 mm in from the sides: back parts within r 1.9 of these points
# are <= 0.43 mm tall, so the bosses stop 0.58 mm under the board (3.3 mm of thread)
SCREWS = [(-16.0, 9.0), (16.0, 9.0)]
BOSS_R = 1.9
BOSS_TOP = 5.0 - 0.43 - 0.15
TAP_D = 1.25            # M1.6 tap drill
SCREW_CLEAR_D, CSK_D = 1.7, 3.2
LUGS = [(-19.3, -16.6), (16.6, 19.3)]  # corner blocks, no back parts there: board stops + lanyard
LUG_Y = (BOTTOM_WALL, 7.8)              # R37 starts at y 8.3 (right)
PIN = (0.0, SPLIT_Y - 2.2, 1.2, 0.65)   # plate pin into the cap tab: x, y, d, h

# --- board ------------------------------------------------------------------------------
PCB_Z, PCB_T = 5.0, 0.8
PCB_TOP = PCB_Z + PCB_T
FRONT_IN = T - WALL_FRONT   # 7.2, inner face of the front wall
LEDGE_GAP = 0.05
LUG_GAP = 0.1


Y0B = BOTTOM_WALL + BOTTOM_GAP + 155.0   # y_e = Y0B - y_b


def b2e(xb, yb):
    return xb - 149.1, Y0B - yb


# --- front -------------------------------------------------------------------------------
# LS013B7DH03: module 26.6 x 30.3 x 0.741, active area 23.04 sq, its centre 17.23 mm
# above the FPC-side edge; module at board y 67.0..97.3, centred on x 149.1
DISPLAY = (26.6, 30.3, 0.741)
DISPLAY_CY = b2e(0, (67.0 + 97.3) / 2)[1]
AA_CY = b2e(0, 97.3 - 17.23)[1]
WINDOW = 24.0            # opening in the aluminium lip (active area 23.04 + margin)
GLASS = (27.5, 27.5, 0.55, 1.2)   # w, h, t, corner r; glued flush in a recess

WHEEL_CY = b2e(0, 126.85)[1]
WHEEL_R_OUT, WHEEL_R_IN = 15.0, 5.9
WHEEL_FLANGE_R = 16.2
BUTTON_R, BUTTON_FLANGE_R = 5.6, 6.6
SWITCH_R = 10.375        # TS-1187B-B at +-10.375 from the wheel centre
SWITCH_TOP = PCB_TOP + 0.75
GAP_WHEEL = 0.3
NUB_GAP = 0.05           # pre-travel above the switch domes (travel 0.2)

# --- ports (bottom face), heights from the datasheets ------------------------------------
USB_X, USB_Z = b2e(138.9, 0)[0], PCB_Z - 0.82   # shell -2.10..+0.46 from the board back face
USB_HOLE = (8.54, 2.76)   # receptacle shell 8.34 x 2.56 sits in it (0.1 all round), face 0.24 under
JACK_X, JACK_Z = b2e(159.3, 0)[0], PCB_Z - 0.60  # tails 0.60 above the plug axis
JACK_HOLE_D = 5.2         # the jack's 5.0 collar sits in it, 0.1 all round (CN1 moved 0.8 mm)

# --- power key (right side) ----------------------------------------------------------------
KEY_Y, KEY_Z = b2e(0, 68.6)[1], PCB_Z - 0.76     # EVQP7J01P actuator axis
KEY_SLOT = (7.0, 1.6)        # along Y, along Z
ACTUATOR_X = 19.6            # actuator tip, x_e

# --- battery -------------------------------------------------------------------------------
# Free length on the back between SW1/SW3 (board y 137.0) and the ESP32 module body
# (board y 74.8): 62.2 mm. The cell incl. its protection PCB must be <= 61.5 mm
BATTERY = (37.0, 61.5, 4.0)
BATTERY_Y0 = b2e(0, 136.8)[1]

# --- lanyard (bottom-left corner) -----------------------------------------------------------
# Two short drilled holes meeting inside the corner wall/lug; both exits sit on the R5
# corner, symmetric about its 45 deg line
LANYARD = dict(d=1.2, z=T / 2, angle=25.0)   # mid-thickness, exits at 25 and 65 deg on the corner arc


def plan(w, l, r, y0=0.0):
    return Pos(0, y0 + l / 2) * RectangleRounded(w, l, r)


def prism(face, z0, z1):
    return Pos(0, 0, z0) * extrude(face, z1 - z0)


def slot_x(cx, cz, w, h, length):
    """Stadium hole along Y through the bottom face (w across X, h along Z)."""
    s = SlotCenterToCenter(w - h, h)
    return Pos(cx, 0, cz) * Rot(90, 0, 0) * Pos(0, 0, -length / 2) * extrude(s, length)


def outer_shell():
    solid = prism(plan(W, L, CORNER_R), 0, T)
    top = solid.edges().group_by(Axis.Z)[-1]
    solid = chamfer(top, FRONT_CHAMFER)
    bottom = solid.edges().group_by(Axis.Z)[0]
    return fillet(bottom, BACK_R)


def inner_plan(extra=0.0):
    return plan(W - 2 * WALL_SIDE + 2 * extra, L - WALL_END - BOTTOM_WALL + 2 * extra,
                CORNER_R - WALL_SIDE + extra, BOTTOM_WALL - extra)


def front_cuts():
    cuts = []
    gw, gh, gt, gr = GLASS
    cuts.append(prism(Pos(0, AA_CY) * RectangleRounded(gw, gh, gr), T - gt, T + 1))
    cuts.append(prism(Pos(0, AA_CY) * RectangleRounded(WINDOW, WINDOW, 0.5), FRONT_IN - 0.1, T))
    cuts.append(Pos(0, WHEEL_CY, T - 1) * Cylinder(WHEEL_R_OUT + GAP_WHEEL, 4))
    return cuts


def port_cuts():
    cuts = [slot_x(USB_X, USB_Z, *USB_HOLE, 8)]
    cuts.append(Pos(JACK_X, 0, JACK_Z) * Rot(90, 0, 0) * Cylinder(JACK_HOLE_D / 2, 8))
    # power key slot in the right wall
    s = SlotCenterToCenter(KEY_SLOT[0] - KEY_SLOT[1], KEY_SLOT[1])
    cuts.append(Pos(W / 2 - 2, KEY_Y, KEY_Z) * Rot(0, 90, 0) * Rot(0, 0, 90) * extrude(s, 4))
    # lanyard: two drilled holes meeting inside the bottom-left lug
    ly = LANYARD
    cx, cy = -(W / 2 - CORNER_R), CORNER_R          # corner arc centre
    s = CORNER_R * math.sin(math.radians(ly["angle"]))
    lx, lyy = cx - s, cy - s                          # where the two holes meet
    r = ly["d"] / 2
    cuts.append(Pos(lx, -1, ly["z"]) * Rot(-90, 0, 0) * Cylinder(r, lyy + r + 1, align=None))
    cuts.append(Pos(-W / 2 - 1, lyy, ly["z"]) * Rot(0, 90, 0) * Cylinder(r, lx + r + W / 2 + 1, align=None))
    return cuts


def lugs():
    inner = prism(inner_plan(), PAD_T, PCB_Z)
    out = None
    for x0, x1 in LUGS:
        # 0.1 below the board: the lugs sit under back copper (tracks, CN1 tail), so they
        # only stop the board if it is pushed back; the battery foam holds it on the ledges
        top = PCB_Z - LUG_GAP
        b = Pos((x0 + x1) / 2, sum(LUG_Y) / 2, (PAD_T + top) / 2) * Box(x1 - x0, LUG_Y[1] - LUG_Y[0] + 1, top - PAD_T)
        b = b & inner
        out = b if out is None else out + b
    for x, y in SCREWS:
        out += Pos(x, y, (PAD_T + BOSS_TOP) / 2) * Cylinder(BOSS_R, BOSS_TOP - PAD_T)
    return out


def build_body():
    shell = outer_shell()
    body = shell - prism(inner_plan(), -1, FRONT_IN)
    body -= prism(plan(W - 2 * PLATE_RIM, L - 2 * PLATE_RIM, CORNER_R - PLATE_RIM, PLATE_RIM), -1, REBATE)
    body += lugs()
    # front stops for the board along both long sides (no front parts within 1 mm of
    # the edge); the battery foam presses the board against them
    for sgn in (-1, 1):
        x = sgn * (W / 2 - WALL_SIDE - 0.3)
        ledge = Pos(x, (BOTTOM_WALL + SPLIT_Y) / 2, (PCB_TOP + LEDGE_GAP + FRONT_IN) / 2) * Box(0.6 + 0.02, SPLIT_Y - BOTTOM_WALL, FRONT_IN - PCB_TOP - LEDGE_GAP + 0.01)
        body += ledge & prism(inner_plan(0.01), 0, T)
    for c in front_cuts() + port_cuts():
        body -= c
    for x, y in SCREWS:
        body -= Pos(x, y, (PAD_T - 0.5 + 4.2) / 2) * Cylinder(TAP_D / 2, 4.2 - PAD_T + 0.5)   # blind, to z 4.2
    # pad pockets: the plate is 1.0 thick under the lugs, so the lugs start at PAD_T
    body = body & prism(plan(W + 2, SPLIT_Y + 1, 1, -1), -1, T + 1)
    return body


def build_cap():
    shell = outer_shell()
    cap = shell - prism(inner_plan(), REBATE, FRONT_IN)
    cap = cap & prism(plan(W + 2, CAP_H + 1, 1, SPLIT_Y), -1, T + 1)
    # back tab reaching into the body over the plate; the plate pin drops into it
    tab = Pos(0, SPLIT_Y - 2.2, REBATE + 0.4) * Box(30, 4.4, 0.8)
    tab -= Pos(PIN[0], PIN[1], REBATE + 0.4) * Cylinder(PIN[2] / 2 + 0.1, 2)
    cap += tab
    # clamp for the top end of the board: two front ribs and a back post (board y 56..60,
    # antenna keepout: plastic only, between the SD socket and the ESP32)
    y0, y1 = b2e(0, 60.0)[1], b2e(0, 56.0)[1]
    for x in (-8.0, 8.0):
        cap += Pos(x, (y0 + y1) / 2, (PCB_TOP + 0.05 + FRONT_IN) / 2) * Box(1.2, y1 - y0, FRONT_IN - PCB_TOP - 0.05 + 0.01)
    xa, xb = b2e(146.5, 0)[0], b2e(150.5, 0)[0]
    cap += Pos((xa + xb) / 2, (y0 + y1) / 2, (REBATE + PCB_Z - 0.05) / 2) * Box(xb - xa, y1 - y0, PCB_Z - 0.05 - REBATE + 0.01)
    return cap


def screw_cut(x, y):
    c = Pos(x, y, 0) * Cylinder(SCREW_CLEAR_D / 2, 6)
    h = (CSK_D - SCREW_CLEAR_D) / 2   # 90 deg countersink
    c += Pos(x, y, h / 2 - 0.001) * Cone(CSK_D / 2, SCREW_CLEAR_D / 2, h)
    return c


def build_plate():
    outline = plan(W - 2 * PLATE_RIM - 2 * PLATE_GAP, SPLIT_Y - PLATE_RIM - PLATE_GAP * 2,
                   CORNER_R - PLATE_RIM - PLATE_GAP, PLATE_RIM + PLATE_GAP)
    # square top end: it closes straight against the cap's back wall
    top = Pos(0, (SPLIT_Y - PLATE_GAP + SPLIT_Y - 15) / 2) * RectangleRounded(
        W - 2 * PLATE_RIM - 2 * PLATE_GAP, 15 - PLATE_GAP, 0.01)
    plate = prism(outline, 0, PLATE_T) + prism(top, 0, PLATE_T)
    for x, y in SCREWS:
        plate += Pos(x, y, (PLATE_T + PAD_T) / 2) * Cylinder(BOSS_R + 0.1, PAD_T - PLATE_T)
    plate = fillet(plate.edges().group_by(Axis.Z)[0], 0.2)
    for x, y in SCREWS:
        plate -= screw_cut(x, y)
    plate += Pos(PIN[0], PIN[1], PLATE_T + PIN[3] / 2) * Cylinder(PIN[2] / 2, PIN[3])
    # the plate sits on the gasket: inner face at REBATE, outer face flush (z 0)
    return plate


def build_gasket():
    ring = plan(W - 2 * PLATE_RIM - 0.1, SPLIT_Y - PLATE_RIM - 0.05, CORNER_R - PLATE_RIM - 0.05, PLATE_RIM + 0.05)
    hole = plan(W - 2 * WALL_SIDE + 0.1, SPLIT_Y - BOTTOM_WALL - 0.6, CORNER_R - WALL_SIDE + 0.05, BOTTOM_WALL + 0.05)
    g = prism(ring, PLATE_T, REBATE) - prism(hole, 0, 1)
    return g


def _unused():
    plate = None
    return plate


# --- engraving ---------------------------------------------------------------------------
ENGRAVE_DEPTH = 0.03
LOGO_W, LOGO_CY = 16.0, 58.0
TEXT, TEXT_Y, TEXT_SIZE = 'made by "humans"', 13.0, 1.9


def logo_polygons():
    svg = LOGO_SVG.read_text()
    v_d = re.search(r'<path d="(M[^"]+Z)" fill="#fff"', svg).group(1)
    v = [tuple(map(float, p.split())) for p in re.findall(r"(\d+ \d+)", v_d)]
    lines_d = re.search(r'<path d="(M[^"]+)" fill="none" stroke="#000" stroke-width="([\d.]+)"', svg)
    stroke = float(lines_d.group(2))
    lines = []
    for sub in re.findall(r"M[^M]+", lines_d.group(1)):
        nums = list(map(float, re.findall(r"-?\d+(?:\.\d+)?", sub)))
        x, y = nums[0], nums[1]
        pts = [(x, y)]
        for dx, dy in zip(nums[2::2], nums[3::2]):
            x, y = x + dx, y + dy
            pts.append((x, y))
        lines.append(LineString(pts))
    gaps = unary_union([ln.buffer(stroke / 2, cap_style="flat") for ln in lines])
    ink = SPolygon(v).difference(gaps)
    s = LOGO_W / (max(p[0] for p in v) - min(p[0] for p in v))
    polys = list(ink.geoms) if hasattr(ink, "geoms") else [ink]

    # Seen from the back: device top up, so x is mirrored
    def tr(p):
        return Vector(-(p[0] - 500) * s, LOGO_CY - (p[1] - 500) * s, 0)
    faces = []
    for pg in polys:
        if pg.area * s * s < 1e-4:
            continue
        outer = Wire.make_polygon([tr(p) for p in pg.exterior.coords[:-1]], close=True)
        inners = [Wire.make_polygon([tr(p) for p in r.coords[:-1]], close=True) for r in pg.interiors]
        faces.append(Face(outer, inners))
    return faces


def _ring(wire, n=24):
    pts = []
    for e in wire.order_edges():
        pts += [tuple(e.position_at(i / n))[:2] for i in range(n)]
    return pts


def face_to_shapely(face):
    return SPolygon(_ring(face.outer_wire()), [_ring(w) for w in face.inner_wires()]).buffer(0)


def shapely_faces(geom, tr):
    out = []
    for pg in (geom.geoms if hasattr(geom, "geoms") else [geom]):
        if pg.area < 1e-4:
            continue
        outer = Wire.make_polygon([tr(p) for p in pg.exterior.coords[:-1]], close=True)
        inners = [Wire.make_polygon([tr(p) for p in r.coords[:-1]], close=True) for r in pg.interiors]
        out.append(Face(outer, inners))
    return out


def engraving():
    """Laser marking on the back face (z = 0), as thin solids just outside the surface,
    for the renders. The laser shop gets out/back_engraving.dxf."""
    parts = [Pos(0, 0, -ENGRAVE_DEPTH) * extrude(f, ENGRAVE_DEPTH) for f in logo_polygons()]
    txt = Pos(0, TEXT_Y) * Text(TEXT, TEXT_SIZE, font_path=FONT)
    # The variable font has overlapping contours: merge them in shapely, then mirror
    # (seen from the back) and rebuild clean faces
    glyphs = unary_union([face_to_shapely(f) for f in txt.faces()])
    for f in shapely_faces(glyphs, lambda p: Vector(-p[0], p[1], 0)):
        parts.append(Pos(0, 0, -ENGRAVE_DEPTH) * extrude(f, ENGRAVE_DEPTH))
    bad = [i for i, p in enumerate(parts) if not p.is_valid]
    if bad:
        print(f"  engraving: {len(bad)} invalid piece(s) dropped: {bad}")
    return Compound(children=[p for i, p in enumerate(parts) if i not in bad])


# --- printed parts, glass, internals ------------------------------------------------------
def build_wheel():
    zb = FRONT_IN - 0.45            # ring underside 6.75
    ring = Pos(0, WHEEL_CY, (zb + T) / 2) * (Cylinder(WHEEL_R_OUT, T - zb) - Cylinder(WHEEL_R_IN, T - zb))
    # flange under the front wall, 0.3 thick and kept high: U1 (CP2102N) sits under its rim
    fb = FRONT_IN - 0.35
    ring += Pos(0, WHEEL_CY, (fb + FRONT_IN - 0.05) / 2) * (Cylinder(WHEEL_FLANGE_R, FRONT_IN - 0.05 - fb) - Cylinder(WHEEL_R_OUT - 1, FRONT_IN - 0.05 - fb))
    # inner relief for the centre button flange
    ring -= Pos(0, WHEEL_CY, (zb + FRONT_IN + 0.05) / 2) * Cylinder(BUTTON_FLANGE_R + 0.3, FRONT_IN + 0.05 - zb + 0.001)
    for a in range(4):
        x, y = SWITCH_R * math.cos(a * math.pi / 2), SWITCH_R * math.sin(a * math.pi / 2)
        ring += Pos(x, WHEEL_CY + y, (SWITCH_TOP + NUB_GAP + zb) / 2) * Cylinder(0.6, zb - SWITCH_TOP - NUB_GAP + 0.01)
    ring = fillet(ring.edges().filter_by(lambda e: e.is_closed and abs(e.center().Z - T) < 1e-3), 0.25)
    return ring


def build_button():
    zb = FRONT_IN - 0.45
    b = Pos(0, WHEEL_CY, (FRONT_IN + 0.05 + T) / 2) * Cylinder(BUTTON_R, T - FRONT_IN - 0.05)
    b += Pos(0, WHEEL_CY, (zb + FRONT_IN) / 2) * Cylinder(BUTTON_FLANGE_R, FRONT_IN - zb)
    b += Pos(0, WHEEL_CY, (SWITCH_TOP + NUB_GAP + zb) / 2) * Cylinder(0.75, zb - SWITCH_TOP - NUB_GAP + 0.01)
    b = fillet(b.edges().filter_by(lambda e: e.is_closed and abs(e.center().Z - T) < 1e-3), 0.25)
    return b


def build_key():
    s = SlotCenterToCenter(KEY_SLOT[0] - 0.4 - (KEY_SLOT[1] - 0.3), KEY_SLOT[1] - 0.3)
    x0, x1 = ACTUATOR_X + 0.05, W / 2 + 0.3
    key = Pos(x0, KEY_Y, KEY_Z) * Rot(0, 90, 0) * Rot(0, 0, 90) * extrude(s, x1 - x0)
    # retaining tabs inside the wall, beyond the switch body ends
    for sgn in (-1, 1):
        key += Pos(19.05, KEY_Y + sgn * 3.35, KEY_Z) * Box(0.4, 2.3, KEY_SLOT[1] - 0.3)
        key += Pos((19.05 + x0) / 2 + 0.1, KEY_Y + sgn * 2.7, KEY_Z) * Box(x0 - 19.05 + 0.2, 0.8, KEY_SLOT[1] - 0.6)
    return key


def build_glass():
    gw, gh, gt, gr = GLASS
    return prism(Pos(0, AA_CY) * RectangleRounded(gw - 0.1, gh - 0.1, gr - 0.05), T - gt, T - 0.005)


def build_display():
    w, h, t = DISPLAY
    return Pos(0, DISPLAY_CY, FRONT_IN - 0.05 - t / 2) * Box(w, h, t)


def build_battery():
    w, l, t = BATTERY
    b = Pos(0, BATTERY_Y0 + l / 2, REBATE + 0.05 + t / 2) * Box(w, l, t)
    return fillet(b.edges().filter_by(Axis.Y), 1.2)


def build_screw(x, y):
    h = (CSK_D - SCREW_CLEAR_D) / 2 + 0.25
    s = Pos(x, y, h / 2) * Cone(1.5, 1.5 - h, h)
    s += Pos(x, y, (h + 4.0) / 2) * Cylinder(0.8, 4.0 - h)    # M1.6 x 4: tip at z 4.0
    # T5 hexalobular recess, approximated by a 6-point star
    pts = []
    for i in range(12):
        r = 0.72 if i % 2 == 0 else 0.45
        a = i * math.pi / 6
        pts.append(Vector(x + r * math.cos(a), y + r * math.sin(a), 0))
    s -= Pos(0, 0, -0.01) * extrude(Face(Wire.make_polygon(pts, close=True)), 0.6)
    return s


def build():
    body = build_body()
    plate = build_plate()
    eng = engraving()   # laser marking: drawn on the surface, not cut into the plate
    parts = [
        (body, "body (6061, bead blasted, natural anodize)", Color(0.70, 0.71, 0.72)),
        (plate, "back plate (6061, natural anodize)", Color(0.70, 0.71, 0.72)),
        (eng, "engraving (laser, bare aluminium)", Color(0.88, 0.89, 0.9)),
        (build_cap(), "antenna cap (3D printed, matte black)", Color(0.06, 0.06, 0.06)),
        (build_wheel(), "click wheel (3D printed, grey)", Color(0.62, 0.63, 0.64)),
        (build_button(), "centre button (3D printed, grey)", Color(0.62, 0.63, 0.64)),
        (build_key(), "power key (3D printed, matte black)", Color(0.06, 0.06, 0.06)),
        (build_glass(), "cover glass 0.55", Color(0.9, 0.95, 1.0, 0.25)),
        (build_display(), "LS013B7DH03", Color(0.55, 0.57, 0.52)),
        (build_battery(), "LiPo LP403759", Color(0.75, 0.75, 0.78)),
        (build_gasket(), "gasket 0.1 (die-cut adhesive)", Color(0.15, 0.15, 0.15)),
    ]
    for i, (x, y) in enumerate(SCREWS):
        parts.append((build_screw(x, y), f"screw M1.6x4 countersunk Torx {i + 1}", Color(0.3, 0.3, 0.32)))
    for shape, label, color in parts:
        shape.label, shape.color = label, color
    return parts


SLUG = {
    "body": "body", "back plate": "plate", "engraving": "engraving", "antenna cap": "cap",
    "click wheel": "wheel", "centre button": "button", "power key": "key", "cover glass": "glass",
    "LS013B7DH03": "display", "LiPo": "battery", "screw": "screw", "gasket": "gasket",
}


def slug(label):
    for k, v in SLUG.items():
        if label.startswith(k):
            return v + (label[-1] if v == "screw" else "")
    return label


def main():
    OUT.mkdir(exist_ok=True)
    parts = build()
    for shape, label, _ in parts:
        name = slug(label)
        export_gltf(shape, str(OUT / f"case_{name}.glb"), binary=True,
                    linear_deflection=0.01, angular_deflection=0.1)
        # meshes for the Blender renders (STL: no node transforms, unlike the glb)
        (OUT / "mesh").mkdir(exist_ok=True)
        export_stl(shape, OUT / "mesh" / f"{name}.stl", tolerance=0.002, angular_tolerance=0.05)
        if name in ("body", "plate"):
            export_step(shape, OUT / f"case_{name}.step")      # CNC
        if name in ("cap", "wheel", "button", "key"):
            export_stl(shape, OUT / f"case_{name}.stl", tolerance=0.005, angular_tolerance=0.1)
            export_step(shape, OUT / f"case_{name}.step")
    # the assembly last: Compound(children=...) re-parents the parts
    case = Compound(children=[p[0] for p in parts], label="mp3_player_case")
    export_step(case, OUT / "case_assembly.step")
    bb = parts[0][0].bounding_box()
    print(f"body {bb.size.X:.2f} x {bb.size.Y:.2f} x {bb.size.Z:.2f} mm, case {W} x {L} x {T}")
    for shape, label, _ in parts:
        print(f"  {label}: volume {shape.volume:.1f} mm3, valid {shape.is_valid}")


if __name__ == "__main__":
    main()

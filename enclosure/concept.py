"""Concept enclosure for the MP3 player, two variants.

A: compact, LiPo 503450 stacked behind the PCB (parts between PCB and cell)
B: thin, LiPo LP403759 next to the parts on the back of the PCB

Axes: X = width (centred), Y = length (0 = bottom edge, USB-C + jack),
Z = thickness (0 = back, T = front face with display and click wheel).

Run: .venv/bin/python concept.py  ->  out/concept_A.step, out/concept_B.step
"""

from dataclasses import dataclass
from pathlib import Path

from build123d import (
    Axis, Box, Color, Compound, Cylinder, Location, Plane, Polyline, Pos,
    Rot, export_step, export_stl, extrude, fillet, make_face,
)

OUT = Path(__file__).parent / "out"

# Fixed dimensions (mm), from datasheets and the 3D models in ../lib
WALL_SIDE = 1.2
WALL_BACK = 0.7
WALL_END = 1.2
FRONT_STACK = 1.6  # front wall 0.8 + display 0.74 + air; wheel uses metal domes
PCB_T = 0.8
CAP_H = 9.0  # 3D printed plastic cap over the ESP32 antenna

DISPLAY = (26.6, 30.3, 0.74)  # LS013B7DH03 module
DISPLAY_WINDOW = (25.0, 25.0)  # active area 23.04 + margin
WHEEL_OD, WHEEL_ID, WHEEL_T = 30.0, 11.5, 1.2
ESP32 = (13.2, 16.6, 2.42)
SD_SOCKET = (15.0, 16.1, 2.55)  # TF-01A, card enters along X
POWER_SW = (3.55, 3.5, 1.35)  # EVQP7J01P side push, on the front of the PCB
POWER_KEY = (7.0, 1.6)  # opening for the printed side key (length along Y, height)
JACK_HOLE_D = 6.0
USBC_HOLE = (9.6, 3.8)


@dataclass(frozen=True)
class Port:
    """Connector on the back of the PCB. Heights are measured from the PCB
    back face: `below` = how far the body hangs below it, `sink` = how far it
    goes up into a board cutout, `centre` = plug axis below the back face."""
    part: str
    w: float  # across the board (X)
    l: float  # along the plug (Y)
    below: float
    sink: float
    centre: float


# From the datasheet drawings (LCSC), not from the EasyEDA 3D models
USB_STD = Port("TYPE-C-31-M-12 (C165948)", 8.94, 7.9, 3.26, 0.0, 1.63)
USB_SINK = Port("TYPE-C 16P CB0.8 073 (C2906289)", 8.94, 7.2, 2.36, 0.8, 0.78)
JACK_STD = Port("PJ-342 (C668606)", 8.4, 14.0, 5.4, 0.0, 2.7)
JACK_SINK = Port("PJ-342C CB (C49287245)", 7.9, 14.0, 3.3, 1.25, 0.8)


@dataclass
class Variant:
    name: str
    width: float
    battery: tuple  # (w, l incl. protection PCB, t)
    stacked: bool  # battery behind the parts (A) or next to them (B)
    bottom_zone: float  # battery-free strip at the bottom: ports, audio, power
    top_zone: float  # ESP32 + SD socket strip under/near the cap
    corner_r: float = 5.0  # plan-view corner radius
    edge_r: float = 1.0  # front/back edge rounding
    parts_h: float = 1.5  # tallest part between PCB and stacked battery
    center_ports: bool = True  # USB-C + jack balanced around mid-thickness
    usb: Port = USB_STD
    jack: Port = JACK_STD

    @property
    def port_drop(self):
        return (self.usb.centre + self.jack.centre) / 2

    @property
    def pcb_bot(self):
        batt = WALL_BACK + 0.1 + self.battery[2] + 0.2
        if self.stacked:
            batt += self.parts_h
        z = max(batt, WALL_BACK + max(self.usb.below, self.jack.below) + 0.1)
        if self.center_ports:
            # Put the mean of the two plug axes at T/2. The display then sits
            # on a spacer above the PCB.
            z = max(z, 2 * self.port_drop + PCB_T + FRONT_STACK)
        return z

    @property
    def thickness(self):
        if self.center_ports:
            return round(2 * (self.pcb_bot - self.port_drop), 2)
        return round(self.pcb_bot + PCB_T + FRONT_STACK, 2)

    @property
    def length(self):
        return round(WALL_END + self.bottom_zone + self.battery[1]
                     + self.top_zone + WALL_END, 1)


VARIANTS = [
    Variant("A", 41.0, (34.0, 54.0, 5.0), True, 17.0, 17.0),
    Variant("B", 41.0, (37.0, 63.0, 4.0), False, 18.0, 19.0, usb=USB_SINK, jack=JACK_SINK),
    Variant("A_sharp", 41.0, (34.0, 54.0, 5.0), True, 17.0, 17.0, corner_r=0.6, edge_r=0.3),
    Variant("B_sharp", 41.0, (37.0, 63.0, 4.0), False, 18.0, 19.0, corner_r=0.6, edge_r=0.3,
            usb=USB_SINK, jack=JACK_SINK),
]


def round_z(shape, r):
    """Fillet the edges parallel to Z, skipped when the radius is too small."""
    return fillet(shape.edges().filter_by(Axis.Z), r) if r > 0.05 else shape


def wedge(width, length, depth, z0=0.0, overshoot=2.0):
    """Ramp on the back: depth at y=0, zero at y=length, centred in X."""
    pts = [(-overshoot, z0 - overshoot), (-overshoot, z0 + depth + depth / length * overshoot),
           (length, z0), (length, z0 - overshoot)]
    face = make_face(Polyline(*pts, close=True))
    face = Plane.YZ * face  # local x -> Y, local y -> Z
    return Pos(-width / 2, 0, 0) * extrude(face, width)


def build(v: Variant):
    W, L, T = v.width, v.length, v.thickness
    pcb_bot = v.pcb_bot
    pcb_top = pcb_bot + PCB_T
    # Ports sit on the flat part of the bottom face, clear of the corner radius;
    # the ramp takes whatever width is left between the two pillars
    port_half = max(USBC_HOLE[0], v.jack.w) / 2
    port_x = W / 2 - max(v.corner_r, WALL_SIDE + 0.8) - port_half - 0.5
    ramp_w = 2 * (port_x - port_half - WALL_SIDE)
    ramp_depth = T / 2
    ramp_len = v.bottom_zone + WALL_END

    # Outer shape
    outer = Pos(0, L / 2, T / 2) * Box(W, L, T)
    outer = round_z(outer, v.corner_r)
    outer = fillet(outer.edges().filter_by(lambda e: e.length > 3 and not e.is_closed
                                           and abs(e.tangent_at(0).Z) < 0.01), v.edge_r)
    outer -= wedge(ramp_w, ramp_len, ramp_depth)

    cavity = Pos(0, L / 2, (WALL_BACK + T - 0.8) / 2) * Box(
        W - 2 * WALL_SIDE, L - 2 * WALL_END, T - 0.8 - WALL_BACK)
    cavity = round_z(cavity, v.corner_r - WALL_SIDE)
    cavity -= wedge(ramp_w + 2 * WALL_SIDE, ramp_len + 1.0, ramp_depth, z0=WALL_BACK)
    shell = outer - cavity

    # Front openings
    disp_cy = L - CAP_H - 4 - DISPLAY[1] / 2
    wheel_cy = (disp_cy - DISPLAY[1] / 2) / 2  # centred between display and bottom edge
    shell -= Pos(0, disp_cy, T) * Box(*DISPLAY_WINDOW, 2)
    shell -= Pos(0, disp_cy, T - 0.4) * Box(DISPLAY[0] + 2, DISPLAY[1] + 2, 0.4)  # glass seat
    shell -= Pos(0, wheel_cy, T) * Cylinder(WHEEL_OD / 2 + 0.3, 2)

    # Bottom ports in the two full-thickness pillars
    usb_z = pcb_bot - v.usb.centre
    jack_z = pcb_bot - v.jack.centre
    usb_cut = Pos(-port_x, 0, usb_z) * Rot(90, 0, 0) * Box(USBC_HOLE[0], USBC_HOLE[1], 6)
    usb_cut = fillet(usb_cut.edges().filter_by(Axis.Y), USBC_HOLE[1] / 2 - 0.05)
    shell -= usb_cut
    shell -= Pos(port_x, 0, jack_z) * Rot(90, 0, 0) * Cylinder(JACK_HOLE_D / 2, 6)

    # microSD slot on the left side, next to the ESP32
    sd_cy = L - WALL_END - 3 - SD_SOCKET[1] / 2
    sd_z = pcb_bot - SD_SOCKET[2] / 2
    shell -= Pos(-W / 2, sd_cy, sd_z) * Box(6, 12.5, 1.8)

    # Power key on the right side, level with the display
    pwr_z = pcb_top + POWER_SW[2] / 2
    shell -= Pos(W / 2, disp_cy, pwr_z) * Box(6, *POWER_KEY)

    # Split into metal body and plastic cap
    split_y = L - CAP_H
    body = shell & (Pos(0, split_y / 2, T / 2) * Box(W + 2, split_y, T + 2))
    cap = shell & (Pos(0, split_y + CAP_H / 2 + 1, T / 2) * Box(W + 2, CAP_H + 2, T + 2))

    # Internals
    inner_w, inner_l = W - 2 * WALL_SIDE - 0.4, L - 2 * WALL_END - 0.4
    pcb = Pos(0, L / 2, pcb_bot + PCB_T / 2) * Box(inner_w, inner_l, PCB_T)
    pcb = round_z(pcb, v.corner_r - WALL_SIDE - 0.2)
    pcb -= wedge(ramp_w + 2 * WALL_SIDE + 1, ramp_len + 1.0, ramp_depth, z0=WALL_BACK)
    for x, port in ((-port_x, v.usb), (port_x, v.jack)):
        if port.sink:  # board cutout for a sinking connector
            pcb -= Pos(x, port.l / 2, pcb_bot) * Box(port.w + 0.2, port.l + 2, 4)
    display = Pos(0, disp_cy, T - FRONT_STACK + 0.1 + DISPLAY[2] / 2) * Box(*DISPLAY)
    bw, bl, bt = v.battery
    batt_y0 = WALL_END + v.bottom_zone
    battery = Pos(0, batt_y0 + bl / 2, WALL_BACK + 0.1 + bt / 2) * Box(bw, bl, bt)
    esp_y = L - WALL_END - 0.5 - ESP32[1] / 2
    esp_x = W / 2 - WALL_SIDE - 1 - ESP32[0] / 2
    esp32 = Pos(esp_x, esp_y, pcb_bot - ESP32[2] / 2) * Box(*ESP32)
    sd = Pos(-W / 2 + WALL_SIDE + SD_SOCKET[0] / 2, sd_cy, sd_z) * Box(*SD_SOCKET)
    power_sw = Pos(W / 2 - WALL_SIDE - 0.2 - POWER_SW[0] / 2, disp_cy, pwr_z) * Box(*POWER_SW)
    power_key = Pos(W / 2 - WALL_SIDE / 2 + 0.3, disp_cy, pwr_z) * Box(WALL_SIDE + 0.6, POWER_KEY[0] - 0.3,
                                                                     POWER_KEY[1] - 0.2)
    def port_body(port, x, y0):
        h = port.below + port.sink
        return Pos(x, y0 + port.l / 2, pcb_bot + port.sink - h / 2) * Box(port.w, port.l, h)

    jack = port_body(v.jack, port_x, WALL_END - 0.5)
    usbc = port_body(v.usb, -port_x, WALL_END - 0.8)
    wheel = Pos(0, wheel_cy, T - WHEEL_T / 2) * (Cylinder(WHEEL_OD / 2, WHEEL_T)
                                                - Cylinder(WHEEL_ID / 2 + 0.3, WHEEL_T))
    center = Pos(0, wheel_cy, T - WHEEL_T / 2) * Cylinder(WHEEL_ID / 2, WHEEL_T)

    parts = [
        (body, "body (anodized aluminium)", Color(0.62, 0.63, 0.65)),
        (cap, "cap (3D printed)", Color(0.95, 0.95, 0.95)),
        (wheel, "click wheel (3D printed)", Color(0.9, 0.9, 0.9)),
        (center, "play button (3D printed)", Color(0.8, 0.8, 0.8)),
        (pcb, "PCB", Color(0.1, 0.45, 0.2)),
        (display, "LS013B7DH03", Color(0.2, 0.2, 0.2)),
        (battery, f"LiPo {bw:g}x{bl:g}x{bt:g}", Color(0.85, 0.7, 0.2)),
        (esp32, "ESP32-PICO-MINI-02", Color(0.6, 0.6, 0.6)),
        (sd, "TF-01A", Color(0.7, 0.7, 0.7)),
        (power_sw, "EVQP7J01P", Color(0.3, 0.3, 0.3)),
        (power_key, "power key (3D printed)", Color(0.9, 0.9, 0.9)),
        (jack, v.jack.part, Color(0.15, 0.15, 0.15)),
        (usbc, v.usb.part, Color(0.75, 0.75, 0.75)),
    ]
    children = []
    for shape, label, color in parts:
        shape.label, shape.color = label, color
        children.append(shape)
    return Compound(children=children, label=f"concept_{v.name}"), parts


def main():
    OUT.mkdir(exist_ok=True)
    for v in VARIANTS:
        assembly, parts = build(v)
        export_step(assembly, OUT / f"concept_{v.name}.step")
        export_stl(parts[0][0], OUT / f"concept_{v.name}_body.stl")
        usb = v.pcb_bot - v.usb.centre - v.thickness / 2
        jack = v.pcb_bot - v.jack.centre - v.thickness / 2
        print(f"{v.name}: {v.width:g} x {v.length:g} x {v.thickness:g} mm, "
              f"USB-C {usb:+.2f} / jack {jack:+.2f} mm from centre "
              f"({v.usb.part} + {v.jack.part}), battery {v.battery}")


if __name__ == "__main__":
    main()

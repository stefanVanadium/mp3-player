# MP3 Player

Author: Stefan Jipa

## Goal
build a good, modern MP3 player with a retro style (going all out on the design)

## Requirements
- custom made, PCB designed in KiCad, assembled by JLCPCB (as many parts as possible from their stock)
- compact
- highest possible audio quality on the jack (FLAC/WAV, not just MP3)
- Bluetooth to wireless headphones (A2DP)
- 3.5mm jack with plug detection
- push-push microSD
- USB-C: charging + programming (USB-UART) + ESD protection
- thin LiPo battery + charger + fuel gauge + soft power (power on from a button)
- display readable in sunlight
- v1 WITHOUT speakers (WM8960/class-D stay for v2)

## Architecture

```
USB-C ─ ESD ─┬─ CP2102N ── auto-reset ── ESP32-PICO-MINI-02
             └─ BQ25180 (charger + power path + ship mode + button)
                   │ VSYS
                   ├─ TPS63802 buck-boost ── 3.3V digital (ESP32, SD, display)
                   ├─ LP5907 LDO ─────────── clean 3.3V analog (DAC)
                   └─ LM27762 ────────────── clean ±rails (headphone amp)
                 LiPo ── MAX17048 (fuel gauge, I2C)

ESP32 ── I2S ── PCM5122 (DAC) ── OPA1622 (headphone amp) ── 3.5mm jack (detect pin → GPIO)
      ├─ SDMMC 4-bit ── microSD push-push
      ├─ SPI ── display (Sharp LS013B7DH03 memory LCD)
      ├─ I2C ── BQ25180, MAX17048, PCM5122
      ├─ GPIO ── buttons
      └─ BT A2DP ── wireless headphones
```

## Components (BOM v1)

JLC prices / stock checked on 2026-10-20. All are "extended" (~$3 JLC fee per part type).
Before ordering: re-check stock + the exact variant on jlcpcb.com/parts.

### Brain
| What | Part | LCSC | Stock | Price | Notes |
|---|---|---|---|---|---|
| MCU | **ESP32-PICO-MINI-02** (N8R2) | C2980306 / C3013939 | ~1100 | ~$5.6 | 13.2x16.6mm, 8MB flash + **2MB PSRAM** (audio/FLAC buffer), built-in antenna + certified. Check which code is the PCB-antenna variant and which is "U" (U.FL) |
| alternative | ESP32-WROOM-32E | C701341 | 27k | $3.75 | larger (18x25.5), no PSRAM |
| why not | ESP32-PICO-V3 (bare chip) | C967022 | 313 | $4.2 | you design the antenna + RF matching + crystal yourself → hard to get right, not worth it |

Only the **classic** ESP32 has Bluetooth Classic (A2DP) for headphones. S3/C3/C6 are BLE only.

### Audio (hi-fi path)
| What | Part | LCSC | Stock | Price | Notes |
|---|---|---|---|---|---|
| DAC | **PCM5122** | C1540085 | 177 | $4.1 | 112dB, 32-bit/384kHz, hardware volume over I2C, works without MCLK (internal PLL from BCK) |
| headphone amp | **OPA1622** | C2876559 | 2682 | $3.0 | top-tier for headphones (very low THD), VSON-10 3x3 |
| amp rails | **LM27762** | C473398 | 35k | $0.96 | generates clean ± voltage (charge pump + LDO) for the OPA1622 |
| jack | **PJ-342C CB**, 4-pole, sinking (enclosure B) | C49287245 | 663 | $0.27 | HP-DET contact for plug detection. Replaced PJ-342 (C668606) on 2026-10-22, see connections.md 4.5 |

"All-in-one" option for a more compact build: **CS43131** (Cirrus, DAC + headphone amp + jack detect, 130dB, the chip in good dongles).
LCSC C965907, only **30 in stock**, ~$5.6. Digital interface probably 1.8V only → would need level shifters
(TXB0104 C105266 + PCA9306 C33196). To be checked in the datasheet.

Simpler/cheaper fallback: PCM5102A (C107671, 3254 pcs, $1.45) instead of PCM5122.

### Power
| What | Part | LCSC | Stock | Price | Notes |
|---|---|---|---|---|---|
| charger | **BQ25180** | C3682423 | 4077 | $1.76 | I2C, power path, **ship mode + button** (MR) = soft power, tiny DSBGA-8 |
| alternative | BQ25185 | C19725033 | 4259 | $1.55 | no I2C (standalone), WSON easier to solder |
| 3.3V digital | **TPS63802** buck-boost 2A | C2845237 | 37k | $0.91 | drains the battery fully, handles BT/WiFi peaks |
| 3.3V analog | **LP5907-3.3** | C80670 | 49k | $0.16 | low-noise LDO, DAC only, from VSYS |
| fuel gauge | **MAX17048** | C2682616 | 24k | $2.15 | real battery percentage, DFN 2x2 |
| battery | **LiPo 503450, 1000 mAh**, with protection circuit | — | — | — | chosen 2026-10-21. 5.0 x 34 x 50 mm, bought separately. Charge at 0.5C = 500 mA (~2.5 h). Estimated runtime ~11-13 h on the jack, ~7-8 h on Bluetooth |

**Soft power (BQ25180):**
- **power on**: press the button, BQ25180 leaves ship mode and powers the system
- **power off**: ESP32 sends the ship mode command over I2C; the battery is disconnected (a few nA)
- **long press**: hardware reset, in case something hangs
- dedicated alternative: LTC2954 (C683782, $6.7, expensive)

### USB-C
| What | Part | LCSC | Stock | Price | Notes |
|---|---|---|---|---|---|
| connector | **TYPE-C 16P CB0.8 073**, sinking, for 0.8 mm boards | C2906289 | 19.8k | $0.10 | + 2x 5.1k on CC1/CC2. Replaced TYPE-C-31-M-12 (C165948) on 2026-10-22 for enclosure B |
| ESD | USBLC6-2SC6 | C7519 | 44k | $0.18 | on D+/D- |
| USB-UART | **CP2102N-A02-GQFN24R** | C969151 | 19.7k | $1.98 | + 2 transistors for ESP32 auto-reset/boot. QFN24, not QFN20: the QFN20 has no DTR pin, and auto-reset needs DTR + RTS |
| alternative | CH343P | C2846043 | 10k | $1.0 | cheaper, just as small |

### Storage, display, buttons
| What | Part | LCSC | Stock | Price | Notes |
|---|---|---|---|---|---|
| microSD | push-push (自弹式) | C91145 (TF-01A) | 181k | $0.19 | check footprint + card detect pin |
| display | **Sharp LS013B7DH03** 1.28" 128x128 memory LCD | 0 stock at JLC | — | ~$10 | DigiKey/Mouser. 10-pin FPC 0.5mm. Chosen 2026-10-21 over ST7567: known pinout, nicer, and the same display is reused across projects (see ../PROJECTS.md) |
| FPC | 0.5mm, pin count per panel | Hirose FH12-10S-0.5SH, C506791 (10P) | 7900 | $0.51 | |
| buttons | side tact switch / small SMD | to choose | — | — | play/pause, next, prev, vol+, vol- (+ power = BQ25180 button) |

**Display notes (LS013B7DH03):**
- SPI up to 1 MHz, SCS is active HIGH
- EXTMODE = GND, so VCOM inversion is done over serial (no EXTCOMIN toggle needed)
- DISP on IO33 with a 100k pull-down: the panel stays blank until firmware has cleared its memory (datasheet power-on sequence)
- check the FPC contact side (Sharp recommends a top-contact connector) before ordering the PCB

### Passives
Chosen for quality, not lowest price. Every part has its code in the `LCSC Part` field (used for the JLC BOM).

| Where | Part | LCSC | Package |
|---|---|---|---|
| audio path, rail dividers, all 10K/100K (470, 10K, 20K, 91K, 100K, 147K, 150K) | Yageo RT0402BRD07 thin film, 0.1%, 25ppm | C852799, C190095, C705630, C852952, C852472, C5197520, C852538 | 0402 |
| odd values with no thin film in stock (511K TPS63802 FB, 22.1K/47.5K CP2102N VBUS) | Yageo RC0402FR-07, 1% | C163461, C163478, C137974 | 0402 |
| digital only (4.7K I2C, 5.1K CC, 1K, 33, 1M) | UniRoyal 1% (basic) | C25900, C25905, C11702, C25105, C26083 | 0402 |
| DAC output filter 2.2nF (C24, C25) | Murata GRM1555 **C0G** ±2% (no piezo/DC-bias distortion in the signal path) | C2987940 | 0402 |
| 0.1µF decoupling | Samsung CL05B X7R 16V | C1525 | 0402 |
| 1µF | Samsung CL05A X5R 25V | C52923 | 0402 |
| 1µF on VBUS (C10) | Samsung X5R 50V | C15849 | 0603 |
| 2.2µF / 4.7µF | Samsung CL10A X5R 16V | C23630 / C19666 | 0603 |
| 10µF on 3.3V rails | Samsung CL10A X5R 10V | C19702 | 0603 |
| 10µF on VSYS (C15, C19, C21) | Samsung X5R 25V (less DC-bias loss) | C96446 | 0603 |
| 10µF on VBUS / C9 | Samsung CL21A X5R 25V | C15850 | 0805 |
| 22µF TPS63802 output | Samsung CL21A X5R 25V | C45783 | 0805 |
| D2 boot diode | B5819W (basic) | C8598 | SOD-123 |
| BT1 battery | JST SH 2-pin SMD, side entry, ~2.9 mm tall (hand-soldered) | C160402 | SM02B-SRSS-TB (JST PH is too tall for enclosure B) |

Bulk caps are 0603/0805 rather than 0402: an 0402 10µF keeps only ~30-40% of its value at 3.3V (DC bias).
Thin film + C0G add 11 extended part types (~$33 JLC fees). Only 6 of them are unavoidable (odd values + C0G); the
quality upgrade (thin film instead of basic 10K/100K/470/20K/150K) costs ~$15 extra per order.
**JST polarity**: there is no standard. Check the red wire of the battery against pad 1 (+) before plugging it in.

## Who solders what

Rule: JLC places only what can't be hand-soldered (QFN/DFN/BGA/LGA, no visible pins).
Parts with visible pins are bought from LCSC in the same cart (same parcel) and soldered at home → no $3/type fee.

### JLC (assembly) — 9 extended types (~$27 in fees)
| Part | LCSC | Package | Why JLC |
|---|---|---|---|
| ESP32-PICO-MINI-02 | C2980306 / C3013939 | LGA (pads underneath) | impossible by hand |
| PCM5122 | C1540085 | TSSOP-28 | 0.65mm pitch, hand-solderable but risky; we want clean joints on audio |
| OPA1622 | C2876559 | VSON-10 3x3 | thermal pad underneath |
| LM27762 | C473398 | WSON-12 2x3 | thermal pad underneath |
| BQ25180 | C3682423 | DSBGA-8 | BGA |
| TPS63802 | C2845237 | VSON-10 2x3 | no pins |
| TPS63802 inductor (0.47uH) | to choose | 2016/2520 | must sit next to the IC, reflowed |
| MAX17048 | C2682616 | DFN-8 2x2 | no pins |
| CP2102N-A02-GQFN24R | C969151 | QFN-24 4x4 | no pins |
| resistors, capacitors, 2 auto-reset transistors, B5819W Schottky (C8598, GPIO2→GPIO0 boot fix) | **basic** list only | 0402/0603, SOT-23, SOD-123 | basic = no fee |

### Me (iron + flux) — 0 fees
| Part | LCSC | Package | Difficulty |
|---|---|---|---|
| click wheel buttons (x5) | C500066 TS-1187B-B, 0.75 mm | SMD | easy |
| power button, side push | C2828254 EVQP7J01P, 1.35 mm | SMD | medium (small pads at the board edge) |
| boot + reset buttons | C720477 TS-1088 | SMD | easy |
| 3.5mm jack with detect | to choose (PJ-320/PJ-342) | SMD/THT | easy |
| LP5907-3.3 | C80670 | SOT-23-5 | easy |
| USBLC6-2SC6 | C7519 | SOT-23-6 | easy |
| microSD push-push | C91145 (TF-01A) | SMD | medium (pins under the metal shell, lots of flux) |
| display FPC (x1, only the one used) | C506791 Hirose FH12-10S | 0.5mm | medium (drag soldering + flux + wick) |
| USB-C 16 pins, sinking | C2906289 | SMD, 0.5mm pitch, sits in a board cutout | **hard** — flux, fine tip, inspect for bridges under magnification |
| battery (JST or direct) | — | — | easy |
| display on FPC | — | — | just plug it into the connector |

Order: JLC does the reflow, then at home first USB-C and microSD (the fine ones), then FPC, finally jack, buttons, battery.

Tools: iron with a fine tip (e.g. Pinecil/TS101), gel flux (no-clean), wick, 0.3-0.5mm solder, magnifier, multimeter.
Check USB-C for continuity (VBUS-GND and D+/D-) **before** plugging it in.

## Cost estimate (2026-10-20, to re-check when ordering)

Parts per board (price at 1-9 pcs): ~$23
- ICs: ~$21 (ESP32 5.6, PCM5122 4.1, OPA1622 3.0, MAX17048 2.15, CP2102N 2.0, BQ25180 1.76, TPS63802+inductor 1.1, LM27762 0.96, rest <1)
- connectors + buttons: ~$1.5
- passives: ~$0.5 (basic)

Prototype (5 PCBs 4 layers, 2 assembled Economic, leaded parts soldered at home):
| What | ~$ |
|---|---|
| 4-layer PCB x5 | 8 |
| PCBA Economic setup + stencil | 10 |
| extended fees (9 x $3) | 27 |
| parts for 2 boards (JLC + LCSC) | 46 |
| shipping to RO (Global Standard) | 12 |
| VAT 21% | 22 |
| **total** | **~125 (~560 lei)** |

If Economic doesn't accept the BGA (BQ25180) → Standard (+~$17) or BQ25185 (WSON, no I2C).

Extra (per unit): battery ~20-30 lei, LS013B7DH03 ~60-70 lei, microSD ~30 lei.

## Design notes
- **antenna area**: no copper (not even a ground plane) under the module antenna, module at the board edge. With a metal case, a plastic window is needed in front of the antenna
- **audio**: ONE solid ground plane, no split (TI recommends a common AGND/DGND for the PCM512x). Separation comes from placement: DAC and amp far from the ESP32 and the TPS63802 inductor, digital traces away from the analog outputs
- **OPA1622 thermal pad = V− (−3V), not GND**. Its vias go to a −3V copper pour
- **ESP32**: SDMMC 4-bit uses strapping pins. GPIO12 (SD D2) has a pull-up, so burn the eFuse ONCE before the first flash: `espefuse.py set_flash_voltage 3.3V`. GPIO2 (SD D0) has a pull-up, so a B5819W diode from GPIO2 (anode) to GPIO0 (cathode) pulls it low when auto-reset enters download mode. Don't use GPIO0 for anything else
- **real quality**: on the jack, FLAC/WAV at 44.1/48kHz. On Bluetooth quality is limited by SBC (ESP32 doesn't do aptX/LDAC)
- **music on the card**: the classic ESP32 has no native USB. Copy to microSD on a PC or upload over WiFi (web page served by the player)
- **speakers (v2)**: WM8960 or a small class-D (MAX98357A on I2S) + phone speakers

## Status (2026-10-21)

Done:
- [x] architecture + BOM chosen, JLC stock/prices checked
- [x] JLC vs "I solder" list, cost estimated ~$125
- [x] KiCad libraries installed (`lib/`, symbol + footprint + 3D per part)
- [x] datasheets in `datasheets/` (all parts, MAX17048 included)
- [x] pins verified against datasheets, full connection list in **[connections.md](connections.md)**
- [x] **schematic done** (2026-10-21): 5 sheets (usb, power, esp32, audio, io), 112 parts, annotated. Final check on the KiCad netlist: 278/278 pin and passive checks against `connections.md` pass. ERC clean (2026-10-22): 0 errors, 0 warnings (`Unspecified` pin type set to OK in the pin conflict map, USBLC6 pins fixed, power flags moved onto real nets)

- [x] **footprints + LCSC codes on all 112 parts** (2026-10-21), see [Passives](#passives)

Next:
- [x] enclosure concept: variant B, rounded (see [Enclosure](#enclosure))
- [x] schematic for enclosure B (2026-10-22): jack PJ-342C CB (CN1), USB-C CB0.8 (USB1), BT1 JST SH, wheel TS-1187B-B, power EVQP7J01P, 100nF on `JACK_DET`. ERC 0/0, netlist diff vs. previous commit = only these changes
- [ ] choose the exact LP403759 cell (drawing with PCM length, JST SH lead)
- [x] Board Setup (2026-10-22): 4 layers (F.Cu signal, In1 GND, In2 GND2, B.Cu signal), 0.8 mm, ENIG. JLC-safe rules: 0.15 mm track/clearance, via 0.6/0.3, hole-to-hole 0.5, edge 0.3, silk 0.15 mm / 1.0 mm text. Net class `Power` (0.4 mm) on VBUS, VBAT, VSYS, +3V3, +3V3_A, ±3V0_AMP
- [x] board outline on Edge.Cuts from `enclosure/out/pcb_outline_B.dxf` (38.2 × 99.6 mm, R3.6), board at x 130–168.2, y 55.4–155 (centre line x 149.1), drill/place and grid origin at the bottom-left corner (130, 155). USB1 at (138.9, 150.35), CN1 at (159.3, 147.89), i.e. ±10.2 mm from the centre line. Their cutouts are drawn on the board outline (removed from the footprints); CN1 pads trimmed to 1.2 × 1.465 mm for 0.2 mm to the slot; `mp3_player.kicad_dru` allows 0.2 mm edge clearance for USB1/CN1 pads only, 0.3 mm elsewhere. TF-01A peg holes made non-plated
- [ ] PCB placement. Front: display, wheel, small parts only (1.6 mm front stack). Back: everything tall; the battery covers the middle (board y ~74–137), so back parts go in the top and bottom strips. Done so far (all on the back): USB1 (138.9, 150.35), CN1 (159.3, 147.89), U7 ESP32 (157.6, 66.5) antenna at the top edge, Card3 microSD (139.9, 65.5) 90°, SW2 power (166.6, 68.6) actuator out of the right edge. Rule area "Antenna keepout" on all copper layers, x 148–168.2, y 55.4–61.0. Chips (2026-10-23), front stays outside the wheel opening (R 15.5 around 149.1, 126.85) and the display (y 67–97.3):
  - power corner, back, bottom-left between the battery end (y ~136.2) and USB1: BT1 (133.2, 139.2) 0°, cable entry toward the battery; U2 BQ25180 (137.2, 140.2); U5 MAX17048 (133.2, 143.8); D1 USBLC6 (138.9, 145.4) right above the USB data pads; U4 TPS63802 (141.0, 141.0) with L1 (143.72, 141.0) on its switch pins. Assumes the cell leads come out at the bottom end
  - front, bottom-left under the wheel: U1 CP2102N (137.5, 143.0) 90°, USB pins toward the connector, UART pins toward Q1 (132.4, 140.4) and Q2 (132.4, 144.6)
  - DAC, front, middle band right (~40 mm from L1): U9 PCM5122 (161.2, 104.5), I2S pins up, analog outputs down; U6 LP5907 (157.6, 110.2) 90°
  - amp at the jack: U8 OPA1622 front (161.5, 140.5) 180°, HP_R/HP_L outputs facing their CN1 pads; U3 LM27762 back (160.5, 138.6) above the jack
  - D2 boot diode, front, top strip (143.0, 63.8)
  - click wheel, front, centre (149.1, 126.85), contacts on the ring mid-radius 10.375 mm: SW4 PLAY centre, SW5 VOL+ top, SW6 VOL− bottom, SW8 PREV left, SW7 NEXT right (TS-1187B-B is 0.75 mm tall, 1.4 mm free under the ring)
  - SW1 EN (147.0, 138.6) and SW3 BOOT (153.0, 138.6) on the back under the start of the ramp (~3.3 mm free for the 2.0 mm switches); reachable only with the battery out, auto-reset covers normal flashing
  - FPC4 not placed: FH12 is 2.0 mm tall and fits neither the front (~1.8 mm) nor the back (the battery is behind the display). The LCD tail (13.63 mm past the glass, centred, contacts on the back side) lies flat and ends at y ~110.9, so x ~143.5–155.5, y ~106.5–111.3 on the front is kept free for a low-profile bottom-contact connector, e.g. Hirose FH19C-10S-0.5SH(10) (C598004, 0.9 mm, 0.3 mm FPC). Needs a schematic footprint/LCSC swap
  - next: FPC4, then passives around their chips
- [ ] check the real PJ-342C CB (HP-DET), TF-01A card detect and LS013 flex contact side against the footprints before ordering
- [ ] firmware bring-up (see `code.md`)

## Enclosure
Concept decided 2026-10-22. **Chosen: variant B, rounded corners** (A and the sharp versions stay in `concept.py` for reference).

- **Form**: vertical, iPod-style. Display on top of the front face, click wheel below it
- **v1 shell: CNC aluminium 6061, anodized.** Any colour (grey, dark blue, pink, purple), matte or gloss, cheap at JLCCNC / PCBWay
- **v2 shell: anodized titanium.** Interference colours (natural grey, blue, purple, gold, magenta; no pastel pink), heavier and more premium, several times the machining cost. Only after v1 fits
- **Click wheel**: mechanical, iPod mini style. A 3D printed ring rocking on 4 contacts (top VOL+, bottom VOL−, left PREV, right NEXT) plus a centre PLAY button. Contacts are **metal domes** (~0.4 mm, hand-applied), not 2 mm tactile switches, or the front stack grows by ~1.5 mm. No capacitive scrolling in v1 (needs a touch controller and free GPIOs)
- **Antenna window**: a metal shell blocks BT/WiFi, so the **top end is a 3D printed plastic cap** (9 mm), with the ESP32 antenna right under it
- **microSD**: stays inside (no slot in the shell, the card is changed with the shell open). Socket on the back, top-left, card enters from the left board edge
- **Back ramp**: a wedge cut into the back, centred, running into the bottom edge (half the thickness deep at the edge). It starts where the battery ends, so it covers the bottom ~19 mm, not half the length. USB-C and jack sit in the two full-thickness pillars on either side
- **Ports**: on the flat part of the bottom face, clear of the corner radius; plug axes centred in the thickness
- **Display**: LS013B7DH03 behind a clear window (glass or acrylic) in the front face, on a spacer above the PCB
- **Tools**: modelled in code with [build123d](https://github.com/gumyr/build123d), `enclosure/concept.py` (venv in `enclosure/.venv`). STEP + renders in `enclosure/out/`. View in FreeCAD. Renders: `.venv/bin/python render/compare.py out` (also `render.py`, `ends_ortho.py`; need `pyvista`)
- **Renders**: `render/hero.py` makes the README image (`out/hero_B.png`). Later, once the PCB and the final model are done: a photoreal render (materials, lighting, depth of field), e.g. in Blender from the STEP
- **Sketch**: `examplev1.dxf`, Stefan's first design sketch (proportions not to scale)

### Final variants (2026-10-22)

| | **A, compact** | **B, thin** |
|---|---|---|
| Size (W × L × T) | **41 × 90.4 × 10.7 mm** | **41 × 102.4 × 8.4 mm** |
| Battery | LiPo 503450, 1000 mAh (5 × 34 × 50, ~54 mm with PCM), behind the parts | LiPo LP403759, 1000 mAh (4 × 37 × 59, ~63 mm with PCM), next to the parts |
| Layout on the back | battery over the middle, parts ≤ 1.5 mm under it | ESP32 + SD at the top, battery in the middle, power + audio at the bottom |
| USB-C | TYPE-C-31-M-12 (C165948), top mount (current part) | **TYPE-C 16P CB0.8 073 (C2906289)**, sinking 0.8 mm, made for 0.8 mm boards, ~$0.10 |
| Jack | PJ-342 (C668606), top mount (current part) | **PJ-342C CB (C49287245)**, sinking 1.25 mm, ~$0.27 |
| Port centring | USB-C +0.5 / jack −0.5 mm from centre (the two parts differ in height) | both within 0.01 mm of centre |
| Ramp width | ~8 mm (rounded corners), ~14 mm (sharp) | same |

Corner options for both: rounded (R5 plan view, 1 mm edges) or sharp (R0.6 / 0.3 mm edges). Sharp corners leave more room for the ports, so the ramp gets wider.

Trade-offs and notes:
- **B could be 7.4 mm** with the ports ~0.4 mm above centre (`center_ports=False`). Centring them costs 1 mm
- A sinking USB-C does **not** help A: it raises the port, and A's ports already sit high
- **B needs schematic changes**: PJ-342C CB is a 4-pole (TRRS) jack with a different pinout (1 MIC, 2 GND, 3 AU-R, 4 AU-L, 5 reserved, 6 HP-DET), so the jack symbol, footprint and detect circuit change. Check how HP-DET switches before drawing it. Both sinking parts need a **board cutout** (Edge.Cuts in their footprints)
- **Battery connector**: JST PH (5.5 mm tall) does not fit in B, so BT1 moves to JST SH (SM02B-SRSS-TB, ~2.9 mm)
- **Power button**: right side, just under the cap (14.6 mm from the top end, near the top of the display). EVQP7J01P side-push switch on the **back** of the PCB at the right edge: hanging under the board, its actuator sits at z 4.33 vs. mid-thickness 4.21, so the opening is centred and the printed key hides the 0.1 mm. On the front it would be 2.3 mm off centre
- **Display connector**: FH12 is 2.0 mm tall and does not fit on the front (~1.8 mm of room). Put it on the back and fold the flex around the board edge or through a slot. Decide at placement
- Catalogue cell sizes exclude the protection PCB and leads (+3–5 mm). Get the exact drawing of the chosen cell before fixing the board outline

## Schematic
One sheet per block: `usb.kicad_sch` (USB-C, ESD, CP2102N, auto-reset), `power.kicad_sch`, `esp32.kicad_sch`, `audio.kicad_sch`, `io.kicad_sch` (microSD, display, buttons, jack detect). Pin-by-pin reference: [connections.md](connections.md).

## Software
code.md
- ESP-IDF or Arduino + `arduino-audio-tools` + `ESP32-A2DP` (pschatzmann): read SD → decode MP3/FLAC → I2S (jack) or A2DP (BT headphones)

## Tests

## Resources
- datasheets: `datasheets/` (all parts + ESP32 hardware design guidelines + LS013B7DH03)
- MAX17048 (source): https://www.analog.com/media/en/technical-documentation/data-sheets/MAX17048-MAX17049.pdf
- JLC parts: https://jlcpcb.com/parts
- arduino-audio-tools: https://github.com/pschatzmann/arduino-audio-tools
- ESP32-A2DP: https://github.com/pschatzmann/ESP32-A2DP

## KiCad libraries
- `lib/mp3_player.kicad_sym` + `lib/mp3_player.pretty` + `lib/mp3_player.3dshapes`, registered in the project's `sym-lib-table` / `fp-lib-table`
- generated with `easyeda2kicad` from LCSC codes. New part: `easyeda2kicad --full --lcsc_id Cxxxx --output $PWD/lib/mp3_player --project-relative`

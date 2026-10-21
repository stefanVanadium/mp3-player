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
| jack | 3.5mm with **detect** pin (switch) | to choose (PJ-320/PJ-342 family) | — | ~$0.1 | check the datasheet for a detect contact |

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
| battery | LiPo pouch with protection | — | — | — | bought separately. e.g. 402535 (~300mAh) / 503040 (~500mAh) / 503450 (~1000mAh) |

**Soft power (BQ25180):**
- **power on**: press the button, BQ25180 leaves ship mode and powers the system
- **power off**: ESP32 sends the ship mode command over I2C; the battery is disconnected (a few nA)
- **long press**: hardware reset, in case something hangs
- dedicated alternative: LTC2954 (C683782, $6.7, expensive)

### USB-C
| What | Part | LCSC | Stock | Price | Notes |
|---|---|---|---|---|---|
| connector | TYPE-C-31-M-12 (16 pins) | C165948 | 347k | $0.19 | + 2x 5.1k on CC1/CC2 |
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
| tact buttons | to choose | SMD/THT | easy |
| 3.5mm jack with detect | to choose (PJ-320/PJ-342) | SMD/THT | easy |
| LP5907-3.3 | C80670 | SOT-23-5 | easy |
| USBLC6-2SC6 | C7519 | SOT-23-6 | easy |
| microSD push-push | C91145 (TF-01A) | SMD | medium (pins under the metal shell, lots of flux) |
| display FPC (x1, only the one used) | C506791 Hirose FH12-10S | 0.5mm | medium (drag soldering + flux + wick) |
| USB-C 16 pins | C165948 | SMD, 0.5mm pitch | **hard** — flux, fine tip, inspect for bridges under magnification |
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
- [x] **schematic done** (2026-10-21): 5 sheets (usb, power, esp32, audio, io), 112 parts, annotated. Final check on the KiCad netlist: 278/278 pin and passive checks against `connections.md` pass. ERC: only cosmetic warnings left (EasyEDA pin types, off-grid wire ends)

Next:
- [ ] assign footprints to passives (0402/0603 from the JLC basic list), D2 (SOD-123) and BT1 (battery connector)
- [ ] PCB: board outline + case, placement (antenna at the edge, audio away from ESP32 and the TPS63802 inductor), 4-layer stackup
- [ ] check the real PJ-342, TF-01A card detect and LS013 flex contact side against the footprints before ordering
- [ ] firmware bring-up (see `code.md`)

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

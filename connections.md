# Schematic connections — MP3 player

Reference for drawing and reviewing the schematic. Pins were checked one by one against the datasheets in `datasheets/` and against the pad numbers in `lib/mp3_player.pretty` (2026-10-21). Reference designators match the annotated schematic.

Sheets: `usb.kicad_sch` → `power.kicad_sch` → `esp32.kicad_sch` → `audio.kicad_sch` → `io.kicad_sch`. Nets that cross sheets use global labels. `GND`, `VBUS` and `+3V3` are power symbols.

## 1. Datasheet review

Symbols and footprints match their datasheets for: ESP32-PICO-MINI-02, PCM5122, OPA1622, LM27762, BQ25180, TPS63802, LP5907, MAX17048, CP2102N (QFN24), MMBT3904, USB-C, USBLC6, TF-01A, FH12, PJ-342.

Issues found and how they were resolved:

| # | Issue | Severity | Resolution |
|---|---|---|---|
| 1 | CP2102N in QFN20 has no DTR pin, and ESP32 auto-reset needs DTR **and** RTS | blocking | switched to **CP2102N-A02-GQFN24R** (C969151), QFN20 removed from `lib/` |
| 2 | OPA1622 thermal pad goes to **V− (−3V), not GND** | high (would short −3V) | symbol pin 11 renamed `V-(EP)`, wired to `-3V0_AMP`. PCB: −3V pour under the pad |
| 3 | GPIO12 = SD D2 has a pull-up, so MTDI reads 1 at boot and selects 1.8V flash | high | burn the eFuse once per board: `espefuse.py set_flash_voltage 3.3V` (see `code.md`) |
| 4 | GPIO2 = SD D0 has a pull-up, but download mode needs GPIO2 = 0 | medium | **D2** B5819W (C8598, basic part) from GPIO2 (anode) to GPIO0 (cathode) |
| 5 | PCM5122 needs AVDD/CPVDD ≥ 3.1–3.2V, and LP5907 from VSYS drops out below ~3.35V | low | firmware shuts down at VBAT ≈ 3.4V |
| 6 | OPA1622 on ±3V swings ~1.5 Vrms, PCM5122 outputs 2.1 Vrms | low | max digital volume capped at ~−4 dB (still >50 mW into 32Ω) |
| 7 | BQ25180 TS/MR without an NTC needs **10k to GND** or it won't charge | medium | R12 10k in parallel with the power button |
| 8 | all 21 GPIOs are used | info | for more I/O add an I2C expander (e.g. TCA9534) |
| 9 | ESP32-PICO-MINI-02 is marked NRND | info | still stocked at JLC, fine for this project |
| 10 | display: ST7567 pinout varies by seller | decision | dropped. **Sharp LS013B7DH03 only** (same display across projects, see `../PROJECTS.md`) |

Not verifiable from the datasheet, check with a multimeter on the real part:
- **PJ-342**: from the drawing, 5 and 2 = sleeve, 6 = ring (NC contact 7), 3 = tip (NC contact 4)
- **TF-01A pin 9 (CD)**: assumed to close to GND/shell when a card is inserted (active low)
- **FH12 vs LS013 flex**: Sharp recommends a top-contact connector. Check which side the contacts face

## 2. Power rails

| Net | Source | Loads |
|---|---|---|
| `VBUS` | USB-C (5V) | BQ25180 IN, USBLC6 VBUS, CP2102N VBUS divider |
| `VBAT` | LiPo + | BQ25180 BAT, MAX17048 CELL + VDD |
| `VSYS` | BQ25180 SYS (3.4–4.5V, off in ship mode) | TPS63802, LP5907, LM27762 |
| `+3V3` | TPS63802 | ESP32, CP2102N, microSD, display, PCM5122 DVDD, all pull-ups |
| `+3V3_A` | LP5907 | PCM5122 AVDD + CPVDD only |
| `+3V0_AMP` / `-3V0_AMP` | LM27762 OUT+ / OUT− | OPA1622 V+ / V− |
| `GND` | — | one solid ground plane (see section 6) |

## 3. ESP32-PICO-MINI-02 (U7) pin map

| Module pin | GPIO | Net | Notes |
|---|---|---|---|
| 3 | 3V3 | `+3V3` | 22µF + 0.1µF next to the pin |
| 1, 2, 11, 14, 36–53 | GND | `GND` | including all center pads (49) |
| 8 | EN | `ESP_EN` | 10k pull-up + 1µF on the USB sheet, Q1 collector |
| 31 | IO1 / TXD0 | `ESP_TX` | → CP2102N RXD |
| 30 | IO3 / RXD0 | `ESP_RX` | ← CP2102N TXD |
| 23 | IO0 | `ESP_BOOT` | 10k pull-up (USB sheet), Q2 collector, BOOT button, D2 cathode |
| 18 | IO14 | `SD_CLK` | SDMMC slot 1 (fixed IO_MUX pins) |
| 21 | IO15 | `SD_CMD` | 10k pull-up |
| 22 | IO2 | `SD_D0` | 10k pull-up, D2 anode |
| 24 | IO4 | `SD_D1` | 10k pull-up |
| 19 | IO12 | `SD_D2` | 10k pull-up (reason for the eFuse, issue 3) |
| 20 | IO13 | `SD_D3` | 10k pull-up |
| 35 | IO21 | `I2C_SDA` | 4.7k pull-up |
| 34 | IO22 | `I2C_SCL` | 4.7k pull-up |
| 16 | IO26 | `I2S_BCK` | → PCM5122 BCK |
| 15 | IO25 | `I2S_LRCK` | → PCM5122 LRCK |
| 17 | IO27 | `I2S_DOUT` | → PCM5122 DIN |
| 29 | IO5 | `LCD_SCK` | display SPI clock |
| 33 | IO19 | `LCD_MOSI` | display SPI data |
| 12 | IO32 | `LCD_CS` | LS013 SCS (active HIGH, handled in firmware) |
| 13 | IO33 | `LCD_DISP` | LS013 DISP, 100k pull-down so the panel stays blank until initialized |
| 26 | IO20 | `BTN_PLAY` | button to GND + 10k pull-up |
| 27 | IO7 | `AUDIO_EN` | 100k pull-down. Enables LM27762 and unmutes the DAC |
| 28 | IO8 | `PWR_INT` | 10k pull-up. BQ25180 /INT + MAX17048 ALRT (wired-OR, both open-drain) |
| 9 | I34 | `BTN_VOLUP` | input-only: **external pull-up required** (10k) |
| 10 | I35 | `BTN_VOLDN` | input-only, 10k pull-up |
| 5 | I37 | `BTN_NEXT` | input-only, 10k pull-up |
| 6 | I38 | `BTN_PREV` | input-only, 10k pull-up |
| 4 | I36 | `SD_DET` | input-only, 10k pull-up |
| 7 | I39 | `JACK_DET` | input-only (see 4.8) |
| 25, 32 | NC | — | no-connect |

GPIO36/39 can glitch briefly when WiFi/ADC is active (ESP32 errata), so they carry `SD_DET` and `JACK_DET`, which are polled with debounce, not buttons on interrupts.

All pull-ups for SD, buttons, `PWR_INT`, I2C and the `AUDIO_EN` / `LCD_DISP` pull-downs live on the ESP32 sheet.

## 4. Blocks

### 4.1 USB-C (J1) + ESD (D1)

**USB-C TYPE-C-31-M-12**
| Pin | Net |
|---|---|
| A4B9, B4A9 (VBUS) | `VBUS` |
| A1B12, B1A12 (GND) | `GND` |
| A5 (CC1) | 5.1k to GND |
| B5 (CC2) | 5.1k to GND (separate resistor) |
| A6, B6 (DP1, DP2) | `USB_DP` (tied together) |
| A7, B7 (DN1, DN2) | `USB_DN` (tied together) |
| A8, B8 (SBU) | no-connect |
| 1–4 (EH, shell) | `GND` |

**USBLC6-2SC6** (symbol pins are unnamed)
| Pin | Function | Net |
|---|---|---|
| 1, 6 | I/O1 | `USB_DP` (flow-through: in on 1, out on 6) |
| 3, 4 | I/O2 | `USB_DN` |
| 2 | GND | `GND` |
| 5 | VBUS | `VBUS` |

`VBUS`: 10µF to GND next to the connector.

### 4.2 CP2102N-A02-GQFN24 (U1), powered from +3V3

| Pin | Name | Connection |
|---|---|---|
| 3 | D+ | `USB_DP` |
| 4 | D− | `USB_DN` |
| 5 | VIO | `+3V3` |
| 6 | VDD | `+3V3`, 4.7µF + 0.1µF |
| 7 | VREGIN | `+3V3`, 4.7µF + 0.1µF (internal regulator unused) |
| 8 | VBUS | divider: `VBUS` → 22.1k → pin 8, 47.5k to GND |
| 9 | RSTb | 1k to `+3V3` |
| 2, EP (25) | GND | `GND` |
| 20 | RXD | `ESP_TX` |
| 21 | TXD | `ESP_RX` |
| 23 | DTR | auto-reset |
| 19 | RTS | auto-reset |
| 1, 10–18, 22, 24 | RI, NC, GPIO, SUSPEND, CTS, DSR, DCD | no-connect |

Why +3V3 and not VBUS: with USB unplugged and the ESP32 running, TX/RX can't back-power the CP2102N. Plugging USB in takes the BQ25180 out of ship mode, so +3V3 is always there when programming. Idle draw without USB is ~0.2 mA, only while the player is on.

### 4.3 Auto-reset + boot (Q1, Q2 = MMBT3904)

| Part | B (pin 1) | E (pin 2) | C (pin 3) |
|---|---|---|---|
| Q1 | 10k ← DTR | RTS | `ESP_EN` |
| Q2 | 10k ← RTS | DTR | `ESP_BOOT` (IO0) |

- `ESP_EN`: 10k to +3V3, 1µF to GND
- `ESP_BOOT`: 10k to +3V3
- **D2** B5819W: anode on `SD_D0` (IO2), cathode on `ESP_BOOT` (IO0). In normal operation IO0 is high and the diode is off. **Don't use IO0 for anything else**, or SD transfers get corrupted
- optional RESET button: `ESP_EN` to GND

### 4.4 Power

**BQ25180 (U2, DSBGA-8)**
| Pin | Name | Connection |
|---|---|---|
| A2 | IN | `VBUS`, 1µF/25V to GND |
| B2 | SYS | `VSYS`, 10µF/25V to GND |
| C2 | BAT | `VBAT`, 1µF to GND |
| D2 | GND | `GND` |
| B1 | SCL | `I2C_SCL` |
| C1 | SDA | `I2C_SDA` |
| A1 | /INT | `PWR_INT` |
| D1 | TS/MR | POWER button to GND **+ 10k to GND** (instead of an NTC). Button ground close to pin D2 |

I2C address 0x6A. Short press wakes from ship mode. While running, presses raise `/INT` (WAKE1/WAKE2), so the ESP32 sees the power button without a dedicated GPIO. Long press = hardware reset.

**Battery (BT1)**: 2-pin connector (e.g. JST-PH), + → `VBAT`, − → `GND`.

**TPS63802 (U4, 3.3V digital)**
| Pin | Name | Connection |
|---|---|---|
| 10 | VIN | `VSYS`, 10µF |
| 1 | EN | `VSYS` |
| 2 | MODE | `GND` (power save) |
| 9 | L1 | L1 0.47µH (WPN201610HR47MT) |
| 7 | L2 | L1 other end |
| 6 | VOUT | `+3V3`, 22µF + 0.1µF |
| 4 | FB | 511k from VOUT to FB, 91k from FB to GND → 3.31V |
| 5 | PG | 100k pull-up to +3V3 (unused otherwise) |
| 3, 8 | AGND, GND | `GND` |

Inductor check (Sunlord datasheet, H series): 0.47µH ±20%, Isat 4.0A, Irms 2.7A, DCR 49mΩ max. Load is <0.5A, plenty of margin.

**LP5907-3.3 (U6, 3.3V analog for the DAC only)**
| Pin | Connection |
|---|---|
| 1 IN | `VSYS`, 1µF |
| 3 EN | `VSYS` |
| 5 OUT | `+3V3_A`, 1µF |
| 2 GND | `GND` |
| 4 N/C | no-connect |

**LM27762 (U3, ±3V for the headphone amp)**: the datasheet example (3.3–4.2V in, ±3V out)
| Pin | Name | Connection |
|---|---|---|
| 3 | VIN | `VSYS`, 2.2µF |
| 12, 8 | EN+, EN− | `AUDIO_EN` |
| 10, 9 | C1+, C1− | 1µF between them |
| 5 | CP | 4.7µF to GND |
| 11 | OUT+ | `+3V0_AMP`, 2.2µF |
| 2 | FB+ | 150k from OUT+ to FB+, 100k from FB+ to GND → +3.00V |
| 6 | OUT− | `-3V0_AMP`, 2.2µF |
| 7 | FB− | 147k from OUT− to FB−, 100k from FB− to GND → −3.01V |
| 1 | PGOOD | `GND` (unused, per datasheet) |
| 4, EP (13) | GND | `GND` |

The bottom feedback resistors must be ≥ 50k (datasheet). Use 1% parts.

**MAX17048 (U5, fuel gauge)**
| Pin | Name | Connection |
|---|---|---|
| 2 | CELL | `VBAT` |
| 3 | VDD | `VBAT`, 0.1µF to GND |
| 1 | CTG | `GND` |
| 6 | QSTRT | `GND` |
| 4, EP (9) | GND | `GND` |
| 7 | SCL | `I2C_SCL` |
| 8 | SDA | `I2C_SDA` |
| 5 | ALRT | `PWR_INT` |

Address 0x36. It sits directly on the battery, so it stays powered in ship mode (~4µA hibernate). To get below 1µA, firmware writes `MODE.EnSleep = 1` before ship mode. Once +3V3 is gone, SDA/SCL stay low (internal pull-downs) and the gauge sleeps after ~2.5s. **Without EnSleep it never sleeps.**

### 4.5 Audio

**PCM5122 (U9, I2C mode)**
| Pin | Name | Connection |
|---|---|---|
| 1 | CPVDD | `+3V3_A`, 0.1µF + 10µF |
| 2–4 | CAPP – CAPM | 2.2µF between 2 and 4 |
| 3 | CPGND | `GND` |
| 5 | VNEG | 2.2µF to GND |
| 6 | OUTL | `DAC_L` |
| 7 | OUTR | `DAC_R` |
| 8 | AVDD | `+3V3_A`, 0.1µF + 10µF |
| 9 | AGND | `GND` |
| 10 | VCOM | `GND` (VREF mode, the default) |
| 11 | SDA | `I2C_SDA` |
| 12 | SCL | `I2C_SCL` |
| 13, 14, 15, 19 | GPIO5/4/3/6 | no-connect (internal pull-downs) |
| 16 | ADR2 | `GND` |
| 24 | ADR1 | `GND` → address 0x4C |
| 17 | MODE1 | `GND` |
| 18 | MODE2 | `+3V3` → I2C mode |
| 20 | SCK | `GND` (no MCLK, the PLL runs from BCK) |
| 21 | BCK | `I2S_BCK` |
| 22 | DIN | `I2S_DOUT` |
| 23 | LRCK | `I2S_LRCK` |
| 25 | XSMT | `AUDIO_EN` (low = mute, so the DAC is silent while the ESP32 boots) |
| 26 | LDOO | 0.1µF to GND |
| 27 | DGND | `GND` |
| 28 | DVDD | `+3V3`, 0.1µF + 10µF (digital supply kept off the clean analog rail) |

Charge-pump capacitors (CAPP/CAPM, VNEG): good ceramics (X7R/C0G), per TI.

**DAC → amp filter** (per channel):
`DAC_L` → 470Ω → `AMP_INL` → 2.2nF C0G to GND
`DAC_R` → 470Ω → `AMP_INR` → 2.2nF C0G to GND

**OPA1622 (U8)**: unity-gain buffer (unity-gain stable)
| Pin | Name | Connection |
|---|---|---|
| 1 | +INA | `AMP_INL` |
| 10 | −INA | `HP_L` (feedback straight from OUTA) |
| 9 | OUTA | `HP_L` |
| 5 | +INB | `AMP_INR` |
| 6 | −INB | `HP_R` |
| 7 | OUTB | `HP_R` |
| 2 | V+ | `+3V0_AMP`, 0.1µF + 2.2µF to GND, right at the pin |
| 4 | V− | `-3V0_AMP`, 0.1µF + 2.2µF to GND |
| 3 | GND | `GND` |
| 8 | EN | divider from V+: 20k from `+3V0_AMP` to EN, 10k from EN to GND (~1.0V, threshold 0.82V) |
| **11** | **V-(EP)** | **`-3V0_AMP`** (issue 2) |

The divider enables the amp only once the rails are almost up, so no pop (datasheet method). While `AUDIO_EN` is low, LM27762 is off and the OPA1622 is unpowered.

**Jack PJ-342 (J2)** (verify with a multimeter, see section 1)
| Pin | Role | Connection |
|---|---|---|
| 3 | Tip (L) | `HP_L`, + 10k to GND |
| 6 | Ring (R) | `HP_R`, + 10k to GND |
| 5, 2 | Sleeve | `GND` |
| 4 | tip NC contact | `JACK_SW` (detect) |
| 7 | ring NC contact | no-connect |

### 4.6 microSD (J3, TF-01A)

| Pin | Name | Connection |
|---|---|---|
| 1 | DAT2 | `SD_D2` |
| 2 | CD/DAT3 | `SD_D3` |
| 3 | CMD | `SD_CMD` |
| 4 | VDD | `+3V3`, 10µF + 0.1µF next to the slot |
| 5 | CLK | 33Ω in series to `SD_CLK` |
| 6 | VSS | `GND` |
| 7 | DAT0 | `SD_D0` |
| 8 | DAT1 | `SD_D1` |
| 9 | CD | `SD_DET` (active low, to verify) |
| 10–13 | shell | `GND` |

The 10k pull-ups on CMD and D0–D3 are on the ESP32 sheet. **No pull-up on CLK.**

### 4.7 Display: Sharp LS013B7DH03 on FH12-10S (J4)

| FPC pin | Signal | Connection |
|---|---|---|
| 1 | SCLK | `LCD_SCK` (1 MHz max on this panel) |
| 2 | SI | `LCD_MOSI` |
| 3 | SCS | `LCD_CS` |
| 4 | EXTCOMIN | `GND` (VCOM inversion done over serial) |
| 5 | DISP | `LCD_DISP` + 0.1µF to GND (Sharp recommendation) |
| 6 | VDDA | `+3V3`, ≥0.1µF |
| 7 | VDD | `+3V3`, ≥1µF |
| 8 | EXTMODE | `GND` (serial VCOM mode) |
| 9 | VSS | `GND` |
| 10 | VSSA | `GND` |
| 11, 12 | mounting tabs | `GND` |

Recommended supply is 2.7–3.3V, so 3.3V is at the top of the range but in spec.

Power-on sequence (datasheet Figure 6-1): DISP stays LOW while the pixel memory is cleared (all-clear command), then goes HIGH. That's why DISP is on a GPIO with a pull-down and not on `ESP_EN`.

### 4.8 Buttons + jack detect

All buttons are TS-1088: one pin on the net, the other to `GND`. Pull-ups are on the ESP32 sheet.

| Button | Net | Sheet |
|---|---|---|
| Play/Pause | `BTN_PLAY` (IO20) | esp32 |
| Vol+ | `BTN_VOLUP` (I34) | io |
| Vol− | `BTN_VOLDN` (I35) | io |
| Next | `BTN_NEXT` (I37) | io |
| Prev | `BTN_PREV` (I38) | io |
| Power | BQ25180 TS/MR (4.4) | power |
| Boot (hidden) | `ESP_BOOT` | esp32 |

**Jack detect**: `JACK_SW` (jack pin 4) → 100k in series → `JACK_DET` (I39), plus a 1M pull-up from `JACK_DET` to +3V3.
- no plug: pin 4 touches the tip (~0V through the 10k bleeder), so `JACK_DET` ≈ 0.3V = **LOW**
- plug in: the contact opens, so `JACK_DET` = **HIGH**
- the 100k protects the GPIO if audio plays with no plug in (the tip can swing ±2V)

## 5. Buses

| Bus | Devices |
|---|---|
| I2C (IO21/IO22, 4.7k pull-ups) | BQ25180 0x6A, MAX17048 0x36, PCM5122 0x4C, no conflicts |
| I2S (IO26/25/27) | PCM5122 |
| SDMMC 4-bit (IO14/15/2/4/12/13) | microSD |
| SPI (IO5/19/32) + DISP (IO33) | display |
| UART0 (IO1/IO3) | CP2102N |

## 6. Schematic / PCB notes

- **GND**: TI says the PCM512x uses one common ground (AGND/DGND tied). Use one solid ground plane with no split, and get the separation from placement: DAC/amp away from the ESP32 and the TPS63802 inductor, digital traces away from the analog outputs
- decoupling capacitors go right at their pins. Draw them next to the chip in the schematic so it's obvious on the PCB
- ESP32: no copper under the antenna, module at the board edge
- **before** the first flash: `espefuse.py set_flash_voltage 3.3V` (issue 3). Until then the firmware won't boot because of the D2 pull-up

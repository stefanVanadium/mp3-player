# mp3-player

![KiCad](https://img.shields.io/badge/KiCad-10-314CB0?logo=kicad&logoColor=white)
![ESP32](https://img.shields.io/badge/ESP32-PICO--MINI--02-E7352C?logo=espressif&logoColor=white)
![Status](https://img.shields.io/badge/status-schematic%20done-yellow)
![License](https://img.shields.io/badge/license-MIT-green)

A modern hi-fi music player with a retro look. It plays FLAC/WAV through a proper DAC and headphone amp, streams to Bluetooth headphones, and has a reflective display you can read in direct sunlight.

## Highlights

- **Hi-fi audio path**: PCM5122 DAC (112dB, 32-bit/384kHz) → OPA1622 headphone amp powered from clean ± rails
- **FLAC / WAV / MP3** from a push-push microSD card
- **Bluetooth A2DP** to wireless headphones (classic ESP32)
- **3.5mm jack with plug detection**
- **Sunlight-readable display**: Sharp LS013B7DH03 memory LCD, crisp in direct sun and almost zero power
- **Soft power**: one button wakes the player from ship mode, and the ESP32 turns it off
- **USB-C**: charging, programming via USB-UART with auto-reset, and ESD protection
- **Real battery percentage** from a MAX17048 fuel gauge

## How it works

```
USB-C ─ ESD ─┬─ CP2102N ── ESP32-PICO-MINI-02
             └─ BQ25180 charger ── TPS63802 3.3V digital
                                ├─ LP5907 3.3V analog
                                └─ LM27762 ± rails
ESP32 ── I2S ── PCM5122 ── OPA1622 ── 3.5mm jack
      ├─ SDMMC ── microSD
      ├─ SPI ── display
      └─ BT ── headphones
```

Full architecture, BOM with JLCPCB stock/prices, who-solders-what, cost estimate and design notes are in **[mp3_player.md](mp3_player.md)**.

## Specs (planned)

| | |
|---|---|
| MCU | ESP32-PICO-MINI-02 (8MB flash, 2MB PSRAM) |
| DAC | PCM5122, hardware volume over I2C |
| Headphone amp | OPA1622 |
| Storage | microSD, 4-bit SDMMC |
| Display | Sharp LS013B7DH03 1.28" 128x128 memory LCD |
| Battery | thin LiPo pouch, 300–1000mAh |
| Wireless | Bluetooth A2DP (SBC) |
| Board | 4-layer, assembled by JLCPCB + hand-soldered connectors |
| Prototype cost | ~$125 for 2 boards |

## Repo layout

```
mp3_player.md         project documentation (start here)
mp3_player.kicad_*    KiCad 10 project
lib/                  symbols, footprints, 3D models (generated from LCSC parts)
datasheets/           datasheets for every chosen part
connections.md        pin-by-pin schematic connections and datasheet review
code.md               firmware notes
mp3_player.tex/.pdf   printable writeup
```

## Status

- [x] Requirements, architecture, BOM
- [x] KiCad libraries + datasheets
- [x] Schematic (5 sheets: USB, power, ESP32, audio, I/O)
- [ ] PCB
- [ ] Firmware (`arduino-audio-tools` + `ESP32-A2DP`)
- [ ] Case

## License

[MIT](LICENSE) for the design files and documentation in this repo. Datasheets in `datasheets/` belong to their manufacturers. Footprints and 3D models in `lib/` were generated from EasyEDA/LCSC data.

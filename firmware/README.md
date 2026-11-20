# Firmware

Draft firmware for the MP3 player. It compiles, but has **not run on the real board yet**: the
board isn't ordered. Expect fixes at bring-up.

Built with PlatformIO on Arduino-ESP32 3.x (ESP-IDF 5), using
[arduino-audio-tools](https://github.com/pschatzmann/arduino-audio-tools) and
[ESP32-A2DP](https://github.com/pschatzmann/ESP32-A2DP). Library versions are pinned in
`platformio.ini`.

## Build and flash

```sh
pio run                      # player firmware
pio run -e bringup           # bring-up test menu
pio run -t upload            # flash over USB-C (CP2102N, auto-reset)
pio device monitor           # serial, 115200
```

**Before the first flash of a new board**, burn the flash-voltage eFuse once (see
[../code.md](../code.md)). Without it the board doesn't boot, because SD D2 pulls GPIO12 high.

## Bring-up

`pio run -e bringup -t upload`, then open the serial monitor. One key per test, in the order of
the bring-up list in [../mp3_player.md](../mp3_player.md):

| Key | Test |
|---|---|
| `i` | I2C scan: expect 0x36 (MAX17048), 0x4C (PCM5122), 0x6A (BQ25180) |
| `c` | charger status, sets the charge current to 500 mA |
| `g` | battery voltage and state of charge |
| `d` | display test pattern |
| `s` | mount the microSD in 4-bit mode, list tracks |
| `t` | 1 kHz tone on the jack at −20 dB (toggle) |
| `k` | PCM5122 clock status (register 94) |
| `b` | live buttons, card detect, jack detect, `PWR_INT` |
| `a` | toggle `AUDIO_EN` (±3 V rails) |
| `z` | ship mode (wake with the power button) |

## Controls

| Input | Action |
|---|---|
| Centre | play / pause |
| Centre, hold | switch output: jack ↔ Bluetooth |
| Top / bottom | volume (hold to repeat) |
| Right / left | next / previous track |
| Right / left, hold | skip 10 tracks |
| Left + right, hold 2 s | WiFi upload mode (on / off) |
| Power, hold 2 s | power off (ship mode) |

Unplugging the headphones pauses playback. With USB plugged in, "power off" shows a charging
screen until the cable is removed.

## Layout

```
include/pins.h        pin map (from ../connections.md, section 3)
include/config.h      charge current, volume limit, cut-off voltage, timings
src/drivers/          BQ25180, MAX17048, PCM5122 register drivers
src/hw/power.*        charger + gauge polling, power button, ship mode
src/hw/inputs.*       click wheel, card and jack detect (debounced)
src/audio/library.*   scans the card for .mp3/.flac/.wav
src/audio/player.*    decode → I2S or A2DP, in its own task on core 1
src/ui/display.*      Sharp memory LCD screens
src/net/upload.*      WiFi access point + upload page (writes to /music)
src/main.cpp          player app
src/bringup.cpp       bring-up menu (env bringup)
```

## Known gaps

- **Bluetooth**: connects to the first headphones in pairing mode. No pairing screen yet, and the
  device isn't remembered. A2DP is fixed at 44.1 kHz, so 48 kHz files need resampling (not done).
- **PCM5122 clocks**: uses the BCK PLL with clock autoset. If there is no sound, check register 94
  (`k`) and set the PLL dividers by hand (datasheet 8.3.6.4).
- **I2S** sends 16-bit words. 24-bit FLAC is reduced to 16 bit.
- **SD card detect** polarity (`SD_DET` LOW = inserted) still needs checking on the TF-01A.
- No library browser yet: tracks play in path order.

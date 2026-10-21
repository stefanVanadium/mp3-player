# Firmware notes

## First boot of a new board (once per board)
1. Plug in USB-C. Auto-reset puts the ESP32 into download mode.
2. `espefuse.py --port /dev/ttyUSB0 set_flash_voltage 3.3V`. This is irreversible, and correct for the ESP32-PICO-MINI-02 (3.3V flash). It is needed because SD D2 sits on GPIO12 (MTDI) with a pull-up, which would otherwise select 1.8V for the flash, and the board would not boot.
3. Flash the firmware normally.

## Hardware limits the firmware must respect
- max digital volume on the PCM5122 is ~−4 dB: the OPA1622 runs on ±3V and clips above ~1.5 Vrms
- shut down at VBAT ≈ 3.4V: below that LP5907 drops out and PCM5122 AVDD leaves spec
- audio on: `AUDIO_EN` (IO7) high, which enables LM27762 and unmutes XSMT. Audio off: mute via I2C first, then `AUDIO_EN` low
- `PWR_INT` (IO8) is shared by BQ25180 /INT (128µs pulse, power button WAKE1/WAKE2) and MAX17048 ALRT. Read both chips to find the source
- GPIO0 is boot-only (diode to GPIO2 = SD D0). Never drive it low at runtime
- `SD_DET` (I36) and `JACK_DET` (I39): poll with debounce (ESP32 errata glitch on GPIO36/39)
- before entering ship mode: write MAX17048 `MODE.EnSleep = 1`. The gauge sits directly on the battery, and with EnSleep set it drops to <1µA sleep once SDA/SCL go low (I2C pull-ups lose power) for >2.5s. Without it, it stays in hibernate at ~4µA
- display (LS013B7DH03): keep `LCD_DISP` (IO33) low, send the all-clear command, then set DISP high. Toggle the VCOM bit in the SPI header about once a second (EXTMODE = GND)
- I2C: BQ25180 0x6A, MAX17048 0x36, PCM5122 0x4C

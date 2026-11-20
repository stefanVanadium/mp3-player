// ESP32-PICO-MINI-02 pin map. Source of truth: ../connections.md, section 3.
#pragma once

namespace pins {
// I2C: BQ25180 (0x6A), MAX17048 (0x36), PCM5122 (0x4C)
constexpr int I2C_SDA = 21;
constexpr int I2C_SCL = 22;

// I2S to the PCM5122 (no MCLK: the DAC's PLL runs from BCK)
constexpr int I2S_BCK = 26;
constexpr int I2S_LRCK = 25;
constexpr int I2S_DOUT = 27;

// microSD: SDMMC slot 1, 4-bit, fixed IO_MUX pins (CLK 14, CMD 15, D0 2, D1 4, D2 12, D3 13)

// Sharp LS013B7DH03 memory LCD
constexpr int LCD_SCK = 5;
constexpr int LCD_MOSI = 19;
constexpr int LCD_CS = 32;    // SCS, active HIGH
constexpr int LCD_DISP = 33;  // 100k pull-down: panel blank until initialized

// Click wheel, active LOW, external 10k pull-ups (34..38 are input-only)
constexpr int BTN_PLAY = 20;
constexpr int BTN_VOLUP = 34;
constexpr int BTN_VOLDN = 35;
constexpr int BTN_NEXT = 37;
constexpr int BTN_PREV = 38;

// Audio power: HIGH enables LM27762 (+-rails for the OPA1622) and releases PCM5122 XSMT
constexpr int AUDIO_EN = 7;

// BQ25180 /INT (128 us pulse) wired-OR with MAX17048 ALRT, 10k pull-up
constexpr int PWR_INT = 8;

// Detect lines on GPIO36/39: poll with debounce (ESP32 errata), never as interrupts
constexpr int SD_DET = 36;    // LOW = card inserted (to verify on the first board)
constexpr int JACK_DET = 39;  // LOW = headphones plugged in

// GPIO0 is boot-only (diode to SD D0). Never drive it at runtime.
}  // namespace pins

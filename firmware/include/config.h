// Tunables. Hardware limits come from ../code.md.
#pragma once
#include <stdint.h>

namespace config {
// Battery: LiPo 1000 mAh, charge at 0.5C
constexpr uint16_t CHARGE_CURRENT_MA = 500;
// Below ~3.4 V the LP5907 drops out and PCM5122 AVDD leaves spec
constexpr float SHUTDOWN_VOLTAGE = 3.40f;
constexpr uint8_t LOW_BATTERY_ALERT_PCT = 5;

// Volume: PCM5122 register code, 0.5 dB per step, 0x30 = 0 dB.
// The OPA1622 on +-3 V clips above ~1.5 Vrms, so never go louder than -4 dB.
constexpr uint8_t DAC_VOLUME_MAX_CODE = 0x30 + 8;  // -4 dB
constexpr uint8_t VOLUME_STEPS = 32;               // UI steps, 1.5 dB each
constexpr uint8_t VOLUME_STEP_DB_X2 = 3;           // 1.5 dB in 0.5 dB units
constexpr uint8_t DEFAULT_VOLUME = 16;

// Music lives anywhere on the card; uploads go here
constexpr const char* UPLOAD_DIR = "/music";

// WiFi upload access point
constexpr const char* AP_SSID = "MP3-Player";
constexpr const char* AP_PASSWORD = "retroplayer";  // >= 8 chars

// Timing
constexpr uint32_t LONG_PRESS_MS = 700;
constexpr uint32_t REPEAT_MS = 150;
constexpr uint32_t DETECT_DEBOUNCE_MS = 200;
constexpr uint32_t CHARGER_POLL_MS = 1000;  // also feeds the BQ25180 I2C watchdog (160 s)
constexpr uint32_t GAUGE_POLL_MS = 5000;
constexpr uint32_t DISPLAY_REFRESH_MS = 500;  // VCOM must toggle at least ~1 Hz
}  // namespace config

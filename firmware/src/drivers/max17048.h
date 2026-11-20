// Maxim MAX17048 ModelGauge fuel gauge (1 cell).
#pragma once
#include <Wire.h>

class MAX17048 {
 public:
  static constexpr uint8_t ADDR = 0x36;

  bool begin(TwoWire& wire);
  float voltage();          // V, NAN on error
  float percent();          // %, NAN on error
  bool setEmptyAlert(uint8_t pct);  // 1..32 %
  bool alertPending();
  bool clearAlert();
  // MODE.EnSleep = 1: once SDA/SCL stay low > 2.5 s (system off) the gauge sleeps at < 1 uA.
  // Without it, it only hibernates at ~4 uA. Call before ship mode.
  bool enableSleep();

 private:
  static constexpr uint8_t VCELL = 0x02, SOC = 0x04, MODE = 0x06, VERSION = 0x08,
                           CONFIG = 0x0C, STATUS = 0x1A;
  TwoWire* wire_ = nullptr;
};

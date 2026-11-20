// Battery, charger and soft power (BQ25180 + MAX17048 on the shared I2C bus).
#pragma once
#include <Wire.h>

namespace power {

struct State {
  bool chargerOk = false;
  bool gaugeOk = false;
  bool usb = false;          // VIN power good
  bool charging = false;
  bool chargeDone = false;
  float voltage = NAN;
  float percent = NAN;
};

bool begin();          // starts Wire; true if both chips answer
void poll();           // call from the main loop
const State& state();
TwoWire& bus();

// Power button seen through BQ25180 /INT. Each returns true once per press.
bool buttonShort();    // held >= 300 ms (WAKE1)
bool buttonLong();     // held >= 2 s (WAKE2)

bool batteryCritical();  // below config::SHUTDOWN_VOLTAGE on 3 readings in a row, no USB

// Gauge to sleep, charger to ship mode. With USB plugged in the charger keeps the system
// powered until the cable is removed, so the caller shows a charging screen meanwhile.
void enterShipMode();

}  // namespace power

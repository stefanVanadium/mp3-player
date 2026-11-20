#include "power.h"
#include <Arduino.h>
#include "config.h"
#include "drivers/bq25180.h"
#include "drivers/max17048.h"
#include "pins.h"

namespace power {
namespace {

BQ25180 charger;
MAX17048 gauge;
State st;
volatile bool intFlag = false;
bool shortPending = false, longPending = false;
uint32_t lastCharger = 0, lastGauge = 0;
uint8_t lowCount = 0;

void IRAM_ATTR onInt() { intFlag = true; }

void readCharger() {
  if (!st.chargerOk) return;
  BQ25180::Status s;
  if (!charger.readStatus(s)) return;
  st.usb = s.vinGood;
  st.charging = s.charge == BQ25180::ChargeState::ConstantCurrent ||
                s.charge == BQ25180::ChargeState::ConstantVoltage;
  st.chargeDone = s.vinGood && s.charge == BQ25180::ChargeState::DoneOrDisabled;
  if (s.wake2) longPending = true;
  else if (s.wake1) shortPending = true;
  // After a watchdog expiry the charger is back at 10 mA: put the current back
  if (charger.chargeCurrent() != config::CHARGE_CURRENT_MA)
    charger.setChargeCurrent(config::CHARGE_CURRENT_MA);
}

void readGauge() {
  if (!st.gaugeOk) return;
  st.voltage = gauge.voltage();
  st.percent = gauge.percent();
  if (!st.usb && st.voltage < config::SHUTDOWN_VOLTAGE) {
    if (lowCount < 255) lowCount++;
  } else {
    lowCount = 0;
  }
}

}  // namespace

TwoWire& bus() { return Wire; }

bool begin() {
  Wire.begin(pins::I2C_SDA, pins::I2C_SCL, 400000);
  st.chargerOk = charger.begin(Wire, config::CHARGE_CURRENT_MA);
  st.gaugeOk = gauge.begin(Wire);
  if (st.gaugeOk) {
    gauge.setEmptyAlert(config::LOW_BATTERY_ALERT_PCT);
    gauge.clearAlert();
  }
  pinMode(pins::PWR_INT, INPUT);  // external 10k pull-up
  attachInterrupt(digitalPinToInterrupt(pins::PWR_INT), onInt, FALLING);
  readCharger();
  shortPending = longPending = false;  // the press that woke us up
  readGauge();
  return st.chargerOk && st.gaugeOk;
}

void poll() {
  uint32_t now = millis();
  // /INT is shared: on a pulse read both chips to find the source
  if (intFlag) {
    intFlag = false;
    readCharger();
    if (st.gaugeOk && gauge.alertPending()) {
      gauge.clearAlert();
      readGauge();
    }
    lastCharger = now;
  }
  if (now - lastCharger >= config::CHARGER_POLL_MS) {
    lastCharger = now;
    readCharger();
  }
  if (now - lastGauge >= config::GAUGE_POLL_MS) {
    lastGauge = now;
    readGauge();
  }
}

const State& state() { return st; }

bool buttonShort() {
  bool r = shortPending;
  shortPending = false;
  return r;
}

bool buttonLong() {
  bool r = longPending;
  longPending = false;
  return r;
}

bool batteryCritical() { return lowCount >= 3; }

void enterShipMode() {
  if (st.gaugeOk) gauge.enableSleep();
  if (st.chargerOk) charger.enterShipMode();
}

}  // namespace power

#include "bq25180.h"
#include "i2c_regs.h"

bool BQ25180::begin(TwoWire& wire, uint16_t chargeCurrentMa) {
  wire_ = &wire;
  uint8_t id;
  if (!i2c::read8(*wire_, ADDR, MASK_ID, id)) return false;
  // SHIP_RST: EN_RST_SHIP = 00, PB_LPRESS_ACTION = 10 (long press = ship mode, hardware
  // fallback if the firmware hangs), WAKE1 = 300 ms, WAKE2 = 2 s, EN_PUSH = 1
  i2c::write8(*wire_, ADDR, SHIP_RST, 0b0'00'10'0'0'1);
  // IC_CTRL keeps its reset value 0x84: TS on (R12 stands in for the NTC), 6 h safety timer,
  // watchdog 160 s "registers back to default". The 1 s status poll keeps it fed; if the
  // firmware stops talking, the charge current falls back to the safe 10 mA default.
  return setChargeCurrent(chargeCurrentMa);
}

// ICHG code: <= 35 mA -> code + 5 mA; above -> 40 + (code - 31) * 10 mA; max 1000 mA
bool BQ25180::setChargeCurrent(uint16_t mA) {
  if (mA < 5) mA = 5;
  if (mA > 1000) mA = 1000;
  uint8_t code = (mA <= 35) ? (mA - 5) : (uint8_t)((mA - 40) / 10 + 31);
  return i2c::write8(*wire_, ADDR, ICHG_CTRL, code & 0x7F);  // CHG_DIS = 0
}

uint16_t BQ25180::chargeCurrent() {
  uint8_t v;
  if (!i2c::read8(*wire_, ADDR, ICHG_CTRL, v)) return 0;
  uint8_t code = v & 0x7F;
  return code <= 30 ? code + 5 : 40 + (code - 31) * 10;
}

bool BQ25180::readStatus(Status& s) {
  uint8_t st0, st1, fl0;
  if (!i2c::read8(*wire_, ADDR, STAT0, st0)) return false;
  if (!i2c::read8(*wire_, ADDR, STAT1, st1)) return false;
  if (!i2c::read8(*wire_, ADDR, FLAG0, fl0)) return false;
  s.vinGood = st0 & 0x01;
  s.thermalReg = st0 & 0x02;
  s.charge = (ChargeState)((st0 >> 5) & 0x03);
  s.tsOpen = st0 & 0x80;
  s.batteryUvlo = st1 & 0x40;
  s.wake1 = st1 & 0x02;
  s.wake2 = st1 & 0x01;
  s.faults = fl0;
  return true;
}

bool BQ25180::enterShipMode() {
  // EN_RST_SHIP = 10: ship mode, wake on button press or adapter insert
  return i2c::write8(*wire_, ADDR, SHIP_RST, 0b0'10'10'0'0'1);
}

bool BQ25180::hardwareReset() {
  return i2c::write8(*wire_, ADDR, SHIP_RST, 0b0'11'10'0'0'1);
}

#include "max17048.h"
#include <math.h>
#include "i2c_regs.h"

bool MAX17048::begin(TwoWire& wire) {
  wire_ = &wire;
  uint16_t ver;
  if (!i2c::read16(*wire_, ADDR, VERSION, ver)) return false;
  return (ver & 0xFFF0) == 0x0010;
}

float MAX17048::voltage() {
  uint16_t v;
  if (!i2c::read16(*wire_, ADDR, VCELL, v)) return NAN;
  return v * 78.125e-6f;
}

float MAX17048::percent() {
  uint16_t v;
  if (!i2c::read16(*wire_, ADDR, SOC, v)) return NAN;
  float p = v / 256.0f;
  return p > 100.0f ? 100.0f : p;
}

// CONFIG LSB: SLEEP(7) ALSC(6) ALRT(5) ATHD(4:0), ATHD = 32 - pct
bool MAX17048::setEmptyAlert(uint8_t pct) {
  if (pct < 1) pct = 1;
  if (pct > 32) pct = 32;
  uint16_t cfg;
  if (!i2c::read16(*wire_, ADDR, CONFIG, cfg)) return false;
  cfg = (cfg & 0xFFE0) | (32 - pct);
  return i2c::write16(*wire_, ADDR, CONFIG, cfg);
}

bool MAX17048::alertPending() {
  uint16_t cfg;
  return i2c::read16(*wire_, ADDR, CONFIG, cfg) && (cfg & 0x0020);
}

bool MAX17048::clearAlert() {
  uint16_t cfg, st;
  if (!i2c::read16(*wire_, ADDR, STATUS, st)) return false;
  i2c::write16(*wire_, ADDR, STATUS, st & 0x00FF);  // clear the flags in the MSB
  if (!i2c::read16(*wire_, ADDR, CONFIG, cfg)) return false;
  return i2c::write16(*wire_, ADDR, CONFIG, cfg & ~0x0020);
}

bool MAX17048::enableSleep() {
  return i2c::write16(*wire_, ADDR, MODE, 0x2000);  // bit 13 = EnSleep
}

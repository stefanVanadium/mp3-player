// Small register helpers shared by the I2C drivers.
#pragma once
#include <Wire.h>

namespace i2c {

inline bool present(TwoWire& w, uint8_t addr) {
  w.beginTransmission(addr);
  return w.endTransmission() == 0;
}

inline bool write8(TwoWire& w, uint8_t addr, uint8_t reg, uint8_t val) {
  w.beginTransmission(addr);
  w.write(reg);
  w.write(val);
  return w.endTransmission() == 0;
}

inline bool read8(TwoWire& w, uint8_t addr, uint8_t reg, uint8_t& val) {
  w.beginTransmission(addr);
  w.write(reg);
  if (w.endTransmission(false) != 0) return false;
  if (w.requestFrom(addr, (uint8_t)1) != 1) return false;
  val = w.read();
  return true;
}

// MAX17048 registers are 16-bit, MSB first
inline bool write16(TwoWire& w, uint8_t addr, uint8_t reg, uint16_t val) {
  w.beginTransmission(addr);
  w.write(reg);
  w.write(val >> 8);
  w.write(val & 0xFF);
  return w.endTransmission() == 0;
}

inline bool read16(TwoWire& w, uint8_t addr, uint8_t reg, uint16_t& val) {
  w.beginTransmission(addr);
  w.write(reg);
  if (w.endTransmission(false) != 0) return false;
  if (w.requestFrom(addr, (uint8_t)2) != 2) return false;
  val = (uint16_t)w.read() << 8;
  val |= w.read();
  return true;
}

}  // namespace i2c

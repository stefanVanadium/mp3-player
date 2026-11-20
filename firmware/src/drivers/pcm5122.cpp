#include "pcm5122.h"
#include "i2c_regs.h"

bool PCM5122::write(uint8_t reg, uint8_t val) { return i2c::write8(*wire_, ADDR, reg, val); }

bool PCM5122::begin(TwoWire& wire) {
  wire_ = &wire;
  if (!i2c::present(*wire_, ADDR)) return false;
  bool ok = true;
  ok &= write(0, 0x00);    // page 0
  ok &= write(2, 0x10);    // RQST: standby while configuring
  ok &= write(1, 0x11);    // reset registers and modules
  ok &= write(1, 0x00);
  ok &= write(3, 0x11);    // mute L+R until audio is started
  // No SCK on this board. PLL reference = BCK (SREF = 001), and don't raise clock errors for
  // the missing SCK (IDSK) or SCK halt (IDCH). Clock autoset stays on (DCAS = 0).
  // If there is no sound at bring-up, check register 94 (bring-up menu "k") and fall back to manual PLL dividers
  // (datasheet 8.3.6.4).
  ok &= write(37, 0x18);
  ok &= write(13, 0x10);
  ok &= write(4, 0x01);    // PLLE
  ok &= write(40, 0x00);   // I2S, 16-bit words (BCK = 32 fs, inside Table 33)
  ok &= setVolumeCode(0xFF);
  ok &= write(2, 0x00);    // run
  return ok;
}

bool PCM5122::setVolumeCode(uint8_t code) {
  if (code < maxCode) code = maxCode;
  return write(61, code) && write(62, code);
}

bool PCM5122::mute(bool on) { return write(3, on ? 0x11 : 0x00); }

bool PCM5122::standby(bool on) { return write(2, on ? 0x10 : 0x00); }

uint8_t PCM5122::clockErrors() {
  uint8_t v;
  return i2c::read8(*wire_, ADDR, 94, v) ? v : 0xFF;
}

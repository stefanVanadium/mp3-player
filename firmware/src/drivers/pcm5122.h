// TI PCM5122 DAC in software (I2C) mode, 3-wire I2S: the PLL runs from BCK.
#pragma once
#include <Wire.h>

class PCM5122 {
 public:
  static constexpr uint8_t ADDR = 0x4C;  // ADR1 = ADR2 = 0

  bool begin(TwoWire& wire);
  // Raw register code: 0x30 = 0 dB, +1 = -0.5 dB, 0xFF = mute. Clamped to maxCode.
  bool setVolumeCode(uint8_t code);
  bool mute(bool on);       // soft mute, ramps per register 63
  bool standby(bool on);
  // Page 0 / Register 94, 0xFF on I2C error. Bit 6 (CDST) = 1 is expected here: no SCK.
  // Bit 5 PLL-L, bits 3..0 = SCK/BCK/fS validity (datasheet Table 107).
  uint8_t clockErrors();

  uint8_t maxCode = 0x30;   // loudest allowed code, set from config

 private:
  bool write(uint8_t reg, uint8_t val);
  TwoWire* wire_ = nullptr;
};

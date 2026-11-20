// Bring-up firmware (pio run -e bringup): a serial menu that tests one block at a time,
// in the order of the bring-up list in ../mp3_player.md. 115200 baud.
#ifdef BRINGUP
#include <Arduino.h>
#include <SD_MMC.h>
#include "AudioTools.h"
#include "AudioTools/Communication/A2DPStream.h"
#include "audio/library.h"
#include "config.h"
#include "drivers/bq25180.h"
#include "drivers/max17048.h"
#include "drivers/pcm5122.h"
#include "hw/inputs.h"
#include "hw/power.h"
#include "pins.h"
#include "ui/display.h"

namespace {

PCM5122 dac;
BQ25180 charger;
MAX17048 gauge;
I2SStream i2s;
SineWaveGenerator<int16_t> sine(8000);  // amplitude ~ -12 dBFS
GeneratedSoundStream<int16_t> tone(sine);
StreamCopy copier;
bool toneOn = false;
bool watchInputs = false;

void menu() {
  Serial.println();
  Serial.println("MP3 player bring-up");
  Serial.println(" i  I2C scan (expect 0x36 gauge, 0x4C DAC, 0x6A charger)");
  Serial.println(" c  charger status + set charge current");
  Serial.println(" g  fuel gauge");
  Serial.println(" d  display test pattern");
  Serial.println(" s  microSD: mount 4-bit, list tracks");
  Serial.println(" t  1 kHz tone on the jack (toggle)");
  Serial.println(" k  DAC clock status (register 94)");
  Serial.println(" b  watch buttons + detect lines (toggle)");
  Serial.println(" a  AUDIO_EN toggle");
  Serial.println(" z  ship mode (power off; press the power button to wake)");
  Serial.println(" h  this menu");
}

void scan() {
  for (uint8_t a = 1; a < 127; a++) {
    Wire.beginTransmission(a);
    if (Wire.endTransmission() == 0) Serial.printf("  found 0x%02X\n", a);
  }
}

void chargerStatus() {
  if (!charger.begin(Wire, config::CHARGE_CURRENT_MA)) {
    Serial.println("  BQ25180 not answering");
    return;
  }
  BQ25180::Status s;
  charger.readStatus(s);
  static const char* states[] = {"not charging", "CC", "CV", "done/disabled"};
  Serial.printf("  VIN good %d, %s, ICHG %u mA, TS open %d, thermal %d, BUVLO %d, FLAG0 0x%02X\n",
                s.vinGood, states[(int)s.charge], charger.chargeCurrent(), s.tsOpen,
                s.thermalReg, s.batteryUvlo, s.faults);
}

void gaugeStatus() {
  if (!gauge.begin(Wire)) {
    Serial.println("  MAX17048 not answering");
    return;
  }
  Serial.printf("  %.3f V, %.1f %%\n", gauge.voltage(), gauge.percent());
}

void sdTest() {
  Library lib;
  int n = lib.scan();
  Serial.printf("  card type %d, %llu MB, %d tracks\n", SD_MMC.cardType(),
                SD_MMC.cardSize() / (1024 * 1024), n);
  for (int i = 0; i < n && i < 20; i++) Serial.printf("  %s\n", lib.path(i));
}

void toggleTone() {
  toneOn = !toneOn;
  if (toneOn) {
    auto cfg = i2s.defaultConfig(TX_MODE);
    cfg.pin_bck = pins::I2S_BCK;
    cfg.pin_ws = pins::I2S_LRCK;
    cfg.pin_data = pins::I2S_DOUT;
    cfg.pin_mck = -1;
    cfg.sample_rate = 44100;
    cfg.channels = 2;
    cfg.bits_per_sample = 16;
    cfg.use_apll = true;
    i2s.begin(cfg);
    sine.begin(cfg, 1000);
    tone.begin(cfg);
    copier.begin(i2s, tone);
    delay(50);  // let the PLL lock before unmuting
    dac.maxCode = config::DAC_VOLUME_MAX_CODE;
    dac.begin(Wire);
    digitalWrite(pins::AUDIO_EN, HIGH);
    delay(50);
    dac.setVolumeCode(0x30 + 40);  // -20 dB: safe on headphones
    dac.mute(false);
    Serial.println("  tone on (-20 dB DAC volume)");
  } else {
    dac.mute(true);
    delay(30);
    digitalWrite(pins::AUDIO_EN, LOW);
    i2s.end();
    Serial.println("  tone off");
  }
}

}  // namespace

void setup() {
  pinMode(pins::AUDIO_EN, OUTPUT);
  digitalWrite(pins::AUDIO_EN, LOW);
  Serial.begin(115200);
  delay(200);
  power::begin();
  inputs::begin();
  menu();
}

void loop() {
  if (toneOn) copier.copy();
  if (watchInputs) {
    static uint32_t last = 0;
    inputs::poll();
    if (millis() - last > 200) {
      last = millis();
      Serial.printf("  buttons 0x%02X  SD %s  jack %s  PWR_INT %d\n", inputs::rawButtons(),
                    inputs::sdInserted() ? "in" : "out", inputs::headphonesIn() ? "in" : "out",
                    digitalRead(pins::PWR_INT));
    }
  }
  if (!Serial.available()) return;
  char c = Serial.read();
  switch (c) {
    case 'i': scan(); break;
    case 'c': chargerStatus(); break;
    case 'g': gaugeStatus(); break;
    case 'd':
      ui::begin();
      ui::testPattern();
      ui::tick();
      Serial.println("  pattern drawn");
      break;
    case 's': sdTest(); break;
    case 't': toggleTone(); break;
    case 'k': Serial.printf("  reg94 = 0x%02X (bit 6 = no SCK, expected; see Table 107)\n", dac.clockErrors()); break;
    case 'b': watchInputs = !watchInputs; break;
    case 'a':
      digitalWrite(pins::AUDIO_EN, !digitalRead(pins::AUDIO_EN));
      Serial.printf("  AUDIO_EN = %d\n", digitalRead(pins::AUDIO_EN));
      break;
    case 'z':
      Serial.println("  ship mode");
      Serial.flush();
      power::enterShipMode();
      break;
    case 'h': menu(); break;
    default: break;
  }
}
#endif  // BRINGUP

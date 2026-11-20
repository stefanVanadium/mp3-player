// MP3 player firmware: playback, UI, power. Build env "bringup" for the test menu instead.
#ifndef BRINGUP
#include <Arduino.h>
#include <Preferences.h>
#include "audio/library.h"
#include "audio/player.h"
#include "config.h"
#include "drivers/pcm5122.h"
#include "hw/inputs.h"
#include "hw/power.h"
#include "net/upload.h"
#include "pins.h"
#include "ui/display.h"

namespace {

enum class Mode { Player, Upload, Charging };

Mode mode = Mode::Player;
Library library;
PCM5122 dac;
Preferences prefs;
uint8_t volume = config::DEFAULT_VOLUME;
audio::Output output = audio::Output::Jack;
bool audioPowered = false;
bool cardWasIn = true;
uint32_t lastDraw = 0;

uint8_t volumeCode(uint8_t v) {
  if (v == 0) return 0xFF;  // mute
  return config::DAC_VOLUME_MAX_CODE + (config::VOLUME_STEPS - v) * config::VOLUME_STEP_DB_X2;
}

void applyVolume() {
  if (output == audio::Output::Jack)
    dac.setVolumeCode(volumeCode(volume));
  else
    audio::setSoftVolume((float)volume / config::VOLUME_STEPS);
}

// AUDIO_EN powers the headphone amp rails and releases XSMT. Mute over I2C around it
// so switching never pops.
void setAudioPower(bool on) {
  if (on == audioPowered) return;
  if (on) {
    dac.mute(true);
    digitalWrite(pins::AUDIO_EN, HIGH);
    delay(50);  // LM27762 rails up
    applyVolume();
    dac.mute(false);
  } else {
    dac.mute(true);
    delay(30);  // soft mute ramp
    digitalWrite(pins::AUDIO_EN, LOW);
  }
  audioPowered = on;
}

void updateAudioPower() {
  setAudioPower(mode == Mode::Player && output == audio::Output::Jack && inputs::headphonesIn());
}

void saveState() {
  prefs.putUChar("vol", volume);
  prefs.putUChar("out", (uint8_t)output);
  prefs.putInt("track", audio::snapshot().index);
}

void drawPlayer() {
  ui::PlayerView v;
  v.audio = audio::snapshot();
  v.index = v.audio.index;
  v.count = library.count();
  v.title = library.title(v.index);
  v.volume = volume;
  v.headphones = inputs::headphonesIn();
  ui::showPlayer(v, power::state());
}

void powerOff(const char* why) {
  audio::pause();
  saveState();
  setAudioPower(false);
  dac.standby(true);
  ui::showMessage(why);
  ui::tick();
  delay(800);
  if (power::state().usb) {
    // The charger keeps the system up while USB is in: stay on the charging screen
    // and drop into ship mode when the cable goes.
    mode = Mode::Charging;
    return;
  }
  ui::off();
  power::enterShipMode();
  for (;;) delay(1000);  // the battery FET opens and power goes away
}

void enterUpload() {
  audio::pause();
  if (output == audio::Output::Bluetooth) {
    output = audio::Output::Jack;  // free the radio for WiFi
    audio::setOutput(output);
  }
  mode = Mode::Upload;
  updateAudioPower();
  if (upload::begin())
    ui::showUpload(config::AP_SSID, config::AP_PASSWORD, upload::ip());
  else
    ui::showMessage("WiFi failed");
}

void leaveUpload() {
  upload::end();
  mode = Mode::Player;
  if (upload::changed()) audio::reload();
  updateAudioPower();
}

void handlePlayer(inputs::Event e) {
  using inputs::Event;
  switch (e) {
    case Event::PlayShort:
      audio::toggle();
      break;
    case Event::PlayLong:
      output = output == audio::Output::Jack ? audio::Output::Bluetooth : audio::Output::Jack;
      audio::setOutput(output);
      updateAudioPower();
      applyVolume();
      break;
    case Event::VolUp:
      if (volume < config::VOLUME_STEPS) volume++;
      applyVolume();
      break;
    case Event::VolDown:
      if (volume > 0) volume--;
      applyVolume();
      break;
    case Event::NextShort:
      audio::next();
      break;
    case Event::PrevShort:
      audio::previous();
      break;
    case Event::NextLong:
      audio::select(audio::snapshot().index + 10);
      break;
    case Event::PrevLong:
      audio::select(audio::snapshot().index - 10);
      break;
    case Event::PrevNextLong:
      enterUpload();
      break;
    default:
      break;
  }
}

}  // namespace

void setup() {
  pinMode(pins::AUDIO_EN, OUTPUT);
  digitalWrite(pins::AUDIO_EN, LOW);
  Serial.begin(115200);

  power::begin();
  inputs::begin();
  ui::begin();
  ui::showMessage("Starting...");
  ui::tick();

  dac.maxCode = config::DAC_VOLUME_MAX_CODE;
  if (!dac.begin(power::bus())) Serial.println("PCM5122 not found");

  prefs.begin("player");
  volume = prefs.getUChar("vol", config::DEFAULT_VOLUME);
  output = (audio::Output)prefs.getUChar("out", 0);
  int track = prefs.getInt("track", 0);

  if (library.scan() == 0) ui::showMessage("No music found", "Hold PREV+NEXT");
  if (track >= library.count()) track = 0;
  audio::begin(library, output, track);
  applyVolume();
  updateAudioPower();
}

void loop() {
  power::poll();
  const power::State& p = power::state();
  inputs::Event e = inputs::poll();

  if (power::buttonLong()) powerOff("Bye");
  if (power::batteryCritical()) powerOff("Battery empty");

  switch (mode) {
    case Mode::Player: {
      handlePlayer(e);
      // Headphones pulled out: pause, like every player does
      bool hp = inputs::headphonesIn();
      if (!hp && output == audio::Output::Jack && audio::snapshot().playing) audio::pause();
      updateAudioPower();
      bool card = inputs::sdInserted();
      if (card && !cardWasIn) audio::reload();
      if (!card && cardWasIn) audio::pause();
      cardWasIn = card;
      if (millis() - lastDraw > 250) {
        lastDraw = millis();
        if (card || library.count()) drawPlayer();
        else ui::showMessage("No card");
      }
      break;
    }
    case Mode::Upload:
      upload::poll();
      if (e == inputs::Event::PrevNextLong) leaveUpload();
      break;
    case Mode::Charging:
      if (millis() - lastDraw > 1000) {
        lastDraw = millis();
        ui::showCharging(p);
      }
      if (!p.usb) {
        ui::off();
        power::enterShipMode();
        for (;;) delay(1000);
      }
      if (power::buttonShort()) ESP.restart();  // back on
      break;
  }

  ui::tick();
  delay(5);
}
#endif  // BRINGUP

// Sharp LS013B7DH03 128x128 memory LCD and the screens drawn on it.
#pragma once
#include <Arduino.h>
#include "audio/player.h"
#include "hw/power.h"

namespace ui {

bool begin();
void tick();  // call from the loop: pushes changes and keeps VCOM toggling
void off();   // blank the panel and drop DISP before power-off

struct PlayerView {
  String title;
  int index;
  int count;
  audio::Snapshot audio;
  uint8_t volume;  // 0..config::VOLUME_STEPS
  bool headphones;
};

void showPlayer(const PlayerView& v, const power::State& p);
void showMessage(const char* line1, const char* line2 = nullptr);
void showUpload(const String& ssid, const String& password, const String& ip);
void showCharging(const power::State& p);  // "off" while USB keeps the system powered
void testPattern();

}  // namespace ui

#include "inputs.h"
#include <Arduino.h>
#include "config.h"
#include "pins.h"

namespace inputs {
namespace {

enum Btn : uint8_t { PLAY, VOLUP, VOLDN, NEXT, PREV, COUNT };
constexpr int kPins[COUNT] = {pins::BTN_PLAY, pins::BTN_VOLUP, pins::BTN_VOLDN, pins::BTN_NEXT,
                              pins::BTN_PREV};
constexpr uint32_t kDebounceMs = 20;
constexpr uint32_t kComboMs = 2000;

struct Button {
  bool down = false;        // debounced
  bool raw = false;
  uint32_t rawSince = 0;
  uint32_t downSince = 0;
  uint32_t lastRepeat = 0;
  bool longFired = false;
  bool suppressed = false;  // part of a combo: no single events until released
};

struct Detect {
  bool level = true;
  bool raw = true;
  uint32_t rawSince = 0;
};

Button btn[COUNT];
Detect sdDet, jackDet;
bool comboFired = false;

Event queue[8];
uint8_t qHead = 0, qTail = 0;

void push(Event e) {
  uint8_t next = (qTail + 1) % 8;
  if (next == qHead) return;  // full: drop
  queue[qTail] = e;
  qTail = next;
}

void pollDetect(Detect& d, int pin, uint32_t now) {
  bool r = digitalRead(pin);
  if (r != d.raw) {
    d.raw = r;
    d.rawSince = now;
  } else if (r != d.level && now - d.rawSince >= config::DETECT_DEBOUNCE_MS) {
    d.level = r;
  }
}

void onPress(int i, uint32_t now) {
  if (i == VOLUP) push(Event::VolUp);
  if (i == VOLDN) push(Event::VolDown);
  btn[i].lastRepeat = now;
}

void onHold(int i, uint32_t now) {
  Button& b = btn[i];
  uint32_t held = now - b.downSince;
  if (i == VOLUP || i == VOLDN) {
    if (held >= config::LONG_PRESS_MS && now - b.lastRepeat >= config::REPEAT_MS) {
      b.lastRepeat = now;
      push(i == VOLUP ? Event::VolUp : Event::VolDown);
    }
    return;
  }
  if (!b.longFired && held >= config::LONG_PRESS_MS) {
    b.longFired = true;
    if (i == PLAY) push(Event::PlayLong);
    if (i == NEXT) push(Event::NextLong);
    if (i == PREV) push(Event::PrevLong);
  }
}

void onRelease(int i) {
  Button& b = btn[i];
  if (b.longFired) return;
  if (i == PLAY) push(Event::PlayShort);
  if (i == NEXT) push(Event::NextShort);
  if (i == PREV) push(Event::PrevShort);
}

}  // namespace

void begin() {
  for (int p : kPins) pinMode(p, INPUT);  // external pull-ups
  pinMode(pins::SD_DET, INPUT);
  pinMode(pins::JACK_DET, INPUT);
  sdDet.level = sdDet.raw = digitalRead(pins::SD_DET);
  jackDet.level = jackDet.raw = digitalRead(pins::JACK_DET);
}

Event poll() {
  uint32_t now = millis();
  for (int i = 0; i < COUNT; i++) {
    Button& b = btn[i];
    bool r = digitalRead(kPins[i]) == LOW;
    if (r != b.raw) {
      b.raw = r;
      b.rawSince = now;
    } else if (r != b.down && now - b.rawSince >= kDebounceMs) {
      b.down = r;
      if (r) {
        b.downSince = now;
        b.longFired = false;
        if (!b.suppressed) onPress(i, now);
      } else {
        if (!b.suppressed) onRelease(i);
        b.suppressed = false;
      }
    } else if (b.down && !b.suppressed) {
      onHold(i, now);
    }
  }

  // PREV + NEXT together: a combo, not two long presses
  if (btn[NEXT].down && btn[PREV].down) {
    btn[NEXT].suppressed = btn[PREV].suppressed = true;
    uint32_t since = max(btn[NEXT].downSince, btn[PREV].downSince);
    if (!comboFired && now - since >= kComboMs) {
      comboFired = true;
      push(Event::PrevNextLong);
    }
  } else {
    comboFired = false;
  }

  pollDetect(sdDet, pins::SD_DET, now);
  pollDetect(jackDet, pins::JACK_DET, now);

  if (qHead == qTail) return Event::None;
  Event e = queue[qHead];
  qHead = (qHead + 1) % 8;
  return e;
}

bool sdInserted() { return !sdDet.level; }
bool headphonesIn() { return !jackDet.level; }

uint8_t rawButtons() {
  uint8_t m = 0;
  for (int i = 0; i < COUNT; i++)
    if (digitalRead(kPins[i]) == LOW) m |= 1 << i;
  return m;
}

}  // namespace inputs

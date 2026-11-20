// Click wheel buttons and the two detect lines.
#pragma once
#include <stdint.h>

namespace inputs {

enum class Event : uint8_t {
  None,
  PlayShort,
  PlayLong,
  VolUp,      // on press, then repeats while held
  VolDown,
  NextShort,
  NextLong,
  PrevShort,
  PrevLong,
  PrevNextLong,  // PREV + NEXT held together for 2 s
};

void begin();
// Call often (every few ms) from the main loop; returns one queued event per call.
Event poll();
bool sdInserted();
bool headphonesIn();
// Raw levels for the bring-up menu
uint8_t rawButtons();

}  // namespace inputs

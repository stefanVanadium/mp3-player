// Playback: Library -> MP3/FLAC/WAV decoder -> I2S (jack, PCM5122) or A2DP (Bluetooth).
// Runs in its own task on core 1; the rest of the firmware talks to it through commands.
#pragma once
#include <stdint.h>

class Library;

namespace audio {

enum class Output : uint8_t { Jack, Bluetooth };

struct Snapshot {
  bool playing = false;
  int index = 0;
  Output output = Output::Jack;
  bool btConnected = false;
  uint32_t sampleRate = 0;
};

bool begin(Library& lib, Output out, int startIndex);
void play();
void pause();
void toggle();
void next();
void previous();
void select(int index);
void setOutput(Output out);
// Software volume 0..1, used only on Bluetooth (the jack uses the DAC's hardware volume)
void setSoftVolume(float v);
// Re-reads the library after an upload; stops playback
void reload();
Snapshot snapshot();

}  // namespace audio

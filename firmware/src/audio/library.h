// Music library on the microSD card: every .mp3/.flac/.wav found under the root,
// sorted by path. Implements the audio-tools AudioSource used by the AudioPlayer.
#pragma once
#include <FS.h>
#include <vector>
#include "AudioTools/Disk/AudioSource.h"

class Library : public audio_tools::AudioSource {
 public:
  // Mounts the card (4-bit SDMMC) if needed and scans it. Returns the track count.
  int scan(const char* root = "/");
  int count() const { return (int)paths_.size(); }
  const char* path(int i) const;
  String title(int i) const;  // file name without folder and extension

  // AudioSource
  bool begin() override { return !paths_.empty(); }
  Stream* nextStream(int offset) override;
  Stream* selectStream(int index) override;
  Stream* selectStream(const char* path) override;
  int index() override { return index_; }
  const char* toStr() override { return path(index_); }

 private:
  void walk(fs::File dir, int depth);
  std::vector<String> paths_;
  fs::File file_;
  int index_ = 0;
};

bool mountCard();

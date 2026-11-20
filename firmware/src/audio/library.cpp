#include "library.h"
#include <SD_MMC.h>
#include <algorithm>

namespace {
bool isAudio(const String& name) {
  String n = name;
  n.toLowerCase();
  return n.endsWith(".mp3") || n.endsWith(".flac") || n.endsWith(".wav");
}
}  // namespace

bool mountCard() {
  // 4-bit mode. GPIO12 (D2) needs the flash-voltage eFuse burned, see ../code.md
  if (SD_MMC.cardType() != CARD_NONE) return true;
  return SD_MMC.begin("/sdcard", false);
}

int Library::scan(const char* root) {
  paths_.clear();
  index_ = 0;
  if (!mountCard()) return 0;
  fs::File dir = SD_MMC.open(root);
  if (dir && dir.isDirectory()) walk(dir, 0);
  std::sort(paths_.begin(), paths_.end(),
            [](const String& a, const String& b) { return a.compareTo(b) < 0; });
  return count();
}

void Library::walk(fs::File dir, int depth) {
  if (depth > 6) return;
  for (fs::File f = dir.openNextFile(); f; f = dir.openNextFile()) {
    String name = f.name();
    if (name.startsWith(".")) continue;  // hidden files, macOS "._" junk
    if (f.isDirectory()) {
      walk(f, depth + 1);
    } else if (isAudio(name)) {
      paths_.push_back(String(f.path()));
    }
  }
}

const char* Library::path(int i) const {
  if (i < 0 || i >= count()) return "";
  return paths_[i].c_str();
}

String Library::title(int i) const {
  String p = path(i);
  int slash = p.lastIndexOf('/');
  int dot = p.lastIndexOf('.');
  if (dot <= slash) dot = p.length();
  return p.substring(slash + 1, dot);
}

Stream* Library::selectStream(int index) {
  if (paths_.empty()) return nullptr;
  int n = count();
  index_ = ((index % n) + n) % n;  // wrap around both ways
  if (file_) file_.close();
  file_ = SD_MMC.open(paths_[index_], FILE_READ);
  return file_ ? &file_ : nullptr;
}

Stream* Library::nextStream(int offset) { return selectStream(index_ + offset); }

Stream* Library::selectStream(const char* p) {
  if (file_) file_.close();
  file_ = SD_MMC.open(p, FILE_READ);
  return file_ ? &file_ : nullptr;
}

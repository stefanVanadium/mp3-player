#include "display.h"
#include <Adafruit_SharpMem.h>
#include <SPI.h>
#include "config.h"
#include "pins.h"

namespace ui {
namespace {

constexpr int W = 128, H = 128;
constexpr uint16_t INK = 0, PAPER = 1;  // memory LCD: 0 = black pixel

Adafruit_SharpMem lcd(&SPI, pins::LCD_CS, W, H, 2000000);
bool dirty = true;
uint32_t lastRefresh = 0;

void clear() { lcd.clearDisplayBuffer(); }

void text(int x, int y, const String& s, uint8_t size = 1) {
  lcd.setTextSize(size);
  lcd.setTextColor(INK);
  lcd.setCursor(x, y);
  lcd.print(s);
}

void centered(int y, const String& s, uint8_t size = 1) {
  int w = s.length() * 6 * size;
  text((W - w) / 2, y, s, size);
}

// Wraps on word boundaries, at most maxLines lines of 21 characters
void wrapped(int y, const String& s, int maxLines) {
  const int cols = W / 6;
  int start = 0;
  for (int line = 0; line < maxLines && start < (int)s.length(); line++) {
    int end = min((int)s.length(), start + cols);
    if (end < (int)s.length()) {
      int sp = s.lastIndexOf(' ', end);
      if (sp > start) end = sp;
    }
    String part = s.substring(start, end);
    if (line == maxLines - 1 && end < (int)s.length()) part = part.substring(0, cols - 1) + "~";
    text(0, y + line * 10, part);
    start = end;
    while (start < (int)s.length() && s[start] == ' ') start++;
  }
}

void battery(int x, int y, const power::State& p) {
  lcd.drawRect(x, y, 18, 8, INK);
  lcd.fillRect(x + 18, y + 2, 2, 4, INK);
  if (!isnan(p.percent)) lcd.fillRect(x + 2, y + 2, (int)(14 * p.percent / 100.0f), 4, INK);
  if (p.charging) text(x - 8, y, "+");
}

}  // namespace

bool begin() {
  pinMode(pins::LCD_DISP, OUTPUT);
  digitalWrite(pins::LCD_DISP, LOW);           // keep the panel blank
  SPI.begin(pins::LCD_SCK, -1, pins::LCD_MOSI, -1);
  bool ok = lcd.begin();
  lcd.setRotation(0);
  lcd.clearDisplay();                          // all-clear command, then show it
  digitalWrite(pins::LCD_DISP, HIGH);
  return ok;
}

void tick() {
  uint32_t now = millis();
  if (dirty || now - lastRefresh >= config::DISPLAY_REFRESH_MS) {
    lcd.refresh();  // the library flips the VCOM bit on every frame
    lastRefresh = now;
    dirty = false;
  }
}

void off() {
  lcd.clearDisplay();
  digitalWrite(pins::LCD_DISP, LOW);
}

void showPlayer(const PlayerView& v, const power::State& p) {
  clear();
  // Status bar
  String out = v.audio.output == audio::Output::Jack ? (v.headphones ? "JACK" : "no jack")
                                                      : (v.audio.btConnected ? "BT" : "BT ...");
  text(0, 0, out);
  battery(W - 20, 0, p);
  lcd.drawFastHLine(0, 10, W, INK);

  // Track
  if (v.count == 0) {
    centered(50, "No music");
    centered(62, "on the card");
  } else {
    wrapped(18, v.title, 4);
    text(0, 64, String(v.index + 1) + "/" + String(v.count));
    if (v.audio.sampleRate) {
      String sr = String(v.audio.sampleRate / 1000.0f, 1) + "k";
      text(W - sr.length() * 6, 64, sr);
    }
  }

  // Transport
  centered(80, v.audio.playing ? "> PLAYING" : "|| PAUSED", 1);

  // Volume bar
  lcd.drawFastHLine(0, 104, W, INK);
  text(0, 110, "VOL");
  int barW = W - 24;
  lcd.drawRect(22, 110, barW, 8, INK);
  lcd.fillRect(24, 112, (barW - 4) * v.volume / config::VOLUME_STEPS, 4, INK);
  dirty = true;
}

void showMessage(const char* line1, const char* line2) {
  clear();
  centered(52, line1);
  if (line2) centered(64, line2);
  dirty = true;
}

void showUpload(const String& ssid, const String& password, const String& ip) {
  clear();
  centered(0, "UPLOAD MODE");
  lcd.drawFastHLine(0, 10, W, INK);
  text(0, 20, "WiFi:");
  text(0, 30, ssid);
  text(0, 46, "Password:");
  text(0, 56, password);
  text(0, 72, "Open in a browser:");
  text(0, 82, "http://" + ip);
  centered(112, "PREV+NEXT to exit");
  dirty = true;
}

void showCharging(const power::State& p) {
  clear();
  centered(30, p.chargeDone ? "Charged" : "Charging", 2);
  if (!isnan(p.percent)) centered(60, String((int)p.percent) + " %", 2);
  if (!isnan(p.voltage)) centered(90, String(p.voltage, 2) + " V");
  dirty = true;
}

void testPattern() {
  clear();
  for (int i = 0; i < W; i += 8) {
    lcd.drawFastVLine(i, 0, H, INK);
    lcd.drawFastHLine(0, i, W, INK);
  }
  lcd.fillRect(32, 32, 64, 64, PAPER);
  centered(60, "LS013B7DH03");
  dirty = true;
}

}  // namespace ui

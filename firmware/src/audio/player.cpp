#include "player.h"
#include <Arduino.h>
#include "AudioTools.h"
#include "AudioTools/AudioCodecs/CodecFLACFoxen.h"
#include "AudioTools/AudioCodecs/CodecMP3Helix.h"
#include "AudioTools/AudioCodecs/CodecWAV.h"
#include "AudioTools/Communication/A2DPStream.h"
#include "library.h"
#include "pins.h"

namespace audio {
namespace {

enum class Cmd : uint8_t { Play, Pause, Toggle, Next, Prev, Select, OutJack, OutBt, Volume, Reload };
struct Msg {
  Cmd cmd;
  int arg;
  float f;
};

QueueHandle_t queue;
Library* library = nullptr;

I2SStream i2s;
A2DPStream a2dp;
bool a2dpStarted = false;
MP3DecoderHelix mp3;
FLACDecoderFoxen flac;
WAVDecoder wav;
MultiDecoder decoder;
AudioPlayer* player = nullptr;

// Written only by the audio task, read by anyone
volatile bool playing = false;
volatile Output output = Output::Jack;
volatile uint32_t sampleRate = 0;

void startI2S() {
  auto cfg = i2s.defaultConfig(TX_MODE);
  cfg.pin_bck = pins::I2S_BCK;
  cfg.pin_ws = pins::I2S_LRCK;
  cfg.pin_data = pins::I2S_DOUT;
  cfg.pin_mck = -1;          // no MCLK: PCM5122 PLL locks to BCK
  cfg.sample_rate = 44100;
  cfg.channels = 2;
  cfg.bits_per_sample = 16;
  cfg.use_apll = true;       // exact 44.1 kHz family rates
  cfg.buffer_count = 8;
  cfg.buffer_size = 512;
  i2s.begin(cfg);
}

void startBluetooth() {
  if (a2dpStarted) return;
  auto cfg = a2dp.defaultConfig(TX_MODE);
  // "[Unknown]" = connect to the first headphones found in pairing mode.
  // TODO: pairing screen + remember the device name in NVS.
  cfg.name = "[Unknown]";
  cfg.auto_reconnect = true;
  cfg.wait_for_connection = false;
  cfg.silence_on_nodata = true;
  a2dp.begin(cfg);
  a2dpStarted = true;
}

void apply(const Msg& m) {
  switch (m.cmd) {
    case Cmd::Play:
      player->setActive(true);
      break;
    case Cmd::Pause:
      player->setActive(false);
      break;
    case Cmd::Toggle:
      player->setActive(!player->isActive());
      break;
    case Cmd::Next:
      player->next();
      break;
    case Cmd::Prev:
      player->previous();
      break;
    case Cmd::Select:
      player->setIndex(m.arg);
      break;
    case Cmd::OutJack:
      player->setOutput(i2s);
      output = Output::Jack;
      break;
    case Cmd::OutBt:
      // A2DP is fixed at 44.1 kHz / 16 bit. TODO: resample 48 kHz files for Bluetooth.
      startBluetooth();
      player->setOutput(a2dp);
      output = Output::Bluetooth;
      break;
    case Cmd::Volume:
      player->setVolume(m.f);
      break;
    case Cmd::Reload: {
      bool wasActive = player->isActive();
      player->setActive(false);
      library->scan();
      player->begin(0, false);
      if (wasActive && library->count()) player->setActive(true);
      break;
    }
  }
}

void task(void*) {
  for (;;) {
    Msg m;
    while (xQueueReceive(queue, &m, 0) == pdTRUE) apply(m);
    size_t n = player->copy();
    playing = player->isActive();
    sampleRate = i2s.audioInfo().sample_rate;
    if (n == 0) vTaskDelay(pdMS_TO_TICKS(5));  // paused or waiting: let core 1 idle
  }
}

void send(Cmd c, int arg = 0, float f = 0) {
  Msg m{c, arg, f};
  xQueueSend(queue, &m, pdMS_TO_TICKS(50));
}

}  // namespace

bool begin(Library& lib, Output out, int startIndex) {
  library = &lib;
  startI2S();
  decoder.addDecoder(mp3, "audio/mpeg");
  decoder.addDecoder(flac, "audio/flac");
  decoder.addDecoder(wav, "audio/vnd.wave");
  player = new AudioPlayer(lib, i2s, decoder);
  player->setSilenceOnInactive(true);  // keep BCK running so the DAC PLL stays locked
  player->setVolume(1.0f);
  player->setAutoFade(true);
  bool ok = player->begin(startIndex, false);
  queue = xQueueCreate(16, sizeof(Msg));
  // Core 1 is the Arduino loop's core too, but the loop mostly sleeps; BT/WiFi live on core 0
  xTaskCreatePinnedToCore(task, "audio", 8192, nullptr, 5, nullptr, 1);
  if (out == Output::Bluetooth) setOutput(out);
  return ok;
}

void play() { send(Cmd::Play); }
void pause() { send(Cmd::Pause); }
void toggle() { send(Cmd::Toggle); }
void next() { send(Cmd::Next); }
void previous() { send(Cmd::Prev); }
void select(int index) { send(Cmd::Select, index); }
void setOutput(Output out) { send(out == Output::Jack ? Cmd::OutJack : Cmd::OutBt); }
void setSoftVolume(float v) { send(Cmd::Volume, 0, v); }
void reload() { send(Cmd::Reload); }

Snapshot snapshot() {
  Snapshot s;
  s.playing = playing;
  s.index = library ? library->index() : 0;
  s.output = output;
  s.btConnected = a2dpStarted && a2dp.isConnected();
  s.sampleRate = sampleRate;
  return s;
}

}  // namespace audio

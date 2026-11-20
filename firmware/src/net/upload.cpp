#include "upload.h"
#include <SD_MMC.h>
#include <WebServer.h>
#include <WiFi.h>
#include "config.h"

namespace upload {
namespace {

WebServer server(80);
fs::File target;
bool filesAdded = false;

const char kPage[] PROGMEM = R"html(<!doctype html>
<html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<title>MP3 Player</title>
<style>body{font-family:sans-serif;max-width:32em;margin:2em auto;padding:0 1em}</style>
</head><body>
<h1>MP3 Player</h1>
<p>Copy MP3, FLAC or WAV files to the card (folder <code>/music</code>).</p>
<form method="POST" action="/upload" enctype="multipart/form-data">
<input type="file" name="f" multiple accept=".mp3,.flac,.wav"><br><br>
<button>Upload</button>
</form>
</body></html>)html";

void handleUploadData() {
  HTTPUpload& up = server.upload();
  if (up.status == UPLOAD_FILE_START) {
    String name = up.filename;
    name.replace("/", "_");
    name.replace("\\", "_");
    SD_MMC.mkdir(config::UPLOAD_DIR);
    target = SD_MMC.open(String(config::UPLOAD_DIR) + "/" + name, FILE_WRITE);
  } else if (up.status == UPLOAD_FILE_WRITE) {
    if (target) target.write(up.buf, up.currentSize);
  } else if (up.status == UPLOAD_FILE_END) {
    if (target) {
      target.close();
      filesAdded = true;
    }
  } else if (up.status == UPLOAD_FILE_ABORTED) {
    if (target) target.close();
  }
}

}  // namespace

bool begin() {
  filesAdded = false;
  WiFi.mode(WIFI_AP);
  if (!WiFi.softAP(config::AP_SSID, config::AP_PASSWORD)) return false;
  server.on("/", HTTP_GET, [] { server.send_P(200, "text/html", kPage); });
  server.on(
      "/upload", HTTP_POST,
      [] {
        server.sendHeader("Location", "/");
        server.send(303);
      },
      handleUploadData);
  server.begin();
  return true;
}

void poll() { server.handleClient(); }

void end() {
  server.stop();
  WiFi.softAPdisconnect(true);
  WiFi.mode(WIFI_OFF);
}

bool changed() { return filesAdded; }

String ip() { return WiFi.softAPIP().toString(); }

}  // namespace upload

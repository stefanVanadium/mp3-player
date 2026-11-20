// WiFi upload mode: the player becomes an access point and serves a page to copy music
// onto the card. Bluetooth audio is stopped while it runs.
#pragma once
#include <Arduino.h>

namespace upload {

bool begin();     // starts the AP and the web server
void poll();      // call from the loop
void end();       // stops WiFi; returns true from changed() if files were added
bool changed();
String ip();

}  // namespace upload

# Conexiuni schematic — MP3 player

Verificat pe 2026-10-21: simbolurile din `lib/mp3_player.kicad_sym` comparate pin cu pin cu datasheet-urile din `datasheets/`, plus numerele de pad din footprint-uri.

## 1. Rezultatul verificării

Simbolurile și footprint-urile se potrivesc cu datasheet-urile la: ESP32-PICO-MINI-02, PCM5122, PCM5102A, OPA1622, LM27762, BQ25180, TPS63802, LP5907, MMBT3904, USB-C, TF-01A, FH12, PJ-342 și USBLC6. Numerotarea pinilor e bună peste tot.

Probleme găsite:

| # | Ce | Gravitate | Status |
|---|---|---|---|
| 1 | **CP2102N QFN20 nu are pin DTR.** Auto-reset-ul ESP32 are nevoie de DTR **și** RTS (DTR există doar la QFN24 și QFN28) | **blocant** | ✅ **rezolvat**: în librărie e acum `CP2102N-A02-GQFN24R` (C969151, simbol + footprint QFN-24 + 3D, pinii verificați cu datasheet-ul). QFN20 a fost scos. BOM actualizat |
| 2 | **OPA1622: pad-ul termic (pin 11 "EP") se leagă la V− (−3V), NU la GND** | **mare**: dacă îl pui la GND faci scurt pe −3V | ✅ **rezolvat în librărie**: pinul 11 se numește acum `V-(EP)`, ca să nu-l legi din greșeală la GND. Tu îl legi la `-3V0_AMP`. Pe PCB: poligon de −3V sub pad |
| 3 | **Conflictul GPIO12 ↔ microSD D2.** Pull-up-ul de pe D2 pune MTDI pe 1 la boot, deci flash-ul ar primi 1.8V în loc de 3.3V și ESP-ul nu mai bootează | mare (se rezolvă din software) | ✅ **documentat** în `code.md` (pas obligatoriu la prima pornire a fiecărei plăci): `espefuse.py set_flash_voltage 3.3V`. Nu se mai poate da înapoi, dar e corect pentru modulul ăsta |
| 4 | **GPIO2 (microSD D0) are pull-up**, iar download mode cere GPIO2 = 0 | mediu | ✅ **rezolvat în design**: D1 = B5819W (C8598, basic, fără taxă) între GPIO2 și GPIO0 (secțiunea 4.3). Adăugată în BOM. Simbolul îl iei din librăria standard KiCad (`Device:D_Schottky`) |
| 5 | PCM5122 cere AVDD/CPVDD ≥ 3.1–3.2V, iar LP5907-3.3 alimentat din VSYS iese din reglaj când bateria scade sub ~3.35V | mic | ✅ în `code.md`: firmware-ul oprește player-ul la VBAT ≈ 3.4V |
| 6 | OPA1622 pe ±3V scoate maxim ~1.5 Vrms (~0.8V de la rail), PCM5122 scoate 2.1 Vrms | mic | ✅ în `code.md`: volumul digital maxim e limitat la ~−4 dB. Pentru căști e oricum mult (>50 mW în 32Ω) |
| 7 | BQ25180 TS/MR: fără NTC, TI cere un **10k de la TS/MR la GND**, altfel nu încarcă | mediu | ✅ în design: 10k în paralel cu butonul de power (secțiunea 4.4) |
| 8 | Ai **exact 21 de GPIO** și le folosești pe toate (vezi tabelul) | info | dacă mai vrei ceva în v1 (LED, backlight), adaugi un expander I2C (ex. TCA9534) |
| 9 | ESP32-PICO-MINI-02 e marcat NRND (Not Recommended for New Designs) în datasheet | info | se mai găsește la JLC. Pentru un hobby e ok, doar să știi |
| 10 | MAX17048: datasheet-ul lipsește din `datasheets/` | info | ✅ **rezolvat**: e în `datasheets/MAX17048.pdf`. Pinii se potrivesc cu simbolul, decuplarea VDD e 0.1µF, adresa e 0x36 |

Nu am putut verifica din datasheet (verifici fizic, cu multimetrul):
- **PJ-342**: din desen, 5 și 2 sunt sleeve, 6 e ring (contact NC: 7), 3 e tip (contact NC: 4). Când ai jack-ul în mână, verifici cu multimetrul pe o mufă băgată
- **TF-01A pin 9 (CD)**: presupun că se închide la GND/shell când e card băgat (active low). Verifici la fel
- **ST7567**: pinout-ul diferă de la vânzător la vânzător (știai deja). Mai jos e după numele semnalelor

## 2. Rail-uri (net-uri de alimentare)

| Net | De unde | Cine se alimentează |
|---|---|---|
| `VBUS` | USB-C (5V) | BQ25180 IN, USBLC6 VBUS, divizor VBUS CP2102N |
| `VBAT` | LiPo + | BQ25180 BAT, MAX17048 CELL + VDD |
| `VSYS` | BQ25180 SYS (3.4–4.5V, dispare în ship mode) | TPS63802, LP5907, LM27762 |
| `+3V3` | TPS63802 | ESP32, CP2102N, microSD, display, PCM5122 DVDD, toate pull-up-urile |
| `+3V3_A` | LP5907 | PCM5122 AVDD + CPVDD (doar atât!) |
| `+3V0_AMP` / `-3V0_AMP` | LM27762 OUT+ / OUT− | OPA1622 V+ / V− |
| `GND` | — | **un singur plan de GND** (vezi nota de la final) |

## 3. ESP32-PICO-MINI-02: alocarea pinilor

| Pin modul | GPIO | Net | Note |
|---|---|---|---|
| 3 | 3V3 | `+3V3` | 22µF + 0.1µF lângă pin |
| 1, 2, 11, 14, 36–53 | GND | `GND` | inclusiv toate pad-urile 49 din centru |
| 8 | EN | `ESP_EN` | 10k la +3V3, 1µF la GND, colector Q1. Merge și la reset-ul display-ului |
| 31 | IO1 / TXD0 | `ESP_TX` | → CP2102N RXD |
| 30 | IO3 / RXD0 | `ESP_RX` | ← CP2102N TXD |
| 23 | IO0 | `ESP_BOOT` | 10k la +3V3, colector Q2, buton BOOT (opțional) la GND, catodul diodei D1 |
| 18 | IO14 | `SD_CLK` | SDMMC slot 1 (pinii sunt ficși, IO_MUX) |
| 21 | IO15 | `SD_CMD` | 10k pull-up |
| 22 | IO2 | `SD_D0` | 10k pull-up, anodul diodei D1 |
| 24 | IO4 | `SD_D1` | 10k pull-up |
| 19 | IO12 | `SD_D2` | 10k pull-up (de aici e eFuse-ul, problema 3) |
| 20 | IO13 | `SD_D3` | 10k pull-up |
| 35 | IO21 | `I2C_SDA` | 4.7k pull-up la +3V3 |
| 34 | IO22 | `I2C_SCL` | 4.7k pull-up la +3V3 |
| 16 | IO26 | `I2S_BCK` | → PCM5122 BCK |
| 15 | IO25 | `I2S_LRCK` | → PCM5122 LRCK |
| 17 | IO27 | `I2S_DOUT` | → PCM5122 DIN |
| 29 | IO5 | `LCD_SCK` | SPI clock display |
| 33 | IO19 | `LCD_MOSI` | SPI data display |
| 12 | IO32 | `LCD_CS` | ST7567 CS / LS013 SCS (la LS013 e activ HIGH, se rezolvă din firmware) |
| 13 | IO33 | `LCD_DC` | ST7567 A0 (D/C). La LS013 nu se folosește (EXTMODE = L) |
| 26 | IO20 | `BTN_PLAY` | buton la GND + 10k pull-up |
| 27 | IO7 | `AUDIO_EN` | 100k pull-down. Pornește LM27762 și scoate DAC-ul din mute |
| 28 | IO8 | `PWR_INT` | 10k pull-up. BQ25180 /INT + MAX17048 ALRT (wired-OR, ambele sunt open-drain) |
| 9 | I34 | `BTN_VOLUP` | input-only: **pull-up extern obligatoriu** (10k) |
| 10 | I35 | `BTN_VOLDN` | input-only, 10k pull-up |
| 5 | I37 | `BTN_NEXT` | input-only, 10k pull-up |
| 6 | I38 | `BTN_PREV` | input-only, 10k pull-up |
| 4 | I36 | `SD_DET` | input-only, 10k pull-up |
| 7 | I39 | `JACK_DET` | input-only (vezi 4.8) |
| 25, 32 | NC | — | nu conectezi nimic |

Pe I36/I39 ESP32-ul poate da glitch-uri scurte când merge WiFi/ADC (errata). De asta acolo am pus SD_DET și JACK_DET, care se citesc cu debounce/polling, nu butoane pe întrerupere.

## 4. Pe blocuri

### 4.1 USB-C + ESD

**USB-C (TYPE-C-31-M-12)**
| Pin | Net |
|---|---|
| A4B9, B4A9 (VBUS) | `VBUS` |
| A1B12, B1A12 (GND) | `GND` |
| A5 (CC1) | 5.1k la GND |
| B5 (CC2) | 5.1k la GND (alt 5.1k, separat) |
| A6, B6 (DP1, DP2) | `USB_DP` (le legi împreună) |
| A7, B7 (DN1, DN2) | `USB_DN` (le legi împreună) |
| A8, B8 (SBU) | NC |
| 1–4 (EH, carcasa) | `GND` |

**USBLC6-2SC6** (simbolul are pinii fără nume, așa că uite-i):
| Pin | Funcție | Net |
|---|---|---|
| 1, 6 | I/O1 | `USB_DP` (D+ trece pe sub cip: intră pe 1, iese pe 6) |
| 3, 4 | I/O2 | `USB_DN` |
| 2 | GND | `GND` |
| 5 | VBUS | `VBUS` |

`VBUS`: 10µF la GND lângă conector.

### 4.2 CP2102N-A02-GQFN24 (USB-UART), alimentat din +3V3

| Pin | Nume | Conectare |
|---|---|---|
| 3 | D+ | `USB_DP` |
| 4 | D− | `USB_DN` |
| 5 | VIO | `+3V3` |
| 6 | VDD | `+3V3`, 4.7µF + 0.1µF |
| 7 | VREGIN | `+3V3`, 4.7µF + 0.1µF (regulatorul intern nu se folosește) |
| 8 | VBUS | divizor: `VBUS` → 22.1k → pin 8, apoi 47.5k la GND |
| 9 | RSTb | 1k la `+3V3` |
| 2, EP (25) | GND | `GND` |
| 20 | RXD | `ESP_TX` |
| 21 | TXD | `ESP_RX` |
| 23 | DTR | `DTR` (la auto-reset) |
| 19 | RTS | `RTS` (la auto-reset) |
| 1, 10–18, 22, 24 | RI, NC, GPIO, SUSPEND, CTS, DSR, DCD | NC |

De ce din +3V3 și nu din VBUS: așa nu se alimentează invers prin TX/RX când USB-ul e scos și ESP-ul merge. Când e băgat USB-ul, BQ25180 iese singur din ship mode, deci +3V3 există mereu când ai nevoie de programare. Consumul CP2102N fără USB e ~0.2 mA, și doar cât timp player-ul e pornit.

### 4.3 Auto-reset + boot (2× MMBT3904)

| Piesă | B (pin 1) | E (pin 2) | C (pin 3) |
|---|---|---|---|
| Q1 | 10k ← `DTR` | `RTS` | `ESP_EN` |
| Q2 | 10k ← `RTS` | `DTR` | `ESP_BOOT` (IO0) |

- `ESP_EN`: 10k la +3V3, 1µF la GND
- `ESP_BOOT`: 10k la +3V3
- **D1**: Schottky (B5819W, C8598 basic), anod pe `SD_D0` (IO2), catod pe `ESP_BOOT` (IO0). În funcționare normală IO0 e sus și dioda nu conduce. **IO0 nu-l folosești la nimic altceva**, altfel strici transferul pe SD
- buton RESET opțional: `ESP_EN` la GND

### 4.4 Alimentare

**BQ25180 (DSBGA-8)**
| Pin | Nume | Conectare |
|---|---|---|
| A2 | IN | `VBUS`, 1µF/25V la GND |
| B2 | SYS | `VSYS`, 10µF/25V la GND |
| C2 | BAT | `VBAT`, 1µF la GND |
| D2 | GND | `GND` |
| B1 | SCL | `I2C_SCL` |
| C1 | SDA | `I2C_SDA` |
| A1 | /INT | `PWR_INT` |
| D1 | TS/MR | buton POWER la GND **+ 10k la GND** (în loc de NTC). GND-ul butonului cât mai aproape de pinul D2 |

Adresă I2C 0x6A. Butonul de power: apăsare scurtă = trezire din ship mode. Cât merge player-ul, BQ-ul dă întrerupere pe `/INT` (WAKE1/WAKE2), așa că ESP-ul vede apăsarea fără GPIO separat. Apăsare lungă = reset hardware.

**Baterie**: conector 2 pini (ex. JST-PH), + → `VBAT`, − → `GND`.

**TPS63802 (3.3V digital)**
| Pin | Nume | Conectare |
|---|---|---|
| 10 | VIN | `VSYS`, 10µF |
| 1 | EN | `VSYS` (pornește odată cu SYS) |
| 2 | MODE | `GND` (power save) |
| 9 | L1 | bobină 0.47µH (WPN201610HR47MT), capătul 1 |
| 7 | L2 | bobină, capătul 2 |
| 6 | VOUT | `+3V3`, 22µF + 0.1µF |
| 4 | FB | R 511k de la VOUT la FB, R 91k de la FB la GND → 3.31V |
| 5 | PG | NC (sau 100k la +3V3 dacă vrei să-l măsori) |
| 3, 8 | AGND, GND | `GND` |

Verifică în datasheet-ul bobinei că Isat ≥ ~2A.

**LP5907-3.3 (3.3V analog, doar pentru DAC)**
| Pin | Conectare |
|---|---|
| 1 IN | `VSYS`, 1µF |
| 3 EN | `VSYS` |
| 5 OUT | `+3V3_A`, 1µF |
| 2 GND | `GND` |
| 4 N/C | NC |

**LM27762 (±3V pentru amplificator)**: exact exemplul din datasheet (3.3–4.2V in, ±3V out)
| Pin | Nume | Conectare |
|---|---|---|
| 3 | VIN | `VSYS`, 2.2µF |
| 12, 8 | EN+, EN− | `AUDIO_EN` (amândouă) |
| 10, 9 | C1+, C1− | 1µF între ele |
| 5 | CP | 4.7µF la GND |
| 11 | OUT+ | `+3V0_AMP`, 2.2µF |
| 2 | FB+ | R1 150k de la OUT+ la FB+, R2 100k de la FB+ la GND → +3.00V |
| 6 | OUT− | `-3V0_AMP`, 2.2µF |
| 7 | FB− | R3 147k de la OUT− la FB−, R4 100k de la FB− la GND → −3.01V |
| 1 | PGOOD | `GND` (nefolosit, așa zice datasheet-ul) |
| 4, EP (13) | GND | `GND` |

R2 și R4 trebuie să fie ≥ 50k (cerință din datasheet). Folosește 1%.

**MAX17048 (fuel gauge)**
| Pin | Nume | Conectare |
|---|---|---|
| 2 | CELL | `VBAT` |
| 3 | VDD | `VBAT`, 0.1µF la GND |
| 1 | CTG | `GND` |
| 6 | QSTRT | `GND` |
| 4, EP (9) | GND | `GND` |
| 7 | SCL | `I2C_SCL` |
| 8 | SDA | `I2C_SDA` |
| 5 | ALRT | `PWR_INT` |

Adresă 0x36. E legat direct pe baterie, deci rămâne alimentat și în ship mode (~4µA în hibernate). Ca să coboare sub 1µA: înainte de ship mode, firmware-ul scrie `MODE.EnSleep = 1`. Apoi, când +3V3 dispare, SDA/SCL stau jos (au și pull-down intern) și după ~2.5s cipul intră în sleep. **Fără EnSleep nu intră în sleep.**

### 4.5 Audio

**PCM5122 (mod I2C)**
| Pin | Nume | Conectare |
|---|---|---|
| 1 | CPVDD | `+3V3_A`, 0.1µF + 10µF |
| 2–4 | CAPP – CAPM | 2.2µF între 2 și 4 |
| 3 | CPGND | `GND` |
| 5 | VNEG | 2.2µF la GND |
| 6 | OUTL | `DAC_L` |
| 7 | OUTR | `DAC_R` |
| 8 | AVDD | `+3V3_A`, 0.1µF + 10µF |
| 9 | AGND | `GND` |
| 10 | VCOM | `GND` (mod VREF, cel implicit) |
| 11 | SDA | `I2C_SDA` |
| 12 | SCL | `I2C_SCL` |
| 13, 14, 15, 19 | GPIO5/4/3/6 | NC (au pull-down intern) |
| 16 | ADR2 | `GND` |
| 24 | ADR1 | `GND` → adresă 0x4C |
| 17 | MODE1 | `GND` |
| 18 | MODE2 | `+3V3` → mod I2C |
| 20 | SCK | `GND` (fără MCLK, PLL-ul intern ia ceasul din BCK) |
| 21 | BCK | `I2S_BCK` |
| 22 | DIN | `I2S_DOUT` |
| 23 | LRCK | `I2S_LRCK` |
| 25 | XSMT | `AUDIO_EN` (low = mute, deci DAC-ul tace cât bootează ESP-ul) |
| 26 | LDOO | 0.1µF la GND (poți pune 1µF) |
| 27 | DGND | `GND` |
| 28 | DVDD | `+3V3`, 0.1µF + 10µF |

Condensatorii de la charge pump (CAPP/CAPM, VNEG): TI recomandă ceramici bune (X7R/C0G).

**Filtru între DAC și amplificator** (pe fiecare canal):
`DAC_L` → 470Ω → `AMP_INL` → 2.2nF C0G la GND
`DAC_R` → 470Ω → `AMP_INR` → 2.2nF C0G la GND

**OPA1622**: buffer cu gain +1 (e stabil la gain unitar)
| Pin | Nume | Conectare |
|---|---|---|
| 1 | +INA | `AMP_INL` |
| 10 | −INA | `HP_L` (feedback direct din OUTA) |
| 9 | OUTA | `HP_L` |
| 5 | +INB | `AMP_INR` |
| 6 | −INB | `HP_R` |
| 7 | OUTB | `HP_R` |
| 2 | V+ | `+3V0_AMP`, 0.1µF + 2.2µF la GND, lipite de pin |
| 4 | V− | `-3V0_AMP`, 0.1µF + 2.2µF la GND |
| 3 | GND | `GND` |
| 8 | EN | divizor din V+: 20k de la `+3V0_AMP` la EN, 10k de la EN la GND (~1.0V, pragul e 0.82V) |
| **11** | **EP** | **`-3V0_AMP`** (problema 2) |

Prin divizor, amplificatorul pornește abia când rail-urile sunt aproape gata, deci fără pop. Asta e metoda din datasheet. Cât timp `AUDIO_EN` e jos, LM27762 e oprit și OPA1622 n-are alimentare.

**Jack PJ-342** (de verificat cu multimetrul, vezi secțiunea 1)
| Pin | Rol | Conectare |
|---|---|---|
| 3 | Tip (L) | `HP_L`, + 10k la GND |
| 6 | Ring (R) | `HP_R`, + 10k la GND |
| 5, 2 | Sleeve | `GND` |
| 4 | contact NC al tip-ului | `JACK_SW` (detect) |
| 7 | contact NC al ring-ului | NC |

### 4.6 microSD (TF-01A)

| Pin | Nume | Conectare |
|---|---|---|
| 1 | DAT2 | `SD_D2` |
| 2 | CD/DAT3 | `SD_D3` |
| 3 | CMD | `SD_CMD` |
| 4 | VDD | `+3V3`, 10µF + 0.1µF lângă slot |
| 5 | CLK | `SD_CLK` (opțional 33Ω în serie, lângă ESP) |
| 6 | VSS | `GND` |
| 7 | DAT0 | `SD_D0` |
| 8 | DAT1 | `SD_D1` |
| 9 | CD | `SD_DET` (10k pull-up, activ LOW, de verificat) |
| 10–13 | carcasă | `GND` |

Cei 5 pull-up de 10k (CMD, D0–D3) îi pui la +3V3. **Nu pui pull-up pe CLK.**

### 4.7 Display: două footprint-uri FPC, montezi doar unul

**Sharp LS013B7DH03 → FH12-10S (J_LS013)**
| Pin FPC | Semnal | Conectare |
|---|---|---|
| 1 | SCLK | `LCD_SCK` (max 1 MHz la panoul ăsta) |
| 2 | SI | `LCD_MOSI` |
| 3 | SCS | `LCD_CS` |
| 4 | EXTCOMIN | `GND` (inversia VCOM se face prin software) |
| 5 | DISP | `ESP_EN` |
| 6 | VDDA | `+3V3`, 1µF |
| 7 | VDD | `+3V3`, 1µF |
| 8 | EXTMODE | `GND` (= mod serial VCOM) |
| 9 | VSS | `GND` |
| 10 | VSSA | `GND` |
| 11, 12 | prinderi | `GND` |

Recomandat pentru panoul ăsta e 2.7–3.3V, deci 3.3V e chiar la limită, dar în spec. Verifică și dacă FPC-ul panoului are contactele sus sau jos, ca să știi orientarea conectorului.

**ST7567 (al doilea FPC)**: numărul de pini îl afli după ce cumperi panoul
| Semnal ST7567 | Conectare |
|---|---|
| SCL / SCLK | `LCD_SCK` |
| SI / SDA | `LCD_MOSI` |
| CS | `LCD_CS` |
| A0 / RS / DC | `LCD_DC` |
| RST | `ESP_EN` |
| VDD | `+3V3` + decuplare |
| VSS | `GND` |
| condensatorii charge pump / VOUT / V0 | cum zice fișa panoului |
| backlight (dacă are) | prin rezistență la +3V3 (sau MOSFET, dar nu mai ai GPIO) |

Reset-ul display-ului e pe `ESP_EN` pentru că n-a mai rămas niciun GPIO. Se resetează odată cu ESP-ul, iar la un reboot software trimiți comanda de reset (0xE2) la ST7567.

### 4.8 Butoane + jack detect

Toate butoanele sunt TS-1088: pinul 1 pe net, pinul 2 la `GND`, cu 10k pull-up la +3V3 pe fiecare net. Opțional un 100nF la GND pentru debounce.

| Buton | Net |
|---|---|
| Play/Pause | `BTN_PLAY` (IO20) |
| Vol+ | `BTN_VOLUP` (I34) |
| Vol− | `BTN_VOLDN` (I35) |
| Next | `BTN_NEXT` (I37) |
| Prev | `BTN_PREV` (I38) |
| Power | BQ25180 TS/MR (secțiunea 4.4) |
| Boot (opțional, ascuns) | `ESP_BOOT` |

**Jack detect**: `JACK_SW` (pinul 4 al jack-ului) → 100k în serie → `JACK_DET` (I39), plus 1M pull-up de la `JACK_DET` la +3V3.
- fără mufă: pinul 4 atinge tip-ul (~0V prin 10k la GND), deci `JACK_DET` ≈ 0.3V, adică **LOW**
- cu mufă: contactul se deschide, deci `JACK_DET` = **HIGH**
- rezistența de 100k din serie protejează GPIO-ul dacă audio pornește fără căști băgate (tip-ul ar urca la ±2V)

## 5. Rezumat magistrale

| Magistrală | Pe ea |
|---|---|
| I2C (IO21/IO22, 4.7k pull-up) | BQ25180 0x6A, MAX17048 0x36, PCM5122 0x4C, fără conflicte |
| I2S (IO26/25/27) | PCM5122 |
| SDMMC 4-bit (IO14/15/2/4/12/13) | microSD |
| SPI (IO5/19/32/33) | display |
| UART0 (IO1/IO3) | CP2102N |

## 6. Note pentru schematic / PCB

- **GND**: TI zice explicit la PCM512x că se folosește un singur GND comun (AGND/DGND legate) și să ții semnalele digitale departe de ieșirile analogice. Fă un singur plan de GND solid, fără split, și obții separarea din plasare: DAC/amp departe de ESP32 și de bobina TPS63802. Nota din `mp3_player.md` e actualizată
- condensatorii de decuplare se pun lipiți de pinii lor. În schematic îi desenezi lângă cip, ca să știi pe PCB
- ESP32: fără cupru sub antenă, modulul la marginea plăcii (rămâne ce era)
- **înainte** de primul flash: `espefuse.py set_flash_voltage 3.3V` (problema 3). Până atunci firmware-ul nu bootează din cauza pull-up-ului de pe D2

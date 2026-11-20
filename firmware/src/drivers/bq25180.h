// TI BQ25180 charger with power path, ship mode and push button (datasheet SLUSE99C).
#pragma once
#include <Wire.h>

class BQ25180 {
 public:
  static constexpr uint8_t ADDR = 0x6A;

  enum class ChargeState : uint8_t { NotCharging, ConstantCurrent, ConstantVoltage, DoneOrDisabled };

  struct Status {
    bool vinGood;          // STAT0.VIN_PGOOD_STAT
    ChargeState charge;    // STAT0.CHG_STAT
    bool thermalReg;       // STAT0.THERMREG_ACTIVE_STAT
    bool tsOpen;           // STAT0.TS_OPEN_STAT (R12 missing or button stuck)
    bool batteryUvlo;      // STAT1.BUVLO_STAT
    bool wake1;            // STAT1.WAKE1_FLAG: button held >= 300 ms (clears on read)
    bool wake2;            // STAT1.WAKE2_FLAG: button held >= 2 s (clears on read)
    uint8_t faults;        // FLAG0 raw (clears on read)
  };

  bool begin(TwoWire& wire, uint16_t chargeCurrentMa);
  bool setChargeCurrent(uint16_t mA);
  uint16_t chargeCurrent();  // 0 on I2C error
  bool readStatus(Status& s);
  // Battery FET off; wakes on button press or adapter insert.
  // The charger only enters ship mode once VIN is removed.
  bool enterShipMode();
  bool hardwareReset();

 private:
  // Registers
  static constexpr uint8_t STAT0 = 0x00, STAT1 = 0x01, FLAG0 = 0x02, VBAT_CTRL = 0x03,
                           ICHG_CTRL = 0x04, IC_CTRL = 0x07, SHIP_RST = 0x09, MASK_ID = 0x0C;
  TwoWire* wire_ = nullptr;
};

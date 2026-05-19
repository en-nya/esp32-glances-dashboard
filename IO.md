# Hardware Pin Configuration

Complete pin mapping and hardware connections for the ESP32 Glances Dashboard project.

## Hardware Overview

- **MCU**: ESP32-WROOM-32E-N4
- **Display**: ST7789 LCD (240×320 pixels)
- **Touch Controller**: XPT2046 (resistive touch)
- **Power**: 3.3V logic level

---

## ESP32 Pin Mapping

### Display (ST7789 LCD)

| Function | ESP32 GPIO | Pin Description |
|----------|-----------|-----------------|
| LCD_MOSI | GPIO13 | SPI MOSI (Master Out Slave In) |
| LCD_SCLK | GPIO14 | SPI Clock |
| LCD_CS   | GPIO15 | Chip Select (active low) |
| LCD_DC   | GPIO2  | Data/Command select (RS) |
| LCD_RST  | GPIO12 | Reset (active low) |
| LCD_BL   | GPIO21 | Backlight control (PWM) |

**SPI Configuration**:
- Baudrate: 80 MHz
- Mode: 0 (CPOL=0, CPHA=0)
- Bus: SPI1

### Touch Controller (XPT2046)

| Function | ESP32 GPIO | Pin Description |
|----------|-----------|-----------------|
| RTP_MOSI | GPIO32 | SPI MOSI (DIN) |
| RTP_MISO | GPIO39 | SPI MISO (DOUT) |
| RTP_SCLK | GPIO25 | SPI Clock (DCLK) |
| RTP_CS   | GPIO33 | Chip Select (active low) |
| RTP_IRQ  | GPIO36 | Touch interrupt (PENIRQ) |

**Touch Panel Connections**:
- X+, Y+, X-, Y- connected to XPT2046 pins 2, 3, 4, 5

**SPI Configuration**:
- Baudrate: 2.5 MHz
- Pull-up resistor: 10kΩ on IRQ line

### SD Card Interface (Optional)

| Function | ESP32 GPIO | Pin Description |
|----------|-----------|-----------------|
| SD_CS    | GPIO5  | SD Card Chip Select |
| SD_SCLK  | GPIO18 | SPI Clock |
| SD_MISO  | GPIO19 | SPI MISO |
| SD_MOSI  | GPIO23 | SPI MOSI |

### Other Peripherals

| Function | ESP32 GPIO | Pin Description |
|----------|-----------|-----------------|
| BOOT_BTN | GPIO0  | Boot button (brightness control) |
| BAT_ADC  | GPIO34 | Battery voltage ADC |
| AUDIO_IN | GPIO26 | Audio input |
| AUDIO_EN | GPIO4  | Audio enable |

---

## Complete GPIO Summary

| GPIO | Function | Direction | Notes |
|------|----------|-----------|-------|
| GPIO0 | BOOT_BTN | Input | Boot button, pull-up, brightness control |
| GPIO2 | LCD_DC | Output | LCD Data/Command select |
| GPIO4 | AUDIO_EN | Output | Audio enable |
| GPIO5 | SD_CS | Output | SD card chip select |
| GPIO12 | LCD_RST | Output | LCD reset |
| GPIO13 | LCD_MOSI | Output | LCD SPI MOSI |
| GPIO14 | LCD_SCLK | Output | LCD SPI clock |
| GPIO15 | LCD_CS | Output | LCD chip select |
| GPIO16 | Reserved | - | Available for expansion |
| GPIO17 | Reserved | - | Available for expansion |
| GPIO18 | SD_SCLK | Output | SD card SPI clock |
| GPIO19 | SD_MISO | Input | SD card SPI MISO |
| GPIO21 | LCD_BL | Output | LCD backlight PWM |
| GPIO22 | Reserved | - | Available for expansion |
| GPIO23 | SD_MOSI | Output | SD card SPI MOSI |
| GPIO25 | RTP_SCLK | Output | Touch SPI clock |
| GPIO26 | AUDIO_IN | Input | Audio input |
| GPIO27 | SPI_CS | Output | General SPI chip select |
| GPIO32 | RTP_MOSI | Output | Touch SPI MOSI |
| GPIO33 | RTP_CS | Output | Touch chip select |
| GPIO34 | BAT_ADC | Input | Battery voltage ADC (input only) |
| GPIO35 | Reserved | Input | Available (input only) |
| GPIO36 | RTP_IRQ | Input | Touch interrupt (input only) |
| GPIO39 | RTP_MISO | Input | Touch SPI MISO (input only) |

**Note**: GPIO34-39 are input-only pins and cannot be used as outputs.

---

## Power Requirements

### Power Supply
- **Voltage**: 3.3V for all logic levels
- **Current**: 200-300mA typical (varies with backlight brightness)
- **Peak Current**: Up to 500mA during WiFi transmission

### Decoupling Capacitors

**ESP32 Module (U2)**:
- C6: 10µF, ±10%, 25V (VCC3V3 to GND)
- C5: 100nF, ±10%, 50V (VCC3V3 to GND)

**XPT2046 Touch Controller (U4)**:
- C12: 100nF, ±10%, 50V (VCC to GND)
- C13: 100nF, ±10%, 50V (VREF/IOVDD to GND)

---

## Important Notes

### GPIO Restrictions
- **GPIO34-39**: Input-only pins, no internal pull-up/pull-down resistors
- **GPIO0**: Used for boot mode selection, pulled high by default
- **GPIO12**: Boot voltage selection, avoid external pull-up during boot

### SPI Bus Sharing
- LCD uses SPI1 (high-speed, 80 MHz)
- Touch controller uses separate SPI pins (2.5 MHz)
- SD card shares pins with general SPI bus

### Backlight Control
- GPIO21 supports PWM for brightness control
- PWM frequency: 1 kHz
- Duty cycle: 0-100% (configurable in software)

---

## Wiring Tips

### Signal Integrity
- Keep SPI traces short and direct
- Use ground plane for noise reduction
- Add 100nF decoupling capacitors close to IC power pins

### Power Distribution
- Use adequate wire gauge for power lines (minimum 22 AWG)
- Connect all GND pins together (common ground)
- Place bulk capacitor (10µF) near ESP32 module

### Touch Screen
- Ensure good contact between touch panel and XPT2046
- 10kΩ pull-up resistor required on IRQ line
- Shield touch traces from LCD noise if possible

---

## Pin Configuration in Code

The pin definitions are centralized in `lib/pins.py`:

```python
# LCD pins
LCD_MOSI = 13
LCD_SCLK = 14
LCD_CS = 15
LCD_DC = 2
LCD_RST = 12
LCD_BL = 21

# Touch pins
TOUCH_MOSI = 32
TOUCH_MISO = 39
TOUCH_SCLK = 25
TOUCH_CS = 33
TOUCH_IRQ = 36

# Button
BOOT_BUTTON = 0
```

---

## Troubleshooting

### Display Issues
- **Blank screen**: Check LCD_BL (GPIO21) is high, verify power supply
- **Garbled display**: Verify SPI connections, check baudrate setting
- **No response**: Check LCD_CS and LCD_DC connections

### Touch Issues
- **No touch response**: Verify RTP_IRQ pull-up resistor (10kΩ)
- **Inaccurate touch**: Calibrate touch controller, check X+/Y+/X-/Y- connections
- **Intermittent touch**: Check for noise on touch lines, add shielding

### Power Issues
- **Random resets**: Add bulk capacitor (10µF+), check power supply current rating
- **WiFi fails**: Ensure power supply can handle 500mA peaks
- **Brown-out**: Use regulated 3.3V supply with low dropout

---

## References

- **ESP32 Datasheet**: [Espressif ESP32 Technical Reference](https://www.espressif.com/sites/default/files/documentation/esp32_datasheet_en.pdf)
- **ST7789 Datasheet**: ST7789V LCD Controller
- **XPT2046 Datasheet**: XPT2046 Touch Screen Controller
- **Pin Definitions**: See `lib/pins.py` in project source code

---

## Board Compatibility

This pin configuration is designed for the **ESP32-2432S028R** development board (also known as "Cheap Yellow Display" or CYD), which includes:
- ESP32-WROOM-32E module
- 2.8" ST7789 LCD (240×320)
- XPT2046 resistive touch
- SD card slot
- Audio amplifier

For other ESP32 boards, adjust pin definitions in `lib/pins.py` to match your hardware.
# ESP32 Glances Dashboard

[中文文档](README_CN.md) | English

A real-time server monitoring dashboard for ESP32 with touchscreen display, powered by MicroPython. Fetches and displays system metrics from [Glances](https://nicolargo.github.io/glances/) monitoring server over WiFi.

![License](https://img.shields.io/badge/license-AGPL--3.0--or--later-blue.svg)

## Features

- **Real-time Monitoring**: Live display of CPU, memory, disk, network, temperature, system load, and Docker container status
- **Visual Dashboard**: Color-coded metrics with progress bars and real-time CPU usage chart
- **WiFi Connectivity**: Automatic connection with animated boot sequence
- **Touchscreen Ready**: XPT2046 resistive touch controller support
- **Brightness Control**: Adjustable backlight via hardware button (long press to adjust, release to reverse direction)
- **Time Synchronization**: Automatic time sync from Glances server
- **Low Resource**: Optimized for ESP32 with efficient polling and incremental display updates

## Hardware Requirements

### Main Components
- **MCU**: ESP32-WROOM-32E-N4 board
- **Display**: ST7789 LCD, 240×320 pixels, SPI interface
- **Touch**: XPT2046 resistive touch controller
- **Button**: Boot button (GPIO0) for backlight control

### Pin Configuration

See [IO.md](IO.md) for complete pin mapping. Key connections:

**LCD (ST7789)**
- MOSI: GPIO13
- SCLK: GPIO14
- CS: GPIO15
- DC: GPIO2
- RST: GPIO12
- BL: GPIO21 (backlight PWM)

**Touch (XPT2046)**
- MOSI: GPIO32
- MISO: GPIO39
- SCLK: GPIO25
- CS: GPIO33
- IRQ: GPIO36

## Software Requirements

- **MicroPython**: v1.19 or later for ESP32
- **Glances Server**: v3.x or v4.x running on your monitoring target
- **Network**: ESP32 and Glances server must be on the same network or have network connectivity

## Installation

### 1. Flash MicroPython

Download and flash MicroPython firmware to your ESP32:

```bash
esptool.py --chip esp32 --port /dev/ttyUSB0 erase_flash
esptool.py --chip esp32 --port /dev/ttyUSB0 write_flash -z 0x1000 esp32-*.bin
```

### 2. Configure WiFi and Glances

Copy the example configuration and edit with your settings:

```bash
cp config.example.py config.py
```

Edit `config.py`:

```python
WIFI_SSID = "your-wifi-name"
WIFI_PASSWORD = "your-wifi-password"

GLANCES_BASE_URL = "http://192.168.1.100:61208"  # Your Glances server
HTTP_TIMEOUT_SECONDS = 2

REFRESH_INTERVAL_SECONDS = 5
```

### 3. Upload Files to ESP32

Upload all project files to your ESP32 using a tool like `ampy`, `rshell`, or Thonny IDE:

```bash
# Using ampy
ampy --port /dev/ttyUSB0 put boot.py
ampy --port /dev/ttyUSB0 put main.py
ampy --port /dev/ttyUSB0 put config.py
ampy --port /dev/ttyUSB0 put lib
```

### 4. Set Up Glances Server

On your monitoring target (Linux server, Raspberry Pi, etc.), install and run Glances:

```bash
# Install Glances
pip install glances

# Run in web server mode
glances -w --disable-plugin docker
```

Or with Docker support:

```bash
glances -w
```

Glances will start on port 61208 by default.

## Usage

### Starting the Dashboard

The dashboard starts automatically on boot. To manually start:

```python
import main
```

Or reset the ESP32 - `boot.py` will initialize the system and `main.py` will launch automatically.

### Brightness Control

- **Long press** the boot button (GPIO0): Brightness increases/decreases continuously
- **Release**: Direction reverses (if increasing, next press will decrease, and vice versa)

### Display Layout

The dashboard shows:

- **Header**: Glances server IP and connection status
- **CPU**: Usage percentage, frequency, and real-time usage chart
- **Memory**: Usage percentage with progress bar
- **Disk**: Usage percentage and used/total capacity
- **Network**: Upload/download rates and total transferred data
- **Temperature**: Highest sensor temperature with color coding (green < 50°C, orange < 70°C, red ≥ 70°C)
- **System Load**: 1-minute, 5-minute, and 15-minute load averages
- **Docker**: Running/stopped container counts
- **Uptime**: System uptime with live updates
- **Footer**: Current time (synced from server) and brightness level

### Troubleshooting

**WiFi connection fails**
- Verify SSID and password in `config.py`
- Check that your ESP32 is within WiFi range
- Ensure your network supports 2.4GHz (ESP32 doesn't support 5GHz)

**No data displayed**
- Verify Glances server is running: `curl http://your-server:61208/api/4/quicklook`
- Check `GLANCES_BASE_URL` in `config.py`
- Ensure firewall allows port 61208
- Check serial output for error messages

**Display issues**
- Verify pin connections match [IO.md](IO.md)
- Check SPI bus initialization in serial output
- Ensure adequate power supply (ESP32 + LCD can draw significant current)

**Slow updates**
- Reduce `REFRESH_INTERVAL_SECONDS` in `config.py` (minimum 1 second recommended)
- Check network latency between ESP32 and Glances server

## Project Structure

```
esp32-glances-dashboard/
├── boot.py                 # Boot initialization
├── main.py                 # Application entry point
├── config.example.py       # Configuration template
├── IO.md                  # Hardware pin mapping documentation
└── lib/
    ├── pins.py           # Pin definitions
    ├── wifi_client.py    # WiFi connection with boot animation
    ├── glances_client.py # Glances API client with polling
    ├── display.py        # ST7789 driver and dashboard UI
    └── backlight_button.py # Button handler for brightness control
```

## API Endpoints Used

The dashboard polls these Glances API v4 endpoints:

- `/api/4/quicklook` - CPU and memory (every 1s)
- `/api/4/network` - Network statistics (every 5s)
- `/api/4/load` - System load averages (every 5s)
- `/api/4/sensors` - Temperature sensors (every 5s)
- `/api/4/uptime` - System uptime (every 5min)
- `/api/4/fs` - Filesystem usage (every 10min)
- `/api/4/containers` - Docker containers (every 10min)
- `/api/4/now` - Server time for sync (every 5min)

## Customization

### Changing Colors

Edit color definitions in `lib/display.py`:

```python
class Display:
    BLACK = color565(0, 0, 0)
    WHITE = color565(220, 230, 235)
    CYAN = color565(50, 230, 245)
    GREEN = color565(100, 230, 80)
    # ... modify as needed
```

### Adjusting Polling Intervals

Edit task intervals in `lib/glances_client.py`:

```python
self.tasks = (
    {"name": "quicklook", "path": "/api/4/quicklook", "interval": 1000, ...},
    # interval in milliseconds
)
```

### Modifying Dashboard Layout

The layout is defined in `lib/display.py` in the `_draw_layout()` method. Adjust card positions and sizes:

```python
self._card(x, y, width, height, "TITLE", color)
```

## Performance

- **Memory**: ~50KB free RAM during operation
- **Network**: ~2-5KB/s average bandwidth usage
- **CPU**: Minimal ESP32 CPU usage, display updates are incremental
- **Power**: ~200-300mA @ 5V (varies with backlight brightness)

## License

This project is licensed under the **GNU Affero General Public License v3.0 or later** (AGPL-3.0-or-later).

See [LICENSE](LICENSE) for full license text.

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## Acknowledgments

- [Glances](https://nicolargo.github.io/glances/) - The monitoring tool that powers this dashboard
- [MicroPython](https://micropython.org/) - Python for microcontrollers
- ST7789 and XPT2046 driver implementations

## Links

- **Source Code**: https://github.com/en-nya/esp32-glances-dashboard
- **Glances Documentation**: https://glances.readthedocs.io/
- **MicroPython ESP32**: https://docs.micropython.org/en/latest/esp32/quickref.html

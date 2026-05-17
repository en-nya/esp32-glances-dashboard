# esp32-glances-dashboard

ESP32-32E MicroPython touchscreen dashboard for displaying Debian server status from Glances on the local network.

## Hardware

- ESP32-WROOM-32E-N4 board
- ST7789 LCD, 240x320
- XPT2046 resistive touch controller

Pin details are documented in `IO.md`.

## Current target

First milestone:

1. Connect ESP32 to Wi-Fi.
2. Fetch status data from Glances at `http://your-glances-host:61208/`.
3. Print selected metrics over serial.
4. Initialize the display layer placeholder for the next step.

## Files

- `boot.py` — boot-time network setup.
- `main.py` — application entrypoint.
- `config.example.py` — copy to `config.py` and fill in Wi-Fi credentials.
- `lib/pins.py` — board pin mapping from `IO.md`.
- `lib/glances_client.py` — minimal Glances HTTP client.
- `lib/display.py` — display abstraction placeholder.

## Setup

Copy the example config:

```python
cp config.example.py config.py
```

Then edit `config.py` with your Wi-Fi name and password.

`config.py` is ignored by Git because it may contain secrets.

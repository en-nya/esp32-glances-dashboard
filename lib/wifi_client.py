# SPDX-License-Identifier: AGPL-3.0-or-later

MIN_BOOT_MS = 2400
FRAME_MS = 120


def connect_wifi(display=None):
    import network
    import time

    try:
        from config import WIFI_SSID, WIFI_PASSWORD
    except ImportError:
        WIFI_SSID = ""
        WIFI_PASSWORD = ""

    if not WIFI_SSID:
        return None

    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    if not wlan.isconnected():
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)
        start = time.ticks_ms()
        frame = 0

        if display and display.ready:
            _boot_init(display)

        while True:
            connected = wlan.isconnected()
            elapsed = time.ticks_diff(time.ticks_ms(), start)
            if connected and elapsed >= MIN_BOOT_MS:
                break
            if display and display.ready:
                _boot_frame(display, frame, WIFI_SSID, connected)
            frame += 1
            time.sleep_ms(FRAME_MS)

    if wlan.isconnected():
        if display and display.ready:
            _boot_complete(display, wlan.ifconfig()[0])
        return wlan

    if display and display.ready:
        display.show_error("WiFi FAIL")
    return None


def _boot_init(display):
    display.lcd.fill(display.BG)
    display.lcd.fill_rect(0, 0, 320, 2, display.CYAN)
    display.lcd.fill_rect(0, 238, 320, 2, display.CYAN)
    display._text(10, 8, "ESP32 BOOT SEQUENCE", display.WHITE)
    display._text(240, 8, "v1.0", display.MUTED)


BOOT_LOG = [
    ("INIT", "System clock", 0),
    ("INIT", "Memory allocator", 0),
    ("INIT", "SPI bus", 0),
    ("INIT", "Display driver", 1),
    ("LOAD", "Network stack", 0),
    ("LOAD", "WiFi module", 0),
    ("SCAN", "Access points", 2),
    ("AUTH", "Handshake", 3),
    ("DHCP", "IP assignment", 3),
    ("LINK", "Established", 1),
]


def _boot_frame(display, frame, ssid, connected):
    log_idx = min(frame // 2, len(BOOT_LOG) - 1)
    if connected:
        log_idx = len(BOOT_LOG) - 1

    if frame % 2 == 0 and log_idx < len(BOOT_LOG):
        y = 32 + log_idx * 16
        tag, msg, color_idx = BOOT_LOG[log_idx]
        colors = (display.CYAN, display.GREEN, display.PURPLE, display.YELLOW)
        color = colors[color_idx]
        display._text(16, y, "[", display.MUTED)
        display._text(24, y, tag, color)
        display._text(24 + len(tag) * 8, y, "]", display.MUTED)
        display._text(24 + len(tag) * 8 + 8, y, msg, display.WHITE)
        if log_idx == len(BOOT_LOG) - 1:
            display._text(24 + len(tag) * 8 + 8 + len(msg) * 8 + 8, y, "OK", display.GREEN)

    _draw_status_bar(display, frame, ssid, connected)
    _draw_activity(display, frame, connected)


def _draw_status_bar(display, frame, ssid, connected):
    y = 210
    display.lcd.fill_rect(10, y, 300, 20, display.PANEL)
    display.lcd.fill_rect(10, y, 300, 1, display.BORDER)
    display.lcd.fill_rect(10, y + 19, 300, 1, display.BORDER)

    if connected:
        display._text(16, y + 6, "SSID: " + str(ssid)[:18], display.GREEN)
    else:
        dots = "." * ((frame // 3) % 4)
        display._text(16, y + 6, "Connecting" + dots + " " * (3 - len(dots)), display.CYAN)
        display._text(140, y + 6, str(ssid)[:12], display.MUTED)


def _draw_activity(display, frame, connected):
    if connected:
        return
    x_base = 280
    y_base = 215
    for i in range(3):
        offset = (frame + i * 3) % 9
        y = y_base + offset
        brightness = 255 - offset * 20
        color = display.CYAN if brightness > 128 else display.GRID
        display.lcd.fill_rect(x_base + i * 6, y, 4, 4, color)


def _boot_complete(display, ip):
    import time
    y = 32 + len(BOOT_LOG) * 16
    display._text(16, y, "[READY] IP: " + ip, display.GREEN)
    time.sleep_ms(600)


def _sin(angle):
    table = (0, 259, 500, 707, 866, 966, 1000, 966, 866, 707, 500, 259, 0, -259, -500, -707, -866, -966, -1000, -966, -866, -707, -500, -259)
    return table[(angle * 24 // 628) % 24]


def _cos(angle):
    return _sin(angle + 157)

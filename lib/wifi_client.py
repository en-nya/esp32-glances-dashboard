# SPDX-License-Identifier: AGPL-3.0-or-later
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

        for i in range(30):
            if wlan.isconnected():
                break
            if display and display.ready:
                progress = min(i * 3, 100)
                bar_len = progress // 10
                bar = "=" * bar_len + ">" + " " * (10 - bar_len)
                display.show_message("[{}] {}%".format(bar, progress))
            time.sleep(1)

    if wlan.isconnected():
        if display and display.ready:
            display.show_message("WiFi Connected!")
        return wlan

    if display and display.ready:
        display.show_error("WiFi FAIL")
    return None

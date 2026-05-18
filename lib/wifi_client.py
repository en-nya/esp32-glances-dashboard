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
        print("Wi-Fi is not configured. Copy config.example.py to config.py first.")
        return None

    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    if not wlan.isconnected():
        print("Connecting to Wi-Fi...")
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)

        anim = ["|", "/", "-", "\\"]
        for i in range(30):
            if wlan.isconnected():
                break
            if display and display.ready:
                display.show_message("WiFi {}".format(anim[i % 4]))
            time.sleep(1)

    if wlan.isconnected():
        print("Wi-Fi connected:", wlan.ifconfig())
        if display and display.ready:
            display.show_message("WiFi OK")
        return wlan

    print("Wi-Fi connection failed.")
    if display and display.ready:
        display.show_error("WiFi FAIL")
    return None

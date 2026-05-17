try:
    from config import WIFI_SSID, WIFI_PASSWORD
except ImportError:
    WIFI_SSID = ""
    WIFI_PASSWORD = ""


def connect_wifi():
    import network
    import time

    if not WIFI_SSID:
        print("Wi-Fi is not configured. Copy config.example.py to config.py first.")
        return None

    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    if not wlan.isconnected():
        print("Connecting to Wi-Fi...")
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)

        for _ in range(30):
            if wlan.isconnected():
                break
            time.sleep(1)

    if wlan.isconnected():
        print("Wi-Fi connected:", wlan.ifconfig())
        return wlan

    print("Wi-Fi connection failed.")
    return None


connect_wifi()

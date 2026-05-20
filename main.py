# SPDX-License-Identifier: AGPL-3.0-or-later
import time

from lib.backlight_button import BacklightButton
from lib.display import Display
from lib.glances_client import GlancesClient
from lib.wifi_client import connect_wifi

DRAW_FRAME_MS = 50


def main():
    display = Display()
    button = BacklightButton(display)

    connect_wifi(display)
    client = GlancesClient()
    force_draw = True
    last_draw = 0

    while True:
        now = time.ticks_ms()

        button.poll()

        try:
            if client.poll(now):
                force_draw = True
        except Exception:
            time.sleep_ms(100)

        if force_draw and time.ticks_diff(now, last_draw) >= DRAW_FRAME_MS:
            try:
                display.draw_dashboard(client.snapshot())
                force_draw = False
                last_draw = now
            except Exception:
                time.sleep_ms(100)

        time.sleep_ms(10)


main()

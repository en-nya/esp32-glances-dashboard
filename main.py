# SPDX-License-Identifier: AGPL-3.0-or-later
import time

from lib.backlight_button import BacklightButton
from lib.display import Display
from lib.glances_client import GlancesClient
from lib.wifi_client import connect_wifi

DRAW_FRAME_MS = 16


def main():
    display = Display()
    button = BacklightButton(display)

    connect_wifi()
    client = GlancesClient()
    force_draw = True

    while True:
        now = time.ticks_ms()

        button.poll()

        if client.poll(now):
            force_draw = True

        if force_draw:
            display.draw_dashboard(client.snapshot())
            force_draw = False

        time.sleep_ms(DRAW_FRAME_MS)


main()

# SPDX-License-Identifier: AGPL-3.0-or-later
from machine import Pin
from time import ticks_diff, ticks_ms

from lib.pins import BOOT_BUTTON


class BacklightButton:
    def __init__(self, display, long_press_ms=500, repeat_ms=35):
        self.display = display
        self.long_press_ms = long_press_ms
        self.repeat_ms = repeat_ms
        self.pin = Pin(BOOT_BUTTON, Pin.IN, Pin.PULL_UP)
        self.pressed_at = None
        self.next_step_at = None
        self.adjusting = False

    def poll(self):
        now = ticks_ms()
        pressed = self.pin.value() == 0

        if pressed and self.pressed_at is None:
            self.pressed_at = now
            self.next_step_at = None
            self.adjusting = False
            return False

        if pressed and not self.adjusting:
            if ticks_diff(now, self.pressed_at) >= self.long_press_ms:
                self.adjusting = True
                self.next_step_at = now

        if pressed and self.adjusting and ticks_diff(now, self.next_step_at) >= 0:
            self.display.step_brightness()
            self.next_step_at = now + self.repeat_ms
            return True

        if not pressed:
            if self.adjusting:
                self.display.reverse_brightness_direction()
            self.pressed_at = None
            self.next_step_at = None
            self.adjusting = False

        return False

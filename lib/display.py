class Display:
    def __init__(self):
        self.ready = False
        self._init_backlight()

    def show_message(self, message):
        print("DISPLAY:", message)

    def _init_backlight(self):
        try:
            from machine import Pin
            from lib.pins import LCD_BL

            Pin(LCD_BL, Pin.OUT).value(1)
            self.ready = True
        except Exception as exc:
            print("Display backlight init skipped:", exc)

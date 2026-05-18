# SPDX-License-Identifier: AGPL-3.0-or-later
from time import sleep_ms, ticks_diff, ticks_ms

from machine import Pin, SPI

from lib.pins import LCD_BL, LCD_CS, LCD_DC, LCD_MOSI, LCD_RST, LCD_SCLK


def color565(r, g, b):
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)


class ST7789:
    def __init__(self, spi, width, height, cs, dc, rst):
        self.spi = spi
        self.width = width
        self.height = height
        self.cs = cs
        self.dc = dc
        self.rst = rst
        self.cs.init(Pin.OUT, value=1)
        self.dc.init(Pin.OUT, value=0)
        self.rst.init(Pin.OUT, value=1)
        self._reset()
        self._init_display()

    def _reset(self):
        self.rst.value(1)
        sleep_ms(50)
        self.rst.value(0)
        sleep_ms(50)
        self.rst.value(1)
        sleep_ms(150)

    def _write(self, command=None, data=None):
        self.cs.value(0)
        if command is not None:
            self.dc.value(0)
            self.spi.write(bytearray([command]))
        if data:
            self.dc.value(1)
            self.spi.write(data)
        self.cs.value(1)

    def _init_display(self):
        self._write(0x01)
        sleep_ms(150)
        self._write(0x11)
        sleep_ms(150)
        self._write(0x3A, b"\x55")
        self._write(0x36, b"\x60")
        self._write(0x20)
        self._write(0x13)
        self._write(0x29)
        sleep_ms(50)

    def _set_window(self, x0, y0, x1, y1):
        self._write(0x2A, bytearray([x0 >> 8, x0 & 255, x1 >> 8, x1 & 255]))
        self._write(0x2B, bytearray([y0 >> 8, y0 & 255, y1 >> 8, y1 & 255]))
        self._write(0x2C)

    def fill_rect(self, x, y, w, h, color):
        if w <= 0 or h <= 0:
            return
        x = max(0, min(self.width - 1, x))
        y = max(0, min(self.height - 1, y))
        w = min(w, self.width - x)
        h = min(h, self.height - y)
        hi = color >> 8
        lo = color & 255
        chunk_pixels = min(w * h, 512)
        chunk = bytearray(chunk_pixels * 2)
        for index in range(0, len(chunk), 2):
            chunk[index] = hi
            chunk[index + 1] = lo
        remaining = w * h
        self._set_window(x, y, x + w - 1, y + h - 1)
        self.cs.value(0)
        self.dc.value(1)
        while remaining:
            count = min(remaining, chunk_pixels)
            self.spi.write(chunk[: count * 2])
            remaining -= count
            sleep_ms(0)
        self.cs.value(1)

    def fill(self, color):
        self.fill_rect(0, 0, self.width, self.height, color)


class Display:
    WIDTH = 320
    HEIGHT = 240

    BLACK = color565(0, 0, 0)
    BG = color565(0, 0, 0)
    PANEL = color565(1, 5, 9)
    BORDER = color565(18, 42, 50)
    GRID = color565(8, 18, 22)
    WHITE = color565(210, 220, 224)
    MUTED = color565(90, 110, 118)
    CYAN = color565(35, 220, 235)
    GREEN = color565(88, 220, 70)
    ORANGE = color565(255, 155, 18)
    RED = color565(245, 70, 70)

    BRIGHTNESS_LEVELS = (20, 35, 50, 70, 85, 100)

    def __init__(self):
        self.ready = False
        self.brightness = 70
        self.brightness_direction = 1
        self.layout_drawn = False
        self.last_error = None
        self.fields = {}
        self._init_backlight()
        self._init_lcd()

    def set_brightness(self, level):
        level = max(1, min(100, int(level)))
        self.brightness = level
        if hasattr(self, "backlight_pwm") and self.backlight_pwm:
            self.backlight_pwm.duty(int(level * 1023 / 100))
        else:
            self.backlight.value(1 if level else 0)

    def step_brightness(self):
        next_level = self.brightness + self.brightness_direction * 5
        if next_level >= 100:
            next_level = 100
        elif next_level <= 1:
            next_level = 1
        self.set_brightness(next_level)
        self.fields.pop("footer_bright", None)
        self._draw_footer()
        return self.brightness

    def reverse_brightness_direction(self):
        self.brightness_direction = -self.brightness_direction

    def adjust_brightness(self):
        return self.step_brightness()

    def next_brightness(self):
        return self.adjust_brightness()

    def show_message(self, message):
        print("DISPLAY:", message)
        if self.ready:
            self._draw_layout(force=True)
            self._field("footer_left", 8, 224, 180, 8, str(message)[:24], self.MUTED)

    def show_error(self, message, status=None):
        print("DISPLAY ERROR:", message)
        self.last_error = str(message)[:24]
        if status:
            self.draw_dashboard(status, self.last_error)
        elif self.ready:
            self._field("footer_left", 8, 224, 200, 8, "ERR " + self.last_error, self.RED)

    def draw_dashboard(self, status, error=None):
        if not self.ready:
            return
        if error != self.last_error:
            self.last_error = error
        self._draw_layout()
        self._update_header(status)
        self._update_cpu(status)
        self._update_memory(status)
        self._update_disk(status)
        self._update_network(status)
        self._update_temp(status)
        self._update_uptime(status)
        self._update_load(status)
        self._update_docker(status)
        self._draw_footer()

    def _init_backlight(self):
        self.backlight = Pin(LCD_BL, Pin.OUT)
        try:
            from machine import PWM

            self.backlight_pwm = PWM(self.backlight, freq=1000)
        except Exception:
            self.backlight_pwm = None
        self.set_brightness(self.brightness)

    def _init_lcd(self):
        try:
            spi = SPI(1, baudrate=40000000, polarity=0, phase=0, sck=Pin(LCD_SCLK), mosi=Pin(LCD_MOSI))
            self.lcd = ST7789(spi, self.WIDTH, self.HEIGHT, Pin(LCD_CS), Pin(LCD_DC), Pin(LCD_RST))
            self.ready = True
            self.lcd.fill(self.BG)
        except Exception as exc:
            self.ready = False
            print("Display init failed:", exc)

    def _draw_layout(self, force=False):
        if self.layout_drawn and not force:
            return
        self.lcd.fill(self.BG)
        self._rect(4, 4, 312, 22, self.BORDER)
        self._text(10, 10, "pi-server", self.WHITE)
        self._text(96, 10, "|", self.MUTED)
        self._text(116, 10, "192.168.8.103", self.WHITE)
        self._text(252, 10, "ONLINE", self.GREEN)
        self.lcd.fill_rect(302, 11, 8, 8, self.GREEN)
        self._card(4, 30, 102, 72, "CPU", self.CYAN)
        self._card(110, 30, 102, 72, "MEM", self.CYAN)
        self._card(216, 30, 100, 72, "DISK", self.GREEN)
        self._card(4, 106, 124, 54, "NETWORK", self.CYAN)
        self._text(12, 126, "U", self.MUTED)
        self._text(82, 126, "/s", self.MUTED)
        self._text(12, 144, "D", self.MUTED)
        self._text(82, 144, "/s", self.MUTED)
        self._card(132, 106, 74, 54, "TEMP", self.ORANGE)
        self._card(210, 106, 106, 54, "UPTIME", self.CYAN)
        self._card(4, 164, 102, 52, "DOCKER", self.CYAN)
        self._card(110, 164, 206, 52, "LOAD", self.CYAN)
        self.layout_drawn = True

    def _card(self, x, y, w, h, title, color):
        self._rect(x, y, w, h, self.BORDER)
        self._text(x + 5, y + 5, title, color)

    def _rect(self, x, y, w, h, color):
        self.lcd.fill_rect(x, y, w, 1, color)
        self.lcd.fill_rect(x, y + h - 1, w, 1, color)
        self.lcd.fill_rect(x, y, 1, h, color)
        self.lcd.fill_rect(x + w - 1, y, 1, h, color)

    def _update_header(self, status):
        return

    def _update_cpu(self, status):
        self._field_big("cpu", 10, 50, 94, 20, status.get("cpu_percent"), self.CYAN)
        self._field("cpu_load", 10, 82, 92, 8, "L " + self._load_short(status.get("load")), self.MUTED)

    def _update_memory(self, status):
        self._field_big("mem", 116, 50, 94, 20, status.get("mem_percent"), self.CYAN)
        self._bar(116, 84, 86, 6, status.get("mem_percent"), self.CYAN)

    def _update_disk(self, status):
        self._field_big("disk", 222, 50, 92, 20, status.get("disk_percent"), self.GREEN)
        self._field("disk_size", 222, 82, 88, 8, self._bytes_pair(status.get("disk_used"), status.get("disk_size")), self.MUTED)

    def _update_network(self, status):
        self._field("net_up", 30, 126, 50, 8, self._rate(status.get("net_tx_rate")), self.CYAN)
        self._field("net_dn", 30, 144, 50, 8, self._rate(status.get("net_rx_rate")), self.GREEN)

    def _update_temp(self, status):
        self._field("temp", 138, 134, 56, 8, self._temp(status.get("temperature")), self.ORANGE)

    def _update_uptime(self, status):
        self._field("uptime", 216, 134, 92, 8, self._uptime(status.get("uptime")), self.CYAN)

    def _update_load(self, status):
        load = status.get("load")
        if load and load[0] is not None:
            self._field("load1", 116, 186, 88, 8, "1m {:.2f}".format(load[0]), self.CYAN)
            load5 = "--" if len(load) < 2 or load[1] is None else "{:.1f}".format(load[1])
            load15 = "--" if len(load) < 3 or load[2] is None else "{:.1f}".format(load[2])
            self._field("load2", 116, 202, 88, 8, "5m {} 15m {}".format(load5, load15), self.MUTED)
        else:
            self._field("load1", 116, 194, 40, 8, "--", self.CYAN)

    def _update_docker(self, status):
        total = status.get("docker_total")
        running = status.get("docker_running")
        if total is None:
            self._field("docker", 12, 186, 86, 8, "--", self.MUTED)
        else:
            stopped = total - running
            self._field("docker_top", 12, 186, 88, 8, "RUN {}/{}".format(running, total), self.GREEN if stopped == 0 else self.WHITE)
            self._field("docker_mid", 12, 202, 88, 8, "STOP {}".format(stopped), self.RED if stopped else self.MUTED)

    def _draw_footer(self):
        if self.last_error:
            self._field("footer_left", 8, 224, 200, 8, "ERR " + self.last_error[:24], self.RED)
        else:
            self._field("footer_left", 8, 224, 120, 8, "60Hz async", self.MUTED)
        self._field("footer_bright", 218, 224, 92, 8, "Light {}%".format(self.brightness), self.MUTED)

    def _field(self, key, x, y, w, h, text, color):
        text = str(text)
        if self.fields.get(key) == text:
            return
        self.fields[key] = text
        self._clear_value(x, y, w, h)
        self._text(x, y, text, color)

    def _field_big(self, key, x, y, w, h, value, color):
        text = "--%" if value is None else "{:.1f}%".format(value)
        if self.fields.get(key) == text:
            return
        self.fields[key] = text
        self._clear_value(x, y, w, h)
        self._text_big(x, y, text, color)

    def _clear_value(self, x, y, w, h):
        self.lcd.fill_rect(x, y, w, h, self.PANEL if y > 26 and y < 218 else self.BG)

    def _text(self, x, y, text, color, bg=None):
        try:
            import framebuf

            text = str(text)
            bg_color = self.PANEL if bg is None else bg
            width = max(1, len(text) * 8)
            buf = bytearray(width * 8 * 2)
            fb = framebuf.FrameBuffer(buf, width, 8, framebuf.RGB565)
            fb.fill(bg_color)
            fb.text(text, 0, 0, color)
            for index in range(0, len(buf), 2):
                buf[index], buf[index + 1] = buf[index + 1], buf[index]
            self.lcd._set_window(x, y, x + width - 1, y + 7)
            self.lcd.cs.value(0)
            self.lcd.dc.value(1)
            self.lcd.spi.write(buf)
            self.lcd.cs.value(1)
        except Exception as exc:
            print("Text draw failed:", exc)

    def _text_big(self, x, y, text, color):
        try:
            import framebuf

            text = str(text)
            width = max(1, len(text) * 16)
            height = 16
            buf = bytearray(width * height * 2)
            fb = framebuf.FrameBuffer(buf, width, height, framebuf.RGB565)
            fb.fill(self.BG)
            for index, ch in enumerate(text):
                bx = index * 16
                fb.text(ch, bx, 0, color)
            for index in range(0, len(buf), 2):
                buf[index], buf[index + 1] = buf[index + 1], buf[index]
            self.lcd._set_window(x, y, x + width - 1, y + height - 1)
            self.lcd.cs.value(0)
            self.lcd.dc.value(1)
            self.lcd.spi.write(buf)
            self.lcd.cs.value(1)
            sleep_ms(0)
        except Exception as exc:
            print("Big text draw failed:", exc)

    def _draw_big_char(self, fb, x, y, ch, color):
        fb.text(ch, x, y, color)
        fb.text(ch, x + 1, y, color)

    def _text_scaled(self, x, y, text, color, scale):
        self._text(x, y, text, color)

    def _draw_char_scaled(self, x, y, ch, color, scale, source_row):
        return

    def _bar(self, x, y, w, h, percent, color):
        self.lcd.fill_rect(x, y, w, h, self.GRID)
        if percent is not None:
            self.lcd.fill_rect(x, y, int(w * max(0, min(100, percent)) / 100), h, color)

    def _rate(self, value):
        if value is None:
            return "--"
        if value >= 1024 * 1024:
            return "{:.1f}M".format(value / 1024 / 1024)
        if value >= 1024:
            return "{:.0f}K".format(value / 1024)
        return "{}B".format(int(value))

    def _temp(self, value):
        return "--C" if value is None else "{:.0f}C".format(value)

    def _uptime(self, value):
        if not value:
            return "--"
        value = str(value)
        if "day" in value:
            days = value.split(" day")[0].strip()
            rest = value.split(",", 1)[1].strip() if "," in value else "0:00"
            parts = rest.split(":")
            hours = parts[0] if len(parts) > 0 else "0"
            minutes = parts[1] if len(parts) > 1 else "00"
            return "{}d{}h{}m".format(days, hours, minutes)
        parts = value.split(":")
        if len(parts) >= 2:
            return "{}h{}m".format(parts[0], parts[1])
        return value[:10]

    def _load_short(self, value):
        if not value:
            return "--"
        return "{:.1f}".format(value[0])

    def _bytes_pair(self, used, size):
        if used is None or size is None:
            return "--"
        return "{:.0f}/{:.0f}G".format(used / 1024 / 1024 / 1024, size / 1024 / 1024 / 1024)

    def _percent(self, value):
        if value is None:
            return "--%"
        return "{:>4.1f}%".format(value)

    def _load(self, value):
        if not value:
            return "-- -- --"
        parts = []
        for item in value:
            if item is None:
                parts.append("--")
            else:
                parts.append("{:.2f}".format(item))
        while len(parts) < 3:
            parts.append("--")
        return "{} {} {}".format(parts[0], parts[1], parts[2])

    def _docker(self, status):
        total = status.get("docker_total")
        running = status.get("docker_running")
        if total is None:
            return "--"
        return "{}/{} running".format(running, total)

    def _serial_line(self, status, error):
        return "CPU {} MEM {} DISK {} NET {}/{} TEMP {} LOAD {} DOCKER {}{}".format(
            self._percent(status.get("cpu_percent")),
            self._percent(status.get("mem_percent")),
            self._percent(status.get("disk_percent")),
            self._rate(status.get("net_tx_rate")),
            self._rate(status.get("net_rx_rate")),
            self._temp(status.get("temperature")),
            self._load(status.get("load")),
            self._docker(status),
            " ERR " + error if error else "",
        )

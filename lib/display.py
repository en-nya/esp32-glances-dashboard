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
        chunk_pixels = min(w * h, 256)
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
            if remaining > 0:
                sleep_ms(1)
        self.cs.value(1)

    def fill(self, color):
        self.fill_rect(0, 0, self.width, self.height, color)


class Display:
    WIDTH = 320
    HEIGHT = 240

    BLACK = color565(0, 0, 0)
    BG = color565(0, 0, 0)
    PANEL = color565(2, 8, 12)
    BORDER = color565(25, 50, 60)
    GRID = color565(12, 25, 30)
    WHITE = color565(220, 230, 235)
    MUTED = color565(100, 120, 130)
    CYAN = color565(50, 230, 245)
    GREEN = color565(100, 230, 80)
    ORANGE = color565(255, 165, 30)
    RED = color565(255, 80, 80)
    BLUE = color565(60, 150, 255)
    PURPLE = color565(180, 100, 255)
    YELLOW = color565(255, 220, 50)

    BRIGHTNESS_LEVELS = (20, 35, 50, 70, 85, 100)

    def __init__(self):
        self.ready = False
        self.brightness = 70
        self.brightness_direction = 1
        self.layout_drawn = False
        self.last_error = None
        self.fields = {}
        self.cpu_history = []
        self.cpu_chart_x = 0
        self.cpu_chart_prev_y = None
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
        self._field("footer_bright", 218, 224, 92, 8, "Light {}%".format(self.brightness), self.MUTED)
        return self.brightness

    def reverse_brightness_direction(self):
        self.brightness_direction = -self.brightness_direction

    def adjust_brightness(self):
        return self.step_brightness()

    def next_brightness(self):
        return self.adjust_brightness()

    def show_message(self, message):
        if self.ready:
            self._draw_layout(force=True)
            self._field("footer_left", 8, 224, 180, 8, str(message)[:24], self.MUTED)

    def show_error(self, message, status=None):
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
        self._draw_footer(status)

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
            spi = SPI(1, baudrate=80000000, polarity=0, phase=0, sck=Pin(LCD_SCLK), mosi=Pin(LCD_MOSI))
            self.lcd = ST7789(spi, self.WIDTH, self.HEIGHT, Pin(LCD_CS), Pin(LCD_DC), Pin(LCD_RST))
            self.ready = True
            self.lcd.fill(self.BG)
        except Exception:
            self.ready = False

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
        self._card(4, 30, 102, 130, "CPU", self.BLUE)
        self._card(110, 30, 102, 72, "MEM", self.PURPLE)
        self._card(216, 30, 100, 72, "DISK", self.GREEN)
        self._card(110, 106, 80, 54, "DOCKER", self.BLUE)
        self._card(194, 106, 122, 54, "UPTIME", self.PURPLE)
        self._card(4, 164, 128, 52, "NETWORK", self.CYAN)
        self._text(12, 184, "U", self.MUTED)
        self._text(100, 184, "/s", self.MUTED)
        self._text(12, 202, "D", self.MUTED)
        self._text(100, 202, "/s", self.MUTED)
        self._card(136, 164, 124, 52, "LOAD", self.YELLOW)
        self._card(264, 164, 52, 52, "TEMP", self.ORANGE)
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
        cpu = status.get("cpu_percent")
        self._field_big("cpu", 10, 50, 94, 20, cpu, self.BLUE)
        load = status.get("load")
        if load and load[0] is not None:
            self._field("cpu_freq", 10, 74, 92, 8, "Load {:.2f}".format(load[0]), self.MUTED)

        if cpu is not None:
            self._update_cpu_chart_column(int(cpu))

    def _update_memory(self, status):
        self._field_big("mem", 116, 50, 94, 20, status.get("mem_percent"), self.PURPLE)
        self._bar(116, 84, 86, 6, status.get("mem_percent"), self.PURPLE)

    def _update_disk(self, status):
        self._field_big("disk", 222, 50, 92, 20, status.get("disk_percent"), self.GREEN)
        self._field("disk_size", 222, 82, 88, 8, self._bytes_pair(status.get("disk_used"), status.get("disk_size")), self.MUTED)

    def _update_network(self, status):
        rate_up = self._rate(status.get("net_tx_rate"))
        total_up = self._bytes_compact(status.get("net_tx_total"))
        rate_dn = self._rate(status.get("net_rx_rate"))
        total_dn = self._bytes_compact(status.get("net_rx_total"))
        self._field("net_up", 30, 184, 96, 8, "{}/s {}".format(rate_up, total_up), self.CYAN)
        self._field("net_dn", 30, 202, 96, 8, "{}/s {}".format(rate_dn, total_dn), self.GREEN)

    def _update_temp(self, status):
        temp = status.get("temperature")
        if temp is None:
            color = self.MUTED
        elif temp < 50:
            color = self.GREEN
        elif temp < 70:
            color = self.ORANGE
        else:
            color = self.RED
        self._text(269, 169, "TEMP", color)
        self._field("temp", 270, 192, 42, 8, self._temp(temp), color)

    def _update_uptime(self, status):
        self._field("uptime", 200, 134, 108, 8, self._uptime(status.get("uptime")), self.PURPLE)

    def _update_load(self, status):
        load = status.get("load")
        if load and load[0] is not None:
            self._field("load1", 142, 186, 58, 8, "1m {:.2f}".format(load[0]), self.YELLOW)
            load5 = "--" if len(load) < 2 or load[1] is None else "{:.1f}".format(load[1])
            load15 = "--" if len(load) < 3 or load[2] is None else "{:.1f}".format(load[2])
            self._field("load2", 142, 202, 58, 8, "5m {} 15m ".format(load5, load15), self.MUTED)
        else:
            self._field("load1", 142, 194, 40, 8, "--", self.YELLOW)

    def _update_docker(self, status):
        total = status.get("docker_total")
        running = status.get("docker_running")
        if total is None:
            self._field("docker", 116, 128, 68, 8, "--", self.MUTED)
        else:
            stopped = total - running
            self._field("docker_top", 116, 128, 68, 8, "RUN {}/{}".format(running, total), self.GREEN if stopped == 0 else self.BLUE)
            self._field("docker_mid", 116, 144, 68, 8, "STOP {}".format(stopped), self.RED if stopped else self.MUTED)

    def _draw_footer(self, status=None):
        if self.last_error:
            self._field("footer_left", 8, 224, 200, 8, "ERR " + self.last_error[:24], self.RED)
        else:
            time_str = status.get('current_time') if status else None
            if time_str:
                self._field("footer_left", 8, 224, 120, 8, time_str, self.CYAN)
            else:
                self._field("footer_left", 8, 224, 120, 8, "Syncing...", self.MUTED)
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
        except Exception:
            pass

    def _text_big(self, x, y, text, color):
        try:
            import framebuf

            text = str(text)
            char_spacing = 9
            src_width = len(text) * char_spacing
            src_height = 8
            src_buf = bytearray(src_width * src_height * 2)
            src_fb = framebuf.FrameBuffer(src_buf, src_width, src_height, framebuf.RGB565)
            src_fb.fill(self.PANEL)
            for index, ch in enumerate(text):
                bx = index * char_spacing
                src_fb.text(ch, bx, 0, color)

            dst_width = src_width * 2
            dst_height = src_height * 2 + 4
            dst_buf = bytearray(dst_width * dst_height * 2)
            dst_fb = framebuf.FrameBuffer(dst_buf, dst_width, dst_height, framebuf.RGB565)
            dst_fb.fill(self.PANEL)

            for sy in range(src_height):
                for sx in range(src_width):
                    pixel = src_fb.pixel(sx, sy)
                    dst_fb.pixel(sx * 2, sy * 2, pixel)
                    dst_fb.pixel(sx * 2 + 1, sy * 2, pixel)
                    dst_fb.pixel(sx * 2, sy * 2 + 1, pixel)
                    dst_fb.pixel(sx * 2 + 1, sy * 2 + 1, pixel)

            for index in range(0, len(dst_buf), 2):
                dst_buf[index], dst_buf[index + 1] = dst_buf[index + 1], dst_buf[index]
            self.lcd._set_window(x, y, x + dst_width - 1, y + dst_height - 1)
            self.lcd.cs.value(0)
            self.lcd.dc.value(1)
            self.lcd.spi.write(dst_buf)
            self.lcd.cs.value(1)
            sleep_ms(1)
        except Exception:
            pass

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

    def _bytes_compact(self, value):
        if value is None:
            return "--"
        if value >= 1024 * 1024 * 1024:
            v = value / 1024 / 1024 / 1024
            return "{:.1f}G".format(v) if v < 100 else "{:.0f}G".format(v)
        if value >= 1024 * 1024:
            v = value / 1024 / 1024
            return "{:.1f}M".format(v) if v < 100 else "{:.0f}M".format(v)
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
            rest = value.split(",", 1)[1].strip() if "," in value else "0:00:00"
            return "{}Day {}".format(days, rest)
        return value

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

    def _draw_cpu_chart(self, x, y, w, h):
        self.lcd.fill_rect(x, y, w, h, self.PANEL)

        for percent in (25, 50, 75):
            line_y = y + h - int(percent * h / 100)
            for i in range(0, w, 4):
                self.lcd.fill_rect(x + i, line_y, 2, 1, self.GRID)

        if len(self.cpu_history) < 2:
            return

        step = max(1, w // len(self.cpu_history))
        for i in range(len(self.cpu_history) - 1):
            v1 = self.cpu_history[i]
            v2 = self.cpu_history[i + 1]
            y1 = y + h - int(v1 * h / 100)
            y2 = y + h - int(v2 * h / 100)
            x1 = x + i * step
            x2 = x + (i + 1) * step
            self.lcd.fill_rect(x1, y1, 1, 1, self.BLUE)
            if abs(x2 - x1) <= 1 and abs(y2 - y1) <= 1:
                self.lcd.fill_rect(x2, y2, 1, 1, self.BLUE)
            else:
                dx = x2 - x1
                dy = y2 - y1
                steps = max(abs(dx), abs(dy))
                if steps > 0:
                    for s in range(steps + 1):
                        px = x1 + s * dx // steps
                        py = y1 + s * dy // steps
                        self.lcd.fill_rect(px, py, 1, 1, self.BLUE)

    def _update_cpu_chart_column(self, cpu_value):
        x, y, w, h = 10, 86, 92, 60

        if self.cpu_chart_x >= w:
            self.lcd.fill_rect(x, y, w, h, self.PANEL)
            for percent in (25, 50, 75):
                line_y = y + h - int(percent * h / 100)
                for i in range(0, w, 4):
                    self.lcd.fill_rect(x + i, line_y, 2, 1, self.GRID)
            self.cpu_chart_x = 0
            self.cpu_chart_prev_y = None

        new_y = y + h - int(cpu_value * h / 100)
        col_x = x + self.cpu_chart_x

        self.lcd.fill_rect(col_x, y, 1, h, self.PANEL)

        for percent in (25, 50, 75):
            line_y = y + h - int(percent * h / 100)
            if line_y >= y and line_y < y + h:
                self.lcd.fill_rect(col_x, line_y, 1, 1, self.GRID)

        if self.cpu_chart_prev_y is not None:
            dy = abs(new_y - self.cpu_chart_prev_y)
            if dy <= 1:
                self.lcd.fill_rect(col_x, new_y, 1, 1, self.BLUE)
            elif dy < 20:
                steps = dy
                dy_sign = 1 if new_y > self.cpu_chart_prev_y else -1
                for s in range(steps + 1):
                    py = self.cpu_chart_prev_y + s * dy_sign
                    self.lcd.fill_rect(col_x, py, 1, 1, self.BLUE)
            else:
                self.lcd.fill_rect(col_x, self.cpu_chart_prev_y, 1, 1, self.BLUE)
                self.lcd.fill_rect(col_x, new_y, 1, 1, self.BLUE)
        else:
            self.lcd.fill_rect(col_x, new_y, 1, 1, self.BLUE)

        self.cpu_chart_prev_y = new_y
        self.cpu_chart_x += 1


    def _draw_line(self, x1, y1, x2, y2, color):
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy
        while True:
            self.lcd.fill_rect(x1, y1, 2, 2, color)
            if x1 == x2 and y1 == y2:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x1 += sx
            if e2 < dx:
                err += dx
                y1 += sy

    def _draw_line_fb(self, fb, x1, y1, x2, y2, color):
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy
        while True:
            fb.pixel(x1, y1, color)
            if x1 == x2 and y1 == y2:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x1 += sx
            if e2 < dx:
                err += dx
                y1 += sy


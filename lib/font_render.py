# SPDX-License-Identifier: AGPL-3.0-or-later
import framebuf

class FontRenderer:
    def __init__(self, display, font_module=None):
        self.display = display
        self.font = None
        if font_module:
            self.load_font(font_module)

    def load_font(self, font_module):
        try:
            self.font = __import__(font_module, globals(), locals(), ['GLYPHS', 'FONT_HEIGHT'])
        except Exception:
            self.font = None

    def get_text_width(self, text):
        if not self.font or not hasattr(self.font, 'GLYPHS'):
            return len(text) * 8
        width = 0
        for char in str(text):
            if char in self.font.GLYPHS:
                width += self.font.GLYPHS[char]['width']
        return width

    def render_text(self, x, y, text, color, bg_color=None):
        if not self.font or not hasattr(self.font, 'GLYPHS'):
            return self._render_fallback(x, y, text, color, bg_color)

        text = str(text)
        if bg_color is None:
            bg_color = self.display.PANEL

        cursor_x = x
        for char in text:
            if char not in self.font.GLYPHS:
                cursor_x += 6
                continue

            glyph = self.font.GLYPHS[char]
            w, h = glyph['width'], glyph['height']
            data = glyph['data']

            buf = bytearray(w * h * 2)
            fb = framebuf.FrameBuffer(buf, w, h, framebuf.RGB565)
            fb.fill(bg_color)

            for py in range(h):
                for px in range(w):
                    if data[py * w + px]:
                        fb.pixel(px, py, color)

            for i in range(0, len(buf), 2):
                buf[i], buf[i + 1] = buf[i + 1], buf[i]

            self.display.lcd._set_window(cursor_x, y, cursor_x + w - 1, y + h - 1)
            self.display.lcd.cs.value(0)
            self.display.lcd.dc.value(1)
            self.display.lcd.spi.write(buf)
            self.display.lcd.cs.value(1)

            cursor_x += w

    def _render_fallback(self, x, y, text, color, bg_color):
        text = str(text)
        if bg_color is None:
            bg_color = self.display.PANEL
        width = max(1, len(text) * 8)
        buf = bytearray(width * 8 * 2)
        fb = framebuf.FrameBuffer(buf, width, 8, framebuf.RGB565)
        fb.fill(bg_color)
        fb.text(text, 0, 0, color)
        for i in range(0, len(buf), 2):
            buf[i], buf[i + 1] = buf[i + 1], buf[i]
        self.display.lcd._set_window(x, y, x + width - 1, y + 7)
        self.display.lcd.cs.value(0)
        self.display.lcd.dc.value(1)
        self.display.lcd.spi.write(buf)
        self.display.lcd.cs.value(1)

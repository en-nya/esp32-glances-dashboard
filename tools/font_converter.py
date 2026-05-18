#!/usr/bin/env python3
# Font converter for MicroPython
from PIL import Image, ImageDraw, ImageFont
import sys

def convert_font(ttf_path, output_path, size=16, chars=None):
    """Convert TTF font to MicroPython format"""
    if chars is None:
        # Default character set for dashboard
        chars = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz .-:/%°CKMGBDayRunStopONLINE'

    font = ImageFont.truetype(ttf_path, size)
    glyphs = {}

    for char in chars:
        # Create image for character
        bbox = font.getbbox(char)
        width = bbox[2] - bbox[0] + 2
        height = size + 4

        img = Image.new('1', (width, height), 0)
        draw = ImageDraw.Draw(img)
        draw.text((1, 0), char, font=font, fill=1)

        # Convert to bytes
        pixels = []
        for y in range(height):
            for x in range(width):
                if img.getpixel((x, y)):
                    pixels.append(1)
                else:
                    pixels.append(0)

        glyphs[char] = {
            'width': width,
            'height': height,
            'data': pixels
        }

    # Generate Python code
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('# Auto-generated font file\n')
        f.write(f'# Size: {size}px\n\n')
        f.write('FONT_HEIGHT = {}\n\n'.format(size + 4))
        f.write('GLYPHS = {\n')

        for char, glyph in glyphs.items():
            char_repr = repr(char)
            f.write(f'    {char_repr}: {{\n')
            f.write(f'        "width": {glyph["width"]},\n')
            f.write(f'        "height": {glyph["height"]},\n')
            f.write(f'        "data": bytes({bytes(glyph["data"])})\n')
            f.write('    },\n')

        f.write('}\n')

    print(f'Font converted: {len(glyphs)} characters')
    print(f'Output: {output_path}')

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print('Usage: python font_converter.py <ttf_path> <output_path> [size]')
        sys.exit(1)

    ttf_path = sys.argv[1]
    output_path = sys.argv[2]
    size = int(sys.argv[3]) if len(sys.argv) > 3 else 16

    convert_font(ttf_path, output_path, size)

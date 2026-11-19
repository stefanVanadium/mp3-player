"""Screen texture for the renders: a 128 x 128 "now playing" frame, the size of the
LS013B7DH03 (1-bit memory LCD), scaled up with nearest neighbour.
Run: .venv/bin/python render/screen.py  ->  out/screen.png
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).parent.parent / "out"
FONT = str(Path.home() / ".local/share/fonts/Inter/InterVariable.ttf")
ON, OFF = (30, 32, 34), (196, 198, 190)   # dark pixels on the reflective panel

im = Image.new("RGB", (128, 128), OFF)
d = ImageDraw.Draw(im)
small = ImageFont.truetype(FONT, 9)
mid = ImageFont.truetype(FONT, 11)
big = ImageFont.truetype(FONT, 13)
# status bar: track count + battery
d.text((4, 2), "3 / 12", font=small, fill=ON)
d.rectangle((104, 4, 121, 11), outline=ON)
d.rectangle((122, 6, 123, 9), fill=ON)
d.rectangle((106, 6, 117, 9), fill=ON)
d.line((0, 15, 127, 15), fill=ON)
# cover art: concentric record
for r in range(22, 4, -3):
    d.ellipse((64 - r, 42 - r, 64 + r, 42 + r), outline=ON)
d.ellipse((60, 38, 68, 46), fill=ON)
# title / artist
def centre(y, text, font):
    w = d.textlength(text, font=font)
    d.text(((128 - w) / 2, y), text, font=font, fill=ON)
centre(68, "Night Drive", big)
centre(85, "Analog Hearts", mid)
# progress
d.rectangle((8, 104, 119, 107), outline=ON)
d.rectangle((8, 104, 54, 107), fill=ON)
d.text((8, 111), "1:42", font=small, fill=ON)
d.text((99, 111), "4:03", font=small, fill=ON)
im = im.convert("1", dither=Image.Dither.NONE).convert("RGB")
im = Image.eval(im, lambda v: v)  # keep 1-bit look
px = im.load()
for y in range(128):
    for x in range(128):
        px[x, y] = ON if px[x, y][0] < 128 else OFF
im.resize((1024, 1024), Image.NEAREST).save(OUT / "screen.png")
print(OUT / "screen.png")

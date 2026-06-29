"""Generate CAP AI logo PNG."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parent.parent / "assets" / "cap_ai_logo.png"

img = Image.new("RGBA", (360, 80), (255, 255, 255, 0))
draw = ImageDraw.Draw(img)
draw.rounded_rectangle([4, 8, 68, 72], radius=14, fill=(31, 78, 121))
draw.polygon([(22, 48), (36, 22), (50, 48)], fill=(255, 255, 255))
draw.ellipse([30, 32, 42, 44], fill=(0, 174, 239))
try:
    font_b = ImageFont.truetype("arial.ttf", 26)
    font_s = ImageFont.truetype("arial.ttf", 20)
    font_t = ImageFont.truetype("arial.ttf", 10)
except OSError:
    font_b = ImageFont.load_default()
    font_s = font_b
    font_t = font_b
draw.text((82, 10), "CAP", fill=(31, 78, 121), font=font_b)
draw.text((82, 36), "AI", fill=(0, 174, 239), font=font_s)
draw.text((140, 38), "ELECTION & COMPLIANCE", fill=(100, 116, 139), font=font_t)
OUT.parent.mkdir(parents=True, exist_ok=True)
img.save(OUT)
print(f"Created {OUT}")

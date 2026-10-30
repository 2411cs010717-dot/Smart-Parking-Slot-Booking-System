"""
Creates a small synthetic dataset so students can test the CNN workflow without a camera.
These are simple illustrative images, not a replacement for a real-world parking dataset.
"""
import os, random
from PIL import Image, ImageDraw
random.seed(17)
ROOT = os.path.join(os.path.dirname(__file__), "dataset")
SIZE = 128

def make_image(occupied):
    im = Image.new("RGB", (SIZE, SIZE), (90, 105, 100))
    d = ImageDraw.Draw(im)
    # asphalt texture
    for _ in range(300):
        x, y = random.randrange(SIZE), random.randrange(SIZE)
        shade = random.randrange(75, 125)
        d.point((x, y), fill=(shade, shade, shade))
    # bay boundary lines
    d.line((8, 0, 8, 127), fill=(235, 235, 210), width=3)
    d.line((120, 0, 120, 127), fill=(235, 235, 210), width=3)
    d.line((8, 8, 120, 8), fill=(235, 235, 210), width=2)
    if occupied:
        body = random.choice([(45, 80, 190), (180, 50, 45), (220, 220, 220), (30, 35, 40), (200, 150, 40)])
        # stylized top-down car body and windows
        d.rounded_rectangle((35, 18, 93, 112), radius=15, fill=body, outline=(20, 25, 30), width=3)
        d.rounded_rectangle((42, 35, 86, 58), radius=7, fill=(65, 105, 125), outline=(25, 35, 40), width=2)
        d.rounded_rectangle((42, 68, 86, 86), radius=5, fill=(65, 105, 125), outline=(25, 35, 40), width=2)
        d.rectangle((31, 35, 37, 48), fill=(25, 25, 25))
        d.rectangle((91, 35, 97, 48), fill=(25, 25, 25))
        d.rectangle((31, 80, 37, 94), fill=(25, 25, 25))
        d.rectangle((91, 80, 97, 94), fill=(25, 25, 25))
    else:
        # empty bay: small concrete marks, but no vehicle
        for _ in range(10):
            x, y = random.randrange(15, 115), random.randrange(15, 118)
            d.point((x, y), fill=(random.randrange(70, 130),)*3)
    return im

for split, count in [("train", 240), ("validation", 60), ("test", 60)]:
    for label, occupied in [("vacant", False), ("occupied", True)]:
        folder = os.path.join(ROOT, split, label)
        os.makedirs(folder, exist_ok=True)
        for i in range(count):
            make_image(occupied).save(os.path.join(folder, f"{label}_{i:04d}.jpg"), quality=92)
print(f"Synthetic demo dataset created at: {ROOT}")
print("Note: use a real labeled parking dataset for meaningful real-world accuracy.")

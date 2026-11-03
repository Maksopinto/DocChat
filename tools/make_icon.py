"""Малює іконку DocChat (assets/icon.ico і assets/icon.png). Запуск: python tools/make_icon.py"""
from pathlib import Path

from PIL import Image, ImageDraw

S = 1024  # малюємо у великому розмірі, потім зменшуємо: так краї гладкі
BG1, BG2 = (31, 36, 48), (20, 22, 27)
ACCENT, ACCENT_DARK = (76, 141, 255), (47, 111, 237)
PAPER, LINE = (238, 241, 247), (160, 170, 190)


def build() -> Image.Image:
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))

    # фон: заокруглений квадрат із м'яким градієнтом
    grad = Image.new("RGBA", (S, S))
    gd = ImageDraw.Draw(grad)
    for y in range(S):
        t = y / (S - 1)
        gd.line([(0, y), (S, y)], fill=tuple(int(BG1[i] + (BG2[i] - BG1[i]) * t) for i in range(3)) + (255,))
    mask = Image.new("L", (S, S), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, S - 1, S - 1], radius=230, fill=255)
    img.paste(grad, (0, 0), mask)
    d = ImageDraw.Draw(img)

    # аркуш документа зі зігнутим кутом
    x0, y0, x1, y1, fold = 200, 150, 700, 800, 130
    d.polygon([(x0, y0), (x1 - fold, y0), (x1, y0 + fold), (x1, y1), (x0, y1)], fill=PAPER)
    d.polygon([(x1 - fold, y0), (x1 - fold, y0 + fold), (x1, y0 + fold)], fill=(196, 204, 220))
    for i, w in enumerate((400, 400, 400, 270)):
        y = y0 + 230 + i * 85
        d.rounded_rectangle([x0 + 60, y, x0 + 60 + w, y + 34], radius=17, fill=LINE)

    # бульбашка чату перед аркушем, праворуч унизу
    bx0, by0, bx1, by1 = 450, 520, 880, 840
    d.rounded_rectangle([bx0 - 22, by0 - 22, bx1 + 22, by1 + 22], radius=110, fill=BG2 + (255,))  # обвідка
    d.polygon([(560, by1 + 20), (560, 950), (700, by1 + 20)], fill=BG2 + (255,))
    d.rounded_rectangle([bx0, by0, bx1, by1], radius=90, fill=ACCENT)
    d.polygon([(585, by1 - 10), (585, 915), (680, by1 - 10)], fill=ACCENT)
    for i in range(3):
        cx = 565 + i * 100
        d.ellipse([cx - 28, 680 - 28, cx + 28, 680 + 28], fill=(255, 255, 255))
    return img


if __name__ == "__main__":
    out = Path(__file__).resolve().parent.parent / "assets"
    out.mkdir(exist_ok=True)
    big = build()
    big.resize((512, 512), Image.LANCZOS).save(out / "icon.png")
    big.save(out / "icon.ico", sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (24, 24), (16, 16)])
    print("Готово:", out)

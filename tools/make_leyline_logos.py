#!/usr/bin/env python3
"""Write the Leyline mark into every file that shows the logo (website, realm page, launchers).

Sources (assets/branding/):
  leyline-swirl-512.png    the swirl alone: it turns (the spinner and the launcher's emblem)
  leyline-crystal-512.png  the crystal alone: it stays upright on top of the swirl
  leyline-mark-512.png     the two together, for places that show a still logo
  leyline-app-icon-512.png the app icon (the mark on a dark rounded square): favicons

Run from anywhere: python3 tools/make_leyline_logos.py
"""
import pathlib
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = pathlib.Path(__file__).resolve().parent.parent
BR = ROOT / "assets/branding"
FONT = ROOT / "launcher/assets/launcher/fonts/Nunito.ttf"   # SIL OFL 1.1, already bundled
BG = (8, 10, 20, 255)
TEXT = (236, 240, 255, 255)
LANCZOS = Image.Resampling.LANCZOS


def nunito(size, weight="ExtraBold"):
    f = ImageFont.truetype(str(FONT), size)
    try:
        f.set_variation_by_name(weight)
    except (OSError, ValueError):
        pass
    return f


def save(im, rel, **kw):
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    if p.suffix == ".webp":
        im.save(p, "WEBP", quality=kw.get("quality", 90), method=6)
    elif p.suffix == ".jpg":
        im.convert("RGB").save(p, "JPEG", quality=88, optimize=True)
    elif p.suffix == ".ico":
        im.save(p, sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64)])
    else:
        im.save(p, "PNG", optimize=True)


def lockup(mark, w, h, mark_px, text_px, bg=None):
    """The mark above the word "Leyline", centred in a w x h box."""
    c = Image.new("RGBA", (w, h), bg or (0, 0, 0, 0))
    f = nunito(text_px)
    gap = round(text_px * 0.25)
    top = (h - (mark_px + gap + text_px)) // 2
    c.alpha_composite(mark.resize((mark_px, mark_px), LANCZOS), ((w - mark_px) // 2, top))
    ImageDraw.Draw(c).text((w / 2, top + mark_px + gap), "Leyline", font=f, fill=TEXT, anchor="mt")
    return c


def og_image(mark):
    W, H = 1200, 630
    f = nunito(150)
    tw = ImageDraw.Draw(Image.new("L", (1, 1))).textlength("Leyline", font=f)
    ms, gap = 400, 40
    x0 = int((W - (ms + gap + tw)) / 2)
    im = Image.new("RGBA", (W, H), BG)
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse([x0 - 40, H // 2 - 240, x0 + ms + 40, H // 2 + 240], fill=(70, 80, 200, 90))
    im.alpha_composite(glow.filter(ImageFilter.GaussianBlur(90)))
    im.alpha_composite(mark.resize((ms, ms), LANCZOS), (x0, (H - ms) // 2))
    ImageDraw.Draw(im).text((x0 + ms + gap, H // 2), "Leyline", font=f, fill=TEXT, anchor="lm")
    return im


def main():
    swirl = Image.open(BR / "leyline-swirl-512.png").convert("RGBA")
    crystal = Image.open(BR / "leyline-crystal-512.png").convert("RGBA")
    mark = Image.open(BR / "leyline-mark-512.png").convert("RGBA")
    app = Image.open(BR / "leyline-app-icon-512.png").convert("RGBA")
    n = 0
    # website: the spinner layers, the still mark, icons, the link preview
    for name, im in (("swirl", swirl), ("crystal", crystal)):
        for px in (512, 256, 128):
            save(im if px == 512 else im.resize((px, px), LANCZOS), f"www/assets/leyline/{name}-{px}.webp", quality=88)
            n += 1
    save(mark, "www/assets/leyline/mark-512.png")
    save(mark.resize((192, 192), LANCZOS), "www/assets/leyline/mark-192.png")
    save(app.resize((180, 180), LANCZOS), "www/assets/leyline/apple-touch-icon.png")
    save(app.resize((256, 256), LANCZOS), "www/favicon.ico")
    save(og_image(mark), "www/assets/og-image.jpg")
    n += 5
    # the realm's in-game page (corner logo on the login screen)
    for rel, px in (("realm/www/ow-corner-logo.webp", 158), ("realm/www/ow-corner-logo@2x.webp", 317)):
        save(lockup(mark, px, px, round(px * 0.72), round(px * 0.17)), rel)
        n += 1
    # the launcher: the emblem's two layers (the swirl turns, the crystal stays upright)
    save(swirl.resize((128, 128), LANCZOS), "launcher/assets/launcher/kit/emblem_swirl.png")
    save(crystal.resize((128, 128), LANCZOS), "launcher/assets/launcher/kit/emblem_crystal.png")
    # Leyline Server's window header (launcher_gui.py shows it at 185 x 105)
    save(lockup(mark, 370, 210, 140, 46), "assets/leyline_logo_header.png")
    n += 3
    print("wrote", n, "files")


if __name__ == "__main__":
    main()

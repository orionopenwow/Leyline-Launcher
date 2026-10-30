#!/usr/bin/env python3
"""Write the flat Leyline backdrops over the old painted art (the silver-haired elf and his portal).

Every file keeps its name, size and format, so nothing that loads it changes:
  login-backdrop.webp / .mp4 / .webm   the game's login screen and the loading screen before it
                                       (www/, www/ow/, realm/www/, realm/login-backdrop/, docs/queue/a/)
  realm/www/ow-signin.webp/.mp4/.webm  the realm page's "Signing in" cover
  launcher/assets/launcher/bg_static.jpg and bg/f*.jpg
                                       the launcher's background (the frames are the animation)

The look: a dark background, a faint glow, and the mark. In the videos and the launcher's frames the
swirl turns once every 7 seconds (as the site's .ly-spin) and the crystal stays upright; the still
images (posters, reduced motion, Data Saver) show the mark at rest.

Sources: assets/branding/leyline-swirl-512.png and leyline-crystal-512.png.
Needs Pillow and ffmpeg (libx264, libvpx-vp9). Run from anywhere: python3 tools/make_leyline_backdrops.py
"""
import pathlib
import shutil
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = pathlib.Path(__file__).resolve().parent.parent
BR = ROOT / "assets/branding"
FONT = ROOT / "launcher/assets/launcher/fonts/Nunito.ttf"   # SIL OFL 1.1, already bundled
BG = (8, 10, 20)
GLOW = (70, 80, 200)
TEXT = (232, 236, 255)
TURN_S = 7.0          # one turn of the swirl, as .ly-spin in www/assets/leyline/leyline.css
LANCZOS = Image.Resampling.LANCZOS
BICUBIC = Image.Resampling.BICUBIC

BACKDROPS = ("www", "www/ow", "realm/www", "realm/login-backdrop")


class Mark:
    """The two layers at one size: frame(t) turns the swirl, the crystal never moves."""

    def __init__(self, px):
        self.px = px
        self.swirl = Image.open(BR / "leyline-swirl-512.png").convert("RGBA").resize((px, px), LANCZOS)
        self.crystal = Image.open(BR / "leyline-crystal-512.png").convert("RGBA").resize((px, px), LANCZOS)

    def frame(self, angle=0.0):
        im = self.swirl.rotate(-angle, resample=BICUBIC) if angle else self.swirl.copy()   # clockwise, as CSS
        im.alpha_composite(self.crystal)
        return im


def nunito(size, weight="ExtraBold"):
    f = ImageFont.truetype(str(FONT), size)
    try:
        f.set_variation_by_name(weight)
    except (OSError, ValueError):
        pass
    return f


def canvas(w, h, cx, cy, r):
    """The flat background with a soft glow centred where the mark sits."""
    im = Image.new("RGBA", (w, h), BG + (255,))
    glow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse([cx - r, cy - r, cx + r, cy + r], fill=GLOW + (70,))
    im.alpha_composite(glow.filter(ImageFilter.GaussianBlur(r * 0.45)))
    return im


class Scene:
    """A background plus where the mark goes (centre and size), and an optional line of text under it."""

    def __init__(self, w, h, cx, cy, size, text=None, text_px=0):
        self.w, self.h, self.size = w, h, size
        self.x, self.y = round(cx - size / 2), round(cy - size / 2)
        self.bg = canvas(w, h, cx, cy, round(size * 0.75))
        if text:
            ImageDraw.Draw(self.bg).text((cx, self.y + size + round(text_px * 0.6)), text, font=nunito(text_px),
                                         fill=TEXT + (255,), anchor="mt")
        self.mark = Mark(size)

    def at(self, angle=0.0):
        im = self.bg.copy()
        im.alpha_composite(self.mark.frame(angle), (self.x, self.y))
        return im.convert("RGB")


def video(scene, fps, rel_mp4, rel_webm):
    """One full turn, so the loop is seamless: H.264 (High, yuv420p) and VP9, as the files they replace."""
    n = round(TURN_S * fps)
    raw = b"".join(scene.at(360.0 * i / n).tobytes() for i in range(n))
    common = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{scene.w}x{scene.h}",
              "-r", str(fps), "-i", "-", "-an", "-pix_fmt", "yuv420p"]
    subprocess.run(common + ["-c:v", "libx264", "-profile:v", "high", "-preset", "veryslow", "-crf", "24",
                             "-movflags", "+faststart", str(ROOT / rel_mp4)], input=raw, check=True)
    subprocess.run(common + ["-c:v", "libvpx-vp9", "-b:v", "0", "-crf", "38", "-row-mt", "1", "-deadline", "good",
                             "-cpu-used", "2", str(ROOT / rel_webm)], input=raw, check=True)


def login_backdrop():
    """960 x 540 poster, 1280 x 720 loops. The mark sits in the upper half, clear of the login form."""
    still = Scene(960, 540, 480, 170, 190)
    loop = Scene(1280, 720, 640, 227, 253)
    first = ROOT / BACKDROPS[0]
    still.at().save(first / "login-backdrop.webp", "WEBP", quality=88, method=6)
    video(loop, 25, f"{BACKDROPS[0]}/login-backdrop.mp4", f"{BACKDROPS[0]}/login-backdrop.webm")
    for d in BACKDROPS[1:]:
        for ext in ("webp", "mp4", "webm"):
            shutil.copyfile(first / f"login-backdrop.{ext}", ROOT / d / f"login-backdrop.{ext}")
    shutil.copyfile(first / "login-backdrop.webp", ROOT / "docs/queue/a/login-backdrop.webp")


def signin_cover():
    """realm/www/ow-signin.*: 864 x 426, the mark and "Signing in" in the middle (the page also crops it)."""
    s = Scene(864, 426, 432, 186, 200, text="Signing in", text_px=30)
    s.at().save(ROOT / "realm/www/ow-signin.webp", "WEBP", quality=88, method=6)
    video(s, 24, "realm/www/ow-signin.mp4", "realm/www/ow-signin.webm")


def launcher_background():
    """1108 x 680, the mark right of centre (the home page's cards sit on the left). bg/ holds one turn at
    the launcher's 80 ms frame step; bg_static.jpg is the still (animation off, or no frames)."""
    s = Scene(1108, 680, 700, 300, 300)
    s.at().save(ROOT / "launcher/assets/launcher/bg_static.jpg", "JPEG", quality=90, optimize=True)
    d = ROOT / "launcher/assets/launcher/bg"
    for old in d.glob("f*.jpg"):
        old.unlink()
    n = round(TURN_S / 0.08)
    for i in range(n):
        s.at(360.0 * i / n).save(d / f"f{i:03d}.jpg", "JPEG", quality=88, optimize=True)


def main():
    if not shutil.which("ffmpeg"):
        sys.exit("needs ffmpeg")
    login_backdrop()
    signin_cover()
    launcher_background()
    print("wrote the login backdrop, the sign-in cover and the launcher background")


if __name__ == "__main__":
    main()

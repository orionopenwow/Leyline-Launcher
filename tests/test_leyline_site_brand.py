"""The Leyline look on the website and in the launcher: the old Open Vanilla and Orion art is gone (the
login backdrop, the sign-in cover and the launcher background included) and
nothing points at it any more, and the spinning mark (the swirl turns, the crystal stays upright) is
the logo and the loading indicator wherever the site shows one."""
import os
import re
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WWW = os.path.join(ROOT, "www")

# art that was removed with the move to the flat Leyline look (October 2026)
REMOVED = [
    "www/assets/orion/",
    "www/assets/loading/",
    "www/assets/openvanilla_logo.png",
    "www/assets/openvanilla_logo_hero.png",
    "www/assets/openvanilla_logo_hero.webp",
    "www/assets/openvanilla_logo_hero_shine.webp",
    "www/assets/openvanilla_logo_nav.png",
    "www/assets/openvanilla_logo_nav.webp",
    "assets/openvanilla_logo_hero.png",
    "assets/openvanilla_logo_proportional.png",
    "assets/branding/openvanilla_badge.png",
    "launcher/assets/launcher/logo.png",
    "launcher/assets/launcher/logo_hero.png",
    "launcher/assets/launcher/logo_openvanilla.png",
    "docs/img/orion.gif",
]
# what a reference to them looks like in a page, stylesheet, script, tool or doc
REMOVED_REFS = re.compile(
    r"assets/orion/|assets/loading/|openvanilla_logo|orion_cookie|orion\.gif|openvanilla_badge"
    r"|logo_hero\.png|logo_openvanilla\.png|launcher/logo\.png")
SCANNED = (".html", ".css", ".js", ".mjs", ".py", ".json", ".md")


def tracked_files():
    out = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    return [f for f in out.splitlines() if f.endswith(SCANNED) and os.path.isfile(os.path.join(ROOT, f))]


def read(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8", errors="replace") as f:
        return f.read()


SPIN = re.compile(r'<span class="ly-spin[^"]*"[^>]*>\s*<img class="ly-swirl" src="([^"]+)"[^>]*>\s*'
                  r'<img class="ly-crystal" src="([^"]+)"[^>]*>\s*</span>')


class RemovedArtTests(unittest.TestCase):
    def test_the_old_art_is_gone(self):
        for rel in REMOVED:
            self.assertFalse(os.path.exists(os.path.join(ROOT, rel)), rel)

    def test_nothing_references_the_old_art(self):
        me = os.path.relpath(__file__, ROOT)
        hits = []
        for rel in tracked_files():
            if rel == me or rel.startswith(("www/wenilla.js", "www/bridge.js", "www/platform.js")):
                continue
            for n, line in enumerate(read(rel).splitlines(), 1):
                if REMOVED_REFS.search(line):
                    hits.append(f"{rel}:{n}: {line.strip()[:120]}")
        self.assertEqual(hits, [], "references to removed art:\n" + "\n".join(hits))


class SpinnerTests(unittest.TestCase):
    def test_the_spinner_css(self):
        css = read("www/assets/leyline/leyline.css")
        self.assertIn("@keyframes ly-swirl", css)
        m = re.search(r"\.ly-spin > \.ly-swirl \{ animation: ly-swirl ([\d.]+)s linear infinite", css)
        self.assertTrue(m, "the swirl turns continuously")
        self.assertTrue(6 <= float(m.group(1)) <= 8, "one turn every 6 to 8 seconds")
        self.assertRegex(css, r"prefers-reduced-motion: reduce\)\s*\{\s*\.ly-spin > \.ly-swirl \{ animation: none; \}")
        self.assertNotRegex(css, r"\.ly-crystal\s*\{[^}]*animation", "the crystal never turns")

    def test_home_page_sends_visitors_to_the_leyline_front_page(self):
        """openvanilla.app's home is the Leyline front page on play.openvanilla.app (owner 2026-10-30)."""
        for page in ("index.html", "portal.html"):
            html = read(f"www/{page}")
            with self.subTest(page=page):
                self.assertIn('<meta http-equiv="refresh" content="0; url=https://play.openvanilla.app/wrath/leyline">', html)
                self.assertIn('<link rel="canonical" href="https://play.openvanilla.app/wrath/leyline">', html)
                self.assertIn('location.replace("https://play.openvanilla.app/wrath/leyline"', html)
                self.assertIn('<a href="https://play.openvanilla.app/wrath/leyline">Open Leyline</a>', html)
                self.assertNotRegex(html, r"(?i)herald|world of warcraft|blizzard")

    def test_realm_site_home_page_still_uses_the_spinner(self):
        """The 1.12 realm site's own home page (labs/openvanilla-realm/site, shipped in Leyline Server)."""
        for page in ("index.html", "portal.html"):
            html = read(f"labs/openvanilla-realm/site/{page}")
            with self.subTest(page=page):
                self.assertIn('href="assets/leyline/site-flat.css"', html)
                self.assertGreaterEqual(len(SPIN.findall(html)), 7, "header, hero, trailer, three sign-in boxes, footer")

    def test_loading_screens_use_the_spinner(self):
        boot = read("www/boot.js")
        self.assertIn('<span class="ly-spin" role="img" aria-label="Leyline is loading">', boot)
        self.assertIn("root.className = 'ly-flat';", boot)
        site = "labs/openvanilla-realm/site/"   # the realm site's pages (www/ has "moved" pages in their place)
        for rel, pre in ((site + "armory/character.html", "../"), (site + "guild.html", ""), (site + "realms.html", ""),
                         (site + "duels.html", ""), ("www/project.html", "")):
            html = read(rel)
            with self.subTest(page=rel):
                self.assertIn(f'href="{pre}assets/leyline/leyline.css"', html)
                self.assertRegex(html, r'class="[^"]*ly-loading">\s*<span class="ly-spin ly-fast"')

    def test_manual_header_uses_the_spinner(self):
        for f in sorted(os.listdir(os.path.join(WWW, "manual"))):
            if f.endswith(".html"):
                html = read(f"www/manual/{f}")
                with self.subTest(page=f):
                    self.assertRegex(html, SPIN)
                    self.assertNotIn("Open Vanilla Manual", html)

    def test_favicon_and_link_preview_exist(self):
        for rel in ("www/favicon.ico", "www/assets/og-image.jpg", "www/assets/leyline/apple-touch-icon.png",
                    "www/assets/leyline/mark-512.png"):
            self.assertTrue(os.path.isfile(os.path.join(ROOT, rel)), rel)


class LauncherEmblemTests(unittest.TestCase):
    def test_swirl_turns_and_crystal_stays_upright(self):
        sys.path.insert(0, os.path.join(ROOT, "launcher"))
        import launcher_art as art
        kit = os.path.join(ROOT, "launcher", "assets", "launcher", "kit")
        if kit not in art.KIT_DIRS:
            art.KIT_DIRS.insert(0, kit)
        frames = art.emblem_frames(64, 48)
        self.assertEqual(len(frames), 48)
        a, b = frames[0], frames[12]
        self.assertNotEqual(a.tobytes(), b.tobytes(), "the swirl moves")
        crystal = art.kit("emblem_crystal").resize((64, 64))
        box = crystal.getbbox()
        # where the crystal is opaque, every frame shows it the same way up
        for x in range(box[0], box[2]):
            for y in range(box[1], box[3]):
                if crystal.getpixel((x, y))[3] == 255:
                    self.assertEqual(a.getpixel((x, y)), b.getpixel((x, y)))

    def test_launcher_no_longer_loads_the_old_logo(self):
        src = read("launcher/openvanilla_launcher.py")
        self.assertNotIn("logo_hero", src)
        self.assertIn('art.flat_wordmark("Leyline"', src)
        self.assertIn('load_img("leyline_logo_header.png"', read("launcher_gui.py"))


# The painted Orion art (the silver-haired elf at his portal) that the flat backdrops replaced in place
# (tools/make_leyline_backdrops.py), and the screenshots and mockups that showed it: sha256 of each.
OLD_ORION_ART = {
    "982def2b390f1ef6dcf548853d8b94deecf4270227a4ad8b6138e8847c9c1b37",  # login-backdrop.webp
    "3f259f92fd0f35c0d28106c061869df7d04cc95c918c3f2b5084e0bce9359b15",  # login-backdrop.mp4
    "bd3cd038167a5e3557e8fb242e8ea024669e36668459b22b18db1355e7d8793f",  # login-backdrop.webm
    "1dde3113730d34ec866d296c81b5e265ec41031de441830fe3ac2de26ab154e1",  # labs/openvanilla-realm/realm/login-backdrop/login-backdrop.webp
    "6b89ca3b4f2077240515e8b9c6b38bf27bfe6666a52e355263a153916731a8da",  # labs/openvanilla-realm/realm/login-backdrop/login-backdrop.mp4
    "6d032637f8f05f0596eea553e762078eb5120c87b173bf033c9c7de68b2720fb",  # labs/openvanilla-realm/realm/www/login-backdrop.webp
    "dec60a08e15cd0b47b041e83b9c5a255f170708a94e211e9e2d75ca4a987490d",  # labs/openvanilla-realm/realm/www/ow-signin.webp
    "5fae28b2f8c32fb1d47c7dba7048dd472ab7d5269a9678375fad73bee4912c61",  # labs/openvanilla-realm/realm/www/ow-signin.mp4
    "e9725552d2b33c56fba4ce0f7bfb6de78c6db8940168b87fd60fe37af1b625c3",  # labs/openvanilla-realm/realm/www/ow-signin.webm
    "860429302c9d327393f07792a41a2c9178be55a199dc2e61e03972b251ca91ef",  # launcher bg_static.jpg
    "e525e3bfcdac193ec84696f855faa11e2eec560c59eac4bae65d34ebaf4219fb",  # launcher bg/f000.jpg
    "9ecef5153308cf99a967cfc2ea71914c51860d42381b98e8077946fde3b5815d",  # launcher bg/f062.jpg
    "2d7487b68cbdd6ad104643adf12c83e572edc79bae57a932e1ed3b3ce5cc8fa9",  # www/assets/launcher_home.jpg
    "260786a2685f206676acbfc308926557067ccf7e1c0db46fed8412212e538b40",  # www/assets/launcher_home.webp
    "fd6a1d6a66def36ccf45ee44222484fb31e7cb7b293085ee04a53557774c44eb",  # www/assets/launcher_workshop.webp
    "8b387cd299f5b17499915d489ead153a0e9c8025ca1f062e6a047abf9d989637",  # www/assets/workshop/ui_repack.webp
    "513b073a811f6bbb11271d5c96e0842a7fede57004d1be81fb8e7acb18fa6e63",  # docs/img/launcher.jpg
    "779b04708fcc6963ee5b0eec998253018dde90f874fdd7a2a17b5292047afce3",  # labs/herald/discord_assets/04_launcher.png
    "bfdcde023eeb403894c90517d8497db24bb96c671f52d619f1e6e50ec276cc0a",  # www/assets/animated_cosmic_bg.jpg
}
MEDIA = (".png", ".jpg", ".jpeg", ".webp", ".gif", ".mp4", ".webm", ".avif")
FLAT_BG = (8, 10, 20)
BACKDROP_DIRS = ("www", "www/ow", "labs/openvanilla-realm/realm/www", "labs/openvanilla-realm/realm/login-backdrop")


def tracked_media():
    out = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    return [f for f in out.splitlines() if f.lower().endswith(MEDIA) and os.path.isfile(os.path.join(ROOT, f))]


def size_of(path):
    from PIL import Image
    with Image.open(path) as im:
        return im.size


def flat_corners(path, tol=10):
    """True when the four corners of the picture are the flat Leyline background."""
    from PIL import Image, ImageStat
    with Image.open(path) as src:
        im = src.convert("RGB")
    w, h = im.size
    k = max(8, min(w, h) // 12)
    for box in ((0, 0, k, k), (w - k, 0, w, k), (0, h - k, k, h), (w - k, h - k, w, h)):
        mean = ImageStat.Stat(im.crop(box)).mean
        if any(abs(m - c) > tol for m, c in zip(mean, FLAT_BG)):
            return False
    return True


class NoOrionArtTests(unittest.TestCase):
    """The owner: "everything, no old Orion art". The login backdrop, the realm's sign-in cover, the
    launcher's background and every screenshot that showed them are the flat Leyline look now."""

    def test_no_file_is_the_old_orion_art(self):
        import hashlib
        hits = []
        for rel in tracked_media():
            with open(os.path.join(ROOT, rel), "rb") as f:
                if hashlib.sha256(f.read()).hexdigest() in OLD_ORION_ART:
                    hits.append(rel)
        self.assertEqual(hits, [], "the old Orion art is back")
        self.assertFalse(os.path.exists(os.path.join(WWW, "assets", "animated_cosmic_bg.jpg")))

    def test_backdrops_keep_their_names_and_sizes_and_are_flat(self):
        stills = [f"{d}/login-backdrop.webp" for d in BACKDROP_DIRS]
        for rel in stills:
            with self.subTest(still=rel):
                self.assertEqual(size_of(os.path.join(ROOT, rel)), (960, 540))
                self.assertTrue(flat_corners(os.path.join(ROOT, rel)))
        sign = os.path.join(ROOT, "labs/openvanilla-realm/realm/www/ow-signin.webp")
        self.assertEqual(size_of(sign), (864, 426))
        self.assertTrue(flat_corners(sign))
        for d in BACKDROP_DIRS:
            for ext in ("mp4", "webm"):
                self.assertTrue(os.path.isfile(os.path.join(ROOT, d, f"login-backdrop.{ext}")), f"{d} {ext}")

    def test_backdrop_videos_are_the_flat_loop(self):
        import shutil
        if not shutil.which("ffmpeg"):
            self.skipTest("needs ffmpeg")
        from PIL import Image
        import io
        for rel, size in [(f"{d}/login-backdrop.{e}", (1280, 720)) for d in BACKDROP_DIRS for e in ("mp4", "webm")] + \
                         [(f"labs/openvanilla-realm/realm/www/ow-signin.{e}", (864, 426)) for e in ("mp4", "webm")]:
            with self.subTest(video=rel):
                png = subprocess.run(["ffmpeg", "-v", "error", "-ss", "1", "-i", os.path.join(ROOT, rel), "-frames:v", "1",
                                      "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True, check=True).stdout
                frame = Image.open(io.BytesIO(png))
                self.assertEqual(frame.size, size)
                path = os.path.join(ROOT, "tests", ".frame.png")
                frame.save(path)
                try:
                    self.assertTrue(flat_corners(path))
                finally:
                    os.remove(path)

    def test_launcher_background_is_flat(self):
        bg = os.path.join(ROOT, "launcher", "assets", "launcher")
        frames = sorted(f for f in os.listdir(os.path.join(bg, "bg")) if f.endswith(".jpg"))
        self.assertGreaterEqual(len(frames), 2, "the frames are the swirl turning")
        for f in ["bg_static.jpg"] + [f"bg/{n}" for n in frames]:
            with self.subTest(frame=f):
                self.assertEqual(size_of(os.path.join(bg, f)), (1108, 680))
                self.assertTrue(flat_corners(os.path.join(bg, f)))

    def test_the_game_page_backdrop_is_the_css_spinner(self):
        js = read("www/login-backdrop.js")
        self.assertIn("spin = null", js)
        self.assertRegex(js, r"#ow-login-backdrop \.ly-swirl \{ animation: ow-ly-swirl 7s linear infinite")
        self.assertRegex(js, r"prefers-reduced-motion: reduce\) \{ #ow-login-backdrop \.ly-swirl \{ animation: none; \}")
        self.assertNotRegex(js, r"\.ly-crystal \{[^}]*animation", "the crystal never turns")
        self.assertEqual(js, read("www/ow/login-backdrop.js"))
        html = read("labs/openvanilla-realm/site/game.html")   # the realm site's play page
        m = re.search(r"spin: \{ swirl: '([^']+)', crystal: '([^']+)' \}", html)
        self.assertTrue(m, "game.html hands login-backdrop.js the two layers")
        for rel in m.groups():
            self.assertTrue(os.path.isfile(os.path.join(WWW, rel)), rel)


if __name__ == "__main__":
    unittest.main()

"""The Leyline look on the website and in the launcher: the old Open Vanilla and Orion art is gone and
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

    def test_home_page_header_hero_and_loading_use_the_spinner(self):
        for page in ("index.html", "portal.html"):
            html = read(f"www/{page}")
            with self.subTest(page=page):
                self.assertIn('href="assets/leyline/leyline.css"', html)
                self.assertIn('href="assets/leyline/site-flat.css"', html)
                header = html[html.index('<header class="ovh3">'):html.index("</header>")]
                self.assertRegex(header, SPIN, "the header logo is the spinner")
                self.assertIn('<span class="ly-word">Leyline</span>', header)
                hero = html[html.index('<div class="hero-logo-container">'):]
                self.assertRegex(hero[:600], SPIN, "the hero logo is the spinner")
                self.assertGreaterEqual(len(SPIN.findall(html)), 7, "header, hero, trailer, three sign-in boxes, footer")
                for swirl, crystal in SPIN.findall(html):
                    self.assertTrue(os.path.isfile(os.path.join(WWW, swirl)), swirl)
                    self.assertTrue(os.path.isfile(os.path.join(WWW, crystal)), crystal)
                self.assertNotIn("nav_v2/", header, "the header's painted label buttons are text now")

    def test_loading_screens_use_the_spinner(self):
        boot = read("www/boot.js")
        self.assertIn('<span class="ly-spin" role="img" aria-label="Leyline is loading">', boot)
        self.assertIn("root.className = 'ly-flat';", boot)
        for rel, pre in (("www/armory/character.html", "../"), ("www/guild.html", ""), ("www/realms.html", ""),
                         ("www/duels.html", ""), ("www/project.html", "")):
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


if __name__ == "__main__":
    unittest.main()

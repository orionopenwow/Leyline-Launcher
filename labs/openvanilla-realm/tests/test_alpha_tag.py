"""The in-game alpha tag (WenillaCore/Alpha.lua) shows the same version as the 1.12 realm site's pill
(labs/openvanilla-realm/site/index.html and portal.html)."""
import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class AlphaTagTests(unittest.TestCase):
    def test_game_and_site_agree(self):
        lua = open(os.path.join(ROOT, "Data", "Interface", "AddOns", "WenillaCore", "Alpha.lua"), encoding="utf-8").read()
        game = re.search(r'W\.ALPHA = "([0-9.]+)"', lua).group(1)
        for page in ("index.html", "portal.html"):
            html = open(os.path.join(ROOT, "labs", "openvanilla-realm", "site", page), encoding="utf-8").read()
            site = re.search(r'hero-build-tag.*?<span class="ver">v([0-9.]+)</span>', html, re.S).group(1)
            self.assertEqual(game, site, f"Alpha.lua says {game}, labs/openvanilla-realm/site/{page} says {site}: bump them together")


if __name__ == "__main__":
    unittest.main()

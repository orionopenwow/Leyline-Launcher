"""launcher/leyline_bridge.py: the 1.57.0 start card "Open Vanilla is now Leyline" with one button to the Leyline
launcher download. No Tk: a fake app stands in for the launcher.

    python -m unittest tests.test_leyline_bridge -v
"""
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "launcher"))
sys.path.append(os.path.join(ROOT, "packaging"))

import leyline_bridge as LB  # noqa: E402
import live_content as LC  # noqa: E402

BANNED = re.compile(r"world of warcraft|\bwow\b|warcraft|lich king|blizzard", re.I)


class Live:
    def __init__(self, flags):
        self.flags = flags

    def flag(self, name):
        return self.flags.get(name, False)


class Dialog:
    def __init__(self, title, text):
        self.title, self.text, self.specs, self.closed = title, text, [], False

    def buttons(self, *specs):
        self.specs = list(specs)

    def close(self):
        self.closed = True

    def press(self, label):
        dict((s[0], s[1]) for s in self.specs)[label]()


class App:
    def __init__(self, flags=None, settings=None):
        self.settings = {} if settings is None else settings
        self.live = Live(dict(LC.DEFAULT_FLAGS) if flags is None else flags)
        self.scheduled, self.saved, self.dialogs = [], 0, []
        self._p2p_dialog = None

    def after(self, ms, fn):
        self.scheduled.append((ms, fn))

    def save_settings(self):
        self.saved += 1

    def p2p_dialog(self, title, text, width=520):
        d = Dialog(title, text)
        self.dialogs.append(d)
        return d


class BridgeTests(unittest.TestCase):
    def test_flag_is_known_and_on_by_default(self):
        self.assertTrue(LC.DEFAULT_FLAGS["leyline_bridge"])
        self.assertEqual(LC.sanitize({"schema": 1, "serial": 1, "flags": {"leyline_bridge": False}})["flags"],
                         {"leyline_bridge": False}, "live.json may turn it off")

    def test_shows_on_start_until_handled(self):
        app = App()
        LB.on_start(app)
        self.assertEqual(len(app.scheduled), 1)
        self.assertLess(app.scheduled[0][0], 2500, "before the AI card, so the two never fight")
        app.scheduled[0][1]()
        d = app.dialogs[0]
        self.assertEqual([s[0] for s in d.specs], [LB.BUTTON, "Not now", "Don't show again"])
        self.assertTrue(d.specs[0][2], "the download is the primary button")

    def test_button_opens_the_leyline_download_once(self):
        app, opened = App(), []
        d = LB.show(app, opener=opened.append)
        d.press(LB.BUTTON)
        self.assertEqual(opened, ["https://github.com/orionopenwow/Leyline/releases/latest"])
        self.assertTrue(d.closed)
        self.assertEqual(app.saved, 1)
        again = App(settings=app.settings)
        LB.on_start(again)
        self.assertEqual(again.scheduled, [], "not shown again after the player took the download")

    def test_not_now_waits_a_week_and_dont_show_again_is_final(self):
        s = {}
        LB.snooze(s, now=1000.0)
        self.assertFalse(LB.should_show(s, True, now=1000.0 + 86400))
        self.assertTrue(LB.should_show(s, True, now=1000.0 + LB.SNOOZE_DAYS * 86400 + 1))
        LB.never_again(s)
        self.assertFalse(LB.should_show(s, True, now=10 ** 12))
        app = App()
        d = LB.show(app, opener=lambda u: self.fail("no download on Not now"))
        d.press("Not now")
        self.assertIn("snooze_until", app.settings["leyline_bridge"])

    def test_hidden_by_live_flag_or_another_card(self):
        app = App(flags={"leyline_bridge": False})
        LB.on_start(app)
        self.assertEqual(app.scheduled, [])
        busy = App()
        busy._p2p_dialog = object()
        self.assertIsNone(LB.show(busy))
        self.assertEqual(busy.settings.get("leyline_bridge", {}).get("done"), None, "asks again next start")

    def test_text_is_plain_and_removes_nothing(self):
        text = " ".join((LB.TITLE, LB.TEXT, LB.BUTTON))
        self.assertIsNone(BANNED.search(text))
        self.assertIn("keep working", LB.TEXT)
        self.assertLess(len(LB.TEXT), 260)
        src = open(os.path.join(ROOT, "launcher", "leyline_bridge.py"), encoding="utf-8").read()
        for word in ("os.remove", "shutil", "rmtree", "unlink"):
            self.assertNotIn(word, src)

    def test_launcher_wires_it_and_the_build_freezes_it(self):
        src = open(os.path.join(ROOT, "launcher", "openvanilla_launcher.py"), encoding="utf-8").read()
        self.assertIn("import leyline_bridge", src)
        self.assertIn("leyline_bridge.on_start(self)", src)
        self.assertLess(src.index("leyline_bridge.on_start(self)"), src.index("ai_setup.on_start(self"))
        import build_repack as B
        self.assertIn("leyline_bridge", B.HIDDEN_IMPORTS)
        self.assertIn('"leyline_bridge")', src[src.index("SELF_TEST_MODULES"):][:400])


if __name__ == "__main__":
    unittest.main()

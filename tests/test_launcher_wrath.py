"""The launcher on WrathUnleashed (3.3.5a, play.openvanilla.app): the realm from defaults and live content,
live status from /wrath/status.json, PLAY > Browser opening /wrath, and the player's own 3.3.5a folder
(folder check, realmlist in Data/<locale>/realmlist.wtf, Config.wtf). The GUI part skips without Tk or a
display (run it under xvfb-run).

    xvfb-run -a python3.12 -m unittest tests.test_launcher_wrath -v
"""
import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "launcher"))

import live_content  # noqa: E402

try:
    import tkinter as tk
    _root = tk.Tk()
    _root.destroy()
    import PIL.ImageTk  # noqa: F401
    HAVE_TK = True
except Exception:
    HAVE_TK = False

def read_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


WRATH = {"name": "WrathUnleashed", "host": "play.openvanilla.app", "port": 3724, "portal": "https://play.openvanilla.app/",
         "play_url": "https://play.openvanilla.app/wrath", "status_url": "https://play.openvanilla.app/wrath/status.json",
         "build": 12340}


class LiveRealmTests(unittest.TestCase):
    def test_play_and_status_urls_survive_https_only(self):
        r = live_content.sanitize({"schema": 1, "realms": [WRATH]})["realms"][0]
        self.assertEqual(r["play_url"], WRATH["play_url"])
        self.assertEqual(r["status_url"], WRATH["status_url"])
        bad = dict(WRATH, play_url="http://play.openvanilla.app/wrath", status_url="file:///c:/x.json")
        r = live_content.sanitize({"schema": 1, "realms": [bad]})["realms"][0]
        self.assertNotIn("play_url", r)
        self.assertNotIn("status_url", r)

    def test_shipped_files_list_wrath_only(self):
        defaults = read_json(os.path.join(ROOT, "launcher", "defaults.json"))
        self.assertEqual([(r["name"], r["build"]) for r in defaults["realms"]], [("WrathUnleashed", 12340)])
        self.assertEqual([c["id"] for c in defaults["clients"]], ["wotlk"])
        self.assertIn("vanilla", [c["id"] for c in defaults["clients_parked"]])
        self.assertFalse(any("download_url" in c for c in defaults["clients"]))    # players bring their own 3.3.5a
        # no game client is ever downloaded: stock (exe) clients have no download link, parked ones included
        self.assertFalse(any("download_url" in c for c in defaults["clients_parked"] if c.get("type") == "exe"))

    def test_no_client_download_anywhere_in_the_launcher(self):
        """The launcher never downloads or links a game client (no download-site flow, no client-link overrides).
        The site names are split so the history scrub (tools/history-scrub) leaves this file as it is."""
        import re
        for name in os.listdir(os.path.join(ROOT, "launcher")):
            if name.endswith((".py", ".json", ".txt")):
                with open(os.path.join(ROOT, "launcher", name), encoding="utf-8") as f:
                    text = f.read()
                self.assertIsNone(re.search("arch" + r"ive\.org|nostalrius|Internet " + "Archive|CLIENT_(112|335)_URL|install_classic",
                                            text, re.I), name)
        import home_logic
        self.assertEqual(home_logic.client_button("exe", False, True)[2], "install")   # choose a folder, never a download
        src = read_json(os.path.join(ROOT, "www", "downloads", "live.src.json"))
        hosts = [r["host"] for r in src["realms"]]
        self.assertEqual(hosts, ["play.openvanilla.app"])
        self.assertNotIn("duels.openvanilla.app", json.dumps(src))


@unittest.skipUnless(HAVE_TK, "needs tkinter, Pillow and a display (xvfb-run)")
class WrathLauncherTests(unittest.TestCase):
    def setUp(self):
        import openvanilla_launcher as L
        import layout
        self.L = L
        self.tmp = tempfile.mkdtemp(prefix="owwrath-")
        self.addCleanup(lambda: shutil.rmtree(self.tmp, ignore_errors=True))
        saved = dict(LAYOUT=L.LAYOUT, SETTINGS_PATH=L.SETTINGS_PATH, LIVE_CACHE=L.LIVE_CACHE, ADDONS_DIR=L.ADDONS_DIR,
                     http_json=L.http_json, tcp_ping=L.tcp_ping, exe_command=L.exe_command)
        saved_cls = {k: getattr(L.Launcher, k) for k in ("refresh_realms", "check_for_update", "load_directory")}
        saved_mod = dict(askdirectory=L.filedialog.askdirectory, askretrycancel=L.messagebox.askretrycancel,
                         Popen=L.subprocess.Popen, launch_web=L.launch_web, showerror=L.messagebox.showerror)

        def restore():
            for k, v in saved.items():
                setattr(L, k, v)
            for k, v in saved_cls.items():
                setattr(L.Launcher, k, v)
            L.filedialog.askdirectory = saved_mod["askdirectory"]
            L.messagebox.askretrycancel = saved_mod["askretrycancel"]
            L.subprocess.Popen = saved_mod["Popen"]
            L.launch_web = saved_mod["launch_web"]
            L.messagebox.showerror = saved_mod["showerror"]
            if self.app is not None:
                try:
                    self.app.destroy()
                except Exception:
                    pass
        self.addCleanup(restore)
        L.LAYOUT = layout.Layout(self.tmp, self.tmp, "portable").ensure()
        L.SETTINGS_PATH = L.LAYOUT.settings_file
        L.LIVE_CACHE = L.LAYOUT.live_cache
        L.ADDONS_DIR = L.LAYOUT.addons_enabled
        for k in saved_cls:
            setattr(L.Launcher, k, lambda s: None)
        self.errors = []
        L.messagebox.showerror = lambda *a, **k: self.errors.append(a)
        L.exe_command = lambda exe: [exe]   # Wow.exe without Wine on this OS
        self.app = None

    def start(self, settings=None):
        if settings:
            with open(self.L.SETTINGS_PATH, "w", encoding="utf-8") as f:
                json.dump(settings, f)
        self.app = self.L.Launcher()
        self.app.show_page("play", animate=False)
        return self.app

    def wow335(self, locale="enGB", exe="Wow.exe"):
        root = os.path.join(self.tmp, "WoW 3.3.5a")
        os.makedirs(os.path.join(root, "Data", locale), exist_ok=True)
        for p in (os.path.join(root, exe), os.path.join(root, "Data", "common.MPQ"),
                  os.path.join(root, "Data", locale, "realmlist.wtf")):
            with open(p, "w") as f:
                f.write("set realmlist logon.example.org\n")
        os.makedirs(os.path.join(root, "WTF"), exist_ok=True)
        with open(os.path.join(root, "WTF", "Config.wtf"), "w") as f:
            f.write('SET realmList "logon.example.org"\nSET gxResolution "1920x1080"\n')
        return root

    def test_wrath_is_the_main_realm_and_browser_play_opens_wrath(self):
        app = self.start()
        self.assertEqual(app.realms[0]["name"], "WrathUnleashed")
        self.assertEqual(app.realms[0]["build"], 12340)
        self.assertFalse(any(r.get("host") == "duels.openvanilla.app" for r in app.realms))
        self.assertEqual(app.client()["id"], "wotlk")
        self.assertEqual(app.web_url(), "https://play.openvanilla.app/wrath")
        opened = []
        self.L.launch_web = lambda url, fs=True: (opened.append(url), (True, "ok"))[1]
        app.play_web()
        self.assertEqual(opened, ["https://play.openvanilla.app/wrath"])

    def test_a_realm_that_left_the_list_falls_back_to_wrath(self):
        app = self.start({"realm_host": "duels.openvanilla.app", "realm_index": 1})
        self.assertEqual(app.realm_index, 0)

    def test_status_comes_from_status_json_and_never_via_the_website(self):
        L = self.L
        asked = []
        L.tcp_ping = lambda host, port, timeout=2.5: 31
        L.http_json = lambda url, timeout=6: (asked.append(url), {"online": True, "players": 3, "bots": 60,
                                                                    "uptime_s": 99, "build": "3.3.5a"})[1]
        app = self.start()
        got = []
        app.after = lambda ms, fn, *a: got.append(a)
        app._probe_realm(0, app.realms[0])
        self.assertEqual(asked, ["https://play.openvanilla.app/wrath/status.json"])   # no /healthz, no /api/status
        st = got[-1][1]
        self.assertEqual((st["status"], st["via"], st["ping"]), ("online", "tcp", 31))
        self.assertEqual(st["detail"], "Players: 3 · Bots: 60")
        L.http_json = lambda url, timeout=6: {"online": False, "players": None, "bots": None}
        app._probe_realm(0, app.realms[0])
        self.assertEqual(got[-1][1]["status"], "offline")

        def down(url, timeout=6):
            raise OSError("no route")
        L.http_json = down
        app._probe_realm(0, app.realms[0])
        self.assertEqual((got[-1][1]["status"], got[-1][1]["detail"]), ("online", "Login server answering · status unavailable"))
        L.tcp_ping = lambda host, port, timeout=2.5: None
        app._probe_realm(0, app.realms[0])
        self.assertEqual((got[-1][1]["status"], got[-1][1]["via"]), ("partial", "tcp"))   # unavailable, not offline

    def test_own_335_folder_then_play_writes_its_realmlist(self):
        L = self.L
        app = self.start()
        ok, head, detail, _, action = app.readiness()
        self.assertFalse(ok)
        self.assertEqual(action, "choose_install")
        self.assertIn("3.3.5a game folder", detail)
        self.assertNotIn("Vanilla Client", detail)
        bad = os.path.join(self.tmp, "empty")
        os.makedirs(bad)
        root = self.wow335()
        picks = [bad, root]
        retries = []
        L.filedialog.askdirectory = lambda **k: picks.pop(0)
        L.messagebox.askretrycancel = lambda title, msg, **k: retries.append(msg) or True
        app._status_click()                                    # PLAY's bar: the folder picker, not the 1.12.1 page
        self.assertEqual(app.page, "play")
        self.assertTrue(retries and "Wow.exe" in retries[0] and "common.MPQ" in retries[0])
        self.assertEqual(app.client()["path"], root)
        self.assertEqual(app.settings["clients"]["wotlk"]["path"], root)
        self.assertNotEqual(app.settings.get("wow_folder"), root)   # the 1.12.1 folder (Solo) is left alone
        app.realm_state[app.realm_index] = {"status": "online", "ping": 30, "detail": "", "via": "tcp"}
        ok, head, *_ = app.readiness()
        self.assertTrue(ok, head)
        started = []
        L.subprocess.Popen = lambda args, **k: started.append((args, k.get("cwd")))
        app.session = {"user": "WR000042"}
        app.play_exe(app.client(), app.client_exe(), app.realms[app.realm_index])
        with open(os.path.join(root, "Data", "enGB", "realmlist.wtf")) as f:
            self.assertEqual(f.read().strip(), "set realmlist play.openvanilla.app")
        self.assertTrue(os.path.isfile(os.path.join(root, "Data", "enGB", "realmlist.wtf.openvanilla-backup")))
        self.assertFalse(os.path.exists(os.path.join(root, "Data", "enUS")))
        cfg = open(os.path.join(root, "WTF", "Config.wtf")).read()
        self.assertIn('SET realmList "play.openvanilla.app"', cfg)
        self.assertIn('SET accountName "WR000042"', cfg)
        self.assertIn('SET gxResolution "1920x1080"', cfg)
        self.assertEqual(started[0][1], root)
        self.assertEqual(self.errors, [])

    def test_realmlist_path(self):
        L = self.L
        root = self.wow335("deDE")
        self.assertEqual(L.realmlist_path(root, "Data/enUS/realmlist.wtf"), os.path.join(root, "Data", "deDE", "realmlist.wtf"))
        os.makedirs(os.path.join(root, "Data", "enUS"))
        self.assertEqual(L.realmlist_path(root, "Data/enUS/realmlist.wtf"), os.path.join(root, "Data", "enUS", "realmlist.wtf"))
        self.assertEqual(L.realmlist_path(root, "realmlist.wtf"), os.path.join(root, "realmlist.wtf"))   # 1.12.1


if __name__ == "__main__":
    unittest.main()

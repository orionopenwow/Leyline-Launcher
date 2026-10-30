"""The 1.57.0 bridge notice: "Open Vanilla is now Leyline". One plain card on start with a button that opens the
Leyline launcher download. Nothing is removed: this launcher keeps working and keeps updating.

    should_show(settings, flag_on, now)   the card shows on start until the player takes the download or says
                                          "Don't show again"; "Not now" waits SNOOZE_DAYS
    on_start(app)                         called once from the launcher's __init__
    show(app)                             the card itself (app.p2p_dialog)

live.json's flag "leyline_bridge" can hide it. Standard library only; Python 3.10 compatible.
"""
import time

FLAG = "leyline_bridge"
DOWNLOAD_URL = "https://github.com/orionopenwow/Leyline/releases/latest"
SNOOZE_DAYS = 7
TITLE = "OPEN VANILLA IS NOW LEYLINE"
TEXT = ("The new Leyline launcher is a separate download. You don't have to switch today: this launcher, "
        "your addons, realms and settings keep working and keep updating.")
BUTTON = "Get the Leyline launcher"


def _state(settings):
    s = settings.get("leyline_bridge")
    if not isinstance(s, dict):
        s = settings["leyline_bridge"] = {}
    return s


def enabled(live):
    try:
        return bool(live.flag(FLAG))
    except Exception:
        return True


def should_show(settings, flag_on=True, now=None):
    if not flag_on:
        return False
    s = _state(settings)
    if s.get("done"):
        return False
    now = time.time() if now is None else now
    return now >= float(s.get("snooze_until", 0) or 0)


def took_download(settings):
    _state(settings)["done"] = "download"


def never_again(settings):
    _state(settings)["done"] = "dismissed"


def snooze(settings, now=None):
    now = time.time() if now is None else now
    _state(settings)["snooze_until"] = now + SNOOZE_DAYS * 86400


def on_start(app):
    """Called once from the launcher's __init__: show the card shortly after the window is up."""
    if should_show(app.settings, enabled(getattr(app, "live", None))):
        app.after(1500, lambda: show(app))


def show(app, opener=None):
    if getattr(app, "_p2p_dialog", None) is not None:   # another card is up: next start instead
        return None
    if opener is None:
        import webbrowser
        opener = webbrowser.open
    dlg = app.p2p_dialog(TITLE, TEXT, width=540)

    def save():
        try:
            app.save_settings()
        except Exception:
            pass

    def get():
        took_download(app.settings)
        save()
        dlg.close()
        opener(DOWNLOAD_URL)

    def later():
        snooze(app.settings)
        save()
        dlg.close()

    def never():
        never_again(app.settings)
        save()
        dlg.close()

    dlg.buttons((BUTTON, get, True), ("Not now", later, False), ("Don't show again", never, False))
    return dlg

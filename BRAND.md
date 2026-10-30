# Brand: the project is called **Leyline** (formerly Open Vanilla)

Decided 29 October 2026 ("rename repo to Leyline Launcher"). Before that, from 17 October 2026, the
project was called Open Vanilla; before that it had an older name. Neither old name is used for
anything new that a player, creator or visitor reads.

## The rule

- Everything people see says **Leyline**: the website, the game page, the installer, docs and plans.
  This launcher, the program in this repository, is the **Leyline Launcher**. The newer Leyline
  launcher (realms and mods for every client) lives in its own repository, `github.com/orionopenwow/Leyline`.
- Write it as one word, capitalised: **Leyline**, **Leyline Launcher**. Possessive: Leyline's.
- "Formerly Open Vanilla" is fine where people need to recognise us (the repo description, the 1.57.0
  bridge card and its release notes). Nowhere else.
- File names are the exception: `OpenVanilla.exe`, `OpenVanilla-Setup-<v>.exe`, `OpenVanilla_<v>_Win64.zip`
  keep their names (see below).
- Never write the game's trademark names in anything people see: say "the game", "1.12.1", "3.3.5a", "Wrath".

## Where things stand

| What | Now | Notes |
|---|---|---|
| Repository | `github.com/orionopenwow/Leyline-Launcher` | Renamed from `OpenVanilla` on 29 October 2026 (the one-off rename tool is in git history). GitHub redirects the old address (web, git, API, release downloads) as long as no new repo takes the old name |
| Launcher | `OpenVanilla.exe`; window, tray, Start menu and desktop shortcuts say "Leyline Launcher" | 1.57.0 removes the old "Open Vanilla" shortcuts and shows one card with a button to the Leyline launcher download |
| Engine | `Game\Open Vanilla Game.exe` | File name kept: installs and the updater look for it |
| Downloads | `OpenVanilla-Setup-<v>.exe`, `OpenVanilla_<v>_Win64.zip`, `OpenVanilla-Server.zip` | File names kept, so old links and the updater keep working |
| Data folder | `%LOCALAPPDATA%\OpenVanilla` (installer), beside the exe (zip) | Never moved |
| From source | `Play Leyline Launcher.bat` / `.command` | `Play Open Vanilla.bat` / `.command` stay as one-line forwarders for old shortcuts |
| Server download | `Start Leyline Server.bat` inside `OpenVanilla-Server.zip` | |
| Logo | The Leyline mark: a blue crystal in a blue/violet swirl, flat on dark, with the name in a rounded sans (Nunito ExtraBold) | Sources in `assets/branding/leyline-{swirl,crystal,mark,app-icon}-512.png`; `tools/make_leyline_logos.py` writes every copy. Wherever it moves (the site's header and hero, every loading screen, the launcher's corner) the swirl turns and the crystal stays upright: `.ly-spin` in `www/assets/leyline/leyline.css` |

## What keeps the old name for now (and why)

These are technical names. Changing them breaks links, saved settings, installs or builds, so they
change only with a redirect or migration.

| Kept for now | Example | Why |
|---|---|---|
| Domains | `openvanilla.app`, `play.openvanilla.app` | Existing links, sign-in redirects, the launcher's update manifest (`openvanilla.app/downloads/version.json`). A new domain comes later |
| Repo homepage | `https://play.openvanilla.app/wrath/leyline` | Until the new domain |
| Container images | `ghcr.io/orionopenwow/openvanilla-realm`, `openvanilla-mangos` | Deleted by the owner (October 2026), and this repo no longer builds them (the realm-image workflows are gone). `labs/openvanilla-realm/hetzner/*_up.sh` still name them: the running realm keeps the image it has, but a fresh pull fails until the realm has another image source |
| Code and config | `openvanilla_*` scripts and modules, `openvanilla://` links, `OPENVANILLA_*` environment variables, settings keys, addon saved-variable names, protocol headers | Internal; renaming has no player benefit and would lose saved data |
| Hero Key files | `-----BEGIN OPEN VANILLA HERO KEY-----` | Keys players already saved must keep loading |
| Firewall rules | `Open Vanilla Host TCP <port>` | Hosts' existing rules must still be found and removed |
| Realm and client names | `Open Vanilla Solo`, `Open Vanilla Classic+` | Saved realm lists and client choices |
| In-game text | the realm patches (`labs/openvanilla-realm/realm/patches`, `labs/openvanilla-realm/realm/mangos`) and the addons in `Data/` | Changes with the next realm image and addon release |
| Workshop packages | `www/community/workshop/cp-*` | Rebuilt with the next Workshop build (their old GitHub links redirect) |

## Still to do

1. **Domain:** buy the new domain, serve the site there, and redirect `openvanilla.app` permanently (301).
   Move sign-in redirects, the update manifest URL and the repo homepage.
2. **In-game text and Workshop packages:** the next realm image and Workshop build say Leyline.
3. **Socials and Discord:** names and descriptions (the owner's call).

Check before any public post: `git grep -n "Open Vanilla" -- www` should only show the kept names above.

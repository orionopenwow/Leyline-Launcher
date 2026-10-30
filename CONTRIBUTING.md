# Contributing to Leyline

Thanks for helping. This repository is the classic Leyline Launcher, Leyline Server and the Leyline
website. Leyline's new launcher, host kit and relay are in
[orionopenwow/Leyline](https://github.com/orionopenwow/Leyline); contribute there for those.

## Where things live

| Folder | What it is |
|---|---|
| `launcher/` | The classic launcher (Python, Tk); `launcher/p2p` is hosting |
| `www/` | The website, openvanilla.app (GitHub Pages) |
| `packaging/` | Release builds and the source of every workflow |
| `Data/Interface/AddOns/`, `realm/classicplus/` | The addon suite the launcher ships, and the Classic+ SQL Play Solo and Leyline Server apply |
| `workshop/` | The Workshop catalogue behind the website's mods hub |
| `devkit/` | Fast checks, the addon simulator, SQL tests, Herald Lite |
| `labs/` | Earlier tools and experiments, kept for later: the frozen 1.12 realm, Herald, the old relay, Vanilla Forge (`labs/README.md`) |

## Before you open a pull request

1. Run the fast checks: `py -3 devkit/check.py` (seconds; see `devkit/README.md`).
2. Run the tests near your change, for example `py -3 -m pytest tests/test_portal_bridge.py`,
   `lua5.1 devkit/sim/run_tests.lua` for addons, or `cargo test` in the patched client for a
   realm patch.
3. Add a test that fails without your fix (`devkit/README.md`, "Adding a test when you fix a bug").
4. Keep the change to one thing, and say in the description what you changed, why, and how you
   checked it.

## Rules that keep the project safe

- **No game data from the original game, ever:** no MPQs other than our own `patch-Z`, no maps, models, textures,
  tables or client files. Players bring their own data. `devkit/check.py` refuses them.
- **No code from closed or leaked sources**, and none built on decompiled original clients.
- **Credit prior art.** If your change builds on another project, link it in the description.
  Fixes that belong upstream (CMaNGOS, PlayerBots, wenilla, benilla) go there too.

## Using AI tools

You may use AI to help write code. You are responsible for every line: read it, test it, and be able
to explain it in review. Say in the pull request that AI helped. Write descriptions, issues and posts
in your own words.

## Reporting bugs

In game, type `/bug` (it attaches your settings and frame rate). On GitHub, use the bug report form.
Security problems: see `SECURITY.md` and report them privately.

## Licensing

Your contribution is released under the MIT License in `LICENSE`. Patches that modify another
project (`labs/openvanilla-realm/realm/mangos/*.patch` for CMaNGOS and PlayerBots, `labs/openvanilla-realm/realm/patches/*.patch` for wenilla)
also fall under the license of the project they modify.

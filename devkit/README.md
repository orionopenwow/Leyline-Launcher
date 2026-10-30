# Leyline devkit

Fast checks and tests for the classic launcher, its addon suite and Leyline Server. Nothing here
ships to players. **Start with `devkit\Dev.bat`** (Windows) or run the parts below directly.

| Part | What it is | Run |
|---|---|---|
| `check.py` | Repo checks: .toc lists, Lua parses, patch-Z matches `Data/Interface`, JSON/YAML/JS/shell/Python parse, realm_up downloads every page file, version vs website links, no game data in git, no original-binary citations, generated files current | `py -3 devkit\check.py` (`--strict` in CI) |
| `sim/` | Every addon in a fake 1.12 game: ~2 s. Two fake players for Persona and Concord. | `lua5.1 devkit/sim/run_tests.lua` |
| `db/` | Our SQL applied twice to a throwaway MariaDB with stock classic-db rows; checks it's re-runnable and does its job | `py -3 devkit\db\test_sql.py` (Docker) or `--local` |
| `heraldlite/` | Headless test bot (Rust): logs in, buys from a vendor, checks weapon skills, trades a Persona between two bots. Built into Leyline Server by `release.yml` | `Dev.bat` option 5 |
| `uistudio/` | UI Studio: move and restyle the addons' windows, then write `Layout.lua` | `uistudio\UI_Studio.bat` |
| `citations.py`, `mpqread.py`, `audit.py` | The citation patterns, a pure-Python MPQ reader, pre-release secret and dependency checks | |

`packaging/workflows/devkit.yml` runs check.py, the Lua sim, the SQL tests, the Warfront rule tests, the dev
proxy tests and Herald Lite's tests on every push.

The 1.12 realm's tools that used to live here (the dev proxy, the staging realm, the load lab, the patch-Z
Docker image, the touch lab) are in `labs/openvanilla-realm/devkit/` (`labs/README.md`). `Dev.bat` still
starts them from there.

## Adding a test when you fix a bug

- Addon bug: a `T.test(...)` in `sim/tests/<addon>.lua` that fails before the fix (see `sim/README.md`).
- Server/SQL bug: a check in `db/test_sql.py`, or a scenario line in `heraldlite/scenarios/`.
- Page bug: a check in `labs/openvanilla-realm/realm/www/owdiag-checks.js`.

## Rules

- No game data from the original game in git: the sim and SQL tests use none, and check.py refuses map, model and
  MPQ files (Warfront's and Duels' Interface-only patch-Z are the exception; Classic+'s patch-Z is built locally
  with `tools/sync_patchz.py --dbc-dir DIR` and never committed).
- Tools here are for building and testing; nothing in `devkit/` ships to players.

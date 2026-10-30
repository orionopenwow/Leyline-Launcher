# The 1.12.1 "Open Vanilla" realm (frozen)

This is the realm Leyline started as: a 1.12.1 realm (Vanilla Remastered, Warfront, Duels, Boss Fights)
with a browser client, run on one Linux server. It is **no longer planned**. Leyline now runs one
temporary sample realm, the Dalaran Hangout (3.3.5a), from the new launcher's repository, and focuses on
the mod launcher and the P2P realm network.

Nothing here is deleted; it moved from the repository root on 30 October 2026 (`git log --follow`
keeps every file's history).

## What is here

| Folder | Was | What it holds |
|---|---|---|
| `realm/` | `realm/` (all but `realm/classicplus`) | `Dockerfile` and `patches/` (the browser client and realm service), `mangos/` (world server patches), `www/` (the realm page layer), `login-backdrop/`, `achievements/`, `ascension/`, `bossfights/`, `duels/`, `transmog/`, `warfront/` (with Warfront's and Duels' committed patch-Z) |
| `hetzner/` | `hetzner/` | Every server script: `openvanilla_realm_up.sh`, `*_up.sh`, the hot patcher, crons, systemd units, GM console, Caddy and compose files |
| `host/` | `host/cloud_init_*.yaml` | Cloud-init files for a fresh Hetzner or Oracle VM |
| `devkit/` | `devkit/{staging,loadlab,patchz,touchlab,proxy}` | The staging realm, the load-time lab, the patch-Z Docker builder, the touch lab and the dev proxy |
| `workflows/` | `.github/workflows` and `packaging/workflows` | `hotpatch.yml` (SSH hot updates on push to `stable`), `loadgate.yml` (load-time gate), `owbot.yml` (the nightly test bot). Parked: GitHub does not run workflows from here |
| `tools/` | `tools/` | Realm-only tools: `owbot.mjs` and `Run_Herald.bat`, `botlab/`, `telemetry/`, `update_web_client.py`, the pre-launch database checks, `combo_audit.py`, the realm UI sheet tools |
| `web-client/` | `www/patch_wasm.py` | The one-off patcher for a browser client build (offsets fixed for one build) |
| `tests/` | `tests/`, `tools/tests/` | The realm page tests (`*.mjs`), the GM console and the achievements generator tests |

What stayed outside, because the classic launcher still uses it:

- `realm/classicplus/`: the Classic+ SQL and fix-ups that Play Solo (`play_local.py`) and Leyline Server
  (`packaging/build_server.py`) apply. `devkit/db/test_sql.py` tests it.
- `host/ovhost` and `Host a Realm.command`: macOS/Linux hosting from `openvanilla_server.py`. It runs the
  deleted realm images, so a fresh install does not work until the realm has an image again.
- `Data/Interface/`: the addon suite the launcher ships. `tools/prepush.py` still rebuilds Warfront's and
  Duels' patch-Z (in `realm/warfront` and `realm/duels` here) from it, and `devkit/check.py` still checks
  them, so they never go stale.
- `tools/warfront/`, `tools/duels/`, `tools/gen_ui_manifest.py`, `tools/gen_achievements.py`: run by
  `prepush.py`, or they also write files the website or the addons use.

## What no longer works

- **Images.** The `openvanilla-realm` and `openvanilla-mangos` container packages were deleted, and the
  `realm-image.yml` / `realm-prebuild.yml` workflows that built them were removed (last present at
  `b214b7d`). A running server keeps the image it has; a fresh pull fails.
- **Downloads from GitHub.** The server scripts fetch their files from
  `https://raw.githubusercontent.com/orionopenwow/OpenVanilla/stable/hetzner/...` and `.../stable/realm/...`.
  Once `stable` contains this move those paths are gone. Point each script's `RAW` (some read `OW_RAW` or
  `OPENVANILLA_RAW` from the environment; others set it in the script) at a commit from before the move (for example
  `https://raw.githubusercontent.com/orionopenwow/Leyline-Launcher/b214b7d`), or update the paths.
- **Hot updates, the load gate and the nightly test bot.** Their workflows are parked in `workflows/`.
- The public guide (`www/guide.html`, "rented server") still shows the old `curl .../stable/hetzner/...`
  commands.

## Bringing it back

1. Move the folders back: `git mv labs/openvanilla-realm/realm/* realm/`, `git mv labs/openvanilla-realm/hetzner hetzner`,
   and the same for `host/`, `devkit/*` and `tools/*`. Or keep them here and change the paths below instead.
2. Restore the image workflows from `b214b7d`:
   `git show b214b7d:packaging/workflows/realm-image.yml > packaging/workflows/realm-image.yml`
   (and `realm-prebuild.yml`), copy both into `.github/workflows`, and let `loadgate.yml` trigger on
   `realm-image` again. They expect `realm/Dockerfile`, `realm/patches`, `realm/login-backdrop` and
   `realm/mangos` at the root.
3. Re-create the `ghcr.io/orionopenwow/openvanilla-{realm,mangos}` packages (or point the `*_up.sh`
   scripts at another registry), then run the workflows once.
4. Put `hotpatch.yml`, `loadgate.yml` and `owbot.yml` back in `packaging/workflows` and `.github/workflows`.
   They need the secrets `REALM_SSH_HOST`, `REALM_SSH_KEY`, `REALM_URL`, `OWBOT_USER`, `OWBOT_PASS`
   (and optionally `OWBOT_WEBHOOK`).
5. Revert the path changes in `devkit/check.py`, `tools/prepush.py`, the tools listed above, the tests and
   `devkit.yml` (the commit "labs/openvanilla-realm: the 1.12 realm and its operations, frozen" lists them).

# labs/

Tools and experiments we built along the way, kept for later. None of this is part of the classic
Leyline Launcher build, its release or the website build, and none of it is maintained day to day.
Everything was moved here with `git mv`, so `git log --follow <file>` shows its full history.

Leyline itself (the mod launcher and P2P realm network, one-click hosting from the browser or the
desktop, the mods hub and the Dalaran Hangout sample realm) lives in
[orionopenwow/Leyline](https://github.com/orionopenwow/Leyline). See the [repository README](../README.md)
for what this repository still ships.

| Folder | What it is | Status | Still used by the rest of the repo |
|---|---|---|---|
| [`openvanilla-realm/`](openvanilla-realm/README.md) | The 1.12.1 "Open Vanilla" realm: wenilla-realm and CMaNGOS patches, Warfront, Duels, Boss Fights, Transmog, the realm page layer (`realm/www`), the server scripts (`hetzner/`), cloud-init files, realm dev tools and the parked realm-ops workflows | **Frozen.** Not planned any more; its container packages are deleted | Yes, a little: `devkit/check.py` and `tools/prepush.py` keep Warfront's and Duels' patch-Z in step with `Data/Interface`, and `devkit.yml` still runs the Warfront rule tests, the dev proxy tests and `devkit/db/test_warfront_sql.py` |
| [`herald/`](herald/HERALD.md) | Herald, the realm's Discord bot: gate, support desk, moderation, the World chat bridge, live-stream alerts, Boss Fights cards, and the autopilot API (`herald_autopilot_api.py`) | **Frozen** with the realm it served | `tests/test_herald_autopilot.py` imports `herald_autopilot_api.py` (Herald Autopilot, `autopilot/`, ships in Leyline Server) |
| [`relay/`](relay/README.md) | `openvanilla-relay`, a Rust WebSocket relay for the classic launcher's "Through Leyline" hosting | **Superseded** by the relay that ships with the new launcher and host kit. Never deployed | The classic launcher's `launcher/p2p` speaks its protocol; `tests/test_node_network.py` runs against a built binary in `labs/relay/target` when there is one |
| [`forge/`](forge/README.md) | Vanilla Forge, the 1.12 creator app (Rust + Tauri): world editor, models, quests, items, packs | **Kept, buildable.** `forge.yml` still tests it and releases it from a `forge-v*` tag | Its sources include `tools/modelport` and `devkit/sim`; `tools/forge_verify.py` and `tests/test_forge_lite.py` read its world schema |
| [`legend/`](legend/SPEC.md) | Legend v1, signed character records issued by the Duels realm | **Frozen** | `legend/build_html.py` writes the website's `www/legend.html` |
| [`prototypes/realm-composer/`](prototypes/realm-composer/realm_composer.py) | Realm Composer: recipe-based realm setup, pack conflict checks | **Prototype**, never wired in | No |

## Running things in labs

- Python tests run where they are, for example `python3 -m pytest -q labs/herald/tests` or
  `python3 -m pytest -q labs/openvanilla-realm/tests`.
- The paths inside these folders were updated where the repo itself runs them (tests, checks,
  `prepush.py`, the Forge build). Scripts that only ran on the realm server (`openvanilla-realm/hetzner/*.sh`)
  still name their old paths and download from `.../stable/hetzner/...` and `.../stable/realm/...`;
  see [openvanilla-realm/README.md](openvanilla-realm/README.md) before running one.

## Bringing something back

Move the folder back to where it was (`git mv labs/<name> <name>`), then undo the path changes the
move made: `git log --stat -- labs/<name>` lists the commit, and its message lists every file it
touched outside labs/.

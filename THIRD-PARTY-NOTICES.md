# Third-party notices

Leyline's own code is MIT licensed (`LICENSE`). These parts come from elsewhere or work with outside software:

- **Leyline display font** (`stream/www-files/art/leyline-display.woff2`): Big Shoulders Display,
  SIL Open Font License 1.1. The license is next to it: `stream/www-files/art/leyline-display-OFL.txt`.
- **Launcher font** (`launcher/ui/art/fonts/`): Inter, SIL Open Font License 1.1. The license is next to it:
  `Inter-OFL.txt`.
- **Ed25519 fallback** (`hosting/kit/tools/wunet/ed25519_pure.py`): from the Leyline Launcher (the older Python launcher), the same
  project, MIT.
- **SRP6 test vectors** (`hosting/tests/test_crypto.py`): from a public MIT-licensed SRP test corpus.
- **AzerothCore** (AGPL-3.0): the realm images the host kit runs are built from AzerothCore and its modules.
  No AzerothCore source is in this repo; its sources are at https://github.com/azerothcore.
- **Tauri** (MIT or Apache-2.0) and the Rust crates in `launcher/src-tauri/Cargo.lock`, each under its own
  license (mostly MIT or Apache-2.0): the launcher is built with them; none of their source is in this repo.
- **Other server cores** (host any client): the host kit's profiles in `hosting/kit/profiles/` build CMaNGOS
  Classic and TBC (GPL-2.0, https://github.com/cmangos) and TrinityCore 4.3.4 (GPL-2.0,
  https://github.com/The-Cataclysm-Preservation-Project/TrinityCore) on the host's PC from that source at pinned
  commits, with each project's own database. None of their source is in this repo; credits and licences: each
  profile's `NOTICE.md`.
- **Game data**: none here. Hosts extract dbc and map files from their own client of the realm's version (3.3.5a,
  or 1.12.1, 2.4.3, 4.3.4 for the other profiles), on their own PC, and they never leave it.

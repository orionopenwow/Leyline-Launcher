# Beacons: realm records (`www/realms/`)

Every realm has one record, `www/realms/<slug>.json`: its beacon. The website renders it at
`realms.html#<slug>` (and in the list at `realms.html`). The launcher, the browser client's realm
list and the GM console read the same files from `https://openvanilla.app/realms/`, so the page and
the Connect button can never disagree.

`www/realms/index.json` lists which records exist (a static site can't list a folder):

```json
{ "schema": 1, "updated": "2026-10-24", "realms": ["wrathunleashed", "vanilla-remastered"] }
```

The list on the page is in `order`, then name. Nothing else changes the order: no paid placement,
no votes. v1 lists official realms only.

## Record

| Field | Type | Meaning |
|---|---|---|
| `schema` | `1` | This document's version. Readers ignore records with a higher number they don't know. |
| `slug` | string | `^[a-z0-9-]{1,40}$`, the same as the file name. Never changes once published (links use it). |
| `name` | string | Realm name as players see it. |
| `official` | bool | Run by Open Vanilla. v1: always `true`. |
| `state` | `"live"` \| `"offline"` \| `"soon"` | What the realm is meant to be doing. `live` means "running, check `status`". |
| `stateNote` | string? | Optional short reason, e.g. "Offline while WrathUnleashed runs." |
| `order` | int | Sort key in the list (low first). |
| `tagline` | string | One line under the name. Owner-written. |
| `summary` | string | A short paragraph on the realm page. Owner-written. |
| `type` | string | `PvE`, `PvP`, `RP`, `RP-PvP`, `Fun`. |
| `profile` | object \| null | How to connect, see below. `null` until the realm has one. |
| `connect` | object \| null | The Connect / Play button, see below. `null` = no button. |
| `rules` | string[] | Realm rules, one per line. |
| `features` | `{title, text?}[]` | What the realm has. Only things that exist today. |
| `media.icon` | path \| null | Small emblem, path from the site root (`assets/...`). |
| `media.screenshots` | `{src, alt, caption?}[]` | Gameplay screenshots, paths from the site root, e.g. `realms/img/wrathunleashed/1.webp`. |
| `media.trailer` | https URL \| null | Trailer link (opened in a new tab, not embedded). |
| `discord` | https URL \| null | Discord invite for the realm. |
| `status` | `{url, format}` \| null | The realm's own status endpoint, see below. `null` = no live status. |
| `leaderboards.duels` | `{url, label?}` \| null | Link to the realm's Duels Legends board, if it issues one. |
| `leaderboards.bossfights` | `{url, label?}` \| null | Link to the realm's Boss Fights times, if it issues them. |
| `updated` | `YYYY-MM-DD` | Last edit of this record. |

### `profile`

| Field | Type | Meaning |
|---|---|---|
| `game` | string | e.g. `Wrath of the Lich King`, `World of Warcraft`. |
| `version` | string | Client version, e.g. `3.3.5a`, `1.12.1`. |
| `build` | int | Client build, e.g. `12340`, `5875`. |
| `address` | string \| null | Realmlist host (`set realmlist <address>`). |
| `port` | int \| null | Auth port (3724 by default). |
| `warden` | bool \| null | Is Warden on. `null` = not stated. |
| `ruleset` | string | Short name of the ruleset, e.g. `fun`, `blizzlike`. |
| `patches` | `{file, sha256, url?}[]` \| null | Patches the player must have, with their SHA-256. `[]` = none required; `null` = not stated yet (shown as nothing). |
| `clientFiles` | `"own"` | Players bring their own game files. Open Vanilla never hosts game data. |
| | `"stream-or-own"` | A small part of the game streams to signed-in players; the whole world needs their own files. |

### `connect`

| Field | Type | Meaning |
|---|---|---|
| `kind` | `"web-signin"` \| `"browser"` \| `"launcher"` | What the button opens: a sign-in page, the browser client, or the launcher (`openvanilla://`). |
| `url` | string | `https://...` or `openvanilla://...`. |
| `label` | string | Button text. |
| `note` | string? | One or two lines shown next to the button. |

The button only shows while `state` is `live`.

### `status`: the realm's own endpoint

`format: "openvanilla-status-1"`. The endpoint answers `GET` with `Access-Control-Allow-Origin: *`:

```json
{ "online": true, "players": 3, "bots": 200, "uptime_s": 93784, "build": "3.3.5a",
  "updated_at": "2026-10-24T20:03:15Z" }
```

- `online` (bool), `players` (int or null: real players), `bots` (int or null: counted separately,
  never added to `players`), `uptime_s` (int or null), `build`, `updated_at` (ISO 8601 UTC).
- Extra fields are allowed (WrathUnleashed adds `realm`, `queue`, `bots_method`).
- Readers show `null` as "not known", never as 0. An endpoint that doesn't answer is shown as
  "status unavailable", not as offline.
- Population only ever comes from here, never from votes or from the record.

## Text the owner hasn't written yet

Any string that starts with `TODO` is a placeholder. The website hides it; open
`realms.html?preview=1#<slug>` to see placeholders outlined. Readers (launcher, client, GM console)
should treat `TODO...` strings as empty too.

## Images

Only the owner's own uploads: gameplay screenshots, no Blizzard logos or box art. Put them in
`www/realms/img/<slug>/` as `.webp`, about 1600 px wide, and list them in `media.screenshots`
with an `alt` text.

## Paths and links

- Image paths are relative to the site root, with no `..`, no leading `/` and no `//`. Readers
  outside the site resolve them against `https://openvanilla.app/`.
- Links (`connect.url`, `discord`, `media.trailer`, leaderboard `url`) are `https://` (or
  `openvanilla://` for `connect`). Anything else is ignored by the page.

## Adding a realm

1. Copy `wrathunleashed.json` to `<slug>.json` and edit it.
2. Add the slug to `realms` in `index.json`.
3. Put its screenshots in `img/<slug>/`.
4. Check: `python -c "import json;json.load(open('www/realms/<slug>.json'))"`, then open
   `realms.html?preview=1#<slug>` locally (`python -m http.server` in `www/`).

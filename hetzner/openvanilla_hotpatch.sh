#!/usr/bin/env bash
# Open Vanilla hot update: ship what changed on GitHub with the smallest restart it needs.
#
#   bash /opt/openvanilla-classicplus/repo/hetzner/openvanilla_hotpatch.sh            apply what changed
#   bash .../openvanilla_hotpatch.sh --dry-run                                      only show the plan
#   bash .../openvanilla_hotpatch.sh --world-restart                                also run a queued world restart
#                                                                                (5-minute in-game countdown)
#   bash .../openvanilla_hotpatch.sh --force-web                                    restart the web service even
#                                                                                with players online
#
# It keeps a sparse clone of the repo in /opt/openvanilla-classicplus/repo, remembers the last commit
# it applied, and sorts every changed file into one of three tiers:
#
#   0  no restart at all — players get it on their next page load or /reload
#        realm/www/*                    page layer (dock, boot art, owdiag), a mounted folder
#        realm/classicplus/bridge.js*   the page bridge (mounted file, rewritten in place)
#        realm/classicplus/addons-loader.js
#        world SQL tables with a .reload command (see RELOADABLE below), via SOAP
#   1  web service restart, ~5 s — the world server keeps running, nobody loses progress, but
#        players in the browser reconnect; done straight away when nobody is online, otherwise
#        at the next empty moment (the script waits up to 30 min) or with --force-web
#        patch-Z.MPQ client data (the realm opens the archive chain at startup): built here by
#        openvanilla_build_patchz.sh when Data/Interface, its tools or realm/classicplus/dbc_deltas change
#        a new ghcr.io/orionopenwow/openvanilla-realm image (engine patches)
#   2  world restart — only for data the world server reads once at boot
#        classicplus_races.sql / _weapons.sql (playercreateinfo), server DBC files
#        Applied to the database/volume now; the restart is queued (run with --world-restart,
#        which counts down 5 minutes in game with .server restart 300).
#
# A GitHub Action (.github/workflows/hotpatch.yml) runs this over SSH on every push that touches
# these paths, so most changes are live a minute after the push, with no image rebuild.
set -euo pipefail
# OW_REALM_DIR / OW_CP point it at the staging stack instead (devkit/staging/promote.sh does).
REALM_DIR=${OW_REALM_DIR:-/opt/wenilla-realm}
CP=${OW_CP:-/opt/openvanilla-classicplus}
export OW_REALM_DIR=$REALM_DIR OW_CP=$CP
REPO_DIR=$CP/repo
REPO_URL=${OPENVANILLA_REPO:-https://github.com/orionopenwow/OpenVanilla}
STATE=$CP/.hotpatch-applied
QUEUE=$CP/.hotpatch-queued-world-restart
DRY=0 WORLD=0 FORCE_WEB=0 TO=""
while [ $# -gt 0 ]; do case $1 in
  --dry-run) DRY=1;; --world-restart) WORLD=1;; --force-web) FORCE_WEB=1;;
  --to) TO=${2:?--to needs a commit}; shift;;    # apply up to this commit (what staging passed), not the newest
  *) echo "unknown option $1"; exit 2;; esac; shift; done
say() { printf '\033[1;33m== %s\033[0m\n' "$*"; }
[ "$(id -u)" -eq 0 ] || { echo "Run as root"; exit 1; }
# WrathUnleashed (3.3.5a, AzerothCore, 2026-10-24) runs on this server in place of the 1.12 realm. Its deploy
# (WrathUnleashed/server/deploy.sh) stopped this stack's mangosd and realmd, put its sign-in page and SOAP bridge
# (container wu-portal) on this stack's network under the name "mangosd", and added /wrath to the site's Caddyfile.
# A hot update here would write the 1.12 world database, pull and recreate the realm service the Wrath sign-in
# depends on, and send .announce through the bridge to Wrath's players: so while Wrath is live it does nothing.
# /srv/wrath/rollback.sh (back to vanilla) removes both markers; OV_ALLOW_WITH_WRATH=1 forces a run anyway.
wrath_live() { [ -e /srv/wrath/stopped-vanilla.txt ] || docker ps -a --format '{{.Names}}' 2>/dev/null | grep -qx wu-portal; }
if [ $DRY = 0 ] && [ "${OV_ALLOW_WITH_WRATH:-0}" != 1 ] && wrath_live; then
  say "WrathUnleashed is the live realm on this server: the 1.12 realm is parked, nothing was updated"
  echo "  (bash /srv/wrath/rollback.sh brings vanilla back; OV_ALLOW_WITH_WRATH=1 forces this update anyway)"
  exit 0
fi
cd "$REALM_DIR"
set -a; . ./.env; set +a
mkdir -p "$CP/www"

# -- 1. What changed ---------------------------------------------------------------------------
export GIT_TERMINAL_PROMPT=0   # the repo is public: never stop and ask for a GitHub password
if [ ! -d "$REPO_DIR/.git" ]; then
  git clone --depth 50 --filter=blob:none --sparse "$REPO_URL" "$REPO_DIR"
fi
# a checkout made before the repo moved still points at the old address: always the current one
git -C "$REPO_DIR" remote set-url origin "$REPO_URL"
git -C "$REPO_DIR" sparse-checkout set realm/classicplus realm/www hetzner devkit/staging devkit/heraldlite Data/Interface tools
# the live realm follows the stable branch (Release.bat moves it); main is work in progress
# by name: a --depth clone tracks only the default branch, so a bare "fetch origin stable" never
# creates origin/stable
git -C "$REPO_DIR" fetch --depth 50 -q origin "+refs/heads/stable:refs/remotes/origin/stable"
git -C "$REPO_DIR" reset -q --hard "${TO:-origin/stable}"
HEAD=$(git -C "$REPO_DIR" rev-parse HEAD)
LAST=$(cat "$STATE" 2>/dev/null || true)
if [ -n "$LAST" ] && git -C "$REPO_DIR" cat-file -e "$LAST" 2>/dev/null; then
  CHANGED=$(git -C "$REPO_DIR" diff --name-only "$LAST" "$HEAD" -- realm/classicplus realm/www Data/Interface \
            tools/sync_patchz.py tools/classicplus_dbc.py tools/modelport)
else
  CHANGED=$(cd "$REPO_DIR" && find realm/classicplus realm/www -type f | sort; echo Data/Interface)   # first run: everything
fi
say "Open Vanilla hot update ${LAST:0:8} -> ${HEAD:0:8}"
[ -n "$CHANGED" ] && printf '  %s\n' $CHANGED || echo "  (no file changes)"

T1=0 T2=0 PATCHZ=0
SQL_RELOAD=()
# A SQL file is tier 0 when every table it writes has a CMaNGOS .reload command; any other table
# (playercreateinfo, creature_template, ...) is read at world start, so it is tier 2.
sql_reloads() {  # sql_reloads FILE -> the .reload commands, or nothing if a restart is needed
  python3 - "$1" <<'PY'
import re, sys
MAP = {
    r".*_loot_template": "reload all_loot",
    r"gossip_menu.*|npc_gossip|npc_text": "reload all_gossips",
    r"npc_vendor": "reload npc_vendor",
    r"npc_trainer": "reload npc_trainer",
    r"creature_questrelation|creature_involvedrelation|gameobject_questrelation|gameobject_involvedrelation": "reload all_quest",
    r"command": "reload command",
    r"mangos_string": "reload mangos_string",
    r"game_tele": "reload game_tele",
}
sql = re.sub(r"--[^\n]*", "", open(sys.argv[1], encoding="utf-8", errors="replace").read())
tables = set(t.lower() for t in re.findall(r"(?:insert(?:\s+ignore)?\s+into|replace\s+into|update|delete\s+from)\s+`?(\w+)`?", sql, re.I))
cmds = []
for t in sorted(tables):
    hit = next((c for pat, c in MAP.items() if re.fullmatch(pat, t)), None)
    if hit is None:
        sys.exit(0)          # unknown table: needs a world restart
    if hit not in cmds:
        cmds.append(hit)
print("\n".join(cmds))
PY
}
compose_exec_sql() { MYSQL_PWD="$DB_ROOT_PASSWORD" docker compose exec -T -e MYSQL_PWD mariadb mariadb -uroot "$@"; }
in_place() {  # in_place SRC DST: rewrite DST's bytes, keeping its inode (single-file bind mounts)
  if [ -e "$2" ]; then cat "$1" > "$2"; else cp "$1" "$2"; fi; chmod 644 "$2"
}

for f in $CHANGED; do
  src="$REPO_DIR/$f"; base=$(basename "$f")
  case "$f" in Data/Interface*|tools/*|realm/classicplus/dbc_deltas/*|realm/classicplus/fix_skillraceclassinfo.py|realm/classicplus/classicplus_weapons.sql)
    PATCHZ=1 ;; esac   # patch-Z's sources: it is built once, after this loop
  case "$f" in Data/Interface*|tools/*|realm/classicplus/dbc_deltas/*) continue ;; esac
  [ -e "$src" ] || { echo "  - $f deleted upstream; left in place"; continue; }
  case "$f" in
    realm/www/*)
      rel=${f#realm/www/}
      echo "  [0] page  $rel"
      [ $DRY = 1 ] || { mkdir -p "$CP/www/$(dirname "$rel")"; cp "$src" "$CP/www/$rel.new"; chmod 644 "$CP/www/$rel.new"; mv "$CP/www/$rel.new" "$CP/www/$rel"; } ;;
    realm/classicplus/bridge.js*|realm/classicplus/addons-loader.js)
      echo "  [0] page  $base"
      [ $DRY = 1 ] || in_place "$src" "$CP/$base" ;;
    realm/classicplus/*.sql)
      cp "$src" "$CP/$base"
      mapfile -t R < <(sql_reloads "$src")
      if [ "${#R[@]}" -gt 0 ] && [ -n "${R[0]}" ]; then
        echo "  [0] SQL   $base + ${R[*]/#/.}"
        [ $DRY = 1 ] || { compose_exec_sql classicmangos < "$src"; SQL_RELOAD+=("${R[@]}"); }
      else
        echo "  [2] SQL   $base (read at world start)"
        T2=1; [ $DRY = 1 ] || compose_exec_sql classicmangos < "$src"
      fi ;;
    realm/classicplus/fix_skillraceclassinfo.py)
      echo "  [2] server SkillRaceClassInfo.dbc (checked below)" ;;
    realm/classicplus/*)
      echo "  [-] $base copied (used by openvanilla_realm_up.sh)"
      [ $DRY = 1 ] || cp "$src" "$CP/$base" ;;
  esac
done

# Client patch-Z: built here from its sources and this realm's own DBC files (never downloaded).
if [ $PATCHZ = 1 ]; then
  echo "  [1] client data patch-Z.MPQ, built on this server (web service restart)"
  T1=1
  if [ $DRY = 0 ]; then
    bash "$REPO_DIR/hetzner/openvanilla_build_patchz.sh" --no-sync   # uses OW_REALM_DIR/OW_CP -> $CP/patch-Z.MPQ
    cp "$CP/patch-Z.MPQ" "$CLIENT_DATA/patch-Z.MPQ.new"
  fi
fi

# Server DBC: weapon skills for the new race/class pairs (idempotent; restart only if it changed).
if printf '%s\n' $CHANGED | grep -q 'fix_skillraceclassinfo.py\|classicplus_weapons.sql\|classicplus_races.sql'; then
  cp "$REPO_DIR/realm/classicplus/fix_skillraceclassinfo.py" "$REPO_DIR/realm/classicplus/classicplus_weapons.sql" "$CP/"
  if [ $DRY = 0 ]; then
    if bash "$REPO_DIR/hetzner/openvanilla_server_dbc.sh"; then T2=1; fi   # uses OW_REALM_DIR/OW_CP
  else echo "  [2] server SkillRaceClassInfo.dbc"; fi
fi

# Server model tables: ported models (tools/modelport). Idempotent; restart only if it changed.
if printf '%s\n' $CHANGED | grep -q 'classicplus_world_models.json\|apply_models_dbc.py'; then
  cp "$REPO_DIR/realm/classicplus/classicplus_world_models.json" "$REPO_DIR/realm/classicplus/apply_models_dbc.py" "$CP/"
  if [ $DRY = 0 ]; then
    if bash "$REPO_DIR/hetzner/openvanilla_server_models.sh"; then T2=1; fi   # uses OW_REALM_DIR/OW_CP
  else echo "  [2] server model tables"; fi
fi

# A newer realm image (engine patches) is a web-service restart too.
if [ $DRY = 0 ]; then
  OLD=$(docker inspect -f '{{.Image}}' "$(docker compose ps -q realm)" 2>/dev/null || true)
  docker compose pull -q realm >/dev/null 2>&1 || true
  NEW=$(docker image inspect -f '{{.Id}}' "$(docker compose config --images realm 2>/dev/null | head -1)" 2>/dev/null || true)
  if [ -n "$NEW" ] && [ "$OLD" != "$NEW" ]; then echo "  [1] new realm image"; T1=1; fi
fi
[ $DRY = 1 ] && { echo "(dry run: nothing changed)"; exit 0; }

# -- 2. SOAP for .reload and announcements -------------------------------------------------------
NET=$(docker inspect -f '{{range $k, $v := .NetworkSettings.Networks}}{{$k}} {{end}}' "$(docker compose ps -q mangosd)" | awk '{print $1}')
soap_account() {  # a GM 3 console account for this script, made once, password kept 0600
  [ -s "$CP/.hotpatch-soap" ] && return
  local pass; pass=$(head -c 24 /dev/urandom | base64 | tr -dc 'A-Za-z0-9' | head -c 16)
  read -r S V < <(python3 - "$pass" <<'PY'
import hashlib, os, sys
N = int("894B645E89E1535BBDAD5B8B290650530801B18EBFBF5E8FAB3C82872A3E9BB7", 16)
p = sys.argv[1]
salt = os.urandom(32)
h1 = hashlib.sha1(f"HOTPATCH:{p.upper()}".encode()).digest()
x = int.from_bytes(hashlib.sha1(salt[::-1] + h1).digest(), "little")
print(salt.hex().upper(), pow(7, x, N).to_bytes(32, "big").hex().upper())
PY
)
  compose_exec_sql classicrealmd -e "INSERT INTO account (username, gmlevel, v, s) VALUES ('HOTPATCH', 3, '$V', '$S')
    ON DUPLICATE KEY UPDATE gmlevel = 3, v = VALUES(v), s = VALUES(s)"
  umask 077; printf 'HOTPATCH:%s\n' "$pass" > "$CP/.hotpatch-soap"; rm -f "$CP/.hotpatch-curlrc"
}
soap() {  # soap "command" -> prints the console's answer
  soap_account
  local body="<?xml version=\"1.0\" encoding=\"utf-8\"?><SOAP-ENV:Envelope xmlns:SOAP-ENV=\"http://schemas.xmlsoap.org/soap/envelope/\" xmlns:ns1=\"urn:MaNGOS\"><SOAP-ENV:Body><ns1:executeCommand><command>$1</command></ns1:executeCommand></SOAP-ENV:Body></SOAP-ENV:Envelope>"
  # the credentials reach curl as a config file (-K), never on a command line other users can read
  [ -s "$CP/.hotpatch-curlrc" ] || (umask 077; printf 'user = "%s"\n' "$(cat "$CP/.hotpatch-soap")" > "$CP/.hotpatch-curlrc")
  docker run --rm --user 0:0 --network "$NET" -v "$CP/.hotpatch-curlrc:/auth:ro" curlimages/curl:8.10.1 -s -m 20 \
    -K /auth -H 'Content-Type: text/xml' -d "$body" http://mangosd:7878/ \
    | sed -n 's:.*<result>\(.*\)</result>.*:\1:p' | sed 's/&#xD;//g'
}
for cmd in "${SQL_RELOAD[@]}"; do echo "  .$cmd: $(soap ".$cmd" | head -c 200)"; done

online() { compose_exec_sql -N classiccharacters -e "SELECT COUNT(*) FROM characters WHERE online = 1" 2>/dev/null || echo 0; }

# -- 3. Tier 1: web service --------------------------------------------------------------------
if [ $T1 = 1 ]; then
  n=$(online)
  if [ "$n" != 0 ] && [ $FORCE_WEB = 0 ]; then
    soap ".announce Server note: the web client gets an update shortly; you may need to reconnect." >/dev/null || true
    say "$n player(s) online; waiting up to 30 min for an empty realm (or rerun with --force-web)"
    for i in $(seq 1 60); do sleep 30; n=$(online); [ "$n" = 0 ] && break; done
  fi
  [ -e "$CLIENT_DATA/patch-Z.MPQ.new" ] && mv "$CLIENT_DATA/patch-Z.MPQ.new" "$CLIENT_DATA/patch-Z.MPQ"
  docker compose up -d --no-deps --force-recreate realm
  # new patch-Z is open: tell service workers to refetch its files (keeps the operator's sw switch)
  SWMODE=$(python3 -c "import json;print(json.load(open('$CP/www/data-version.json')).get('sw','opt-in'))" 2>/dev/null || echo opt-in)
  printf '{"patchZ":"%s","sw":"%s"}\n' "$(sha256sum "$CP/patch-Z.MPQ" | cut -c1-16)" "$SWMODE" > "$CP/www/data-version.json"
  chmod 644 "$CP/www/data-version.json"
  say "web service restarted ($n online at the time)"
fi

# -- 4. Tier 2: world restart (queued unless asked) --------------------------------------------
[ $T2 = 1 ] && date -u +%FT%TZ > "$QUEUE"
if [ -e "$QUEUE" ]; then
  if [ $WORLD = 1 ]; then
    say "world restart: 5-minute countdown in game"
    soap ".server restart 300" || docker compose restart mangosd
    rm -f "$QUEUE"
  else
    say "a world restart is queued (since $(cat "$QUEUE")): rerun with --world-restart when it suits"
  fi
fi
echo "$HEAD" > "$STATE"
say "done"

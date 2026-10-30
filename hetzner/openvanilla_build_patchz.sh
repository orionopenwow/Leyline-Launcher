#!/usr/bin/env bash
# Build Classic+'s patch-Z.MPQ on the realm. The archive is not in git: it is made here from our own
# files (a sparse clone of the repo: Data/Interface, tools, realm/classicplus) plus two client tables
# (CharBaseInfo, SkillRaceClassInfo) made from THIS realm's own stock DBC files in its gamedata volume
# (the ".orig" copy first) and our row deltas (realm/classicplus/dbc_deltas, tools/classicplus_dbc.py).
#
#   bash openvanilla_build_patchz.sh              sync the repo to stable, then build -> $CP/patch-Z.MPQ
#   bash openvanilla_build_patchz.sh --no-sync    build from the repo as it is (openvanilla_hotpatch.sh)
#
# Called by openvanilla_realm_up.sh (step 2) and openvanilla_hotpatch.sh. The caller copies the result
# into the client data folder.
set -euo pipefail
REALM_DIR=${OW_REALM_DIR:-/opt/wenilla-realm}
CP=${OW_CP:-/opt/openvanilla-classicplus}
REPO_DIR=$CP/repo
REPO_URL=${OPENVANILLA_REPO:-https://github.com/orionopenwow/OpenVanilla}
SYNC=1
[ "${1:-}" = --no-sync ] && SYNC=0
export GIT_TERMINAL_PROMPT=0
SPARSE="realm/classicplus realm/www hetzner devkit/staging devkit/heraldlite Data/Interface tools"
if [ ! -d "$REPO_DIR/.git" ]; then
  git clone --depth 50 --filter=blob:none --sparse "$REPO_URL" "$REPO_DIR"
  SYNC=1
fi
# shellcheck disable=SC2086
git -C "$REPO_DIR" sparse-checkout set $SPARSE
if [ $SYNC = 1 ]; then
  git -C "$REPO_DIR" fetch --depth 50 -q origin "+refs/heads/stable:refs/remotes/origin/stable"
  git -C "$REPO_DIR" reset -q --hard origin/stable
fi

cd "$REALM_DIR"
PROJECT=${COMPOSE_PROJECT_NAME:-$(basename "$REALM_DIR")}
VOL=$(docker volume ls -q --filter "label=com.docker.compose.project=$PROJECT" --filter "label=com.docker.compose.volume=gamedata" | head -1)
[ -n "$VOL" ] || { echo "No gamedata volume found (was 'realmctl extract' run?)"; exit 2; }
STOCK=$CP/dbc/client-stock
rm -rf "$STOCK" && mkdir -p "$STOCK"
docker run --rm -v "$VOL":/data:ro -v "$STOCK":/out debian:bookworm-slim sh -c '
  for t in CharBaseInfo SkillRaceClassInfo; do
    f=$(ls /data/dbc | grep -i "^$t.dbc.orig$" | head -1)
    [ -n "$f" ] || f=$(ls /data/dbc | grep -i "^$t.dbc$" | head -1)
    [ -n "$f" ] || { echo "no $t.dbc in the gamedata volume"; exit 2; }
    cp "/data/dbc/$f" "/out/$t.dbc"
  done'
python3 "$REPO_DIR/tools/sync_patchz.py" --dbc-dir "$STOCK" --out "$CP/patch-Z.MPQ.built"
mv -f "$CP/patch-Z.MPQ.built" "$CP/patch-Z.MPQ"
rm -rf "$STOCK"
echo "patch-Z.MPQ built: $CP/patch-Z.MPQ"

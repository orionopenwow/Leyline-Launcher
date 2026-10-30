#!/usr/bin/env python3
"""Build realm/classicplus/patch-Z.MPQ from its sources. The archive is NOT in git (.gitignore): it is
made on the creator's PC or on the realm, from our files plus the creator's own game tables.

    python3 tools/sync_patchz.py --dbc-dir DIR    build it, with the Classic+ client tables
    python3 tools/sync_patchz.py                  build it without client tables (Interface only)
    python3 tools/sync_patchz.py --check [--dbc-dir DIR]   only report differences from the built file
    --out PATH                                    write somewhere else (default realm/classicplus/patch-Z.MPQ)
    PATCHZ_DBC_DIR=DIR                            same as --dbc-dir

Sources:
  Data/Interface/AddOns/<suite addon>/**   every folder whose .toc has "## X-ClassicPlus"
                                           (plus !Compat_112), as Interface\\AddOns\\...
  Data/Interface/ClassicPlus/*.blp         as Interface\\ClassicPlus\\...
  Data/Interface/ClassicPlus/LoadingScreens/*.blp   Open Vanilla's loading screens, as
                                           Interface\\Glues\\LoadingScreens\\... (tools/png_to_blp_dxt1.py)
  Data/Interface/ClassicPlus/Glues/**      Open Vanilla's glue art (the corner logo), as Interface\\Glues\\...
  Data/Creature/OpenVanilla/**             ported models (tools/modelport), as Creature\\OpenVanilla\\...
  --dbc-dir DIR                            DBFilesClient\\CharBaseInfo.dbc and SkillRaceClassInfo.dbc, made
                                           from the stock files in DIR (your own 1.12.1 client's, or the
                                           realm's <gamedata>/dbc) plus our row deltas (tools/classicplus_dbc.py)
Uses the model porter's pure-Python MPQ writer (no StormLib needed).
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MPQ = os.path.join(ROOT, "realm", "classicplus", "patch-Z.MPQ")
ADDONS = os.path.join(ROOT, "Data", "Interface", "AddOns")
CPART = os.path.join(ROOT, "Data", "Interface", "ClassicPlus")
TOOLS = os.path.join(ROOT, "tools")


# Text files go in with plain LF line endings, whatever the checkout used: on Windows git hands out
# CRLF (core.autocrlf), on Linux (CI) LF, and the archive must not depend on which one built it.
TEXT_EXT = (".toc", ".lua", ".xml", ".txt", ".md", ".json")


def source_bytes(path):
    data = open(path, "rb").read()
    return data.replace(b"\r\n", b"\n") if path.lower().endswith(TEXT_EXT) else data


def suite_folders():
    out = []
    for d in sorted(os.listdir(ADDONS)):
        toc = os.path.join(ADDONS, d, d + ".toc")
        if not os.path.isfile(toc):
            continue
        txt = open(toc, encoding="utf-8", errors="replace").read()
        if "## X-ClassicPlus" in txt or d.startswith("!Compat"):
            out.append(d)
    return out


# Only what the game loads: backups ("Plates.lua.before-pill", "*.bak", "*~") and editor
# litter stay out of the patch.
SHIPPED_EXT = (".lua", ".toc", ".xml", ".blp", ".tga", ".ttf", ".wav", ".mp3", ".ogg", ".txt", ".m2", ".skin")


def shipped(name):
    low = name.lower()
    return low.endswith(SHIPPED_EXT) and not low.startswith(".")


def wanted():
    """archive path (lower-case key) -> (archive path, source file)"""
    w = {}
    for d in suite_folders():
        base = os.path.join(ADDONS, d)
        for r, _, names in os.walk(base):
            for n in names:
                if not shipped(n):
                    continue
                full = os.path.join(r, n)
                arc = "Interface\\AddOns\\" + os.path.relpath(full, ADDONS).replace(os.sep, "\\")
                w[arc.lower()] = (arc, full)
    sys.path.insert(0, TOOLS)
    from modelport import content
    w.update(content.patch_files(ROOT))
    for n in sorted(os.listdir(CPART)):
        if n.lower().endswith(".blp"):
            arc = "Interface\\ClassicPlus\\" + n
            w[arc.lower()] = (arc, os.path.join(CPART, n))
    glues = os.path.join(CPART, "Glues")
    for r, _, names in os.walk(glues):
        for n in sorted(names):
            if n.lower().endswith(".blp"):
                full = os.path.join(r, n)
                arc = "Interface\\Glues\\" + os.path.relpath(full, glues).replace(os.sep, "\\")
                w[arc.lower()] = (arc, full)
    screens = os.path.join(CPART, "LoadingScreens")
    if os.path.isdir(screens):
        for n in sorted(os.listdir(screens)):
            if n.lower().endswith(".blp"):
                arc = "Interface\\Glues\\LoadingScreens\\" + n
                w[arc.lower()] = (arc, os.path.join(screens, n))
    return w


def arg(name):
    if name in sys.argv:
        i = sys.argv.index(name)
        if i + 1 < len(sys.argv):
            return sys.argv[i + 1]
    return None


def build_files(dbc_dir=None):
    """{archive name: bytes} for patch-Z: the sources, plus the client tables when dbc_dir is given."""
    files = {arc: source_bytes(full) for arc, full in wanted().values()}
    if dbc_dir:
        sys.path.insert(0, TOOLS)
        import classicplus_dbc
        for name, data in classicplus_dbc.build(dbc_dir).items():
            files["DBFilesClient\\" + name] = data
    return files


def main():
    check = "--check" in sys.argv
    dbc_dir = arg("--dbc-dir") or os.environ.get("PATCHZ_DBC_DIR") or None
    out = arg("--out") or MPQ
    sys.path.insert(0, TOOLS)
    from modelport import mpq
    try:
        files = build_files(dbc_dir)
    except FileNotFoundError as e:
        print(e)
        return 2
    if check:
        if not os.path.isfile(out):
            print(f"{os.path.relpath(out, ROOT)} isn't built yet (run tools/sync_patchz.py --dbc-dir DIR)")
            return 1
        a = mpq.Archive(out)
        have = {n: a.read(n) for n in a.names()}
        if not dbc_dir:   # without the creator's tables, compare everything else
            have = {n: d for n, d in have.items() if not n.lower().startswith("dbfilesclient\\")}
        diffs = sorted({n for n in set(have) | set(files) if have.get(n) != files.get(n)}, key=str.lower)
        for n in diffs:
            print(f"  {'add' if n not in have else 'remove' if n not in files else 'update':7} {n}")
        if not diffs:
            print("patch-Z.MPQ matches the source folders (nothing to do)")
            return 0
        print(f"{len(diffs)} difference(s); run without --check to rebuild")
        return 1
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    size = mpq.write(out, files)
    tables = sum(1 for n in files if n.lower().startswith("dbfilesclient\\"))
    print(f"patch-Z.MPQ built: {len(files)} files ({tables} client tables), {size} bytes -> {out}"
          + ("" if dbc_dir else "\n  (no --dbc-dir: built without the Classic+ client tables)"))
    return 0


if __name__ == "__main__":
    sys.exit(main())

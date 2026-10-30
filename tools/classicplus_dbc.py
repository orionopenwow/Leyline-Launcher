#!/usr/bin/env python3
"""Classic+ client tables for patch-Z, built from YOUR OWN 1.12.1 game files plus our row deltas.

No game file is kept in this repo. The two tables the Classic+ client needs are made here from the
creator's (or the realm's) own copies:

  DBFilesClient\\CharBaseInfo.dbc        your CharBaseInfo.dbc + the pairs in realm/classicplus/dbc_deltas/client_pairs.txt
  DBFilesClient\\SkillRaceClassInfo.dbc  your SkillRaceClassInfo.dbc + every new pair's class weapon skills
                                        (realm/classicplus/fix_skillraceclassinfo.py, classicplus_weapons.sql)

    python3 tools/classicplus_dbc.py --dbc-dir DIR --out OUTDIR [--verify]

DIR is a folder holding the stock DBC files of your own 1.12.1 client: the realm's extracted
<gamedata>/dbc folder (a "<name>.orig" copy is preferred: the realm keeps the stock file under that
name), or DBFilesClient\\ extracted from your client's dbc.MPQ. --verify compares the result with
realm/classicplus/dbc_deltas/expected.sha256 (the tables patch-Z shipped before 1.55.1) and exits 1 when
they differ. tools/sync_patchz.py --dbc-dir DIR calls this and puts the tables in patch-Z.MPQ.
"""
import argparse
import hashlib
import os
import re
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CP = os.path.join(ROOT, "realm", "classicplus")
DELTAS = os.path.join(CP, "dbc_deltas")
TABLES = ("CharBaseInfo.dbc", "SkillRaceClassInfo.dbc")
sys.path.insert(0, CP)
import fix_skillraceclassinfo as srci  # noqa: E402


def find_stock(dbc_dir, name):
    """DIR/<name>.orig, else DIR/<name> (any case). None when absent."""
    have = {n.lower(): n for n in os.listdir(dbc_dir)}
    for want in (name.lower() + ".orig", name.lower()):
        if want in have:
            return os.path.join(dbc_dir, have[want])
    return None


def read_pairs(path):
    with open(path, encoding="utf-8") as f:
        text = re.sub(r"#[^\n]*", "", f.read())
    return sorted({(int(r), int(c)) for r, c in re.findall(r"(\d+)\s+(\d+)", text)})


def char_base_info(stock_path, pairs):
    """CharBaseInfo.dbc bytes: the stock pairs plus ours, sorted by race then class."""
    stock = srci.read_combos(stock_path)
    rows = sorted(set(stock) | set(pairs))
    out = struct.pack("<4s4I", b"WDBC", len(rows), 2, 2, 1)
    return out + b"".join(struct.pack("<BB", r, c) for r, c in rows) + b"\0"


def skill_race_class_info(stock_path, pairs, sql_path):
    """SkillRaceClassInfo.dbc bytes: the stock rows with every pair's class weapon skills allowed."""
    rows, strings = srci.read_dbc(stock_path)
    srci.fix(rows, pairs, srci.class_skills(sql_path))
    out = struct.pack("<4s4I", b"WDBC", len(rows), 8, 32, len(strings))
    return out + b"".join(struct.pack("<8I", *r) for r in rows) + strings


def build(dbc_dir, sql_path=None):
    """{table name: bytes} from the stock files in dbc_dir. Raises FileNotFoundError when one is missing."""
    missing = [t for t in TABLES if not find_stock(dbc_dir, t)]
    if missing:
        raise FileNotFoundError(f"{dbc_dir}: no {', '.join(missing)} (your own 1.12.1 client's DBC files)")
    pairs = read_pairs(os.path.join(DELTAS, "client_pairs.txt"))
    srci_pairs = srci.read_combos(find_stock(dbc_dir, "CharBaseInfo.dbc"))
    cbi = char_base_info(find_stock(dbc_dir, "CharBaseInfo.dbc"), pairs)
    all_pairs = sorted(set(srci_pairs) | set(pairs))
    sk = skill_race_class_info(find_stock(dbc_dir, "SkillRaceClassInfo.dbc"), all_pairs,
                               sql_path or os.path.join(CP, "classicplus_weapons.sql"))
    return {"CharBaseInfo.dbc": cbi, "SkillRaceClassInfo.dbc": sk}


def expected():
    out = {}
    with open(os.path.join(DELTAS, "expected.sha256"), encoding="utf-8") as f:
        for line in f:
            parts = line.split()
            if len(parts) == 2:
                out[parts[1]] = parts[0]
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dbc-dir", required=True, help="the stock DBC files of your own 1.12.1 client")
    ap.add_argument("--out", required=True, help="folder to write the two tables into")
    ap.add_argument("--verify", action="store_true", help="compare with realm/classicplus/dbc_deltas/expected.sha256")
    a = ap.parse_args(argv)
    try:
        tables = build(a.dbc_dir)
    except FileNotFoundError as e:
        print(e)
        return 2
    os.makedirs(a.out, exist_ok=True)
    want, bad = expected(), 0
    for name, data in tables.items():
        with open(os.path.join(a.out, name), "wb") as f:
            f.write(data)
        h = hashlib.sha256(data).hexdigest()
        same = want.get(name) == h
        bad += a.verify and not same
        print(f"{name}: {len(data)} bytes sha256 {h}" + (" (matches the shipped table)" if same else ""))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())

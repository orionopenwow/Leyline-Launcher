"""
make_patch_w.py  (Open Vanilla / Warfront)

Warfront's client patch: patch-Z's sources (the Classic+ addons and art, tools/sync_patchz.py) without client tables,
so the character screen offers only the stock 1.12.1 race/class pairs and everything else in the
client is stock data. Warfront's world server runs a stock world database.

    python3 tools/warfront/make_patch_w.py
writes labs/openvanilla-realm/realm/warfront/patch-Z.MPQ (served as the browser client's patch-Z on the Warfront stack).
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "devkit"))
from mpqread import MPQ  # noqa: E402

OUT = os.path.join(ROOT, "labs", "openvanilla-realm", "realm", "warfront", "patch-Z.MPQ")


def main():
    # patch-Z's sources without the client tables (tools/sync_patchz.py; the Classic+ archive itself
    # is no longer in git, and its client tables are made from the creator's own files)
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import sync_patchz
    from modelport import mpq as pympq
    files = sync_patchz.build_files(None)
    kept, dropped = len(files), 0
    pympq.write(OUT, files)
    check = MPQ(OUT)
    names = check.names()
    assert not any(n.lower().startswith("dbfilesclient\\") for n in names), "a DBC slipped through"
    assert any(n.lower() == "interface\\addons\\warfront\\warfront.toc" for n in names), "no Warfront addon"
    print("%s: %d files (dropped %d DBFilesClient tables), %d bytes" % (OUT, kept, dropped, os.path.getsize(OUT)))


if __name__ == "__main__":
    main()

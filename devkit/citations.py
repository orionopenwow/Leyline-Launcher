"""Original-binary citations: addresses and symbols of the stock game client in text we write.

Our code and comments describe behaviour in plain words; they never cite the stock client's addresses
or internal symbols ("`CanTargetUnit 0x6e4440`", "`[0xcf0bc8]`", "CGGameUI::SetUIScale", "the reference's").

    python3 devkit/citations.py FILE...     list hits (patches: only the lines a patch adds)

devkit/check.py runs it over the repo ("no original-binary citations"). Lines a patch keeps as context or
removes are upstream's (wenilla) and are not ours to edit, so only "+" lines of a .patch are checked.
"""
import re
import sys

CITE = re.compile(
    r"`\[?0x[0-9a-fA-F]{6,8}\]?`"                                   # `0x689110`, `[0xbd0778]`
    r"|\[0x[0-9a-fA-F]{6,8}\]"                                      # [0xcf0bc8] (a read of a client global)
    r"|\b[A-Z][a-z0-9]+(?:_?[A-Z][a-z0-9]*)+\s+`?0x[0-9a-fA-F]{6,8}\b"   # CanTargetUnit 0x6e4440
    r"|\b(?:C(?!Str\b|String\b)[A-Z][A-Za-z0-9]*|[A-Z][A-Za-z0-9]*_C)::[A-Za-z_]\w*"   # CGGameUI::SetUIScale, CGUnit_C::
    r"|\bsub_[0-9A-Fa-f]{6,}\b"
    r"|(?i:\bthe reference(?:'s\b| client\b| binary\b| exe\b)|\bas the reference does\b)",
)


def hits_in_text(text):
    """[(line number, match, line)] for every citation in plain text."""
    out = []
    for n, line in enumerate(text.splitlines(), 1):
        for m in CITE.finditer(line):
            out.append((n, m.group(0), line.strip()))
    return out


def hits_in_patch(text):
    """Like hits_in_text, but only for the lines the patch adds."""
    out = []
    for n, line in enumerate(text.splitlines(), 1):
        if line.startswith("+") and not line.startswith("+++"):
            for m in CITE.finditer(line[1:]):
                out.append((n, m.group(0), line[1:].strip()))
    return out


def hits(path, text):
    return hits_in_patch(text) if path.endswith((".patch", ".diff")) else hits_in_text(text)


def main(paths):
    bad = 0
    for p in paths:
        with open(p, encoding="utf-8", errors="replace") as f:
            for n, m, line in hits(p, f.read()):
                bad += 1
                print(f"{p}:{n}: {m}  ::  {line[:160]}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

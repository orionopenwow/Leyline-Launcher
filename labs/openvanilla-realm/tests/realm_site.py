"""The 1.12 realm's website as Leyline Server serves it: www/ with the realm site's own pages
(labs/openvanilla-realm/site) in place of the public site's "moved" pages. Built in a temp folder from
symlinks, so nothing is copied but the archived pages."""
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
WWW = os.path.join(ROOT, "www")
SITE = os.path.join(ROOT, "labs", "openvanilla-realm", "site")
sys.path.insert(0, os.path.join(ROOT, "tests"))   # pagekit (HAVE_PW, serve), armory_fixture


def build(dest=None):
    """A folder that serves like the realm's site. Returns its path (the caller removes it)."""
    dest = dest or tempfile.mkdtemp(prefix="realm-site-")
    for name in os.listdir(WWW):
        os.symlink(os.path.join(WWW, name), os.path.join(dest, name))
    for d, _, files in os.walk(SITE):
        rel_dir = os.path.relpath(d, SITE)
        target_dir = dest if rel_dir == "." else os.path.join(dest, rel_dir)
        if os.path.islink(target_dir):   # a real folder of links, so the archived page can sit beside them
            src = os.readlink(target_dir)
            os.unlink(target_dir)
            os.makedirs(target_dir)
            for n in os.listdir(src):
                os.symlink(os.path.join(src, n), os.path.join(target_dir, n))
        for f in files:
            t = os.path.join(target_dir, f)
            if os.path.lexists(t):
                os.unlink(t)
            shutil.copy2(os.path.join(d, f), t)
    return dest

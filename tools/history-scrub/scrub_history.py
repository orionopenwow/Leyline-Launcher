#!/usr/bin/env python3
"""Scrub OpenVanilla's git history: game data and the old client-download links, in every commit and tag.

Run by "Scrub OpenVanilla history.bat" (Windows) or directly:

    python3 scrub_history.py --work DIR                 clone, scrub, verify, then ask before force-pushing
    python3 scrub_history.py --work DIR --dry-run       everything except the push
    --source URL_OR_PATH    what to mirror-clone (default: the GitHub repo)

What it removes (the lists below are the whole job; nothing else is touched):
  * PATHS: files dropped from every commit (git filter-repo --invert-paths).
  * REPLACE: text replaced in every file of every commit (git filter-repo --replace-text): the full-client
    download links and the download site's name. The code that used them stays in old commits, link-free.
Commits that only touched a removed file become empty and are dropped by git filter-repo.

Before anything is pushed it proves:
  1. no commit holds a PATHS file, and no file in any commit matches a REPLACE pattern;
  2. main's tree is unchanged by the scrub (main already carries the tip changes: merge
     legal-cleanup-20261029 first); every other branch and tag changes only by the PATHS files and the
     REPLACE lines;
then prints every ref it will force-push, and pushes only after you type SCRUB.
It pushes branches and tags to github.com/orionopenwow/OpenVanilla as the GitHub user orionopenwow.
Standard library only (plus git and git-filter-repo).
"""
import argparse
import os
import re
import shutil
import subprocess
import sys

REPO_URL = "https://github.com/orionopenwow/OpenVanilla.git"
PUSH_URL = "https://orionopenwow@github.com/orionopenwow/OpenVanilla.git"   # the credential for this user only
PUSH_USER = "orionopenwow"
AUTHOR = ("Orion", "orionopenwow@users.noreply.github.com")

PATHS = [
    "realm/classicplus/patch-Z.MPQ",   # held whole CharBaseInfo.dbc and SkillRaceClassInfo.dbc (all 59 versions)
]
# (pattern, replacement); "regex:" patterns are Python regexes. The names are split so this file never
# matches its own patterns (it lives in the tree the scrub checks).
_AO = "arch" + "ive"
_NW = "nostal" + "rius-wow-classic"
REPLACE = [   # all regexes, applied in this order
    ("regex:https?://(?:www\\.)?" + _AO + "\\.org/(?:details|download|metadata)/" + _NW + "[^\\s\"'<>)\\]`}]*",
     "https://removed.invalid/"),
    ("regex:https://" + _AO + "\\.org/metadata/", "https://removed.invalid/metadata/"),
    ("regex:https://" + _AO + "\\.org/download/x/x\\.zip", "https://example.org/x/x.zip"),
    ("regex:openvanilla\\.app/downloads/WoW-[0-9.a-zA-Z]+-EnUS-Client\\.zip", "removed.invalid/client.zip"),
    ("regex:" + _AO + "\\\\\\.org", "removed\\\\.invalid"),          # the escaped form in code regexes
    ("regex:" + _AO + "\\.org", "removed.invalid"),
    ("regex:" + _NW, "removed-client"),
    ("regex:Internet " + _AO.capitalize(), "download site"),
]
# What must be gone afterwards (checked in every commit).
GONE = re.compile(_AO + r"\\?\.org|" + _NW + "|Internet " + _AO.capitalize()
                  + r"|WoW-[0-9.]+[a-z]?-EnUS-Client\.zip")


def run(*cmd, cwd=None, check=True):
    r = subprocess.run(list(cmd), cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if check and r.returncode:
        sys.exit(f"!! {' '.join(cmd)} failed:\n{r.stdout}{r.stderr}")
    return r.stdout


def git(repo, *a, check=True):
    return run("git", "-C", repo, *a, check=check)


def refs(repo):
    out = {}
    for line in git(repo, "for-each-ref", "--format=%(refname) %(objectname) %(objecttype)",
                    "refs/heads", "refs/tags").splitlines():
        name, sha, kind = line.split()
        out[name] = (sha, kind)
    return out


def tree_of(repo, ref):
    return git(repo, "rev-parse", f"{ref}^{{tree}}").strip()


def count_commits(repo):
    return int(git(repo, "rev-list", "--all", "--count").strip() or 0)


def filter_repo_cmd():
    for cmd in (["git", "filter-repo"], [sys.executable, "-m", "git_filter_repo"]):
        if subprocess.run(cmd + ["--version"], capture_output=True).returncode == 0:
            return cmd
    sys.exit("!! git-filter-repo is missing: run  py -3 -m pip install --user git-filter-repo")


def scrub(work, source):
    before, after = os.path.join(work, "before.git"), os.path.join(work, "after.git")
    for d in (before, after):
        if os.path.exists(d):
            shutil.rmtree(d)
    print(f"== 1. Mirror clone of {source}")
    run("git", "clone", "--quiet", "--mirror", source, before)
    git(before, "config", "user.name", AUTHOR[0])
    git(before, "config", "user.email", AUTHOR[1])
    run("git", "clone", "--quiet", "--mirror", before, after)
    git(after, "config", "user.name", AUTHOR[0])
    git(after, "config", "user.email", AUTHOR[1])
    for ref in [r for r in refs(after) if not r.startswith(("refs/heads/", "refs/tags/"))]:
        git(after, "update-ref", "-d", ref)
    rules = os.path.join(work, "replace-rules.txt")
    with open(rules, "w", encoding="utf-8", newline="\n") as f:
        for pat, rep in REPLACE:
            f.write(f"{pat}==>{rep}\n")
    print(f"== 2. git filter-repo: {len(PATHS)} path(s) out of every commit, {len(REPLACE)} text rule(s)")
    cmd = filter_repo_cmd() + ["--force", "--invert-paths", "--replace-text", rules]
    for p in PATHS:
        cmd += ["--path", p]
    r = subprocess.run(cmd, cwd=after, capture_output=True, text=True)
    if r.returncode:
        sys.exit("!! git filter-repo failed:\n" + r.stdout + r.stderr)
    return before, after


def allowed_diff(before, after, old_ref, new_ref):
    """Differences between the two trees that are not a PATHS removal or a REPLACE line. [] = only allowed ones."""
    bad = []
    old_t, new_t = tree_of(before, old_ref), tree_of(after, new_ref)
    if old_t == new_t:
        return bad
    # the trees live in different repos: compare file lists and blob ids, then the changed blobs' lines
    def ls(repo, ref):
        out = {}
        for line in git(repo, "ls-tree", "-r", "--full-tree", ref).splitlines():
            meta, path = line.split("\t", 1)
            out[path] = meta.split()[2]
        return out
    a, b = ls(before, old_ref), ls(after, new_ref)
    for path in sorted(set(a) | set(b)):
        if a.get(path) == b.get(path):
            continue
        if path not in b and path in PATHS:
            continue
        if path not in a or path not in b:
            bad.append(f"{path}: {'added' if path not in a else 'removed'}")
            continue
        old_lines = git(before, "cat-file", "blob", a[path], check=False).split("\n")
        new_lines = git(after, "cat-file", "blob", b[path], check=False).split("\n")
        if len(old_lines) != len(new_lines):
            bad.append(f"{path}: line count changed")
            continue
        for o, n in zip(old_lines, new_lines):
            if o != n and not GONE.search(o):
                bad.append(f"{path}: changed a line without a scrub pattern: {o[:80]}")
                break
    return bad


def verify(before, after):
    print("== 3. Verify")
    ok = True
    commits = git(after, "rev-list", "--all").split()
    left = git(after, "log", "--all", "--format=%H", "--", *PATHS).split()
    print(f"   {', '.join(PATHS)}: in {len(left)} commit(s) after the scrub (must be 0)")
    ok &= not left
    hits = []
    for i in range(0, len(commits), 50):
        out = git(after, "grep", "-I", "-l", "-E", GONE.pattern, *commits[i:i + 50], check=False)
        hits += out.split()
    print(f"   download links / site name: in {len(hits)} file version(s) after the scrub (must be 0)")
    for h in hits[:10]:
        print("     ", h)
    ok &= not hits
    old, new = refs(before), refs(after)
    lost = sorted(set(old) - set(new))
    print(f"   refs: {len(old)} before, {len(new)} after" + (f"; MISSING: {', '.join(lost)}" if lost else ""))
    ok &= not lost
    main = "refs/heads/main"
    if main in old:
        same = tree_of(before, main) == tree_of(after, main)
        print(f"   main's tree unchanged by the scrub: {'yes' if same else 'NO (merge legal-cleanup-20261029 first)'}")
        ok &= same
    for ref in sorted(new):
        bad = allowed_diff(before, after, ref, ref)
        if bad:
            ok = False
            print(f"   {ref}: UNEXPECTED changes:")
            for b in bad[:5]:
                print("     ", b)
    print(f"   every other branch and tag changes only by the scrubbed file and lines: {'yes' if ok else 'see above'}")
    print(f"   commits: {count_commits(before)} before, {count_commits(after)} after")
    return ok


def push_plan(before, after):
    old, new = refs(before), refs(after)
    print("== 4. This will force-push to " + REPO_URL + " as GitHub user " + PUSH_USER + ":")
    for ref in sorted(new):
        o = old.get(ref, ("-",))[0][:8]
        print(f"   {ref:32} {o} -> {new[ref][0][:8]}{'' if o != new[ref][0][:8] else '  (unchanged)'}")


def check_push_user():
    """Refuse to push as anyone but orionopenwow when the GitHub CLI can tell who is signed in."""
    if shutil.which("gh"):
        r = subprocess.run(["gh", "api", "user", "--jq", ".login"], capture_output=True, text=True)
        login = r.stdout.strip()
        if r.returncode == 0 and login and login.lower() != PUSH_USER:
            sys.exit(f"!! The GitHub CLI is signed in as {login}, not {PUSH_USER}. Sign in as {PUSH_USER} "
                     f"(gh auth login, and in Git Credential Manager) and run this again. Nothing was pushed.")
        if login:
            print(f"   GitHub CLI account: {login}")


def push(after):
    git(after, "config", "user.name", AUTHOR[0])
    git(after, "config", "user.email", AUTHOR[1])
    for what in ("--all", "--tags"):
        r = subprocess.run(["git", "-C", after, "-c", "credential.username=" + PUSH_USER, "push", "--force",
                            what, PUSH_URL], text=True)
        if r.returncode:
            sys.exit("!! The push failed (see above). Branch protection on main/stable must allow force pushes.")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--work", required=True)
    ap.add_argument("--source", default=REPO_URL)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    os.makedirs(a.work, exist_ok=True)
    before, after = scrub(a.work, a.source)
    if not verify(before, after):
        print("!! Verification failed: nothing was pushed.")
        return 1
    push_plan(before, after)
    if a.dry_run:
        print("(dry run: nothing was pushed)")
        return 0
    check_push_user()
    if input("Type SCRUB to force-push these refs (anything else stops): ").strip() != "SCRUB":
        print("Stopped. Nothing was pushed.")
        return 1
    push(after)
    print("Pushed.")
    print("Reminder: forks and existing clones still hold the old history, and GitHub can keep cached views")
    print("(old commit pages, pull-request diffs) until GitHub Support removes them: ask them to run a")
    print("garbage collection on orionopenwow/OpenVanilla and to purge cached views of the removed file.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

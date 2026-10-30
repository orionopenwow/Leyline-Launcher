"""labs/openvanilla-realm/tools/stop-112-jobs.sh and start-112-jobs.sh against fake crontab, systemctl,
docker and id: which lines, units and containers count as 1.12 jobs, that the dry run changes nothing,
and that --go then the undo puts everything back.

    python3 -m pytest -q labs/openvanilla-realm/tests/test_stop_112_jobs.py
"""
import os
import shutil
import subprocess
import tempfile
import textwrap
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.join(os.path.dirname(HERE), "tools")
STOP = os.path.join(TOOLS, "stop-112-jobs.sh")
START = os.path.join(TOOLS, "start-112-jobs.sh")

CRONTAB = textwrap.dedent("""\
    # m h dom mon dow command
    SHELL=/bin/bash
    MAILTO=""
    0 4 * * * /opt/openvanilla/backup_cron.sh >> /var/log/openvanilla-backup.log 2>&1
    */10 * * * * bash /opt/openvanilla-herald/armory_cron.sh
    */5 * * * * bash /root/streams_cron.sh >/dev/null 2>&1
    30 3 * * * cd /opt/wenilla-duels && docker compose restart mangosd
    15 * * * * /usr/bin/python3 /root/hetzner/bug_digest.sh
    0 5 * * * /opt/wu-discord/backup.sh
    */2 * * * * /srv/wrath/stream/server/fastloop.sh
    0 6 * * * cd /opt/wenilla-realm && docker compose exec -T caddy caddy reload --config /etc/caddy/Caddyfile
    0 2 * * * /opt/leyline/hangout/nightly.sh
    20 * * * * /opt/wu-relay/rotate.sh
    0 1 * * 0 /usr/bin/certbot renew
    @reboot /usr/local/bin/portal-up.sh
    0 0 * * * /root/openvanilla-hangout-sync.sh
""")
OFF_LINES = {
    "0 4 * * * /opt/openvanilla/backup_cron.sh >> /var/log/openvanilla-backup.log 2>&1",
    "*/10 * * * * bash /opt/openvanilla-herald/armory_cron.sh",
    "*/5 * * * * bash /root/streams_cron.sh >/dev/null 2>&1",
    "30 3 * * * cd /opt/wenilla-duels && docker compose restart mangosd",
    "15 * * * * /usr/bin/python3 /root/hetzner/bug_digest.sh",
}

UNITS = {   # name -> (is-enabled, is-active)
    "openvanilla-armory.timer": ("enabled", "active"),
    "openvanilla-armory.service": ("static", "inactive"),
    "openvanilla-streams.timer": ("enabled", "active"),
    "openvanilla-herald.service": ("enabled", "active"),
    "openvanilla-herald-autopilot.service": ("enabled", "active"),
    "openvanilla-warfront-live.timer": ("disabled", "inactive"),
    "openvanilla-binfmt.service": ("enabled", "inactive"),
    "openvanilla-relay.service": ("enabled", "active"),
    "openwow-herald.service": ("enabled", "inactive"),
    "wu-discord.service": ("enabled", "active"),
    "wu-backup.timer": ("enabled", "active"),
}
CONTAINERS = [   # name|project|service, restart policy, running
    ("wenilla-realm-mangosd-1|wenilla-realm|mangosd", "unless-stopped", "true"),
    ("wenilla-realm-realmd-1|wenilla-realm|realmd", "unless-stopped", "true"),
    ("wenilla-realm-realm-1|wenilla-realm|realm", "unless-stopped", "true"),
    ("wenilla-realm-caddy-1|wenilla-realm|caddy", "unless-stopped", "true"),
    ("wenilla-realm-mariadb-1|wenilla-realm|mariadb", "unless-stopped", "true"),
    ("owduels-mangosd-1|owduels|mangosd", "unless-stopped", "false"),
    ("openvanilla-support-mariadb||", "unless-stopped", "true"),
    ("openvanilla-relay-relay-1|openvanilla-relay|relay", "unless-stopped", "true"),
    ("wu-relay|wu-relay|relay", "always", "true"),
    ("leyline-hangout-1|leyline|hangout", "always", "true"),
]

FAKES = {
    "id": 'echo 0\n',
    "crontab": textwrap.dedent('''\
        if [ "$1" = -l ]; then [ -f "$FAKE/crontab.txt" ] && cat "$FAKE/crontab.txt" || exit 1
        else cp "$1" "$FAKE/crontab.txt"; echo "crontab $1" >> "$FAKE/calls"; fi
    '''),
    "systemctl": textwrap.dedent('''\
        case "$1" in
          list-unit-files) awk '{print $1, $2}' "$FAKE/units.txt";;
          is-enabled) awk -v u="$2" '$1==u {print $2}' "$FAKE/units.txt";;
          is-active) awk -v u="$2" '$1==u {print $3}' "$FAKE/units.txt";;
          show) echo "$FAKE/unitfiles/$5";;   # show -p FragmentPath --value UNIT
          *) echo "systemctl $*" >> "$FAKE/calls";;
        esac
    '''),
    "docker": textwrap.dedent('''\
        case "$1" in
          ps) cut -d' ' -f1 "$FAKE/containers.txt";;
          inspect) n=$4; line=$(grep "^$n|" "$FAKE/containers.txt")
                   case "$3" in *RestartPolicy*) echo "$line" | cut -d' ' -f2;; *) echo "$line" | cut -d' ' -f3;; esac;;
          *) echo "docker $*" >> "$FAKE/calls";;
        esac
    '''),
}


def sh(script, *args, env=None):
    return subprocess.run(["bash", script, *args], capture_output=True, text=True, env=env, timeout=60)


class Classify(unittest.TestCase):
    def test_crontab_lines(self):
        r = subprocess.run(["bash", STOP, "--classify-cron"], input=CRONTAB, capture_output=True, text=True, timeout=30)
        self.assertEqual(r.returncode, 0, r.stderr)
        got = {}
        for out in r.stdout.splitlines():
            tag, _, line = out.partition(" ")
            got[line] = tag
        self.assertEqual(len(got), len(CRONTAB.splitlines()))
        for line, tag in got.items():
            self.assertEqual(tag, "OFF" if line in OFF_LINES else "KEEP", line)

    def test_units(self):
        for u, want in (("openvanilla-armory.timer", "OFF"), ("openvanilla-streams.service", "OFF"),
                        ("openvanilla-herald-autopilot.service", "OFF"), ("openwow-herald.service", "OFF"),
                        ("openvanilla-binfmt.service", "KEEP"), ("openvanilla-relay.service", "KEEP"),
                        ("wu-discord.service", "KEEP"), ("leyline-hangout.service", "KEEP"), ("caddy.service", "KEEP"),
                        ("openvanilla-wrath-bridge.service", "KEEP"), ("sshd.service", "KEEP")):
            self.assertEqual(sh(STOP, "--classify-unit", u).stdout.strip(), want, u)

    def test_containers(self):
        for name, proj, svc, want in (("wenilla-realm-mangosd-1", "wenilla-realm", "mangosd", "OFF"),
                                      ("wenilla-realm-realmd-1", "wenilla-realm", "realmd", "OFF"),
                                      ("wenilla-realm-realm-1", "wenilla-realm", "realm", "KEEP"),
                                      ("wenilla-realm-caddy-1", "wenilla-realm", "caddy", "KEEP"),
                                      ("wenilla-realm-mariadb-1", "wenilla-realm", "mariadb", "KEEP"),
                                      ("owduels-realm-1", "owduels", "realm", "OFF"),
                                      ("wenilla-warfront-mangosd-1", "wenilla-warfront", "mangosd", "OFF"),
                                      ("openvanilla-support-mangosd", "", "", "OFF"),
                                      ("openvanilla-relay-relay-1", "openvanilla-relay", "relay", "KEEP"),
                                      ("wu-relay", "wu-relay", "relay", "KEEP"),
                                      ("leyline-portal-1", "leyline", "portal", "KEEP"),
                                      ("tc-worldserver-1", "tc", "worldserver", "KEEP")):
            self.assertEqual(sh(STOP, "--classify-container", name, proj, svc).stdout.strip(), want, name)


class EndToEnd(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ov112-")
        self.fake = os.path.join(self.tmp, "fake")
        bindir = os.path.join(self.tmp, "bin")
        os.makedirs(os.path.join(self.fake, "unitfiles"))
        os.makedirs(bindir)
        for name, body in FAKES.items():
            p = os.path.join(bindir, name)
            with open(p, "w") as f:
                f.write("#!/bin/bash\n" + body)
            os.chmod(p, 0o755)
        self.write("crontab.txt", CRONTAB)
        self.write("units.txt", "".join(f"{u} {e} {a}\n" for u, (e, a) in UNITS.items()))
        for u in UNITS:
            self.write(os.path.join("unitfiles", u), f"[Unit]\nDescription={u}\n")
        self.write("containers.txt", "".join(f"{c} {p} {r}\n" for c, p, r in CONTAINERS))
        self.env = dict(os.environ, PATH=bindir + os.pathsep + os.environ["PATH"], FAKE=self.fake,
                        OV112_BACKUP_ROOT=os.path.join(self.tmp, "root"))
        os.makedirs(self.env["OV112_BACKUP_ROOT"])

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def write(self, rel, text):
        with open(os.path.join(self.fake, rel), "w") as f:
            f.write(text)

    def read(self, rel):
        p = os.path.join(self.fake, rel)
        return open(p).read() if os.path.exists(p) else ""

    def test_dry_run_changes_nothing(self):
        r = sh(STOP, env=self.env)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("OV112 DRY", r.stdout)
        self.assertEqual(self.read("calls"), "")
        self.assertEqual(self.read("crontab.txt"), CRONTAB)
        self.assertEqual(os.listdir(self.env["OV112_BACKUP_ROOT"]), [])
        for line in OFF_LINES:
            self.assertIn("off: " + line, r.stdout)
        self.assertIn("off: openvanilla-herald.service", r.stdout)
        self.assertNotIn("wu-discord", r.stdout)   # only openvanilla-*/openwow-* units are even looked at
        self.assertIn("keep: openvanilla-binfmt.service", r.stdout)
        self.assertIn("keep: wenilla-realm-caddy-1", r.stdout)

    def test_go_then_undo(self):
        r = sh(STOP, "--go", env=self.env)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("OV112 OFF", r.stdout)
        kept = [l for l in CRONTAB.splitlines() if l not in OFF_LINES]
        self.assertEqual(self.read("crontab.txt").splitlines(), kept)
        calls = self.read("calls").splitlines()
        disabled = [c.split()[-1] for c in calls if c.startswith("systemctl disable --now")]
        self.assertEqual(sorted(disabled), sorted(["openvanilla-armory.timer", "openvanilla-streams.timer",
                                                   "openvanilla-herald.service", "openvanilla-herald-autopilot.service",
                                                   "openwow-herald.service"]))
        self.assertLess(calls.index("systemctl disable --now openvanilla-armory.timer"),
                        calls.index("systemctl disable --now openvanilla-herald.service"), "timers first")
        updated = sorted(c.split()[-1] for c in calls if c.startswith("docker update --restart=no"))
        self.assertEqual(updated, sorted(["wenilla-realm-mangosd-1", "wenilla-realm-realmd-1", "owduels-mangosd-1",
                                          "openvanilla-support-mariadb"]))
        stopped = sorted(c.split()[-1] for c in calls if c.startswith("docker stop"))
        self.assertEqual(stopped, sorted(["wenilla-realm-mangosd-1", "wenilla-realm-realmd-1", "openvanilla-support-mariadb"]))
        for c in calls:
            self.assertNotRegex(c, r"wu-|leyline|hangout|relay|caddy|wenilla-realm-realm-1|mariadb-1|binfmt", c)
        (backup,) = os.listdir(self.env["OV112_BACKUP_ROOT"])
        b = os.path.join(self.env["OV112_BACKUP_ROOT"], backup)
        self.assertEqual(open(os.path.join(b, "crontab.before")).read(), CRONTAB)
        self.assertIn("openvanilla-herald.service", os.listdir(os.path.join(b, "units")))

        # the undo: dry run first changes nothing, then --go puts it back
        open(os.path.join(self.fake, "calls"), "w").close()
        r = sh(START, env=self.env)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(self.read("calls"), "")
        r = sh(START, "--go", env=self.env)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("OV112 ON", r.stdout)
        self.assertEqual(sorted(self.read("crontab.txt").splitlines()), sorted(CRONTAB.splitlines()))
        calls = self.read("calls").splitlines()
        self.assertIn("systemctl enable openvanilla-herald.service", calls)
        self.assertIn("systemctl start openvanilla-armory.timer", calls)
        self.assertNotIn("systemctl enable openvanilla-armory.service", calls)   # it was static
        self.assertIn("docker update --restart=unless-stopped wenilla-realm-mangosd-1", calls)
        self.assertIn("docker start openvanilla-support-mariadb", calls)
        self.assertNotIn("docker start owduels-mangosd-1", calls)   # it was not running


if __name__ == "__main__":
    unittest.main()

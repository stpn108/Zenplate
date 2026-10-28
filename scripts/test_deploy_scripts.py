#!/usr/bin/env python3
"""Tests for redeploy.sh's terminal detach (T-011), .env guard (T-012), --no-cache (T-013) and four test
workers (T-014), and merge-to-main.sh's guards (T-010).

The deploy scripts live outside app/, so the app-tests container and ci.yml cannot see them.
Run on the host from the repo root (needs bash, git, flock, setsid, GNU tail):

    python3 scripts/test_deploy_scripts.py

redeploy.sh runs for real under a pseudo-terminal, with a fake `docker` on PATH; Ctrl-C is
sent as the terminal's ^C. merge-to-main.sh runs against throwaway git repos with a local origin.
Exit code 0 = all checks passed.
"""
import os
import pty
import re
import select
import signal
import subprocess
import sys
import tempfile
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = []


def check(name, ok, detail=""):
    RESULTS.append(ok)
    print(("PASS " if ok else "FAIL ") + name + ("" if ok else f"  | {detail}"))


# ---------------------------------------------------------------- redeploy.sh

# Stands in for `docker` and `docker compose`: the app is healthy at once and runs FAKE_COMMIT;
# `logs -f` prints LOGLINE until it is killed. A build of the service named in FAKE_BUILD_FAIL fails.
# Every compose call is appended to FAKE_COMPOSE_LOG when that is set.
FAKE_DOCKER = r"""#!/bin/bash
if [ "$1" = "compose" ]; then
    shift
    [ -n "${FAKE_COMPOSE_LOG:-}" ] && echo "$*" >> "$FAKE_COMPOSE_LOG"
    case "$1" in
        run)   sleep "${FAKE_TEST_SLEEP:-0}"; exit "${FAKE_TEST_EXIT:-0}" ;;
        build) sleep "${FAKE_BUILD_SLEEP:-0}"
               [ -n "${FAKE_BUILD_FAIL:-}" ] && [ "${!#}" = "$FAKE_BUILD_FAIL" ] && exit 1
               exit 0 ;;
        ps)    echo healthy; exit 0 ;;
        exec)  echo "$FAKE_COMMIT"; exit 0 ;;
        logs)  [ "$2" = "-f" ] || exit 0
               while true; do echo LOGLINE; sleep 0.2; done ;;
    esac
    exit 0
fi
exit 0
"""


# A deploy .env as the guard (T-012) reads it: a comment, a CRLF line, quotes, `export`, an inline comment.
GUARD_ENV = ("# staging\nZT_GUARD_PREFIX=9\r\nZT_GUARD_SECRET=\"s3cr3t\"\nexport ZT_GUARD_SINGLE='a b'\n"
             "ZT_GUARD_UNSET=x\nZT_GUARD_COMMENT=10                 # Host port prefix\n")
REQUIREMENTS = "pytest\n"


def make_deploy_dir(base, tested_requirements=True):
    """A git checkout holding the real redeploy.sh, plus a fake docker on PATH. With
    tested_requirements, app-tests counts as built for the current requirements.txt."""
    d = tempfile.mkdtemp(dir=base)
    with open(os.path.join(REPO, "redeploy.sh")) as src, open(os.path.join(d, "redeploy.sh"), "w") as dst:
        dst.write(src.read())
    os.chmod(os.path.join(d, "redeploy.sh"), 0o755)
    open(os.path.join(d, "VERSION"), "w").write("1.0\n")
    os.makedirs(os.path.join(d, "app"))
    open(os.path.join(d, "app", "requirements.txt"), "w").write(REQUIREMENTS)
    if tested_requirements:
        md5 = subprocess.run(["md5sum", "app/requirements.txt"], cwd=d, capture_output=True, text=True).stdout
        open(os.path.join(d, "app", ".requirements_hash"), "w").write(md5.split()[0] + "\n")
    git(d, "init", "-q")
    git(d, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "--allow-empty", "-m", "deploy me")
    bindir = os.path.join(d, "fakebin")
    os.makedirs(bindir)
    with open(os.path.join(bindir, "docker"), "w") as f:
        f.write(FAKE_DOCKER)
    os.chmod(os.path.join(bindir, "docker"), 0o755)
    env = {"PATH": bindir + os.pathsep + os.environ["PATH"],
           "FAKE_COMMIT": git(d, "rev-parse", "--short", "HEAD").stdout.strip()}
    return d, env


def run_tty(d, env, action=None, when=None, script="./redeploy.sh", timeout=30):
    """Run the script under a pseudo-terminal. `action` ("ctrl-c" or "hangup") fires once
    `when` (a text) shows up in the output, or after `when` seconds."""
    pid, fd = pty.fork()
    if pid == 0:
        os.chdir(d)
        os.execve("/bin/bash", ["bash", script], dict(os.environ, **env))
    out, start, acted = b"", time.time(), False
    while time.time() - start < timeout:
        due = isinstance(when, str) and when in out.decode(errors="replace") or \
            isinstance(when, (int, float)) and time.time() - start > when
        if action and not acted and due:
            acted = True
            if action == "hangup":
                os.close(fd)  # the terminal goes away, like a dropped SSH session
                fd = None
            else:
                os.write(fd, b"\x03")  # Ctrl-C: SIGINT to the terminal's foreground group
        if fd is None:
            break
        if not select.select([fd], [], [], 0.1)[0]:
            continue
        try:
            chunk = os.read(fd, 4096)
        except OSError:
            break
        if not chunk:
            break
        out += chunk
    else:
        os.kill(pid, signal.SIGKILL)
    _, status = os.waitpid(pid, 0)
    return os.waitstatus_to_exitcode(status), out.decode(errors="replace")


def run_inline(d, env, *args):
    """Run the script without a terminal, as the deploy pipeline does."""
    return subprocess.run(["bash", "./redeploy.sh", *args], cwd=d, capture_output=True, text=True, timeout=30,
                          env=dict(os.environ, **env))


def deploy_log(d):
    path = os.path.join(d, "redeploy.log")
    return open(path).read() if os.path.exists(path) else None


def wait_for_log(d, marker, timeout=20):
    start = time.time()
    while time.time() - start < timeout:
        if marker in (deploy_log(d) or ""):
            break
        time.sleep(0.2)
    return deploy_log(d) or ""


def lock_free(d):
    lock = f"/tmp/{os.path.basename(d)}-redeploy.lock"
    return subprocess.run(["flock", "-n", lock, "true"]).returncode == 0


def compose_calls(d, env, *args):
    calls = os.path.join(d, "compose-calls")
    p = run_inline(d, dict(env, FAKE_COMPOSE_LOG=calls), *args)
    return p, open(calls).read().splitlines() if os.path.exists(calls) else []


DONE = "app is healthy."


def test_redeploy(base):
    d, env = make_deploy_dir(base)
    code, out = run_tty(d, env, action="ctrl-c", when="LOGLINE")
    log = deploy_log(d)
    check("redeploy: success, then Ctrl-C only stops watching the logs",
          code == 0 and DONE in out and "LOGLINE" in out and "aborting the deploy" not in out
          and "[redeploy exit 0]" in log and "LOGLINE" not in log and lock_free(d), f"{code} {out[-400:]}")

    d, env = make_deploy_dir(base)
    run_tty(d, env, action="hangup", when="LOGLINE")
    time.sleep(1)
    size = len(deploy_log(d))
    time.sleep(1)
    check("redeploy: dropped session while watching logs leaves nothing running",
          lock_free(d) and len(deploy_log(d)) == size and "[redeploy exit 0]" in deploy_log(d), deploy_log(d)[-300:])

    d, env = make_deploy_dir(base)
    start = time.time()
    run_tty(d, dict(env, FAKE_BUILD_SLEEP="3"), action="hangup", when=1.0)
    viewer_gone, at_hangup = time.time() - start, deploy_log(d) or ""
    final = wait_for_log(d, "[redeploy exit")
    check("redeploy: dropped session during the deploy does not stop it",
          viewer_gone < 2.5 and DONE not in at_hangup and DONE in final
          and "[redeploy exit 0]" in final and "LOGLINE" not in final, f"{viewer_gone:.1f}s {final[-400:]!r}")

    d, env = make_deploy_dir(base)
    code, out = run_tty(d, dict(env, FAKE_BUILD_SLEEP="5"), action="ctrl-c", when=1.0)
    final = wait_for_log(d, "[redeploy exit")
    check("redeploy: Ctrl-C during the deploy aborts it with 130",
          code == 130 and "Aborted by Ctrl-C." in final and "[redeploy exit 130]" in final
          and DONE not in final and lock_free(d), f"{code} {final[-400:]!r}")

    d, env = make_deploy_dir(base)
    code, out = run_tty(d, dict(env, FAKE_TEST_EXIT="1"))
    check("redeploy: failing tests stop it, no log following", code == 1 and "LOGLINE" not in out
          and DONE not in out and "TESTS FAILED" in out, f"{code} {out[-400:]}")

    d, env = make_deploy_dir(base)
    first = subprocess.Popen([sys.executable, __file__, "--hold", d], env=dict(os.environ, **env, FAKE_BUILD_SLEEP="4"))
    time.sleep(1.5)
    code, out = run_tty(d, env)
    first.wait()
    check("redeploy: second start refused while one runs", code == 1 and "already running" in out, f"{code} {out[-300:]}")

    d, env = make_deploy_dir(base)
    code, out = run_tty(d, env, action="ctrl-c", when="LOGLINE", script="redeploy.sh")
    check("redeploy: `bash redeploy.sh` (no ./) works", code == 0 and DONE in out, f"{code} {out[-300:]}")

    d, env = make_deploy_dir(base)
    p = run_inline(d, env)
    check("redeploy: without a terminal (the pipeline) it runs inline and ends", p.returncode == 0 and DONE in p.stdout
          and "LOGLINE" not in p.stdout and deploy_log(d) is None, f"{p.returncode} {p.stdout[-300:]} {p.stderr[-300:]}")

    d, env = make_deploy_dir(base)
    open(os.path.join(d, ".env"), "w", newline="").write(GUARD_ENV)
    code, out = run_tty(d, dict(env, ZT_GUARD_PREFIX="10", ZT_GUARD_SECRET="prod-secret", ZT_GUARD_COMMENT="11"))
    check("redeploy: a shell value other than in .env stops it before anything runs, names the keys only",
          code == 1 and "ZT_GUARD_PREFIX ZT_GUARD_SECRET ZT_GUARD_COMMENT" in out and "prod-secret" not in out
          and "s3cr3t" not in out and "Running tests" not in out and deploy_log(d) is None and lock_free(d),
          f"{code} {out[-400:]}")

    d, env = make_deploy_dir(base)
    open(os.path.join(d, ".env"), "w", newline="").write(GUARD_ENV)
    p = run_inline(d, dict(env, ZT_GUARD_PREFIX="9", ZT_GUARD_SECRET="s3cr3t", ZT_GUARD_SINGLE="a b",
                           ZT_GUARD_COMMENT="10"))
    check("redeploy: shell values equal to .env (quoted, export, CRLF, inline comment) pass", p.returncode == 0
          and DONE in p.stdout, f"{p.returncode} {p.stdout[-300:]} {p.stderr[-300:]}")

    for args, tested, builds in [
        ([], True, ["build app"]),
        ([], False, ["build app-tests", "build app"]),
        (["--no-cache"], True, ["build --no-cache app-tests", "build --no-cache app"]),
    ]:
        d, env = make_deploy_dir(base, tested_requirements=tested)
        p, calls = compose_calls(d, env, *args)
        seen = [c for c in calls if c.startswith("build")]
        restarted = "up -d app-tests" in calls
        check(f"redeploy {' '.join(args) or '(no option)'}, requirements {'tested' if tested else 'changed'}: "
              f"builds {'without' if args else 'with'} the cache",
              p.returncode == 0 and DONE in p.stdout and seen == builds and restarted == (len(builds) == 2),
              f"{p.returncode} {calls}")

    d, env = make_deploy_dir(base, tested_requirements=False)
    p, calls = compose_calls(d, dict(env, FAKE_BUILD_FAIL="app-tests"))
    check("redeploy: a failed app-tests build stops it and keeps the requirements unmarked",
          p.returncode == 1 and "BUILD OF app-tests FAILED" in p.stderr and not any(c.startswith("run") for c in calls)
          and not os.path.exists(os.path.join(d, "app", ".requirements_hash")), f"{p.returncode} {calls}")

    d, env = make_deploy_dir(base)
    p, calls = compose_calls(d, env, "--nocache")
    check("redeploy: an unknown option stops it before tests and build",
          p.returncode == 1 and "Unknown option: --nocache" in p.stderr and calls == [],
          f"{p.returncode} {p.stdout[-300:]} {p.stderr[-300:]}")

    d, env = make_deploy_dir(base)
    p, calls = compose_calls(d, env)
    runs = [c for c in calls if c.startswith("run")]
    tests = open(os.path.join(REPO, "docker-compose.yml")).read().split("\n  app-tests:\n")[1].split("\nnetworks:\n")[0]
    check("redeploy: the tests run on four workers, the watcher too, with room for them (T-014)",
          p.returncode == 0 and len(runs) == 1
          and re.fullmatch(r"run --name test_run_\d+ --rm app-tests pytest -n 4 --testmon", runs[0]) is not None
          and "pytest -n 4 --testmon" in tests and "ptw . --delay 2 --testmon -n 4" in tests
          and "mem_limit: 1g" in tests and "memswap_limit: 1g" in tests
          and "pytest-xdist==" in open(os.path.join(REPO, "app", "requirements.txt")).read(), f"{p.returncode} {runs}")


# ------------------------------------------------------------ merge-to-main.sh

def git(cwd, *args, check_rc=True):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=check_rc)


def merge_setup(base):
    """origin + work clone on branch claude/feature; origin/main then moves ahead (version bump)."""
    d = tempfile.mkdtemp(dir=base)
    git(d, "init", "-q", "--bare", "-b", "main", "origin.git")
    git(d, "clone", "-q", "origin.git", "work")
    work = os.path.join(d, "work")
    git(work, "config", "user.email", "t@t")
    git(work, "config", "user.name", "t")
    open(os.path.join(work, "VERSION"), "w").write("1.0\n")
    open(os.path.join(work, "app.txt"), "w").write("a\n")
    git(work, "add", "-A"); git(work, "commit", "-qm", "init"); git(work, "push", "-q", "origin", "main")
    git(work, "switch", "-qc", "claude/feature")
    open(os.path.join(work, "feature.txt"), "w").write("feature\n")
    git(work, "add", "-A"); git(work, "commit", "-qm", "feature"); git(work, "push", "-q", "-u", "origin", "claude/feature")
    git(d, "clone", "-q", "origin.git", "other")
    other = os.path.join(d, "other")
    git(other, "config", "user.email", "t@t"); git(other, "config", "user.name", "t")
    open(os.path.join(other, "VERSION"), "w").write("1.1\n")
    git(other, "commit", "-qam", "bump version"); git(other, "push", "-q", "origin", "main")
    return work


def run_merge(work):
    script = open(os.path.join(REPO, "merge-to-main.sh")).read().replace("\nsleep 15\n", "\nsleep 0\n")
    return subprocess.run(["bash", "-c", script], cwd=work, capture_output=True, text=True)


def test_merge_to_main(base):
    work = merge_setup(base)
    p = run_merge(work)
    merged = "feature" in git(work, "log", "--oneline", "origin/main").stdout
    same = git(work, "rev-parse", "origin/claude/feature").stdout == git(work, "rev-parse", "origin/main").stdout
    check("merge: works although origin/main moved ahead", p.returncode == 0 and merged and same,
          f"{p.returncode} {p.stdout[-300:]} {p.stderr[-300:]}")

    work = merge_setup(base)
    git(work, "switch", "-q", "main"); git(work, "pull", "-q", "origin", "main")
    open(os.path.join(work, "app.txt"), "w").write("main side\n")
    git(work, "commit", "-qam", "main edit"); git(work, "push", "-q", "origin", "main")
    git(work, "switch", "-q", "claude/feature")
    open(os.path.join(work, "app.txt"), "w").write("branch side\n")
    git(work, "commit", "-qam", "branch edit")
    p = run_merge(work)
    clean = git(work, "status", "--porcelain").stdout == "" and not os.path.exists(os.path.join(work, ".git", "MERGE_HEAD"))
    check("merge: conflict aborts without a half merge", p.returncode == 1 and clean and "app.txt" in p.stdout,
          f"{p.returncode} {p.stdout[-400:]}")

    work = merge_setup(base)
    open(os.path.join(work, ".git", "MERGE_HEAD"), "w").write("")
    p = run_merge(work)
    check("merge: refuses while a merge is in progress", p.returncode == 1 and "already in progress" in p.stdout,
          f"{p.returncode} {p.stdout}")

    work = merge_setup(base)
    with open(os.path.join(work, "feature.txt"), "a") as f:
        f.write("uncommitted\n")
    p = run_merge(work)
    kept = "uncommitted" in open(os.path.join(work, "feature.txt")).read()
    check("merge: uncommitted change stops it and survives", p.returncode != 0 and kept, f"{p.returncode} {p.stdout}")


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--hold":  # helper: one detached deploy holding the lock
        run_tty(sys.argv[2], {}, action="ctrl-c", when="LOGLINE")
        sys.exit(0)
    with tempfile.TemporaryDirectory() as base:
        test_redeploy(base)
        test_merge_to_main(base)
    print("ALL PASS" if all(RESULTS) else "SOME FAILED")
    sys.exit(0 if all(RESULTS) else 1)

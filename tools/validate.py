#!/usr/bin/env python3
"""
Full publication gate. Runs every step in order and fails on the first problem.

  1. tools/verify.py  - prove the data against the official NFL.com standings
  2. tools/build.py   - regenerate every published number into data/output/
  3. tools/pages.py   - regenerate the site pages
  4. tools/sync.py    - keep the repository-root copies in step with site/
  5. site/check.py    - check the rendered site for broken links and unsourced rows
  6. determinism      - rebuild and confirm the output is byte-identical
  7. data hygiene     - no stray files, no oversized artifacts, no secrets

Exit code 0 = the repository is publishable.
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = sys.executable

STEPS = [
    ("verify data against official standings", [PY, os.path.join(ROOT, "tools", "verify.py")]),
    ("verify the injury dataset cell for cell against the official capture",
     [PY, os.path.join(ROOT, "tools", "capture_check.py")]),
    ("verify every stored official capture is unaltered (SHA-256)",
     [PY, os.path.join(ROOT, "tools", "capture_official.py"), "verify"]),
    ("test the official-capture gates offline (no network)",
     [PY, "-m", "unittest", "discover", "-s", os.path.join(ROOT, "tests"), "-p", "test_capture_official.py"]),
    ("test the capture watchdog offline (T69, no network, no clock)",
     [PY, "-m", "unittest", "discover", "-s", os.path.join(ROOT, "tests"), "-p", "test_capture_alert.py"]),
    ("schedule announcement: offline validation (T71)",
     [PY, "-m", "unittest", "discover", "-s", os.path.join(ROOT, "tests"), "-p", "test_schedule_page.py"]),
    ("build published numbers", [PY, os.path.join(ROOT, "tools", "build.py")]),
    ("check the price store, origination card and results feed",
     [PY, os.path.join(ROOT, "tools", "market_store.py")]),
    ("build the market layer (captured prices, skill/staking boards)",
     [PY, os.path.join(ROOT, "tools", "market.py")]),
    ("re-derive every market number independently",
     [PY, os.path.join(ROOT, "tools", "market_check.py")]),
    ("reconcile the two independent price captures",
     [PY, os.path.join(ROOT, "tools", "reconcile_prices.py")]),
    ("build site pages", [PY, os.path.join(ROOT, "tools", "pages.py")]),
    ("build the integrity datasets", [PY, os.path.join(ROOT, "tools", "build_integrity.py")]),
    ("build the programme page", [PY, os.path.join(ROOT, "tools", "gen_programme.py")]),
    ("build the suggestion workbench page", [PY, os.path.join(ROOT, "tools", "gen_workbench.py")]),
    ("build the desk data tables", [PY, os.path.join(ROOT, "tools", "gen_data_html.py")]),
    ("build the desk signals tables", [PY, os.path.join(ROOT, "tools", "gen_strategies_html.py")]),
    ("build the brief register page", [PY, os.path.join(ROOT, "tools", "gen_brief_register.py")]),
    ("build the desk executive summary", [PY, os.path.join(ROOT, "tools", "gen_exec_summary_desk.py")]),
    ("build the console executive summary", [PY, os.path.join(ROOT, "tools", "gen_exec_summary.py")]),
    ("originate the markets and the price store", [PY, os.path.join(ROOT, "tools", "fetch.py"), "plan"]),
    ("ingest the cached bodies", [PY, os.path.join(ROOT, "tools", "fetch.py"), "ingest"]),
    ("fail if the gate run mutated the committed data tree", [PY, os.path.join(ROOT, "tools", "validate.py"), "--gate-clean"]),
    ("check the official Game Book sweep (Week 10)",
     [PY, os.path.join(ROOT, "tools", "gamebook_sweep.py"), "--check"]),
    ("build the official depth charts", [PY, os.path.join(ROOT, "tools", "depth.py")]),
    ("rebuild the open-question register", [PY, os.path.join(ROOT, "tools", "open_questions.py")]),
    ("re-derive the paired sign test on the walk-forward corpus",
     [PY, os.path.join(ROOT, "tools", "sign_test.py"), "--check"]),
    ("re-derive the personnel / availability ablation",
     [PY, os.path.join(ROOT, "tools", "personnel_ablation.py"), "--check"]),
    ("test origination settlement rules", [PY, os.path.join(ROOT, "tools", "test_origination.py")]),
    ("originate lines and grade them", [PY, os.path.join(ROOT, "tools", "origination.py")]),
    ("build the replacement-depth ledger", [PY, os.path.join(ROOT, "tools", "depth_ledger.py")]),
    ("build the origination pages", [PY, os.path.join(ROOT, "tools", "ops.py")]),
    ("self-test the two-stage escrow (T48)", [PY, os.path.join(ROOT, "tools", "test_escrow.py")]),
    ("build the two-stage escrow page (T48)", [PY, os.path.join(ROOT, "tools", "gen_escrow.py")]),
    ("write the research findings", [PY, os.path.join(ROOT, "tools", "research.py")]),
    ("sync root copies", [PY, os.path.join(ROOT, "tools", "sync.py")]),
    ("check site", [PY, os.path.join(ROOT, "site", "check.py")]),
    ("check repository-root copy of the site", [PY, os.path.join(ROOT, "site", "check.py"), ROOT]),
    ("check the desk pages", [PY, os.path.join(ROOT, "tools", "check_site.py")]),
]


def run(label, cmd):
    print("\n=== %s ===" % label, flush=True)
    r = subprocess.run(cmd, cwd=ROOT)
    if r.returncode != 0:
        print("\nVALIDATION FAILED at step: %s" % label)
        return False
    return True


def main():
    for label, cmd in STEPS:
        if not run(label, cmd):
            return 1

    # ---- determinism: rebuild and require byte-identical output ----
    print("\n=== determinism ===", flush=True)
    before = {}
    for rel in ("site/index.html", "site/styles.css", "site/app.js",
                "index.html", "styles.css", "app.js",
                "research/strategy-validation.md", "research/injuries-and-depth.md",
                "site/market.html", "market.html", "data/output/market.json",
                "data/market-snapshots-2026.csv",
                "site/programme.html", "programme.html", "site/workbench.html", "workbench.html",
                "research/data/integrity_summary.json",
                "site/data.html", "data.html", "site/signals.html", "signals.html",
                "site/brief-register.html", "brief-register.html",
                "site/executive-summary.html", "executive-summary.html"):
        path = os.path.join(ROOT, rel)
        if os.path.exists(path):
            before[rel] = open(path, "rb").read()
    subprocess.run([PY, os.path.join(ROOT, "tools", "build.py")], cwd=ROOT,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run([PY, os.path.join(ROOT, "tools", "market.py")], cwd=ROOT,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run([PY, os.path.join(ROOT, "tools", "pages.py")], cwd=ROOT,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run([PY, os.path.join(ROOT, "tools", "build_integrity.py")], cwd=ROOT,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run([PY, os.path.join(ROOT, "tools", "gen_programme.py")], cwd=ROOT,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run([PY, os.path.join(ROOT, "tools", "gen_workbench.py")], cwd=ROOT,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run([PY, os.path.join(ROOT, "tools", "gen_data_html.py")], cwd=ROOT,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run([PY, os.path.join(ROOT, "tools", "gen_strategies_html.py")], cwd=ROOT,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run([PY, os.path.join(ROOT, "tools", "research.py")], cwd=ROOT,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run([PY, os.path.join(ROOT, "tools", "sync.py")], cwd=ROOT,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for rel, data in before.items():
        now = open(os.path.join(ROOT, rel), "rb").read()
        if now != data:
            print("  - %s is not reproducible: rebuilding changed the file" % rel)
            print("\nVALIDATION FAILED at step: determinism")
            return 1
        print("  - %s reproducible" % rel)

    # ---- the second console, if a parallel session published one ----
    console_check = os.path.join(ROOT, "docs", "check.js")
    if os.path.exists(console_check):
        print("\n=== check the X4 console (docs/) ===", flush=True)
        r = subprocess.run(["node", console_check], cwd=ROOT)
        if r.returncode != 0:
            print("\nVALIDATION FAILED at step: console check")
            return 1

    # ---- the repository-root mirror must match site/ and docs/ ----
    print("\n=== repository-root mirror ===", flush=True)
    mirror_problems = []
    for src, dst, skip in (("site", ".", {"check.py"}), ("docs", "console", {"check.js"})):
        src_dir = os.path.join(ROOT, src)
        dst_dir = os.path.join(ROOT, dst)
        for dirpath, dirnames, filenames in os.walk(src_dir):
            dirnames[:] = [d for d in dirnames if d not in (".git", "node_modules", "__pycache__")]
            for fn in filenames:
                if fn in skip:
                    continue
                full = os.path.join(dirpath, fn)
                rel = os.path.relpath(full, src_dir)
                target = os.path.join(dst_dir, rel)
                if not os.path.exists(target):
                    mirror_problems.append("%s/%s is missing from %s/" % (src, rel, dst))
                elif open(full, "rb").read() != open(target, "rb").read():
                    mirror_problems.append("%s/%s differs from %s/%s" % (src, rel, dst, rel))
    if mirror_problems:
        for mp in mirror_problems[:20]:
            print("  - %s" % mp)
        print("\nVALIDATION FAILED at step: repository-root mirror")
        return 1
    print("  - the repository root is a byte-identical mirror of site/ and docs/")

    # ---- data hygiene ----
    print("\n=== data hygiene ===", flush=True)
    problems = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in (".git", "node_modules", "__pycache__")]
        for fn in filenames:
            path = os.path.join(dirpath, fn)
            rel = os.path.relpath(path, ROOT)
            if rel.startswith(".git/"):
                continue
            size = os.path.getsize(path)
            if size > 5 * 1024 * 1024:
                problems.append("%s is %.1f MB" % (rel, size / 1048576.0))
            if fn.endswith((".pyc", ".pyo")):
                problems.append("%s is a compiled artifact" % rel)
            if fn in (".env", "credentials.json", "secrets.json"):
                problems.append("%s looks like a credential file" % rel)
    for rel in ("data/output", "research", "site"):
        if not os.path.isdir(os.path.join(ROOT, rel)):
            problems.append("expected directory is missing: %s" % rel)
    for rel in ("README.md", "COORDINATION.md", "data/games-2026.csv",
                "data/standings-wk10-2026.csv", "data/schedule-wk11-2026.csv",
                "data/injuries-wk10-2026.csv", "site/index.html",
                "site/app.js", "site/styles.css", "site/check.py",
                "console/index.html", "docs/index.html",
                "data/output/payload.json", "data/output/payload.js",
                ".github/workflows/pages.yml"):
        if not os.path.exists(os.path.join(ROOT, rel)):
            problems.append("expected file is missing: %s" % rel)
    if problems:
        for p in problems:
            print("  - %s" % p)
        print("\nVALIDATION FAILED at step: data hygiene")
        return 1
    print("  - no oversized artifacts, no stray files, required files present")

    print("\nVALIDATION PASSED - the repository is publishable.")
    return 0


def gate_clean():
    """A publication gate run must leave every committed dataset unchanged.

    tools/fetch.py ingest rebuilds the data/ops CSVs from the committed raw
    bodies. When its output matches what is already committed the tree is
    unchanged (the normal case). When it would differ, this guard fails loudly
    and names the files: a gate run must never silently append or rewrite rows
    (request logged by arena/e6ee28a8-x4: "Gate runs should not mutate
    datasets"). The diff is left visible on purpose so it can be reviewed and
    either committed as an explicit data change or reverted - a failing gate
    restores nothing and hides nothing."""
    changed = []
    diff = subprocess.run(["git", "diff", "--name-only", "--", "data/"],
                          cwd=ROOT, capture_output=True, text=True)
    changed += [line for line in diff.stdout.splitlines() if line.strip()]
    untracked = subprocess.run(["git", "ls-files", "--others", "--exclude-standard", "--", "data/"],
                               cwd=ROOT, capture_output=True, text=True)
    changed += [line for line in untracked.stdout.splitlines() if line.strip()]
    if not changed:
        print("  - the gate run left every committed dataset unchanged")
        return 0
    print("VALIDATION FAILED: the gate run changed the data tree:")
    for rel in changed:
        print("  changed: %s" % rel)
    print("Run 'python3 tools/fetch.py ingest' (and the other data steps) explicitly, review the")
    print("diff, and commit it as a deliberate data change - or revert it. A publication gate")
    print("run must never mutate a dataset silently.")
    return 1


if __name__ == "__main__":
    if sys.argv[1:] == ["--gate-clean"]:
        sys.exit(gate_clean())
    sys.exit(main())

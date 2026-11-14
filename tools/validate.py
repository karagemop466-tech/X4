#!/usr/bin/env python3
"""
Full publication gate. Runs every step in order and fails on the first problem.

  1. tools/verify.py  - prove the data against the official NFL.com standings
  2. tools/build.py   - regenerate every published number into site/data.js
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
    ("build published numbers", [PY, os.path.join(ROOT, "tools", "build.py")]),
    ("build site pages", [PY, os.path.join(ROOT, "tools", "pages.py")]),
    ("sync root copies", [PY, os.path.join(ROOT, "tools", "sync.py")]),
    ("check site", [PY, os.path.join(ROOT, "site", "check.py")]),
    ("check repository-root copy of the site", [PY, os.path.join(ROOT, "site", "check.py"), ROOT]),
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
    for rel in ("site/data.js", "site/index.html", "site/styles.css",
                "index.html", "data.js", "styles.css"):
        path = os.path.join(ROOT, rel)
        if os.path.exists(path):
            before[rel] = open(path, "rb").read()
    subprocess.run([PY, os.path.join(ROOT, "tools", "build.py")], cwd=ROOT,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run([PY, os.path.join(ROOT, "tools", "pages.py")], cwd=ROOT,
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
                "data/injuries-wk10-2026.csv", "site/index.html", "site/data.js",
                "site/app.js", "site/styles.css", "site/check.py",
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


if __name__ == "__main__":
    sys.exit(main())

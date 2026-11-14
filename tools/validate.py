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
    ("build published numbers", [PY, os.path.join(ROOT, "tools", "build.py")]),
    ("build site pages", [PY, os.path.join(ROOT, "tools", "pages.py")]),
    ("write the research findings", [PY, os.path.join(ROOT, "tools", "research.py")]),
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

    # ---- the published mirrors must hold identical bytes ----
    print("\n=== published mirrors ===", flush=True)
    problems = []
    site = os.path.join(ROOT, "site")
    for fn in sorted(os.listdir(site)):
        path = os.path.join(site, fn)
        if not os.path.isfile(path) or fn == "check.py":
            continue
        root_copy = os.path.join(ROOT, fn)
        if not os.path.exists(root_copy):
            problems.append("the repository root is missing %s" % fn)
        elif open(path, "rb").read() != open(root_copy, "rb").read():
            problems.append("the repository-root copy of %s differs from site/%s" % (fn, fn))
    console = os.path.join(ROOT, "console")
    docs = os.path.join(ROOT, "docs")
    if os.path.isdir(docs):
        for dst, label in ((console, "console/"), (os.path.join(site, "console"), "site/console/")):
            for dirpath, _dirs, files in os.walk(docs):
                for fn in files:
                    if fn == "check.js":
                        continue
                    src = os.path.join(dirpath, fn)
                    rel = os.path.relpath(src, docs)
                    target = os.path.join(dst, rel)
                    if not os.path.exists(target):
                        problems.append("%s is missing %s" % (label, rel))
                    elif open(src, "rb").read() != open(target, "rb").read():
                        problems.append("%s differs from docs/%s" % (target, rel))
    if problems:
        for p in problems:
            print("  - %s" % p)
        print("\nVALIDATION FAILED at step: published mirrors")
        return 1
    print("  - the repository root, site/ and the console mirrors hold identical bytes")

    # ---- determinism: rebuild and require byte-identical output ----
    print("\n=== determinism ===", flush=True)
    before = {}
    for rel in ("site/index.html", "site/styles.css", "site/app.js",
                "index.html", "styles.css", "app.js",
                "research/strategy-validation.md", "research/injuries-and-depth.md"):
        path = os.path.join(ROOT, rel)
        if os.path.exists(path):
            before[rel] = open(path, "rb").read()
    subprocess.run([PY, os.path.join(ROOT, "tools", "build.py")], cwd=ROOT,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run([PY, os.path.join(ROOT, "tools", "pages.py")], cwd=ROOT,
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


if __name__ == "__main__":
    sys.exit(main())

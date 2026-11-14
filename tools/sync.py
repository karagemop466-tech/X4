#!/usr/bin/env python3
"""Keep the repository-root copies of the site in step with site/.

An earlier session kept index.html, styles.css and app.js at the repository root
as well as inside site/. The Pages workflow publishes site/, but a reader who
opens the repository root should still find a working site, so the whole
published site is mirrored to the root.

Files mirrored: every page and asset in site/ except check.py, which is a build
tool rather than a site asset. Root copies that are no longer part of the site
are removed.
"""
import os
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "site")

SKIP = {"check.py"}
KEEP_ROOT = {"README.md", "COORDINATION.md"}


def main():
    changed = []
    names = []
    for fn in sorted(os.listdir(SITE)):
        path = os.path.join(SITE, fn)
        if not os.path.isfile(path) or fn in SKIP:
            continue
        names.append(fn)
        dst = os.path.join(ROOT, fn)
        if os.path.exists(dst) and open(path, "rb").read() == open(dst, "rb").read():
            continue
        shutil.copyfile(src=path, dst=dst)
        changed.append(fn)

    # remove root files that used to be part of the site but are not any more
    removed = []
    for fn in sorted(os.listdir(ROOT)):
        if fn in names or fn in SKIP or fn in KEEP_ROOT:
            continue
        path = os.path.join(ROOT, fn)
        if not os.path.isfile(path):
            continue
        if fn.endswith((".html", ".css", ".js")):
            os.remove(path)
            removed.append(fn)

    if changed:
        print("mirrored to the repository root: %s" % ", ".join(changed))
    if removed:
        print("removed stale root files: %s" % ", ".join(removed))
    if not changed and not removed:
        print("repository-root copies already match site/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

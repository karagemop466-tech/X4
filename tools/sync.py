#!/usr/bin/env python3
"""Keep the repository-root copies of the site in step with site/.

An earlier session kept index.html, styles.css and app.js at the repository root as
well as inside site/. The Pages workflow publishes site/, but a reader who opens the
repository root should still find a working site, so the whole published site is
mirrored to the root.

Files mirrored: every page and every asset in site/ except check.py, which is a
build tool rather than a site asset.
"""
import os
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "site")

SKIP = {"check.py"}


def site_files():
    names = []
    for fn in sorted(os.listdir(SITE)):
        path = os.path.join(SITE, fn)
        if not os.path.isfile(path) or fn in SKIP:
            continue
        names.append(fn)
    return names


def main():
    changed = []
    for name in site_files():
        src = os.path.join(SITE, name)
        dst = os.path.join(ROOT, name)
        if os.path.exists(dst) and open(src, "rb").read() == open(dst, "rb").read():
            continue
        shutil.copyfile(src, dst)
        changed.append(name)
    if changed:
        print("mirrored to the repository root: %s" % ", ".join(changed))
    else:
        print("repository-root copies already match site/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Keep the repository-root copies of the site in step with site/.

Two things are mirrored to the repository root:

1. The published site (`site/`) - so a reader who opens the repository root
   finds a working site.
2. The parallel session's X4 console (`docs/`) - to `console/` - so that the
   repository root, which is what the legacy GitHub Pages build publishes, is
   byte-identical to what the custom workflow publishes from `site/`.

Without the second mirror the two Pages builds would race and the published
site would differ depending on which deployment finished last.

Files mirrored: every page and asset in site/ except check.py, which is a build
tool rather than a site asset. Root copies that are no longer part of the site
are removed.
"""
import filecmp
import os
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "site")
DOCS = os.path.join(ROOT, "docs")
CONSOLE = os.path.join(ROOT, "console")

SKIP = {"check.py", "README.md", "COORDINATION.md"}
# README.md and COORDINATION.md are repository files, not site assets: they are
# published INTO site/ (step 4) and must never be mirrored back over the root copy.

# Pages published by the decision-desk layer. They also live in site/, but they
# are not owned by this mirror step, so it must never delete them from the root.
DESK_OWNED = {
    "executive-summary.html", "requirements.html", "data.html", "signals.html",
    "leaderboard.html", "injuries.html", "decisions.html", "review.html",
    "flagged.html", "repo-review.html", "sources.html",
}


def is_desk_mirror(fn):
    return fn in DESK_OWNED
KEEP_ROOT = {"README.md", "COORDINATION.md", ".gitignore"}
# Build tools that live next to a site but are not part of it.
NOT_SITE = {"check.js"}


def mirror_tree(src, dst, skip=()):
    """Copy every file under src into dst, and report what changed."""
    changed = []
    src_files = {}
    for dirpath, dirnames, filenames in os.walk(src):
        dirnames[:] = [d for d in dirnames if d not in (".git", "node_modules", "__pycache__")]
        for fn in filenames:
            if fn in skip:
                continue
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, src)
            src_files[rel] = full
    for rel, full in src_files.items():
        target = os.path.join(dst, rel)
        os.makedirs(os.path.dirname(target), exist_ok=True)
        if os.path.exists(target) and filecmp.cmp(full, target, shallow=False):
            continue
        shutil.copyfile(full, target)
        changed.append(rel)
    # remove files in dst that are no longer in src
    for dirpath, dirnames, filenames in os.walk(dst, topdown=False):
        for fn in filenames:
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, dst)
            if rel not in src_files:
                os.remove(full)
                changed.append("(removed) " + rel)
    return changed


def main():
    changed = []
    # 1. the published site
    names = []
    for fn in sorted(os.listdir(SITE)):
        path = os.path.join(SITE, fn)
        if not os.path.isfile(path) or fn in SKIP:
            continue
        names.append(fn)
        dst = os.path.join(ROOT, fn)
        if os.path.exists(dst) and filecmp.cmp(path, dst, shallow=False):
            continue
        shutil.copyfile(path, dst)
        changed.append(fn)

    # remove root files that used to be part of the site but are not any more
    for fn in sorted(os.listdir(ROOT)):
        if fn in names or fn in SKIP or fn in KEEP_ROOT:
            continue
        path = os.path.join(ROOT, fn)
        if os.path.isfile(path) and fn.endswith((".html", ".css", ".js")):
            # Only remove root copies that this file used to mirror. A page owned
            # by another session (the decision-desk layer in site/ that is not in
            # the main PAGES list) must survive - deleting it would silently take
            # another session's published page off the site.
            if not is_desk_mirror(fn):
                os.remove(path)
                changed.append("(removed) " + fn)

    # 2. the parallel console, so the legacy Pages build publishes the same site
    if os.path.isdir(DOCS):
        changed += ["console/" + c for c in mirror_tree(DOCS, CONSOLE, skip=NOT_SITE)]

    # 3. the datasets and notes the published pages cite.
    # The Pages artifact is `site/`, so a page that links to research/<file>.csv
    # or data/ops/<file>.csv would 404 for a reader unless the file is published
    # next to the page. `data/output/` and `data/transactions/` are build output
    # and transaction ledgers that no page links to, so they are not published.
    research = os.path.join(ROOT, "research")
    if os.path.isdir(research):
        changed += ["site/" + c for c in mirror_tree(research, os.path.join(SITE, "research"))]

    data = os.path.join(ROOT, "data")
    if os.path.isdir(data):
        for name in sorted(os.listdir(data)):
            src = os.path.join(data, name)
            if not os.path.isfile(src) or not name.endswith(".csv"):
                continue
            dst = os.path.join(SITE, "data", name)
            if os.path.exists(dst) and filecmp.cmp(src, dst, shallow=False):
                continue
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copyfile(src, dst)
            changed.append("site/data/" + name)
        ops = os.path.join(data, "ops")
        if os.path.isdir(ops):
            changed += ["site/" + c for c in mirror_tree(ops, os.path.join(SITE, "data", "ops"))]

    # 4. the audit trail the pages point at
    for name in ("COORDINATION.md", "README.md"):
        src = os.path.join(ROOT, name)
        dst = os.path.join(SITE, name)
        if not os.path.exists(src):
            continue
        if os.path.exists(dst) and filecmp.cmp(src, dst, shallow=False):
            continue
        shutil.copyfile(src, dst)
        changed.append("site/" + name)

    if changed:
        print("synchronised: %s" % ", ".join(changed))
    else:
        print("repository-root copies already match site/ and docs/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

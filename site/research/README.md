# Research layer — what is private and what is published

This directory is the **private layer**. It holds the evidence behind every
published number: raw official captures, verification records, and the audit
trails that let a reader re-derive a value instead of trusting it.

The boundary is deliberate. A PDF or an official page is a *licensed artefact*,
not data. Its verbatim text is stored here as evidence — hashed, stamped, and
re-readable — while only values **derived** from it reach the site. That is the
reuse gate, and it is what makes a blank defensible: when a cell the source does
not print is published blank, the capture is what proves the blank is the
source's and not ours.

## Layers

| Layer | Lives in | Published? | Why |
|---|---|---|---|
| Raw official captures | `data/ops/raw/` | No — evidence only | Verbatim text from a licensed source; stored with a UTC stamp and a SHA-256 |
| Verification records | `research/verification/` | Yes — as audit records | What was checked, what it proved, what it could not prove |
| Derived datasets | `data/` | Yes | Values computed from official sources by a written-down rule |
| Rendered pages | `site/` (+ root mirror) | Yes | The published site |

## Captures

Every file in `data/ops/raw/` carries a sibling `.stamp` holding its UTC
retrieval time, and the byte-level SHA-256 of each Game Book capture is
recorded in `data/ops/gamebook-capture-inventory.json`. A later edit —
accidental or not — changes the hash, so an altered capture is detectable
rather than invisible.

`gamebook-*.txt` (15 files, Week 10 2026) are the official NFL Game Books for
all 14 Week 10 games, converted to text. Two captures exist for Houston at
Cleveland: the T47 capture of the Houston side only, and the full re-capture of
both clubs. Both are kept, and their Houston rows agree independently.

## What is never done with a capture

- Its verbatim text is not re-published as a table of its own.
- A cell the conversion lost is not filled from another week, a club site, or
  memory of a roster. It is published blank with the reason.
- A player absent from all four Game Book sections is **unresolved**, not "did
  not play". Absence is not an outcome.
- Depth order is never inferred from jersey number, salary or experience.

## Reproducing the Game Book layer

```
python3 tools/gamebook_sweep.py --check    # validate only; exit 1 on any problem
python3 tools/gamebook_sweep.py            # rebuild the five derived datasets
sha256sum data/ops/raw/gamebook-*.txt      # compare with the inventory above
```

The gate enforces 14 games, an `https` source on every row, eleven-or-blank
starters per unit, and the arithmetic of the reliability table.

## Private page

`site/gamebook-ops.html` documents this layer for readers: the capture register
with hashes and stamps, the seven-stage pipeline, the private artefacts, the
five public exports, and the reuse gate.

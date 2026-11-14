# Raw retrieval captures (moved here by T32, 2026-11-14)

The harness scripts in this directory (`record.py`, `save.py`) write `fetch_page`
payloads to exactly this path (`data/ops/raw/`, per their `RAW` constant), so this
is their natural home. The capture files below were found committed at the
repository root as `.retrieval/` and `.scratch/` — sandbox working directories
that had been accidentally staged into git. Because the publish workflow's
repository-root mirror gate (`diff -rq site .`) treats any extra root entry as a
mirror break, they are now tracked here instead, unchanged, byte for byte.

| File | Content |
|---|---|
| `p1.txt`–`p4.txt` | Verbatim ESPN odds-API payloads (provider DraftKings) for Week 11 2026 events, captured 2026-11-14 |
| `p_401873037.txt`–`p_401873039.txt` | The same, for three additional events |
| `odds_notes.md` | The derived opening/current odds table behind `data/market-prices.csv` |
| `record.py`, `save.py` | The capture harness (verbatim body + parsed cache body + UTC stamp) |

Provenance of the derived data itself is documented in `data/ops/README.md` and
`research/data-verification.md`; the capture bodies above remain available as
evidence. If the owning session (T21 origination layer) prefers a different
location, move them freely — the publish gate only requires that no stray
entries remain at the repository root.

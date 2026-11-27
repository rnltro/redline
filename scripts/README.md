# scripts/ — verification suites

Headless (Playwright) checks that back the claims in the repo README — the same
suites used during the build. Paths are relative: they default to the repo root
(one level up from `scripts/`), or pass an explicit folder as argv[1].

| Script | What it proves |
| --- | --- |
| `verify_upload_security.py` | 30 checks — malicious / oversized / path-trick uploads rejected; placeholders-only cloud path |
| `verify_phone_install.py` | 23 checks — install modal steps + copy-link box, service worker + manifest boot, zero page errors |
| `verify_pwa.py` | offline PWA pipeline — cached shell boot, TXT/PDF scanning and OCR with the network off |
| `benchmark_redaction.py` | precision/recall of the scanner vs hand-annotated ground truth on `samples/` — P 0.912 · R 1.000 · F1 0.954 (64 entities) |
| `make_pwa_icons.py` | regenerates the `icons/` set from a source image |

Run:

```bash
pip install playwright && playwright install chromium
python scripts/verify_upload_security.py                 # defaults to the repo root
python scripts/verify_phone_install.py /path/to/repo     # or pass a folder
```

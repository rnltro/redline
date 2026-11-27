# Redline — Redact first, ask later

**The confidential-document copilot that never sees your real text.** Redline
finds the sensitive entities in any document, replaces them with typed
placeholders, and only sends *those* to the AI — with an append-only receipt
proving where every stage ran and what was sent. Built with **Firebase AI Logic
hybrid inference** for the **#BuildHybridAI** hackathon.

> Most AI workflows paste contracts straight into a model: names, amounts,
> client terms — one paste, and they're on someone else's server. Redline
> flips the order: **redact first, ask later.**

---

## How the hybrid pipeline works

```
┌─────────────────┐   ┌──────────────────┐   ┌───────────────────────────┐
│ 1 · SCAN        │   │ 2 · CONSENT GATE │   │ 3 · HYBRID ANSWER         │
│ 100% on device  │ → │ approve exactly  │ → │ Gemini Nano on device     │
│ OCR + 6 entity  │   │ what may leave,  │   │ first; cloud Gemini 2.5   │
│ types →         │   │ entity by entity │   │ Flash-Lite fallback —     │
│ [PERSON_1]…     │   │ (the only door   │   │ placeholders only, never  │
│                 │   │  out)            │   │ the original text         │
└─────────────────┘   └──────────────────┘   └───────────────────────────┘
                                   ↓
                     ┌───────────────────────────┐
                     │ 4 · RECEIPT (append-only) │
                     │ where each stage ran,     │
                     │ what was sent, the counts │
                     └───────────────────────────┘
```

- **Scan** — `.txt`, `.md`, `.docx`, `.pdf`, and photos/scans of documents
  (on-device Tesseract OCR). Finds **six entity types**: people, companies,
  amounts, dates, emails, titles → typed placeholders like `[PERSON_1]`,
  `[AMOUNT_1]`.
- **Consent gate** — the real value and its placeholder, side by side. You
  approve entity by entity. Nothing reaches the network without a green check.
- **Hybrid inference** — Firebase AI Logic tries **Gemini Nano on device**
  first (zero network); heavier questions fall back to **cloud Gemini 2.5
  Flash-Lite**, which receives the approved placeholders only.
- **Receipt** — append-only proof (where each stage ran / what was sent /
  counts), exportable as `.json`; the redlined document exports as `.docx`.

## Try it — three ways

| Way | What you get |
| --- | --- |
| **Live demo** | Open the hosted `https://…` URL — nothing to install, no sign-up. *(paste your link here)* |
| **Open locally** | Download/clone → open `redline_app_preview.html` in any browser. Full pipeline, demo mode, works offline. |
| **Deploy yourself** | `cd firebase_deploy_kit && firebase use --add && firebase deploy --only hosting` — see `firebase_deploy_kit/DEPLOY.md` (10 minutes, free Spark plan). |

## Judge quick test (2 minutes)

1. Drop any `.txt` / `.docx` / `.pdf` — or a **photo** of a contract (OCR kicks in).
2. Watch the scan: typed placeholders replace every sensitive entity.
3. Approve the gate, ask a question, read the answer.
4. **Download audit log (.json)** — the receipt shows exactly what was sent: placeholders only.
5. *Power move:* install on your phone (the **📱 Install on phone** pill has the steps),
   scan once online, then **airplane mode** — it boots from cache, parses, even OCRs.

**App Check note:** the connected build works without any keys — demo mode runs
the same pipeline locally. To exercise the real Firebase AI path, register a
debug token (Devpost rules accept debug tokens) or add a Fraud Defense site key.
No secrets live in this repo; your config never leaves your machine.

## Run with your own Firebase (optional)

The connected build (`redline_app_connected.html`) imports the Firebase SDK and
calls Firebase AI Logic, App Check, Remote Config and Firestore at runtime.
It ships **placeholder-only config** (`REPLACE_ME`) — wire it either way:

- paste your `firebaseConfig` into the `FIREBASE_CONFIG` block, or
- open with `?fb_apiKey=…&fb_projectId=…&fb_appId=…`

The kit in `firebase_deploy_kit/` ships `firebase.json`, Firestore rules
(append-only receipts, default-deny), indexes, and a 10-minute deploy guide.

## Privacy & security model

- Document text is parsed, redacted and restored **entirely on device** — it is
  never stored server-side.
- Firestore stores **only** matter metadata, the findings *index* and receipts —
  never document text. Rules: owner-only access, **append-only** receipts
  (no update/delete), default-deny everywhere else.
- App Check (Fraud Defense / debug-token submission mode) gates AI Logic + Firestore.
- The service worker caches app shell + engines, **never** Firebase API calls.

## Repo structure

```
redline_app_preview.html      # the app, demo mode — open in any browser
redline_app_connected.html    # same app + live Firebase (placeholder config)
sw.js · manifest.webmanifest  # PWA: offline boot, airplane-mode OCR
icons/                        # 192 / 512 / maskable / apple-touch / favicon
samples/                      # judge test files: brief/txt, contracts, photo scan for OCR
firebase_deploy_kit/          # firebase.json, Firestore rules+indexes, DEPLOY.md
scripts/                      # verification suites (Playwright) + icon generator
```

## Verification

`scripts/` contains reproducible Playwright suites: upload security
(malicious/oversized/path-trick files — 30 checks), phone-install flow
(23 checks), PWA offline pipelines. They run headless against the shipped
builds and are the fastest way to confirm the claims above.

## Redaction benchmark

`scripts/benchmark_redaction.py` scores the local scanner against hand-annotated
ground truth on the bundled samples, through the real UI path — **precision 0.912,
recall 1.000, F1 0.954** (64 entities, six types; raw results in
`scripts/benchmark_results.json`). Every false positive over-redacts (a superset
of the sensitive span near two-column signature blocks) rather than under-redacts:
nothing annotated ever escapes redaction. Rerun it:
`python3 scripts/benchmark_redaction.py`.

## License

Apache-2.0 — see [LICENSE](LICENSE).

*Built for the #BuildHybridAI hackathon (Firebase Hybrid AI, Devpost) —
Firebase AI Logic hybrid inference · App Check · Remote Config · Firestore · Hosting.*

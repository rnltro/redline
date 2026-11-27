# Redline — Firebase Deployment Runbook

Covers both hosting routes from build plan §10 (Table 13): the **static preview**
route for an instant live URL, and the **App Hosting** route for the real Next.js
build — plus App Check, Auth, Firestore and App Distribution setup for the
#BuildHybridAI submission.

## 0. Prerequisites

| Requirement | Why | Notes |
| --- | --- | --- |
| Node.js 20+ | Firebase CLI, Next.js build | `node -v` |
| Firebase CLI | deploys, App Distribution | `npm install -g firebase-tools` |
| Google account + Firebase project | everything | console.firebase.google.com → **Add project** |
| **Blaze plan** (pay-as-you-go) | App Hosting + Firebase AI Logic cloud path | Required for both; free trial credits cover a hackathon-scale project. The on-device path (Stage 1) works regardless of plan. |
| GitHub repo | App Hosting auto-deploys on push | Connect in console |

Register **both apps** in the one project ("One Project, Two Apps", Table 13):
Project settings → Your apps → **Web** (get the `firebaseConfig` object) and
**Android** with package name `com.redline.app`.

Then in this folder:

```bash
firebase login
# edit .firebaserc → replace REPLACE_WITH_YOUR_PROJECT_ID
firebase use --add          # or: firebase use <your-project-id>
```

## 1. Route A — static preview live in 5 minutes

`public/index.html` already contains the Redline app preview. This works on the
free Spark plan and needs no build step:

```bash
firebase deploy --only hosting
```

→ Live at `https://<project-id>.web.app` (and `<project-id>.firebaseapp.com`).

Use this for the Devpost "live demo" link while the Next.js app is in progress.
Cache headers are set to `no-cache` so every deploy is picked up instantly.

## 2. Route B — Firebase App Hosting (the real Next.js app)

App Hosting runs Next.js SSR on Cloud Run with a global CDN, and auto-builds on
every push to GitHub. Requires the Blaze plan.

1. Firebase console → **App Hosting** → **Create backend** → pick region →
   **Connect GitHub repo** → select branch (`main`).
2. Point it at the Next.js app directory (monorepo-aware).
3. `apphosting.yaml` (already in this kit, committed at the repo root) sets
   `runConfig` (scale-to-zero, 512 MiB) and the env vars. Fill the
   `NEXT_PUBLIC_FIREBASE_*` values from the web app's config object.
4. Server-only credentials go through **Secret Manager**, never plaintext:

   ```bash
   firebase apphosting:secrets:set GEMINI_API_KEY
   ```

5. Every `git push` → build → rollout. Rollbacks are one click in the console.

Local development stays plain Next.js (`npm run dev`) — no emulator needed for
App Hosting itself; the emulators block in `firebase.json` covers Auth +
Firestore + Hosting for local iteration.

## 3. Firestore — rules and indexes

The kit ships the security model that matches §4.6 (document text never stored):

```bash
firebase deploy --only firestore:rules,firestore:indexes
```

What `firestore.rules` enforces:

- Everything lives under `/users/{uid}/…` — read/write only for the signed-in owner.
- `/users/{uid}/receipts/{id}` is **append-only**: reads and creates, no updates
  or deletes — the trust receipt can't be quietly rewritten.
- Default-deny for every other path, including cross-user reads.

Remember what this database deliberately does NOT contain: document text.
Only matter metadata, the findings index and receipts.

## 4. App Check — the gate for the AI calls

App Check makes sure only your genuine web/Android binaries can reach the AI
Logic backend and Firestore. Console → **App Check** → **Apps**:

| Platform | Provider | Setup |
| --- | --- | --- |
| Web | **Fraud Defense (formerly reCAPTCHA Enterprise)** — the provider the App Check console registers today; classic reCAPTCHA v3 keys still work via `fb_appCheckProvider=v3` | Create a **Score**-based key in Cloud console → reCAPTCHA (domains: `localhost`, `<project-id>.web.app`, `<project-id>.firebaseapp.com`); put the site key in `FIREBASE_CONFIG.appCheckSiteKey` (connected.html) or `NEXT_PUBLIC_FIREBASE_APP_CHECK_SITE_KEY` (Next.js route) |
| Android | Play Integrity | Requires the app to be connected to a Play Console project; while testing via App Distribution before Play review, use the **Debug provider** and note it in the Devpost description |

Then enable **enforcement** for: Firebase AI Logic (the Gemini calls),
Firestore, and Hosting/App Hosting if you use rewrites to protected backends.
Initialize it in code before any AI call (`initializeAppCheck` on web,
`FirebaseAppCheck` on Android).

**No site key yet? Debug tokens are accepted in submissions** (per the
challenge rules: "Firebase AI Logic requires App Check; debug tokens are
accepted"). The connected build supports this directly:

- Put a token in `FIREBASE_CONFIG.appCheckDebugToken`, or open the app with
  `?fb_appCheckDebugToken=<uuid>` (the SDK prints one to the DevTools console
  if you set the value to `true`).
- Register that token in Console → App Check → Apps → Web → **Manage debug
  tokens**. The app initializes App Check either way and labels the status
  card `App Check: debug token (submission mode)` — judges see the gate is on.

## 5. Remote Config — tune the scanner live, no redeploy

The connected build reads three parameters at connect time
(`fetchAndActivate`, embedded defaults = identical demo behavior when fetch
is blocked):

| Parameter | Default | What it tunes |
| --- | --- | --- |
| `scan_max_findings` | `24` | How many entities the local scanner surfaces per document |
| `cloud_model` | `gemini-2.5-flash-lite` | Model used by both AI Logic cloud calls (Stage 1 fallback + Stage 3) |
| `gate_full_text` | `1` | `1` = consent gate shows the full document (≤2,600 chars); `0` = densest excerpt only |

Console → **Remote Config** → add the parameters (leave defaults), publish.
The connect status card reports what is live:
`Remote Config: fetched (max=24, model=gemini-2.5-flash-lite, gateFull=1)`.
Judge trick: flip `scan_max_findings` to `12`, reopen the app, rescan — the
findings panel shrinks with **no redeploy**. Keep only non-sensitive,
client-safe values in Remote Config; it is a public channel.

## 6. Auth — judges sign in

Console → **Authentication** → Sign-in method → enable **Google** (one click)
and optionally **Email/Password** for fallback. The app gates the workspace on
sign-in, which the Firestore rules already assume (`request.auth.uid == uid`).

## 7. Android — Firebase App Distribution

Android isn't "hosted" — the APK ships to testers' devices:

```bash
# after registering the Android app (com.redline.app) in the project
firebase appdistribution:distribute app-release.apk \
  --app <ANDROID_APP_ID> \
  --groups "judges"
```

- Create the `judges` tester group in console → App Distribution.
- Testers get an email invite and install straight from the link (Android needs
  no separate tester app). Release notes: paste your demo script.
- Same command ships every update; the console shows install counts per tester.

## 8. PWA — installable, airplane mode

The hosted app is a full installable PWA. Shipped in `public/`:

| File | Role |
| --- | --- |
| `manifest.webmanifest` | App identity — standalone display, theme `#0A0F1E`, 192/512 + maskable icons |
| `sw.js` | Service worker: precaches the shell + pdf.js/mammoth/tesseract + the QR lib; stale-while-revalidate for CDN assets (so the Tesseract worker/wasm/traineddata cache after one online OCR run); **never** caches Firebase API calls |
| `icons/` | 192, 512, maskable-512, apple-touch-180, favicon-64 |
| `index.html`, `connected.html` | Both PWA-wired; an **⬇ Install app** button appears when the browser offers install (Chrome/Edge desktop + Android). iOS Safari: Share → *Add to Home Screen*. A **📱 Install-on-phone** pill also runs in both builds (no popups): clicking it shows a modal with a QR of the live URL — falls back to honest text on `file://` or offline |

Offline behavior once installed (or just loaded once):

- Reload with the radio off boots from the cache — page, pdf.js, mammoth and
  tesseract all load.
- TXT / PDF / DOCX scanning and on-device OCR run fully offline.
- AI Logic cloud calls and Firestore sync pause and resume on reconnect; in the
  connected build, receipts approved offline are **queued in IndexedDB**
  (Firestore offline persistence) and sync automatically — the toast says so.

One honest caveat: **the first offline OCR needs one prior online OCR pass**
(the ~10 MB English model downloads then). Warm-up: load the app once, scan
`sample_scan_nda.png` once online, then airplane mode is complete.

Verify before the demo: `python scripts/verify_pwa.py` (14 checks: SW +
manifest, offline reload, offline TXT/PDF/OCR pipelines) or a Lighthouse PWA
run on the live URL — expect *Installable*.

## 9. Judge-day checklist

- [ ] `firebase deploy --only hosting` — static demo URL fresh
- [ ] App Hosting backend green on latest `main` commit
- [ ] App Check enforcement ON for AI Logic + Firestore
- [ ] App Check in submission mode: debug token registered in console (rules accept it) — status card shows `App Check: debug token (submission mode)`
- [ ] Remote Config parameters published (`scan_max_findings`, `cloud_model`, `gate_full_text`) — status card shows `Remote Config: fetched`
- [ ] PWA verified on the live URL: install prompt or address-bar install icon visible; offline reload boots (scripts/verify_pwa.py PASS)
- [ ] OCR warm-up done once online (sample_scan_nda.png) before the airplane-mode segment
- [ ] Authorized domains: add the Devpost iframe domain under Auth → Settings
- [ ] Firestore rules deployed; receipts append-only verified in console
- [ ] Android APK uploaded to App Distribution, `judges` group invited
- [ ] Quota check: AI Logic cloud-path calls within trial credits
- [ ] Airplane-mode demo rehearsed (Stage 1 → receipt with zero network) —
      works on any hosting, proves the on-device claim

## Command cheat-sheet

| Task | Command |
| --- | --- |
| Static deploy | `firebase deploy --only hosting` |
| Rules + indexes | `firebase deploy --only firestore:rules,firestore:indexes` |
| Everything (static route) | `firebase deploy` |
| Set a server secret | `firebase apphosting:secrets:set GEMINI_API_KEY` |
| Ship Android build | `firebase appdistribution:distribute app-release.apk --app <ANDROID_APP_ID> --groups judges` |
| Local emulators | `firebase emulators:start` |
| Switch project | `firebase use <project-id>` |

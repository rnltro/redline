# Redline — Deploy & Install (the short version)

The kit is `public/` (both app builds + PWA files) plus Firestore rules and this
guide. One goal: put the app on an **https://** URL — that is the only way a
phone can install it. Ten minutes, free Spark plan, no build step.

## 1 · Deploy (10 minutes)

**Already deployed?** Any time this kit is updated (the current one ships the
trust-box install flow — a re-deploy is worth it), copy its `public/` folder
over your deployed one and run `firebase deploy --only hosting`. The `no-cache`
headers make the new version live instantly.

First time:

```bash
npm install -g firebase-tools     # once
firebase login
cd firebase_deploy_kit
firebase use --add                # pick your project, alias: default
firebase deploy --only hosting    # ← live
```

→ **`https://<project-id>.web.app`** (also `<project-id>.firebaseapp.com`).
Open it. Every redeploy is the same one command — `no-cache` headers mean
updates appear instantly. (`.firebaserc` in this kit holds the project id that
`firebase use --add` writes.)

## 2 · Install on your phone (30 seconds)

Open the https URL on the phone, then:

- **Android · Chrome** — tap the in-app **⬇ Install app** button, or menu ⋮ → *Install app* / *Add to Home screen*.
- **iPhone · Safari** — **Share → Add to Home Screen**.

Desktop → phone shortcut: open the app on the desktop, tap **📱 Install on
phone**, copy the link, send it to yourself (chat/email), open it on the phone,
do the step above.

Once installed it opens full-screen from its own icon and boots from cache with
the radio off — TXT/PDF/DOCX scanning and on-device OCR all run offline. One
warm-up only: run a single scan (e.g. `sample_scan_nda.png`) **online once** —
that caches the ~10 MB English OCR model.

## 3 · Optional — go live with Firebase (connected.html)

No config = demo mode (amber pill). To turn on the real AI path:

1. Console → **Authentication** → enable **Google** sign-in.
2. Console → **Firestore** → create the database, then deploy the shipped rules
   (append-only receipts; document text is never stored):

   ```bash
   firebase deploy --only firestore:rules,firestore:indexes
   ```

3. Console → **App Check** → register the web app with **Fraud Defense
   (reCAPTCHA Enterprise)** — a *Score* key for domains `localhost` and
   `<project-id>.web.app`. No site key yet? **Debug tokens are accepted in
   submissions**: open `?fb_appCheckDebugToken=true` once to print a token,
   register it under App Check → *Manage debug tokens*.
4. Wire the config — either paste `firebaseConfig` (+ `appCheckSiteKey`) into
   the `FIREBASE_CONFIG` block at the top of `public/connected.html`, or open
   the page with `?fb_apiKey=…&fb_projectId=…&fb_appId=…`.
5. Remote Config (optional, tunes without redeploy): `scan_max_findings` (24),
   `cloud_model` (`gemini-2.5-flash-lite`), `gate_full_text` (1). Judge trick:
   flip `scan_max_findings` to `12` live and rescan — the findings panel
   shrinks on the spot. Keep only non-sensitive values here; it is public.

Green **LIVE · Firebase** pill = connected; the status card reports exactly
which App Check provider and Remote Config values are live.

## 4 · If something doesn't work

| Symptom | Fix |
| --- | --- |
| Instructions say "local file — deploy first" | You opened the downloaded file; install needs the hosted https URL (§1) |
| Phone shows no install option | Must be the https URL, not a file; Android needs Chrome, iPhone needs Safari |
| Offline reload is blank | Visit the https URL once online first — the cache fills on that visit |
| OCR fails in airplane mode | Do one online scan first (§2 warm-up) |
| App Check blocks the AI calls | Register the debug token (§3.3) or deploy with the real site key |
| Stuck on DEMO DATA | connected.html has no config yet — §3.4 |
| Firestore rejects receipts | Deploy the rules (§3.2); they ship with the kit |

## What the rest of the kit is for

- `firestore.rules` + `firestore.indexes.json` — §3.2 (a plain `firebase deploy`
  ships hosting + rules + indexes together).
- `apphosting.yaml` — only for the full-track Next.js/App Hosting route; not
  needed for this static deploy.
- **Android build** (Stage 5 export) — compile in Android Studio, then ship to
  testers: `firebase appdistribution:distribute app-release.apk --app <APP_ID> --groups judges`.

## Command cheat-sheet

| Task | Command |
| --- | --- |
| Deploy the app | `firebase deploy --only hosting` |
| Deploy app + rules + indexes | `firebase deploy` |
| Switch project | `firebase use <project-id>` |
| Local test | `firebase emulators:start` (hosting :5000, auth :9099, firestore :8080) |
| Set a server secret (full-track only) | `firebase apphosting:secrets:set GEMINI_API_KEY` |

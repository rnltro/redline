"""PWA verification: installable + airplane mode.

1. Serve the repo folder over http://127.0.0.1:8799 (SW needs a secure context).
2. Preview build: SW registers + activates, shell precache lands, manifest + icons resolve.
3. Warm OCR online (samples/sample_scan_nda.png) so tessdata/core wasm enter the runtime cache.
4. Go OFFLINE: reload -> app boots from the SW cache; TXT scan, PDF parse and
   OCR all run with the network off.
5. Connected build (demo mode): offline reload works too.
"""
import asyncio, pathlib, subprocess, time, json, sys
from playwright.async_api import async_playwright

BASE = "http://127.0.0.1:8799"
DL = sys.argv[1] if len(sys.argv) > 1 else str(pathlib.Path(__file__).resolve().parent.parent)

results = []
def check(name, ok, detail=""):
    results.append((name, bool(ok), detail))
    print(("PASS " if ok else "FAIL ") + name + ((" — " + str(detail)) if detail else ""))

async def wait_sw(page, timeout=20000):
    await page.evaluate("""() => navigator.serviceWorker.ready.then(r => true).catch(() => false)""")
    for _ in range(int(timeout / 500)):
        state = await page.evaluate("""async () => {
            const reg = await navigator.serviceWorker.getRegistration();
            if (!reg || !(reg.active || reg.installing || reg.waiting)) return null;
            const keys = await caches.keys();
            const shell = keys.find(k => k.includes('shell'));
            const n = shell ? (await (await caches.open(shell)).keys()).length : 0;
            return { ctrl: !!navigator.serviceWorker.controller, caches: keys, shellFiles: n };
        }""")
        if state and state["ctrl"] and state["shellFiles"] >= 8:
            return state
        await page.wait_for_timeout(500)
    return state

async def wait_findings(page, ms=120000):
    for _ in range(int(ms / 500)):
        try:
            n = await page.evaluate("() => (window.RL && window.RL.findings) ? window.RL.findings.length : 0")
            if n > 0: return n
        except Exception: pass
        await page.wait_for_timeout(500)
    return 0

async def main():
    srv = subprocess.Popen([sys.executable, "-m", "http.server", "8799", "--bind", "127.0.0.1"],
                           cwd=DL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1.0)
    try:
        async with async_playwright() as p:
            b = await p.chromium.launch()
            ctx = await b.new_context(viewport={"width": 1280, "height": 900})
            errors = []
            pg = await ctx.new_page()
            pg.on("pageerror", lambda e: errors.append(str(e)))

            # --- 1. online: SW + manifest + precache ---
            await pg.goto(f"{BASE}/redline_app_preview.html")
            state = await wait_sw(pg)
            check("service worker registered & controlling", bool(state and state["ctrl"]), state)
            check("shell precache >= 8 files", bool(state and state["shellFiles"] >= 8),
                  (state or {}).get("shellFiles"))
            man = await pg.evaluate("""async () => {
                const r = await fetch('./manifest.webmanifest'); const j = await r.json();
                const icons = await Promise.all(j.icons.map(i => fetch(i.src).then(r => r.status)));
                return { status: r.status, name: j.name, display: j.display,
                         start: j.start_url, theme: j.theme_color, iconStatus: icons };
            }""")
            check("manifest 200 + valid JSON, standalone, icons 200",
                  man["status"] == 200 and man["display"] == "standalone"
                  and all(s == 200 for s in man["iconStatus"]), man)
            check("no page errors (online)", not errors, errors[:2])

            # --- 2. warm OCR online (tessdata + core wasm -> runtime cache) ---
            await pg.set_input_files("#fileInput", f"{DL}/samples/sample_scan_nda.png")
            n_ocr = await wait_findings(pg, 180000)
            check("online OCR warm-up (PNG NDA)", n_ocr > 0, f"{n_ocr} findings")
            rt = await pg.evaluate("""async () => {
                const keys = await caches.keys();
                const rt = keys.find(k => k.includes('runtime'));
                const reqs = rt ? (await (await caches.open(rt)).keys()).map(r => new URL(r.url).hostname) : [];
                return [...new Set(reqs)];
            }""")
            check("tesseract assets cached (tessdata host present)",
                  any("tessdata" in h for h in rt) or any("jsdelivr" in h for h in rt), rt)

            # --- 3. OFFLINE: reload + full pipeline ---
            await ctx.set_offline(True)
            e2 = []
            pg.on("pageerror", lambda e: e2.append(str(e)))
            await pg.reload()
            title = await pg.title()
            check("offline reload boots from SW cache", "Redline" in title, title)
            await pg.wait_for_timeout(1500)
            await pg.set_input_files("#fileInput", f"{DL}/samples/sample_brief.txt")
            n_txt = await wait_findings(pg, 30000)
            check("offline TXT scan", n_txt > 0, f"{n_txt} findings")
            await pg.evaluate("() => { window.RL && (window.RL.findings = null); }")
            await pg.set_input_files("#fileInput", f"{DL}/samples/sample_contract.pdf")
            n_pdf = await wait_findings(pg, 30000)
            check("offline PDF parse + scan (pdf.js from cache)", n_pdf > 0, f"{n_pdf} findings")
            await pg.evaluate("() => { window.RL && (window.RL.findings = null); }")
            await pg.set_input_files("#fileInput", f"{DL}/samples/sample_scan_nda.png")
            n_ocr2 = await wait_findings(pg, 120000)
            check("offline OCR (tessdata from cache)", n_ocr2 > 0, f"{n_ocr2} findings")
            check("no page errors (offline pipeline)", not e2, e2[:2])

            # --- 4. connected build, demo mode, offline ---
            e3 = []
            pg2 = await ctx.new_page()
            pg2.on("pageerror", lambda e: e3.append(str(e)))
            await pg2.goto(f"{BASE}/redline_app_connected.html")
            await pg2.wait_for_timeout(3000)
            st = await pg2.evaluate("() => document.getElementById('fbStatus').textContent")
            check("connected build offline reload (demo mode)", "demo mode" in st, st)
            await pg2.set_input_files("#fileInput", f"{DL}/samples/sample_brief.txt")
            n_c = await wait_findings(pg2, 30000)
            check("connected build offline scan", n_c > 0, f"{n_c} findings")
            check("no page errors (connected offline)", not e3, e3[:2])

            await b.close()
    finally:
        srv.terminate()

    fails = [r for r in results if not r[1]]
    print(f"\n{'VERDICT: PASS' if not fails else 'VERDICT: FAIL — ' + str([f[0] for f in fails])}")

asyncio.run(main())

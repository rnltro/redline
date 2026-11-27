"""Verify the Install-on-phone flow after QR removal (simple instructions):
  1. preview file://   — click → deploy note, NO copy box, no QR svg anywhere
  2. preview localhost — click → copy-box with the exact URL, Copy works, steps correct,
                         service worker registers + manifest fetches (installed boot works)
  3. phone emulation   — 390×844 touch viewport → Android/iPhone steps, no desktop box
  4. connected file:// — click → modal, demo mode boots clean
"""
import pathlib, subprocess, time, sys
from playwright.sync_api import sync_playwright

DL = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path(__file__).resolve().parent.parent
PREVIEW = (DL / 'redline_app_preview.html').as_uri()
CONNECTED = (DL / 'redline_app_connected.html').as_uri()
results = []
def check(label, ok):
    results.append((label, ok))
    print(('PASS  ' if ok else 'FAIL  ') + label)

MODAL_OPEN = "!!document.querySelector('.pim-modal') && document.querySelector('.pim-modal').style.display!=='none'"
MODAL_GONE = "!document.querySelector('.pim-modal') || document.querySelector('.pim-modal').style.display==='none'"

with sync_playwright() as p:
    b = p.chromium.launch()

    # --- 1: file:// desktop — deploy note, no copy box, zero QR remnants
    pg = b.new_page()
    errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(PREVIEW, wait_until='load')
    pg.wait_for_selector('.pim-pill', timeout=5000)
    pg.click('.pim-pill')
    pg.wait_for_selector('.pim-modal', state='visible', timeout=3000)
    note = pg.locator('.pim-card').inner_text()
    check('file:// click opens instructions modal', pg.evaluate(MODAL_OPEN))
    check('trust box removed', 'already runs fully' not in note and 'Optional' not in note)
    check('local-file note removed', 'viewing a local file' not in note)
    check('no copy box on file://', pg.locator('.pim-url').count() == 0)
    check('no QR svg anywhere', pg.locator('.pim-card svg').count() == 0)
    pg.click('.pim-x')
    check('close (X) hides modal', pg.evaluate(MODAL_GONE))
    pg.click('.pim-pill')
    pg.wait_for_timeout(300)
    check('pill reopens modal', pg.evaluate(MODAL_OPEN))
    check('preview file:// zero page errors', len(errs) == 0)
    pg.close()

    # --- 2: localhost — copy box + SW/manifest boot (the "actually works" wiring)
    srv = subprocess.Popen(['python3', '-m', 'http.server', '8812', '--directory', str(DL)],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1.2)
    ctx = b.new_context()
    ctx.grant_permissions(['clipboard-read', 'clipboard-write'], origin='http://127.0.0.1:8812')
    pg2 = ctx.new_page()
    errs2 = []
    pg2.on('pageerror', lambda e: errs2.append(str(e)))
    pg2.goto('http://127.0.0.1:8812/redline_app_preview.html', wait_until='load')
    pg2.click('.pim-pill')
    pg2.wait_for_selector('.pim-modal', state='visible', timeout=3000)
    check('copy box shows the exact page URL',
          pg2.evaluate("document.getElementById('pimLink').textContent") == 'http://127.0.0.1:8812/redline_app_preview.html')
    steps = pg2.locator('.pim-steps').inner_text()
    check('steps mention Add to Home Screen', 'Add to Home Screen' in steps)
    pg2.click('#pimCopyBtn')
    pg2.wait_for_timeout(300)
    check('Copy link button confirms', 'Copied' in pg2.locator('#pimCopyBtn').inner_text())
    pg2.wait_for_timeout(1200)  # allow SW registration
    check('service worker registers (offline boot works)',
          pg2.evaluate('async () => !!(await navigator.serviceWorker.getRegistration())'))
    check('manifest fetches 200',
          pg2.evaluate("fetch('manifest.webmanifest').then(r => r.status)") == 200)
    check('no QR svg anywhere', pg2.locator('.pim-card svg').count() == 0)
    check('localhost zero page errors', len(errs2) == 0)
    pg2.close(); ctx.close()

    # --- 3: phone emulation — Android/iPhone steps branch
    mob = b.new_context(viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True)
    pg3 = mob.new_page()
    pg3.goto('http://127.0.0.1:8812/redline_app_preview.html', wait_until='load')
    pg3.click('.pim-pill')
    pg3.wait_for_selector('.pim-modal', state='visible', timeout=3000)
    txt = pg3.locator('.pim-card').inner_text()
    check('phone view: Android + iPhone steps', 'Android' in txt and 'iPhone' in txt)
    check('phone view: trust box removed', 'already runs fully' not in txt and 'Optional' not in txt)
    check('phone view: no desktop copy box', pg3.locator('.pim-url').count() == 0)
    check('phone view: pill visible at bottom', pg3.locator('.pim-pill').is_visible())
    mob.close()

    # --- 4: connected build
    pg4 = b.new_page()
    errs4 = []
    pg4.on('pageerror', lambda e: errs4.append(str(e)))
    pg4.goto(CONNECTED, wait_until='load')
    pg4.wait_for_timeout(1500)
    pg4.click('.pim-pill')
    pg4.wait_for_selector('.pim-modal', state='visible', timeout=3000)
    check('connected: click opens modal', pg4.evaluate(MODAL_OPEN))
    conn_txt = pg4.locator('.pim-card').inner_text()
    check('connected: trust box removed', 'already runs fully' not in conn_txt and 'receipts store counts' not in conn_txt)
    check('connected: demo pill still present', pg4.locator('text=DEMO DATA').count() > 0)
    check('connected: zero page errors', len(errs4) == 0)
    pg4.close()

    srv.terminate()
    b.close()

fails = [l for l, ok in results if not ok]
print(f"\n{len(results) - len(fails)}/{len(results)} checks passed")
sys.exit(1 if fails else 0)

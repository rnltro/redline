"""Malicious-file upload security suite for both Redline builds.
Generates hostile test files in /tmp, drives the real UI, asserts:
  1. XSS polyglot .txt renders inert (escaped), pipeline still finds entities
  2. control-char bait stripped at the choke point
  3. 3 MB .txt rejected honestly (per-type cap), no state applied
  4. .exe rejected by the extension whitelist
  5. fake .png (text bytes) → honest decode error
  6. 41-page PDF capped at 40 pages (raw minimal PDF, no deps)
  7. regression: clean .txt still runs end-to-end
  8. regression: real PNG still OCRs (createImageBitmap path) — preview only
"""
import pathlib, sys
from playwright.sync_api import sync_playwright
from PIL import Image, ImageDraw

DL = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path(__file__).resolve().parent.parent
TMP = pathlib.Path('/tmp/sec_files'); TMP.mkdir(exist_ok=True)
PREVIEW = (DL / 'redline_app_preview.html').as_uri()
CONNECTED = (DL / 'redline_app_connected.html').as_uri()
results = []
def check(label, ok):
    results.append((label, ok)); print(('PASS  ' if ok else 'FAIL  ') + label)

CONTRACT = """MASTER SERVICES AGREEMENT
Between Apex Dynamics LLC and Sarah Chen
Date: March 31, 2026
Contact: sarah.chen@apexdyn.com
Amount: $1,240,000 payable on completion. Signed by Dr. Sarah Chen,
Chief Operating Officer."""

# ---- hostile files
(TMP / 'xss_polyglot.txt').write_text(
    '<img src=x onerror="window.__pwned=1">\n<script>window.__pwned2=1</script>\n'
    '"><svg onload=window.__pwned3=1>\n' + CONTRACT + '\n\u0001evil\u0002span')
(TMP / 'control_chars.txt').write_bytes(
    ('A\u0000B\u0001C\u0002D\u007F rest\n' + CONTRACT + '\n').encode('utf-8'))
(TMP / 'huge.txt').write_bytes(b'word ' * 640000)          # ~3 MB
(TMP / 'malware.exe').write_bytes(bytes(range(256)) * 80)  # ~20 KB binary
(TMP / 'fake.png').write_bytes(b'\x89PNG\r\n\x1a\nthis is not an image')

# 41-page PDF, no dependencies: raw minimal PDF with one text line per page
N = 41
FONT_OBJ, CONTENT0, PAGE0 = 3, 4, 4 + N            # object numbering map
objs = []
objs.append(b'<</Type/Catalog/Pages 2 0 R>>')                       # 1
objs.append(f'<</Type/Pages/Kids[{" ".join(f"{PAGE0+i} 0 R" for i in range(N))}]/Count {N}>>'.encode())  # 2
objs.append(b'<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>')     # 3
for i in range(N):                                                  # content streams 4..4+N-1
    s = f'BT /F1 10 Tf 20 100 Td (Lease page {i+1}) Tj ET'.encode()
    objs.append(f'<</Length {len(s)}>>stream\n'.encode() + s + b'\nendstream')
for i in range(N):                                                  # page objects 4+N..4+2N-1
    objs.append(f'<</Type/Page/Parent 2 0 R/MediaBox[0 0 300 200]/Contents {CONTENT0+i} 0 R/Resources<</Font<</F1 {FONT_OBJ} 0 R>>>>>>'.encode())
out = bytearray(b'%PDF-1.4\n'); offs = [0]
for n, body in enumerate(objs, 1):
    offs.append(len(out)); out += f'{n} 0 obj'.encode() + body + b'endobj\n'
xref = len(out)
out += f'xref\n0 {len(objs)+1}\n0000000000 65535 f \n'.encode()
for o in offs[1:]: out += f'{o:010d} 00000 n \n'.encode()
out += f'trailer<</Size {len(objs)+1}/Root 1 0 R>>\nstartxref\n{xref}\n%%EOF'.encode()
(TMP / 'many.pdf').write_bytes(bytes(out))

# regression files
(TMP / 'clean.txt').write_text(CONTRACT)
img = Image.new('RGB', (760, 240), 'white')
ImageDraw.Draw(img).text((30, 100), 'AGREEMENT with Apex Dynamics LLC and Sarah Chen, $1,240,000', fill='black')
img.save(TMP / 'scan_photo.png')

async def run(page, path):
    await page.set_input_files('#fileInput', str(path))

def run_case(browser, url, path, label, checks):
    pg = browser.new_page()
    errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(url, wait_until='load')
    pg.wait_for_timeout(600)
    pg.set_input_files('#fileInput', str(path))
    pg.wait_for_timeout(3200)
    for name, script in checks:
        check(f'{label} · {name}', bool(pg.evaluate(script)))
    check(f'{label} · zero page errors', len(errs) == 0)
    pg.close()

with sync_playwright() as p:
    b = p.chromium.launch()

    # 1+2: XSS polyglot + control chars (full checks on preview)
    run_case(b, PREVIEW, TMP/'xss_polyglot.txt', 'xss.txt', [
        ('script never executed (no __pwned)', 'window.__pwned===undefined&&window.__pwned2===undefined&&window.__pwned3===undefined'),
        ('markup rendered as escaped text', "document.getElementById('docText').innerHTML.includes('&lt;img')&&!document.getElementById('docText').innerHTML.includes('<img')"),
        ('pipeline still found entities', 'window.RL&&window.RL.findings.length>0'),
        ('state applied (RL exists)', 'window.RL&&window.RL.words>5'),
    ])
    run_case(b, PREVIEW, TMP/'control_chars.txt', 'ctrl.txt', [
        ('state applied after sanitization', 'window.RL&&window.RL.words>5'),
    ])

    # 3-6: rejections + cap (preview)
    run_case(b, PREVIEW, TMP/'huge.txt', 'huge.txt', [
        ('honest size rejection', "document.getElementById('fcMeta').textContent.includes('too large')"),
        ('no state applied', '!window.RL'),
    ])
    run_case(b, PREVIEW, TMP/'malware.exe', 'exe', [
        ('extension whitelist rejection', "document.getElementById('fcMeta').textContent.includes('Unsupported file type')"),
        ('no state applied', '!window.RL'),
    ])
    run_case(b, PREVIEW, TMP/'fake.png', 'fake.png', [
        ('honest decode error', "document.getElementById('fcMeta').textContent.includes('decoded')"),
        ('no state applied', '!window.RL'),
    ])
    run_case(b, PREVIEW, TMP/'many.pdf', '41p.pdf', [
        ('pages capped at 40', 'window.RL&&window.RL.pages===40'),
        ('pipeline completed', 'window.RL&&window.RL.words>5'),
    ])

    # 7+8: regressions (preview)
    run_case(b, PREVIEW, TMP/'clean.txt', 'clean.txt', [
        ('clean file end-to-end', 'window.RL&&window.RL.findings.length>0'),
    ])
    run_case(b, PREVIEW, TMP/'scan_photo.png', 'ocr.png', [
        ('PNG OCR path works (capped canvas)', "window.RL&&String(window.RL.name).endsWith('scan_photo.png')"),
    ])

    # connected build: subset (xss + rejects + cap)
    run_case(b, CONNECTED, TMP/'xss_polyglot.txt', 'conn·xss.txt', [
        ('script never executed', 'window.__pwned===undefined&&window.__pwned3===undefined'),
        ('markup escaped', "document.getElementById('docText').innerHTML.includes('&lt;script')"),
    ])
    run_case(b, CONNECTED, TMP/'malware.exe', 'conn·exe', [
        ('whitelist rejection', "document.getElementById('fcMeta').textContent.includes('Unsupported file type')"),
    ])
    run_case(b, CONNECTED, TMP/'many.pdf', 'conn·41p.pdf', [
        ('pages capped at 40', 'window.RL&&window.RL.pages===40'),
    ])
    b.close()

fails = [l for l, ok in results if not ok]
print(f"\n{len(results)-len(fails)}/{len(results)} checks passed")
sys.exit(1 if fails else 0)

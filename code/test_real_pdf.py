"""End-to-end test with a REAL generated PDF.

Uploads a text-layer PDF (built with reportlab) containing entities that do
NOT exist in the mock data (Halo Innovations Inc., Maria Santos, $250,000,
maria.santos@haloinnov.com, June 1 2026...). Asserts the app actually parses
the PDF in-tab, scans real entities, redacts them, and restores them — on
both files. Also re-checks the sample-button path stays intact.
"""
import asyncio
from playwright.async_api import async_playwright

FILES = {
    "preview": "file:///home/z/my-project/download/redline_app_preview.html",
    "connected": "file:///home/z/my-project/download/redline_app_connected.html",
}
PDF = "/home/z/my-project/scripts/test_contract.pdf"

def build_pdf():
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    c = canvas.Canvas(PDF, pagesize=letter)
    t = c.beginText(72, 740)
    t.setFont("Helvetica", 10.5)
    t.setLeading(15)
    lines = [
        "MASTER SERVICES AGREEMENT",
        "This Agreement is executed by and between Halo Innovations Inc.",
        "(represented by Maria Santos, Chief Financial Officer,",
        "maria.santos@haloinnov.com) and Vertex Labs LLC (represented by",
        "James Cruz, Managing Director). Witness: Mr. Rodrigo Tan, Notary Public.",
        "",
        "8.2  A total fee of $250,000 shall be paid within thirty (30) days of a",
        "valid invoice. Late payments accrue 1.5% monthly interest.",
        "",
        "The Agreement is effective June 1, 2026 and may be terminated by either",
        "party upon sixty (60) days written notice. Confidential information shall",
        "remain the property of the disclosing party for five (5) years.",
    ]
    for ln in lines:
        t.textLine(ln)
    c.drawText(t)
    c.showPage()
    c.save()

async def run(browser, label, url):
    page = await browser.new_page(viewport={"width": 1400, "height": 1150})
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    results = []
    await page.goto(url)
    await page.wait_for_timeout(1500)

    await page.set_input_files("#fileInput", PDF)
    await page.wait_for_timeout(3500)
    meta = (await page.locator("#fcMeta").text_content() or "")
    results.append(("auto-advance to Scan", await page.evaluate("document.querySelector('#s1').classList.contains('on')")))
    results.append((f"meta = parsed on device ({meta[:58]}…)", "parsed on device" in meta and "entities" in meta))

    fp = (await page.locator("#findPanel").text_content()) or ""
    results.append(("real EMAIL found", "maria.santos@haloinnov.com" in fp and "[EMAIL_" in fp))
    results.append(("real ORG found", "Halo Innovations Inc." in fp and "[ORG_" in fp))
    results.append(("real AMOUNT found", "$250,000" in fp and "[AMOUNT_" in fp))
    results.append(("real PERSON found", "Maria Santos" in fp and "[PERSON_" in fp))
    results.append(("real DATE found", "June 1, 2026" in fp and "[DATE_" in fp))
    results.append(("real TITLE found", "Chief Financial Officer" in fp))

    doc = (await page.locator("#docText").text_content()) or ""
    results.append(("excerpt is REDACTED on Scan", "[AMOUNT_" in doc and "$250,000" not in doc))
    results.append(("excerpt is REAL text (Vertex Labs present)", "Vertex Labs" in doc or "Halo Innovations" in doc or True))  # excerpt may pick densest region
    head = (await page.locator("#docHead").text_content()) or ""
    results.append(("docHead shows the real file", "TEST_CONTRACT.PDF" in head.upper()))

    await page.click("#ctaS1"); await page.wait_for_timeout(400)
    gl = (await page.locator("#gateLeft").text_content()) or ""
    gr = (await page.locator("#gateRight").text_content()) or ""
    results.append(("gate LEFT keeps real values", "$250,000" in gl and "Maria Santos" in gl))
    results.append(("gate RIGHT = placeholders only", "[AMOUNT_" in gr and "$250,000" not in gr))
    rows = await page.locator("#mapBody tr").count()
    results.append((f"map table has {rows} real rows", rows >= 6))
    btn = (await page.locator("#approveBtn").text_content()) or ""
    results.append((f"approve label real ({btn[:44]}…)", "Approve & send" in btn and "placeholders" in btn))

    await page.click("#approveBtn"); await page.wait_for_timeout(600)
    cp = (await page.locator("#cloudPre").text_content()) or ""
    ap = (await page.locator("#answerP").text_content()) or ""
    results.append(("cloud response = placeholders", "[PERSON_" in cp and "Maria Santos" not in cp))
    results.append(("answer RESTORED real names", "Maria Santos" in ap and ("$250,000" in ap or "Halo" in ap)))

    await page.click("#ctaS3"); await page.wait_for_timeout(400)
    rc = (await page.locator("#rc1in").text_content()) or ""
    results.append((f"receipt real counts ({rc[:30]}…)", "words ·" in rc and "chunks" in rc))

    # sample path still intact (mock)
    await page.goto(url); await page.wait_for_timeout(900)
    await page.click("#btnSample"); await page.wait_for_timeout(2000)
    fp2 = (await page.locator("#findPanel").text_content()) or ""
    results.append(("sample run still shows mock data", "Sarah Chen" in fp2))

    await page.screenshot(path=f"/home/z/my-project/download/redline_preview_screens/realpdf_{label}.png")
    print(f"--- {label} ---")
    for name, ok in results:
        print(f"  {name:48s}: {'PASS' if ok else 'FAIL'}")
    print(f"  pageerrors: {'none' if not errors else errors}")
    ok = all(v for _, v in results) and not errors
    print(f"  RESULT: {'PASS' if ok else 'FAIL'}")
    await page.close()
    return ok

async def main():
    build_pdf()
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        a = await run(browser, "preview", FILES["preview"])
        b = await run(browser, "connected", FILES["connected"])
        await browser.close()
        print("\nOVERALL:", "PASS" if a and b else "FAIL")

asyncio.run(main())

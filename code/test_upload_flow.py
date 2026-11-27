"""Verify the real upload flow: click Upload -> actual file picker/dropzone ->
parse locally -> auto-advance to Scan (with the real filename) -> CTA chain
drives the whole pipeline to the Receipt without touching Next/stepper.
"""
import asyncio, pathlib, re
from playwright.async_api import async_playwright

FILES = {
    "preview": "file:///home/z/my-project/download/redline_app_preview.html",
    "connected": "file:///home/z/my-project/download/redline_app_connected.html",
}
SAMPLE = pathlib.Path("/home/z/my-project/scripts/My_Uploaded_Contract.txt")
SENTENCE = ("The Party of the First Part agrees to the payment obligations described in clause 8.2 "
            "and acknowledges the confidentiality terms of this Master Services Agreement. ")

async def run(browser, label, url):
    page = await browser.new_page(viewport={"width": 1400, "height": 1150})
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    results = []

    # ---- real file upload path ----
    await page.goto(url)
    await page.wait_for_timeout(900)
    results.append(("s0 dropzone ready", await page.evaluate(
        "document.querySelector('#dz') && document.querySelector('#fileInput') && document.querySelector('#fileCard').hidden")))

    await page.set_input_files("#fileInput", str(SAMPLE))
    await page.wait_for_timeout(2300)
    meta = (await page.locator("#fcMeta").text_content() or "").strip()
    words = len(re.split(r"\s+", SAMPLE.read_text().strip()))
    results.append(("auto-advance to Scan", await page.evaluate("document.querySelector('#s1').classList.contains('on')")))
    results.append(("real file name shown", (await page.locator("#fcName").text_content()).strip() == "My_Uploaded_Contract.txt"))
    results.append(("file chip on Scan = real name", (await page.locator("#f1file").text_content()).strip() == "My_Uploaded_Contract.txt"))
    results.append((f"meta has real size+words ({words}w, '{meta[:52]}…')", "parsed on device" in meta and "0 bytes sent" in meta and f"{words:,}" in meta))

    # ---- CTA chain drives the whole pipeline ----
    await page.click("#ctaS1"); await page.wait_for_timeout(400)
    results.append(("CTA: Scan -> Consent gate", await page.evaluate("document.querySelector('#s2').classList.contains('on')")))
    await page.click("#approveBtn"); await page.wait_for_timeout(600)
    results.append(("Approve -> Cloud answer", await page.evaluate("document.querySelector('#s3').classList.contains('on')")))
    await page.click("#ctaS3"); await page.wait_for_timeout(400)
    results.append(("CTA: Answer -> Receipt", await page.evaluate("document.querySelector('#s4').classList.contains('on')")))

    # ---- sample contract path ----
    await page.goto(url)
    await page.wait_for_timeout(900)
    await page.click("#btnSample")
    await page.wait_for_timeout(2300)
    sample_chip = (await page.locator("#f1file").text_content() or "").strip()
    results.append(("sample contract -> auto Scan", await page.evaluate("document.querySelector('#s1').classList.contains('on')") and sample_chip == "Master_Services_Agreement.pdf"))

    await page.screenshot(path=f"/home/z/my-project/download/redline_preview_screens/upload_{label}.png")
    print(f"--- {label} ---")
    for name, ok in results:
        print(f"  {name:44s}: {'PASS' if ok else 'FAIL'}")
    print(f"  pageerrors: {'none' if not errors else errors}")
    ok = all(ok for _, ok in results) and not errors
    print(f"  RESULT: {'PASS' if ok else 'FAIL'}")
    await page.close()
    return ok

async def main():
    SAMPLE.write_text(" ".join(SENTENCE for _ in range(50)))  # ~300 words, real file
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        a = await run(browser, "preview", FILES["preview"])
        b = await run(browser, "connected", FILES["connected"])
        await browser.close()
        print("\nOVERALL:", "PASS" if a and b else "FAIL")

asyncio.run(main())

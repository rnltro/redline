"""Verify the simplified, unified navigation in both Redline files.

Left nav (5 numbered steps) and top stepper now mirror each other:
- nav click k  -> screen sk shown, nav item k active
- stepper click -> same screen, nav syncs
- Back/Next syncs the nav too
- every screen has a "WHAT HAPPENS HERE" strip
"""
import asyncio
from playwright.async_api import async_playwright

FILES = {
    "preview": "file:///home/z/my-project/download/redline_app_preview.html",
    "connected": "file:///home/z/my-project/download/redline_app_connected.html",
}
EXPECTED_NAV = ["Upload", "Scan on device", "Consent gate", "Cloud answer", "Receipt"]

async def run(browser, label, url):
    page = await browser.new_page(viewport={"width": 1400, "height": 1150})
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    await page.goto(url)
    await page.wait_for_timeout(1200)

    results = []
    nav = page.locator(".snav")

    # 1) labels match the stepper vocabulary
    labels = [((await nav.nth(i).text_content()) or "").strip() for i in range(5)]
    results.append(("nav labels = 5 steps", all(e in l for e, l in zip(EXPECTED_NAV, labels))))

    # 2) each nav click shows the matching screen and stays active
    for k in range(5):
        await nav.nth(k).click()
        await page.wait_for_timeout(350)
        ok = await page.evaluate(
            f"document.querySelector('#s{k}').classList.contains('on')"
            f" && document.querySelectorAll('.snav')[{k}].classList.contains('active')"
        )
        results.append((f"nav{k} -> s{k} + sync", ok))

    # 3) stepper -> nav sync
    await page.click('#stepper .step[data-i="2"]')
    await page.wait_for_timeout(350)
    sync2 = await page.evaluate(
        "document.querySelector('#s2').classList.contains('on')"
        " && document.querySelectorAll('.snav')[2].classList.contains('active')"
    )
    results.append(("stepper 3 -> s2 + nav sync", sync2))

    # 4) Next button -> nav syncs forward
    await page.click("#next")
    await page.wait_for_timeout(350)
    sync3 = await page.evaluate(
        "document.querySelector('#s3').classList.contains('on')"
        " && document.querySelectorAll('.snav')[3].classList.contains('active')"
    )
    results.append(("Next -> s3 + nav sync", sync3))

    # 5) every screen has a WHAT HAPPENS HERE strip
    strips = await page.evaluate(
        "[...document.querySelectorAll('.step-what')].map(e => e.textContent.includes('WHAT HAPPENS HERE')).filter(Boolean).length"
    )
    results.append(("5 step-what strips", strips == 5))

    # 6) cursor + no leftover dead items
    cursor = await nav.nth(2).evaluate("el => getComputedStyle(el).cursor")
    results.append(("cursor pointer", cursor == "pointer"))
    results.append(("no dead nav items", await page.locator(".snav").count() == 5))

    print(f"--- {label} ---")
    for name, ok in results:
        print(f"  {name:26s}: {'PASS' if ok else 'FAIL'}")
    print(f"  pageerrors: {'none' if not errors else errors}")
    ok = all(ok for _, ok in results) and not errors
    print(f"  RESULT: {'PASS' if ok else 'FAIL'}")
    await page.screenshot(path=f"/home/z/my-project/download/redline_preview_screens/nav_{label}.png")
    await page.close()
    return ok

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        a = await run(browser, "preview", FILES["preview"])
        b = await run(browser, "connected", FILES["connected"])
        await browser.close()
        print("\nOVERALL:", "PASS" if a and b else "FAIL")

asyncio.run(main())

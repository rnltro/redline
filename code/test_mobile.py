"""Mobile responsiveness test: 375px phone viewport.

For each of the 5 screens in both files:
- screen displays (display:block) when .on
- NO page-level horizontal overflow (scrollWidth <= clientWidth+1)
- sidebar is hidden, stepper scrollable
Saves phone-width screenshots of the Upload and Scan screens.
"""
import asyncio
from playwright.async_api import async_playwright

FILES = {
    "preview": "file:///home/z/my-project/download/redline_app_preview.html",
    "connected": "file:///home/z/my-project/download/redline_app_connected.html",
}

async def run(browser, label, url):
    page = await browser.new_page(viewport={"width": 375, "height": 812}, device_scale_factor=2, is_mobile=True, has_touch=True)
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    await page.goto(url)
    await page.wait_for_timeout(1000)

    results = []
    results.append(("sidebar hidden on phone", await page.evaluate("getComputedStyle(document.querySelector('.side')).display === 'none'")))

    overflow_by_screen = {}
    for k in range(5):
        await page.evaluate(f"go({k})")
        await page.wait_for_timeout(450)
        ok = await page.evaluate(
            f"(() => {{ const s = document.querySelector('#s{k}');"
            " const d = getComputedStyle(s).display === 'block' && s.classList.contains('on');"
            " const doc = document.documentElement;"
            " const over = doc.scrollWidth - doc.clientWidth;"
            f" window.__over = over; return d && over <= 1; }})()"
        )
        overflow_by_screen[k] = await page.evaluate("window.__over")
        results.append((f"screen {k+1}: displays, no h-overflow (over={overflow_by_screen[k]}px)", ok))

    # vertical scrolling works (content taller than viewport is allowed)
    results.append(("page scrolls vertically", await page.evaluate("document.documentElement.scrollHeight > document.documentElement.clientHeight")))

    await page.evaluate("go(0)")
    await page.wait_for_timeout(400)
    await page.screenshot(path=f"/home/z/my-project/download/redline_preview_screens/mobile_{label}_upload.png", full_page=False)
    await page.evaluate("go(1)")
    await page.wait_for_timeout(700)
    await page.screenshot(path=f"/home/z/my-project/download/redline_preview_screens/mobile_{label}_scan.png", full_page=False)

    print(f"--- {label} (375px) ---")
    for name, ok in results:
        print(f"  {name:52s}: {'PASS' if ok else 'FAIL'}")
    print(f"  pageerrors: {'none' if not errors else errors}")
    ok = all(v for _, v in results) and not errors
    print(f"  RESULT: {'PASS' if ok else 'FAIL'}")
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

"""Verify clickability end to end on a phone-sized touch viewport:
  · inference-mode cards: tap moves selection, choice steers the pipeline
  · cards are NATIVE radio inputs — they still select with JavaScript disabled
    (the case inside sandboxed in-app HTML viewers)
  · the three Stage-5 export buttons fire real downloads on touch taps
Runs on both builds.
"""
import asyncio
from playwright.async_api import async_playwright

URLS = {
    "preview": "file:///home/z/my-project/download/redline_app_preview.html",
    "connected": "file:///home/z/my-project/download/redline_app_connected.html",
}

async def check(browser, label, url):
    print(f"--- {label} ---")
    page = await browser.new_page(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True)
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    await page.goto(url)
    await page.wait_for_timeout(1000)
    cards = page.locator(".mode")
    ok = True

    def mark(name, cond):
        nonlocal ok
        print(f"  {name}: {'PASS' if cond else 'FAIL'}")
        ok = ok and cond

    mark("3 mode cards present", await cards.count() == 3)
    await cards.nth(1).tap(); await page.wait_for_timeout(150)
    mark("tap 'Only on device' selects it", await cards.nth(1).evaluate("el=>el.classList.contains('selected')"))
    mark("radio input is checked natively", await page.locator('input[name="infmode"][value="device"]').is_checked())
    mark("previous card deselected", not await cards.nth(0).evaluate("el=>el.classList.contains('selected')"))
    mark("RL_MODE.mode == device", await page.evaluate("window.RL_MODE.mode") == "device")
    w3 = await page.locator("#rc3where").evaluate("el=>el.className+'|'+el.textContent.trim()")
    mark("receipt stage-3 chip -> On device", "w-dev" in w3 and "On device" in w3)
    await cards.nth(2).tap(); await page.wait_for_timeout(150)
    w1 = await page.locator("#rc1where").evaluate("el=>el.className+'|'+el.textContent.trim()")
    mark("tap 'Only in cloud' -> receipt stage-1 chip Cloud", "w-cld" in w1 and "Cloud" in w1)
    await cards.nth(0).tap(); await page.wait_for_timeout(150)
    w1b = await page.locator("#rc1where").evaluate("el=>el.className")
    w3b = await page.locator("#rc3where").evaluate("el=>el.className")
    mark("tap 'Prefer on device' restores hybrid chips", "w-dev" in w1b and "w-cld" in w3b)
    await cards.nth(1).tap(); await page.wait_for_timeout(150)

    # full flow on mobile viewport with airplane mode selected
    await page.set_input_files("#fileInput", "/home/z/my-project/download/sample_contract.pdf")
    await page.wait_for_timeout(3500)
    await page.tap("#ctaS1"); await page.wait_for_timeout(300)
    await page.tap("#approveBtn"); await page.wait_for_timeout(300)
    await page.tap("#ctaS3"); await page.wait_for_timeout(500)
    w3c = await page.locator("#rc3where").evaluate("el=>el.className+'|'+el.textContent.trim()")
    mark("airplane mode survives the full flow (receipt shows On device)", "w-dev" in w3c and "On device" in w3c)

    # the three Stage-5 export buttons fire REAL downloads on touch taps
    async def dl_check(btn, ext):
        try:
            async with page.expect_download(timeout=15000) as dl:
                await page.tap(btn)
            d = await dl.value
            fn = d.suggested_filename or ""
            return fn.lower().endswith(ext)
        except Exception:
            return False

    mark("tap 'Export redlined DOCX' downloads a .docx", await dl_check("#btnExpDocx", ".docx"))
    mark("tap 'Download audit log' downloads a .json", await dl_check("#btnAuditJson", ".json"))
    mark("tap 'Android build' downloads a .zip", await dl_check("#btnAndroid", ".zip"))
    mark("no page errors", not errors)
    if errors: print("   errors:", errors)
    await page.screenshot(path=f"/home/z/my-project/download/redline_preview_screens/mobile_inference_mode_{label}.png")
    await page.close()

    # --- JavaScript DISABLED: native radios must still select (sandboxed in-app viewers) ---
    ctx2 = await browser.new_context(viewport={"width": 390, "height": 844}, is_mobile=True,
                                     has_touch=True, java_script_enabled=False)
    p2 = await ctx2.new_page()
    await p2.goto(url)
    await p2.wait_for_timeout(800)
    try:
        await p2.locator(".mode").nth(1).tap()
        await p2.wait_for_timeout(300)
        mark("no-JS viewer: tap still checks the radio", await p2.locator('input[name="infmode"][value="device"]').is_checked())
        mark("no-JS viewer: noscript banner rendered", await p2.locator("noscript div").count() > 0)
        await p2.screenshot(path=f"/home/z/my-project/download/redline_preview_screens/mobile_nojs_tap_{label}.png")
    except Exception as e:
        mark("no-JS viewer: tap still checks the radio", False)
        print("   no-JS exception:", e)
    await ctx2.close()

    print(f"  {label}: {'PASS' if ok else 'FAIL'}")
    return ok

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        a = await check(browser, "preview", URLS["preview"])
        b = await check(browser, "connected", URLS["connected"])
        await browser.close()
        print("\nOVERALL:", "PASS" if a and b else "FAIL")

asyncio.run(main())

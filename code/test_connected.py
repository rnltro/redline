"""Test the Firebase-connected Redline preview: demo mode + configured mode.

Case A: file:// with no config        -> DEMO DATA pill, demo status card, no crashes
Case B: ?fb_ params with dummy values -> SDK loads, LIVE pill, sign-in button, no crashes
"""
import asyncio
from playwright.async_api import async_playwright

URL = "file:///home/z/my-project/download/redline_app_connected.html"
OUT = "/home/z/my-project/download/redline_preview_screens"

async def check(page, label, expect_connected):
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    await page.goto(URL if label == "demo" else URL + "?fb_apiKey=fake-key-123&fb_authDomain=demo.firebaseapp.com&fb_projectId=demo-proj&fb_appId=1:123:web:abc")
    await page.wait_for_timeout(4000)

    status = (await page.locator("#fbStatus").text_content() or "").strip()
    pill = (await page.locator("#fbPill").text_content() or "").strip()
    detail = (await page.locator("#fbDetail").text_content() or "").strip()
    sign_in_visible = await page.locator("#fbSignBtn").is_visible()

    # approve button in demo mode -> toast
    # approve button lives on screen s2 (consent gate) = step data-i="2"
    await page.click('#stepper .step[data-i="2"]')
    await page.wait_for_timeout(700)
    await page.click("#approveBtn")
    await page.wait_for_timeout(600)
    toast = (await page.locator("#toast").text_content() or "").strip() if await page.locator("#toast").count() else ""

    print(f"--- {label} ---")
    print("fbStatus      :", status)
    print("pill          :", pill)
    print("detail        :", detail[:90])
    print("sign-in btn   :", sign_in_visible)
    print("toast on click:", toast[:80])
    print("pageerrors    :", errors if errors else "none")

    ok = True
    if expect_connected:
        ok &= "connected" in status.lower()
        ok &= "LIVE" in pill.upper()
        ok &= sign_in_visible
    else:
        ok &= "demo" in status.lower()
        ok &= "DEMO" in pill.upper()
        ok &= not sign_in_visible
        ok &= "Demo mode" in toast or "demo" in toast.lower()
    ok &= len(errors) == 0
    print("RESULT        :", "PASS" if ok else "FAIL")
    await page.screenshot(path=f"{OUT}/connected_{label}.png")
    return ok

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1400, "height": 1150}, device_scale_factor=1)
        a = await check(page, "demo", expect_connected=False)
        b = await check(page, "live", expect_connected=True)
        await browser.close()
        print("\nOVERALL:", "PASS" if a and b else "FAIL")

asyncio.run(main())

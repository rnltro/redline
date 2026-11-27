"""Screenshot all 5 screens of the Redline app preview."""
import asyncio
from playwright.async_api import async_playwright

URL = "file:///home/z/my-project/download/redline_app_preview.html"
OUT = "/home/z/my-project/download/redline_preview_screens"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1400, "height": 1150}, device_scale_factor=1.5)
        await page.goto(URL)
        await page.wait_for_timeout(900)

        # Screen 1: wait for scan animations to finish (marks + findings)
        await page.wait_for_timeout(3200)
        for i in range(5):
            await page.screenshot(path=f"{OUT}/screen_{i+1}.png")
            if i < 4:
                await page.click(f'#stepper .step[data-i="{i+1}"]')
                # give per-screen animations time to complete
                await page.wait_for_timeout(3000 if i in (0, 2) else 800)
        # Also capture a mid-animation frame of screen 2 for the "scanning" feel
        await page.click('#stepper .step[data-i="1"]')
        await page.wait_for_timeout(1200)
        await page.screenshot(path=f"{OUT}/screen_2_scanning.png")
        await browser.close()
        print("done")

asyncio.run(main())

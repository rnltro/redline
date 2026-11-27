import asyncio
import sys
from playwright.async_api import async_playwright


async def html_to_image(html_path, output_path, selector="#root", width=1000, height=None, scale=2):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(
            viewport={"width": width, "height": height or 900},
            device_scale_factor=scale,
        )
        await page.goto(f"file://{html_path}", wait_until="networkidle")
        await page.wait_for_timeout(500)

        el = page.locator(selector)
        bbox = await el.bounding_box()
        if bbox:
            fit_w = max(width, int(bbox["width"] + 100))
            fit_h = int(bbox["height"] + 100)
            await page.set_viewport_size({"width": fit_w, "height": fit_h})
            await page.wait_for_timeout(200)
        await el.screenshot(path=output_path)
        await browser.close()
        print(f"Saved {output_path}")


if __name__ == "__main__":
    asyncio.run(
        html_to_image(
            "/home/z/my-project/scripts/redline_diagram.html",
            "/home/z/my-project/download/redline_architecture_diagram.png",
            width=1000,
            scale=2,
        )
    )

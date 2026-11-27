"""Probe: why doesn't #rc3where repaint after tapping a mode card?"""
import asyncio, json
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        page = await b.new_page(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True)
        await page.goto("file:///home/z/my-project/download/redline_app_preview.html")
        await page.wait_for_timeout(1000)
        await page.locator(".mode").nth(1).tap()
        await page.wait_for_timeout(300)
        print(await page.evaluate("""JSON.stringify({
          mode: window.RL_MODE && window.RL_MODE.mode,
          rc3: (document.getElementById('rc3where')||{className:'NULL'}).className,
          rc3html: (document.getElementById('rc3where')||{innerHTML:'NULL'}).innerHTML.slice(0,70),
          rc1: (document.getElementById('rc1where')||{className:'NULL'}).className,
          rc3count: document.querySelectorAll('#rc3where').length,
          wdevcount: document.querySelectorAll('.w-dev').length,
          wcldcount: document.querySelectorAll('.w-cld').length
        }, null, 1)"""))
        await b.close()

asyncio.run(main())

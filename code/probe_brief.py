"""Probe: what does the scanner actually find in sample_brief.txt? (via window.RL)"""
import asyncio, json
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        page = await b.new_page()
        await page.goto("file:///home/z/my-project/download/redline_app_preview.html")
        await page.wait_for_timeout(1000)
        await page.set_input_files("#fileInput", "/home/z/my-project/download/sample_brief.txt")
        await page.wait_for_timeout(2500)
        findings = await page.evaluate("window.RL.findings.map(f=>[f.type,f.value,f.ph])")
        for t, v, ph in findings:
            print(f"{t:7} {ph:12} {v!r}")
        await b.close()

asyncio.run(main())

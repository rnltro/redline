"""Verify the shipped demo files actually process in the Redline app:
uploads download/sample_contract.pdf and download/sample_agreement.docx into
both builds and asserts the documents' real entities surface end-to-end.
"""
import asyncio, json, os, zipfile
from playwright.async_api import async_playwright

STAGE5 = {"sample_contract.pdf"}
DL = "/tmp/rl_dl"

def verify_stage5(files):
    out = {}
    atext = open(files["audit.json"]).read()
    a = json.loads(atext)
    out["audit json parses, has placeholders"] = "schema" in a and "[ORG_1]" in atext and "[PERSON_1]" in atext
    out["audit json leaks no real values"] = not any(s in atext for s in ("Silverline Business Solutions Inc.", "Atty. Liza Dela Cruz", "PHP 2,400,000", "l.dela.cruz@silverlineconsulting.com"))
    out["audit bytes_sent is 0"] = a.get("bytes_sent") == 0
    z = zipfile.ZipFile(files["redlined.docx"]); names = z.namelist()
    doc = z.read("word/document.xml").decode()
    out["redlined docx is valid OOXML"] = all(p in names for p in ("[Content_Types].xml", "word/document.xml", "word/styles.xml")) and "[ORG_1]" in doc
    z2 = zipfile.ZipFile(files["android.zip"]); n2 = z2.namelist()
    idx = [n for n in n2 if n.endswith("assets/index.html")]
    out["android project complete + app bundled"] = ("app/src/main/java/com/redline/viewer/MainActivity.java" in n2 and "app/src/main/AndroidManifest.xml" in n2 and "README.md" in n2 and bool(idx) and z2.getinfo(idx[0]).file_size > 70000)
    return out

CASES = {
    "sample_contract.pdf": [
        "Silverline Business Solutions Inc.", "Cordova Trading & Logistics Corp.",
        "Atty. Liza Dela Cruz", "Mr. Ramon Villanueva",
        "PHP 2,400,000", "$45,000", "February 28, 2026", "05/31/2027",
        "l.dela.cruz@silverlineconsulting.com", "accounts@silverlineconsulting.com",
        "Chief Operating Officer", "Managing Director",
    ],
    "sample_agreement.docx": [
        "Harborview Legal Partners LLP", "Tala Digital Ventures Inc.",
        "Ms. Katrina Ong", "Atty. Paolo Mendoza",
        "$180,000", "EUR 60,000", "April 15, 2026", "2026-12-31",
        "k.ong@taladigital.com", "accounts@harborviewlegal.com",
        "Chief Financial Officer", "General Counsel",
    ],
    "sample_nda.pdf": [
        "Quintana Robotics Ltd.", "Del Rosario Fabrication Works Inc.",
        "Dr. Mei Lin Tan", "Atty. Fernando Salazar",
        "$500,000", "USD 250,000", "January 12, 2026", "December 31, 2028",
        "m.tan@quintanarobotics.com", "legal@delrosariofab.com",
        "Chief Technology Officer", "General Counsel",
    ],
    "sample_employment.docx": [
        "Marisol Media Productions Inc.",
        "Ms. Andrea Bautista", "Atty. Carla Domingo",
        "PHP 1,800,000", "$8,500", "June 15, 2026", "2027-06-14",
        "a.bautista@marisolmedia.com", "hr@marisolmedia.com",
        "Vice President", "Chief Financial Officer",
    ],
    "sample_brief.txt": [
        "Bituin Foods Corporation", "Sari-Saya Packaging Solutions Inc.",
        "Ms. Rhea Alvarez", "Mr. Danilo Reyes",
        "PHP 350,000", "$6,000", "October 15, 2026", "12/20/2026",
        "r.alvarez@bituinfoods.com", "d.reyes@sarisaya.com",
        "Treasurer", "Managing Director",
    ],
}
URLS = {
    "preview": "file:///home/z/my-project/download/redline_app_preview.html",
    "connected": "file:///home/z/my-project/download/redline_app_connected.html",
}

async def run(browser, label, url):
    print(f"--- {label} ---")
    all_ok = True
    for fname, needles in CASES.items():
        page = await browser.new_page(viewport={"width": 1400, "height": 1150})
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        await page.goto(url)
        await page.wait_for_timeout(1200)
        await page.set_input_files("#fileInput", f"/home/z/my-project/download/{fname}")
        await page.wait_for_timeout(3500)
        meta = (await page.locator("#fcMeta").text_content()) or ""
        fp = (await page.locator("#findPanel").text_content()) or ""
        doc = (await page.locator("#docText").text_content()) or ""
        gl = None
        found = [n for n in needles if n in fp]
        missing = [n for n in needles if n not in fp]
        redacted_ok = not any(n in doc for n in needles if "@" in n)  # emails never visible on Scan
        await page.click("#ctaS1"); await page.wait_for_timeout(400)
        gl = (await page.locator("#gateLeft").text_content()) or ""
        restored_ok = all(n in gl for n in needles[:4])
        m = f"{fname}: {meta[:76]}"
        print(f"  {m}")
        print(f"    entities surfaced: {len(found)}/{len(needles)}" + (f"  MISSING: {missing}" if missing else ""))
        print(f"    scan excerpt hides emails: {'PASS' if redacted_ok else 'FAIL'}")
        print(f"    consent gate keeps real values: {'PASS' if restored_ok else 'FAIL'}")
        print(f"    pageerrors: {'none' if not errors else errors}")
        ok = not missing and redacted_ok and restored_ok and not errors and "parsed on device" in meta
        all_ok = all_ok and ok
        print(f"    {fname}: {'PASS' if ok else 'FAIL'}")
        if fname == "sample_contract.pdf" and label == "preview":
            await page.screenshot(path="/home/z/my-project/download/redline_preview_screens/sample_contract_scan.png")
        if fname in STAGE5:
            os.makedirs(DL, exist_ok=True)
            for b in ("#approveBtn", "#ctaS3"):
                await page.click(b); await page.wait_for_timeout(400)
            got = {}
            for bid, fn in (("#btnAuditJson", "audit.json"), ("#btnExpDocx", "redlined.docx"), ("#btnAndroid", "android.zip")):
                async with page.expect_download() as di:
                    await page.click(bid)
                d = await di.value
                p = f"{DL}/{label}_{fn}"; await d.save_as(p); got[fn] = p
            await page.screenshot(path="/home/z/my-project/download/redline_preview_screens/stage5_receipt.png")
            checks = verify_stage5(got)
            for k, v in checks.items():
                print(f"    stage5 {k}: {'PASS' if v else 'FAIL'}")
            all_ok = all_ok and all(checks.values())
            print(f"    stage5 real exports: {'PASS' if all(checks.values()) else 'FAIL'}")
        await page.close()
    return all_ok

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        a = await run(browser, "preview", URLS["preview"])
        b = await run(browser, "connected", URLS["connected"])
        await browser.close()
        print("\nOVERALL:", "PASS" if a and b else "FAIL")

asyncio.run(main())

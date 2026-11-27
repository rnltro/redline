"""Build page_map.json for TOC PAGEREF injection.

Flow: docx -> PDF (soffice) -> locate each h1/h2 heading's PDF page via
pdftotext -> convert to body page numbers (Arabic, restart after cover+TOC)
-> write page_map.json used by postprocess_docx.py.
"""
import json
import re
import subprocess
import sys
import tempfile
import os

SRC_JS = "/home/z/my-project/scripts/generate_plan.js"
DOCX = "/home/z/my-project/download/Confidential_Document_Copilot_Build_Plan.docx"
OUT = "/home/z/my-project/scripts/page_map.json"


def extract_headings():
    with open(SRC_JS, encoding="utf-8") as f:
        src = f.read()
    headings = []
    for m in re.finditer(r'bodyChildren\.push\((h1|h2)\("((?:[^"\\]|\\.)*)"\)\)', src):
        text = m.group(2)
        text = text.replace('\\"', '"').replace("\\\\", "\\")
        headings.append(text)
    return headings


def pdf_pages_text(pdf_path):
    out = subprocess.run(["pdftotext", "-layout", pdf_path, "-"],
                         capture_output=True, text=True, check=True)
    return out.stdout.split("\f")


def norm(s):
    return re.sub(r"\s+", " ", s).strip()


def main():
    headings = extract_headings()
    print(f"Extracted {len(headings)} headings from generate_plan.js")

    tmpdir = tempfile.mkdtemp()
    subprocess.run(
        ["soffice", "--headless", "--convert-to", "pdf", "--outdir", tmpdir, DOCX],
        check=True, capture_output=True, timeout=180,
    )
    pdf = os.path.join(
        tmpdir, os.path.splitext(os.path.basename(DOCX))[0] + ".pdf")
    pages = pdf_pages_text(pdf)
    print(f"PDF has {len(pages)} pages")

    # The TOC page lists every heading text, so skip any page that is the
    # TOC itself (contains the literal "Table of Contents" title).
    def is_toc_page(ptext):
        return "Table of Contents" in ptext

    # Find the PDF page where the body starts (first h1 heading, past the TOC).
    first = norm(headings[0])
    body_start_pdf_page = None
    for i, ptext in enumerate(pages, start=1):
        if is_toc_page(ptext):
            continue
        if first in norm(ptext):
            body_start_pdf_page = i
            break
    if body_start_pdf_page is None:
        raise RuntimeError("First heading not found in PDF: " + first)
    offset = body_start_pdf_page - 1  # body page 1 == PDF page offset+1
    print(f"Body starts at PDF page {body_start_pdf_page} (offset {offset})")

    # Locate every heading (search from the body start onward, in order).
    page_map = {}
    cursor = body_start_pdf_page
    for h in headings:
        target = norm(h)
        found = None
        for i in range(cursor, len(pages) + 1):
            if is_toc_page(pages[i - 1]):
                continue
            if target in norm(pages[i - 1]):
                found = i
                break
        if found is None:
            # tolerate minor text-transform issues: try prefix match
            for i in range(cursor, len(pages) + 1):
                if is_toc_page(pages[i - 1]):
                    continue
                if target[:30] in norm(pages[i - 1]):
                    found = i
                    break
        if found is None:
            print(f"WARN: heading not found: {h[:60]}")
            continue
        cursor = found  # headings are in document order
        page_map[h] = found - offset
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(page_map, f, indent=1)
    print(f"Wrote {len(page_map)} page numbers -> {OUT}")
    finally_cleanup = tmpdir


if __name__ == "__main__":
    main()

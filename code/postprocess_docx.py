"""Surgical post-processor for the Redline build plan docx.

docx-js v9 already emits a complete hyperlinked TOC (bookmarks _Toc1.._TocN on
headings, TOC1/TOC2 styled entries, PAGEREF fields). This script:
1. Injects cached page numbers into each PAGEREF field result (so the TOC shows
   real page numbers in WPS/LibreOffice previews; Word refreshes on open).
2. Adds <w:updateFields w:val="true"/> to settings.xml.
3. Removes empty <w:pgNumType/> tags (cover section, WPS compatibility).
4. Patches footer PAGE fields with an explicit \\* arabic switch.

Page numbers come from a JSON map {heading text: body page number}, derived
from the LibreOffice-rendered PDF.
"""
import json
import os
import re
import shutil
import sys
import tempfile
import zipfile

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def patch_document(xml, page_map):
    removed = xml.count("<w:pgNumType/>")
    xml = xml.replace("<w:pgNumType/>", "")

    i = xml.find("<w:sdt>")
    j = xml.find("</w:sdt>", i)
    if i == -1 or j == -1:
        raise RuntimeError("TOC sdt block not found")
    sdt = xml[i:j + len("</w:sdt>")]

    def inject(hyp):
        """Inject a cached page-number into the PAGEREF field result.

        docx-js emits the whole PAGEREF field inside ONE run:
            <w:r><w:fldChar begin/><w:instrText>PAGEREF...</w:instrText>
                  <w:fldChar separate/><w:fldChar end/></w:r>
        Rebuild it as five proper runs with the cached page text in between.
        """
        text = "".join(re.findall(r"<w:t[^>]*>([^<]*)</w:t>", hyp))
        text = text.replace("&apos;", "'").replace("&quot;", '"').replace("&amp;", "&")
        page = page_map.get(text)
        if page is None:
            return hyp, False
        m = re.search(
            r'<w:r[^>]*>'
            r'(<w:fldChar w:fldCharType="begin"[^>]*/>)'
            r'(<w:instrText[^>]*>[^<]*PAGEREF[^<]*</w:instrText>)'
            r'(<w:fldChar w:fldCharType="separate"/>)'
            r'(<w:fldChar w:fldCharType="end"/>)'
            r'</w:r>',
            hyp,
        )
        if not m:
            return hyp, False
        rebuilt = (
            f'<w:r>{m.group(1)}</w:r>'
            f'<w:r>{m.group(2)}</w:r>'
            f'<w:r>{m.group(3)}</w:r>'
            '<w:r><w:rPr><w:noProof/></w:rPr>'
            f'<w:t>{page}</w:t></w:r>'
            '<w:r><w:fldChar w:fldCharType="end"/></w:r>'
        )
        new_hyp = hyp[: m.start()] + rebuilt + hyp[m.end():]
        return new_hyp, True

    out, count, missing = [], 0, []
    pos = 0
    for m in re.finditer(r"<w:hyperlink[^>]*>.*?</w:hyperlink>", sdt, re.S):
        out.append(sdt[pos:m.start()])
        new_hyp, ok = inject(m.group(0))
        if ok:
            count += 1
        else:
            t = "".join(re.findall(r"<w:t[^>]*>([^<]*)</w:t>", m.group(0)))
            missing.append(t[:50])
        out.append(new_hyp)
        pos = m.end()
    out.append(sdt[pos:])
    new_sdt = "".join(out)

    xml = xml[:i] + new_sdt + xml[j + len("</w:sdt>"):]
    print(f"PAGEREF cached page numbers injected: {count}; missing: {missing}")
    print(f"Removed {removed} empty <w:pgNumType/> tags")
    return xml


def patch_footer(xml):
    new, n = re.subn(
        r"(<w:instrText[^>]*>)\s*PAGE\s*(</w:instrText>)",
        r"\1 PAGE \\* arabic \\* MERGEFORMAT \2",
        xml,
    )
    print(f"Footer PAGE fields patched: {n}")
    return new


def patch_styles(xml):
    if 'w:styleId="Hyperlink"' not in xml:
        print("WARNING: Hyperlink style missing")
    # Compress TOC entry styles so all 29 entries + refresh hint fit on one page.
    n = 0
    for sid in ("TOC1", "TOC2", "TOC3"):
        m = re.search(
            r'(<w:style [^>]*w:styleId="%s"[^>]*>)(.*?)(</w:style>)' % sid, xml, re.S
        )
        if not m:
            continue
        body_xml = m.group(2)
        spacing = '<w:spacing w:before="12" w:after="12" w:line="238" w:lineRule="auto"/>'
        if "<w:spacing" in body_xml:
            body_xml = re.sub(r"<w:spacing[^/]*/>", spacing, body_xml, count=1)
        else:
            body_xml = body_xml.replace("</w:pPr>", spacing + "</w:pPr>", 1)
            if spacing not in body_xml:
                body_xml = "<w:pPr>" + spacing + "</w:pPr>" + body_xml
        xml = xml[: m.start()] + m.group(1) + body_xml + m.group(3) + xml[m.end():]
        n += 1
    print(f"TOC styles compressed: {n}")
    return xml


def patch_settings(xml):
    if "updateFields" in xml:
        print("settings.xml: updateFields already present")
        return xml
    xml = xml.replace(
        "<w:updateFields w:val=\"true\"/>", ""
    )  # normalize (no-op)
    # insert right after <w:settings ...> opening tag
    m = re.search(r"(<w:settings[^>]*>)", xml)
    if not m:
        raise RuntimeError("settings.xml malformed")
    xml = xml[: m.end()] + "<w:updateFields w:val=\"true\"/>" + xml[m.end():]
    print("settings.xml: added updateFields=true")
    return xml


def main(docx_path, page_map_path):
    with open(page_map_path) as f:
        page_map = json.load(f)

    tmpdir = tempfile.mkdtemp()
    try:
        with zipfile.ZipFile(docx_path) as z:
            z.extractall(tmpdir)

        doc_p = os.path.join(tmpdir, "word", "document.xml")
        with open(doc_p, encoding="utf-8") as f:
            xml = f.read()
        xml = patch_document(xml, page_map)

        foot_p = os.path.join(tmpdir, "word", "footer1.xml")
        if os.path.exists(foot_p):
            with open(foot_p, encoding="utf-8") as f:
                fx = f.read()
            fx = patch_footer(fx)
            with open(foot_p, "w", encoding="utf-8") as f:
                f.write(fx)

        set_p = os.path.join(tmpdir, "word", "settings.xml")
        with open(set_p, encoding="utf-8") as f:
            sx = f.read()
        sx = patch_settings(sx)
        with open(set_p, "w", encoding="utf-8") as f:
            f.write(sx)

        sty_p = os.path.join(tmpdir, "word", "styles.xml")
        with open(sty_p, encoding="utf-8") as f:
            stx = f.read()
        stx = patch_styles(stx)
        with open(sty_p, "w", encoding="utf-8") as f:
            f.write(stx)

        with open(doc_p, "w", encoding="utf-8") as f:
            f.write(xml)

        out = docx_path + ".tmp"
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
            for root, _, files in os.walk(tmpdir):
                for fn in files:
                    full = os.path.join(root, fn)
                    z.write(full, os.path.relpath(full, tmpdir))
        shutil.move(out, docx_path)
        print("Repacked:", docx_path)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])

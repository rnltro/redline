"""Post-process docx for WPS/Word compatibility:
1. Remove empty <w:pgNumType/> tags from document.xml (cover/front-matter sections).
2. Patch footer PAGE fields with explicit \\* arabic format switch.
"""
import re
import shutil
import sys
import zipfile
import tempfile
import os

SRC = "/home/z/my-project/download/Confidential_Document_Copilot_Build_Plan.docx"


def main(path):
    tmpdir = tempfile.mkdtemp()
    try:
        with zipfile.ZipFile(path, "r") as z:
            z.extractall(tmpdir)

        doc_path = os.path.join(tmpdir, "word", "document.xml")
        with open(doc_path, "r", encoding="utf-8") as f:
            xml = f.read()

        n_pgnum = len(re.findall(r"<w:pgNumType/>", xml))
        xml = xml.replace("<w:pgNumType/>", "")
        with open(doc_path, "w", encoding="utf-8") as f:
            f.write(xml)
        print(f"document.xml: removed {n_pgnum} empty <w:pgNumType/> tags")

        # Patch footers: bare PAGE -> PAGE \* arabic \* MERGEFORMAT
        word_dir = os.path.join(tmpdir, "word")
        patched = 0
        for name in os.listdir(word_dir):
            if name.startswith("footer") and name.endswith(".xml"):
                fp = os.path.join(word_dir, name)
                with open(fp, "r", encoding="utf-8") as f:
                    fx = f.read()
                new_fx, n = re.subn(
                    r"(<w:instrText[^>]*>)\s*PAGE\s*(</w:instrText>)",
                    r"\1 PAGE \\* arabic \\* MERGEFORMAT \2",
                    fx,
                )
                if n:
                    with open(fp, "w", encoding="utf-8") as f:
                        f.write(new_fx)
                    patched += n
                    print(f"{name}: patched {n} PAGE field(s) -> arabic")
        print(f"Total footer fields patched: {patched}")

        # Rezip
        out = path + ".tmp"
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
            for root, _, files in os.walk(tmpdir):
                for fn in files:
                    full = os.path.join(root, fn)
                    rel = os.path.relpath(full, tmpdir)
                    z.write(full, rel)
        shutil.move(out, path)
        print("Repacked:", path)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else SRC)

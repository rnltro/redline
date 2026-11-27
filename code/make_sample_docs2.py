"""Two more demo documents for the Redline app:
  3) sample_nda.pdf          - mutual NDA, 2 pages (reportlab)
  4) sample_employment.docx  - employment contract (python-docx)
Fictional parties again, chosen so every name survives the ORG/PERSON
regexes cleanly (single-suffix org names, title-prefixed person names).
"""
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

OUT_PDF = "/home/z/my-project/download/sample_nda.pdf"
OUT_DOCX = "/home/z/my-project/download/sample_employment.docx"

PAGE1 = [
    "MUTUAL NON-DISCLOSURE AGREEMENT",
    "",
    "This Mutual Non-Disclosure Agreement (the \"Agreement\") is made on",
    "January 12, 2026 (the \"Effective Date\") by and between:",
    "",
    "   Quintana Robotics Ltd., a company registered in Singapore, with",
    "   offices at 9 Battery Road, Singapore (the \"Disclosing Party\"); and",
    "",
    "   Del Rosario Fabrication Works Inc., with offices at 23 Banawe Avenue,",
    "   Quezon City (the \"Receiving Party\").",
    "",
    "The parties wish to explore a joint manufacturing partnership (the",
    "\"Purpose\") and may disclose confidential information to each other in",
    "connection with the Purpose.",
    "",
    "1. CONFIDENTIAL INFORMATION. \"Confidential Information\" means all",
    "non-public technical drawings, tooling specifications, supplier pricing",
    "and business plans disclosed by either party, in any form.",
    "",
    "2. OBLIGATIONS. Each party shall use the other party's Confidential",
    "Information solely for the Purpose, protect it with at least the same",
    "care used for its own, and limit access to employees who need to know.",
    "",
    "3. TERM. The obligations in this Agreement run from the Effective Date",
    "until December 31, 2028, and survive termination of the partnership",
    "talks.",
]
PAGE2 = [
    "4. DAMAGES. The parties agree that unauthorized disclosure may cause",
    "irreparable harm. As a genuine pre-estimate of damages, each party",
    "accepts liquidated damages of $500,000 per breach, without prejudice to",
    "further relief, and a performance bond of USD 250,000 shall be",
    "maintained while the talks are ongoing.",
    "",
    "5. REMEDIES. The injured party may seek injunctive relief in addition to",
    "any monetary remedy under this Agreement.",
    "",
    "6. GOVERNING LAW. This Agreement is governed by the laws of Singapore.",
    "",
    "IN WITNESS WHEREOF, the parties have executed this Agreement by:",
    "",
    "   For Quintana Robotics Ltd.:       For Del Rosario Fabrication Works Inc.:",
    "",
    "   Dr. Mei Lin Tan                   Atty. Fernando Salazar",
    "   Chief Technology Officer          General Counsel",
    "   m.tan@quintanarobotics.com        legal@delrosariofab.com",
    "",
    "   signed Singapore,                 signed Quezon City,",
    "   January 12, 2026                  January 12, 2026",
]

def build_pdf():
    c = canvas.Canvas(OUT_PDF, pagesize=letter)
    for lines in (PAGE1, PAGE2):
        t = c.beginText(72, 740)
        t.setFont("Helvetica", 10.5)
        t.setLeading(15)
        for ln in lines:
            t.textLine(ln)
        c.drawText(t)
        c.showPage()
    c.save()
    print("PDF written:", OUT_PDF)

DOC_BODY = [
    ("h", "EMPLOYMENT CONTRACT"),
    ("p", "This Employment Contract is entered into on June 15, 2026 (the \"Start Date\") between:"),
    ("b", "Marisol Media Productions Inc. (the \"Employer\"), with offices at Ortigas Center, Pasig City; and"),
    ("b", "Ms. Andrea Bautista (the \"Employee\"), of Quezon City."),
    ("p", "1. POSITION. The Employer hires the Employee as Vice President for Content, reporting directly to the Chief Financial Officer."),
    ("b", "2. COMPENSATION. The Employee shall receive a salary of PHP 1,800,000 per annum, paid in twelve (12) monthly installments, plus a one-time signing bonus of $8,500."),
    ("b", "3. PROBATION. The first six (6) months of employment constitute the probationary period."),
    ("p", "4. TERM. This Contract runs until 2027-06-14, renewable by mutual written agreement."),
    ("p", "5. CONFIDENTIALITY. The Employee shall keep all production plans and talent agreements strictly confidential."),
    ("p", "6. RESIGNATION. The Employee may resign by giving thirty (30) days written notice."),
    ("p", "7. GOVERNING LAW. The laws of the Philippines apply to this Contract."),
    ("p", "8. SIGNATURES. This Contract is executed by:"),
    ("b", "   Ms. Andrea Bautista — Vice President — a.bautista@marisolmedia.com"),
    ("b", "   Atty. Carla Domingo — General Counsel — c.domingo@marisolmedia.com"),
    ("p", "For HR matters: hr@marisolmedia.com"),
]

def build_docx():
    import docx
    from docx.shared import Pt
    d = docx.Document()
    for kind, txt in DOC_BODY:
        p = d.add_paragraph()
        run = p.add_run(txt)
        run.font.size = Pt(11)
        run.bold = kind in ("h", "b")
        if kind == "h":
            run.font.size = Pt(14)
    d.save(OUT_DOCX)
    print("DOCX written:", OUT_DOCX)

if __name__ == "__main__":
    build_pdf()
    build_docx()

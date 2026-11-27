"""Build the two demo documents for the Redline app:
  1) sample_contract.pdf     - 2-page consulting agreement (reportlab, Helvetica)
  2) sample_agreement.docx   - master services agreement (python-docx)
Both are fictional but realistic, and contain entities for all 6 scanner
types (PERSON / ORG / AMOUNT / DATE / EMAIL / TITLE). Different parties per
file so uploading either proves the scan is live, not hardcoded.
"""
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

OUT_PDF = "/home/z/my-project/download/sample_contract.pdf"
OUT_DOCX = "/home/z/my-project/download/sample_agreement.docx"

PAGE1 = [
    "CONSULTING SERVICES AGREEMENT",
    "",
    "This Consulting Services Agreement (the \"Agreement\") is entered into on",
    "February 28, 2026 (the \"Effective Date\") by and between:",
    "",
    "   Silverline Business Solutions Inc., a company organized under the laws",
    "   of the Philippines, with registered office at 88F Ayala Avenue, Makati",
    "   City (the \"Consultant\"); and",
    "",
    "   Cordova Trading & Logistics Corp., with registered office at 12 Rizal",
    "   Street, Cebu City (the \"Client\").",
    "",
    "The Client wishes to engage the Consultant for supply-chain analytics and",
    "process automation services, and the Consultant accepts such engagement",
    "under the terms of this Agreement.",
    "",
    "1. SCOPE OF SERVICES. The Consultant shall deliver the analytics platform",
    "described in Annex A, including quarterly training for up to forty (40) of",
    "the Client's staff.",
    "",
    "2. FEES AND PAYMENT.",
    "   2.1 The Client shall pay a total fee of PHP 2,400,000 (the \"Total",
    "   Fee\"), invoiced in four (4) equal installments.",
    "   2.2 Each invoice is payable within forty-five (45) days. The first",
    "   installment of $45,000 equivalent is due on March 1, 2026.",
    "   2.3 Late payments accrue interest at 1.5% per month.",
    "",
    "3. TERM. This Agreement begins on March 1, 2026 and ends on 05/31/2027,",
    "unless terminated earlier under Clause 5.",
]
PAGE2 = [
    "4. CONFIDENTIALITY. Each party shall keep confidential information of the",
    "other party secret for five (5) years after the end of the Term.",
    "",
    "5. TERMINATION. Either party may terminate for convenience upon sixty (60)",
    "days written notice, or immediately for material breach not cured within",
    "fifteen (15) days.",
    "",
    "6. LIABILITY. The total liability of the Consultant shall not exceed the",
    "Total Fee paid under this Agreement.",
    "",
    "7. GOVERNING LAW. This Agreement is governed by the laws of the",
    "Philippines.",
    "",
    "IN WITNESS WHEREOF, the parties have executed this Agreement by:",
    "",
    "   For the Consultant:                    For the Client:",
    "",
    "   Atty. Liza Dela Cruz                   Mr. Ramon Villanueva",
    "   Chief Operating Officer                Managing Director",
    "   Silverline Business Solutions Inc.     Cordova Trading & Logistics Corp.",
    "   l.dela.cruz@silverlineconsulting.com   r.villanueva@cordovatrading.com",
    "   signed Makati City,                    signed Cebu City,",
    "   February 28, 2026                      February 28, 2026",
    "",
    "For billing matters: accounts@silverlineconsulting.com",
]

def build_pdf():
    c = canvas.Canvas(OUT_PDF, pagesize=letter)
    t = c.beginText(72, 740)
    t.setFont("Helvetica", 10.5)
    t.setLeading(15)
    for ln in PAGE1:
        t.textLine(ln)
    c.drawText(t)
    c.showPage()
    t = c.beginText(72, 740)
    t.setFont("Helvetica", 10.5)
    t.setLeading(15)
    for ln in PAGE2:
        t.textLine(ln)
    c.drawText(t)
    c.showPage()
    c.save()
    print("PDF written:", OUT_PDF)

DOC_BODY = [
    ("h", "MASTER SERVICES AGREEMENT"),
    ("p", "This Master Services Agreement is made on April 15, 2026 between:"),
    ("b", "Harborview Legal Partners LLP (the \"Firm\"), with offices at Bonifacio Global City, Taguig; and"),
    ("b", "Tala Digital Ventures Inc. (the \"Company\"), with offices at Pasig City."),
    ("p", "1. SCOPE. The Firm shall provide contract review and compliance advisory services for the Company's fintech products."),
    ("p", "2. FEES."),
    ("b", "   2.1 A fixed fee of $180,000 covers the period up to 2026-12-31."),
    ("b", "   2.2 Additional work beyond the scope above is billed at EUR 60,000 per quarter."),
    ("b", "   2.3 Invoices are payable within thirty (30) days of receipt."),
    ("p", "3. TERM. Twelve (12) months from the Effective Date, renewable by mutual written agreement."),
    ("p", "4. CONFIDENTIALITY. The Firm shall protect the Company's data under the Data Privacy Act and keep all matter files confidential."),
    ("p", "5. TERMINATION. Either party may terminate this Agreement upon thirty (30) days written notice."),
    ("p", "6. SIGNATURES. This Agreement is executed by:"),
    ("b", "   Ms. Katrina Ong, Chief Financial Officer, Tala Digital Ventures Inc., k.ong@taladigital.com"),
    ("b", "   Atty. Paolo Mendoza, General Counsel, Harborview Legal Partners LLP, accounts@harborviewlegal.com"),
    ("p", "7. GOVERNING LAW. The laws of the Philippines apply to this Agreement."),
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
    try:
        import docx  # noqa
    except ImportError:
        raise SystemExit("python-docx missing — run: pip install python-docx")
    build_docx()

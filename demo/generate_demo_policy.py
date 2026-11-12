"""Generates the official demonstration policy PDF: ACME Expense Reimbursement Policy."""
import os
import pymupdf


def generate_policy_pdf(output_path: str = "demo/sample_expense_policy.pdf") -> None:
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    doc = pymupdf.open()

    # --- Page 1 ---
    page1 = doc.new_page(width=595, height=842)  # A4 standard

    # Header banner
    page1.draw_rect(pymupdf.Rect(40, 40, 555, 110), color=None, fill=(0.08, 0.18, 0.36))
    page1.insert_text(
        (55, 75),
        "ACME ENTERPRISE HOLDINGS INC.",
        fontsize=16,
        color=(1, 1, 1),
        fontname="helv",
    )
    page1.insert_text(
        (55, 95),
        "CORPORATE POLICY MANUAL | FINANCE & GOVERNANCE DIVISION",
        fontsize=9,
        color=(0.8, 0.85, 0.95),
        fontname="helv",
    )

    # Document Title
    page1.insert_text(
        (50, 150),
        "Employee Expense Reimbursement Policy (POL-FIN-2026-04)",
        fontsize=15,
        color=(0.1, 0.15, 0.25),
        fontname="helv",
    )
    page1.insert_text(
        (50, 170),
        "Effective Date: January 1, 2026 | Document Version: 3.2 | Classification: Internal Sensitive",
        fontsize=8.5,
        color=(0.4, 0.45, 0.5),
        fontname="helv",
    )

    # Separator Line
    page1.draw_line(pymupdf.Point(50, 185), pymupdf.Point(545, 185), color=(0.8, 0.85, 0.9), width=1)

    # Section 1: Objective & Scope
    page1.insert_text((50, 210), "1. PURPOSE AND PRINCIPLES", fontsize=11, color=(0.08, 0.18, 0.36), fontname="helv")
    s1_text = (
        "1.1 ACME Enterprise Holdings commits to reimbursing employees for all necessary, reasonable, "
        "and properly documented business expenses incurred while carrying out company duties.\n"
        "1.2 This policy applies universally across all regional branches, subsidiaries, business units, "
        "and remote workforce members operating within India."
    )
    page1.insert_textbox(pymupdf.Rect(50, 220, 545, 270), s1_text, fontsize=9.5, fontname="helv")

    # Section 2: Approval Limits & Hierarchy
    page1.insert_text((50, 285), "2. APPROVAL THRESHOLDS AND HIERARCHY", fontsize=11, color=(0.08, 0.18, 0.36), fontname="helv")
    s2_text = (
        "2.1 Department Manager Approval:\n"
        "    Expenses up to and including INR 5,000 may be approved directly by the employee's designated "
        "Department Manager or direct team lead.\n\n"
        "2.2 Finance Department Approval:\n"
        "    Expense claims between INR 5,001 and INR 10,000 require formal review and explicit sign-off "
        "from the Central Finance Department.\n\n"
        "2.3 Senior Leadership Approval:\n"
        "    Any single expenditure or aggregated travel voucher exceeding INR 10,000 requires prior written "
        "authorization from a Vice President (VP) or Executive Director."
    )
    page1.insert_textbox(pymupdf.Rect(50, 295, 545, 415), s2_text, fontsize=9.5, fontname="helv")

    # Section 3: Receipt Substantiation & Submission Deadlines (INTENTIONAL FINDING / COMPLIANCE ISSUE)
    page1.insert_text((50, 430), "3. DOCUMENTATION AND DEADLINES", fontsize=11, color=(0.08, 0.18, 0.36), fontname="helv")
    s3_text = (
        "3.1 Valid Itemized Invoices:\n"
        "    All expense reimbursement claims must be accompanied by an itemized tax invoice or formal receipt. "
        "Credit card slips or bank charge summaries alone are not admissible as sole substantiation.\n\n"
        "3.2 Submission Window:\n"
        "    Employees are requested to submit receipts within 60 days of incurring the transaction. "
        "Claims submitted outside this extended timeframe may be approved subject to departmental discretion."
    )
    page1.insert_textbox(pymupdf.Rect(50, 440, 545, 540), s3_text, fontsize=9.5, fontname="helv")

    # Section 4: Non-Reimbursable Categories
    page1.insert_text((50, 555), "4. EXCLUSIONS AND PROHIBITED ITEMS", fontsize=11, color=(0.08, 0.18, 0.36), fontname="helv")
    s4_text = (
        "4.1 The following items shall not be reimbursed under any circumstances:\n"
        "    - Alcoholic beverages during solo business travel.\n"
        "    - Traffic violations, speeding penalties, or parking citations.\n"
        "    - Personal entertainment, in-flight WiFi for leisure, or hotel mini-bar purchases.\n"
        "    - Spousal travel or accommodation additions without executive pre-clearance."
    )
    page1.insert_textbox(pymupdf.Rect(50, 565, 545, 660), s4_text, fontsize=9.5, fontname="helv")

    # Footer
    page1.draw_line(pymupdf.Point(50, 780), pymupdf.Point(545, 780), color=(0.8, 0.85, 0.9), width=1)
    page1.insert_text(
        (50, 795),
        "Confidential - ACME Enterprise Holdings Inc. | Page 1 of 1",
        fontsize=8,
        color=(0.5, 0.5, 0.5),
        fontname="helv",
    )

    doc.save(output_path)
    doc.close()
    print(f"Generated sample policy PDF at: {output_path}")


if __name__ == "__main__":
    generate_policy_pdf()

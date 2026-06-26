"""
app/utils/pdf_generator.py
Generates a professional PDF prediction report using ReportLab.
"""

import io
from datetime import datetime
from typing import Optional

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        HRFlowable, KeepTogether
    )
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


def generate_prediction_pdf(prediction) -> Optional[bytes]:
    """
    Generate a PDF report for a Prediction model instance.

    Args:
        prediction: A Prediction ORM instance (or plain dict with the same keys).

    Returns:
        PDF bytes, or None if ReportLab is not installed.
    """
    if not REPORTLAB_AVAILABLE:
        return None

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        title="Credit Card Approval Report",
    )

    # ── Colour palette ─────────────────────────────────────────────────────
    PRIMARY   = colors.HexColor("#0F4C81")
    SECONDARY = colors.HexColor("#1565C0")
    SUCCESS   = colors.HexColor("#2E7D32")
    DANGER    = colors.HexColor("#D32F2F")
    LIGHT_BG  = colors.HexColor("#F5F7FA")
    GREY      = colors.HexColor("#546E7A")
    WHITE     = colors.white

    # ── Styles ─────────────────────────────────────────────────────────────
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "Title", fontSize=20, textColor=WHITE, alignment=TA_CENTER,
        fontName="Helvetica-Bold", leading=28
    )
    subtitle_style = ParagraphStyle(
        "Subtitle", fontSize=11, textColor=WHITE, alignment=TA_CENTER,
        fontName="Helvetica", leading=16
    )
    section_header = ParagraphStyle(
        "SectionHeader", fontSize=12, textColor=PRIMARY, fontName="Helvetica-Bold",
        spaceBefore=14, spaceAfter=6, leading=16
    )
    label_style = ParagraphStyle(
        "Label", fontSize=9, textColor=GREY, fontName="Helvetica-Bold"
    )
    value_style = ParagraphStyle(
        "Value", fontSize=10, textColor=colors.black, fontName="Helvetica"
    )
    normal = styles["Normal"]
    normal.fontSize = 9

    # ── Helper: get attr from ORM instance or dict ─────────────────────────
    def g(attr, default="N/A"):
        if isinstance(prediction, dict):
            return prediction.get(attr, default) or default
        return getattr(prediction, attr, default) or default

    # ── Story ──────────────────────────────────────────────────────────────
    story = []

    # Header banner
    is_approved = g("result") == "Approved"
    header_color = SUCCESS if is_approved else DANGER
    header_data = [[
        Paragraph("CREDIT CARD APPROVAL PREDICTION", title_style),
    ], [
        Paragraph("IBM Watson Machine Learning · Credit Risk Report", subtitle_style),
    ]]
    header_table = Table(header_data, colWidths=[17 * cm])
    header_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), PRIMARY),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [PRIMARY]),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 0.4 * cm))

    # Result banner
    result_text = f"✓  APPLICATION {g('result', 'N/A').upper()}" if is_approved else f"✗  APPLICATION {g('result', 'N/A').upper()}"
    result_para = Paragraph(result_text, ParagraphStyle(
        "Result", fontSize=16, textColor=WHITE, alignment=TA_CENTER,
        fontName="Helvetica-Bold", leading=22
    ))
    result_table = Table([[result_para]], colWidths=[17 * cm])
    result_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), header_color),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(result_table)
    story.append(Spacer(1, 0.5 * cm))

    # Key metrics row
    prob_pct = f"{float(g('probability', 0)) * 100:.1f}%"
    confidence = f"{g('confidence', 0)}%"
    risk_score = f"{g('risk_score', 0)}/100"
    credit_rating = g('credit_rating', 'N/A')

    metrics_data = [
        [
            _metric_cell("Approval Prob.", prob_pct, styles),
            _metric_cell("Confidence", confidence, styles),
            _metric_cell("Risk Score", risk_score, styles),
            _metric_cell("Credit Rating", credit_rating, styles),
        ]
    ]
    metrics_table = Table(metrics_data, colWidths=[4.25 * cm] * 4)
    metrics_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BG),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CFD8DC")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CFD8DC")),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(metrics_table)
    story.append(Spacer(1, 0.4 * cm))

    # Personal Information
    story.append(Paragraph("Personal Information", section_header))
    story.append(HRFlowable(width="100%", thickness=1, color=PRIMARY))
    story.append(Spacer(1, 0.2 * cm))
    personal_data = [
        ["Applicant Name", g("applicant_name"),   "Age",           g("age")],
        ["Gender",         g("gender"),            "Marital Status", g("marital_status")],
        ["Education",      g("education"),         "Children",      g("num_children")],
        ["Email",          g("applicant_email"),   "Occupation",    g("occupation")],
    ]
    story.append(_info_table(personal_data))
    story.append(Spacer(1, 0.3 * cm))

    # Financial Details
    story.append(Paragraph("Financial Details", section_header))
    story.append(HRFlowable(width="100%", thickness=1, color=PRIMARY))
    story.append(Spacer(1, 0.2 * cm))
    fin_data = [
        ["Annual Income",    _fmt_currency(g("annual_income", 0)),
         "Credit Score",     str(g("credit_score", "N/A"))],
        ["Total Assets",     _fmt_currency(g("total_assets", 0)),
         "Total Debt",       _fmt_currency(g("total_debt", 0))],
        ["Net Worth",        _fmt_currency(g("net_worth", 0)),
         "Debt-to-Income",   _debt_ratio(g("total_debt", 0), g("annual_income", 1))],
    ]
    story.append(_info_table(fin_data))
    story.append(Spacer(1, 0.3 * cm))

    # Loan Information
    story.append(Paragraph("Loan Information", section_header))
    story.append(HRFlowable(width="100%", thickness=1, color=PRIMARY))
    story.append(Spacer(1, 0.2 * cm))
    loan_data = [
        ["Loan Amount",   _fmt_currency(g("loan_amount", 0)),
         "Loan Term",     f"{g('loan_term', 'N/A')} months"],
        ["Loan Purpose",  g("loan_purpose"),
         "Employment",    g("employment_status")],
        ["Years Employed", str(g("years_employed", "N/A")),
         "Prior Loans",   str(g("prior_loans", "N/A"))],
    ]
    story.append(_info_table(loan_data))
    story.append(Spacer(1, 0.3 * cm))

    # Recommendation
    story.append(Paragraph("Recommendation", section_header))
    story.append(HRFlowable(width="100%", thickness=1, color=PRIMARY))
    story.append(Spacer(1, 0.2 * cm))
    rec_text = g("recommendation", "No recommendation available.")
    story.append(Paragraph(rec_text, ParagraphStyle(
        "Rec", fontSize=10, leading=16, textColor=colors.black
    )))
    story.append(Spacer(1, 0.3 * cm))

    # Factors
    risk_factors = g("risk_factors", [])
    if isinstance(risk_factors, str):
        import json
        try:
            risk_factors = json.loads(risk_factors)
        except Exception:
            risk_factors = []

    positive_factors = g("positive_factors", [])
    if isinstance(positive_factors, str):
        import json
        try:
            positive_factors = json.loads(positive_factors)
        except Exception:
            positive_factors = []

    factors_data = []
    max_rows = max(len(risk_factors), len(positive_factors), 1)
    for i in range(max_rows):
        rf = f"• {risk_factors[i]}" if i < len(risk_factors) else ""
        pf = f"• {positive_factors[i]}" if i < len(positive_factors) else ""
        factors_data.append([Paragraph(rf, normal), Paragraph(pf, normal)])

    if factors_data:
        story.append(Paragraph("Risk & Positive Factors", section_header))
        story.append(HRFlowable(width="100%", thickness=1, color=PRIMARY))
        story.append(Spacer(1, 0.2 * cm))
        hdr = [
            Paragraph("Risk Factors", ParagraphStyle("H", fontName="Helvetica-Bold", fontSize=10, textColor=WHITE)),
            Paragraph("Positive Factors", ParagraphStyle("H", fontName="Helvetica-Bold", fontSize=10, textColor=WHITE)),
        ]
        full_data = [hdr] + factors_data
        f_table = Table(full_data, colWidths=[8.5 * cm, 8.5 * cm])
        f_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, 0), DANGER),
            ("BACKGROUND", (1, 0), (1, 0), SUCCESS),
            ("BACKGROUND", (0, 1), (-1, -1), LIGHT_BG),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CFD8DC")),
        ]))
        story.append(f_table)

    # Footer
    story.append(Spacer(1, 0.8 * cm))
    footer_text = (
        f"Report generated on {datetime.now().strftime('%d %B %Y at %H:%M')}  |  "
        f"Model: {g('model_used', 'XGBoost')}  |  "
        f"Prediction ID: #{g('id', 'N/A')}  |  "
        "Credit Card Approval Prediction System · IBM Watson ML"
    )
    story.append(Paragraph(footer_text, ParagraphStyle(
        "Footer", fontSize=8, textColor=GREY, alignment=TA_CENTER
    )))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


# ── Helpers ────────────────────────────────────────────────────────────────────

def _metric_cell(label: str, value: str, styles) -> Table:
    normal = styles["Normal"]
    lbl = Paragraph(label, ParagraphStyle("L", fontSize=8, textColor=colors.HexColor("#546E7A"),
                                          fontName="Helvetica", alignment=TA_CENTER))
    val = Paragraph(value, ParagraphStyle("V", fontSize=14, textColor=colors.HexColor("#0F4C81"),
                                          fontName="Helvetica-Bold", alignment=TA_CENTER))
    t = Table([[lbl], [val]])
    t.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


def _info_table(rows: list) -> Table:
    """Build a two-column key/value info table."""
    LIGHT_BG = colors.HexColor("#F5F7FA")
    GREY = colors.HexColor("#546E7A")

    styled_rows = []
    for row in rows:
        styled_row = []
        for i, cell in enumerate(row):
            if i % 2 == 0:
                styled_row.append(Paragraph(str(cell), ParagraphStyle(
                    "K", fontSize=8, textColor=GREY, fontName="Helvetica-Bold"
                )))
            else:
                styled_row.append(Paragraph(str(cell), ParagraphStyle(
                    "V", fontSize=9, textColor=colors.black, fontName="Helvetica"
                )))
        styled_rows.append(styled_row)

    t = Table(styled_rows, colWidths=[4 * cm, 4.5 * cm, 4 * cm, 4.5 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BG),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#CFD8DC")),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [LIGHT_BG, colors.white]),
    ]))
    return t


def _fmt_currency(val) -> str:
    try:
        return f"₹{float(val):,.0f}"
    except (TypeError, ValueError):
        return "N/A"


def _debt_ratio(debt, income) -> str:
    try:
        r = float(debt) / float(income)
        return f"{r:.1%}"
    except (TypeError, ValueError, ZeroDivisionError):
        return "N/A"

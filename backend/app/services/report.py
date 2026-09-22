import html
import uuid
from datetime import datetime
from pathlib import Path

from app.core.config import get_settings
from app.core.models import Prediction
from app.services.ml.base import DISEASES


def _text(value: object) -> str:
    return html.escape(str(value))


def _disease_name(disease_id: str) -> str:
    return DISEASES.get(disease_id).name if disease_id in DISEASES else disease_id.title()


def _input_rows(prediction: Prediction) -> list[list[str]]:
    values = prediction.input_text or {}
    spec = DISEASES.get(prediction.disease)
    if spec is None:
        return [[str(key).replace("_", " ").title(), str(value)] for key, value in values.items()]
    rows = []
    for field in spec.features:
        if field.name in values:
            rows.append([field.label, str(values[field.name])])
    return rows


def _interpretation(prediction: Prediction) -> str:
    evidence = (
        "The attached image and attention overlay show the model input and visual focus area."
        if prediction.input_type == "image"
        else "The result is based on the clinical values recorded in the input summary."
    )
    mode = " This result was generated in demo mode and is illustrative only." if prediction.is_demo else ""
    return (
        f"The model classified this assessment as <b>{_text(prediction.label)}</b> with a reported "
        f"confidence of <b>{prediction.confidence:.1%}</b>. {evidence}{mode}"
    )


def _footer(canvas, doc) -> None:
    from reportlab.lib.units import mm

    canvas.saveState()
    canvas.setStrokeColorRGB(0.82, 0.87, 0.86)
    canvas.line(18 * mm, 15 * mm, 192 * mm, 15 * mm)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColorRGB(0.4, 0.47, 0.47)
    canvas.drawString(18 * mm, 10 * mm, "AI Medical Diagnostic System - Decision-support report")
    canvas.drawRightString(192 * mm, 10 * mm, f"Page {doc.page}")
    canvas.restoreState()


def generate_report(prediction: Prediction) -> Path:
    settings = get_settings()
    report_dir = Path(settings.media_dir) / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    out_path = report_dir / f"report_{prediction.id}_{uuid.uuid4().hex[:8]}.pdf"

    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import Image as RLImage
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    doc = SimpleDocTemplate(
        str(out_path), pagesize=A4, rightMargin=18 * mm, leftMargin=18 * mm,
        topMargin=18 * mm, bottomMargin=24 * mm,
        title=f"Medical Assessment Report - {prediction.id}",
        author="AI Medical Diagnostic System",
    )
    styles = getSampleStyleSheet()
    title = ParagraphStyle("ReportTitle", parent=styles["Title"], fontSize=20, leading=24, textColor=colors.HexColor("#14252b"), alignment=1, spaceAfter=4)
    subtitle = ParagraphStyle("ReportSubtitle", parent=styles["Normal"], fontSize=10, leading=14, textColor=colors.HexColor("#58706f"), alignment=1, spaceAfter=14)
    section = ParagraphStyle("ReportSection", parent=styles["Heading2"], fontSize=13, leading=16, textColor=colors.HexColor("#087f78"), spaceBefore=10, spaceAfter=7)
    body = ParagraphStyle("ReportBody", parent=styles["BodyText"], fontSize=9.5, leading=14, spaceAfter=5)
    small = ParagraphStyle("ReportSmall", parent=body, fontSize=8.5, leading=12, textColor=colors.HexColor("#58706f"))
    cell = ParagraphStyle("ReportCell", parent=body, fontSize=8.5, leading=11)
    bold = ParagraphStyle("ReportCellBold", parent=cell, fontName="Helvetica-Bold")

    def table_style(header=False):
        commands = [
            ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#c6ddd8")),
            ("INNERGRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#d8e7e3")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 7), ("RIGHTPADDING", (0, 0), (-1, -1), 7),
            ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]
        if header:
            commands.extend([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#087f78")), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white), ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f8f7")])])
        else:
            commands.append(("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#e8f3f0")))
        return TableStyle(commands)

    story = [
        Paragraph("AI Medical Diagnostic System", title),
        Paragraph("Clinical decision-support assessment report", subtitle),
        Paragraph("Assessment details", section),
    ]
    details = [
        [Paragraph("Patient", bold), Paragraph(_text(prediction.user.full_name if prediction.user else "Not available"), cell)],
        [Paragraph("Assessment ID", bold), Paragraph(_text(prediction.id), cell)],
        [Paragraph("Disease module", bold), Paragraph(_text(_disease_name(prediction.disease)), cell)],
        [Paragraph("Assessment type", bold), Paragraph(_text("Medical image" if prediction.input_type == "image" else "Clinical data"), cell)],
        [Paragraph("Generated", bold), Paragraph(datetime.now().strftime("%Y-%m-%d %H:%M"), cell)],
    ]
    details_table = Table(details, colWidths=[48 * mm, 112 * mm])
    details_table.setStyle(table_style())
    story.extend([details_table, Paragraph("Assessment result", section)])

    result_rows = [[Paragraph("Primary classification", bold), Paragraph(_text(prediction.label), cell)], [Paragraph("Reported confidence", bold), Paragraph(f"{prediction.confidence:.2%}", cell)]]
    for label, value in (prediction.probabilities or {}).items():
        result_rows.append([Paragraph(f"Probability: {_text(label)}", bold), Paragraph(f"{value:.2%}", cell)])
    result_rows.append([Paragraph("Inference mode", bold), Paragraph("Demo / illustrative" if prediction.is_demo else "Trained model", cell)])
    result_table = Table(result_rows, colWidths=[78 * mm, 82 * mm])
    result_table.setStyle(table_style())
    story.extend([result_table, Paragraph("Clinical input summary", section)])

    input_rows = _input_rows(prediction)
    if input_rows:
        input_table = Table([[Paragraph("Measure", bold), Paragraph("Recorded value", bold)]] + [[Paragraph(_text(label), cell), Paragraph(_text(value), cell)] for label, value in input_rows], colWidths=[110 * mm, 50 * mm], repeatRows=1)
        input_table.setStyle(table_style(header=True))
        story.append(input_table)
    elif prediction.input_type == "image":
        story.append(Paragraph("This assessment was based on an uploaded medical image.", body))

    if prediction.input_image_path and Path(prediction.input_image_path).exists():
        story.extend([Paragraph("Image evidence", section), RLImage(str(prediction.input_image_path), width=72 * mm, height=72 * mm)])
    if prediction.heatmap_path and Path(prediction.heatmap_path).exists():
        story.extend([Spacer(1, 4 * mm), Paragraph("Model attention overlay", section), RLImage(str(prediction.heatmap_path), width=72 * mm, height=72 * mm)])

    story.extend([
        Paragraph("Interpretation", section), Paragraph(_interpretation(prediction), body),
        Paragraph("Model information", section), Paragraph(f"Model version: <b>{_text(prediction.model_version)}</b>", body),
        Paragraph("This report presents model output and the values supplied for this assessment. It does not establish a medical diagnosis or treatment plan.", small),
        Paragraph("Important medical disclaimer", section), Paragraph("This system is an academic decision-support prototype for screening and demonstration. It is not a certified diagnostic device. Results may be incorrect or incomplete and must not be used alone to make medical decisions. A licensed healthcare professional should review the patient, source image or measurements, symptoms, history, and any appropriate tests.", body),
    ])
    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return out_path

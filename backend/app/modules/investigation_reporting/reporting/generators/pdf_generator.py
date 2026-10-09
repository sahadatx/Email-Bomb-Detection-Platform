from __future__ import annotations

import json
from io import BytesIO
from typing import Any
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

from .base import GeneratedReport


class PdfReportGenerator:
    """Create a paginated printable PDF from a persisted report snapshot."""

    output_format = "pdf"
    PAGE_WIDTH, _ = A4

    @staticmethod
    def _text(value: Any) -> str:
        if value is None:
            value = "Unavailable"
        if isinstance(value, (dict, list, tuple)):
            value = json.dumps(value, ensure_ascii=True, default=str, sort_keys=True)
        return escape(str(value).encode("latin-1", "replace").decode("latin-1"))

    def generate(self, snapshot: dict[str, Any]) -> GeneratedReport:
        stream = BytesIO()
        doc = SimpleDocTemplate(
            stream, pagesize=A4, rightMargin=18 * mm, leftMargin=18 * mm,
            topMargin=18 * mm, bottomMargin=20 * mm,
            title=str(snapshot.get("title") or "Investigation Report"),
        )
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name="InvestigationTitle", parent=styles["Title"], alignment=TA_CENTER, textColor=colors.HexColor("#20366f"), spaceAfter=4 * mm))
        styles.add(ParagraphStyle(name="InvestigationBody", parent=styles["BodyText"], fontSize=8.5, leading=12, wordWrap="CJK"))
        styles.add(ParagraphStyle(name="InvestigationCell", parent=styles["BodyText"], fontSize=7.3, leading=9, wordWrap="CJK"))
        self.cell_style = styles["InvestigationCell"]

        story = [
            Paragraph(self._text(snapshot.get("title") or "Investigation Report"), styles["InvestigationTitle"]),
            Paragraph(f"Report ID: {self._text(snapshot.get('report_id'))} &nbsp; · &nbsp; Generated: {self._text(snapshot.get('generated_at'))}", styles["InvestigationBody"]),
            Spacer(1, 5 * mm),
        ]
        summary = snapshot.get("executive_summary")
        if summary is not None:
            story.append(Paragraph("Executive Summary", styles["Heading2"]))
            summary_rows = [["Total", "Bomb", "Normal", "Failed"]]
            summary_rows.append([self._text(summary.get("total_detections", 0)), self._text(summary.get("bomb_detections", 0)), self._text(summary.get("normal_detections", 0)), self._text(summary.get("failed_detections", 0))])
            story.append(self._table(summary_rows, [38 * mm] * 4))
        if snapshot.get("description"):
            story.extend([Spacer(1, 3 * mm), Paragraph(self._text(snapshot["description"]), styles["InvestigationBody"])])

        detections = snapshot.get("detections") or []
        if detections:
            story.extend([Spacer(1, 4 * mm), Paragraph("Detection Records", styles["Heading2"])])
            columns = ["id", "predicted_label", "confidence"]
            if "risk_analysis" in (snapshot.get("sections") or []):
                columns.append("risk")
            columns.extend(["model_name", "created_at"])
            rows = [[self._text(label.replace("_", " ").title()) for label in columns]]
            for item in detections:
                values = dict(item)
                risk = item.get("risk") or {}
                values["risk"] = f"{risk.get('score', 'Unavailable')} / {risk.get('level', 'Unavailable')}"
                rows.append([self._text(values.get(key)) for key in columns])
            story.append(self._table(rows, [(A4[0] - 36 * mm) / len(columns)] * len(columns)))

        for section in snapshot.get("sections") or []:
            if section in {"executive_summary", "detection_summary"}:
                continue
            content = snapshot.get(section)
            if content is None:
                continue
            story.extend([Spacer(1, 5 * mm), Paragraph(self._text(section.replace("_", " ").title()), styles["Heading2"])])
            story.extend(self._render_section(content, styles))

        if snapshot.get("report_analyst_notes"):
            story.extend([Spacer(1, 5 * mm), Paragraph("Report Notes", styles["Heading2"]), Paragraph(self._text(snapshot["report_analyst_notes"]), styles["InvestigationBody"])])
        doc.build(story, onFirstPage=self._footer, onLaterPages=self._footer)
        return GeneratedReport(stream.getvalue(), "application/pdf", "pdf")

    def _render_section(self, value: Any, styles) -> list[Any]:
        if isinstance(value, dict):
            rows = [["Field", "Value"]]
            rows.extend([[self._text(key), self._text(item)] for key, item in value.items()])
            return [self._table(rows, [43 * mm, 119 * mm])]
        if isinstance(value, list) and value and all(isinstance(item, dict) for item in value):
            columns = list(dict.fromkeys(key for item in value for key in item.keys()))
            rows = [[self._text(key.replace("_", " ").title()) for key in columns]]
            rows.extend([[self._text(item.get(key)) for key in columns] for item in value])
            width = (A4[0] / mm - 36) / max(1, len(columns))
            return [self._table(rows, [width * mm for _ in columns])]
        if isinstance(value, list):
            return [Paragraph(self._text(item), styles["InvestigationBody"]) for item in value] or [Paragraph("No records were available in the report snapshot.", styles["InvestigationBody"])]
        return [Paragraph(self._text(value), styles["InvestigationBody"])]

    def _table(self, rows: list[list[str]], widths: list[float]) -> Table:
        wrapped_rows = [[Paragraph(cell, self.cell_style) for cell in row] for row in rows]
        table = Table(wrapped_rows, repeatRows=1, colWidths=widths, hAlign="LEFT")
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eaf0ff")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#253b76")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 7),
            ("GRID", (0, 0), (-1, -1), .35, colors.HexColor("#d7deea")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8faff")]),
            ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        return table

    @staticmethod
    def _footer(canvas, document) -> None:
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor("#d7deea"))
        canvas.line(18 * mm, 14 * mm, A4[0] - 18 * mm, 14 * mm)
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#68758a"))
        canvas.drawString(18 * mm, 9 * mm, "Email Bomb Detection Platform · Investigation Report")
        canvas.drawRightString(A4[0] - 18 * mm, 9 * mm, f"Page {document.page}")
        canvas.restoreState()

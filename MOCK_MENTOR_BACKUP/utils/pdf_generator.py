# utils/pdf_generator.py
# Generates PDF performance reports using ReportLab

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import io
from datetime import datetime

def generate_interview_pdf(interview_data, responses, candidate):
    """
    Generate a PDF report for a completed interview.
    Returns bytes of the PDF.
    """
    buffer = io.BytesIO()
    doc    = SimpleDocTemplate(buffer, pagesize=A4,
                               rightMargin=2*cm, leftMargin=2*cm,
                               topMargin=2*cm, bottomMargin=2*cm)

    styles = getSampleStyleSheet()
    story  = []

    # ── Header ────────────────────────────────────────────────
    title_style = ParagraphStyle('Title',
        parent    = styles['Title'],
        fontSize  = 22,
        textColor = colors.HexColor('#1a73e8'),
        alignment = TA_CENTER,
        spaceAfter= 6
    )
    sub_style = ParagraphStyle('Sub',
        parent    = styles['Normal'],
        fontSize  = 11,
        textColor = colors.grey,
        alignment = TA_CENTER,
        spaceAfter= 14
    )

    story.append(Paragraph("🎓 MockMentor", title_style))
    story.append(Paragraph("Smart Interview Preparation & Analytics", sub_style))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#1a73e8')))
    story.append(Spacer(1, 12))

    # ── Candidate Info ────────────────────────────────────────
    heading_style = ParagraphStyle('Heading',
        parent    = styles['Heading2'],
        textColor = colors.HexColor('#1a73e8'),
        spaceAfter= 6
    )
    story.append(Paragraph("Interview Performance Report", heading_style))

    info_data = [
        ['Candidate Name', candidate.get('name', 'N/A')],
        ['Email',          candidate.get('email', 'N/A')],
        ['College',        candidate.get('college', 'N/A')],
        ['Topic',          interview_data.get('topic_name', 'N/A')],
        ['Date',           str(interview_data.get('interview_date', datetime.now().strftime('%Y-%m-%d %H:%M')))],
        ['Total Score',    f"{interview_data.get('total_score', 0):.1f} / 100"],
        ['Duration',       f"{interview_data.get('interview_duration', 0) // 60} min {interview_data.get('interview_duration', 0) % 60} sec"],
    ]

    info_table = Table(info_data, colWidths=[5*cm, 10*cm])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#e8f0fe')),
        ('TEXTCOLOR',  (0,0), (0,-1), colors.HexColor('#1a73e8')),
        ('FONTNAME',   (0,0), (0,-1), 'Helvetica-Bold'),
        ('FONTSIZE',   (0,0), (-1,-1), 10),
        ('ROWBACKGROUNDS', (0,0), (-1,-1), [colors.white, colors.HexColor('#f8f9fa')]),
        ('GRID',       (0,0), (-1,-1), 0.5, colors.lightgrey),
        ('PADDING',    (0,0), (-1,-1), 8),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 16))

    # ── Responses Table ───────────────────────────────────────
    story.append(Paragraph("Question-wise Performance", heading_style))
    story.append(Spacer(1, 6))

    resp_header = ['#', 'Question', 'Your Score', 'Time (sec)']
    resp_data   = [resp_header]
    for i, r in enumerate(responses, 1):
        q_text = r.get('question_text', '')
        if len(q_text) > 70:
            q_text = q_text[:70] + '...'
        resp_data.append([
            str(i),
            q_text,
            f"{r.get('score', 0):.1f}/10",
            str(r.get('time_taken', 0))
        ])

    resp_table = Table(resp_data, colWidths=[1*cm, 11*cm, 2.5*cm, 2.5*cm])
    resp_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1a73e8')),
        ('TEXTCOLOR',  (0,0), (-1,0), colors.white),
        ('FONTNAME',   (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE',   (0,0), (-1,-1), 9),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f8f9fa')]),
        ('GRID',       (0,0), (-1,-1), 0.5, colors.lightgrey),
        ('PADDING',    (0,0), (-1,-1), 6),
        ('ALIGN',      (2,0), (-1,-1), 'CENTER'),
    ]))
    story.append(resp_table)
    story.append(Spacer(1, 16))

    # ── Feedback & Suggestions ────────────────────────────────
    if interview_data.get('feedback'):
        story.append(Paragraph("Feedback", heading_style))
        story.append(Paragraph(interview_data['feedback'], styles['Normal']))
        story.append(Spacer(1, 12))

    # ── Footer ────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=1, color=colors.lightgrey))
    footer_style = ParagraphStyle('Footer',
        parent    = styles['Normal'],
        fontSize  = 8,
        textColor = colors.grey,
        alignment = TA_CENTER,
        spaceBefore=6
    )
    story.append(Paragraph(
        f"Generated by MockMentor on {datetime.now().strftime('%d %B %Y %H:%M')} | mockmentor.app",
        footer_style
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


from flask import Flask, render_template, request, send_file, jsonify
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4, legal
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.units import inch
import re
import os
import uuid

app = Flask(__name__)

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "generated")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def normalize_whitespace(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def smart_format_text(text: str) -> str:
    replacements = {
        r'\bfull stop\b': '.',
        r'\bcomma\b': ',',
        r'\bsemicolon\b': ';',
        r'\bcolon\b': ':',
        r'\bquestion mark\b': '?',
        r'\bexclamation mark\b': '!',
        r'\bnew paragraph\b': '\n\n',
        r'\bnext line\b': '\n',
        r'पूर्ण विराम': '।',
        r'नया पैराग्राफ': '\n\n',
        r'नई लाइन': '\n',
    }
    for pattern, repl in replacements.items():
        text = re.sub(pattern, repl, text, flags=re.IGNORECASE)

    text = normalize_whitespace(text)

    # Capitalize simple Latin-script sentence starts
    parts = re.split(r'(?<=[.!?।])\s+', text)
    parts = [p[:1].upper() + p[1:] if p else p for p in parts]
    text = " ".join(parts)

    return text

def build_formatted_text(title: str, text: str, include_signature: bool, include_stamp: bool) -> str:
    sections = []
    if title.strip():
        sections.append(title.strip().upper())
        sections.append("")
    sections.append(text.strip())
    sections.append("")
    sections.append("Place: ____________________")
    sections.append("Date: _____________________")
    sections.append("")
    if include_signature:
        sections.append("Signature: __________________________")
        sections.append("Authorized Signatory")
        sections.append("")
    if include_stamp:
        sections.append("[STAMP HERE]")
    return "\n".join(sections).strip()

@app.route("/")
def home():
    return render_template("index.html")

@app.post("/preview")
def preview():
    data = request.get_json(force=True)
    title = data.get("title", "LEGAL DOCUMENT")
    text = data.get("text", "")
    include_signature = bool(data.get("signature", True))
    include_stamp = bool(data.get("stamp", True))
    ai_enabled = bool(data.get("ai_enabled", True))

    if ai_enabled:
        text = smart_format_text(text)
    else:
        text = normalize_whitespace(text)

    preview_text = build_formatted_text(title, text, include_signature, include_stamp)
    return jsonify({"preview": preview_text})

@app.post("/generate")
def generate():
    text = request.form.get("text", "")
    title = request.form.get("title", "LEGAL DOCUMENT")
    format_type = request.form.get("format", "legal")
    file_type = request.form.get("filetype", "word")
    ai_enabled = request.form.get("ai_enabled") == "on"
    include_signature = request.form.get("signature") == "on"
    include_stamp = request.form.get("stamp") == "on"

    if ai_enabled:
        text = smart_format_text(text)
    else:
        text = normalize_whitespace(text)

    formatted_text = build_formatted_text(title, text, include_signature, include_stamp)

    uid = uuid.uuid4().hex[:10]
    paper_size = legal if format_type == "legal" else A4

    if file_type == "word":
        filename = f"document_{uid}.docx"
        path = os.path.join(OUTPUT_DIR, filename)
        doc = Document()

        section = doc.sections[0]
        if format_type == "legal":
            section.page_width = Inches(8.5)
            section.page_height = Inches(14)
        else:
            section.page_width = Inches(8.27)
            section.page_height = Inches(11.69)

        section.top_margin = Inches(1)
        section.bottom_margin = Inches(1)
        section.left_margin = Inches(1)
        section.right_margin = Inches(1)

        normal = doc.styles["Normal"]
        normal.font.name = "Times New Roman"
        normal.font.size = Pt(12)

        title_para = doc.add_paragraph()
        title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = title_para.add_run(title.strip().upper())
        run.bold = True
        run.font.name = "Times New Roman"
        run.font.size = Pt(14)

        doc.add_paragraph("")

        body_lines = formatted_text.split("\n")
        skip_first_title = True
        for line in body_lines:
            if skip_first_title and line.strip().upper() == title.strip().upper():
                skip_first_title = False
                continue
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.line_spacing = 1.5
            p.paragraph_format.space_after = Pt(8)
            p.add_run(line)

        doc.save(path)
    else:
        filename = f"document_{uid}.pdf"
        path = os.path.join(OUTPUT_DIR, filename)
        pdf = SimpleDocTemplate(
            path,
            pagesize=paper_size,
            leftMargin=72,
            rightMargin=72,
            topMargin=72,
            bottomMargin=72,
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "LegalTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=14,
            alignment=TA_CENTER,
            spaceAfter=16,
        )
        body_style = ParagraphStyle(
            "LegalBody",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=11,
            leading=17,
            alignment=TA_LEFT,
            spaceAfter=10,
        )

        story = [Paragraph(title.strip().upper(), title_style), Spacer(1, 4)]
        body_lines = formatted_text.split("\n")
        skip_first_title = True
        for line in body_lines:
            if skip_first_title and line.strip().upper() == title.strip().upper():
                skip_first_title = False
                continue
            if line.strip():
                safe_line = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                story.append(Paragraph(safe_line, body_style))
            else:
                story.append(Spacer(1, 8))
        pdf.build(story)

    return send_file(path, as_attachment=True, download_name=filename)

if __name__ == "__main__":
    app.run(debug=True)

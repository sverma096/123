from flask import Flask, render_template, request, send_file
from docx import Document
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
import re

app = Flask(__name__)

def ai_format_text(text):
    text = text.replace("full stop", ".")
    text = text.replace("comma", ",")
    text = text.replace("next line", "\n")
    text = text.replace("new paragraph", "\n\n")

    sentences = re.split(r'(?<=[.!?]) +', text)
    return ' '.join(s.capitalize() for s in sentences)

def legal_format(text):
    return f"""
LEGAL DOCUMENT

{text}

------------------------------
Place: ___________
Date: ___________

Signature: ___________________

[STAMP HERE]
"""

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/generate", methods=["POST"])
def generate():
    text = request.form["text"]
    format_type = request.form["format"]
    filetype = request.form["filetype"]

    text = ai_format_text(text)

    if format_type == "legal":
        text = legal_format(text)

    if filetype == "word":
        filename = "output.docx"
        doc = Document()
        doc.add_paragraph(text)
        doc.save(filename)
    else:
        filename = "output.pdf"
        doc = SimpleDocTemplate(filename, pagesize=A4)
        styles = getSampleStyleSheet()

        content = []
        for line in text.split("\n"):
            content.append(Paragraph(line, styles["Normal"]))
            content.append(Spacer(1, 10))

        doc.build(content)

    return send_file(filename, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)

from flask import Flask, render_template, request, send_file, jsonify
from docx import Document
from docx.shared import Pt
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4, legal
import os, re, uuid

app = Flask(__name__)
OUTPUT = "generated"
os.makedirs(OUTPUT, exist_ok=True)

def format_text(text):
    text = text.replace("full stop", ".").replace("comma", ",")
    text = text.replace("new paragraph", "\n\n").replace("next line", "\n")
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def build_doc(title, text, sign, stamp):
    lines = [
        title.upper(), "",
        text,
        "",
        "Place: __________",
        "Date: __________",
        ""
    ]
    if sign:
        lines += ["Signature: __________", ""]
    if stamp:
        lines += ["[STAMP HERE]"]
    return "\n".join(lines)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/preview", methods=["POST"])
def preview():
    data = request.json
    text = format_text(data["text"])
    doc = build_doc(data["title"], text, data["sign"], data["stamp"])
    return jsonify({"preview": doc})

@app.route("/generate", methods=["POST"])
def generate():
    text = format_text(request.form["text"])
    title = request.form["title"]
    filetype = request.form["filetype"]
    fmt = request.form["format"]
    sign = "sign" in request.form
    stamp = "stamp" in request.form

    final = build_doc(title, text, sign, stamp)

    name = f"{uuid.uuid4().hex[:6]}"

    if filetype == "word":
        file = f"{OUTPUT}/{name}.docx"
        doc = Document()
        style = doc.styles["Normal"]
        style.font.size = Pt(12)
        doc.add_paragraph(final)
        doc.save(file)
    else:
        file = f"{OUTPUT}/{name}.pdf"
        doc = SimpleDocTemplate(file, pagesize=(legal if fmt=="legal" else A4))
        styles = getSampleStyleSheet()
        content = []
        for l in final.split("\n"):
            content.append(Paragraph(l, styles["Normal"]))
            content.append(Spacer(1,10))
        doc.build(content)

    return send_file(file, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)

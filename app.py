from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os, uuid, json
from appwrite.input_file import InputFile

from model import predict_prakriti
from appwrite_client import database, storage, DATABASE_ID, COLLECTION_ID, BUCKET_ID

from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image,
    Table, TableStyle
)
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# --------------------------------------------------
# QUESTION TEXT (for PDF display)
# --------------------------------------------------
QUESTION_MAP = {
    "1": "How would you describe your body frame?",
    "2": "How does your body weight change over time?",
    "3": "How is your appetite usually?",
    "4": "How is your digestion after meals?",
    "5": "How do you generally feel after eating?",
    "6": "Bowel movements?"
}

# --------------------------------------------------
# QUESTION → COLUMN (q1, q2, q3...)
# --------------------------------------------------
QUESTION_COLUMN_MAP = {
    "1": "q1",
    "2": "q2",
    "3": "q3",
    "4": "q4",
    "5": "q5",
    "6": "q6"
}

# -----------------------------
# Home
# -----------------------------
@app.route("/")
def home():
    return "Prakriti API Running with Appwrite"

# -----------------------------
# Upload + Predict
# -----------------------------
@app.route("/predict", methods=["POST"])
def predict():
    try:
        image = request.files["image"]
        answers_raw = request.form.get("answers")  # JSON string
        name = request.form.get("name")
        age = int(request.form.get("age"))

        parsed_answers = json.loads(answers_raw)

        # ---------------- Save image ----------------
        image_filename = f"{uuid.uuid4()}.png"
        image_path = os.path.join(UPLOAD_FOLDER, image_filename)
        image.save(image_path)

        # ---------------- Upload image ----------------
        image_upload = storage.create_file(
            bucket_id=BUCKET_ID,
            file_id="unique()",
            file=InputFile.from_path(image_path)
        )
        image_id = image_upload["$id"]

        # ---------------- Predict ----------------
        result = predict_prakriti(image_path, answers_raw)

        # ---------------- Generate PDF ----------------
        pdf_filename = f"{uuid.uuid4()}.pdf"
        pdf_path = os.path.join(UPLOAD_FOLDER, pdf_filename)
        generate_pdf(pdf_path, name, age, answers_raw, result, image_path)

        # ---------------- Upload PDF ----------------
        pdf_upload = storage.create_file(
            bucket_id=BUCKET_ID,
            file_id="unique()",
            file=InputFile.from_path(pdf_path)
        )
        pdf_id = pdf_upload["$id"]

        # ---------------- Map answers → q1, q2, ... ----------------
        answer_columns = {}

        for qid, selected_opts in parsed_answers.items():
            column_name = QUESTION_COLUMN_MAP.get(qid)
            if column_name:
                answer_columns[column_name] = ", ".join(selected_opts)

        # ---------------- Save record ----------------
        database.create_document(
            database_id=DATABASE_ID,
            collection_id=COLLECTION_ID,
            document_id="unique()",
            data={
                "name": name,
                "age": age,
                **answer_columns,
                "prakriti": result["prakriti"],
                "confidence": result["confidence"],
                "image_id": image_id,
                "pdf_id": pdf_id
            }
        )

        return jsonify({
            "prakriti": result["prakriti"],
            "confidence": result["confidence"],
            "pdf_id": pdf_id
        })

    except Exception as e:
        print("ERROR:", e)
        return jsonify({"error": str(e)}), 500

# -----------------------------
# Download PDF
# -----------------------------
@app.route("/download/<pdf_id>")
def download_pdf(pdf_id):
    try:
        file_bytes = storage.get_file_download(
            bucket_id=BUCKET_ID,
            file_id=pdf_id
        )

        temp_path = f"/tmp/{pdf_id}.pdf"
        with open(temp_path, "wb") as f:
            f.write(file_bytes)

        return send_file(
            temp_path,
            as_attachment=True,
            download_name="prakriti_report.pdf"
        )

    except Exception as e:
        print("DOWNLOAD ERROR:", e)
        return jsonify({"error": str(e)}), 500

# -----------------------------
# PDF Generator
# -----------------------------
def generate_pdf(path, name, age, answers, result, image_path):

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "title",
        fontSize=24,
        alignment=1,
        textColor=colors.white
    )

    table_header_style = ParagraphStyle(
        "tableHeader",
        fontSize=12,
        textColor=colors.white,
        alignment=1
    )

    table_cell_style = ParagraphStyle(
        "tableCell",
        fontSize=11
    )

    result_style = ParagraphStyle(
        "result",
        fontSize=16,
        alignment=1,
        textColor=colors.white
    )

    doc = SimpleDocTemplate(path, pagesize=A4)
    elements = []

    # Header
    header = Table([[Paragraph("PRAKRITI ASSESSMENT REPORT", title_style)]])
    header.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), colors.HexColor("#1e3a8a")),
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
        ("PADDING", (0,0), (-1,-1), 16),
    ]))
    elements.append(header)
    elements.append(Spacer(1, 20))

    # Answers table
    parsed_answers = json.loads(answers)
    table_data = [[
        Paragraph("Question", table_header_style),
        Paragraph("Answer", table_header_style)
    ]]

    for qid, selected_opts in parsed_answers.items():
        table_data.append([
            Paragraph(QUESTION_MAP.get(qid, f"Question {qid}"), table_cell_style),
            Paragraph(", ".join(selected_opts), table_cell_style)
        ])

    answers_table = Table(table_data, colWidths=[3.5*inch, 3.5*inch])
    answers_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#2563eb")),
        ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
    ]))

    elements.append(answers_table)
    elements.append(Spacer(1, 25))

    # Result
    result_table = Table([[
        Paragraph(
            f"<b>Prakriti:</b> {result['prakriti']} &nbsp;&nbsp; "
            f"<b>Confidence:</b> {result['confidence']}",
            result_style
        )
    ]])

    result_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), colors.HexColor("#047857")),
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
        ("PADDING", (0,0), (-1,-1), 16),
    ]))

    elements.append(result_table)
    doc.build(elements)

# -----------------------------
# Run
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)

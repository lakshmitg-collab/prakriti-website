from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os, uuid, json
from appwrite.input_file import InputFile

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
# QUESTION TEXT (for PDF)
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
    return "Prakriti Data Collection API Running"

# -----------------------------
# Upload + Store ONLY
# -----------------------------
@app.route("/submit", methods=["POST"])
def submit():
    try:
        image = request.files["image"]
        answers_raw = request.form.get("answers")
        name = request.form.get("name")
        age = int(request.form.get("age"))

        parsed_answers = json.loads(answers_raw)

        # ---------------- Save image locally ----------------
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

        # ---------------- Generate PDF (no prediction) ----------------
        pdf_filename = f"{uuid.uuid4()}.pdf"
        pdf_path = os.path.join(UPLOAD_FOLDER, pdf_filename)
        generate_pdf(pdf_path, name, age, answers_raw, image_path)

        pdf_upload = storage.create_file(
            bucket_id=BUCKET_ID,
            file_id="unique()",
            file=InputFile.from_path(pdf_path)
        )
        pdf_id = pdf_upload["$id"]

        # ---------------- Map answers → q1, q2, ... ----------------
        answer_columns = {}

        for qid, selected_opts in parsed_answers.items():
            col = QUESTION_COLUMN_MAP.get(qid)
            if col:
                answer_columns[col] = ", ".join(selected_opts)

        # ---------------- Save ONLY RAW DATA ----------------
        database.create_document(
            database_id=DATABASE_ID,
            collection_id=COLLECTION_ID,  # data_collection
            document_id="unique()",
            data={
                "name": name,
                "age": age,
                **answer_columns,
                "image_id": image_id,
                "pdf_id": pdf_id
            }
        )

        return jsonify({
            "status": "success",
            "message": "Data collected successfully",
            "pdf_id": pdf_id
        })

    except Exception as e:
        print("ERROR:", e)
        return jsonify({"error": str(e)}), 500

# -----------------------------
# PDF Generator (NO PREDICTION)
# -----------------------------
def generate_pdf(path, name, age, answers, image_path):

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

    doc = SimpleDocTemplate(path, pagesize=A4)
    elements = []

    # Header
    header = Table([[Paragraph("PRAKRITI DATA COLLECTION", title_style)]])
    header.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), colors.HexColor("#1e3a8a")),
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
        ("PADDING", (0,0), (-1,-1), 16),
    ]))
    elements.append(header)
    elements.append(Spacer(1, 20))

    # Answers
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
    doc.build(elements)

# -----------------------------
# Run
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)

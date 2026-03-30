from pathlib import Path
from google.cloud import firestore
from extract_data import parse_course_pdf

db = firestore.Client(project="buoyant-world-491810-n6")

def write_course_to_firestore(course: dict):
    id = course["class_id"] + " " + course["title"]
    doc_ref = db.collection("courses").document(id)
    doc_ref.set({
        **course,
        "updated_at": firestore.SERVER_TIMESTAMP,
    })

def parse_and_upload_all(folder_path):
    pdf_files = list(Path(folder_path).glob("*.pdf"))
    
    if not pdf_files:
        print("No PDFs found")
        return
    print("Processing...")

    for pdf_file in pdf_files:
        course = parse_course_pdf(str(pdf_file))
        courses_ref = db.collection("courses")
        query = (
            courses_ref
            .where("class_id", "==", course["class_id"])
            .where("title", "==", course["title"])
        )

        docs = list(query.stream())
        if len(docs) == 0:
            write_course_to_firestore(course)
    
    print(f"Done — {len(pdf_files)} courses uploaded")

parse_and_upload_all("data")

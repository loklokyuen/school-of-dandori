from pathlib import Path
import csv
from pipeline.extract_data import parse_course_pdf

def parse_all_courses(folder_path):
    results = []
    pdf_files = Path(folder_path).glob("*.pdf")
    
    for pdf_file in pdf_files:
        course = parse_course_pdf(str(pdf_file))
        results.append(course)
    
    return results

courses = parse_all_courses("data")

with open("courses.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=courses[0].keys())
    writer.writeheader()
    for course in courses:
        row = {
            k: " | ".join(v) if isinstance(v, list) else v
            for k, v in course.items()
        }
        writer.writerow(row)
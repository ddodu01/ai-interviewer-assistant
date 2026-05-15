from pathlib import Path
import pandas as pd

root = Path.cwd()

jd_dir = root / "data" / "job_descriptions"
cv_dir = root / "data" / "cvs"
skills_path = root / "data" / "skills_dataset.csv"

pdf_jds_dir = root / "data" / "test_documents" / "pdf_jds"
pdf_cvs_dir = root / "data" / "test_documents" / "pdf_cvs"
docx_jds_dir = root / "data" / "test_documents" / "docx_jds"
docx_cvs_dir = root / "data" / "test_documents" / "docx_cvs"

jd_files = list(jd_dir.glob("*.txt"))
cv_files = list(cv_dir.glob("*.txt"))
skills = pd.read_csv(skills_path)

print("JD txt files:", len(jd_files))
print("CV txt files:", len(cv_files))
print("Skills:", len(skills))

print("PDF JD files:", len(list(pdf_jds_dir.glob("*.pdf"))) if pdf_jds_dir.exists() else 0)
print("PDF CV files:", len(list(pdf_cvs_dir.glob("*.pdf"))) if pdf_cvs_dir.exists() else 0)
print("DOCX JD files:", len(list(docx_jds_dir.glob("*.docx"))) if docx_jds_dir.exists() else 0)
print("DOCX CV files:", len(list(docx_cvs_dir.glob("*.docx"))) if docx_cvs_dir.exists() else 0)
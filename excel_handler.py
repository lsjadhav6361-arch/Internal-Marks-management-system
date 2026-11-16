
from __future__ import annotations
from io import BytesIO
import pandas as pd
REQUIRED_STUDENT_COLUMNS = ['Academic Year', 'Course', 'Semester', 'Register No', 'Student Name', 'DOB', 'Section']

def _build_template(rows, sheet_name):
    df = pd.DataFrame(rows)
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
    buffer.seek(0)
    return buffer

def build_student_template():
    return _build_template([{'Academic Year':'2025-2028','Course':'BCA','Semester':1,'Register No':'BCA001','Student Name':'Student Name','DOB':'2005-01-15','Section':'A'}], 'Students')

def build_teacher_template():
    return _build_template([{'Name':'Anita Madam','Email':'anita@example.com','Phone':'9876543210','Qualification':'MCA','Experience':'5 years','Notes':'Theory faculty'}], 'Teachers')

def build_subject_template():
    return _build_template([{'Academic Year':'2025-2028','Course':'BCA','Semester':3,'Subject Code':'BCA301','Subject Name':'Python Programming','Subject Type':'theory'}], 'Subjects')

def build_course_template():
    return _build_template([{'Course Name':'BCA'},{'Course Name':'BSc'}], 'Courses')

def build_academic_year_template():
    return _build_template([{'Academic Year':'2025-2028'},{'Academic Year':'2026-2029'}], 'AcademicYears')

def normalize_student_dataframe(file):
    df = pd.read_excel(file)
    mapping = {str(column).strip().lower(): column for column in df.columns}
    expected = {'academic year':'Academic Year','course':'Course','semester':'Semester','register no':'Register No','reg_no':'Register No','register_no':'Register No','student name':'Student Name','name':'Student Name','dob':'DOB','section':'Section'}
    selected = {}
    for source_key, target_key in expected.items():
        if source_key in mapping:
            selected[mapping[source_key]] = target_key
    renamed = df.rename(columns=selected)
    missing = [col for col in REQUIRED_STUDENT_COLUMNS[:-1] if col not in renamed.columns]
    if missing:
        raise ValueError(f"Excel is missing required columns: {', '.join(missing)}")
    if 'Section' not in renamed.columns:
        renamed['Section'] = ''
    renamed = renamed[REQUIRED_STUDENT_COLUMNS].copy()
    renamed['Register No'] = renamed['Register No'].astype(str).str.strip()
    renamed['Student Name'] = renamed['Student Name'].astype(str).str.strip()
    renamed['DOB'] = renamed['DOB'].astype(str).str.strip()
    renamed['Academic Year'] = renamed['Academic Year'].astype(str).str.strip()
    renamed['Course'] = renamed['Course'].astype(str).str.strip()
    renamed['Section'] = renamed['Section'].astype(str).str.strip()
    renamed['Semester'] = pd.to_numeric(renamed['Semester'], errors='coerce')
    duplicate_reg = renamed['Register No'][renamed['Register No'].duplicated()].unique().tolist()
    if duplicate_reg:
        raise ValueError(f"Duplicate register numbers found in upload: {', '.join(duplicate_reg)}")
    invalid_rows = renamed[(renamed['Register No'] == '') | (renamed['Student Name'] == '') | (renamed['DOB'] == '') | (renamed['Academic Year'] == '') | (renamed['Course'] == '') | (renamed['Semester'].isna())]
    if not invalid_rows.empty:
        raise ValueError('Excel contains blank or invalid Academic Year / Course / Semester / Register No / Student Name / DOB values.')
    renamed['Semester'] = renamed['Semester'].astype(int)
    return renamed

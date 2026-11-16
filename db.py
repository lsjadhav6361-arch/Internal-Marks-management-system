from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterable

import mysql.connector
from flask import current_app


@contextmanager
def get_db():
    conn = mysql.connector.connect(
        host=current_app.config['MYSQL_HOST'],
        port=current_app.config['MYSQL_PORT'],
        user=current_app.config['MYSQL_USER'],
        password=current_app.config['MYSQL_PASSWORD'],
        database=current_app.config['MYSQL_DATABASE'],
        autocommit=current_app.config.get('MYSQL_AUTOCOMMIT', False),
    )
    try:
        yield conn
    finally:
        conn.close()


def fetch_all(query: str, params: Iterable[Any] | None = None):
    with get_db() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params or ())
        rows = cursor.fetchall()
        cursor.close()
        return rows


def fetch_one(query: str, params: Iterable[Any] | None = None):
    with get_db() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params or ())
        row = cursor.fetchone()
        cursor.close()
        return row



def execute_write(query: str, params: Iterable[Any] | None = None):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params or ())
        conn.commit()
        lastrowid = cursor.lastrowid
        cursor.close()
        return lastrowid


def table_exists(table_name: str) -> bool:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES LIKE %s", (table_name,))
        exists = cursor.fetchone() is not None
        cursor.close()
        return exists


def get_columns(table_name: str):
    if not table_exists(table_name):
        return []
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(f"SHOW COLUMNS FROM `{table_name}`")
        columns = [row[0] for row in cursor.fetchall()]
        cursor.close()
        return columns


SCHEMA_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS users (
        id INT PRIMARY KEY AUTO_INCREMENT,
        role VARCHAR(30) NOT NULL,
        username VARCHAR(120) NOT NULL UNIQUE,
        password VARCHAR(255) NOT NULL,
        display_name VARCHAR(120) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB;
    """,
    """
    CREATE TABLE IF NOT EXISTS academic_years (
        id INT PRIMARY KEY AUTO_INCREMENT,
        label VARCHAR(50) NOT NULL UNIQUE,
        is_active TINYINT(1) NOT NULL DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB;
    """,
    """
    CREATE TABLE IF NOT EXISTS courses (
        id INT PRIMARY KEY AUTO_INCREMENT,
        course_name VARCHAR(80) NOT NULL UNIQUE,
        is_active TINYINT(1) NOT NULL DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB;
    """,
    """
    CREATE TABLE IF NOT EXISTS teachers (
        id INT PRIMARY KEY AUTO_INCREMENT,
        name VARCHAR(120) NOT NULL,
        email VARCHAR(120) NOT NULL UNIQUE,
        password VARCHAR(255) NOT NULL DEFAULT 'demo123',
        phone VARCHAR(30),
        qualification VARCHAR(120),
        experience VARCHAR(80),
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB;
    """,
    """
    CREATE TABLE IF NOT EXISTS subjects (
        id INT PRIMARY KEY AUTO_INCREMENT,
        academic_year VARCHAR(50) NOT NULL,
        course VARCHAR(80) NOT NULL,
        semester INT NOT NULL,
        subject_code VARCHAR(40),
        subject_name VARCHAR(120) NOT NULL,
        subject_type VARCHAR(30) NOT NULL DEFAULT 'theory',
        is_active TINYINT(1) NOT NULL DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE KEY unique_subject_context (academic_year, course, semester, subject_name)
    ) ENGINE=InnoDB;
    """,
    """
    CREATE TABLE IF NOT EXISTS teacher_allocations (
        id INT PRIMARY KEY AUTO_INCREMENT,
        teacher_id INT NOT NULL,
        academic_year VARCHAR(50) NOT NULL,
        course VARCHAR(80) NOT NULL,
        semester INT NOT NULL,
        subject_name VARCHAR(120) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT fk_teacher_allocations_teacher FOREIGN KEY (teacher_id) REFERENCES teachers(id) ON DELETE CASCADE,
        UNIQUE KEY unique_teacher_allocation (teacher_id, academic_year, course, semester, subject_name)
    ) ENGINE=InnoDB;
    """,
    """
    CREATE TABLE IF NOT EXISTS students (
        id INT PRIMARY KEY AUTO_INCREMENT,
        academic_year VARCHAR(50) NOT NULL,
        course VARCHAR(80) NOT NULL,
        semester INT NOT NULL,
        reg_no VARCHAR(80) NOT NULL UNIQUE,
        student_name VARCHAR(150) NOT NULL,
        dob VARCHAR(40) NOT NULL,
        section VARCHAR(30),
        is_active TINYINT(1) NOT NULL DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    ) ENGINE=InnoDB;
    """,
    """
    CREATE TABLE IF NOT EXISTS ia_settings (
        id INT PRIMARY KEY AUTO_INCREMENT,
        academic_year VARCHAR(50) NOT NULL,
        course VARCHAR(80) NOT NULL,
        semester INT NOT NULL,
        assignment_max DECIMAL(6,2) NOT NULL DEFAULT 0,
        ia1_max DECIMAL(6,2) NOT NULL DEFAULT 0,
        ia1_convert_to DECIMAL(6,2) NOT NULL DEFAULT 0,
        ia2_max DECIMAL(6,2) NOT NULL DEFAULT 0,
        ia2_convert_to DECIMAL(6,2) NOT NULL DEFAULT 0,
        practical_enabled TINYINT(1) NOT NULL DEFAULT 0,
        practical_count INT NOT NULL DEFAULT 0,
        practical_max DECIMAL(6,2) NOT NULL DEFAULT 0,
        total_marks DECIMAL(6,2) NOT NULL DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        UNIQUE KEY unique_ia_context (academic_year, course, semester)
    ) ENGINE=InnoDB;
    """,
    """
    CREATE TABLE IF NOT EXISTS internal_marks (
        id INT PRIMARY KEY AUTO_INCREMENT,
        student_id INT NOT NULL,
        teacher_id INT,
        academic_year VARCHAR(50) NOT NULL,
        course VARCHAR(80) NOT NULL,
        semester INT NOT NULL,
        subject_name VARCHAR(120) NOT NULL,
        assignment_marks DECIMAL(6,2) DEFAULT 0,
        ia1_marks DECIMAL(6,2) DEFAULT 0,
        ia2_marks DECIMAL(6,2) DEFAULT 0,
        practical_marks DECIMAL(6,2) DEFAULT 0,
        ia1_converted DECIMAL(6,2) DEFAULT 0,
        ia2_converted DECIMAL(6,2) DEFAULT 0,
        grand_total DECIMAL(6,2) DEFAULT 0,
        query_text TEXT NULL,
        status VARCHAR(30) NOT NULL DEFAULT 'draft',
        confirmed_at DATETIME NULL,
        source_type VARCHAR(30) NOT NULL DEFAULT 'manual',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        CONSTRAINT fk_internal_marks_student FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
        CONSTRAINT fk_internal_marks_teacher FOREIGN KEY (teacher_id) REFERENCES teachers(id) ON DELETE SET NULL,
        UNIQUE KEY unique_marks_context (student_id, academic_year, course, semester, subject_name)
    ) ENGINE=InnoDB;
    """,
    """
    CREATE TABLE IF NOT EXISTS student_queries (
        id INT PRIMARY KEY AUTO_INCREMENT,
        student_id INT NOT NULL,
        subject_name VARCHAR(120) NULL,
        query_text TEXT NOT NULL,
        status VARCHAR(30) NOT NULL DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        solved_at TIMESTAMP NULL DEFAULT NULL,
        solved_by_teacher_id INT NULL DEFAULT NULL,
        CONSTRAINT fk_student_queries_student FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
        CONSTRAINT fk_student_queries_teacher FOREIGN KEY (solved_by_teacher_id) REFERENCES teachers(id) ON DELETE SET NULL
    ) ENGINE=InnoDB;
    """,
]


def ensure_internal_marks_teacher_columns(conn):
    cursor = conn.cursor()
    cursor.execute("SHOW COLUMNS FROM internal_marks")
    existing = {row[0] for row in cursor.fetchall()}

    if "query_text" not in existing:
        cursor.execute("ALTER TABLE internal_marks ADD COLUMN query_text TEXT NULL AFTER grand_total")

    if "confirmed_at" not in existing:
        cursor.execute("ALTER TABLE internal_marks ADD COLUMN confirmed_at DATETIME NULL AFTER status")

    if "source_type" not in existing:
        cursor.execute(
            "ALTER TABLE internal_marks ADD COLUMN source_type VARCHAR(30) NOT NULL DEFAULT 'manual' AFTER confirmed_at"
        )

    cursor.close()


def seed_default_users(conn):
    """Seed the users table with initial Admin and HOD accounts.

    This function hashes the seeded passwords using Werkzeug's
    ``generate_password_hash`` to avoid storing credentials in plain text.
    If the record already exists, only the display_name is updated and the
    password is left unchanged.  This ensures existing hashed passwords
    remain intact when ``init_db`` is called multiple times.
    """
    from werkzeug.security import generate_password_hash

    cursor = conn.cursor()
    users = [
        ('admin', 'admin@imms.local', 'admin123', 'Admin User'),
        ('hod', 'hod@imms.local', 'hod123', 'HOD User'),
    ]
    for role, username, password, display_name in users:
        hashed = generate_password_hash(password)
        cursor.execute(
            """
            INSERT INTO users (role, username, password, display_name)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE display_name = VALUES(display_name)
            """,
            (role, username, hashed, display_name),
        )
    cursor.close()


def seed_lookup_data(conn):
    cursor = conn.cursor()
    for label in ('2023-2026', '2024-2027', '2025-2028'):
        cursor.execute(
            "INSERT INTO academic_years (label) VALUES (%s) ON DUPLICATE KEY UPDATE label = VALUES(label)",
            (label,),
        )
    for course in ('BCA', 'BSc'):
        cursor.execute(
            "INSERT INTO courses (course_name) VALUES (%s) ON DUPLICATE KEY UPDATE course_name = VALUES(course_name)",
            (course,),
        )
    cursor.close()


def seed_teacher_module_data(conn):
    from werkzeug.security import generate_password_hash

    cursor = conn.cursor()
    # Insert a demo teacher.  Passwords are now hashed on insert.  On duplicate
    # key, keep the existing password to avoid rehashing a hashed value.
    demo_password = generate_password_hash('demo123')
    cursor.execute(
        """
        INSERT INTO teachers (id, name, email, password, phone, qualification, experience, notes)
        VALUES (1, 'Demo Teacher', 'teacher@example.com', %s, NULL, 'MCA', '2 Years', 'Teacher demo account')
        ON DUPLICATE KEY UPDATE name = VALUES(name)
        """,
        (demo_password,)
    )
    subjects = [
        ('2025-2028', 'BCA', 3, 'BCA301', 'DBMS', 'theory'),
        ('2025-2028', 'BCA', 3, 'BCA302', 'Python', 'theory'),
    ]
    for academic_year, course, semester, code, name, s_type in subjects:
        cursor.execute(
            """
            INSERT INTO subjects (academic_year, course, semester, subject_code, subject_name, subject_type)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE subject_code = VALUES(subject_code), subject_type = VALUES(subject_type)
            """,
            (academic_year, course, semester, code, name, s_type),
        )
    for subject_name in ('DBMS', 'Python'):
        cursor.execute(
            """
            INSERT INTO teacher_allocations (teacher_id, academic_year, course, semester, subject_name)
            VALUES (1, '2025-2028', 'BCA', 3, %s)
            ON DUPLICATE KEY UPDATE subject_name = VALUES(subject_name)
            """,
            (subject_name,),
        )
    students = [
        ('2025-2028', 'BCA', 3, 'BCA001', 'Asha Patil', '2005-01-10', 'A'),
        ('2025-2028', 'BCA', 3, 'BCA002', 'Kiran Mane', '2005-02-14', 'A'),
        ('2025-2028', 'BCA', 3, 'BCA003', 'Manoj Patil', '2005-03-18', 'A'),
    ]
    for row in students:
        cursor.execute(
            """
            INSERT INTO students (academic_year, course, semester, reg_no, student_name, dob, section)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE student_name = VALUES(student_name), section = VALUES(section)
            """,
            row,
        )
    cursor.execute(
        """
        INSERT INTO ia_settings (
            academic_year, course, semester,
            assignment_max, ia1_max, ia1_convert_to, ia2_max, ia2_convert_to,
            practical_enabled, practical_count, practical_max, total_marks
        ) VALUES ('2025-2028', 'BCA', 3, 5, 40, 5, 80, 10, 0, 0, 0, 20)
        ON DUPLICATE KEY UPDATE
            assignment_max = VALUES(assignment_max),
            ia1_max = VALUES(ia1_max),
            ia1_convert_to = VALUES(ia1_convert_to),
            ia2_max = VALUES(ia2_max),
            ia2_convert_to = VALUES(ia2_convert_to),
            practical_enabled = VALUES(practical_enabled),
            practical_count = VALUES(practical_count),
            practical_max = VALUES(practical_max),
            total_marks = VALUES(total_marks)
        """
    )
    cursor.close()


def init_db():
    root_conn = mysql.connector.connect(
        host=current_app.config['MYSQL_HOST'],
        port=current_app.config['MYSQL_PORT'],
        user=current_app.config['MYSQL_USER'],
        password=current_app.config['MYSQL_PASSWORD'],
        autocommit=True,
    )
    root_cursor = root_conn.cursor()
    root_cursor.execute(
        f"CREATE DATABASE IF NOT EXISTS `{current_app.config['MYSQL_DATABASE']}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
    )
    root_cursor.close()
    root_conn.close()

    with get_db() as conn:
        cursor = conn.cursor()
        for statement in SCHEMA_STATEMENTS:
            cursor.execute(statement)
        cursor.execute("SHOW COLUMNS FROM ia_settings LIKE 'practical_count'")
        if cursor.fetchone() is None:
            cursor.execute("ALTER TABLE ia_settings ADD COLUMN practical_count INT NOT NULL DEFAULT 0 AFTER practical_enabled")
        ensure_internal_marks_teacher_columns(conn)
        cursor.close()
        seed_default_users(conn)
        seed_lookup_data(conn)
        seed_teacher_module_data(conn)
        conn.commit()

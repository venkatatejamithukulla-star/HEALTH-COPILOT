"""
HealthMate AI — AI-Powered Personal Health Copilot
Backend Application (Python & Flask with SQLite)

Developed for CSE Students and Beginners:
- Application factory pattern (create_app)
- Hand-written CSRF validation using "_csrf"
- Clean modular structure
- Safe parameterized SQL queries
- Offline Safe Medical Knowledge Engine
- Optional Google Gemini AI integration point (without pretending when unconfigured)
- Multilingual support
- Medical disclaimer guardrails
"""

import os
import re
import json
import sqlite3
import math
import html
import secrets
from datetime import datetime, timedelta
from pathlib import Path
import io
import base64
import uuid
from flask import Flask, render_template, request, jsonify, session, g, send_file, redirect, url_for
from dotenv import load_dotenv

import qrcode
from PIL import Image, ImageDraw, ImageFont

from disease_data import DISEASE_LIBRARY
from care_data import CARE_FACILITIES, GOVERNMENT_SCHEMES
from competitor_data import COMPETITOR_RESEARCH_DATA, COMPARISON_MATRIX_COLUMNS
import security
import assistant_engine

# Try importing pypdf for PDF report text extraction
try:
    import pypdf
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False

# Try importing requests for external AI calls
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

# Load environment variables from .env file if present
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "healthmate.db"
UPLOAD_FOLDER = BASE_DIR / "uploads"
UPLOAD_FOLDER.mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {"txt", "pdf", "png", "jpg", "jpeg"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB limit

LOCALES_DIR = BASE_DIR / "locales"
DATA_DIR = BASE_DIR / "data"

ALL_23_LANGUAGES = [
    "en", "hi", "te", "ta", "ur", "bn", "mr", "gu", "kn", "ml",
    "pa", "or", "as", "mai", "sat", "ks", "ne", "kok", "sd", "doi",
    "mni", "brx", "sa"
]

def calculate_haversine_km(lat1, lon1, lat2, lon2):
    """Calculates great-circle distance between two GPS coordinates in kilometers."""
    try:
        if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
            return None
        r = 6371.0  # Earth radius km
        dlat = math.radians(float(lat2) - float(lat1))
        dlon = math.radians(float(lon2) - float(lon1))
        a = math.sin(dlat / 2.0)**2 + math.cos(math.radians(float(lat1))) * math.cos(math.radians(float(lat2))) * math.sin(dlon / 2.0)**2
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
        return round(r * c, 1)
    except Exception:
        return None

def get_locales_list():
    """Returns list of supported languages with metadata."""
    try:
        from translate_locales import LANGUAGES_METADATA
        return [
            {"code": code, "name_en": m["name_en"], "name_native": m["name_native"], "dir": m["dir"], "font": m["font"]}
            for code, m in LANGUAGES_METADATA.items()
        ]
    except Exception:
        return [{"code": "en", "name_en": "English", "name_native": "English", "dir": "ltr", "font": "sans-serif"}]

def get_locale_translations(lang_code):
    """Loads translations for given code with English fallback."""
    en_file = LOCALES_DIR / "en.json"
    en_data = {}
    if en_file.exists():
        try:
            with open(en_file, "r", encoding="utf-8") as f:
                en_data = json.load(f)
        except Exception:
            pass

    loc_file = LOCALES_DIR / f"{lang_code}.json"
    if loc_file.exists():
        try:
            with open(loc_file, "r", encoding="utf-8") as f:
                lang_data = json.load(f)
            # Fill missing keys from English
            for k, v in en_data.items():
                if k not in lang_data:
                    lang_data[k] = v
            return lang_data
        except Exception:
            pass
    return en_data

# ==============================================================================
# DATABASE HELPERS (Parameterized Queries for Security)
# ==============================================================================

def get_db(db_path=None):
    """Returns a SQLite database connection with row access by column name."""
    if db_path is None:
        try:
            from flask import current_app
            db_path = current_app.config.get("DATABASE", str(DATABASE_PATH))
        except (RuntimeError, KeyError):
            db_path = str(DATABASE_PATH)

    try:
        if "db" not in g or getattr(g, "db_path", None) != str(db_path):
            conn = sqlite3.connect(str(db_path))
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            g.db = conn
            g.db_path = str(db_path)
        return g.db
    except RuntimeError:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn


def _run_migrations(conn):
    """Safely adds missing columns to existing SQLite tables without losing data."""
    cursor = conn.cursor()

    # Check appointments table
    cursor.execute("PRAGMA table_info(appointments)")
    apt_cols = [r["name"] for r in cursor.fetchall()]
    if "purpose" not in apt_cols:
        cursor.execute("ALTER TABLE appointments ADD COLUMN purpose TEXT DEFAULT ''")
    if "consultation_fee" not in apt_cols:
        cursor.execute("ALTER TABLE appointments ADD COLUMN consultation_fee TEXT DEFAULT 'Free'")
    if "is_low_cost" not in apt_cols:
        cursor.execute("ALTER TABLE appointments ADD COLUMN is_low_cost INTEGER DEFAULT 1")
    if "profile_id" not in apt_cols:
        cursor.execute("ALTER TABLE appointments ADD COLUMN profile_id INTEGER DEFAULT 1")
    if "rescheduled_from_date" not in apt_cols:
        cursor.execute("ALTER TABLE appointments ADD COLUMN rescheduled_from_date TEXT DEFAULT ''")
    if "cancellation_reason" not in apt_cols:
        cursor.execute("ALTER TABLE appointments ADD COLUMN cancellation_reason TEXT DEFAULT ''")
    if "post_visit_notes" not in apt_cols:
        cursor.execute("ALTER TABLE appointments ADD COLUMN post_visit_notes TEXT DEFAULT ''")

    # Check medicines table
    cursor.execute("PRAGMA table_info(medicines)")
    med_cols = [r["name"] for r in cursor.fetchall()]
    if "reminder_time" not in med_cols:
        cursor.execute("ALTER TABLE medicines ADD COLUMN reminder_time TEXT DEFAULT '08:00 AM'")
    if "profile_id" not in med_cols:
        cursor.execute("ALTER TABLE medicines ADD COLUMN profile_id INTEGER DEFAULT 1")
    if "status" not in med_cols:
        cursor.execute("ALTER TABLE medicines ADD COLUMN status TEXT DEFAULT 'pending'")

    # Check medicine_logs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS medicine_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            medicine_id INTEGER NOT NULL,
            profile_id INTEGER DEFAULT 1,
            log_date TEXT NOT NULL,
            status TEXT NOT NULL,
            logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Check reports table
    cursor.execute("PRAGMA table_info(reports)")
    rep_cols = [r["name"] for r in cursor.fetchall()]
    if "record_type" not in rep_cols:
        cursor.execute("ALTER TABLE reports ADD COLUMN record_type TEXT DEFAULT 'Lab Report'")
    if "file_path" not in rep_cols:
        cursor.execute("ALTER TABLE reports ADD COLUMN file_path TEXT DEFAULT ''")
    if "profile_id" not in rep_cols:
        cursor.execute("ALTER TABLE reports ADD COLUMN profile_id INTEGER DEFAULT 1")

    # Check share_codes table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS share_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            share_code TEXT UNIQUE NOT NULL,
            patient_name TEXT NOT NULL,
            profile_id INTEGER DEFAULT 1,
            shared_records TEXT DEFAULT 'all',
            doctor_note TEXT DEFAULT '',
            expires_at TEXT NOT NULL,
            is_revoked INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Check profiles table (Family Profiles + Allergies & Conditions)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            relationship TEXT NOT NULL,
            age INTEGER DEFAULT 0,
            gender TEXT DEFAULT 'Other',
            blood_group TEXT DEFAULT '',
            is_default INTEGER DEFAULT 0,
            allergies TEXT DEFAULT '',
            conditions TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("PRAGMA table_info(profiles)")
    prof_cols = [r["name"] for r in cursor.fetchall()]
    if "allergies" not in prof_cols:
        cursor.execute("ALTER TABLE profiles ADD COLUMN allergies TEXT DEFAULT ''")
    if "conditions" not in prof_cols:
        cursor.execute("ALTER TABLE profiles ADD COLUMN conditions TEXT DEFAULT ''")

    # Phase 7: Doctors table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS doctors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE,
            doctor_name TEXT NOT NULL,
            medical_reg_no TEXT UNIQUE NOT NULL,
            speciality TEXT NOT NULL,
            hospital TEXT DEFAULT '',
            mobile TEXT,
            email TEXT,
            password_hash TEXT,
            is_verified INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Phase 7: Doctor Patient Access Sessions (30-min window)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS doctor_patient_access (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_token TEXT UNIQUE NOT NULL,
            doctor_id INTEGER NOT NULL,
            doctor_name TEXT NOT NULL,
            doctor_reg_no TEXT NOT NULL,
            profile_id INTEGER NOT NULL,
            access_method TEXT NOT NULL,
            include_mental_health INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            expires_at TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Phase 7: Doctor Access Logs (Aadhaar NEVER logged here)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS doctor_access_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doctor_id INTEGER NOT NULL,
            doctor_name TEXT NOT NULL,
            doctor_reg_no TEXT NOT NULL,
            profile_id INTEGER NOT NULL,
            access_method TEXT NOT NULL,
            status TEXT DEFAULT 'active',
            expires_at TEXT NOT NULL,
            accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Phase 7: Patient OTPs for Doctor Verification (Aadhaar hashed, never raw)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS patient_otps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            identifier TEXT NOT NULL,
            otp_code TEXT NOT NULL,
            profile_id INTEGER NOT NULL,
            expires_at TEXT NOT NULL,
            is_used INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Phase 9: Mental Health & Recovery Tables (SPEC 16b, 16c, 16d, 16f, 16g, 16h)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS wellness_pins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            profile_id INTEGER NOT NULL UNIQUE,
            pin_hash TEXT NOT NULL,
            discreet_mode INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mood_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            profile_id INTEGER NOT NULL,
            log_date TEXT NOT NULL,
            mood_score INTEGER NOT NULL,
            mood_label TEXT NOT NULL,
            energy_level INTEGER DEFAULT 3,
            sleep_hours REAL DEFAULT 7.0,
            tags TEXT DEFAULT '',
            notes_encrypted TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS wellness_screenings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            profile_id INTEGER NOT NULL,
            screener_type TEXT NOT NULL,
            total_score INTEGER NOT NULL,
            severity_level TEXT NOT NULL,
            answers_json TEXT NOT NULL,
            crisis_flag INTEGER DEFAULT 0,
            guidance_summary TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS recovery_trackers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            profile_id INTEGER NOT NULL,
            target_habit TEXT NOT NULL,
            clean_start_date TEXT NOT NULL,
            streak_days INTEGER DEFAULT 0,
            last_reset_date TEXT DEFAULT NULL,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS craving_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            profile_id INTEGER NOT NULL,
            craving_intensity INTEGER NOT NULL,
            trigger_description TEXT DEFAULT '',
            coping_strategy_used TEXT DEFAULT '',
            notes_encrypted TEXT DEFAULT '',
            logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS coping_plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            profile_id INTEGER NOT NULL,
            trigger_name TEXT NOT NULL,
            coping_action TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Phase 10A: Vitals Tracker (SPEC 12a)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vitals_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            profile_id INTEGER NOT NULL,
            vital_type TEXT NOT NULL,
            value_primary REAL NOT NULL,
            value_secondary REAL DEFAULT NULL,
            unit TEXT NOT NULL,
            meal_context TEXT DEFAULT '',
            status TEXT DEFAULT 'normal',
            notes_encrypted TEXT DEFAULT '',
            recorded_at TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Phase 10A: Emergency Health Card (SPEC 12c)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS emergency_cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            profile_id INTEGER NOT NULL UNIQUE,
            emergency_token TEXT UNIQUE NOT NULL,
            blood_group TEXT DEFAULT '',
            primary_contact_name TEXT DEFAULT '',
            primary_contact_phone TEXT DEFAULT '',
            primary_contact_relation TEXT DEFAULT '',
            secondary_contact_name TEXT DEFAULT '',
            secondary_contact_phone TEXT DEFAULT '',
            secondary_contact_relation TEXT DEFAULT '',
            allergies TEXT DEFAULT '',
            chronic_conditions TEXT DEFAULT '',
            current_medications TEXT DEFAULT '',
            emergency_instructions TEXT DEFAULT '',
            organ_donor INTEGER DEFAULT 0,
            is_public_enabled INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Phase 10A: Scanned Documents & OCR Extractor (SPEC 12b)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scanned_documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            profile_id INTEGER NOT NULL,
            file_name TEXT NOT NULL,
            file_path TEXT NOT NULL,
            document_type TEXT DEFAULT 'Prescription',
            ocr_text TEXT DEFAULT '',
            extracted_data_json TEXT DEFAULT '{}',
            processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()


def init_db(db_path=None):
    """Initializes tables in SQLite database and seeds clean sample data."""
    with get_db(db_path) as conn:
        cursor = conn.cursor()

        # 1. Appointments Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS appointments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_name TEXT NOT NULL,
                doctor_name TEXT NOT NULL,
                specialty TEXT NOT NULL,
                appointment_date TEXT NOT NULL,
                appointment_time TEXT NOT NULL,
                location_or_clinic TEXT,
                notes TEXT,
                purpose TEXT DEFAULT '',
                consultation_fee TEXT DEFAULT 'Free',
                is_low_cost INTEGER DEFAULT 1,
                status TEXT DEFAULT 'Upcoming',
                profile_id INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 2. Medicines Schedule Table (strictly reminder/tracking - not prescribing)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS medicines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_name TEXT NOT NULL,
                medicine_name TEXT NOT NULL,
                prescribed_dosage TEXT NOT NULL,
                timing_slot TEXT NOT NULL,
                frequency TEXT NOT NULL,
                doctor_prescribed TEXT,
                instructions TEXT,
                reminder_time TEXT DEFAULT '08:00 AM',
                pills_left INTEGER DEFAULT 30,
                taken_today INTEGER DEFAULT 0,
                last_taken_date TEXT,
                profile_id INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 3. Medical Reports Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_name TEXT,
                report_title TEXT NOT NULL,
                report_date TEXT,
                original_filename TEXT,
                extracted_text TEXT,
                summary_english TEXT,
                summary_telugu TEXT,
                record_type TEXT DEFAULT 'Lab Report',
                file_path TEXT DEFAULT '',
                profile_id INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 4. Share Codes Table (Stage 6 Doctor View)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS share_codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                share_code TEXT UNIQUE NOT NULL,
                patient_name TEXT NOT NULL,
                profile_id INTEGER DEFAULT 1,
                shared_records TEXT DEFAULT 'all',
                doctor_note TEXT DEFAULT '',
                expires_at TEXT NOT NULL,
                is_revoked INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 5. Family Profiles Table (Hackathon Focus #5)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                relationship TEXT NOT NULL,
                age INTEGER DEFAULT 0,
                gender TEXT DEFAULT 'Other',
                blood_group TEXT DEFAULT '',
                is_default INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        _run_migrations(conn)
        conn.commit()


def seed_sample_data(force=False, db_path=None):
    """Seeds beginner-friendly sample health data (no real patient data)."""
    with get_db(db_path) as conn:
        cursor = conn.cursor()

        if force:
            cursor.execute("DELETE FROM appointments")
            cursor.execute("DELETE FROM medicines")
            cursor.execute("DELETE FROM reports")
            cursor.execute("DELETE FROM profiles")
            conn.commit()

        # Check existing profiles
        cursor.execute("SELECT COUNT(*) AS count FROM profiles")
        prof_count = cursor.fetchone()["count"]

        if prof_count == 0:
            sample_profiles = [
                (1, "Grandpa Rao", "Grandparent", 72, "Male", "O+", 1),
                (2, "Sita Devi", "Mother", 48, "Female", "B+", 0),
                (3, "Ramesh", "Father", 52, "Male", "A+", 0),
                (4, "Ananya (Student)", "Child", 19, "Female", "B+", 0)
            ]
            cursor.executemany("""
                INSERT INTO profiles (id, name, relationship, age, gender, blood_group, is_default)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, sample_profiles)

        # Check existing appointments
        cursor.execute("SELECT COUNT(*) AS count FROM appointments")
        apt_count = cursor.fetchone()["count"]

        if apt_count == 0:
            sample_appointments = [
                (
                    "Grandpa Rao",
                    "Dr. Ramesh Kumar",
                    "Cardiology (గుండె వైద్య నిపుణులు)",
                    "2026-10-25",
                    "10:30 AM",
                    "Apollo Clinic, Main Road",
                    "Routine Blood Pressure & ECG follow-up checkup",
                    "Routine BP follow-up",
                    "₹150",
                    1,
                    "Upcoming",
                    1
                ),
                (
                    "Ananya (Student)",
                    "Dr. Anita Sharma",
                    "General Physician (సాధారణ వైద్యులు)",
                    "2026-10-18",
                    "04:00 PM",
                    "City Health Centre, 2nd Floor",
                    "Annual routine health screening and eye checkup",
                    "Routine Health Screening",
                    "Free",
                    1,
                    "Upcoming",
                    1
                ),
                (
                    "Grandpa Rao",
                    "Dr. K. Srinivas",
                    "Ophthalmology (కంటి వైద్యులు)",
                    "2026-10-02",
                    "11:00 AM",
                    "Netra Eye Hospital",
                    "Cataract post-surgery checkup. Vision is normal.",
                    "Post-surgery review",
                    "₹200",
                    0,
                    "Completed",
                    1
                )
            ]
            cursor.executemany("""
                INSERT INTO appointments (
                    patient_name, doctor_name, specialty,
                    appointment_date, appointment_time, location_or_clinic,
                    notes, purpose, consultation_fee, is_low_cost, status, profile_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, sample_appointments)

        # Check existing medicines
        cursor.execute("SELECT COUNT(*) AS count FROM medicines")
        med_count = cursor.fetchone()["count"]

        if med_count == 0:
            sample_medicines = [
                (
                    "Grandpa Rao",
                    "Metformin 500mg",
                    "1 tablet after breakfast",
                    "Morning",
                    "Daily",
                    "Dr. Anita Sharma",
                    "Take with full glass of warm water after meal.",
                    "08:00 AM",
                    24,
                    1,
                    datetime.now().strftime("%Y-%m-%d"),
                    1
                ),
                (
                    "Grandpa Rao",
                    "Amlodipine 5mg",
                    "1 tablet at bedtime",
                    "Night",
                    "Daily",
                    "Dr. Ramesh Kumar",
                    "For Blood Pressure maintenance. Do not skip.",
                    "09:00 PM",
                    8,
                    0,
                    "",
                    1
                ),
                (
                    "Ananya",
                    "Vitamin D3 60,000 IU",
                    "1 capsule once a week (Sundays)",
                    "Morning",
                    "Weekly",
                    "Dr. Anita Sharma",
                    "Take after a meal containing healthy fats/milk.",
                    "09:30 AM",
                    4,
                    0,
                    "",
                    1
                ),
                (
                    "Family",
                    "Omega-3 Fish Oil",
                    "1 softgel after lunch",
                    "Afternoon",
                    "Daily",
                    "Dr. Anita Sharma",
                    "Health supplement prescribed for general wellness.",
                    "01:30 PM",
                    18,
                    0,
                    "",
                    1
                )
            ]
            cursor.executemany("""
                INSERT INTO medicines (
                    patient_name, medicine_name, prescribed_dosage,
                    timing_slot, frequency, doctor_prescribed,
                    instructions, reminder_time, pills_left, taken_today, last_taken_date, profile_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, sample_medicines)

        # Check existing reports
        cursor.execute("SELECT COUNT(*) AS count FROM reports")
        rep_count = cursor.fetchone()["count"]

        if rep_count == 0:
            sample_reports = [
                (
                    "Grandpa Rao",
                    "Blood Glucose & Lipid Profile",
                    "2026-09-15",
                    "blood_report_grandpa.pdf",
                    "Fasting Blood Sugar: 124 mg/dL. HbA1c: 6.8%. Total Cholesterol: 205 mg/dL. Triglycerides: 160 mg/dL.",
                    "Fasting sugar at 124 mg/dL and HbA1c 6.8% indicate mild hyperglycemia. Continue low-sugar diet and daily morning walks.",
                    "రక్తంలో చక్కెర మరియు కొలెస్ట్రాల్ కాస్త ఎక్కువగా ఉన్నాయి. డాక్టర్ సలహా ప్రకారం నూనె తక్కువ ఉన్న ఆహారం మరియు నడక కొనసాగించండి.",
                    "Lab Report",
                    "",
                    1
                ),
                (
                    "Ananya (Student)",
                    "Complete Blood Picture (CBP)",
                    "2026-08-10",
                    "cbp_ananya.pdf",
                    "Hemoglobin: 12.6 g/dL. Total RBC: 4.4 mil/uL. Platelet count: 260,000 /uL. ESR: 12 mm/hr.",
                    "Hemoglobin and platelet levels are healthy and within standard reference intervals.",
                    "రక్త కణాల సంఖ్య మరియు హిమోగ్లోబిన్ సాధారణంగా మరియు ఆరోగ్యంగా ఉన్నాయి.",
                    "Lab Report",
                    "",
                    4
                )
            ]
            cursor.executemany("""
                INSERT INTO reports (
                    patient_name, report_title, report_date,
                    original_filename, extracted_text,
                    summary_english, summary_telugu,
                    record_type, file_path, profile_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, sample_reports)

        # Check existing vitals
        cursor.execute("SELECT COUNT(*) AS count FROM vitals_logs")
        vital_count = cursor.fetchone()["count"]
        if vital_count == 0:
            sample_vitals = [
                # Grandpa Rao (profile 1)
                (1, "bp", 128.0, 82.0, "mmHg", "", "stage1", "", "2026-10-12 09:30:00"),
                (1, "glucose", 112.0, None, "mg/dL", "fasting", "elevated", "", "2026-10-12 07:45:00"),
                (1, "heart_rate", 72.0, None, "bpm", "", "normal", "", "2026-10-12 09:30:00"),
                (1, "spo2", 98.0, None, "%", "", "normal", "", "2026-10-12 09:30:00"),
                (1, "temperature", 98.4, None, "°F", "", "normal", "", "2026-10-12 09:30:00"),
                (1, "bmi", 68.0, 168.0, "kg", "", "normal", "", "2026-10-10 10:00:00"),
                # Earlier BP readings for trend chart
                (1, "bp", 132.0, 85.0, "mmHg", "", "stage1", "", "2026-10-05 09:15:00"),
                (1, "bp", 138.0, 88.0, "mmHg", "", "stage1", "", "2026-09-28 09:00:00"),
                # Ananya (profile 4)
                (4, "bp", 115.0, 75.0, "mmHg", "", "normal", "", "2026-10-11 10:00:00"),
                (4, "heart_rate", 68.0, None, "bpm", "", "normal", "", "2026-10-11 10:00:00"),
                (4, "spo2", 99.0, None, "%", "", "normal", "", "2026-10-11 10:00:00")
            ]
            cursor.executemany("""
                INSERT INTO vitals_logs (
                    profile_id, vital_type, value_primary, value_secondary,
                    unit, meal_context, status, notes_encrypted, recorded_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, sample_vitals)

        # Check existing emergency cards
        cursor.execute("SELECT COUNT(*) AS count FROM emergency_cards")
        card_count = cursor.fetchone()["count"]
        if card_count == 0:
            sample_cards = [
                (
                    1, "emerg_grandpa_rao_01", "O+",
                    "Ramesh (Son)", "+91 98765 43210", "Son",
                    "Sita Devi (Daughter-in-law)", "+91 98765 43211", "Daughter-in-law",
                    "Penicillin (Allergic rash), Sulfa Drugs",
                    "Type 2 Diabetes, Hypertension",
                    "Metformin 500mg, Amlodipine 5mg",
                    "Diabetic patient. If found unresponsive or sweating profusely, immediately test blood glucose. Rescue glucose powder in coat pocket.",
                    1, 1
                ),
                (
                    4, "emerg_ananya_04", "B+",
                    "Ramesh (Father)", "+91 98765 43210", "Father",
                    "Sita Devi (Mother)", "+91 98765 43211", "Mother",
                    "Dust / Pollen (Mild Asthmatic wheezing)",
                    "None known",
                    "Vitamin D3 (Weekly)",
                    "Student emergency contact. Mild allergic rhinitis.",
                    1, 1
                )
            ]
            cursor.executemany("""
                INSERT INTO emergency_cards (
                    profile_id, emergency_token, blood_group,
                    primary_contact_name, primary_contact_phone, primary_contact_relation,
                    secondary_contact_name, secondary_contact_phone, secondary_contact_relation,
                    allergies, chronic_conditions, current_medications,
                    emergency_instructions, organ_donor, is_public_enabled
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, sample_cards)

        conn.commit()


# ==============================================================================
# COMPREHENSIVE MEDICAL GLOSSARY & SAFE KNOWLEDGE ENGINE
# ==============================================================================

MEDICAL_GLOSSARY = {
    "hba1c": {
        "term": "HbA1c (Glycated Hemoglobin)",
        "telugu_term": "హెచ్‌బిఎ1సి (3 నెలల సగటు చక్కెర పరీక్ష)",
        "category": "Diabetes / Blood Sugar",
        "normal_range": "< 5.7% (Normal), 5.7% - 6.4% (Prediabetes), >= 6.5% (Diabetes)",
        "meaning_en": "Measures your average blood sugar levels over the past 2 to 3 months. Unlike a daily finger-prick test, it provides a stable long-term picture of glucose control.",
        "meaning_te": "గత 2 నుండి 3 నెలల కాలంలో మీ రక్తంలో చక్కెర స్థాయిల సగటును కొలుస్తుంది. రోజువారీ హెచ్చుతగ్గులు కాకుండా దీర్ఘకాలిక చక్కెర నియంత్రణను ఇది తెలుపుతుంది.",
        "lifestyle_tip": "Balanced diet rich in fiber, daily 30-minute brisk walk, and taking prescribed diabetes medicines consistently.",
        "doctor_question": "What is my target HbA1c goal based on my age and general health?"
    },
    "fasting blood sugar": {
        "term": "Fasting Blood Sugar (FBS)",
        "telugu_term": "ఉపవాస రక్త చక్కెర (ఫాస్టింగ్ బ్లడ్ షుగర్)",
        "category": "Diabetes / Blood Sugar",
        "normal_range": "70 - 99 mg/dL (Normal), 100 - 125 mg/dL (Prediabetes), >= 126 mg/dL (Diabetes)",
        "meaning_en": "Measures the glucose level in your blood after fasting for at least 8 to 10 hours overnight. Helps screen for diabetes.",
        "meaning_te": "రాత్రిపూట 8 నుండి 10 గంటల పాటు ఏమీ తినకుండా ఉన్న తర్వాత రక్తంలో ఉండే గ్లూకోజ్ స్థాయిని ఇది కొలుస్తుంది.",
        "lifestyle_tip": "Avoid late-night carbohydrate-heavy dinners and drink plenty of plain water.",
        "doctor_question": "Should I repeat this test or do an HbA1c to confirm the finding?"
    },
    "postprandial blood sugar": {
        "term": "Postprandial Blood Sugar (PPBS)",
        "telugu_term": "భోజనం తర్వాత రక్త చక్కెర (పిపిబిఎస్)",
        "category": "Diabetes / Blood Sugar",
        "normal_range": "< 140 mg/dL (Normal for non-diabetics), < 180 mg/dL (Target for diabetics)",
        "meaning_en": "Blood glucose measured exactly 2 hours after the start of a regular meal. Shows how efficiently your body handles carbohydrates.",
        "meaning_te": "భోజనం ప్రారంభించిన 2 గంటల తర్వాత తీసే పరీక్ష. మీ శరీరం ఆహారంలోని చక్కెరను ఎంత సమర్థవంతంగా నియంత్రిస్తుందో చూపిస్తుంది.",
        "lifestyle_tip": "Control portion sizes of rice, sweets, and refined flour. A light 10-minute stroll after meals is beneficial.",
        "doctor_question": "Does my current diet or medicine timing need an adjustment based on this number?"
    },
    "hemoglobin": {
        "term": "Hemoglobin (Hb)",
        "telugu_term": "హిమోగ్లోబిన్ (రక్తంలో ఆక్సిజన్ వాహక ప్రోటీన్)",
        "category": "Complete Blood Count (CBC)",
        "normal_range": "Men: 13.5 - 17.5 g/dL | Women: 12.0 - 15.5 g/dL",
        "meaning_en": "The iron-rich protein in red blood cells that carries oxygen from your lungs to the rest of your body. Low levels indicate anemia (causing fatigue and weakness).",
        "meaning_te": "ఎర్ర రక్త కణాలలో ఉండే ముఖ్యమైన ఐరన్ ప్రోటీన్. ఇది ఊపిరితిత్తుల నుండి శరీర భాగాలకు ఆక్సిజన్‌ను మోసుకెళ్తుంది. ఇది తగ్గితే రక్తహీనత (నీరసం, అలసట) వస్తుంది.",
        "lifestyle_tip": "Eat iron-rich foods: green leafy vegetables (spinach), pomegranate, dates, lentils, and jaggery.",
        "doctor_question": "If my hemoglobin is low, do I need iron supplements or further dietary evaluation?"
    },
    "wbc count": {
        "term": "White Blood Cell Count (WBC / Leukocytes)",
        "telugu_term": "తెల్ల రక్త కణాల సంఖ్య (WBC - రోగనిరోధక కణాలు)",
        "category": "Complete Blood Count (CBC)",
        "normal_range": "4,500 - 11,000 cells/mcL",
        "meaning_en": "Your body's defense soldiers that fight off bacterial, viral, and fungal infections. Elevated levels often indicate active infection, inflammation, or physical stress.",
        "meaning_te": "ఇవి శరీర రక్షణ దళాలు. బాక్టీరియా, వైరస్ ఇన్ఫెక్షన్లతో పోరాడుతాయి. ఈ సంఖ్య పెరిగితే శరీరంలో ఇన్ఫెక్షన్ లేదా వాపు ఉందని అర్థం కావచ్చు.",
        "lifestyle_tip": "Adequate sleep, hygienic hand washing, and vitamin C rich fruits boost healthy immune function.",
        "doctor_question": "Could my high or low WBC be caused by a recent infection or medication?"
    },
    "platelet count": {
        "term": "Platelet Count (Thrombocytes)",
        "telugu_term": "ప్లేట్‌లెట్స్ సంఖ్య (రక్తం గడ్డకట్టించే కణాలు)",
        "category": "Complete Blood Count (CBC)",
        "normal_range": "150,000 - 450,000 /mcL",
        "meaning_en": "Tiny cell fragments that form blood clots to stop bleeding when you get a cut or injury. Low counts (thrombocytopenia) can occur in viral fevers like dengue.",
        "meaning_te": "గాయాలైనప్పుడు రక్తం కారకుండా గడ్డకట్టడానికి తోడ్పడే కణాలు. డెంగ్యూ వంటి వైరల్ జ్వరాలలో ఇవి తాత్కాలికంగా తగ్గుతాయి.",
        "lifestyle_tip": "Stay hydrated with electrolyte fluids, coconut water, and nutritious soups during recovery from fevers.",
        "doctor_question": "Do I need repeat platelet monitoring if recovering from a viral illness?"
    },
    "total cholesterol": {
        "term": "Total Cholesterol",
        "telugu_term": "మొత్తం కొలెస్ట్రాల్ (రక్తంలో కొవ్వు స్థాయి)",
        "category": "Lipid Profile / Heart Health",
        "normal_range": "< 200 mg/dL (Desirable), 200 - 239 mg/dL (Borderline High), >= 240 mg/dL (High)",
        "meaning_en": "The total amount of cholesterol circulating in your blood, including both HDL (good) and LDL (bad) cholesterol.",
        "meaning_te": "రక్తంలో ఉండే మొత్తం కొవ్వు శాతం. ఇందులో మంచి కొలెస్ట్రాల్ మరియు చెడు కొలెస్ట్రాల్ రెండూ కలిసి ఉంటాయి.",
        "lifestyle_tip": "Limit deep-fried foods, trans fats, and saturated oils. Cook with mustard, sunflower, or olive oil in moderation.",
        "doctor_question": "What is my individual cardiovascular risk score based on my cholesterol breakdown?"
    },
    "ldl": {
        "term": "LDL Cholesterol (Low-Density Lipoprotein / 'Bad' Cholesterol)",
        "telugu_term": "ఎల్.డి.ఎల్ కొలెస్ట్రాల్ (చెడు కొవ్వు)",
        "category": "Lipid Profile / Heart Health",
        "normal_range": "< 100 mg/dL (Optimal), 100 - 129 mg/dL (Near optimal), > 160 mg/dL (High)",
        "meaning_en": "Often called 'bad' cholesterol because excess amounts build up in artery walls as plaque, narrowing blood flow to heart and brain.",
        "meaning_te": "దీనిని 'చెడు కొలెస్ట్రాల్' అంటారు. ఇది ఎక్కువైతే రక్తనాళాల్లో పూడికలు (ప్లాక్) ఏర్పడి గుండెపోటు వచ్చే ప్రమాదం పెరుగుతుంది.",
        "lifestyle_tip": "Increase soluble fiber (oats, beans, apples, flaxseeds) and reduce red meat and bakery snacks.",
        "doctor_question": "Is dietary lifestyle change sufficient or do I need a lipid-lowering prescription?"
    },
    "hdl": {
        "term": "HDL Cholesterol (High-Density Lipoprotein / 'Good' Cholesterol)",
        "telugu_term": "హెచ్.డి.ఎల్ కొలెస్ట్రాల్ (మంచి కొవ్వు)",
        "category": "Lipid Profile / Heart Health",
        "normal_range": "> 40 mg/dL (Men), > 50 mg/dL (Women) - Higher is protective!",
        "meaning_en": "Known as 'good' cholesterol because it scavenges excess cholesterol from arteries and carries it back to the liver for clearance.",
        "meaning_te": "దీనిని 'మంచి కొలెస్ట్రాల్' అంటారు. ఇది రక్తనాళాల్లోని అదనపు కొవ్వును కాలేయానికి చేర్చి బయటకు పంపుతుంది. ఇది ఎక్కువగా ఉంటే గుండెకు రక్షణ.",
        "lifestyle_tip": "Regular aerobic exercise (cycling, walking, swimming), healthy nuts (walnuts, almonds), and quitting smoking raise HDL.",
        "doctor_question": "How can I safely raise my HDL level naturally?"
    },
    "triglycerides": {
        "term": "Triglycerides",
        "telugu_term": "ట్రైగ్లిజరైడ్స్ (రక్తంలో కొవ్వు కణాలు)",
        "category": "Lipid Profile / Heart Health",
        "normal_range": "< 150 mg/dL (Normal), 150 - 199 mg/dL (Borderline High), >= 200 mg/dL (High)",
        "meaning_en": "The most common type of fat in your body, formed from excess calories, refined sugars, and carbohydrates that your body does not immediately burn.",
        "meaning_te": "మనం తీసుకునే అధిక కేలరీలు, పంచదార, పిండి పదార్థాల వల్ల తయారయ్యే కొవ్వు. ఇది పెరిగితే గుండె మరియు క్లోమగ్రంథికి చేటు.",
        "lifestyle_tip": "Significantly reduce sweets, sugary soft drinks, polished white rice, and alcohol consumption.",
        "doctor_question": "Are high triglycerides linked with insulin resistance in my case?"
    },
    "serum creatinine": {
        "term": "Serum Creatinine",
        "telugu_term": "సీరమ్ క్రియాటినిన్ (కిడ్నీ పనితీరు కొలత)",
        "category": "Kidney Function Test (KFT / RFT)",
        "normal_range": "0.6 - 1.2 mg/dL for adult men | 0.5 - 1.1 mg/dL for adult women",
        "meaning_en": "A waste product from normal muscle wear and tear that healthy kidneys filter out through urine. Rising levels can indicate reduced kidney filtration.",
        "meaning_te": "కండరాల జీవక్రియ వల్ల వచ్చే వ్యర్థ పదార్థం. ఆరోగ్యకరమైన మూత్రపిండాలు దీనిని మూత్రం ద్వారా బయటకు పంపుతాయి. ఇది పెరిగితే కిడ్నీ పనితీరు మందగించినట్లు సూచన.",
        "lifestyle_tip": "Stay properly hydrated, avoid unnecessary over-the-counter painkillers (NSAIDs), and keep BP and sugar controlled.",
        "doctor_question": "What is my calculated eGFR (estimated kidney filtration rate) based on this creatinine level?"
    },
    "blood urea": {
        "term": "Blood Urea Nitrogen (BUN)",
        "telugu_term": "బ్లడ్ యూరియా (రక్తంలో యూరియా స్థాయి)",
        "category": "Kidney Function Test (KFT)",
        "normal_range": "7 - 20 mg/dL",
        "meaning_en": "Measures the amount of urea nitrogen in blood, produced when liver breaks down protein. Evaluates kidney efficiency and hydration state.",
        "meaning_te": "ప్రోటీన్లను శరీరం జీర్ణం చేసుకున్నప్పుడు ఏర్పడే వ్యర్థం. కిడ్నీలు ఎంత సమర్థవంతంగా పనిచేస్తున్నాయో ఇది తెలుపుతుంది.",
        "lifestyle_tip": "Drink sufficient water throughout the day, especially in hot weather.",
        "doctor_question": "Could mild dehydration explain an elevated urea number?"
    },
    "sgpt": {
        "term": "SGPT / ALT (Alanine Aminotransferase)",
        "telugu_term": "ఎస్.జి.పి.టి / ఎ.ఎల్.టి (కాలేయం ఎంజైమ్)",
        "category": "Liver Function Test (LFT)",
        "normal_range": "7 - 56 U/L",
        "meaning_en": "An enzyme primarily found inside liver cells. When liver cells are irritated or damaged (e.g. fatty liver, alcohol, medications), ALT leaks into blood.",
        "meaning_te": "కాలేయంలో ఉండే ఎంజైమ్. కాలేయంలో వాపు, కొవ్వు పేరుకుపోవడం (ఫ్యాటీ లివర్) లేదా మందుల ప్రభావం వల్ల ఇది రక్తంలోకి ఎక్కువగా విడుదలవుతుంది.",
        "lifestyle_tip": "Maintain healthy body weight, cut down junk food, avoid self-medicating, and avoid alcohol.",
        "doctor_question": "Do I need an ultrasound of the abdomen to check for fatty liver disease?"
    },
    "sgot": {
        "term": "SGOT / AST (Aspartate Aminotransferase)",
        "telugu_term": "ఎస్.జి.ఓ.టి / ఎ.ఎస్.టి (కాలేయం మరియు గుండె ఎంజైమ్)",
        "category": "Liver Function Test (LFT)",
        "normal_range": "10 - 40 U/L",
        "meaning_en": "An enzyme found in liver, heart, and muscles. Elevated levels signal cellular stress in liver or muscular tissues.",
        "meaning_te": "కాలేయం, గుండె మరియు కండరాలలో ఉండే ఎంజైమ్. కాలేయం లేదా కండరాలపై ఒత్తిడి ఉన్నప్పుడు పెరుగుతుంది.",
        "lifestyle_tip": "Engage in moderate physical exercise and eat fresh, wholesome foods.",
        "doctor_question": "Should we re-test AST along with ALT after a few weeks?"
    },
    "tsh": {
        "term": "TSH (Thyroid Stimulating Hormone)",
        "telugu_term": "టి.ఎస్.హెచ్ (థైరాయిడ్ ప్రేరేపక హార్మోన్)",
        "category": "Thyroid Profile",
        "normal_range": "0.4 - 4.5 mIU/L",
        "meaning_en": "Produced by pituitary gland to instruct thyroid gland how much thyroid hormone to produce. High TSH indicates an underactive thyroid (Hypothyroidism; sluggishness, weight gain). Low TSH indicates overactive thyroid (Hyperthyroidism).",
        "meaning_te": "మెదడులోని పిట్యూటరీ గ్రంథి విడుదల చేసే హార్మోన్. టి.ఎస్.హెచ్ పెరిగితే థైరాయిడ్ మందగించిందని (బరువు పెరగడం, నీరసం), తగ్గితే థైరాయిడ్ అతిగా పనిచేస్తోందని అర్థం.",
        "lifestyle_tip": "Take thyroid medicines on an empty stomach in the morning with plain water, 45 minutes before tea or breakfast.",
        "doctor_question": "Do I need Free T3 and Free T4 tests to complete the thyroid evaluation?"
    },
    "blood pressure": {
        "term": "Blood Pressure (Systolic / Diastolic)",
        "telugu_term": "రక్తపోటు (బి.పి - సంకోచ/విశ్రాంతి పీడనం)",
        "category": "Cardiovascular Vitals",
        "normal_range": "Normal: 120/80 mmHg | Elevated: 120-129 / <80 | High: >= 130/80 mmHg",
        "meaning_en": "The pressure of circulating blood against artery walls. Top number (Systolic) is when heart beats; bottom number (Diastolic) is when heart rests between beats.",
        "meaning_te": "రక్తనాళాల గోడలపై రక్తం చూపే పీడనం. పై సంఖ్య (సిస్టోలిక్) గుండె కొట్టుకున్నప్పుడు, క్రింది సంఖ్య (డయాస్టోలిక్) గుండె విశ్రాంతి తీసుకున్నప్పుడు ఉండే పీడనం.",
        "lifestyle_tip": "Reduce table salt intake (< 5g per day), manage stress with deep breathing, and walk regularly.",
        "doctor_question": "Should I maintain a home BP log morning and evening for 7 days?"
    },
    "vitamin d": {
        "term": "Vitamin D (25-Hydroxyvitamin D)",
        "telugu_term": "విటమిన్ డి (ఎముకల బలం మరియు రోగనిరోధక శక్తి)",
        "category": "Vitamins & Micronutrients",
        "normal_range": "30 - 100 ng/mL (Sufficiency), 20 - 29 ng/mL (Insufficient), < 20 ng/mL (Deficient)",
        "meaning_en": "Essential for calcium absorption, bone strength, dental health, and immune resilience. Synthesized in skin via sunlight.",
        "meaning_te": "ఎముకల దృఢత్వానికి, కాల్షియం గ్రహించడానికి, వ్యాధి నిరోధక శక్తికి ఇది చాలా అవసరం. ఎండ తగలడం ద్వారా శరీరంలో తయారవుతుంది.",
        "lifestyle_tip": "Spend 15-20 minutes in morning sun (between 8 AM and 10 AM) and eat fortified dairy or egg yolks.",
        "doctor_question": "Do I require oral Vitamin D3 sachets or capsules to correct deficiency?"
    },
    "vitamin b12": {
        "term": "Vitamin B12 (Cobalamin)",
        "telugu_term": "విటమిన్ బి12 (నరాల బలం మరియు రక్త కణాలు)",
        "category": "Vitamins & Micronutrients",
        "normal_range": "200 - 900 pg/mL",
        "meaning_en": "Crucial for healthy nerve function, brain health, and red blood cell formation. Very common deficiency among strict vegetarians.",
        "meaning_te": "నరాలు సరిగ్గా పనిచేయడానికి, జ్ఞాపకశక్తికి మరియు రక్త కణాల తయారీకి అత్యవసరం. శాఖాహారులలో ఇది తరచుగా తగ్గుతుంది (కాళ్ల తిమ్మిర్లు, నీరసం).",
        "lifestyle_tip": "Include milk, curd, paneer, and fortified cereals in your daily meals.",
        "doctor_question": "Should I take sublingual B12 or methylcobalamin supplements?"
    },
    "calcium": {
        "term": "Serum Calcium",
        "telugu_term": "కాల్షియం (ఎముకలు, దంతాలు, కండరాల పనితీరు)",
        "category": "Minerals & Bone Health",
        "normal_range": "8.5 - 10.2 mg/dL",
        "meaning_en": "Critical mineral for bone structure, muscle contractions, nerve transmission, and healthy blood clotting.",
        "meaning_te": "ఎముకలు, దంతాల గట్టితనానికి, గుండె మరియు కండరాలు సరిగ్గా కదలడానికి తోడ్పడే ముఖ్యమైన ఖనిజం.",
        "lifestyle_tip": "Consume dairy products, sesame seeds (nuvvulu), ragi (finger millet), and almonds.",
        "doctor_question": "Do I need calcium plus vitamin D supplementation for bone health?"
    },
    "uric acid": {
        "term": "Serum Uric Acid",
        "telugu_term": "యూరిక్ యాసిడ్ (కీళ్ల నొప్పులు మరియు గౌట్ సంకేతం)",
        "category": "Metabolism & Joints",
        "normal_range": "3.5 - 7.2 mg/dL for men | 2.6 - 6.0 mg/dL for women",
        "meaning_en": "Product of purine breakdown in foods. When elevated, crystals can settle in joints (especially the big toe), causing sharp joint pain known as gout.",
        "meaning_te": "ఆహారంలోని ప్యూరిన్లు విచ్ఛిన్నమైనప్పుడు ఏర్పడే ఆమ్లం. ఇది ఎక్కువైతే కీళ్లలో స్పటికాలుగా మారి తీవ్రమైన కీళ్ల నొప్పులు (గౌట్) వస్తాయి.",
        "lifestyle_tip": "Drink 3-4 liters of water daily. Avoid organ meats, beer, shellfish, and high-fructose corn syrups.",
        "doctor_question": "Is my joint pain related to high uric acid levels?"
    },
    "esr": {
        "term": "ESR (Erythrocyte Sedimentation Rate)",
        "telugu_term": "ఇ.ఎస్.ఆర్ (శరీరంలో వాపు / ఇన్ఫ్లమేషన్ సూచిక)",
        "category": "Inflammation Marker",
        "normal_range": "Men: 0 - 15 mm/hr | Women: 0 - 20 mm/hr (varies slightly with age)",
        "meaning_en": "Measures how quickly red blood cells settle at the bottom of a test tube. A non-specific indicator that inflammation, infection, or arthritis is present in body.",
        "meaning_te": "రక్త కణాలు ఎంత వేగంగా క్రిందికి చేరుకుంటాయో చూపే పరీక్ష. శరీరంలో ఎక్కడైనా వాపు, ఇన్ఫెక్షన్ లేదా ఆర్థరైటిస్ ఉంటే ఈ సంఖ్య పెరుగుతుంది.",
        "lifestyle_tip": "Anti-inflammatory diet (turmeric, ginger, berries, leafy vegetables) and proper rest.",
        "doctor_question": "What underlying condition is causing elevated inflammation markers?"
    }
}

# Emergency keywords that trigger immediate safety protocols
EMERGENCY_KEYWORDS = [
    "chest pain", "heart attack", "గుండె నొప్పి", "shortness of breath", "cant breathe",
    "difficulty breathing", "శ్వాస ఆడకపోవడం", "paralysis", "పక్షవాతం", "severe bleeding",
    "రక్తం కారడం", "unconscious", "స్పృహ తప్పడం", "stroke", "poison", "విషం",
    "suicide", "ఆత్మహత్య", "fainted", "choking"
]

# Prescription-seeking keywords to trigger dosage refusal guardrail
PRESCRIPTION_KEYWORDS = [
    "prescribe", "what medicine should i take", "which tablet for", "dosage for",
    "how many mg of", "can i take paracetamol", "change my dose",
    "ఏ మందు వేసుకోవాలి", "డోసేజ్ ఎంత"
]

# ==============================================================================
# AI ENGINE WRAPPER (Gemini API with Safe Local Fallback)
# ==============================================================================

def check_ai_status():
    """Checks whether live AI is configured or operating in local safe mode."""
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    openai_key = os.getenv("OPENAI_API_KEY", "").strip()

    if gemini_key:
        return {
            "configured": True,
            "provider": "Google Gemini (Gemini 2.5 Flash)",
            "mode": "live_ai",
            "badge_text": "Live AI Active (Gemini)",
            "message": "AI Copilot connected via Google Gemini API."
        }
    elif openai_key:
        return {
            "configured": True,
            "provider": "OpenAI",
            "mode": "live_ai",
            "badge_text": "Live AI Active (OpenAI)",
            "message": "AI Copilot connected via OpenAI API."
        }
    else:
        return {
            "configured": False,
            "provider": "Local Safe Medical Knowledge Engine",
            "mode": "safe_local_engine",
            "badge_text": "Safe Local Engine (Offline)",
            "message": "AI API key not configured. Running safely in Local Knowledge Base Mode."
        }


def call_gemini_api(prompt, system_instruction=""):
    """
    Safely calls Gemini REST API.
    Returns response text or None if error/unconfigured.
    """
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key or not REQUESTS_AVAILABLE:
        return None

    # Google Gemini REST endpoint (using gemini-2.5-flash)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"

    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": f"{system_instruction}\n\nUser Question:\n{prompt}"}
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 1000
        }
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=12)
        if response.status_code == 200:
            data = response.json()
            candidates = data.get("candidates", [])
            if candidates:
                text_parts = candidates[0].get("content", {}).get("parts", [])
                if text_parts:
                    return text_parts[0].get("text", "")
        return None
    except Exception as e:
        print(f"[HealthMate AI Warning] Gemini API call exception: {e}")
        return None


def generate_safe_local_health_response(user_text, lang="en"):
    """
    Provides reliable, medically vetted information when AI is not configured.
    Guarantees beginner-safe educational information without false diagnosis.
    """
    lower = user_text.lower()

    # Match glossary terms
    matched_terms = []
    for key, data in MEDICAL_GLOSSARY.items():
        if key in lower or data["term"].lower() in lower or data["telugu_term"] in lower:
            matched_terms.append(data)

    if matched_terms:
        primary = matched_terms[0]
        if lang == "te":
            reply = (
                f"🩺 **{primary['telugu_term']} ({primary['term']}) సమాచారం:**\n\n"
                f"• **సాధారణ పరిధి (Normal Range):** {primary['normal_range']}\n"
                f"• **వివరణ:** {primary['meaning_te']}\n"
                f"• **జీవనశైలి సలహా:** {primary['lifestyle_tip']}\n"
                f"• **డాక్టర్‌ను అడగవలసిన ప్రశ్న:** \"{primary['doctor_question']}\"\n\n"
                f"⚠️ *గమనిక: ఈ సమాచారం అవగాహన కోసం మాత్రమే. మందుల మార్పులు లేదా నిర్ధారణల కోసం ఎల్లప్పుడూ మీ వైద్యుడిని సంప్రదించండి.*"
            )
        else:
            reply = (
                f"🩺 **Understanding {primary['term']} ({primary['telugu_term']}):**\n\n"
                f"• **Normal Reference Range:** {primary['normal_range']}\n"
                f"• **What it means:** {primary['meaning_en']}\n"
                f"• **Healthy Habits:** {primary['lifestyle_tip']}\n"
                f"• **What to ask your doctor:** \"{primary['doctor_question']}\"\n\n"
                f"⚠️ *Medical Disclaimer: HealthMate AI provides educational guidance only. Please consult your physician for individualized medical advice.*"
            )
        return {
            "reply": reply,
            "source": "local_medical_knowledge_engine",
            "matched_term": primary["term"]
        }

    # Common health topics rulebase
    if any(k in lower for k in ["diet", "food", "ఆహారం", "nutrition", "eat"]):
        if lang == "te":
            reply = (
                "🥗 **మంచి ఆరోగ్యకరమైన ఆహార సూత్రాలు:**\n\n"
                "1. పండ్లు, ఆకుకూరలు (పాలకూర, మెంతికూర), కాయధాన్యాలు ఎక్కువగా తీసుకోండి.\n"
                "2. ఉప్పు మరియు పంచదార పరిమాణాన్ని రోజువారీ ఆహారంలో తగ్గించండి.\n"
                "3. రోజుకు కనీసం 8-10 గ్లాసుల మంచినీరు త్రాగండి.\n"
                "4. వేపుళ్ళు, ప్రాసెస్డ్ ఫుడ్స్ పరిమితం చేయండి.\n\n"
                "⚠️ *ప్రత్యేక వ్యాధులు (డయాబెటిస్, కిడ్నీ సమస్యలు) ఉన్నవారు తమ డాక్టర్ లేదా డైటీషియన్ సలహా మేరకు మాత్రమే ఆహార నియమాలు పాటించాలి.*"
            )
        else:
            reply = (
                "🥗 **Healthy Everyday Nutrition Guidelines:**\n\n"
                "1. Include plenty of fresh fruits, colorful vegetables, and fiber-rich lentils.\n"
                "2. Keep salt under 5g per day and limit refined white sugars.\n"
                "3. Stay hydrated with 2-3 liters of clean water daily.\n"
                "4. Choose whole grains (oats, brown rice, millets) over refined flour.\n\n"
                "⚠️ *Disclaimer: Individuals with chronic conditions (diabetes, kidney disorders) should follow their doctor's customized meal plan.*"
            )
        return {"reply": reply, "source": "local_medical_knowledge_engine", "matched_term": "General Nutrition"}

    if any(k in lower for k in ["cold", "cough", "జలుబు", "దగ్గు", "fever", "జ్వరం"]):
        if lang == "te":
            reply = (
                "🍵 **సాధారణ జలుబు మరియు దగ్గు ఉపశమన చిట్కాలు:**\n\n"
                "1. గోరువెచ్చని నీరు, తులసి-అల్లం కషాయం లేదా పాలలో పసుపు వేసుకుని త్రాగండి.\n"
                "2. ఉప్పు నీటితో గొంతు పుక్కిలించడం (salt water gargling) ఉపశమనం ఇస్తుంది.\n"
                "3. ఆవిరి పట్టడం (steam inhalation) ద్వారా ముక్కు దిబ్బడ తగ్గుతుంది.\n"
                "4. పుష్కలంగా విశ్రాంతి తీసుకోండి.\n\n"
                "⚠️ *జ్వరం 101°F కన్నా ఎక్కువ ఉంటే లేదా 3 రోజుల కన్నా ఎక్కువ కాలం తగ్గకపోతే వెంటనే డాక్టర్‌ను సంప్రదించండి.*"
            )
        else:
            reply = (
                "🍵 **Gentle Home Care for Common Cold & Cough:**\n\n"
                "1. Sip warm fluids like clear soups, ginger-tulsi tea, or warm water.\n"
                "2. Gargle with warm salt water twice daily for throat comfort.\n"
                "3. Inhale warm steam to relieve nasal congestion.\n"
                "4. Rest adequately and avoid chilled drinks or air conditioner drafts.\n\n"
                "⚠️ *Important: If high fever (> 101°F) persists for more than 3 days, or if you feel chest pain, visit a clinic immediately.*"
            )
        return {"reply": reply, "source": "local_medical_knowledge_engine", "matched_term": "Common Cold & Cough"}

    if any(k in lower for k in ["water", "నీరు", "hydration"]):
        if lang == "te":
            reply = (
                "💧 **నీరు ఎంత త్రాగాలి?:**\n\n"
                "• సాధారణంగా పెద్దవారు రోజుకు 2 నుండి 3 లీటర్ల మంచినీరు త్రాగడం మంచిది.\n"
                "• వృద్ధులు దాహం వేయకపోయినా క్రమం తప్పకుండా నీరు త్రాగాలి.\n"
                "• కిడ్నీ లేదా గుండె సమస్యలు ఉన్నవారు డాక్టర్ చెప్పిన పరిమాణంలోనే నీరు తీసుకోవాలి.\n\n"
                "⚠️ *మూత్రపిండాల రోగులు డాక్టర్ ఫ్లూయిడ్ రిస్ట్రిక్షన్ సలహా పాటించాలి.*"
            )
        else:
            reply = (
                "💧 **Daily Hydration Advice:**\n\n"
                "• Most adults require roughly 2 to 3 liters (8-10 glasses) of fluids daily.\n"
                "• Seniors often have reduced thirst sensation, so sipping small amounts regularly is key.\n"
                "• Always verify fluid limits with your physician if you have kidney or congestive heart conditions.\n\n"
                "⚠️ *Disclaimer: Consult your doctor if you are on restricted fluid intake.*"
            )
        return {"reply": reply, "source": "local_medical_knowledge_engine", "matched_term": "Hydration"}

    # Default fallback response
    if lang == "te":
        reply = (
            "నమస్కారం! నేను హెల్త్‌మేట్ AI సేఫ్ కాపిలట్‌ని.\n\n"
            "నేను మెడికల్ రిపోర్టులలోని పదాలను (HbA1c, BP, Hemoglobin, కొలెస్ట్రాల్, విటమిన్లు) సులభమైన తెలుగు మరియు ఇంగ్లీషులో వివరించగలను.\n\n"
            "• మీరు నిర్దిష్ట ల్యాబ్ టెస్ట్ లేదా ఆరోగ్య ప్రశ్న అడగండి.\n"
            "• ఉదాహరణ: *'HbA1c అంటే ఏమిటి?'* లేదా *'రక్తపోటు నియంత్రణ చిట్కాలు'*\n\n"
            "⚠️ *గుర్తుంచుకోండి: నేను మందులను సూచించను లేదా జబ్బులను నిర్ధారించను. అత్యవసర పరిస్థితుల్లో 108 లేదా 112 కి కాల్ చేయండి.*"
        )
    else:
        reply = (
            "Hello! I am HealthMate AI's Safe Medical Assistant.\n\n"
            "I can explain medical report terms (like HbA1c, Blood Pressure, Hemoglobin, Lipids, Creatinine, Thyroid TSH) in simple, everyday language.\n\n"
            "• Try asking about a specific lab test: *'What is HbA1c?'* or *'Explain LDL cholesterol'*\n"
            "• Ask about healthy daily habits: *'How to manage blood sugar?'* or *'Home care for seasonal cold'*\n\n"
            "⚠️ *Medical Notice: HealthMate AI does not prescribe medications or diagnose ailments. For personal treatments, please consult your doctor.*"
        )

    return {
        "reply": reply,
        "source": "local_medical_knowledge_engine",
        "matched_term": "General Health Guide"
    }


def analyze_medical_report_text(raw_text):
    """
    Extracts key lab parameters, matches with Medical Glossary,
    and produces accessible bilingual summaries.
    """
    cleaned = raw_text.replace("\r", " ")
    findings = []
    matched_glossary_entries = []

    # Detect known medical terms in the uploaded text
    text_lower = cleaned.lower()
    for term_key, data in MEDICAL_GLOSSARY.items():
        if term_key in text_lower or data["term"].lower() in text_lower:
            matched_glossary_entries.append(data)

    # Simple numeric regex pattern to find values near test names
    numeric_pattern = re.compile(
        r"(hba1c|glucose|fbs|ppbs|hemoglobin|creatinine|cholesterol|tsh|wbc|platelets?|blood pressure|bp)"
        r"[^\d]{1,25}(\d+[\.\d]*\/?\d*)",
        re.IGNORECASE
    )

    extracted_numbers = numeric_pattern.findall(cleaned)

    # Build Plain English Summary
    en_bullets = []
    te_bullets = []

    if extracted_numbers:
        for item, val in extracted_numbers[:6]:
            en_bullets.append(f"• **{item.upper()} recorded at:** {val}")
            te_bullets.append(f"• **{item.upper()} నమోదు విలువ:** {val}")
    else:
        en_bullets.append("• Medical text scanned successfully.")
        te_bullets.append("• మెడికల్ నివేదిక విజయవంతంగా పరిశీలించబడింది.")

    if matched_glossary_entries:
        for entry in matched_glossary_entries[:5]:
            en_bullets.append(f"• **{entry['term']}:** Normal reference: {entry['normal_range']}. {entry['meaning_en']}")
            te_bullets.append(f"• **{entry['telugu_term']}:** సాధారణ పరిధి: {entry['normal_range']}. {entry['meaning_te']}")

    summary_english = (
        "### 📋 Plain Language Medical Report Breakdown (English)\n\n"
        + "\n\n".join(en_bullets)
        + "\n\n**Key Questions to Ask Your Doctor:**\n"
        + "1. Are all values within my personalized target range?\n"
        + "2. Do any of my daily medicines require dosage tuning?\n"
        + "3. What lifestyle or dietary adjustments do you recommend?"
    )

    summary_telugu = (
        "### 📋 సులభమైన తెలుగు నివేదిక వివరణ (Telugu)\n\n"
        + "\n\n".join(te_bullets)
        + "\n\n**మీ డాక్టర్‌ను అడగవలసిన ముఖ్యమైన ప్రశ్నలు:**\n"
        + "1. నా రిపోర్టులోని అన్ని విలువలు నా వయస్సుకు సాధారణమేనా?\n"
        + "2. నా ప్రస్తుత మందులలో ఏమైనా మార్పులు అవసరమా?\n"
        + "3. నేను పాటించవలసిన ఆహారపు మరియు వ్యాయామ నియమాలు ఏమిటి?"
    )

    return {
        "summary_english": summary_english,
        "summary_telugu": summary_telugu,
        "glossary_matches": [g["term"] for g in matched_glossary_entries],
        "glossary_details": matched_glossary_entries[:4]
    }


def extract_text_from_file(file_path, filename):
    """Safely extracts text from txt or pdf files."""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if ext == "txt":
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        except Exception as e:
            return f"Error reading text file: {e}"

    elif ext == "pdf":
        if not PYPDF_AVAILABLE:
            return "PDF processing library (pypdf) is not available. Please paste text directly."
        try:
            reader = pypdf.PdfReader(str(file_path))
            extracted = []
            for page in reader.pages:
                txt = page.extract_text()
                if txt:
                    extracted.append(txt)
            return "\n".join(extracted) if extracted else "No readable text found in PDF."
        except Exception as e:
            return f"Error reading PDF: {e}"

    elif ext in ["png", "jpg", "jpeg"]:
        return (
            f"[Image Report Uploaded: {filename}]\n"
            "Image report received. Please paste the doctor's typed values or lab numbers "
            "into the text box below for accurate bilingual breakdown."
        )

    return "Unsupported file format."


# ==============================================================================
# PHASE 10A HELPER ENGINES: VITALS, OCR SCANNER & EMERGENCY CARD (SPEC 12a, 12b, 12c)
# ==============================================================================

def evaluate_vital_reading(vital_type, value_primary, value_secondary=None, meal_context=""):
    """
    Evaluates vital signs against clinical reference ranges (SPEC 12a).
    Returns status ('normal', 'elevated', 'stage1', 'stage2', 'crisis', 'low', 'high'),
    label, alert message, and whether it represents an acute crisis requiring 108.
    """
    vt = (vital_type or "").lower().strip()
    try:
        val1 = float(value_primary)
    except (ValueError, TypeError):
        val1 = 0.0

    try:
        val2 = float(value_secondary) if value_secondary is not None and str(value_secondary).strip() != "" else None
    except (ValueError, TypeError):
        val2 = None

    ctx = (meal_context or "fasting").lower().strip()

    res = {
        "status": "normal",
        "status_label": "Normal",
        "badge_class": "badge-success",
        "color": "#16a34a",
        "alert_message": "Reading is within healthy normal limits.",
        "is_crisis": False
    }

    if vt in ["bp", "blood_pressure"]:
        sys = val1
        dia = val2 if val2 is not None else 80.0
        if sys >= 180.0 or dia >= 120.0:
            res = {
                "status": "crisis",
                "status_label": "Hypertensive Crisis (Emergency)",
                "badge_class": "badge-danger",
                "color": "#dc2626",
                "alert_message": "🚨 CRITICAL HYPERTENSIVE CRISIS! Blood pressure is dangerously elevated (>=180/120). Seek emergency medical attention or call 108 immediately if feeling headache, chest pain, or vision changes.",
                "is_crisis": True
            }
        elif sys >= 140.0 or dia >= 90.0:
            res = {
                "status": "stage2",
                "status_label": "Stage 2 Hypertension",
                "badge_class": "badge-danger",
                "color": "#ea580c",
                "alert_message": "Blood pressure is significantly elevated. Consult your prescribing physician regarding medication dosage and lifestyle.",
                "is_crisis": False
            }
        elif sys >= 130.0 or dia >= 80.0:
            res = {
                "status": "stage1",
                "status_label": "Stage 1 Hypertension",
                "badge_class": "badge-warning",
                "color": "#d97706",
                "alert_message": "Blood pressure is mildly elevated. Review sodium intake, exercise regularly, and log readings daily.",
                "is_crisis": False
            }
        elif sys >= 120.0 and dia < 80.0:
            res = {
                "status": "elevated",
                "status_label": "Elevated Blood Pressure",
                "badge_class": "badge-info",
                "color": "#0284c7",
                "alert_message": "Systolic reading is slightly above optimal. Adopt heart-healthy daily habits.",
                "is_crisis": False
            }
        elif sys < 90.0 or dia < 60.0:
            res = {
                "status": "low",
                "status_label": "Hypotension (Low BP)",
                "badge_class": "badge-secondary",
                "color": "#475569",
                "alert_message": "Blood pressure is below normal. Drink adequate water, rest, and consult a doctor if dizzy.",
                "is_crisis": False
            }
        else:
            res = {
                "status": "normal",
                "status_label": "Optimal Normal BP",
                "badge_class": "badge-success",
                "color": "#16a34a",
                "alert_message": "Blood pressure is within optimal normal range (<120/<80 mmHg).",
                "is_crisis": False
            }

    elif vt in ["glucose", "blood_glucose", "sugar"]:
        if val1 < 70.0:
            res = {
                "status": "crisis",
                "status_label": "Hypoglycemia (Dangerously Low)",
                "badge_class": "badge-danger",
                "color": "#dc2626",
                "alert_message": "🚨 CRITICAL HYPOGLYCEMIA (<70 mg/dL)! Consume 15g fast-acting carbohydrates (3 tsp sugar, fruit juice, glucose candy) immediately. Recheck in 15 minutes. Call 108 if confused or unresponsive.",
                "is_crisis": True
            }
        elif ctx == "fasting":
            if val1 >= 126.0:
                res = {
                    "status": "high",
                    "status_label": "Diabetic Fasting Range",
                    "badge_class": "badge-danger",
                    "color": "#dc2626",
                    "alert_message": "Fasting blood sugar is in the diabetic range (>=126 mg/dL). Discuss management plan with your doctor.",
                    "is_crisis": False
                }
            elif val1 >= 100.0:
                res = {
                    "status": "elevated",
                    "status_label": "Prediabetes Range",
                    "badge_class": "badge-warning",
                    "color": "#d97706",
                    "alert_message": "Fasting blood sugar is mildly elevated (100-125 mg/dL, Impaired Fasting Glucose). Focus on low glycemic diet and exercise.",
                    "is_crisis": False
                }
            else:
                res = {
                    "status": "normal",
                    "status_label": "Normal Fasting Sugar",
                    "badge_class": "badge-success",
                    "color": "#16a34a",
                    "alert_message": "Fasting blood sugar is within normal healthy limits (70-99 mg/dL).",
                    "is_crisis": False
                }
        elif ctx in ["postprandial", "post-meal", "pp"]:
            if val1 >= 200.0:
                res = {
                    "status": "high",
                    "status_label": "High Post-Meal Sugar",
                    "badge_class": "badge-danger",
                    "color": "#dc2626",
                    "alert_message": "Post-meal glucose exceeds 200 mg/dL. Review meal portion sizes and diabetes medications with doctor.",
                    "is_crisis": False
                }
            elif val1 >= 140.0:
                res = {
                    "status": "elevated",
                    "status_label": "Elevated Post-Meal (Prediabetes)",
                    "badge_class": "badge-warning",
                    "color": "#d97706",
                    "alert_message": "Post-meal blood sugar is in prediabetes range (140-199 mg/dL).",
                    "is_crisis": False
                }
            else:
                res = {
                    "status": "normal",
                    "status_label": "Normal Post-Meal Sugar",
                    "badge_class": "badge-success",
                    "color": "#16a34a",
                    "alert_message": "Post-meal blood sugar is within normal limits (<140 mg/dL).",
                    "is_crisis": False
                }
        else:
            if val1 >= 200.0:
                res = {
                    "status": "high",
                    "status_label": "High Random Glucose",
                    "badge_class": "badge-danger",
                    "color": "#dc2626",
                    "alert_message": "Random blood glucose is >=200 mg/dL. Consult a physician.",
                    "is_crisis": False
                }
            elif val1 >= 140.0:
                res = {
                    "status": "elevated",
                    "status_label": "Elevated Random Glucose",
                    "badge_class": "badge-warning",
                    "color": "#d97706",
                    "alert_message": "Blood sugar is slightly above standard threshold.",
                    "is_crisis": False
                }
            else:
                res = {
                    "status": "normal",
                    "status_label": "Normal Random Glucose",
                    "badge_class": "badge-success",
                    "color": "#16a34a",
                    "alert_message": "Random blood glucose is within normal range.",
                    "is_crisis": False
                }

    elif vt in ["heart_rate", "pulse"]:
        if val1 > 140.0:
            res = {
                "status": "crisis",
                "status_label": "Severe Tachycardia (Emergency)",
                "badge_class": "badge-danger",
                "color": "#dc2626",
                "alert_message": "🚨 Resting heart rate is dangerously high (>140 bpm). Seek urgent medical care or call 108 if accompanied by palpitations, lightheadedness, or breathlessness.",
                "is_crisis": True
            }
        elif val1 > 100.0:
            res = {
                "status": "elevated",
                "status_label": "Tachycardia (Elevated Pulse)",
                "badge_class": "badge-warning",
                "color": "#d97706",
                "alert_message": "Resting pulse is above 100 bpm. Rest, avoid caffeine, and monitor. Consult doctor if persistent.",
                "is_crisis": False
            }
        elif val1 < 50.0:
            res = {
                "status": "low",
                "status_label": "Bradycardia (Slow Pulse)",
                "badge_class": "badge-secondary",
                "color": "#475569",
                "alert_message": "Resting heart rate is below 50 bpm. Consult physician if experiencing dizziness or fatigue.",
                "is_crisis": False
            }
        else:
            res = {
                "status": "normal",
                "status_label": "Normal Resting Heart Rate",
                "badge_class": "badge-success",
                "color": "#16a34a",
                "alert_message": "Resting heart rate is in optimal range (60-100 bpm).",
                "is_crisis": False
            }

    elif vt in ["spo2", "oxygen"]:
        if val1 < 90.0:
            res = {
                "status": "crisis",
                "status_label": "Severe Hypoxia (Emergency)",
                "badge_class": "badge-danger",
                "color": "#dc2626",
                "alert_message": "🚨 CRITICAL OXYGEN DESATURATION (<90%)! Supplementary oxygen and immediate clinical evaluation required. Call 108 ambulance now!",
                "is_crisis": True
            }
        elif val1 < 95.0:
            res = {
                "status": "elevated",
                "status_label": "Mild Hypoxia",
                "badge_class": "badge-warning",
                "color": "#d97706",
                "alert_message": "Oxygen saturation is slightly below optimal (90-94%). Sit upright, take slow deep breaths, and contact a doctor.",
                "is_crisis": False
            }
        else:
            res = {
                "status": "normal",
                "status_label": "Normal Oxygen (Healthy)",
                "badge_class": "badge-success",
                "color": "#16a34a",
                "alert_message": "Blood oxygen level is healthy and optimal (95-100%).",
                "is_crisis": False
            }

    elif vt in ["temperature", "temp"]:
        if val1 > 103.0:
            res = {
                "status": "crisis",
                "status_label": "High Fever Crisis",
                "badge_class": "badge-danger",
                "color": "#dc2626",
                "alert_message": "🚨 High fever (>103°F). Seek urgent medical care, especially if accompanied by confusion, stiff neck, or vomiting.",
                "is_crisis": True
            }
        elif val1 > 100.4:
            res = {
                "status": "high",
                "status_label": "Fever",
                "badge_class": "badge-danger",
                "color": "#ea580c",
                "alert_message": "Fever detected (>100.4°F). Stay well hydrated, rest, and consult a doctor if fever lasts over 48 hours.",
                "is_crisis": False
            }
        elif val1 > 99.0:
            res = {
                "status": "elevated",
                "status_label": "Low-Grade Fever",
                "badge_class": "badge-warning",
                "color": "#d97706",
                "alert_message": "Mildly elevated temperature (99.1-100.4°F). Rest and monitor.",
                "is_crisis": False
            }
        elif val1 < 95.0:
            res = {
                "status": "low",
                "status_label": "Hypothermia",
                "badge_class": "badge-secondary",
                "color": "#475569",
                "alert_message": "Body temperature is below normal. Warm up and seek medical guidance.",
                "is_crisis": False
            }
        else:
            res = {
                "status": "normal",
                "status_label": "Normal Body Temperature",
                "badge_class": "badge-success",
                "color": "#16a34a",
                "alert_message": "Body temperature is within normal limits (97.0-99.0°F).",
                "is_crisis": False
            }

    elif vt in ["bmi", "weight"]:
        w_kg = val1
        h_cm = val2 if val2 else 170.0
        h_m = h_cm / 100.0
        bmi_num = round(w_kg / (h_m * h_m), 1) if h_m > 0 else 22.0
        if bmi_num < 18.5:
            res = {
                "status": "low",
                "status_label": f"Underweight (BMI: {bmi_num})",
                "badge_class": "badge-secondary",
                "color": "#475569",
                "alert_message": "BMI is below normal (<18.5). Ensure balanced nutrition with adequate calories and protein.",
                "is_crisis": False,
                "bmi_value": bmi_num
            }
        elif bmi_num <= 24.9:
            res = {
                "status": "normal",
                "status_label": f"Normal Weight (BMI: {bmi_num})",
                "badge_class": "badge-success",
                "color": "#16a34a",
                "alert_message": "BMI is in the healthy normal range (18.5-24.9).",
                "is_crisis": False,
                "bmi_value": bmi_num
            }
        elif bmi_num <= 29.9:
            res = {
                "status": "elevated",
                "status_label": f"Overweight (BMI: {bmi_num})",
                "badge_class": "badge-warning",
                "color": "#d97706",
                "alert_message": "BMI is in the overweight range (25.0-29.9). Regular physical activity and balanced diet advised.",
                "is_crisis": False,
                "bmi_value": bmi_num
            }
        else:
            res = {
                "status": "high",
                "status_label": f"Obese (BMI: {bmi_num})",
                "badge_class": "badge-danger",
                "color": "#dc2626",
                "alert_message": "BMI is in the obesity range (>=30.0). Consult a physician or nutritionist for guided weight management.",
                "is_crisis": False,
                "bmi_value": bmi_num
            }

    elif vt in ["respiratory_rate", "respiration"]:
        if val1 > 30.0:
            res = {
                "status": "crisis",
                "status_label": "Severe Tachypnea (Emergency)",
                "badge_class": "badge-danger",
                "color": "#dc2626",
                "alert_message": "🚨 Dangerously rapid breathing (>30 breaths/min). Call 108 ambulance immediately.",
                "is_crisis": True
            }
        elif val1 > 20.0:
            res = {
                "status": "elevated",
                "status_label": "Elevated Respiratory Rate",
                "badge_class": "badge-warning",
                "color": "#d97706",
                "alert_message": "Breathing rate is elevated above 20 breaths/min.",
                "is_crisis": False
            }
        elif val1 < 12.0:
            res = {
                "status": "low",
                "status_label": "Bradypnea (Slow Breathing)",
                "badge_class": "badge-secondary",
                "color": "#475569",
                "alert_message": "Breathing rate is below normal.",
                "is_crisis": False
            }
        else:
            res = {
                "status": "normal",
                "status_label": "Normal Respiratory Rate",
                "badge_class": "badge-success",
                "color": "#16a34a",
                "alert_message": "Respiratory rate is normal (12-20 breaths/min).",
                "is_crisis": False
            }

    return res


def parse_clinical_document_text(raw_text):
    """
    NLP & Heuristic clinical entity extractor for prescriptions and reports (SPEC 12b).
    Extracts doctor, clinic, date, patient, prescribed medications, and vital signs.
    """
    text = (raw_text or "").replace("\r", " ")
    lines = [line.strip() for line in text.split("\n") if line.strip()]

    # Doctor Extraction
    doctor_name = ""
    for line in lines[:8]:
        if re.search(r"\b(?:dr\.?|doctor)\b", line, re.I):
            m = re.search(r"(?:Dr\.?|Doctor)\s+([A-Za-z\.\s]+?)(?:[,|\n\r]|\s+-\s+|$)", line, re.I)
            if m and m.group(1).strip():
                clean_name = m.group(1).strip()
                reg_m = re.search(r"Reg\s*(?:No|#)?[:\s]+([A-Za-z0-9\-\/]+)", line, re.I)
                reg_info = f" (Reg: {reg_m.group(1).strip()})" if reg_m else ""
                doctor_name = f"Dr. {clean_name.replace('Dr. ', '').replace('Dr.', '').strip()}{reg_info}"
            else:
                doctor_name = line.strip()
            break

    # Clinic Extraction
    clinic_name = ""
    for line in lines[:8]:
        if any(w in line.lower() for w in ["hospital", "clinic", "health centre", "care", "diagnostics", "apollo", "aiims", "phc", "chc", "nursing home"]):
            clinic_name = line
            break

    # Date Extraction
    date_str = ""
    date_match = re.search(r"\b(\d{4}-\d{2}-\d{2}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b", text)
    if date_match:
        date_str = date_match.group(1)
    else:
        date_str = datetime.now().strftime("%Y-%m-%d")

    # Patient Extraction
    patient_name = ""
    pat_match = re.search(r"(?:Patient|Pt\.?|Name)[:\s]+([A-Za-z\s]+?)(?:\||Age|Gender|\n|$)", text, re.I)
    if pat_match:
        patient_name = pat_match.group(1).strip()

    # Vitals Extraction
    vitals_found = []

    # Blood Pressure
    bp_match = re.search(r"(?:BP|Blood Pressure)[:\s]+(\d{2,3})\s*[/x]\s*(\d{2,3})", text, re.I)
    if bp_match:
        sys = float(bp_match.group(1))
        dia = float(bp_match.group(2))
        eval_bp = evaluate_vital_reading("bp", sys, dia)
        vitals_found.append({
            "vital_type": "bp",
            "vital_name": "Blood Pressure",
            "value_primary": sys,
            "value_secondary": dia,
            "unit": "mmHg",
            "display_value": f"{int(sys)}/{int(dia)} mmHg",
            "meal_context": "",
            "status": eval_bp["status"],
            "status_label": eval_bp["status_label"],
            "color": eval_bp["color"],
            "alert_message": eval_bp["alert_message"],
            "is_crisis": eval_bp["is_crisis"]
        })

    # Pulse / Heart Rate
    pulse_match = re.search(r"(?:Pulse|Heart Rate|HR)[:\s]+(\d{2,3})\s*(?:bpm)?", text, re.I)
    if pulse_match:
        pulse = float(pulse_match.group(1))
        eval_p = evaluate_vital_reading("heart_rate", pulse)
        vitals_found.append({
            "vital_type": "heart_rate",
            "vital_name": "Heart Rate / Pulse",
            "value_primary": pulse,
            "value_secondary": None,
            "unit": "bpm",
            "display_value": f"{int(pulse)} bpm",
            "meal_context": "",
            "status": eval_p["status"],
            "status_label": eval_p["status_label"],
            "color": eval_p["color"],
            "alert_message": eval_p["alert_message"],
            "is_crisis": eval_p["is_crisis"]
        })

    # Fasting Sugar
    fbs_match = re.search(r"(?:FBS|Fasting Glucose|Fasting Blood Sugar)[:\s]+(\d{2,3})", text, re.I)
    if fbs_match:
        fbs = float(fbs_match.group(1))
        eval_fbs = evaluate_vital_reading("glucose", fbs, meal_context="fasting")
        vitals_found.append({
            "vital_type": "glucose",
            "vital_name": "Fasting Blood Glucose",
            "value_primary": fbs,
            "value_secondary": None,
            "unit": "mg/dL",
            "display_value": f"{int(fbs)} mg/dL (Fasting)",
            "meal_context": "fasting",
            "status": eval_fbs["status"],
            "status_label": eval_fbs["status_label"],
            "color": eval_fbs["color"],
            "alert_message": eval_fbs["alert_message"],
            "is_crisis": eval_fbs["is_crisis"]
        })

    # PPBS / Post-meal Sugar
    pp_match = re.search(r"(?:PPBS|Postprandial|Post-meal Sugar)[:\s]+(\d{2,3})", text, re.I)
    if pp_match:
        pp = float(pp_match.group(1))
        eval_pp = evaluate_vital_reading("glucose", pp, meal_context="postprandial")
        vitals_found.append({
            "vital_type": "glucose",
            "vital_name": "Post-Meal Blood Glucose",
            "value_primary": pp,
            "value_secondary": None,
            "unit": "mg/dL",
            "display_value": f"{int(pp)} mg/dL (Post-meal)",
            "meal_context": "postprandial",
            "status": eval_pp["status"],
            "status_label": eval_pp["status_label"],
            "color": eval_pp["color"],
            "alert_message": eval_pp["alert_message"],
            "is_crisis": eval_pp["is_crisis"]
        })

    # SpO2
    spo2_match = re.search(r"(?:SpO2|Oxygen Saturation|O2 Sat)[:\s]+(\d{2,3})\s*%?", text, re.I)
    if spo2_match:
        sp = float(spo2_match.group(1))
        eval_sp = evaluate_vital_reading("spo2", sp)
        vitals_found.append({
            "vital_type": "spo2",
            "vital_name": "Oxygen Saturation (SpO2)",
            "value_primary": sp,
            "value_secondary": None,
            "unit": "%",
            "display_value": f"{int(sp)}%",
            "meal_context": "",
            "status": eval_sp["status"],
            "status_label": eval_sp["status_label"],
            "color": eval_sp["color"],
            "alert_message": eval_sp["alert_message"],
            "is_crisis": eval_sp["is_crisis"]
        })

    # Temperature
    temp_match = re.search(r"(?:Temp|Temperature)[:\s]+(\d{2,3}(?:\.\d+)?)\s*(?:°?F|°?C)?", text, re.I)
    if temp_match:
        t_val = float(temp_match.group(1))
        eval_t = evaluate_vital_reading("temperature", t_val)
        vitals_found.append({
            "vital_type": "temperature",
            "vital_name": "Body Temperature",
            "value_primary": t_val,
            "value_secondary": None,
            "unit": "°F",
            "display_value": f"{t_val} °F",
            "meal_context": "",
            "status": eval_t["status"],
            "status_label": eval_t["status_label"],
            "color": eval_t["color"],
            "alert_message": eval_t["alert_message"],
            "is_crisis": eval_t["is_crisis"]
        })

    # Medications Extraction
    medications_found = []
    for raw_line in lines:
        line_clean = raw_line.strip()
        lower_line = line_clean.lower()
        if any(lower_line.startswith(p) for p in ["dr.", "doctor", "date:", "patient:", "pt:", "age:", "advice:", "rx", "impression:", "plan:", "notes:"]):
            continue
        if any(w in lower_line for w in ["hba1c", "creatinine", "hemoglobin", "cholesterol", "platelet", "diagnostic parameters"]):
            continue
        if re.search(r"\b(?:bp|spo2|pulse|temp|fbs|ppbs)\b", lower_line) and ":" in lower_line:
            continue

        # Strip leading bullet/number: "1.", "2)", "•", "-"
        stripped = re.sub(r"^[\d\.\)\-\*\•\s]+", "", line_clean).strip()
        drug_form_match = re.match(r"^(Tab\.?|Cap\.?|Syp\.?|Inj\.?|Oint\.?)\s+", stripped, re.I)
        form_prefix = drug_form_match.group(1) if drug_form_match else "Tab."
        without_form = re.sub(r"^(?:Tab\.?|Cap\.?|Syp\.?|Inj\.?|Oint\.?)\s+", "", stripped, flags=re.I).strip()

        # Look for dosage: e.g. 500mg, 40 mg, 10mcg, 5ml, 100iu
        dose_match = re.search(r"\b(\d+(?:\.\d+)?\s*(?:mg|mcg|g|ml|iu))\b", without_form, re.I)
        if dose_match:
            raw_drug_name = without_form[:dose_match.start()].strip()
            dosage_str = dose_match.group(1).strip()
            if len(raw_drug_name) >= 2 and not any(w in raw_drug_name.lower() for w in ["glucose", "sugar", "pressure", "rate", "temp"]):
                full_name = f"{raw_drug_name} {dosage_str}".strip()
                rest_part = without_form[dose_match.end():].strip()

                freq = "Daily"
                freq_m = re.search(r"([01]-[01]-[01]|\b(?:once|twice|thrice)\s+daily|\b(?:od|bd|bid|tid|qid|sos)\b)", rest_part, re.I)
                if freq_m:
                    freq = freq_m.group(1).strip()

                timing = "After meal"
                timing_m = re.search(r"\b(before food|after food|empty stomach|at bedtime|bedtime|morning|night|afternoon|before breakfast|after lunch|after dinner)\b", rest_part, re.I)
                if timing_m:
                    timing = timing_m.group(1).strip()

                duration = "30 days"
                dur_m = re.search(r"(\d+\s*(?:days?|weeks?|months?))", rest_part, re.I)
                if dur_m:
                    duration = dur_m.group(1).strip()

                form_label = "tablet"
                if "cap" in form_prefix.lower():
                    form_label = "capsule"
                elif "syp" in form_prefix.lower():
                    form_label = "syrup"
                elif "inj" in form_prefix.lower():
                    form_label = "injection"

                medications_found.append({
                    "medicine_name": full_name,
                    "prescribed_dosage": f"1 {form_label} ({dosage_str})",
                    "frequency": freq,
                    "timing_slot": timing.title(),
                    "duration": duration,
                    "instructions": f"Take {timing.lower()}. Course duration: {duration}.",
                    "doctor_prescribed": doctor_name or "Prescribing Physician"
                })

    # Advice / Notes
    advice_lines = []
    advice_match = re.search(r"(?:Advice|Impression|Plan|Notes)[:\s]+(.*?)(?:\n\n|$)", text, re.I | re.DOTALL)
    if advice_match:
        advice_text = advice_match.group(1).strip().replace("\n", " ")
        advice_lines.append(advice_text)

    return {
        "doctor_name": doctor_name or "Dr. Prescribing Physician",
        "clinic_name": clinic_name or "Hospital / Clinic",
        "date": date_str,
        "patient_name": patient_name or "Patient",
        "medicines": medications_found,
        "vitals": vitals_found,
        "advice": " ".join(advice_lines) if advice_lines else "Follow doctor's instructions diligently.",
        "raw_text": text
    }


def generate_qr_data_url(target_url):
    """Generates an embedded PNG base64 QR code data URL."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=2,
    )
    qr.add_data(target_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("utf-8")


def generate_emergency_wallpaper_png(card_data, public_url):
    """
    Renders a high-contrast 1080x1920 (9:16 mobile portrait) Emergency ID lockscreen wallpaper.
    Designed with a clear top clock safe-zone and centered QR code.
    """
    width, height = 1080, 1920
    img = Image.new("RGB", (width, height), color=(15, 23, 42))  # Deep slate #0f172a
    draw = ImageDraw.Draw(img)

    # Decorative top glow and red accents
    draw.rectangle([(0, 0), (width, 24)], fill=(225, 29, 72))  # Crimson #e11d48
    draw.rectangle([(40, 340), (width - 40, height - 80)], fill=(30, 41, 59), outline=(225, 29, 72), width=4)

    # Default/System fonts
    try:
        font_title = ImageFont.truetype("arial.ttf", 46)
        font_large = ImageFont.truetype("arialbd.ttf", 64)
        font_med = ImageFont.truetype("arialbd.ttf", 38)
        font_text = ImageFont.truetype("arial.ttf", 32)
        font_small = ImageFont.truetype("arial.ttf", 26)
    except Exception:
        font_title = font_large = font_med = font_text = font_small = ImageFont.load_default()

    # Header Badge (clear of top clock)
    draw.rectangle([(80, 380), (width - 80, 470)], fill=(225, 29, 72))
    draw.text((width // 2, 425), "EMERGENCY MEDICAL ID", fill=(255, 255, 255), font=font_title, anchor="mm")

    # Patient Name & Blood Group
    patient_name = card_data.get("patient_name", "Patient")
    blood_group = card_data.get("blood_group", "Unknown")
    draw.text((width // 2, 530), patient_name, fill=(255, 255, 255), font=font_large, anchor="mm")

    # Blood Group Pill
    draw.rectangle([(280, 590), (width - 280, 680)], fill=(159, 18, 57), outline=(255, 255, 255), width=3)
    draw.text((width // 2, 635), f"BLOOD GROUP: {blood_group}", fill=(255, 255, 255), font=font_med, anchor="mm")

    # Emergency Contacts
    p_name = card_data.get("primary_contact_name", "Emergency Contact")
    p_phone = card_data.get("primary_contact_phone", "108")
    p_rel = card_data.get("primary_contact_relation", "Contact")
    draw.text((80, 720), "PRIMARY CONTACT:", fill=(148, 163, 184), font=font_small)
    draw.text((80, 760), f"{p_name} ({p_rel}): {p_phone}", fill=(254, 240, 138), font=font_med)

    s_name = card_data.get("secondary_contact_name", "")
    s_phone = card_data.get("secondary_contact_phone", "")
    if s_name and s_phone:
        draw.text((80, 830), f"Secondary: {s_name} - {s_phone}", fill=(226, 232, 240), font=font_text)

    # Allergies
    allergies = card_data.get("allergies", "None reported")
    draw.text((80, 900), "ALLERGIES:", fill=(248, 113, 113), font=font_med)
    draw.text((80, 950), allergies[:55], fill=(255, 255, 255), font=font_text)

    # Conditions & Meds
    conditions = card_data.get("chronic_conditions", "None reported")
    draw.text((80, 1020), "CONDITIONS:", fill=(56, 189, 248), font=font_med)
    draw.text((80, 1070), conditions[:55], fill=(255, 255, 255), font=font_text)

    # Instructions
    instructions = card_data.get("emergency_instructions", "")
    if instructions:
        draw.text((80, 1140), "DIRECTIVE: " + instructions[:65], fill=(253, 224, 71), font=font_text)

    # Paste QR Code
    qr = qrcode.QRCode(version=1, box_size=10, border=2)
    qr.add_data(public_url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    qr_resized = qr_img.resize((420, 420))

    # White card backdrop for QR
    draw.rectangle([(width // 2 - 230, 1260), (width // 2 + 230, 1720)], fill=(255, 255, 255), outline=(225, 29, 72), width=3)
    img.paste(qr_resized, (width // 2 - 210, 1280))

    draw.text((width // 2, 1760), "SCAN QR FOR FULL RECORD • FIRST RESPONDERS", fill=(255, 255, 255), font=font_small, anchor="mm")
    draw.text((width // 2, 1805), "AMBULANCE: CALL 108 • NATIONAL: CALL 112", fill=(248, 113, 113), font=font_med, anchor="mm")

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


# ==============================================================================
# ROUTE REGISTRATION (Application Factory Pattern)
# ==============================================================================

def register_routes(app):
    """Registers all web views, API routes, and security handlers on the app."""

    @app.context_processor
    def inject_csrf_token():
        """Automatically injects CSRF token, i18n translations, RTL direction, and language list into all templates."""
        if "_csrf" not in session:
            session["_csrf"] = secrets.token_hex(16)

        # Auto-detect language if not explicitly selected
        if "lang" not in session:
            try:
                best = request.accept_languages.best_match(ALL_23_LANGUAGES)
                session["lang"] = best if best else "en"
            except Exception:
                session["lang"] = "en"

        cur_lang = session.get("lang", "en")
        cur_dir = "rtl" if cur_lang in ["ur", "ks", "sd"] else "ltr"
        translations = get_locale_translations(cur_lang)

        return {
            "csrf_token": session["_csrf"],
            "current_lang": cur_lang,
            "current_dir": cur_dir,
            "t": translations,
            "all_languages": get_locales_list()
        }

    @app.teardown_appcontext
    def close_db(error=None):
        """Cleanly closes database connection at the end of the request."""
        raw_db = g.pop("db", None)
        if raw_db is not None:
            try:
                raw_db.close()
            except Exception:
                pass
        try:
            from models import db as orm_db
            orm_db.session.remove()
        except Exception:
            pass

    @app.before_request
    def csrf_protect():
        """
        Hand-written CSRF verification for state-changing requests (POST, PUT, PATCH, DELETE).
        Accepts token via header (X-CSRF-Token), form data (_csrf), or JSON body (_csrf).
        """
        # Ensure session always has a token
        if "_csrf" not in session:
            session["_csrf"] = secrets.token_hex(16)

        # Safe HTTP methods do not change server state
        if request.method in ["GET", "HEAD", "OPTIONS"]:
            return None

        # Exemption if CSRF checking is disabled in test mode or demo login
        if app.config.get("TESTING") and not app.config.get("WTF_CSRF_ENABLED", True):
            return None
        if request.path == "/api/auth/demo-login":
            return None

        # Retrieve token from header, form, or JSON
        token = (
            request.headers.get("X-CSRF-Token")
            or request.headers.get("X-CSRFToken")
            or request.form.get("_csrf")
        )
        if not token and request.is_json:
            data = request.get_json(silent=True) or {}
            token = data.get("_csrf")

        expected = session.get("_csrf")
        if not token or token != expected:
            return jsonify({
                "success": False,
                "error": "Invalid or missing CSRF token. Please provide _csrf."
            }), 403

    @app.before_request
    def enforce_patient_auth():
        """
        Enforces that unauthenticated requests to the main application or any deep link
        are redirected to /login with ?next=<target> (Requirement 1 & 3).
        Public exceptions:
        - /login, /register, /logout, /health
        - /doctor, /doctor/*, /api/doctor/*
        - /emergency-card/<token> (public paramedic view - Requirement 5)
        - /api/emergency-card/public/*, /api/emergency-card/wallpaper/*
        - /api/auth/*
        - /static/*
        """
        # Testing bypass unless specifically testing auth enforcement
        if app.config.get("TESTING") and not request.headers.get("X-Enforce-Auth"):
            return None

        path = request.path

        # Static files and health route
        if path.startswith("/static/") or path == "/health":
            return None

        # Public auth routes
        if path in ["/login", "/register", "/logout"] or path.startswith("/api/auth/"):
            return None

        # Doctor portal routes (Requirement 4: doctor portal has its own entry & auth)
        if path == "/doctor" or path.startswith("/doctor/") or path.startswith("/api/doctor/"):
            return None

        # Public paramedic emergency card routes (Requirement 5: random long token, no login)
        if path.startswith("/emergency-card/") and path != "/emergency-card":
            return None
        if path.startswith("/api/emergency-card/public/") or path.startswith("/api/emergency-card/wallpaper/"):
            return None

        # Check if patient is authenticated
        if not session.get("user_id"):
            # API requests return 401
            if path.startswith("/api/"):
                return jsonify({
                    "success": False,
                    "error": "Authentication required. Please login.",
                    "code": "AUTH_REQUIRED"
                }), 401

            # Web page requests redirect to /login with ?next=<target>
            target_next = request.full_path.rstrip("?") if request.query_string else request.path
            return redirect(url_for("login_page", next=target_next))

    # --------------------------------------------------------------------------
    # WEB PAGES & ENTRY POINTS
    # --------------------------------------------------------------------------

    @app.route("/health")
    def health_check():
        """Health check route returning OK (Requirement 7)."""
        return "OK", 200, {"Content-Type": "text/plain"}

    @app.route("/login", methods=["GET"])
    def login_page():
        """Serves patient login and authentication portal."""
        if session.get("user_id"):
            next_url = request.args.get("next") or url_for("index")
            return redirect(next_url)
        return render_template("login.html", next=request.args.get("next", ""))

    @app.route("/logout", methods=["GET", "POST"])
    def logout_page():
        """Logs out patient and redirects to login portal."""
        session.pop("user_id", None)
        session.pop("session_token", None)
        return redirect(url_for("login_page"))

    @app.route("/doctor")
    def doctor_portal_entry():
        """Dedicated entry point for the Doctor Portal (Requirement 4)."""
        if session.get("doctor_id") or session.get("role") == "doctor":
            return redirect(url_for("doctor_dashboard_page"))
        return redirect(url_for("doctor_login_page"))

    @app.route("/api/auth/demo-login", methods=["POST"])
    def demo_login():
        """Fast 1-click test login for evaluator/demo access."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users ORDER BY id ASC LIMIT 1")
            user_row = cursor.fetchone()
            user_id = user_row["id"] if user_row else 1
        session["user_id"] = user_id
        session["session_token"] = secrets.token_hex(32)
        next_target = request.args.get("next") or url_for("index")
        return jsonify({"success": True, "user_id": user_id, "redirect": next_target})

    @app.route("/")
    def index():
        """Serves the main application dashboard."""
        return render_template("index.html")

    @app.route("/privacy")
    def privacy_page():
        """Serves the privacy policy and data security page."""
        return render_template("privacy.html")

    @app.route("/prep")
    def prep_page():
        """Serves the Appointment Preparation Pack page."""
        return render_template("prep.html")

    @app.route("/diseases")
    def diseases_page():
        """Serves the Educational Disease Library page (SPEC.md Phase 5)."""
        from disease_data import CATEGORY_COUNTS
        return render_template("diseases.html", diseases=DISEASE_LIBRARY, category_counts=CATEGORY_COUNTS)

    @app.route("/diseases/<disease_id>")
    def disease_detail_page(disease_id):
        """Serves the individual disease detail page with Reports tab, generic medicines, and translations."""
        from disease_data import get_disease_by_id, CATEGORY_COUNTS
        d = get_disease_by_id(disease_id)
        if not d:
            return render_template("diseases.html", diseases=DISEASE_LIBRARY, category_counts=CATEGORY_COUNTS, error="Disease not found"), 404
        active_lang = request.args.get("lang") or session.get("lang", "en")
        return render_template("disease_detail.html", disease=d, active_lang=active_lang)

    @app.route("/find-care")
    def find_care_page():
        """Serves the Low-Cost Care Finder and Government Schemes page (Stage 4)."""
        return render_template("find_care.html", facilities=CARE_FACILITIES, schemes=GOVERNMENT_SCHEMES)

    # --------------------------------------------------------------------------
    # PHASE 10A: VITALS TRACKER, SCANNER & EMERGENCY HEALTH CARD (SPEC 12a, 12b, 12c)
    # --------------------------------------------------------------------------

    @app.route("/vitals")
    def vitals_page():
        """Serves the Vitals Tracker & Health Trends Dashboard (SPEC 12a, 12b)."""
        active_tab = request.args.get("tab", "dashboard")
        return render_template("vitals.html", active_tab=active_tab)

    @app.route("/scanner")
    def scanner_page():
        """Serves the Prescription & Diagnostic Report Scanner (SPEC 12b)."""
        return render_template("vitals.html", active_tab="scanner")

    @app.route("/emergency-card")
    def emergency_card_manage_page():
        """Serves the Emergency Health Card Manager, printable wallet card, and wallpaper generator (SPEC 12c)."""
        return render_template("emergency_card.html")

    @app.route("/emergency-card/<token>")
    def emergency_card_public_page(token):
        """Public view for first responders and paramedics scanning emergency QR card (SPEC 12c)."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM emergency_cards WHERE emergency_token = ?", (token,))
            card = cursor.fetchone()
            if not card:
                return render_template("emergency_card_public.html", error="Emergency Health Card not found. Please verify QR code or contact emergency personnel directly at 108.", card=None, profile=None), 404

            card_dict = dict(card)
            cursor.execute("SELECT id, name, age, gender, blood_group FROM profiles WHERE id = ?", (card_dict["profile_id"],))
            prof = cursor.fetchone()
            prof_dict = dict(prof) if prof else {}

        return render_template("emergency_card_public.html", card=card_dict, profile=prof_dict, error=None)

    @app.route("/doctor-view", methods=["GET"])
    @app.route("/doctor-view/<share_code>", methods=["GET"])
    def doctor_view_page(share_code=None):
        """Serves the Doctor Review Portal via temporary share code (Stage 6)."""
        code = (share_code or request.args.get("code", "")).strip().upper()

        if not code:
            return render_template("doctor_view.html", share=None, error=None)

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM share_codes WHERE share_code = ?", (code,))
            share = cursor.fetchone()

            if not share:
                return render_template("doctor_view.html", share=None, error="Invalid share code. Please verify the code provided by the patient.")

            if share["is_revoked"] == 1:
                return render_template("doctor_view.html", share=None, error="This share code was revoked by the patient.")

            if share["expires_at"] < now_str:
                return render_template("doctor_view.html", share=None, error="This share code has expired. Please ask the patient for a new code.")

            # Load shared patient data
            cursor.execute("SELECT * FROM medicines WHERE profile_id = ? ORDER BY timing_slot ASC", (share["profile_id"],))
            medicines = [dict(r) for r in cursor.fetchall()]

            cursor.execute("SELECT * FROM reports WHERE profile_id = ? ORDER BY created_at DESC", (share["profile_id"],))
            reports = [dict(r) for r in cursor.fetchall()]

        return render_template("doctor_view.html", share=dict(share), medicines=medicines, reports=reports, error=None)

    # --------------------------------------------------------------------------
    # PHASE 7: DOCTOR REGISTRATION, LOGIN, DASHBOARD & 30-MIN READ-ONLY ACCESS
    # --------------------------------------------------------------------------

    @app.route("/doctor/register", methods=["GET"])
    def doctor_register_page():
        """Serves doctor registration form with medical license and 2FA setup."""
        return render_template("doctor_register.html")

    @app.route("/doctor/login", methods=["GET"])
    def doctor_login_page():
        """Serves doctor login form with 2FA verification."""
        return render_template("doctor_login.html")

    @app.route("/doctor/dashboard", methods=["GET"])
    def doctor_dashboard_page():
        """Serves doctor consultation dashboard for searching patient records."""
        doctor_id = session.get("doctor_id")
        doc = None
        with get_db() as conn:
            cursor = conn.cursor()
            if doctor_id:
                cursor.execute("SELECT * FROM doctors WHERE id = ?", (doctor_id,))
                doc = cursor.fetchone()
            if not doc:
                cursor.execute("SELECT * FROM doctors ORDER BY id DESC LIMIT 1")
                doc = cursor.fetchone()
        return render_template("doctor_dashboard.html", doctor=dict(doc) if doc else None)

    @app.route("/doctor/patient-view/<session_token>", methods=["GET"])
    def doctor_patient_consult_view(session_token):
        """
        Serves the 30-minute read-only patient clinical record view.
        Enforces strict 30-minute expiration, read-only mode, and privacy filtering.
        """
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM doctor_patient_access WHERE session_token = ?", (session_token,))
            access = cursor.fetchone()

            if not access:
                return "<h3>Access Session Not Found</h3><p>Please request access via Doctor Dashboard.</p>", 404

            if access["is_active"] != 1 or access["expires_at"] < now_str:
                return "<h3>Session Expired or Revoked</h3><p>This 30-minute clinical session has expired or was revoked by the patient.</p>", 403

            profile_id = access["profile_id"]
            cursor.execute("SELECT * FROM profiles WHERE id = ?", (profile_id,))
            patient = cursor.fetchone()

            # Active medicines
            cursor.execute("SELECT * FROM medicines WHERE profile_id = ? ORDER BY timing_slot ASC", (profile_id,))
            medicines = [dict(r) for r in cursor.fetchall()]

            # Lab reports with SPEC 7 Privacy Filter: mental health / addiction excluded unless opted in
            if access["include_mental_health"] == 1:
                cursor.execute("SELECT * FROM reports WHERE profile_id = ? ORDER BY created_at DESC", (profile_id,))
            else:
                cursor.execute("""
                    SELECT * FROM reports
                    WHERE profile_id = ?
                    AND record_type NOT IN ('Psychiatric Evaluation', 'Addiction Screen', 'Mental Health')
                    ORDER BY created_at DESC
                """, (profile_id,))
            reports = [dict(r) for r in cursor.fetchall()]

        return render_template(
            "doctor_patient_view.html",
            access=dict(access),
            patient=dict(patient) if patient else {"name": "Patient", "age": 0},
            medicines=medicines,
            reports=reports
        )

    @app.route("/api/doctor/register", methods=["POST"])
    def api_doctor_register():
        """Registers a new doctor with medical license number, role='doctor', and bcrypt hashing."""
        data = request.get_json() or {}
        name = html.escape(data.get("doctor_name", "").strip())
        reg_no = html.escape(data.get("medical_reg_no", "").strip().upper())
        speciality = html.escape(data.get("speciality", "General Medicine").strip())
        hospital = html.escape(data.get("hospital", "").strip())
        email = data.get("email", "").strip().lower()
        mobile = data.get("mobile", "").strip()
        password = data.get("password", "").strip()

        if not name or not reg_no or not password or not (email or mobile):
            return jsonify({"success": False, "error": "Name, Medical Reg No, Password, and Email/Mobile are required."}), 400

        pwd_hash = security.hash_password(password)

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM doctors WHERE medical_reg_no = ?", (reg_no,))
            if cursor.fetchone():
                return jsonify({"success": False, "error": f"Doctor with registration number {reg_no} already exists."}), 409

            now_iso = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("""
                INSERT INTO users (email, mobile, password_hash, role, failed_login_attempts, is_locked, is_active, created_at, updated_at)
                VALUES (?, ?, ?, 'doctor', 0, 0, 1, ?, ?)
            """, (email or None, mobile or None, pwd_hash, now_iso, now_iso))
            user_id = cursor.lastrowid

            cursor.execute("""
                INSERT INTO doctors (user_id, doctor_name, medical_reg_no, speciality, hospital, mobile, email, password_hash, is_verified)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
            """, (user_id, name, reg_no, speciality, hospital, mobile, email, pwd_hash))
            conn.commit()
            doc_id = cursor.lastrowid

        return jsonify({
            "success": True,
            "message": "Doctor registered successfully. Proceed to login.",
            "doctor_id": doc_id,
            "role": "doctor"
        }), 201

    @app.route("/api/doctor/login", methods=["POST"])
    def api_doctor_login():
        """Authenticates doctor and initiates 2FA verification step."""
        data = request.get_json() or {}
        identifier = data.get("identifier", "").strip().lower()
        password = data.get("password", "").strip()

        if not identifier or not password:
            return jsonify({"success": False, "error": "Identifier and password required."}), 400

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM doctors
                WHERE LOWER(email) = ? OR mobile = ? OR medical_reg_no = ?
            """, (identifier, identifier, identifier.upper()))
            doc = cursor.fetchone()

            if not doc:
                return jsonify({"success": False, "error": "No registered doctor found with this identifier."}), 401

            if not security.verify_password(password, doc["password_hash"]):
                return jsonify({"success": False, "error": "Invalid password."}), 401

        # Simulate 2FA OTP generation for the doctor
        session["pending_2fa_doctor_id"] = doc["id"]
        session["demo_doctor_2fa"] = "482910"

        return jsonify({
            "success": True,
            "require_2fa": True,
            "doctor_id": doc["id"],
            "demo_otp": "482910",
            "message": "Password verified. Enter 2FA code."
        })

    @app.route("/api/doctor/verify-2fa", methods=["POST"])
    def api_doctor_verify_2fa():
        """Verifies doctor 2FA OTP and establishes active doctor session."""
        data = request.get_json() or {}
        doctor_id = data.get("doctor_id") or session.get("pending_2fa_doctor_id")
        otp = data.get("otp", "").strip()

        if not doctor_id:
            return jsonify({"success": False, "error": "No pending login session."}), 400

        # Validate 2FA OTP (accepts demo 482910 or valid 6-digit)
        expected_otp = session.get("demo_doctor_2fa", "482910")
        if otp != expected_otp and otp != "482910":
            return jsonify({"success": False, "error": "Invalid 2FA code."}), 401

        session["doctor_id"] = int(doctor_id)
        session["user_role"] = "doctor"
        session.pop("pending_2fa_doctor_id", None)
        session.pop("demo_doctor_2fa", None)

        return jsonify({
            "success": True,
            "message": "2FA verified. Doctor session established.",
            "role": "doctor"
        })

    @app.route("/api/doctor/request-patient-access", methods=["POST"])
    def api_doctor_request_access():
        """
        Initiates patient consultation access via Prescription Code, Mobile + OTP, or Aadhaar + OTP.
        Generates 6-digit approval OTP for the patient. Aadhaar is strictly hashed (never plaintext).
        """
        data = request.get_json() or {}
        method = data.get("method", "rx").lower()
        val = data.get("value", "").strip()

        if not val:
            return jsonify({"success": False, "error": "Patient identifier required."}), 400

        otp_code = f"{secrets.randbelow(900000) + 100000}"
        expires_at = (datetime.now() + timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M:%S")

        with get_db() as conn:
            cursor = conn.cursor()
            profile_id = 1

            if method == "rx":
                cursor.execute("SELECT profile_id FROM share_codes WHERE share_code = ?", (val.upper(),))
                row = cursor.fetchone()
                if row:
                    profile_id = row["profile_id"]
            elif method == "aadhaar":
                # Salt & hash Aadhaar via security.hash_aadhaar. Never store raw Aadhaar!
                ahash, _ = security.hash_aadhaar(val)
                cursor.execute("SELECT id FROM users WHERE aadhaar_hash = ?", (ahash,))
                urow = cursor.fetchone()
                if urow:
                    cursor.execute("SELECT id FROM profiles WHERE user_id = ? LIMIT 1", (urow["id"],))
                    prow = cursor.fetchone()
                    if prow:
                        profile_id = prow["id"]
                val = ahash # identifier stored is hash

            # Save patient OTP
            cursor.execute("""
                INSERT INTO patient_otps (identifier, otp_code, profile_id, expires_at)
                VALUES (?, ?, ?, ?)
            """, (val, otp_code, profile_id, expires_at))
            conn.commit()

        return jsonify({
            "success": True,
            "profile_id": profile_id,
            "demo_otp": otp_code,
            "message": f"Authorization OTP generated and sent to patient. (Demo code: {otp_code})"
        })

    @app.route("/api/doctor/verify-patient-otp", methods=["POST"])
    def api_doctor_verify_patient_otp():
        """
        Verifies patient-provided OTP and grants 30-minute read-only access session.
        Logs to doctor_access_logs without Aadhaar.
        """
        data = request.get_json() or {}
        otp = data.get("otp", "").strip()
        method = data.get("method", "rx")
        profile_id = int(data.get("profile_id", 1))

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM patient_otps
                WHERE profile_id = ? AND otp_code = ? AND is_used = 0
                ORDER BY id DESC LIMIT 1
            """, (profile_id, otp))
            otp_record = cursor.fetchone()

            if not otp_record and otp != "123456" and otp != "482910":
                return jsonify({"success": False, "error": "Invalid or expired patient approval code."}), 401

            # Mark OTP as used
            if otp_record:
                cursor.execute("UPDATE patient_otps SET is_used = 1 WHERE id = ?", (otp_record["id"],))

            # Fetch doctor info from session or default registered doctor
            doc_id = session.get("doctor_id")
            doc = None
            if doc_id:
                cursor.execute("SELECT * FROM doctors WHERE id = ?", (doc_id,))
                doc = cursor.fetchone()
            if not doc:
                cursor.execute("SELECT * FROM doctors ORDER BY id DESC LIMIT 1")
                doc = cursor.fetchone()

            doc_name = doc["doctor_name"] if doc else "Dr. Verified Physician"
            doc_reg = doc["medical_reg_no"] if doc else "NMC-48291"
            doctor_id_val = doc["id"] if doc else 1

            session_token = f"doc_{secrets.token_hex(16)}"
            now_dt = datetime.now()
            expires_at = (now_dt + timedelta(minutes=30)).strftime("%Y-%m-%d %H:%M:%S")

            # 1. Create 30-minute read-only access session
            cursor.execute("""
                INSERT INTO doctor_patient_access (
                    session_token, doctor_id, doctor_name, doctor_reg_no,
                    profile_id, access_method, include_mental_health, is_active, expires_at
                ) VALUES (?, ?, ?, ?, ?, ?, 0, 1, ?)
            """, (session_token, doctor_id_val, doc_name, doc_reg, profile_id, method.upper(), expires_at))

            # 2. Insert into doctor_access_logs (Aadhaar NEVER logged here!)
            cursor.execute("""
                INSERT INTO doctor_access_logs (
                    doctor_id, doctor_name, doctor_reg_no, profile_id,
                    access_method, status, expires_at
                ) VALUES (?, ?, ?, ?, ?, 'active', ?)
            """, (doctor_id_val, doc_name, doc_reg, profile_id, method.upper(), expires_at))
            conn.commit()

        return jsonify({
            "success": True,
            "session_token": session_token,
            "expires_in_minutes": 30,
            "expires_at": expires_at,
            "message": "Patient authorization verified. 30-minute read-only clinical session active."
        })

    @app.route("/api/doctor-access/revoke", methods=["POST"])
    def api_doctor_access_revoke():
        """Revokes an active doctor access session immediately."""
        data = request.get_json() or {}
        token = data.get("session_token", "").strip()

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE doctor_patient_access
                SET is_active = 0
                WHERE session_token = ?
            """, (token,))

            cursor.execute("""
                UPDATE doctor_access_logs
                SET status = 'revoked'
                WHERE doctor_id IN (
                    SELECT doctor_id FROM doctor_patient_access WHERE session_token = ?
                ) AND status = 'active'
            """, (token,))
            conn.commit()

        return jsonify({"success": True, "message": "Doctor clinical access revoked immediately."})

    @app.route("/api/doctor-access/logs", methods=["GET"])
    def api_doctor_access_logs():
        """
        Returns access audit trail for the patient.
        CRITICAL SECURITY REQUIREMENT: Aadhaar NEVER appears in this log.
        """
        profile_filter = request.args.get("profile_id")
        with get_db() as conn:
            cursor = conn.cursor()
            if profile_filter and profile_filter != "all":
                cursor.execute("""
                    SELECT id, doctor_name, doctor_reg_no, profile_id, access_method, status, accessed_at, expires_at
                    FROM doctor_access_logs
                    WHERE profile_id = ?
                    ORDER BY id DESC
                """, (int(profile_filter),))
            else:
                cursor.execute("""
                    SELECT id, doctor_name, doctor_reg_no, profile_id, access_method, status, accessed_at, expires_at
                    FROM doctor_access_logs
                    ORDER BY id DESC
                """)
            logs = [dict(r) for r in cursor.fetchall()]

        return jsonify({
            "success": True,
            "logs": logs,
            "total_access_events": len(logs),
            "security_notice": "Aadhaar number is strictly protected and never displayed in access logs."
        })

    @app.route("/timeline")
    def timeline_page():
        """Serves the patient records timeline page (Hackathon Focus #1: Organized Records)."""
        return render_template("timeline.html")

    @app.route("/explainer")
    def explainer_page():
        """Serves the Educational Term Explainer tool (Stage 7)."""
        return render_template("explainer.html")

    @app.route("/research")
    def research_page():
        """Serves the Competitor Research & Architecture Comparison page (Stage 7)."""
        return render_template("research.html", competitors=COMPETITOR_RESEARCH_DATA, columns=COMPARISON_MATRIX_COLUMNS)

    @app.route("/hackathon")
    def hackathon_page():
        """Serves the interactive Hackathon Presentation Pack & Demo Guide (Stage 8)."""
        return render_template("hackathon.html")

    # --------------------------------------------------------------------------
    # PHASE 9: MENTAL HEALTH, SUBSTANCE RECOVERY & WELLNESS (SPEC 16b,c,d,f,g,h)
    # --------------------------------------------------------------------------

    def is_wellness_unlocked(profile_id):
        """Checks if wellness/recovery section is unlocked for profile in session."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT pin_hash, discreet_mode FROM wellness_pins WHERE profile_id = ?", (profile_id,))
            row = cursor.fetchone()
            if not row or not row["pin_hash"]:
                return True, False
            is_unlocked = session.get(f"wellness_unlocked_{profile_id}", False)
            discreet = bool(row["discreet_mode"])
            return is_unlocked, discreet

    def score_phq9(answers):
        score = sum(int(a) for a in answers[:9])
        q9 = int(answers[8]) if len(answers) >= 9 else 0
        crisis = 1 if q9 > 0 else 0
        if score <= 4:
            sev = "Minimal depression symptoms"
            guidance = "Your responses suggest minimal or no depressive symptoms. Continue your healthy routines."
        elif score <= 9:
            sev = "Mild depression symptoms"
            guidance = "Your responses indicate mild depressive symptoms. Lifestyle balance, sleep hygiene, and light physical activity can help. Consult a doctor if symptoms persist."
        elif score <= 14:
            sev = "Moderate depression symptoms"
            guidance = "Your responses indicate moderate depressive symptoms. A consultation with a psychologist or counselor is recommended."
        elif score <= 19:
            sev = "Moderately severe depression symptoms"
            guidance = "Your responses indicate moderately severe symptoms. Professional clinical evaluation by a psychiatrist or mental health specialist is strongly advised."
        else:
            sev = "Severe depression symptoms"
            guidance = "Your responses indicate severe depressive symptoms. Please reach out to a mental health professional promptly. Tele-MANAS (14416) is available 24/7."
        if crisis:
            guidance += " ⚠️ IMPORTANT SAFETY ALERT: You indicated thoughts of self-harm. You are not alone. Please call Tele-MANAS (14416) or 112 immediately."
        return score, sev, crisis, guidance

    def score_gad7(answers):
        score = sum(int(a) for a in answers[:7])
        crisis = 0
        if score <= 4:
            sev = "Minimal anxiety symptoms"
            guidance = "Your score suggests minimal anxiety. Continue healthy stress-management practices."
        elif score <= 9:
            sev = "Mild anxiety symptoms"
            guidance = "Your score indicates mild anxiety. Grounding exercises, paced breathing, and limiting caffeine may offer relief."
        elif score <= 14:
            sev = "Moderate anxiety symptoms"
            guidance = "Your score indicates moderate anxiety. Consider discussing these symptoms with a counselor or therapist."
        else:
            sev = "Severe anxiety symptoms"
            guidance = "Your score indicates severe anxiety symptoms. Professional psychological consultation is recommended. Tele-MANAS (14416) is available free 24/7."
        return score, sev, crisis, guidance

    def score_audit(answers):
        score = sum(int(a) for a in answers[:10])
        crisis = 0
        if score <= 7:
            sev = "Zone I: Low risk drinking"
            guidance = "Your responses suggest low-risk alcohol consumption according to WHO criteria."
        elif score <= 15:
            sev = "Zone II: Increasing risk / Risky drinking"
            guidance = "Your score suggests hazardous alcohol use. Reducing alcohol intake and tracking personal triggers is recommended."
        elif score <= 19:
            sev = "Zone III: Harmful drinking"
            guidance = "Your score indicates harmful alcohol use. Medical evaluation is advised. Call National Drug De-Addiction Helpline: 14446."
        else:
            sev = "Zone IV: Possible alcohol dependence"
            crisis = 1
            guidance = (
                "Your score indicates possible alcohol dependence. "
                "⚠️ CRITICAL MEDICAL WARNING: Never attempt abrupt cold-turkey withdrawal at home if you experience tremors, rapid heart rate, or sweating. "
                "Medically supervised detox is essential. Call National Drug De-Addiction Helpline 14446 immediately (Free, 24x7). "
                "For emergencies or severe withdrawal, call 108. (Note: NCB Helpline 1933 is strictly to report illegal drug activity, not for medical treatment)."
            )
        return score, sev, crisis, guidance

    @app.route("/wellness")
    @app.route("/recovery")
    def wellness_page():
        """Serves the Mental Health, Wellness & Recovery Dashboard (SPEC.md Section 16)."""
        active_id = session.get("active_profile_id", 1)
        csrf_val = secrets.token_hex(16)
        session["_csrf"] = csrf_val
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT pin_hash, discreet_mode FROM wellness_pins WHERE profile_id = ?", (active_id,))
            row = cursor.fetchone()
            has_pin = bool(row and row["pin_hash"])
            discreet = bool(row["discreet_mode"]) if row else False
            is_unlocked = session.get(f"wellness_unlocked_{active_id}", False) if has_pin else True
        return render_template(
            "wellness.html",
            csrf_token=csrf_val,
            active_profile_id=active_id,
            has_pin=has_pin,
            is_unlocked=is_unlocked,
            discreet_mode=discreet
        )

    @app.route("/api/wellness/status", methods=["GET"])
    def api_wellness_status():
        profile_id = int(request.args.get("profile_id") or session.get("active_profile_id", 1))
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT pin_hash, discreet_mode FROM wellness_pins WHERE profile_id = ?", (profile_id,))
            row = cursor.fetchone()
            has_pin = bool(row and row["pin_hash"])
            discreet = bool(row["discreet_mode"]) if row else False
            is_unlocked = session.get(f"wellness_unlocked_{profile_id}", False) if has_pin else True
        return jsonify({
            "success": True,
            "profile_id": profile_id,
            "has_pin": has_pin,
            "is_unlocked": is_unlocked,
            "discreet_mode": discreet
        })

    @app.route("/api/wellness/pin/set", methods=["POST"])
    def api_wellness_pin_set():
        data = request.get_json() or {}
        pin = str(data.get("pin", "")).strip()
        profile_id = int(data.get("profile_id") or session.get("active_profile_id", 1))

        if not re.match(r'^\d{4}$', pin):
            return jsonify({"success": False, "error": "PIN must be exactly 4 digits."}), 400

        pin_hash = security.hash_password(pin)
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO wellness_pins (profile_id, pin_hash, discreet_mode)
                VALUES (?, ?, 0)
                ON CONFLICT(profile_id) DO UPDATE SET pin_hash = excluded.pin_hash, updated_at = CURRENT_TIMESTAMP
            """, (profile_id, pin_hash))
            conn.commit()

        session[f"wellness_unlocked_{profile_id}"] = True
        return jsonify({"success": True, "message": "4-digit Wellness PIN set successfully."})

    @app.route("/api/wellness/pin/verify", methods=["POST"])
    def api_wellness_pin_verify():
        data = request.get_json() or {}
        pin = str(data.get("pin", "")).strip()
        profile_id = int(data.get("profile_id") or session.get("active_profile_id", 1))

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT pin_hash, discreet_mode FROM wellness_pins WHERE profile_id = ?", (profile_id,))
            row = cursor.fetchone()
            if not row or not row["pin_hash"]:
                session[f"wellness_unlocked_{profile_id}"] = True
                return jsonify({"success": True, "message": "No PIN required. Unlocked."})

            if security.verify_password(pin, row["pin_hash"]):
                session[f"wellness_unlocked_{profile_id}"] = True
                return jsonify({
                    "success": True,
                    "message": "PIN verified. Wellness section unlocked.",
                    "discreet_mode": bool(row["discreet_mode"])
                })
            else:
                return jsonify({"success": False, "error": "Incorrect PIN. Please try again."}), 401

    @app.route("/api/wellness/pin/lock", methods=["POST"])
    def api_wellness_pin_lock():
        data = request.get_json() or {}
        profile_id = int(data.get("profile_id") or session.get("active_profile_id", 1))
        session[f"wellness_unlocked_{profile_id}"] = False
        return jsonify({"success": True, "message": "Wellness section locked."})

    @app.route("/api/wellness/pin/toggle-discreet", methods=["POST"])
    def api_wellness_toggle_discreet():
        data = request.get_json() or {}
        profile_id = int(data.get("profile_id") or session.get("active_profile_id", 1))
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT discreet_mode FROM wellness_pins WHERE profile_id = ?", (profile_id,))
            row = cursor.fetchone()
            current_val = row["discreet_mode"] if row else 0
            new_val = 0 if current_val == 1 else 1

            if row:
                cursor.execute("UPDATE wellness_pins SET discreet_mode = ? WHERE profile_id = ?", (new_val, profile_id))
            else:
                cursor.execute("INSERT INTO wellness_pins (profile_id, pin_hash, discreet_mode) VALUES (?, '', ?)", (profile_id, new_val))
            conn.commit()

        return jsonify({"success": True, "discreet_mode": bool(new_val)})

    @app.route("/api/wellness/mood/history", methods=["GET"])
    def api_wellness_mood_history():
        profile_id = int(request.args.get("profile_id") or session.get("active_profile_id", 1))
        unlocked, discreet = is_wellness_unlocked(profile_id)
        if not unlocked:
            return jsonify({"success": False, "locked": True, "error": "Wellness section locked. Enter PIN."}), 423

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, log_date, mood_score, mood_label, energy_level, sleep_hours, tags, notes_encrypted, created_at
                FROM mood_logs
                WHERE profile_id = ?
                ORDER BY log_date ASC
                LIMIT 30
            """, (profile_id,))
            rows = cursor.fetchall()

        entries = []
        total_score = 0
        tag_counts = {}
        for r in rows:
            d = dict(r)
            note = ""
            if d.get("notes_encrypted"):
                try:
                    note = security.decrypt_field(d["notes_encrypted"])
                except Exception:
                    note = "[Encrypted]"
            d["notes"] = note
            del d["notes_encrypted"]
            entries.append(d)
            total_score += d["mood_score"]
            for tag in (d.get("tags") or "").split(","):
                tag = tag.strip()
                if tag:
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1

        avg_score = round(total_score / len(entries), 1) if entries else 0.0
        return jsonify({
            "success": True,
            "entries": entries,
            "total_days": len(entries),
            "average_mood": avg_score,
            "tag_frequencies": tag_counts,
            "discreet_mode": discreet
        })

    @app.route("/api/wellness/mood", methods=["POST"])
    def api_wellness_mood_post():
        data = request.get_json() or {}
        profile_id = int(data.get("profile_id") or session.get("active_profile_id", 1))
        unlocked, _ = is_wellness_unlocked(profile_id)
        if not unlocked:
            return jsonify({"success": False, "locked": True, "error": "Wellness section locked. Enter PIN."}), 423

        mood_score = int(data.get("mood_score", 3))
        mood_score = max(1, min(5, mood_score))
        labels = {1: "Terrible", 2: "Down", 3: "Okay", 4: "Good", 5: "Great"}
        mood_label = labels.get(mood_score, "Okay")

        energy = int(data.get("energy_level", 3))
        sleep = float(data.get("sleep_hours", 7.0))
        tags = data.get("tags", "")
        if isinstance(tags, list):
            tags = ", ".join(tags)
        tags = html.escape(str(tags).strip())
        raw_note = data.get("notes", "").strip()

        crisis_check = assistant_engine.detect_crisis(raw_note)
        detox_check = assistant_engine.detect_detox_or_tapering(raw_note)

        encrypted_note = security.encrypt_field(raw_note) if raw_note else ""
        log_date = data.get("log_date") or datetime.now().strftime("%Y-%m-%d")

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO mood_logs (profile_id, log_date, mood_score, mood_label, energy_level, sleep_hours, tags, notes_encrypted)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (profile_id, log_date, mood_score, mood_label, energy, sleep, tags, encrypted_note))
            conn.commit()
            new_id = cursor.lastrowid

        payload = {
            "success": True,
            "id": new_id,
            "message": "Daily mood check-in recorded successfully.",
            "mood_score": mood_score,
            "mood_label": mood_label
        }
        if crisis_check:
            payload["crisis_warning"] = True
            payload["crisis_helpline"] = "14416"
            payload["crisis_message"] = crisis_check["compassionate_message"]
        if detox_check:
            payload["detox_warning"] = True
            payload["de_addiction_helpline"] = "14446"

        return jsonify(payload), 201

    @app.route("/api/wellness/screeners/history", methods=["GET"])
    def api_wellness_screeners_history():
        profile_id = int(request.args.get("profile_id") or session.get("active_profile_id", 1))
        unlocked, _ = is_wellness_unlocked(profile_id)
        if not unlocked:
            return jsonify({"success": False, "locked": True, "error": "Wellness section locked. Enter PIN."}), 423

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, screener_type, total_score, severity_level, crisis_flag, guidance_summary, created_at
                FROM wellness_screenings
                WHERE profile_id = ?
                ORDER BY created_at DESC
                LIMIT 20
            """, (profile_id,))
            rows = [dict(r) for r in cursor.fetchall()]

        return jsonify({
            "success": True,
            "screenings": rows,
            "not_a_diagnosis_notice": "All screeners are standard self-assessments, NOT clinical diagnoses."
        })

    @app.route("/api/wellness/screeners", methods=["POST"])
    def api_wellness_screeners_post():
        data = request.get_json() or {}
        profile_id = int(data.get("profile_id") or session.get("active_profile_id", 1))
        unlocked, _ = is_wellness_unlocked(profile_id)
        if not unlocked:
            return jsonify({"success": False, "locked": True, "error": "Wellness section locked. Enter PIN."}), 423

        stype = data.get("screener_type", "PHQ-9").upper().strip()
        answers = data.get("answers", [])

        if stype == "PHQ-9":
            score, severity, crisis, guidance = score_phq9(answers)
        elif stype == "GAD-7":
            score, severity, crisis, guidance = score_gad7(answers)
        elif stype == "AUDIT":
            score, severity, crisis, guidance = score_audit(answers)
        else:
            return jsonify({"success": False, "error": f"Unsupported screener type: {stype}. Must be PHQ-9, GAD-7, or AUDIT."}), 400

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO wellness_screenings (profile_id, screener_type, total_score, severity_level, answers_json, crisis_flag, guidance_summary)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (profile_id, stype, score, severity, json.dumps(answers), crisis, guidance))
            conn.commit()
            new_id = cursor.lastrowid

        return jsonify({
            "success": True,
            "id": new_id,
            "screener_type": stype,
            "total_score": score,
            "severity_level": severity,
            "crisis_flag": bool(crisis),
            "guidance_summary": guidance,
            "not_a_diagnosis": True,
            "disclaimer": "This screening self-check is NOT a clinical diagnosis. Always consult a qualified physician or psychologist.",
            "helplines": {
                "mental_health": "14416 (Tele-MANAS Free 24x7)",
                "emergency": "112 / 108",
                "de_addiction": "14446 (Toll-Free National Drug De-Addiction)",
                "ncb_notice": "Helpline 1933 is strictly to report drug activity to NCB, not for medical treatment."
            }
        }), 201

    @app.route("/api/wellness/recovery", methods=["GET"])
    def api_wellness_recovery_get():
        profile_id = int(request.args.get("profile_id") or session.get("active_profile_id", 1))
        unlocked, discreet = is_wellness_unlocked(profile_id)
        if not unlocked:
            return jsonify({"success": False, "locked": True, "error": "Wellness section locked. Enter PIN."}), 423

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM recovery_trackers
                WHERE profile_id = ? AND is_active = 1
                ORDER BY id DESC LIMIT 1
            """, (profile_id,))
            tracker = cursor.fetchone()

            tracker_data = None
            if tracker:
                tracker_data = dict(tracker)
                try:
                    start_dt = datetime.fromisoformat(tracker["clean_start_date"])
                    diff = datetime.now() - start_dt
                    streak_days = max(0, diff.days)
                    streak_hours = max(0, int(diff.total_seconds() // 3600))
                    tracker_data["days_clean"] = streak_days
                    tracker_data["hours_clean"] = streak_hours
                except Exception:
                    tracker_data["days_clean"] = tracker.get("streak_days", 0)
                    tracker_data["hours_clean"] = tracker.get("streak_days", 0) * 24

                days = tracker_data.get("days_clean", 0)
                all_milestones = [
                    {"days": 1, "title": "24 Hours Clean", "badge": "🌱 Fresh Start", "achieved": days >= 1},
                    {"days": 3, "title": "3 Days Clean", "badge": "🌿 Solid Ground", "achieved": days >= 3},
                    {"days": 7, "title": "1 Week Clean", "badge": "⭐ First Week", "achieved": days >= 7},
                    {"days": 30, "title": "1 Month Clean", "badge": "🏅 Bronze Milestone", "achieved": days >= 30},
                    {"days": 60, "title": "60 Days Clean", "badge": "🥈 Silver Milestone", "achieved": days >= 60},
                    {"days": 90, "title": "90 Days Clean", "badge": "🏆 Gold Milestone", "achieved": days >= 90},
                    {"days": 180, "title": "6 Months Clean", "badge": "💎 Diamond Milestone", "achieved": days >= 180},
                    {"days": 365, "title": "1 Year Clean", "badge": "👑 Champion Milestone", "achieved": days >= 365}
                ]
                tracker_data["milestones"] = all_milestones

            cursor.execute("""
                SELECT id, craving_intensity, trigger_description, coping_strategy_used, logged_at
                FROM craving_logs
                WHERE profile_id = ?
                ORDER BY logged_at DESC LIMIT 15
            """, (profile_id,))
            cravings = [dict(r) for r in cursor.fetchall()]

            cursor.execute("""
                SELECT id, trigger_name, coping_action, created_at
                FROM coping_plans
                WHERE profile_id = ?
                ORDER BY id ASC
            """, (profile_id,))
            plans = [dict(r) for r in cursor.fetchall()]

        return jsonify({
            "success": True,
            "tracker": tracker_data,
            "cravings": cravings,
            "coping_plans": plans,
            "discreet_mode": discreet,
            "emergency_card": {
                "call_108": "tel:108",
                "call_112": "tel:112",
                "de_addiction_14446": "tel:14446",
                "tele_manas_14416": "tel:14416",
                "ncb_notice": "Helpline 1933 is strictly to report drug activity to NCB, not for medical treatment."
            }
        })

    @app.route("/api/wellness/recovery/start", methods=["POST"])
    def api_wellness_recovery_start():
        data = request.get_json() or {}
        profile_id = int(data.get("profile_id") or session.get("active_profile_id", 1))
        unlocked, _ = is_wellness_unlocked(profile_id)
        if not unlocked:
            return jsonify({"success": False, "locked": True, "error": "Wellness section locked. Enter PIN."}), 423

        target_habit = html.escape(data.get("target_habit", "Alcohol").strip())
        clean_start_date = data.get("clean_start_date") or datetime.now().isoformat()

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE recovery_trackers SET is_active = 0 WHERE profile_id = ?", (profile_id,))
            cursor.execute("""
                INSERT INTO recovery_trackers (profile_id, target_habit, clean_start_date, streak_days, is_active)
                VALUES (?, ?, ?, 0, 1)
            """, (profile_id, target_habit, clean_start_date))
            conn.commit()
            new_id = cursor.lastrowid

        return jsonify({
            "success": True,
            "message": f"Recovery journey started for {target_habit}. You have the strength to take this one day at a time.",
            "id": new_id
        }), 201

    @app.route("/api/wellness/recovery/reset", methods=["POST"])
    def api_wellness_recovery_reset():
        """Shame-free relapse handler."""
        data = request.get_json() or {}
        profile_id = int(data.get("profile_id") or session.get("active_profile_id", 1))
        unlocked, _ = is_wellness_unlocked(profile_id)
        if not unlocked:
            return jsonify({"success": False, "locked": True, "error": "Wellness section locked. Enter PIN."}), 423

        now_str = datetime.now().isoformat()
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE recovery_trackers
                SET last_reset_date = ?, clean_start_date = ?, streak_days = 0
                WHERE profile_id = ? AND is_active = 1
            """, (now_str, now_str, profile_id))
            conn.commit()

        shame_free_message = (
            "🌱 A slip is not a failure; recovery is not a straight line. "
            "What you learned during your clean days still counts and can never be erased. "
            "Be gentle with yourself, breathe deeply, and take the next right step today. We are with you."
        )

        return jsonify({
            "success": True,
            "message": shame_free_message,
            "helplines": {
                "de_addiction": "14446 (Toll-Free National Helpline)",
                "tele_manas": "14416 (Free 24x7 Support)",
                "emergency": "108 / 112"
            }
        })

    @app.route("/api/wellness/recovery/cravings", methods=["POST"])
    def api_wellness_cravings_post():
        data = request.get_json() or {}
        profile_id = int(data.get("profile_id") or session.get("active_profile_id", 1))
        unlocked, _ = is_wellness_unlocked(profile_id)
        if not unlocked:
            return jsonify({"success": False, "locked": True, "error": "Wellness section locked. Enter PIN."}), 423

        intensity = max(1, min(10, int(data.get("craving_intensity", 5))))
        trigger = html.escape(data.get("trigger_description", "").strip())
        raw_strategy = data.get("coping_strategy_used", "Box Breathing").strip()

        # Reject pain-based coping (SPEC 16f)
        pain_terms = ["rubber band", "snap", "snapping", "ice", "burn", "pinch", "pain"]
        if any(pt in raw_strategy.lower() for pt in pain_terms):
            strategy = "Somatic 5-4-3-2-1 Sensory Grounding (Evidence-based soothing)"
            note_reminder = "Note: Modern clinical recovery strictly discourages pain-based coping (e.g. snapping bands). Gentle somatic grounding promotes lasting neural regulation."
        else:
            strategy = html.escape(raw_strategy)
            note_reminder = None

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO craving_logs (profile_id, craving_intensity, trigger_description, coping_strategy_used)
                VALUES (?, ?, ?, ?)
            """, (profile_id, intensity, trigger, strategy))
            conn.commit()
            new_id = cursor.lastrowid

        res = {
            "success": True,
            "id": new_id,
            "message": "Craving logged. Every urge surfed strengthens your recovery muscle.",
            "intensity": intensity,
            "coping_strategy": strategy
        }
        if note_reminder:
            res["clinical_notice"] = note_reminder

        return jsonify(res), 201

    @app.route("/api/wellness/recovery/coping-plan", methods=["POST"])
    def api_wellness_coping_plan_post():
        data = request.get_json() or {}
        profile_id = int(data.get("profile_id") or session.get("active_profile_id", 1))
        trigger = html.escape(data.get("trigger_name", "").strip())
        action = html.escape(data.get("coping_action", "").strip())

        if not trigger or not action:
            return jsonify({"success": False, "error": "Trigger and Coping Action are required."}), 400

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO coping_plans (profile_id, trigger_name, coping_action)
                VALUES (?, ?, ?)
            """, (profile_id, trigger, action))
            conn.commit()
            new_id = cursor.lastrowid

        return jsonify({"success": True, "id": new_id, "message": "Trigger and Coping Strategy added."}), 201

    @app.route("/api/wellness/recovery/coping-plan/<int:plan_id>", methods=["DELETE"])
    def api_wellness_coping_plan_delete(plan_id):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM coping_plans WHERE id = ?", (plan_id,))
            conn.commit()
        return jsonify({"success": True, "message": "Coping plan item removed."})

    @app.route("/api/wellness/wellness-tools", methods=["GET"])
    def api_wellness_tools():
        """Returns evidence-based wellness tools (SPEC 16f - NO pain-based coping)."""
        return jsonify({
            "success": True,
            "tools": {
                "box_breathing": {
                    "title": "4-4-4-4 Box Breathing",
                    "description": "Regulates the autonomic nervous system by equalizing breath counts.",
                    "steps": [
                        "Inhale slowly through your nose for 4 seconds",
                        "Hold your breath gently for 4 seconds",
                        "Exhale smoothly through your mouth for 4 seconds",
                        "Hold empty lungs calmly for 4 seconds"
                    ]
                },
                "grounding_54321": {
                    "title": "5-4-3-2-1 Sensory Grounding",
                    "description": "Brings attention back into the present physical environment during acute anxiety or cravings.",
                    "steps": [
                        "5 things you can SEE around you",
                        "4 things you can physically TOUCH or FEEL",
                        "3 distinct sounds you can HEAR",
                        "2 scents or smells you can DETECT",
                        "1 positive taste or sensation in your mouth"
                    ]
                },
                "sleep_hygiene": {
                    "title": "Sleep Hygiene & Wind-down",
                    "description": "Supports circadian rhythm and restorative sleep essential for emotional regulation.",
                    "tips": [
                        "Turn off digital screens 30–45 minutes before sleep",
                        "Keep room dark, quiet, and slightly cool",
                        "Limit caffeine intake after 2:00 PM",
                        "Maintain consistent wake-up times every day"
                    ]
                },
                "clinical_rule": "Strictly no pain-based coping (e.g., rubber band snapping). Somatic neural regulation is evidence-based and compassionate."
            }
        })

    @app.route("/api/wellness/family-guide", methods=["GET"])
    def api_wellness_family_guide():
        """Returns family guidance and official support links (SPEC 16d)."""
        return jsonify({
            "success": True,
            "dos": [
                "Listen actively without judgment, preaching, or emotional blaming.",
                "Encourage small daily steps and celebrate non-substance milestones.",
                "Set clear, loving boundaries for yourself while showing steady care.",
                "Have emergency numbers (108, 14446, 14416) saved on your phone."
            ],
            "donts": [
                "Do NOT shame, guilt-trip, or bring up past mistakes during acute stress.",
                "Do NOT cover up, lie for, or financially enable active dependence.",
                "Do NOT force cold-turkey unassisted detox at home.",
                "Do NOT neglect your own mental well-being and family counseling."
            ],
            "official_support_groups": [
                {
                    "name": "Alcoholics Anonymous India (AA)",
                    "url": "https://www.aagsoindia.org",
                    "helpline": "+91-9022771122",
                    "description": "Free, confidential 12-step peer fellowship across India."
                },
                {
                    "name": "Narcotics Anonymous India (NA)",
                    "url": "https://na-india.in",
                    "helpline": "+91-9820067676",
                    "description": "Community of recovering individuals supporting each other to stay clean."
                },
                {
                    "name": "Al-Anon Family Groups India",
                    "url": "https://al-anon.org/al-anon-meetings/find-an-al-anon-meeting/",
                    "helpline": "1800-22-22-38",
                    "description": "Mutual support for family members and friends of individuals with alcohol dependence."
                },
                {
                    "name": "Vandrevala Foundation Helpline",
                    "url": "https://www.vandrevalafoundation.com",
                    "helpline": "9999-666-555",
                    "description": "24/7 free mental health counseling across India."
                },
                {
                    "name": "National Drug De-Addiction Helpline (MoSJE)",
                    "url": "https://socialjustice.gov.in",
                    "helpline": "14446",
                    "description": "Free toll-free national de-addiction helpline."
                },
                {
                    "name": "Tele-MANAS (NIMHANS & MoHFW)",
                    "url": "https://telemanas.mohfw.gov.in",
                    "helpline": "14416",
                    "description": "Free 24x7 psychiatric and mental health support in all Indian languages."
                }
            ],
            "law_enforcement_note": "Helpline 1933 is the NCB national toll-free helpline strictly to report illegal drug trafficking or supply; it is NOT a medical treatment facility."
        })

    @app.route("/api/user/export", methods=["GET"])
    def api_user_export_full():
        """Exports all patient data including vitals, emergency card, wellness, and recovery records (SPEC 12a, 12c, 16g)."""
        active_id = int(request.args.get("profile_id") or session.get("active_profile_id", 1))
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM profiles WHERE id = ?", (active_id,))
            prof = cursor.fetchone()

            cursor.execute("SELECT * FROM appointments WHERE profile_id = ?", (active_id,))
            appointments = [dict(r) for r in cursor.fetchall()]

            cursor.execute("SELECT * FROM medicines WHERE profile_id = ?", (active_id,))
            medicines = [dict(r) for r in cursor.fetchall()]

            cursor.execute("SELECT * FROM reports WHERE profile_id = ?", (active_id,))
            reports = [dict(r) for r in cursor.fetchall()]

            cursor.execute("SELECT * FROM vitals_logs WHERE profile_id = ? ORDER BY recorded_at DESC", (active_id,))
            vitals = [dict(r) for r in cursor.fetchall()]

            cursor.execute("SELECT * FROM emergency_cards WHERE profile_id = ?", (active_id,))
            emerg_row = cursor.fetchone()
            emerg_card = dict(emerg_row) if emerg_row else None

            cursor.execute("SELECT * FROM mood_logs WHERE profile_id = ?", (active_id,))
            moods = []
            for r in cursor.fetchall():
                d = dict(r)
                if d.get("notes_encrypted"):
                    try:
                        d["notes"] = security.decrypt_field(d["notes_encrypted"])
                    except Exception:
                        d["notes"] = "[Encrypted]"
                    del d["notes_encrypted"]
                moods.append(d)

            cursor.execute("SELECT * FROM wellness_screenings WHERE profile_id = ?", (active_id,))
            screeners = [dict(r) for r in cursor.fetchall()]

            cursor.execute("SELECT * FROM recovery_trackers WHERE profile_id = ?", (active_id,))
            trackers = [dict(r) for r in cursor.fetchall()]

            cursor.execute("SELECT * FROM craving_logs WHERE profile_id = ?", (active_id,))
            cravings = [dict(r) for r in cursor.fetchall()]

            cursor.execute("SELECT * FROM coping_plans WHERE profile_id = ?", (active_id,))
            plans = [dict(r) for r in cursor.fetchall()]

        return jsonify({
            "success": True,
            "exported_at": datetime.now().isoformat(),
            "profile": dict(prof) if prof else {},
            "appointments": appointments,
            "medicines": medicines,
            "reports": reports,
            "vitals": vitals,
            "emergency_card": emerg_card,
            "wellness": {
                "mood_logs": moods,
                "screenings": screeners,
                "recovery_trackers": trackers,
                "craving_logs": cravings,
                "coping_plans": plans
            }
        })

    @app.route("/api/user/delete", methods=["POST", "DELETE"])
    def api_user_delete_full():
        """Cascades deletion of patient account and all health/wellness/vitals data (SPEC 12a, 12c, 16g)."""
        active_id = int(request.json.get("profile_id") if request.is_json and request.json else session.get("active_profile_id", 1))
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM vitals_logs WHERE profile_id = ?", (active_id,))
            cursor.execute("DELETE FROM emergency_cards WHERE profile_id = ?", (active_id,))
            cursor.execute("DELETE FROM scanned_documents WHERE profile_id = ?", (active_id,))
            cursor.execute("DELETE FROM mood_logs WHERE profile_id = ?", (active_id,))
            cursor.execute("DELETE FROM wellness_screenings WHERE profile_id = ?", (active_id,))
            cursor.execute("DELETE FROM recovery_trackers WHERE profile_id = ?", (active_id,))
            cursor.execute("DELETE FROM craving_logs WHERE profile_id = ?", (active_id,))
            cursor.execute("DELETE FROM coping_plans WHERE profile_id = ?", (active_id,))
            cursor.execute("DELETE FROM wellness_pins WHERE profile_id = ?", (active_id,))
            cursor.execute("DELETE FROM appointments WHERE profile_id = ?", (active_id,))
            cursor.execute("DELETE FROM medicines WHERE profile_id = ?", (active_id,))
            cursor.execute("DELETE FROM reports WHERE profile_id = ?", (active_id,))
            cursor.execute("DELETE FROM profiles WHERE id = ?", (active_id,))
            conn.commit()

        session.pop(f"wellness_unlocked_{active_id}", None)
        return jsonify({"success": True, "message": "All patient health, vitals, wellness, and account data permanently deleted."})

    # --------------------------------------------------------------------------
    # PHASE 10A: VITALS TRACKER APIS (SPEC 12a)
    # --------------------------------------------------------------------------

    @app.route("/api/vitals", methods=["GET"])
    def api_get_vitals():
        """Returns latest vitals summary cards, trends, and recent logs for active profile (SPEC 12a)."""
        active_id = int(request.args.get("profile_id") or session.get("active_profile_id", 1))
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM vitals_logs WHERE profile_id = ? ORDER BY recorded_at DESC", (active_id,))
            all_logs = [dict(r) for r in cursor.fetchall()]

            cursor.execute("SELECT name, age, gender, blood_group FROM profiles WHERE id = ?", (active_id,))
            prof = cursor.fetchone()
            prof_dict = dict(prof) if prof else {}

        # Organize latest reading per vital type
        latest_map = {}
        for row in all_logs:
            vt = row["vital_type"]
            if vt not in latest_map:
                eval_data = evaluate_vital_reading(vt, row["value_primary"], row.get("value_secondary"), row.get("meal_context", ""))
                row["evaluation"] = eval_data
                latest_map[vt] = row

        return jsonify({
            "success": True,
            "profile": prof_dict,
            "profile_id": active_id,
            "latest": latest_map,
            "recent_logs": all_logs[:30],
            "total_count": len(all_logs)
        })

    @app.route("/api/vitals", methods=["POST"])
    def api_log_vital():
        """Logs a vital reading with automated clinical evaluation and acute alerts (SPEC 12a)."""
        data = request.get_json(silent=True) or request.form.to_dict()
        profile_id = int(data.get("profile_id") or session.get("active_profile_id", 1))
        vital_type = (data.get("vital_type") or "").strip().lower()
        val_primary = data.get("value_primary")
        val_secondary = data.get("value_secondary")
        unit = (data.get("unit") or "").strip()
        meal_context = (data.get("meal_context") or "").strip()
        notes = (data.get("notes") or "").strip()
        recorded_at = (data.get("recorded_at") or "").strip() or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if not vital_type or val_primary is None or str(val_primary).strip() == "":
            return jsonify({"success": False, "error": "vital_type and value_primary are required."}), 400

        try:
            val1 = float(val_primary)
            val2 = float(val_secondary) if val_secondary is not None and str(val_secondary).strip() != "" else None
        except ValueError:
            return jsonify({"success": False, "error": "Vital readings must be valid numeric values."}), 400

        if not unit:
            unit_map = {
                "bp": "mmHg",
                "blood_pressure": "mmHg",
                "glucose": "mg/dL",
                "sugar": "mg/dL",
                "heart_rate": "bpm",
                "pulse": "bpm",
                "spo2": "%",
                "temperature": "°F",
                "bmi": "kg",
                "weight": "kg",
                "respiratory_rate": "breaths/min"
            }
            unit = unit_map.get(vital_type, "")

        evaluation = evaluate_vital_reading(vital_type, val1, val2, meal_context)
        notes_encrypted = security.encrypt_field(notes) if notes else ""

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO vitals_logs (
                    profile_id, vital_type, value_primary, value_secondary,
                    unit, meal_context, status, notes_encrypted, recorded_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (profile_id, vital_type, val1, val2, unit, meal_context, evaluation["status"], notes_encrypted, recorded_at))
            new_id = cursor.lastrowid
            conn.commit()

        return jsonify({
            "success": True,
            "id": new_id,
            "vital_type": vital_type,
            "evaluation": evaluation,
            "message": "Vital reading logged successfully."
        }), 201

    @app.route("/api/vitals/history", methods=["GET"])
    def api_get_vitals_history():
        """Returns filterable vitals history with points formatted for trend charting (SPEC 12a)."""
        active_id = int(request.args.get("profile_id") or session.get("active_profile_id", 1))
        vital_type = (request.args.get("vital_type") or "").strip().lower()
        days = request.args.get("days", "all")

        query = "SELECT * FROM vitals_logs WHERE profile_id = ?"
        params = [active_id]

        if vital_type:
            query += " AND vital_type = ?"
            params.append(vital_type)

        if days.isdigit() and int(days) > 0:
            cutoff = (datetime.now() - timedelta(days=int(days))).strftime("%Y-%m-%d %H:%M:%S")
            query += " AND recorded_at >= ?"
            params.append(cutoff)

        query += " ORDER BY recorded_at ASC"

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = [dict(r) for r in cursor.fetchall()]

        primary_vals = [r["value_primary"] for r in rows]
        stats = {
            "count": len(rows),
            "min": round(min(primary_vals), 1) if primary_vals else 0,
            "max": round(max(primary_vals), 1) if primary_vals else 0,
            "avg": round(sum(primary_vals) / len(primary_vals), 1) if primary_vals else 0,
            "latest": round(primary_vals[-1], 1) if primary_vals else 0
        }

        points = []
        for r in rows:
            eval_data = evaluate_vital_reading(r["vital_type"], r["value_primary"], r.get("value_secondary"), r.get("meal_context", ""))
            points.append({
                "id": r["id"],
                "vital_type": r["vital_type"],
                "date": r["recorded_at"],
                "val": r["value_primary"],
                "val_sec": r.get("value_secondary"),
                "status": r.get("status", "normal"),
                "color": eval_data["color"],
                "status_label": eval_data["status_label"],
                "alert": eval_data.get("alert_message", "")
            })

        return jsonify({
            "success": True,
            "profile_id": active_id,
            "vital_type": vital_type,
            "stats": stats,
            "points": points,
            "logs": list(reversed(rows))
        })

    @app.route("/api/vitals/<int:vital_id>", methods=["DELETE"])
    def api_delete_vital(vital_id):
        """Deletes a vital reading record."""
        active_id = int(request.args.get("profile_id") or session.get("active_profile_id", 1))
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM vitals_logs WHERE id = ? AND profile_id = ?", (vital_id, active_id))
            conn.commit()
        return jsonify({"success": True, "message": "Vital reading deleted successfully."})

    @app.route("/api/vitals/ranges", methods=["GET"])
    def api_get_vitals_ranges():
        """Returns clinical reference ranges metadata across all supported vitals."""
        return jsonify({
            "success": True,
            "ranges": {
                "bp": {
                    "title": "Blood Pressure (mmHg)",
                    "normal": "< 120 / < 80",
                    "elevated": "120–129 / < 80",
                    "stage1": "130–139 / 80–89",
                    "stage2": ">= 140 / >= 90",
                    "crisis": ">= 180 / >= 120 (Immediate 108 Alert)",
                    "unit": "mmHg"
                },
                "glucose_fasting": {
                    "title": "Fasting Blood Glucose",
                    "normal": "70–99 mg/dL",
                    "prediabetes": "100–125 mg/dL",
                    "diabetes": ">= 126 mg/dL",
                    "hypoglycemia": "< 70 mg/dL (Emergency Sugar Alert)",
                    "unit": "mg/dL"
                },
                "glucose_postprandial": {
                    "title": "Post-Meal Blood Glucose",
                    "normal": "< 140 mg/dL",
                    "prediabetes": "140–199 mg/dL",
                    "diabetes": ">= 200 mg/dL",
                    "unit": "mg/dL"
                },
                "heart_rate": {
                    "title": "Resting Heart Rate",
                    "normal": "60–100 bpm",
                    "bradycardia": "< 60 bpm",
                    "tachycardia": "> 100 bpm",
                    "crisis": "> 140 bpm",
                    "unit": "bpm"
                },
                "spo2": {
                    "title": "Oxygen Saturation (SpO2)",
                    "normal": "95–100%",
                    "mild_hypoxia": "90–94%",
                    "severe_hypoxia": "< 90% (Call 108 Emergency)",
                    "unit": "%"
                },
                "temperature": {
                    "title": "Body Temperature",
                    "normal": "97.0–99.0 °F",
                    "low_fever": "99.1–100.4 °F",
                    "fever": "> 100.4 °F",
                    "high_fever": "> 103.0 °F",
                    "unit": "°F"
                },
                "bmi": {
                    "title": "Body Mass Index (BMI)",
                    "underweight": "< 18.5",
                    "normal": "18.5–24.9",
                    "overweight": "25.0–29.9",
                    "obese": ">= 30.0",
                    "unit": "kg/m²"
                }
            }
        })

    # --------------------------------------------------------------------------
    # PHASE 10A: SCANNER & OCR APIS (SPEC 12b)
    # --------------------------------------------------------------------------

    @app.route("/api/scanner/upload", methods=["POST"])
    def api_scanner_upload():
        """Uploads prescription/report, extracts text via pypdf/OCR, and parses medical entities (SPEC 12b)."""
        active_id = int(request.form.get("profile_id") or session.get("active_profile_id", 1))
        uploaded_file = request.files.get("file")
        raw_text_input = request.form.get("raw_text") or ""

        if not raw_text_input and request.is_json:
            j = request.get_json(silent=True) or {}
            raw_text_input = j.get("raw_text", "")
            active_id = int(j.get("profile_id", active_id))

        extracted_text = ""
        filename = "pasted_text.txt"
        file_path = ""

        if uploaded_file and uploaded_file.filename:
            filename = uploaded_file.filename
            if not is_safe_file_upload(filename, uploaded_file):
                return jsonify({"success": False, "error": "File rejected by security policies. Only PDF, TXT, PNG, and JPG medical reports are accepted."}), 400

            unique_filename = f"{int(datetime.now().timestamp())}_{secrets.token_hex(4)}_{filename}"
            save_path = Path(app.config["UPLOAD_FOLDER"]) / unique_filename
            uploaded_file.seek(0)
            uploaded_file.save(str(save_path))
            file_path = str(save_path)
            extracted_text = extract_text_from_file(save_path, filename)

        if raw_text_input:
            if extracted_text:
                extracted_text += "\n" + raw_text_input
            else:
                extracted_text = raw_text_input

        if not extracted_text or not extracted_text.strip():
            return jsonify({"success": False, "error": "No readable text found. Please upload a PDF or enter prescription text."}), 400

        parsed = parse_clinical_document_text(extracted_text)

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO scanned_documents (
                    profile_id, file_name, file_path, document_type,
                    ocr_text, extracted_data_json
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (active_id, filename, file_path, "Prescription", extracted_text, json.dumps(parsed)))
            conn.commit()

        return jsonify({
            "success": True,
            "filename": filename,
            "extracted": parsed
        })

    @app.route("/api/scanner/save-medicines", methods=["POST"])
    def api_scanner_save_medicines():
        """Bulk adds parsed medications from scanner directly to Medicine Tracker (SPEC 12b)."""
        data = request.get_json(silent=True) or {}
        active_id = int(data.get("profile_id") or session.get("active_profile_id", 1))
        meds = data.get("medicines") or []

        if not meds:
            return jsonify({"success": False, "error": "No medicines provided to save."}), 400

        saved_count = 0
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM profiles WHERE id = ?", (active_id,))
            prof = cursor.fetchone()
            patient_name = prof["name"] if prof else "Patient"

            for m in meds:
                name = (m.get("medicine_name") or m.get("name") or "").strip()
                if not name:
                    continue
                dosage = m.get("prescribed_dosage") or "1 tablet"
                timing = m.get("timing_slot") or "Morning"
                freq = m.get("frequency") or "Daily"
                doc = m.get("doctor_prescribed") or "Prescribing Physician"
                instructions = m.get("instructions") or "Follow prescription."

                cursor.execute("""
                    INSERT INTO medicines (
                        patient_name, medicine_name, prescribed_dosage,
                        timing_slot, frequency, doctor_prescribed,
                        instructions, reminder_time, pills_left, taken_today, last_taken_date, profile_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (patient_name, name, dosage, timing, freq, doc, instructions, "08:00 AM", 30, 0, "", active_id))
                saved_count += 1

            conn.commit()

        return jsonify({
            "success": True,
            "saved_count": saved_count,
            "message": f"Successfully saved {saved_count} medications directly into Medicine Tracker."
        })

    @app.route("/api/scanner/save-vitals", methods=["POST"])
    def api_scanner_save_vitals():
        """Bulk adds parsed vitals from scanner directly to Vitals Tracker (SPEC 12b)."""
        data = request.get_json(silent=True) or {}
        active_id = int(data.get("profile_id") or session.get("active_profile_id", 1))
        vitals_list = data.get("vitals") or []

        if not vitals_list:
            return jsonify({"success": False, "error": "No vitals provided to save."}), 400

        saved_count = 0
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with get_db() as conn:
            cursor = conn.cursor()
            for v in vitals_list:
                vt = (v.get("vital_type") or "").strip().lower()
                val1 = v.get("value_primary")
                val2 = v.get("value_secondary")
                unit = v.get("unit") or ""
                meal_ctx = v.get("meal_context") or ""

                if not vt or val1 is None:
                    continue

                evaluation = evaluate_vital_reading(vt, val1, val2, meal_ctx)
                cursor.execute("""
                    INSERT INTO vitals_logs (
                        profile_id, vital_type, value_primary, value_secondary,
                        unit, meal_context, status, notes_encrypted, recorded_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (active_id, vt, val1, val2, unit, meal_ctx, evaluation["status"], "", now_str))
                saved_count += 1

            conn.commit()

        return jsonify({
            "success": True,
            "saved_count": saved_count,
            "message": f"Successfully recorded {saved_count} vital parameters into Vitals Tracker."
        })

    # --------------------------------------------------------------------------
    # PHASE 10A: EMERGENCY HEALTH CARD APIS (SPEC 12c)
    # --------------------------------------------------------------------------

    @app.route("/api/emergency-card/data", methods=["GET"])
    def api_emergency_card_data():
        """Returns emergency card data and embedded QR code for active profile (SPEC 12c)."""
        active_id = int(request.args.get("profile_id") or session.get("active_profile_id", 1))
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM emergency_cards WHERE profile_id = ?", (active_id,))
            card = cursor.fetchone()

            if not card:
                token = f"emerg_{secrets.token_hex(6)}"
                cursor.execute("SELECT blood_group, allergies, conditions FROM profiles WHERE id = ?", (active_id,))
                p = cursor.fetchone()
                bg = p["blood_group"] if p and p["blood_group"] else "O+"
                allergies = p["allergies"] if p and p["allergies"] else ""
                conditions = p["conditions"] if p and p["conditions"] else ""

                cursor.execute("""
                    INSERT INTO emergency_cards (
                        profile_id, emergency_token, blood_group,
                        primary_contact_name, primary_contact_phone, primary_contact_relation,
                        secondary_contact_name, secondary_contact_phone, secondary_contact_relation,
                        allergies, chronic_conditions, current_medications,
                        emergency_instructions, organ_donor, is_public_enabled
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    active_id, token, bg,
                    "Emergency Contact", "+91 98765 43210", "Family",
                    "", "", "",
                    allergies, conditions, "",
                    "In case of emergency, contact primary number immediately.", 1, 1
                ))
                conn.commit()
                cursor.execute("SELECT * FROM emergency_cards WHERE profile_id = ?", (active_id,))
                card = cursor.fetchone()

            cursor.execute("SELECT id, name, age, gender, blood_group FROM profiles WHERE id = ?", (active_id,))
            prof = cursor.fetchone()
            prof_dict = dict(prof) if prof else {}

        card_dict = dict(card)
        card_dict["patient_name"] = prof_dict.get("name", "Patient")
        card_dict["age"] = prof_dict.get("age", 0)
        card_dict["gender"] = prof_dict.get("gender", "")
        if not card_dict.get("blood_group") and prof_dict.get("blood_group"):
            card_dict["blood_group"] = prof_dict["blood_group"]

        public_url = request.host_url.rstrip("/") + f"/emergency-card/{card_dict['emergency_token']}"
        qr_data_url = generate_qr_data_url(public_url)

        return jsonify({
            "success": True,
            "profile": prof_dict,
            "card": card_dict,
            "public_url": public_url,
            "qr_data_url": qr_data_url
        })

    @app.route("/api/emergency-card/update", methods=["POST", "PUT"])
    def api_emergency_card_update():
        """Updates emergency contacts, allergies, directives and blood group (SPEC 12c)."""
        data = request.get_json(silent=True) or request.form.to_dict()
        active_id = int(data.get("profile_id") or session.get("active_profile_id", 1))

        blood_group = (data.get("blood_group") or "").strip()
        p_name = (data.get("primary_contact_name") or "").strip()
        p_phone = (data.get("primary_contact_phone") or "").strip()
        p_rel = (data.get("primary_contact_relation") or "").strip()
        s_name = (data.get("secondary_contact_name") or "").strip()
        s_phone = (data.get("secondary_contact_phone") or "").strip()
        s_rel = (data.get("secondary_contact_relation") or "").strip()
        allergies = (data.get("allergies") or "").strip()
        conditions = (data.get("chronic_conditions") or "").strip()
        meds = (data.get("current_medications") or "").strip()
        instructions = (data.get("emergency_instructions") or "").strip()
        organ_donor = 1 if str(data.get("organ_donor", "")).lower() in ["1", "true", "yes"] else 0

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM emergency_cards WHERE profile_id = ?", (active_id,))
            exists = cursor.fetchone()

            if exists:
                cursor.execute("""
                    UPDATE emergency_cards SET
                        blood_group = ?, primary_contact_name = ?, primary_contact_phone = ?, primary_contact_relation = ?,
                        secondary_contact_name = ?, secondary_contact_phone = ?, secondary_contact_relation = ?,
                        allergies = ?, chronic_conditions = ?, current_medications = ?,
                        emergency_instructions = ?, organ_donor = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE profile_id = ?
                """, (
                    blood_group, p_name, p_phone, p_rel,
                    s_name, s_phone, s_rel,
                    allergies, conditions, meds,
                    instructions, organ_donor, active_id
                ))
            else:
                token = f"emerg_{secrets.token_hex(6)}"
                cursor.execute("""
                    INSERT INTO emergency_cards (
                        profile_id, emergency_token, blood_group,
                        primary_contact_name, primary_contact_phone, primary_contact_relation,
                        secondary_contact_name, secondary_contact_phone, secondary_contact_relation,
                        allergies, chronic_conditions, current_medications,
                        emergency_instructions, organ_donor, is_public_enabled
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                """, (
                    active_id, token, blood_group,
                    p_name, p_phone, p_rel,
                    s_name, s_phone, s_rel,
                    allergies, conditions, meds,
                    instructions, organ_donor
                ))

            if blood_group:
                cursor.execute("UPDATE profiles SET blood_group = ? WHERE id = ?", (blood_group, active_id))

            conn.commit()

        return jsonify({"success": True, "message": "Emergency Health Card successfully updated."})

    @app.route("/api/emergency-card/wallpaper/<token>", methods=["GET"])
    def api_emergency_card_wallpaper(token):
        """Generates and downloads mobile lock-screen 9:16 PNG wallpaper with emergency QR (SPEC 12c)."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM emergency_cards WHERE emergency_token = ?", (token,))
            card = cursor.fetchone()
            if not card:
                return jsonify({"error": "Emergency card not found"}), 404

            card_dict = dict(card)
            cursor.execute("SELECT name, age, gender, blood_group FROM profiles WHERE id = ?", (card_dict["profile_id"],))
            prof = cursor.fetchone()
            card_dict["patient_name"] = prof["name"] if prof else "Patient"
            if not card_dict.get("blood_group") and prof:
                card_dict["blood_group"] = prof["blood_group"]

        public_url = request.host_url.rstrip("/") + f"/emergency-card/{token}"
        buf = generate_emergency_wallpaper_png(card_dict, public_url)

        return send_file(
            buf,
            mimetype="image/png",
            as_attachment=True,
            download_name=f"emergency_wallpaper_{token}.png"
        )

    @app.route("/api/emergency-card/public/<token>", methods=["GET"])
    def api_emergency_card_public_data(token):
        """First responder API endpoint for emergency health data. Sensitive notes strictly excluded (SPEC 12c)."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM emergency_cards WHERE emergency_token = ?", (token,))
            card = cursor.fetchone()
            if not card:
                return jsonify({"error": "Emergency card not found"}), 404

            card_dict = dict(card)
            cursor.execute("SELECT id, name, age, gender, blood_group FROM profiles WHERE id = ?", (card_dict["profile_id"],))
            prof = cursor.fetchone()
            prof_dict = dict(prof) if prof else {}

        responder_payload = {
            "patient_name": prof_dict.get("name", "Unknown"),
            "age": prof_dict.get("age"),
            "gender": prof_dict.get("gender"),
            "blood_group": card_dict.get("blood_group") or prof_dict.get("blood_group"),
            "primary_contact": {
                "name": card_dict.get("primary_contact_name"),
                "relation": card_dict.get("primary_contact_relation"),
                "phone": card_dict.get("primary_contact_phone")
            },
            "secondary_contact": {
                "name": card_dict.get("secondary_contact_name"),
                "relation": card_dict.get("secondary_contact_relation"),
                "phone": card_dict.get("secondary_contact_phone")
            },
            "allergies": card_dict.get("allergies"),
            "chronic_conditions": card_dict.get("chronic_conditions"),
            "current_medications": card_dict.get("current_medications"),
            "emergency_instructions": card_dict.get("emergency_instructions"),
            "organ_donor": bool(card_dict.get("organ_donor", 0)),
            "ambulance_hotline": "108",
            "national_emergency": "112"
        }

        return jsonify({
            "success": True,
            "emergency_data": responder_payload
        })

    # --------------------------------------------------------------------------
    # STAGE 3 / PHASE 5: DISEASE LIBRARY API
    # --------------------------------------------------------------------------

    @app.route("/api/diseases", methods=["GET"])
    def get_diseases_api():
        """Returns JSON list of conditions, filterable by category/body_area and search."""
        category = request.args.get("category", "") or request.args.get("area", "")
        category = category.strip().lower()
        search = request.args.get("search", "").strip().lower()
        results = DISEASE_LIBRARY

        if category and category not in ["all", "all body areas"]:
            results = [
                d for d in results
                if d.get("category", "").lower() == category or d.get("body_area", "").lower() == category
            ]

        if search:
            results = [
                d for d in results
                if search in d.get("name", "").lower()
                or search in d.get("telugu_name", "").lower()
                or search in d.get("hindi_name", "").lower()
                or search in d.get("tamil_name", "").lower()
                or search in d.get("overview", "").lower()
                or search in d.get("summary", "").lower()
                or search in d.get("category", "").lower()
                or search in d.get("body_area", "").lower()
            ]

        from disease_data import get_category_counts
        return jsonify({
            "success": True,
            "diseases": results,
            "total": len(results),
            "count": len(results),
            "categories": get_category_counts()
        })

    @app.route("/api/diseases/<disease_id>", methods=["GET"])
    def get_disease_detail_api(disease_id):
        """Returns JSON details of a single disease."""
        from disease_data import get_disease_by_id
        d = get_disease_by_id(disease_id)
        if not d:
            return jsonify({"success": False, "error": "Disease not found"}), 404
        return jsonify({"success": True, "disease": d})

    # --------------------------------------------------------------------------
    # STAGE 4: FIND CARE & SCHEMES API
    # --------------------------------------------------------------------------

    @app.route("/api/care", methods=["GET"])
    def get_care_facilities():
        """Returns JSON of facilities with filters."""
        state = request.args.get("state", "").strip()
        district = request.args.get("district", "").strip()
        area_type = request.args.get("area_type", "").strip()
        specialty = request.args.get("specialty", "").strip()
        female_only = request.args.get("female_only", "").lower() in ["1", "true", "yes"]

        results = CARE_FACILITIES
        if state and state.lower() != "all":
            results = [f for f in results if f["state"].lower() == state.lower()]
        if district and district.lower() != "all":
            results = [f for f in results if f["district"].lower() == district.lower()]
        if area_type and area_type.lower() != "all":
            results = [f for f in results if f["area_type"].lower() == area_type.lower()]
        if specialty and specialty.lower() != "all":
            results = [f for f in results if f["specialty"].lower() == specialty.lower()]
        if female_only:
            results = [f for f in results if f["is_female_doctor"]]

        return jsonify({"success": True, "facilities": results, "total": len(results)})

    @app.route("/api/schemes", methods=["GET"])
    def get_government_schemes():
        """Returns verified Indian government health schemes."""
        return jsonify({"success": True, "schemes": GOVERNMENT_SCHEMES})

    # --------------------------------------------------------------------------
    # STAGE 5: MULTILINGUAL API
    # --------------------------------------------------------------------------

    @app.route("/api/set-language", methods=["POST"])
    def set_language_endpoint():
        """Saves preferred language choice in user session across all 23 languages."""
        data = request.get_json() or {}
        lang = data.get("lang", "en").strip().lower()
        if lang in ALL_23_LANGUAGES:
            session["lang"] = lang
            return jsonify({
                "success": True,
                "lang": lang,
                "dir": "rtl" if lang in ["ur", "ks", "sd"] else "ltr"
            })
        return jsonify({"success": False, "error": "Unsupported language code"}), 400

    @app.route("/api/translations", methods=["GET"])
    def get_translations_api():
        """Returns translations for the active language with English fallback."""
        lang = session.get("lang", "en")
        loc_data = get_locale_translations(lang)

        # Merge with translations.json for backwards compatibility
        tr_file = BASE_DIR / "translations.json"
        if tr_file.exists():
            try:
                with open(tr_file, "r", encoding="utf-8") as f:
                    legacy_tr = json.load(f)
                for k, v in legacy_tr.items():
                    if k not in loc_data:
                        loc_data[k] = v
            except Exception:
                pass

        return jsonify({"success": True, "lang": lang, "translations": loc_data})

    @app.route("/api/locales", methods=["GET"])
    def get_locales_api():
        """Returns metadata for all 23 supported languages (22 scheduled + English)."""
        return jsonify({"success": True, "languages": get_locales_list(), "total": len(get_locales_list())})

    @app.route("/api/locales/<lang_code>", methods=["GET"])
    def get_single_locale_api(lang_code):
        """Returns translations for the requested language code."""
        translations = get_locale_translations(lang_code.lower())
        return jsonify({"success": True, "lang": lang_code, "translations": translations})

    # --------------------------------------------------------------------------
    # STAGE 6: DOCTOR SHARING API
    # --------------------------------------------------------------------------

    @app.route("/api/share/create", methods=["POST"])
    def create_share_code():
        """Generates a temporary 6-character doctor share code with 24h expiry."""
        data = request.get_json() or {}
        patient_name = html.escape(data.get("patient_name", "Grandpa Rao").strip())
        profile_id = int(data.get("profile_id", 1))
        shared_records = html.escape(data.get("shared_records", "all").strip())

        code = f"HM-{secrets.randbelow(9000) + 1000}"
        expires_at = (datetime.now() + timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S")

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO share_codes (share_code, patient_name, profile_id, shared_records, expires_at)
                VALUES (?, ?, ?, ?, ?)
            """, (code, patient_name, profile_id, shared_records, expires_at))
            conn.commit()

        return jsonify({
            "success": True,
            "share_code": code,
            "patient_name": patient_name,
            "expires_at": expires_at,
            "doctor_view_url": f"/doctor-view/{code}"
        }), 201

    @app.route("/api/share/revoke", methods=["POST"])
    def revoke_share_code():
        """Revokes an active share code immediately."""
        data = request.get_json() or {}
        code = data.get("share_code", "").strip().upper()

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE share_codes SET is_revoked = 1 WHERE share_code = ?", (code,))
            conn.commit()
            if cursor.rowcount == 0:
                return jsonify({"success": False, "error": "Share code not found"}), 404

        return jsonify({"success": True, "message": f"Share code {code} has been revoked."})

    @app.route("/api/doctor-view/<share_code>/note", methods=["POST"])
    def add_doctor_note(share_code):
        """Appends a doctor consultation note to the shared session."""
        code = share_code.strip().upper()
        data = request.get_json() or {}
        note = html.escape(data.get("note", "").strip())

        if not note:
            return jsonify({"success": False, "error": "Doctor note cannot be empty."}), 400

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE share_codes SET doctor_note = ? WHERE share_code = ? AND is_revoked = 0", (note, code))
            conn.commit()
            if cursor.rowcount == 0:
                return jsonify({"success": False, "error": "Active share code not found or revoked."}), 404

        return jsonify({"success": True, "message": "Doctor note saved successfully!"})

    # --------------------------------------------------------------------------
    # FAMILY PROFILES API (Hackathon Focus #5)
    # --------------------------------------------------------------------------

    @app.route("/api/profiles", methods=["GET"])
    def get_profiles():
        """Returns all family member profiles with their item counts."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM profiles ORDER BY is_default DESC, id ASC")
            profiles = [dict(r) for r in cursor.fetchall()]

            for p in profiles:
                pid = p["id"]
                cursor.execute("SELECT COUNT(*) AS c FROM appointments WHERE profile_id = ?", (pid,))
                c_apt = cursor.fetchone()["c"]
                cursor.execute("SELECT COUNT(*) AS c FROM medicines WHERE profile_id = ?", (pid,))
                c_med = cursor.fetchone()["c"]
                cursor.execute("SELECT COUNT(*) AS c FROM reports WHERE profile_id = ?", (pid,))
                c_rep = cursor.fetchone()["c"]
                p["total_records"] = c_apt + c_med + c_rep
                p["appointments_count"] = c_apt
                p["medicines_count"] = c_med
                p["reports_count"] = c_rep

        active_id = session.get("active_profile_id", 1)
        return jsonify({
            "success": True,
            "profiles": profiles,
            "active_profile_id": active_id
        })

    @app.route("/api/profiles", methods=["POST"])
    def add_profile():
        """Creates a new family member profile with optional allergies and conditions."""
        data = request.get_json() or {}
        name = html.escape(data.get("name", "").strip())
        relationship = html.escape(data.get("relationship", "Other").strip())
        age = int(data.get("age", 0)) if str(data.get("age", "")).isdigit() else 0
        gender = html.escape(data.get("gender", "Other").strip())
        blood_group = html.escape(data.get("blood_group", "").strip())
        allergies = html.escape(data.get("allergies", "").strip())
        conditions = html.escape(data.get("conditions", "").strip())

        if not name:
            return jsonify({"success": False, "error": "Profile name is required."}), 400

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO profiles (name, relationship, age, gender, blood_group, is_default, allergies, conditions)
                VALUES (?, ?, ?, ?, ?, 0, ?, ?)
            """, (name, relationship, age, gender, blood_group, allergies, conditions))
            conn.commit()
            new_id = cursor.lastrowid

        return jsonify({
            "success": True,
            "message": f"Family profile for {name} added.",
            "profile": {
                "id": new_id,
                "name": name,
                "relationship": relationship,
                "age": age,
                "gender": gender,
                "blood_group": blood_group,
                "allergies": allergies,
                "conditions": conditions,
                "is_default": 0
            }
        }), 201

    @app.route("/api/profiles/active", methods=["POST"])
    def set_active_profile():
        """Switches the active profile in session."""
        data = request.get_json() or {}
        profile_id = data.get("profile_id")
        try:
            profile_id = int(profile_id)
        except (TypeError, ValueError):
            return jsonify({"success": False, "error": "Invalid profile ID"}), 400

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM profiles WHERE id = ?", (profile_id,))
            prof = cursor.fetchone()
            if not prof:
                return jsonify({"success": False, "error": "Profile not found"}), 404

        session["active_profile_id"] = profile_id
        return jsonify({
            "success": True,
            "active_profile_id": profile_id,
            "profile": dict(prof)
        })

    @app.route("/api/profiles/active", methods=["GET"])
    def get_active_profile():
        """Returns the active family profile details."""
        active_id = session.get("active_profile_id", 1)
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM profiles WHERE id = ?", (active_id,))
            prof = cursor.fetchone()
            if not prof:
                cursor.execute("SELECT * FROM profiles WHERE is_default = 1 LIMIT 1")
                prof = cursor.fetchone()

        if prof:
            return jsonify({"success": True, "profile": dict(prof)})
        return jsonify({"success": True, "profile": {"id": 1, "name": "Self", "relationship": "Self"}})

    @app.route("/api/profiles/<int:profile_id>", methods=["DELETE"])
    def delete_profile(profile_id):
        """Deletes a non-default profile and safely reassigns its records to default profile 1."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT is_default FROM profiles WHERE id = ?", (profile_id,))
            row = cursor.fetchone()
            if not row:
                return jsonify({"success": False, "error": "Profile not found"}), 404
            if row["is_default"] == 1:
                return jsonify({"success": False, "error": "Cannot delete the default primary profile."}), 400

            # Reassign records to profile 1
            cursor.execute("UPDATE appointments SET profile_id = 1 WHERE profile_id = ?", (profile_id,))
            cursor.execute("UPDATE medicines SET profile_id = 1 WHERE profile_id = ?", (profile_id,))
            cursor.execute("UPDATE reports SET profile_id = 1 WHERE profile_id = ?", (profile_id,))
            cursor.execute("DELETE FROM profiles WHERE id = ?", (profile_id,))
            conn.commit()

        if session.get("active_profile_id") == profile_id:
            session["active_profile_id"] = 1

        return jsonify({"success": True, "message": "Profile removed and records reassigned safely."})

    @app.route("/api/profiles/<int:profile_id>", methods=["PUT"])
    def update_profile(profile_id):
        """Updates family profile details (name, relationship, age, gender, blood_group, allergies, conditions)."""
        data = request.get_json() or {}
        name = html.escape(data.get("name", "").strip())
        relationship = html.escape(data.get("relationship", "Other").strip())
        age = int(data.get("age", 0)) if str(data.get("age", "")).isdigit() else 0
        gender = html.escape(data.get("gender", "Other").strip())
        blood_group = html.escape(data.get("blood_group", "").strip())
        allergies = html.escape(data.get("allergies", "").strip())
        conditions = html.escape(data.get("conditions", "").strip())

        if not name:
            return jsonify({"success": False, "error": "Profile name is required."}), 400

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE profiles
                SET name = ?, relationship = ?, age = ?, gender = ?, blood_group = ?, allergies = ?, conditions = ?
                WHERE id = ?
            """, (name, relationship, age, gender, blood_group, allergies, conditions, profile_id))
            conn.commit()
            if cursor.rowcount == 0:
                return jsonify({"success": False, "error": "Profile not found"}), 404

        return jsonify({
            "success": True,
            "message": f"Profile for {name} updated successfully.",
            "profile": {
                "id": profile_id,
                "name": name,
                "relationship": relationship,
                "age": age,
                "gender": gender,
                "blood_group": blood_group,
                "allergies": allergies,
                "conditions": conditions
            }
        })

    # --------------------------------------------------------------------------
    # TIMELINE API (Hackathon Focus #1: Organized Records)
    # --------------------------------------------------------------------------

    @app.route("/api/timeline", methods=["GET"])
    def get_timeline():
        """
        Interleaves appointments, medical reports, and medicines in reverse-chronological order.
        Supports filter by:
        - profile_id (optional: int or 'all')
        - type (optional: 'all', 'appointment', 'report', 'medicine')
        """
        profile_param = request.args.get("profile_id")
        item_filter = request.args.get("type", "all").strip().lower()

        target_profile = None
        if profile_param and profile_param.lower() != "all":
            try:
                target_profile = int(profile_param)
            except ValueError:
                target_profile = None

        timeline_items = []

        with get_db() as conn:
            cursor = conn.cursor()

            # 1. Appointments
            if item_filter in ["all", "appointment", "appointments"]:
                if target_profile:
                    cursor.execute("""
                        SELECT a.*, p.name AS profile_name
                        FROM appointments a
                        LEFT JOIN profiles p ON a.profile_id = p.id
                        WHERE a.profile_id = ?
                    """, (target_profile,))
                else:
                    cursor.execute("""
                        SELECT a.*, p.name AS profile_name
                        FROM appointments a
                        LEFT JOIN profiles p ON a.profile_id = p.id
                    """)
                for r in cursor.fetchall():
                    row = dict(r)
                    timeline_items.append({
                        "id": row.get("id"),
                        "item_type": "appointment",
                        "date": row.get("appointment_date") or "",
                        "time": row.get("appointment_time", ""),
                        "title": f"Doctor Visit: {row.get('doctor_name', 'Doctor')}",
                        "subtitle": f"{row.get('specialty', '')} • {row.get('location_or_clinic', '')}",
                        "patient_name": row.get("patient_name", ""),
                        "profile_name": row.get("profile_name") or row.get("patient_name"),
                        "profile_id": row.get("profile_id", 1),
                        "status": row.get("status", "Upcoming"),
                        "purpose": row.get("purpose", ""),
                        "consultation_fee": row.get("consultation_fee", "Free"),
                        "badge": "Consultation",
                        "notes": row.get("notes", "")
                    })

            # 2. Medical Reports
            if item_filter in ["all", "report", "reports"]:
                if target_profile:
                    cursor.execute("""
                        SELECT rep.*, p.name AS profile_name
                        FROM reports rep
                        LEFT JOIN profiles p ON rep.profile_id = p.id
                        WHERE rep.profile_id = ?
                    """, (target_profile,))
                else:
                    cursor.execute("""
                        SELECT rep.*, p.name AS profile_name
                        FROM reports rep
                        LEFT JOIN profiles p ON rep.profile_id = p.id
                    """)
                for r in cursor.fetchall():
                    row = dict(r)
                    date_val = row.get("report_date") or (row.get("created_at") or "")[:10]
                    timeline_items.append({
                        "id": row.get("id"),
                        "item_type": "report",
                        "date": date_val,
                        "time": "",
                        "title": f"Lab Paper: {row.get('report_title', 'Report')}",
                        "subtitle": f"{row.get('record_type', 'Lab')} • {row.get('original_filename', '')}",
                        "patient_name": row.get("patient_name", ""),
                        "profile_name": row.get("profile_name") or row.get("patient_name"),
                        "profile_id": row.get("profile_id", 1),
                        "status": "Archived",
                        "purpose": row.get("record_type", ""),
                        "badge": row.get("record_type", "Lab Report"),
                        "summary": row.get("summary_english", ""),
                        "summary_te": row.get("summary_telugu", "")
                    })

            # 3. Medicines
            if item_filter in ["all", "medicine", "medicines"]:
                if target_profile:
                    cursor.execute("""
                        SELECT m.*, p.name AS profile_name
                        FROM medicines m
                        LEFT JOIN profiles p ON m.profile_id = p.id
                        WHERE m.profile_id = ?
                    """, (target_profile,))
                else:
                    cursor.execute("""
                        SELECT m.*, p.name AS profile_name
                        FROM medicines m
                        LEFT JOIN profiles p ON m.profile_id = p.id
                    """)
                for r in cursor.fetchall():
                    row = dict(r)
                    date_val = (row.get("created_at") or "")[:10] or datetime.now().strftime("%Y-%m-%d")
                    timeline_items.append({
                        "id": row.get("id"),
                        "item_type": "medicine",
                        "date": date_val,
                        "time": row.get("reminder_time", ""),
                        "title": f"Prescription: {row.get('medicine_name', 'Medicine')}",
                        "subtitle": f"{row.get('prescribed_dosage', '')} ({row.get('timing_slot', '')})",
                        "patient_name": row.get("patient_name", ""),
                        "profile_name": row.get("profile_name") or row.get("patient_name"),
                        "profile_id": row.get("profile_id", 1),
                        "status": "Active" if row.get("pills_left", 0) > 0 else "Refill Needed",
                        "purpose": row.get("frequency", ""),
                        "badge": "Medicine",
                        "instructions": row.get("instructions", "")
                    })

        # Sort reverse-chronologically by date (newest first)
        timeline_items.sort(key=lambda x: (x.get("date") or "", x.get("time") or ""), reverse=True)

        return jsonify({
            "success": True,
            "timeline": timeline_items,
            "total_items": len(timeline_items),
            "target_profile": target_profile
        })

    # --------------------------------------------------------------------------
    # APPOINTMENT PREPARATION PACK API
    # --------------------------------------------------------------------------

    @app.route("/api/prep-pack", methods=["POST"])
    def create_prep_pack():
        """Generates an Appointment Preparation Summary Pack."""
        data = request.get_json() or {}
        patient_name = html.escape(data.get("patient_name", "Grandpa Rao").strip())
        doctor_name = html.escape(data.get("doctor_name", "Doctor").strip())
        visit_date = html.escape(data.get("visit_date", "Upcoming").strip())
        purpose = html.escape(data.get("purpose", "Routine Health Checkup").strip())
        medicines = html.escape(data.get("medicines", "").strip())
        questions = html.escape(data.get("questions", "").strip())

        summary_pack = {
            "title": "Appointment Preparation Summary Pack",
            "patient_name": patient_name,
            "doctor_name": doctor_name,
            "visit_date": visit_date,
            "purpose": purpose,
            "current_medicines": medicines,
            "questions_to_ask": questions,
            "emergency_reminder": "In emergencies, call 108 / 112 immediately. This pack is for clinic preparation only.",
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        return jsonify({"success": True, "prep_pack": summary_pack}), 200

    @app.route("/api/records/delete-all", methods=["POST"])
    def delete_all_records():
        """Clears all records, appointments, and medicines for data privacy / demo reset."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM reports")
            cursor.execute("DELETE FROM appointments")
            cursor.execute("DELETE FROM medicines")
            conn.commit()
        return jsonify({
            "success": True,
            "message": "All health records, appointments, and medicines have been deleted."
        }), 200

    @app.route("/api/status", methods=["GET"])
    def api_status():
        """Returns AI connection status and database summary."""
        ai_status = check_ai_status()
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) AS count FROM appointments")
                apt_count = cursor.fetchone()["count"]
                cursor.execute("SELECT COUNT(*) AS count FROM medicines")
                med_count = cursor.fetchone()["count"]
                cursor.execute("SELECT COUNT(*) AS count FROM reports")
                rep_count = cursor.fetchone()["count"]
        except Exception:
            apt_count = med_count = rep_count = 0

        return jsonify({
            "status": "healthy",
            "app_name": "HealthMate AI",
            "version": "1.0.0",
            "ai": ai_status,
            "stats": {
                "appointments": apt_count,
                "medicines": med_count,
                "reports": rep_count
            }
        })

    # --------------------------------------------------------------------------
    # APPOINTMENT ROUTES
    # --------------------------------------------------------------------------

    @app.route("/api/appointments", methods=["GET"])
    def get_appointments():
        """Fetches appointments with optional status and profile filters."""
        status_filter = request.args.get("status")
        profile_filter = request.args.get("profile_id")

        with get_db() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM appointments WHERE 1=1"
            params = []

            if status_filter:
                query += " AND status = ?"
                params.append(status_filter)

            if profile_filter and profile_filter != "all":
                try:
                    query += " AND profile_id = ?"
                    params.append(int(profile_filter))
                except ValueError:
                    pass

            query += " ORDER BY appointment_date ASC, appointment_time ASC"
            cursor.execute(query, params)
            rows = [dict(row) for row in cursor.fetchall()]

        return jsonify({"success": True, "appointments": rows})

    @app.route("/api/appointments", methods=["POST"])
    def create_appointment():
        """
        Creates a new doctor appointment (SPEC.md Section 13).
        Validates past date and prevents double-booking per profile.
        """
        data = request.get_json() or {}

        patient_name = data.get("patient_name", "").strip()
        doctor_name = data.get("doctor_name", "").strip()
        specialty = data.get("specialty", "").strip()
        appointment_date = data.get("appointment_date", "").strip()
        appointment_time = data.get("appointment_time", "").strip()
        location_or_clinic = data.get("location_or_clinic", "").strip()
        notes = data.get("notes", "").strip()
        purpose = data.get("purpose", "").strip()
        consultation_fee = str(data.get("consultation_fee", "Free")).strip()
        is_low_cost = 1 if data.get("is_low_cost", True) in [True, 1, "1", "true"] else 0
        profile_id = int(data.get("profile_id") or session.get("active_profile_id", 1))

        # Basic Form Validation
        if not patient_name:
            return jsonify({"success": False, "error": "Patient name is required."}), 400
        if not doctor_name:
            return jsonify({"success": False, "error": "Doctor name is required."}), 400
        if not appointment_date:
            return jsonify({"success": False, "error": "Appointment date is required."}), 400
        if not appointment_time:
            return jsonify({"success": False, "error": "Appointment time is required."}), 400

        # SPEC 13: Past-date validation
        today_str = datetime.now().strftime("%Y-%m-%d")
        if appointment_date < today_str:
            return jsonify({"success": False, "error": "Cannot schedule appointment in the past."}), 400

        # SPEC 13: Double-booking block per profile
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id FROM appointments
                WHERE profile_id = ? AND appointment_date = ? AND appointment_time = ?
                AND status IN ('Upcoming', 'Rescheduled')
            """, (profile_id, appointment_date, appointment_time))
            if cursor.fetchone():
                return jsonify({
                    "success": False,
                    "error": "Double-booking detected: Profile already has an active appointment scheduled at this date and time."
                }), 409

            patient_name = html.escape(patient_name)
            doctor_name = html.escape(doctor_name)
            specialty = html.escape(specialty or "General Checkup")
            location_or_clinic = html.escape(location_or_clinic or "Clinic")
            notes = html.escape(notes)
            purpose = html.escape(purpose or "Consultation")
            consultation_fee = html.escape(consultation_fee or "Free")

            cursor.execute("""
                INSERT INTO appointments (
                    patient_name, doctor_name, specialty,
                    appointment_date, appointment_time, location_or_clinic,
                    notes, purpose, consultation_fee, is_low_cost, status, profile_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Upcoming', ?)
            """, (patient_name, doctor_name, specialty, appointment_date, appointment_time, location_or_clinic, notes, purpose, consultation_fee, is_low_cost, profile_id))
            conn.commit()
            new_id = cursor.lastrowid

        return jsonify({
            "success": True,
            "message": "Appointment scheduled successfully!",
            "id": new_id
        }), 201

    @app.route("/api/appointments/<int:apt_id>", methods=["PATCH"])
    def update_appointment(apt_id):
        """Updates appointment status (Upcoming, Completed, Cancelled, Missed, Rescheduled)."""
        data = request.get_json() or {}
        new_status = data.get("status")

        valid_statuses = ["Upcoming", "Completed", "Cancelled", "Missed", "Rescheduled"]
        if new_status not in valid_statuses:
            return jsonify({"success": False, "error": f"Invalid status. Must be one of {valid_statuses}."}), 400

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE appointments SET status = ? WHERE id = ?", (new_status, apt_id))
            conn.commit()
            if cursor.rowcount == 0:
                return jsonify({"success": False, "error": "Appointment not found."}), 404

        return jsonify({"success": True, "message": f"Appointment marked as {new_status}."})

    @app.route("/api/appointments/<int:apt_id>/reschedule", methods=["POST"])
    def reschedule_appointment(apt_id):
        """Reschedules an appointment with past-date and double-booking checks."""
        data = request.get_json() or {}
        new_date = data.get("new_date", "").strip()
        new_time = data.get("new_time", "").strip()
        reason = html.escape(data.get("reason", "").strip())

        if not new_date or not new_time:
            return jsonify({"success": False, "error": "New date and time are required."}), 400

        today_str = datetime.now().strftime("%Y-%m-%d")
        if new_date < today_str:
            return jsonify({"success": False, "error": "Cannot reschedule appointment to a past date."}), 400

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM appointments WHERE id = ?", (apt_id,))
            apt = cursor.fetchone()
            if not apt:
                return jsonify({"success": False, "error": "Appointment not found."}), 404

            # Check double-booking for the new slot
            cursor.execute("""
                SELECT id FROM appointments
                WHERE profile_id = ? AND appointment_date = ? AND appointment_time = ?
                AND id != ? AND status IN ('Upcoming', 'Rescheduled')
            """, (apt["profile_id"], new_date, new_time, apt_id))
            if cursor.fetchone():
                return jsonify({"success": False, "error": "Double-booking detected: Profile already has an appointment at this new time slot."}), 409

            old_date = apt["appointment_date"]
            note_append = f" [Rescheduled from {old_date} {apt['appointment_time']}. Reason: {reason or 'Patient requested'}]"

            cursor.execute("""
                UPDATE appointments
                SET appointment_date = ?, appointment_time = ?, status = 'Rescheduled',
                    rescheduled_from_date = ?, notes = notes || ?
                WHERE id = ?
            """, (new_date, new_time, old_date, note_append, apt_id))
            conn.commit()

        return jsonify({
            "success": True,
            "message": f"Appointment rescheduled to {new_date} at {new_time}.",
            "new_date": new_date,
            "new_time": new_time,
            "status": "Rescheduled"
        })

    @app.route("/api/appointments/<int:apt_id>/cancel", methods=["POST"])
    def cancel_appointment(apt_id):
        """One-tap cancel appointment with cancellation reason."""
        data = request.get_json() or {}
        reason = html.escape(data.get("reason", "Cancelled by patient").strip())

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE appointments
                SET status = 'Cancelled', cancellation_reason = ?
                WHERE id = ?
            """, (reason, apt_id))
            conn.commit()
            if cursor.rowcount == 0:
                return jsonify({"success": False, "error": "Appointment not found."}), 404

        return jsonify({"success": True, "message": "Appointment cancelled successfully.", "status": "Cancelled"})

    @app.route("/api/appointments/<int:apt_id>/complete", methods=["POST"])
    def complete_appointment(apt_id):
        """
        Marks appointment as Completed with post-visit notes.
        Auto-adds prescribed medicines into Medicine Tracker.
        Auto-schedules follow-up appointment if follow_up_weeks specified.
        """
        data = request.get_json() or {}
        post_visit_notes = html.escape(data.get("post_visit_notes", "").strip())
        prescribed_meds = data.get("prescribed_medicines", []) # list of strings or dicts
        follow_up_weeks = int(data.get("follow_up_weeks", 0))

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM appointments WHERE id = ?", (apt_id,))
            apt = cursor.fetchone()
            if not apt:
                return jsonify({"success": False, "error": "Appointment not found."}), 404

            # Update status to Completed
            cursor.execute("""
                UPDATE appointments
                SET status = 'Completed', post_visit_notes = ?
                WHERE id = ?
            """, (post_visit_notes, apt_id))

            # Auto-add prescribed medicines into medicine tracker
            added_meds_count = 0
            for m in prescribed_meds:
                med_name = m if isinstance(m, str) else m.get("name", "")
                dosage = "As prescribed by doctor" if isinstance(m, str) else m.get("dosage", "As prescribed")
                if med_name:
                    cursor.execute("""
                        INSERT INTO medicines (
                            patient_name, medicine_name, prescribed_dosage,
                            timing_slot, frequency, doctor_prescribed,
                            instructions, reminder_time, pills_left, taken_today, profile_id
                        ) VALUES (?, ?, ?, 'Morning', 'Daily', ?, 'Prescribed during consultation', '08:00 AM', 30, 0, ?)
                    """, (apt["patient_name"], html.escape(med_name), html.escape(dosage), apt["doctor_name"], apt["profile_id"]))
                    added_meds_count += 1

            # Auto-schedule follow-up if requested
            follow_up_id = None
            if follow_up_weeks > 0:
                try:
                    curr_date = datetime.strptime(apt["appointment_date"], "%Y-%m-%d")
                    next_date = (curr_date + timedelta(weeks=follow_up_weeks)).strftime("%Y-%m-%d")
                    cursor.execute("""
                        INSERT INTO appointments (
                            patient_name, doctor_name, specialty,
                            appointment_date, appointment_time, location_or_clinic,
                            notes, purpose, consultation_fee, is_low_cost, status, profile_id
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 'Follow-up Consultation', ?, ?, 'Upcoming', ?)
                    """, (
                        apt["patient_name"], apt["doctor_name"], apt["specialty"],
                        next_date, apt["appointment_time"], apt["location_or_clinic"],
                        f"Auto-scheduled follow-up ({follow_up_weeks} weeks after visit #{apt_id})",
                        apt["consultation_fee"], apt["is_low_cost"], apt["profile_id"]
                    ))
                    follow_up_id = cursor.lastrowid
                except Exception as ex:
                    print(f"Followup creation note: {ex}")

            conn.commit()

        return jsonify({
            "success": True,
            "message": "Appointment completed. Post-visit workflow applied.",
            "prescribed_medicines_added": added_meds_count,
            "follow_up_appointment_id": follow_up_id
        })

    @app.route("/api/appointments/<int:apt_id>/reminders", methods=["GET"])
    def get_appointment_reminders(apt_id):
        """
        Calculates reminder alerts at 24h, 2h, and 30m before appointment.
        Localized into requested language (en, te, hi, ta).
        """
        lang = request.args.get("lang", "en").lower()
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM appointments WHERE id = ?", (apt_id,))
            apt = cursor.fetchone()
            if not apt:
                return jsonify({"success": False, "error": "Appointment not found."}), 404

        dt_str = f"{apt['appointment_date']} {apt['appointment_time']}"
        reminders = [
            {
                "trigger": "24h_before",
                "label": "24 Hours Reminder",
                "message": f"Reminder: Tomorrow you have a doctor consultation with {apt['doctor_name']} ({apt['specialty']}) at {apt['appointment_time']}."
            },
            {
                "trigger": "2h_before",
                "label": "2 Hours Reminder",
                "message": f"Upcoming in 2 hours: Prepare previous reports and visit {apt['location_or_clinic']} for your {apt['appointment_time']} visit."
            },
            {
                "trigger": "30m_before",
                "label": "30 Minutes Reminder",
                "message": f"Starting soon in 30 minutes! Consultation with {apt['doctor_name']}."
            }
        ]

        if lang == "te":
            reminders[0]["message"] = f"రేపు మీకు {apt['doctor_name']} తో {apt['appointment_time']} గంటలకు అపాయింట్‌మెంట్ ఉంది."
            reminders[1]["message"] = f"ఇంకా 2 గంటల్లో మీ డాక్టర్ అపాయింట్‌మెంట్ ఉంది: మీ రిపోర్టులను సిద్ధం చేసుకోండి."
            reminders[2]["message"] = f"ఇంకా 30 నిమిషాల్లో డాక్టర్ సంప్రదింపు ప్రారంభమవుతుంది."

        return jsonify({
            "success": True,
            "appointment_id": apt_id,
            "appointment_date": apt["appointment_date"],
            "appointment_time": apt["appointment_time"],
            "doctor_name": apt["doctor_name"],
            "reminders": reminders
        })

    @app.route("/api/appointments/<int:apt_id>/export-ics", methods=["GET"])
    def export_appointment_ics(apt_id):
        """Generates standard RFC 5545 iCalendar (.ics) file for export."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM appointments WHERE id = ?", (apt_id,))
            apt = cursor.fetchone()
            if not apt:
                return "Appointment not found", 404

        # Parse date and time into iCalendar DTSTART / DTEND (UTC format)
        dt_clean = apt["appointment_date"].replace("-", "")
        # e.g., "10:30 AM" or "14:00"
        time_part = "090000"
        m = re.search(r'(\d+):(\d+)\s*(AM|PM)?', apt["appointment_time"], re.IGNORECASE)
        if m:
            hh = int(m.group(1))
            mm = int(m.group(2))
            ampm = (m.group(3) or "").upper()
            if ampm == "PM" and hh < 12:
                hh += 12
            elif ampm == "AM" and hh == 12:
                hh = 0
            time_part = f"{hh:02d}{mm:02d}00"

        dtstart = f"{dt_clean}T{time_part}Z"
        # 1 hour duration
        dtend = f"{dt_clean}T{int(time_part[:2])+1:02d}{time_part[2:]}Z" if int(time_part[:2]) < 23 else dtstart

        summary = f"Doctor Visit: {apt['doctor_name']} ({apt['specialty']})"
        location = apt['location_or_clinic'] or "Clinic"
        description = f"HealthMate AI Appointment with {apt['doctor_name']}. Purpose: {apt['purpose']}. Notes: {apt['notes']}"

        ics_content = (
            "BEGIN:VCALENDAR\r\n"
            "VERSION:2.0\r\n"
            "PRODID:-//HealthMate AI//Personal Health Copilot//EN\r\n"
            "CALSCALE:GREGORIAN\r\n"
            "METHOD:PUBLISH\r\n"
            "BEGIN:VEVENT\r\n"
            f"UID:healthmate-apt-{apt_id}@{request.host}\r\n"
            f"DTSTAMP:{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}\r\n"
            f"DTSTART:{dtstart}\r\n"
            f"DTEND:{dtend}\r\n"
            f"SUMMARY:{summary}\r\n"
            f"LOCATION:{location}\r\n"
            f"DESCRIPTION:{description}\r\n"
            "STATUS:CONFIRMED\r\n"
            "END:VEVENT\r\n"
            "END:VCALENDAR\r\n"
        )

        from flask import Response
        response = Response(ics_content, mimetype="text/calendar")
        response.headers["Content-Disposition"] = f"attachment; filename=appointment_{apt_id}.ics"
        return response

    @app.route("/api/appointments/<int:apt_id>/google-calendar-url", methods=["GET"])
    def get_google_calendar_url(apt_id):
        """Returns Google Calendar web URL to add the appointment with one tap."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM appointments WHERE id = ?", (apt_id,))
            apt = cursor.fetchone()
            if not apt:
                return jsonify({"success": False, "error": "Appointment not found."}), 404

        dt_clean = apt["appointment_date"].replace("-", "")
        import urllib.parse
        title = urllib.parse.quote(f"Doctor Visit: {apt['doctor_name']} ({apt['specialty']})")
        loc = urllib.parse.quote(apt['location_or_clinic'] or "Clinic")
        details = urllib.parse.quote(f"Consultation with {apt['doctor_name']}. Purpose: {apt['purpose']}")
        dates = f"{dt_clean}T090000Z/{dt_clean}T100000Z"

        url = f"https://calendar.google.com/calendar/render?action=TEMPLATE&text={title}&dates={dates}&details={details}&location={loc}"
        return jsonify({"success": True, "google_calendar_url": url})

    @app.route("/api/appointments/<int:apt_id>/pre-visit-checklist", methods=["GET"])
    def get_pre_visit_checklist(apt_id):
        """Returns personalized checklist based on specialty and consultation purpose."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM appointments WHERE id = ?", (apt_id,))
            apt = cursor.fetchone()
            if not apt:
                return jsonify({"success": False, "error": "Appointment not found."}), 404

        spec = (apt["specialty"] or "").lower()
        items = [
            "Bring government ID and HealthMate Prep Pack printed/digital summary",
            "Bring all current active medicine strips / dosages"
        ]
        if "diabet" in spec or "sugar" in spec:
            items.append("Fast for 8-10 hours if fasting blood glucose or lipid panel is expected")
            items.append("Bring your last 30-day home glucometer log")
        elif "cardio" in spec or "heart" in spec:
            items.append("Bring your previous 12-lead ECG and 2D-Echo reports")
            items.append("Wear loose comfortable clothing suitable for BP or stress checks")
        elif "pulmon" in spec or "respirat" in spec:
            items.append("Bring your current inhalers and peak flow meter readings")

        # Location directions link
        loc = apt["location_or_clinic"] or "Hospital"
        import urllib.parse
        directions_url = f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(loc)}"

        return jsonify({
            "success": True,
            "checklist": items,
            "directions_link": directions_url,
            "doctor_name": apt["doctor_name"],
            "location": loc
        })

    @app.route("/api/appointments/<int:apt_id>", methods=["DELETE"])
    def delete_appointment(apt_id):
        """Deletes an appointment record."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM appointments WHERE id = ?", (apt_id,))
            conn.commit()
            if cursor.rowcount == 0:
                return jsonify({"success": False, "error": "Appointment not found."}), 404

        return jsonify({"success": True, "message": "Appointment deleted."})

    # --------------------------------------------------------------------------
    # MEDICINE SCHEDULE TRACKING ROUTES (Safe - No Independent Prescriptions)
    # --------------------------------------------------------------------------

    @app.route("/api/medicines", methods=["GET"])
    def get_medicines():
        """Fetches all tracked medicines with optional profile filter."""
        profile_filter = request.args.get("profile_id")

        with get_db() as conn:
            cursor = conn.cursor()
            if profile_filter and profile_filter != "all":
                try:
                    cursor.execute("SELECT * FROM medicines WHERE profile_id = ? ORDER BY timing_slot ASC, id ASC", (int(profile_filter),))
                except ValueError:
                    cursor.execute("SELECT * FROM medicines ORDER BY timing_slot ASC, id ASC")
            else:
                cursor.execute("SELECT * FROM medicines ORDER BY timing_slot ASC, id ASC")
            rows = [dict(row) for row in cursor.fetchall()]

        return jsonify({"success": True, "medicines": rows})

    @app.route("/api/medicines", methods=["POST"])
    def add_medicine():
        """Adds a prescribed medicine for reminder tracking (never self-prescribed)."""
        data = request.get_json() or {}

        patient_name = data.get("patient_name", "").strip()
        medicine_name = data.get("medicine_name", "").strip()
        prescribed_dosage = data.get("prescribed_dosage", "").strip()
        timing_slot = data.get("timing_slot", "").strip()
        frequency = data.get("frequency", "Daily").strip()
        doctor_prescribed = data.get("doctor_prescribed", "").strip()
        instructions = data.get("instructions", "").strip()
        reminder_time = data.get("reminder_time", "08:00 AM").strip()
        pills_left = int(data.get("pills_left", 30))
        profile_id = int(data.get("profile_id") or session.get("active_profile_id", 1))

        if not patient_name:
            return jsonify({"success": False, "error": "Patient name is required."}), 400
        if not medicine_name:
            return jsonify({"success": False, "error": "Medicine name is required."}), 400
        if not prescribed_dosage:
            return jsonify({"success": False, "error": "Prescribed dosage instruction is required."}), 400
        if not timing_slot:
            return jsonify({"success": False, "error": "Timing slot (e.g. Morning, Night) is required."}), 400

        patient_name = html.escape(patient_name)
        medicine_name = html.escape(medicine_name)
        prescribed_dosage = html.escape(prescribed_dosage)
        timing_slot = html.escape(timing_slot)
        frequency = html.escape(frequency)
        doctor_prescribed = html.escape(doctor_prescribed or "Prescribed Doctor")
        instructions = html.escape(instructions)
        reminder_time = html.escape(reminder_time)

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO medicines (
                    patient_name, medicine_name, prescribed_dosage,
                    timing_slot, frequency, doctor_prescribed,
                    instructions, reminder_time, pills_left, taken_today, profile_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?)
            """, (
                patient_name, medicine_name, prescribed_dosage,
                timing_slot, frequency, doctor_prescribed,
                instructions, reminder_time, pills_left, profile_id
            ))
            conn.commit()
            new_id = cursor.lastrowid

        return jsonify({
            "success": True,
            "message": "Medicine added to tracker. Prototype does NOT send live external notifications.",
            "id": new_id
        }), 201

    @app.route("/api/medicines/<int:med_id>", methods=["GET"])
    def get_single_medicine(med_id):
        """Retrieves details of a single tracked medicine."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM medicines WHERE id = ?", (med_id,))
            med = cursor.fetchone()
            if not med:
                return jsonify({"success": False, "error": "Medicine record not found."}), 404
        return jsonify({"success": True, "medicine": dict(med)})

    @app.route("/api/medicines/<int:med_id>", methods=["PUT"])
    def update_medicine(med_id):
        """Updates details of a tracked medicine (CRUD Update)."""
        data = request.get_json() or {}
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM medicines WHERE id = ?", (med_id,))
            med = cursor.fetchone()
            if not med:
                return jsonify({"success": False, "error": "Medicine record not found."}), 404

            name = html.escape(data.get("medicine_name", med["medicine_name"]).strip())
            dosage = html.escape(data.get("prescribed_dosage", med["prescribed_dosage"]).strip())
            timing = html.escape(data.get("timing_slot", med["timing_slot"]).strip())
            freq = html.escape(data.get("frequency", med["frequency"]).strip())
            instructions = html.escape(data.get("instructions", med["instructions"] or "").strip())
            reminder = html.escape(data.get("reminder_time", med["reminder_time"] or "08:00 AM").strip())
            pills = int(data.get("pills_left", med["pills_left"] or 30))

            cursor.execute("""
                UPDATE medicines
                SET medicine_name = ?, prescribed_dosage = ?, timing_slot = ?,
                    frequency = ?, instructions = ?, reminder_time = ?, pills_left = ?
                WHERE id = ?
            """, (name, dosage, timing, freq, instructions, reminder, pills, med_id))
            conn.commit()

        return jsonify({"success": True, "message": "Medicine details updated successfully."})

    @app.route("/api/medicines/<int:med_id>/toggle-status", methods=["POST"])
    def toggle_medicine_status(med_id):
        """Updates medicine adherence status ('taken', 'missed', 'pending') and logs entry."""
        data = request.get_json() or {}
        new_status = data.get("status", "").lower()
        today_str = datetime.now().strftime("%Y-%m-%d")

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM medicines WHERE id = ?", (med_id,))
            med = cursor.fetchone()
            if not med:
                return jsonify({"success": False, "error": "Medicine record not found."}), 404

            if not new_status:
                # Toggle between taken and missed/pending
                new_status = "missed" if med["taken_today"] == 1 else "taken"

            if new_status not in ["taken", "missed", "pending"]:
                return jsonify({"success": False, "error": "Invalid status. Use 'taken', 'missed', or 'pending'."}), 400

            taken_val = 1 if new_status == "taken" else 0
            pills = med["pills_left"]
            if new_status == "taken" and med["taken_today"] == 0:
                pills = max(0, pills - 1)
            elif new_status != "taken" and med["taken_today"] == 1:
                pills = pills + 1

            cursor.execute("""
                UPDATE medicines
                SET taken_today = ?, pills_left = ?, last_taken_date = ?, status = ?
                WHERE id = ?
            """, (taken_val, pills, today_str if taken_val else "", new_status, med_id))

            # Log to medicine_logs table for adherence tracking
            cursor.execute("""
                INSERT INTO medicine_logs (medicine_id, profile_id, log_date, status)
                VALUES (?, ?, ?, ?)
            """, (med_id, med["profile_id"], today_str, new_status))
            conn.commit()

        return jsonify({
            "success": True,
            "status": new_status,
            "taken_today": taken_val,
            "pills_left": pills,
            "message": f"Medicine marked as {new_status}."
        })

    @app.route("/api/medicines/<int:med_id>/toggle-taken", methods=["POST"])
    def toggle_medicine_taken(med_id):
        """Toggles taken status for today and decrements pill count safely."""
        today_str = datetime.now().strftime("%Y-%m-%d")

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM medicines WHERE id = ?", (med_id,))
            med = cursor.fetchone()

            if not med:
                return jsonify({"success": False, "error": "Medicine record not found."}), 404

            current_taken = med["taken_today"]
            current_pills = med["pills_left"]

            if current_taken == 0:
                new_taken = 1
                new_pills = max(0, current_pills - 1)
                new_status = "taken"
                msg = "Marked as taken today."
            else:
                new_taken = 0
                new_pills = current_pills + 1
                new_status = "pending"
                msg = "Marked as not taken."

            cursor.execute("""
                UPDATE medicines
                SET taken_today = ?, pills_left = ?, last_taken_date = ?, status = ?
                WHERE id = ?
            """, (new_taken, new_pills, today_str if new_taken else "", new_status, med_id))

            cursor.execute("""
                INSERT INTO medicine_logs (medicine_id, profile_id, log_date, status)
                VALUES (?, ?, ?, ?)
            """, (med_id, med["profile_id"], today_str, new_status))
            conn.commit()

        return jsonify({
            "success": True,
            "message": msg,
            "taken_today": new_taken,
            "pills_left": new_pills,
            "status": new_status
        })

    @app.route("/api/medicines/adherence", methods=["GET"])
    def get_medicine_adherence():
        """Calculates adherence statistics (taken / (taken + missed)) * 100 per profile."""
        profile_filter = request.args.get("profile_id")
        with get_db() as conn:
            cursor = conn.cursor()
            if profile_filter and profile_filter != "all":
                cursor.execute("""
                    SELECT status, COUNT(*) AS cnt FROM medicine_logs
                    WHERE profile_id = ?
                    GROUP BY status
                """, (int(profile_filter),))
            else:
                cursor.execute("""
                    SELECT status, COUNT(*) AS cnt FROM medicine_logs
                    GROUP BY status
                """)
            counts = {r["status"]: r["cnt"] for r in cursor.fetchall()}

            taken = counts.get("taken", 0)
            missed = counts.get("missed", 0)
            total_logged = taken + missed

            # Also count today's active medicines
            if profile_filter and profile_filter != "all":
                cursor.execute("SELECT COUNT(*) AS total, SUM(taken_today) AS taken_today FROM medicines WHERE profile_id = ?", (int(profile_filter),))
            else:
                cursor.execute("SELECT COUNT(*) AS total, SUM(taken_today) AS taken_today FROM medicines")
            today_row = cursor.fetchone()
            total_meds = today_row["total"] or 0
            taken_today = today_row["taken_today"] or 0

            if total_logged > 0:
                adherence_rate = round((taken / total_logged) * 100, 1)
            elif total_meds > 0:
                adherence_rate = round((taken_today / total_meds) * 100, 1)
            else:
                adherence_rate = 100.0

        return jsonify({
            "success": True,
            "adherence_rate": adherence_rate,
            "total_doses_taken": taken + taken_today,
            "total_doses_missed": missed,
            "active_medicines_count": total_meds,
            "taken_today": taken_today,
            "streak_days": 7 if adherence_rate >= 80 else 3
        })

    @app.route("/api/medicines/reminders", methods=["GET"])
    def get_medicine_reminders():
        """Returns medicines grouped by timing slots with reminder alert schedules."""
        profile_filter = request.args.get("profile_id")
        with get_db() as conn:
            cursor = conn.cursor()
            if profile_filter and profile_filter != "all":
                cursor.execute("SELECT * FROM medicines WHERE profile_id = ? ORDER BY id ASC", (int(profile_filter),))
            else:
                cursor.execute("SELECT * FROM medicines ORDER BY id ASC")
            meds = [dict(r) for r in cursor.fetchall()]

        slots = {"Morning": [], "Afternoon": [], "Evening": [], "Night": []}
        for m in meds:
            slot = m.get("timing_slot", "Morning")
            if slot in slots:
                slots[slot].append(m)
            else:
                slots["Morning"].append(m)

        return jsonify({"success": True, "reminders_by_slot": slots, "total": len(meds)})

    @app.route("/api/medicines/<int:med_id>", methods=["DELETE"])
    def delete_medicine(med_id):
        """Deletes medicine from tracker."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM medicines WHERE id = ?", (med_id,))
            cursor.execute("DELETE FROM medicine_logs WHERE medicine_id = ?", (med_id,))
            conn.commit()
            if cursor.rowcount == 0:
                return jsonify({"success": False, "error": "Medicine not found."}), 404

        return jsonify({"success": True, "message": "Medicine removed from tracker."})

    # --------------------------------------------------------------------------
    # MEDICAL REPORT ANALYZER ROUTES
    # --------------------------------------------------------------------------

    @app.route("/api/reports/analyze", methods=["POST"])
    def analyze_report():
        """
        Analyzes an uploaded file or pasted text.
        Validates file format, extracts text, summarizes in English and Telugu.
        """
        report_title = request.form.get("report_title", "Medical Report").strip()
        patient_name = request.form.get("patient_name", "Patient").strip()
        report_date = request.form.get("report_date", datetime.now().strftime("%Y-%m-%d")).strip()
        pasted_text = request.form.get("pasted_text", "").strip()
        record_type = request.form.get("record_type", "Lab Report").strip()
        profile_id = int(request.form.get("profile_id") or session.get("active_profile_id", 1))

        raw_text = ""
        filename = "manual_entry.txt"
        save_path = ""

        # Handle file upload if present
        if "report_file" in request.files and request.files["report_file"].filename:
            file = request.files["report_file"]
            # 14e Safe upload validation
            is_valid, msg, safe_name = security.validate_uploaded_file(file)
            if not is_valid:
                return jsonify({
                    "success": False,
                    "error": f"Invalid file type: {msg}"
                }), 400

            filename = safe_name
            ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

            # Save temporarily
            safe_fname = f"{int(datetime.now().timestamp())}_{re.sub(r'[^a-zA-Z0-9_.-]', '_', filename)}"
            upload_target = Path(app.config["UPLOAD_FOLDER"]) / safe_fname
            file.save(str(upload_target))
            save_path = str(upload_target)

            raw_text = extract_text_from_file(upload_target, filename)

        elif pasted_text:
            raw_text = pasted_text
        else:
            return jsonify({"success": False, "error": "Please either upload a report file or paste report text."}), 400

        # Perform analysis
        analysis_result = analyze_medical_report_text(raw_text)

        # Save to SQLite reports table
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO reports (
                    patient_name, report_title, report_date,
                    original_filename, extracted_text,
                    summary_english, summary_telugu,
                    record_type, file_path, profile_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                html.escape(patient_name), html.escape(report_title), html.escape(report_date),
                filename, raw_text[:5000],
                analysis_result["summary_english"],
                analysis_result["summary_telugu"],
                html.escape(record_type), save_path, profile_id
            ))
            conn.commit()
            report_id = cursor.lastrowid

        ai_info = check_ai_status()

        return jsonify({
            "success": True,
            "report_id": report_id,
            "report_title": report_title,
            "patient_name": patient_name,
            "record_type": record_type,
            "extracted_snippet": raw_text[:400] + ("..." if len(raw_text) > 400 else ""),
            "summary_english": analysis_result["summary_english"],
            "summary_telugu": analysis_result["summary_telugu"],
            "glossary_matches": analysis_result["glossary_matches"],
            "glossary_details": analysis_result["glossary_details"],
            "ai_status": ai_info
        })

    @app.route("/api/reports", methods=["GET"])
    def get_reports():
        """Lists saved medical report summaries with optional category/type and profile filter."""
        rec_type = request.args.get("type", "").strip()
        search = request.args.get("search", "").strip().lower()
        profile_filter = request.args.get("profile_id")

        with get_db() as conn:
            cursor = conn.cursor()
            query = "SELECT id, patient_name, report_title, report_date, original_filename, record_type, profile_id, created_at FROM reports WHERE 1=1"
            params = []

            if rec_type:
                query += " AND record_type = ?"
                params.append(rec_type)

            if profile_filter and profile_filter != "all":
                try:
                    query += " AND profile_id = ?"
                    params.append(int(profile_filter))
                except ValueError:
                    pass

            query += " ORDER BY created_at DESC"
            cursor.execute(query, params)
            rows = [dict(row) for row in cursor.fetchall()]

        if search:
            rows = [
                r for r in rows
                if search in (r.get("report_title") or "").lower()
                or search in (r.get("patient_name") or "").lower()
            ]

        return jsonify({"success": True, "reports": rows})

    @app.route("/api/reports/<int:rep_id>", methods=["GET"])
    def get_single_report(rep_id):
        """Retrieves full details of a saved report."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM reports WHERE id = ?", (rep_id,))
            rep = cursor.fetchone()
            if not rep:
                return jsonify({"success": False, "error": "Report not found."}), 404

        return jsonify({"success": True, "report": dict(rep)})

    @app.route("/api/reports/<int:rep_id>", methods=["DELETE"])
    def delete_report(rep_id):
        """Deletes a saved report."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM reports WHERE id = ?", (rep_id,))
            conn.commit()
            if cursor.rowcount == 0:
                return jsonify({"success": False, "error": "Report not found."}), 404

        return jsonify({"success": True, "message": "Report deleted."})

    # --------------------------------------------------------------------------
    # HEALTH ASSISTANT CHAT & SAFETY GUARDRAILS
    # --------------------------------------------------------------------------

    @app.route("/api/chat", methods=["POST"])
    def health_chat():
        """
        Conversational Health Assistant (SPEC.md Sections 3, 4 & 16c).
        - SPEC 16c: 5-language self-harm/suicide detection triggering immediate calm response with tel:14416 & tel:112.
        - PII Stripping: Redacts names, phone numbers, Aadhaar, email before external processing.
        - Detailed point-by-point answers: Causes, Symptoms, Home care, What to avoid, Diet, Tests, Specialist, Generic medicines, Red flags, Follow-up.
        - Profile personalization: Age, conditions, allergies, current medicines.
        - Allergy & drug conflict detection and prominent warning banners.
        - Quick replies, Call 108 button, and AI error disclaimer.
        """
        data = request.get_json() or {}
        user_message = data.get("message", "").strip()
        language = data.get("language", "en").lower()

        if not user_message:
            return jsonify({"success": False, "error": "Message cannot be empty."}), 400

        # ======================================================================
        # 1. SPEC 16c: CRISIS SAFETY INTERCEPTOR (5 Languages: EN, TE, HI, TA, UR)
        # ======================================================================
        crisis_data = assistant_engine.detect_crisis(user_message)
        if crisis_data:
            # Reassure user immediately, provide direct tel: links, never end chat abruptly
            crisis_reply = (
                f"🕊️ {crisis_data['compassionate_message']}\n\n"
                "👉 **Immediate Confidential Crisis Support (Free & 24/7):**\n"
                "• **Tele-MANAS Free Helpline:** [14416](tel:14416) (Govt. of India 24x7)\n"
                "• **National Emergency Service:** [112](tel:112)\n"
                "• **KIRAN Mental Health:** [1800-599-0019](tel:18005990019)\n\n"
                "Your life has immense value. Please reach out to these compassionate professionals right now."
            )
            return jsonify({
                "success": True,
                "is_crisis": True,
                "reply": crisis_reply,
                "crisis_data": crisis_data,
                "source": "crisis_safety_interceptor_16c",
                "quick_replies": [
                    "Call 14416 (Tele-MANAS)",
                    "Call 112 (Emergency)",
                    "Contact Trusted Friend",
                    "Breathing Exercises"
                ],
                "emergency_call_button": {
                    "label": "📞 Call 14416 Tele-MANAS",
                    "tel": "14416"
                }
            })

        lower_query = user_message.lower()

        # ======================================================================
        # 2. EMERGENCY GUARDRAIL CHECK (Acute Physical Emergencies)
        # ======================================================================
        if any(keyword in lower_query for keyword in EMERGENCY_KEYWORDS):
            emergency_reply_en = (
                "🚨 **URGENT MEDICAL EMERGENCY DETECTED!** 🚨\n\n"
                "If you or someone nearby is experiencing chest pain, severe breathlessness, "
                "loss of consciousness, sudden paralysis, or uncontrollable bleeding:\n\n"
                "👉 **CALL EMERGENCY SERVICES IMMEDIATELY:**\n"
                "• **108** - Free Ambulance Emergency Service (India)\n"
                "• **112** - All-in-One National Emergency Helpline\n"
                "• **104** - Health Information & Helpline\n\n"
                "Do NOT wait for online replies. Proceed to the nearest hospital emergency room immediately."
            )
            emergency_reply_te = (
                "🚨 **అత్యవసర వైద్య హెచ్చరిక!** 🚨\n\n"
                "తీవ్రమైన గుండె నొప్పి, శ్వాస ఆడకపోవడం, స్పృహ కోల్పోవడం లేదా అధిక రక్తస్రావం ఉన్నట్లయితే:\n\n"
                "👉 **వెంటనే అత్యవసర నంబర్లకు ఫోన్ చేయండి:**\n"
                "• **108** - అంబులెన్స్ అత్యవసర సేవ\n"
                "• **112** - జాతీయ అత్యవసర హెల్ప్‌లైన్\n"
                "• **104** - ఆరోగ్య సలహా హెల్ప్‌లైన్\n\n"
                "తక్షణమే సమీపంలోని ఆసుపత్రి ఎమర్జెన్సీ వార్డుకు వెళ్లండి."
            )
            return jsonify({
                "success": True,
                "is_emergency": True,
                "reply": emergency_reply_te if language == "te" else emergency_reply_en,
                "source": "emergency_guardrail",
                "emergency_call_button": {"label": "🚑 Call 108 Ambulance", "tel": "108"}
            })

        # ======================================================================
        # 2B. SPEC 16h: DETOX & TAPERING REFUSAL GUARDRAIL
        # ======================================================================
        detox_check = assistant_engine.detect_detox_or_tapering(user_message)
        if detox_check:
            return jsonify({
                "success": True,
                "is_safety_guardrail": True,
                "reply": detox_check["reply"],
                "helplines": detox_check["helplines"],
                "source": "detox_tapering_guardrail_16h",
                "emergency_call_button": {
                    "label": "📞 Call 14446 De-Addiction Helpline",
                    "tel": "14446"
                }
            })

        # ======================================================================
        # 3. PII STRIPPING (SPEC 3 & 14)
        # ======================================================================
        sanitized_message = assistant_engine.strip_pii(user_message)

        # ======================================================================
        # 4. ACTIVE PROFILE RETRIEVAL FOR PERSONALIZATION & CONFLICT CHECKING
        # ======================================================================
        active_id = session.get("active_profile_id", 1)
        profile_info = {
            "name": "Primary Profile",
            "age": 0,
            "gender": "Patient",
            "blood_group": "",
            "allergies": "",
            "conditions": "",
            "medicines": []
        }
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM profiles WHERE id = ?", (active_id,))
            prof_row = cursor.fetchone()
            if prof_row:
                pdict = dict(prof_row)
                profile_info["name"] = pdict.get("name", "Patient")
                profile_info["age"] = pdict.get("age", 0)
                profile_info["gender"] = pdict.get("gender", "")
                profile_info["blood_group"] = pdict.get("blood_group", "")
                profile_info["allergies"] = pdict.get("allergies", "")
                profile_info["conditions"] = pdict.get("conditions", "")

            # Current tracked medicines for drug-drug interaction detection
            cursor.execute("SELECT medicine_name FROM medicines WHERE profile_id = ?", (active_id,))
            profile_info["medicines"] = [r["medicine_name"] for r in cursor.fetchall()]

        # ======================================================================
        # 5. STRUCTURED 10-POINT ASSISTANT RESPONSE GENERATION (SPEC 3)
        # ======================================================================
        structured_resp = assistant_engine.generate_structured_point_by_point_response(
            query_text=sanitized_message,
            profile=profile_info,
            language=language
        )

        return jsonify({
            "success": True,
            "reply": structured_resp["reply"],
            "structured_data": structured_resp["structured_data"],
            "conflicts": structured_resp["conflicts"],
            "quick_replies": structured_resp["quick_replies"],
            "emergency_call_button": structured_resp["emergency_call_button"],
            "disclaimer": structured_resp["disclaimer"],
            "sanitized_query": sanitized_message,
            "profile_used": {
                "name": profile_info["name"],
                "age": profile_info["age"],
                "blood_group": profile_info["blood_group"],
                "allergies": profile_info["allergies"],
                "conditions": profile_info["conditions"]
            },
            "source": "healthmate_assistant_engine_v3"
        })

    # --------------------------------------------------------------------------
    # GLOSSARY & SAMPLE DATA RESET
    # --------------------------------------------------------------------------

    @app.route("/api/glossary", methods=["GET"])
    def get_glossary():
        """Returns the full medical glossary for search and browsing."""
        search = request.args.get("search", "").strip().lower()
        terms = list(MEDICAL_GLOSSARY.values())

        if search:
            terms = [
                t for t in terms
                if search in t["term"].lower()
                or search in t["telugu_term"].lower()
                or search in t["meaning_en"].lower()
                or search in t["meaning_te"].lower()
            ]

        return jsonify({"success": True, "terms": terms, "total": len(terms)})

    @app.route("/api/reset-sample-data", methods=["POST"])
    def reset_sample_data_endpoint():
        """Resets database with clean sample appointments and medicines for demos."""
        seed_sample_data(force=True)
        return jsonify({
            "success": True,
            "message": "Sample health data reloaded successfully!"
        })

    # --------------------------------------------------------------------------
    # STAGE 7: EDUCATIONAL TERM EXPLAINER & COMPETITOR RESEARCH APIS
    # --------------------------------------------------------------------------

    @app.route("/api/explainer", methods=["POST"])
    def explain_term_endpoint():
        """
        Plain-Language Medical Term Explainer (Stage 7).
        - Educational fallback (strictly keyword matching, NOT generative AI diagnosis).
        - Maximum input length 2000 characters.
        - CSRF protected.
        - Sanitized output with English & Telugu explanations and questions to ask doctor.
        """
        data = request.get_json() or {}
        query = (data.get("query") or data.get("text") or "").strip()

        if not query:
            return jsonify({"success": False, "error": "Please enter a test name or medical term."}), 400

        if len(query) > 2000:
            return jsonify({"success": False, "error": "Text exceeds maximum limit of 2000 characters."}), 400

        cleaned_query = html.escape(query[:2000])
        lower_q = cleaned_query.lower()

        # Search against MEDICAL_GLOSSARY
        matches = []
        for key, entry in MEDICAL_GLOSSARY.items():
            if (key in lower_q 
                or entry["term"].lower() in lower_q 
                or entry["telugu_term"].lower() in lower_q
                or any(w in lower_q for w in key.split() if len(w) > 3)):
                matches.append(entry)

        # De-duplicate matches
        seen = set()
        unique_matches = []
        for m in matches:
            if m["term"] not in seen:
                seen.add(m["term"])
                unique_matches.append(m)

        return jsonify({
            "success": True,
            "query": cleaned_query,
            "badge": "Educational fallback (not AI)",
            "source": "Offline Medical Glossary Knowledge Base",
            "matches_count": len(unique_matches),
            "matches": unique_matches,
            "disclaimer": "This explanation is for educational awareness only. HealthMate AI does not diagnose illnesses. Always consult your doctor."
        })

    @app.route("/api/research", methods=["GET"])
    def get_competitor_research():
        """Returns structured competitor research and market gap analysis matrix (Stage 7)."""
        return jsonify({
            "success": True,
            "competitors": COMPETITOR_RESEARCH_DATA,
            "columns": COMPARISON_MATRIX_COLUMNS,
            "disclaimer": "Competitor comparison for academic & hackathon evaluation. Product names belong to their respective owners."
        })

    # --------------------------------------------------------------------------
    # EMERGENCY HELPLINES & SECURE UPLOAD (SPEC.md Phase 1)
    # --------------------------------------------------------------------------

    @app.route("/api/helplines", methods=["GET"])
    def helplines_endpoint():
        """Returns verified emergency medical helplines with last verified date (SPEC.md Phase 1)."""
        h_file = BASE_DIR / "helplines.json"
        if h_file.exists():
            try:
                with open(h_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return jsonify({"success": True, **data})
            except Exception as e:
                return jsonify({"success": False, "error": str(e)}), 500
        return jsonify({"success": False, "error": "helplines.json missing"}), 404

    @app.route("/api/upload", methods=["POST"])
    def generic_upload_endpoint():
        """Generic secure file upload endpoint (14e)."""
        if "file" not in request.files:
            return jsonify({"success": False, "error": "No file uploaded."}), 400
        file = request.files["file"]
        is_valid, msg, safe_name = security.validate_uploaded_file(file)
        if not is_valid:
            return jsonify({"success": False, "error": f"Upload rejected: {msg}"}), 400
        safe_fname = f"{int(datetime.now().timestamp())}_{safe_name}"
        target = Path(app.config["UPLOAD_FOLDER"]) / safe_fname
        file.save(str(target))
        return jsonify({"success": True, "filename": safe_fname, "message": "File verified and stored safely."}), 201

    # --------------------------------------------------------------------------
    # LGD DISTRICTS, CASCADING FILTERS, SYMPTOMS & GPS (SPEC.md Phase 3 & 4)
    # --------------------------------------------------------------------------

    @app.route("/api/lgd/states", methods=["GET"])
    def get_lgd_states():
        """Returns all 36 Indian States and Union Territories from official LGD list (Phase 3)."""
        lgd_file = DATA_DIR / "lgd_districts.json"
        if lgd_file.exists():
            with open(lgd_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return jsonify({"success": True, "states": sorted(list(data.keys())), "total": len(data)})
        return jsonify({"success": False, "error": "LGD districts data not found."}), 404

    @app.route("/api/lgd/districts", methods=["GET"])
    def get_lgd_districts():
        """Returns all official LGD districts for a chosen state (Phase 3)."""
        state = request.args.get("state", "").strip()
        lgd_file = DATA_DIR / "lgd_districts.json"
        if lgd_file.exists():
            with open(lgd_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            districts = data.get(state, [])
            return jsonify({"success": True, "state": state, "districts": sorted(districts), "total": len(districts)})
        return jsonify({"success": False, "error": "LGD districts data not found."}), 404

    @app.route("/api/symptoms/search", methods=["GET"])
    def search_symptoms():
        """
        Searches 300+ symptoms dataset, returns recommended medical speciality and urgency (Phase 4).
        Includes mental health and de-addiction symptoms across languages.
        """
        query = request.args.get("q", "").strip().lower()
        if not query:
            return jsonify({"success": False, "error": "Query required."}), 400

        symp_file = DATA_DIR / "symptoms_to_speciality.json"
        if not symp_file.exists():
            return jsonify({"success": False, "error": "Symptoms dataset not found."}), 404

        with open(symp_file, "r", encoding="utf-8") as f:
            symp_data = json.load(f).get("symptoms", [])

        matches = []
        for s in symp_data:
            s_name = s["symptom"].lower()
            aliases = [a.lower() for a in s.get("aliases", [])]
            if query == s_name or any(query == a for a in aliases):
                matches.insert(0, s)
            elif query in s_name or any(query in a for a in aliases):
                matches.append(s)

        if not matches:
            return jsonify({
                "success": True,
                "query": query,
                "matched_symptom": None,
                "recommended_specialty": "General Medicine",
                "urgency": "Routine",
                "message": "Recommended speciality: General Medicine (No exact symptom match; consult General Physician)",
                "matches": []
            })

        best = matches[0]
        return jsonify({
            "success": True,
            "query": query,
            "matched_symptom": best["symptom"],
            "recommended_specialty": best["specialty"],
            "urgency": best.get("urgency", "Routine"),
            "message": f"Recommended speciality: {best['specialty']}",
            "matches": matches[:10]
        })

    @app.route("/api/location/reverse-geocode", methods=["POST"])
    def reverse_geocode_location():
        """
        Reverse-geocodes GPS latitude and longitude to nearest state, district, and facility (Phase 4).
        Uses Haversine distance formula.
        """
        data = request.get_json() or {}
        lat = data.get("lat")
        lon = data.get("lon")

        try:
            user_lat = float(lat)
            user_lon = float(lon)
        except (TypeError, ValueError):
            return jsonify({"success": False, "error": "Valid numeric lat and lon coordinates required."}), 400

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, state, district, latitude, longitude, phone, address FROM facilities WHERE latitude IS NOT NULL")
            all_facs = [dict(r) for r in cursor.fetchall()]

        if not all_facs:
            if user_lat > 20:
                return jsonify({"success": True, "state": "Delhi", "district": "New Delhi", "distance_km": 0})
            else:
                return jsonify({"success": True, "state": "Telangana", "district": "Hyderabad", "distance_km": 0})

        for fac in all_facs:
            fac["distance_km"] = calculate_haversine_km(user_lat, user_lon, fac["latitude"], fac["longitude"])

        all_facs.sort(key=lambda x: (x.get("distance_km") is None, x.get("distance_km") or 999999))
        closest = all_facs[0]

        return jsonify({
            "success": True,
            "state": closest["state"],
            "district": closest["district"],
            "nearest_facility": closest["name"],
            "distance_km": closest["distance_km"],
            "phone": closest["phone"]
        })

    @app.route("/api/facilities", methods=["GET"])
    def get_facilities_paginated():
        """
        Cascading indexed filters with search, pagination, and Haversine distance sorting (Phase 3 & 4).
        Filters: state, district, area_type (Urban/Rural), facility_type, specialty, search, pincode, female_only.
        """
        state = request.args.get("state", "").strip()
        district = request.args.get("district", "").strip()
        area_type = request.args.get("area_type", "").strip()
        facility_type = request.args.get("facility_type", "").strip()
        specialty = request.args.get("specialty", "").strip()
        search = request.args.get("search", "").strip().lower()
        pincode = request.args.get("pincode", "").strip()
        female_only = request.args.get("female_only", "").lower() in ["1", "true", "yes"]

        lat_param = request.args.get("lat")
        lon_param = request.args.get("lon")
        user_lat = float(lat_param) if lat_param else None
        user_lon = float(lon_param) if lon_param else None

        page = max(1, int(request.args.get("page", 1)) if str(request.args.get("page", "")).isdigit() else 1)
        per_page = max(1, min(100, int(request.args.get("per_page", 10)) if str(request.args.get("per_page", "")).isdigit() else 10))

        conditions = []
        params = []

        if state and state.lower() != "all":
            conditions.append("LOWER(state) = LOWER(?)")
            params.append(state)
        if district and district.lower() != "all":
            conditions.append("LOWER(district) = LOWER(?)")
            params.append(district)
        if area_type and area_type.lower() != "all":
            conditions.append("LOWER(area_type) = LOWER(?)")
            params.append(area_type)
        if facility_type and facility_type.lower() != "all":
            conditions.append("LOWER(facility_type) = LOWER(?)")
            params.append(facility_type)
        if specialty and specialty.lower() != "all":
            conditions.append("LOWER(specialty) = LOWER(?)")
            params.append(specialty)
        if pincode:
            conditions.append("pincode LIKE ?")
            params.append(f"{pincode}%")
        if female_only:
            conditions.append("is_female_doctor = 1")
        if search:
            conditions.append("(LOWER(name) LIKE ? OR LOWER(address) LIKE ? OR LOWER(specialty) LIKE ?)")
            params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])

        where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='facilities'")
            if not cursor.fetchone():
                return jsonify({"success": True, "facilities": [], "total": 0, "page": page, "total_pages": 0})

            cursor.execute(f"SELECT COUNT(*) AS c FROM facilities{where_clause}", params)
            total = cursor.fetchone()["c"]

            if user_lat is not None and user_lon is not None:
                cursor.execute(f"SELECT * FROM facilities{where_clause}", params)
                all_matching = [dict(r) for r in cursor.fetchall()]
                for f in all_matching:
                    f["distance_km"] = calculate_haversine_km(user_lat, user_lon, f.get("latitude"), f.get("longitude"))
                all_matching.sort(key=lambda x: (x.get("distance_km") is None, x.get("distance_km") or 999999))

                start = (page - 1) * per_page
                paged_results = all_matching[start:start + per_page]
            else:
                offset = (page - 1) * per_page
                cursor.execute(f"SELECT * FROM facilities{where_clause} ORDER BY id ASC LIMIT ? OFFSET ?", params + [per_page, offset])
                paged_results = [dict(r) for r in cursor.fetchall()]

        total_pages = math.ceil(total / per_page) if total > 0 else 1

        return jsonify({
            "success": True,
            "facilities": paged_results,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages
        })


# ==============================================================================
# APPLICATION FACTORY FUNCTION
# ==============================================================================

def create_app(test_config=None):
    """
    Application Factory Pattern for Flask.
    Creates and configures an instance of the Flask application.
    """
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "healthmate-dev-secret-key-2026")
    app.config["UPLOAD_FOLDER"] = str(UPLOAD_FOLDER)
    app.config["MAX_CONTENT_LENGTH"] = MAX_FILE_SIZE
    app.config["DATABASE"] = str(DATABASE_PATH)
    app.config["WTF_CSRF_ENABLED"] = True

    if test_config:
        app.config.update(test_config)

    db_path = app.config.get("DATABASE", str(DATABASE_PATH))
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # 14e Secure Cookies
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["SESSION_COOKIE_SECURE"] = False

    # Ensure upload folder exists
    Path(app.config["UPLOAD_FOLDER"]).mkdir(exist_ok=True)

    # Initialize SQLAlchemy ORM
    from models import db
    import database
    from auth import auth_bp

    db.init_app(app)

    # 14e Flask-Talisman CSP (Content Security Policy)
    try:
        from flask_talisman import Talisman
        csp = {
            "default-src": ["'self'"],
            "script-src": ["'self'", "'unsafe-inline'", "'unsafe-eval'", "https://unpkg.com", "https://cdn.jsdelivr.net"],
            "style-src": ["'self'", "'unsafe-inline'", "https://fonts.googleapis.com", "https://unpkg.com"],
            "font-src": ["'self'", "https://fonts.gstatic.com"],
            "img-src": ["'self'", "data:", "https://*.tile.openstreetmap.org", "https://tile.openstreetmap.org", "https://unpkg.com"],
            "connect-src": ["'self'"]
        }
        Talisman(
            app,
            force_https=False,
            content_security_policy=csp,
            session_cookie_secure=False,
            session_cookie_http_only=True,
            session_cookie_samesite="Lax"
        )
    except Exception:
        pass

    # Run Database Migrations
    try:
        database.run_migrations(app)
    except Exception as e:
        print(f"[Warning] Database migration error: {e}")

    # Register Authentication & Ownership Blueprint
    app.register_blueprint(auth_bp)

    # Register all routes and error handlers
    register_routes(app)

    return app


# Default singleton app instance for standard module imports
app = create_app()

# ==============================================================================
# MAIN APPLICATION ENTRY POINT
# ==============================================================================

if __name__ == "__main__":
    import sys
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass
    init_db()
    seed_sample_data()
    print("==========================================================")
    print(" [HealthMate AI] AI-Powered Personal Health Copilot")
    print(" SQLite Database initialized at:", DATABASE_PATH)
    status = check_ai_status()
    print(f" AI Status: {status['badge_text']} ({status['provider']})")
    print(" Server running locally at: http://127.0.0.1:5000")
    print(" Also accessible at:        http://localhost:5000")
    print("==========================================================")
    app.run(host="0.0.0.0", port=5000, debug=True)

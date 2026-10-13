"""
HealthMate AI - Database & Migration Engine (SPEC.md Phase 1)
Manages ORM initialization and version-tracked schema migrations.
"""

import sqlite3
from datetime import datetime
from pathlib import Path
from flask import Flask
from models import db, User, Profile, AuditLog, Consent, UserSession

# Schema migration definitions
MIGRATIONS = [
    {
        "version": 1,
        "name": "001_initial_phase1_schema",
        "description": "Create base tables: users, profiles, audit_log, consents, user_sessions"
    },
    {
        "version": 2,
        "name": "002_security_indexes",
        "description": "Ensure indices for performance and security lookups"
    }
]

def init_migrations_table(connection: sqlite3.Connection):
    """Creates the schema_migrations tracking table if it doesn't exist."""
    cursor = connection.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    connection.commit()


def get_applied_migrations(connection: sqlite3.Connection):
    """Returns set of applied migration versions."""
    cursor = connection.cursor()
    cursor.execute("SELECT version FROM schema_migrations")
    return {row[0] for row in cursor.fetchall()}


def record_migration(connection: sqlite3.Connection, version: int, name: str, description: str):
    """Records an applied migration in schema_migrations."""
    cursor = connection.cursor()
    cursor.execute("""
        INSERT INTO schema_migrations (version, name, description, applied_at)
        VALUES (?, ?, ?, ?)
    """, (version, name, description, datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")))
    connection.commit()


def run_migrations(app: Flask):
    """
    Executes database migrations inside the Flask application context.
    Creates and validates base tables using SQLAlchemy ORM and records versions.
    """
    with app.app_context():
        db_uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
        # Extract path if sqlite
        if "sqlite:///" in db_uri:
            db_path = db_uri.replace("sqlite:///", "")
            conn = sqlite3.connect(db_path)
            try:
                # Upgrade columns if profiles already existed in legacy DB
                cur = conn.cursor()
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS profiles (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER DEFAULT 1,
                        name TEXT NOT NULL,
                        relationship TEXT NOT NULL,
                        age INTEGER DEFAULT 0,
                        gender TEXT DEFAULT 'Other',
                        blood_group TEXT DEFAULT '',
                        is_default INTEGER DEFAULT 0,
                        emergency_contact_encrypted TEXT DEFAULT '',
                        medical_notes_encrypted TEXT DEFAULT '',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT NULL
                    )
                """)
                cur.execute("PRAGMA table_info(profiles)")
                pcols = [r[1] for r in cur.fetchall()]
                if "user_id" not in pcols:
                    cur.execute("ALTER TABLE profiles ADD COLUMN user_id INTEGER DEFAULT 1")
                if "age" not in pcols:
                    cur.execute("ALTER TABLE profiles ADD COLUMN age INTEGER DEFAULT 0")
                if "gender" not in pcols:
                    cur.execute("ALTER TABLE profiles ADD COLUMN gender TEXT DEFAULT 'Other'")
                if "blood_group" not in pcols:
                    cur.execute("ALTER TABLE profiles ADD COLUMN blood_group TEXT DEFAULT ''")
                if "is_default" not in pcols:
                    cur.execute("ALTER TABLE profiles ADD COLUMN is_default INTEGER DEFAULT 0")
                if "emergency_contact_encrypted" not in pcols:
                    cur.execute("ALTER TABLE profiles ADD COLUMN emergency_contact_encrypted TEXT DEFAULT ''")
                if "medical_notes_encrypted" not in pcols:
                    cur.execute("ALTER TABLE profiles ADD COLUMN medical_notes_encrypted TEXT DEFAULT ''")
                if "updated_at" not in pcols:
                    cur.execute("ALTER TABLE profiles ADD COLUMN updated_at TIMESTAMP DEFAULT NULL")
                conn.commit()
            finally:
                conn.close()

        # Step 2: Create all ORM tables (users, audit_log, consents, user_sessions)
        db.create_all()

        # Step 3: Record migrations and apply indexes
        if "sqlite:///" in db_uri:
            db_path = db_uri.replace("sqlite:///", "")
            conn = sqlite3.connect(db_path)
            try:
                init_migrations_table(conn)
                applied = get_applied_migrations(conn)

                for mig in MIGRATIONS:
                    v = mig["version"]
                    if v not in applied:
                        if v == 2:
                            cur = conn.cursor()
                            cur.execute("CREATE INDEX IF NOT EXISTS idx_audit_created ON audit_log (created_at)")
                            cur.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users (email)")
                            cur.execute("CREATE INDEX IF NOT EXISTS idx_users_mobile ON users (mobile)")
                            conn.commit()

                        record_migration(conn, v, mig["name"], mig["description"])
            finally:
                conn.close()


def get_migration_status(app: Flask):
    """Returns list of migration statuses (applied vs pending)."""
    with app.app_context():
        db_uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
        if "sqlite:///" in db_uri:
            db_path = db_uri.replace("sqlite:///", "")
            conn = sqlite3.connect(db_path)
            try:
                init_migrations_table(conn)
                applied = get_applied_migrations(conn)
                status = []
                for m in MIGRATIONS:
                    status.append({
                        "version": m["version"],
                        "name": m["name"],
                        "applied": m["version"] in applied
                    })
                return status
            finally:
                conn.close()
        return []

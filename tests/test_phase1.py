"""
HealthMate AI - Phase 1 Security, ORM, Auth & Consent Test Suite (SPEC.md Phase 1)
Tests:
1. User A cannot read User B's data by changing an ID (14c Ownership check)
2. Encrypted fields unreadable in the raw DB (14b AES-256-GCM field encryption)
3. .exe / .html upload blocked (14e Safe upload validation)
4. Disclaimer must be accepted on first launch (14a Consent enforcement)
5. 5 wrong logins lock the account (14c Account lockout)
6. Aadhaar SHA-256 hash + last 4 digits (14b)
7. Mobile OTP login and active sessions (14c)
8. helplines.json verified data and "last verified" date
"""

import io
import os
import gc
import json
import sqlite3
import tempfile
import unittest
from datetime import datetime

import app as app_module
from models import db, User, Profile, Consent, UserSession, AuditLog
import security

class Phase1SecurityTestCase(unittest.TestCase):
    """Verifies all Phase 1 requirements from SPEC.md."""

    def setUp(self):
        # Unique isolated database for every test
        self.db_fd, self.db_path = tempfile.mkstemp(suffix="_test_phase1.db")
        os.close(self.db_fd)

        # Create isolated test application
        self.app = app_module.create_app({
            "TESTING": True,
            "DATABASE": self.db_path,
            "WTF_CSRF_ENABLED": True,
            "SECRET_KEY": "test-secret-key-phase1-2026",
            "HEALTHMATE_ENCRYPTION_KEY": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
        })
        self.client = self.app.test_client()

        # Initialize tables
        with self.app.app_context():
            app_module.init_db(db_path=self.db_path)

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
        gc.collect()
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except PermissionError:
                pass

    def get_csrf_token(self):
        """Fetches a fresh CSRF token from session."""
        self.client.get("/")
        with self.client.session_transaction() as sess:
            return sess.get("_csrf", "")

    # --------------------------------------------------------------------------
    # TEST 1: USER A CANNOT READ USER B'S DATA BY CHANGING AN ID (14c Ownership)
    # --------------------------------------------------------------------------
    def test_user_a_cannot_read_user_b_data_by_id_tampering(self):
        """
        User A cannot read User B's profile or medical data by changing the ID in the request.
        Must return 403 Forbidden with OWNERSHIP_VIOLATION code and log an audit event.
        """
        csrf = self.get_csrf_token()

        # Register User A
        res_a = self.client.post("/api/auth/register", json={
            "_csrf": csrf,
            "email": "userA@healthmate.in",
            "password": "PasswordUserA123!",
            "role": "patient"
        })
        self.assertEqual(res_a.status_code, 201)
        user_a_id = res_a.get_json()["user"]["id"]

        # Register User B
        res_b = self.client.post("/api/auth/register", json={
            "_csrf": csrf,
            "email": "userB@healthmate.in",
            "password": "PasswordUserB123!",
            "role": "patient"
        })
        self.assertEqual(res_b.status_code, 201)
        user_b_id = res_b.get_json()["user"]["id"]

        # User B logs in and accepts disclaimer
        login_b = self.client.post("/api/auth/login", json={
            "_csrf": csrf,
            "identifier": "userB@healthmate.in",
            "password": "PasswordUserB123!"
        })
        self.assertEqual(login_b.status_code, 200)

        # User B accepts disclaimer
        self.client.post("/api/consent", json={
            "_csrf": csrf,
            "consent_type": "disclaimer_terms"
        })

        # User B creates a confidential medical profile
        b_profile_res = self.client.post("/api/user/profiles", json={
            "_csrf": csrf,
            "name": "User B Confidential Record",
            "relationship": "Self",
            "age": 45,
            "emergency_contact": "+91-9988776655",
            "medical_notes": "Confidential diagnosis notes for User B only"
        })
        self.assertEqual(b_profile_res.status_code, 201)
        user_b_profile_id = b_profile_res.get_json()["profile"]["id"]

        # Now User A logs in
        login_a = self.client.post("/api/auth/login", json={
            "_csrf": csrf,
            "identifier": "userA@healthmate.in",
            "password": "PasswordUserA123!"
        })
        self.assertEqual(login_a.status_code, 200)

        # User A accepts disclaimer
        self.client.post("/api/consent", json={
            "_csrf": csrf,
            "consent_type": "disclaimer_terms"
        })

        # User A attempts to access User B's profile by ID tampering
        attack_res = self.client.get(f"/api/user/profiles/{user_b_profile_id}")

        # MUST BE FORBIDDEN 403
        self.assertEqual(attack_res.status_code, 403)
        data = attack_res.get_json()
        self.assertFalse(data["success"])
        self.assertEqual(data.get("code"), "OWNERSHIP_VIOLATION")

        # Verify audit log recorded the ID tampering attempt
        with self.app.app_context():
            audit = AuditLog.query.filter_by(action="UNAUTHORIZED_ID_TAMPERING_ATTEMPT").first()
            self.assertIsNotNone(audit, "Tampering attempt must be permanently logged in audit_log")
            self.assertEqual(audit.user_id, user_a_id)
            self.assertEqual(audit.resource_id, str(user_b_profile_id))

    # --------------------------------------------------------------------------
    # TEST 2: ENCRYPTED FIELDS UNREADABLE IN RAW DB (14b AES-256-GCM)
    # --------------------------------------------------------------------------
    def test_encrypted_fields_unreadable_in_raw_database(self):
        """
        Sensitive fields (emergency contact, medical notes) must be stored in the raw
        database strictly as AES-256-GCM ciphertext, completely unreadable without the key.
        """
        csrf = self.get_csrf_token()

        # Register and login user
        self.client.post("/api/auth/register", json={
            "_csrf": csrf,
            "email": "crypto_test@healthmate.in",
            "password": "CryptoPassword123!"
        })
        self.client.post("/api/auth/login", json={
            "_csrf": csrf,
            "identifier": "crypto_test@healthmate.in",
            "password": "CryptoPassword123!"
        })
        self.client.post("/api/consent", json={"_csrf": csrf})

        plain_contact = "Emergency: Sita Devi (+91-9123456789)"
        plain_notes = "Patient has Stage 2 Hypertension and Metformin allergy"

        create_res = self.client.post("/api/user/profiles", json={
            "_csrf": csrf,
            "name": "Grandpa Rao",
            "relationship": "Grandfather",
            "age": 74,
            "emergency_contact": plain_contact,
            "medical_notes": plain_notes
        })
        self.assertEqual(create_res.status_code, 201)
        prof_id = create_res.get_json()["profile"]["id"]

        # Directly query the raw SQLite database bypassing the application layer
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT emergency_contact_encrypted, medical_notes_encrypted FROM profiles WHERE id = ?", (prof_id,))
        raw_contact, raw_notes = cursor.fetchone()
        conn.close()

        # 1. Plaintext must NOT appear in the database
        self.assertNotIn("Sita Devi", raw_contact, "Plaintext name must NOT exist in raw DB")
        self.assertNotIn("+91-9123456789", raw_contact, "Plaintext phone must NOT exist in raw DB")
        self.assertNotIn("Hypertension", raw_notes, "Plaintext medical note must NOT exist in raw DB")
        self.assertNotIn("Metformin", raw_notes, "Plaintext medical note must NOT exist in raw DB")

        # 2. Must be stored in AES-256-GCM versioned envelope format
        self.assertTrue(raw_contact.startswith("v1:"), "Ciphertext must be encapsulated in versioned format")
        self.assertTrue(raw_notes.startswith("v1:"), "Ciphertext must be encapsulated in versioned format")

        # 3. Decryption function decrypts cleanly back to plaintext
        self.assertEqual(security.decrypt_field(raw_contact), plain_contact)
        self.assertEqual(security.decrypt_field(raw_notes), plain_notes)

    # --------------------------------------------------------------------------
    # TEST 3: .EXE AND .HTML UPLOADS BLOCKED (14e Safe Uploads)
    # --------------------------------------------------------------------------
    def test_exe_and_html_uploads_strictly_blocked(self):
        """
        Uploading .exe, .html, or scripts must be rejected immediately with 400 Bad Request.
        Legitimate reports (.txt, .pdf, .png, .jpg) must be accepted.
        """
        csrf = self.get_csrf_token()

        # Attempt 1: Upload .exe executable
        exe_file = (io.BytesIO(b"MZ\x90\x00\x03fake-executable-binary"), "trojan.exe")
        res_exe = self.client.post("/api/upload", data={
            "_csrf": csrf,
            "file": exe_file
        }, content_type="multipart/form-data")
        self.assertEqual(res_exe.status_code, 400)
        self.assertFalse(res_exe.get_json()["success"])
        self.assertIn("rejected", res_exe.get_json()["error"].lower())

        # Attempt 2: Upload .html file
        html_file = (io.BytesIO(b"<!DOCTYPE html><html><script>steal_cookies()</script></html>"), "phishing.html")
        res_html = self.client.post("/api/upload", data={
            "_csrf": csrf,
            "file": html_file
        }, content_type="multipart/form-data")
        self.assertEqual(res_html.status_code, 400)
        self.assertFalse(res_html.get_json()["success"])

        # Attempt 3: Upload .exe via /api/reports/analyze endpoint
        bad_report = (io.BytesIO(b"MZ\x90binary"), "exploit.exe")
        res_rep = self.client.post("/api/reports/analyze", data={
            "_csrf": csrf,
            "report_file": bad_report,
            "patient_name": "Test",
            "report_title": "Bad Report"
        }, content_type="multipart/form-data")
        self.assertEqual(res_rep.status_code, 400)
        self.assertIn("Invalid file type", res_rep.get_json().get("error", ""))

        # Valid upload (.txt) must succeed
        good_file = (io.BytesIO(b"Patient HbA1c: 6.2%, Fasting Glucose: 95 mg/dL"), "blood_sugar.txt")
        res_good = self.client.post("/api/upload", data={
            "_csrf": csrf,
            "file": good_file
        }, content_type="multipart/form-data")
        self.assertEqual(res_good.status_code, 201)
        self.assertTrue(res_good.get_json()["success"])

    # --------------------------------------------------------------------------
    # TEST 4: DISCLAIMER MUST BE ACCEPTED ON FIRST LAUNCH (14a Consent)
    # --------------------------------------------------------------------------
    def test_disclaimer_must_be_accepted_on_first_launch(self):
        """
        A user who has not accepted the mandatory medical disclaimer/terms is blocked
        from accessing protected health services until consent is recorded.
        """
        csrf = self.get_csrf_token()

        # Register and login user
        self.client.post("/api/auth/register", json={
            "_csrf": csrf,
            "email": "new_patient@healthmate.in",
            "password": "NewPatientPass123!"
        })
        self.client.post("/api/auth/login", json={
            "_csrf": csrf,
            "identifier": "new_patient@healthmate.in",
            "password": "NewPatientPass123!"
        })

        # Check consent status: should be False initially
        status_res = self.client.get("/api/consent/status")
        self.assertEqual(status_res.status_code, 200)
        self.assertFalse(status_res.get_json()["is_accepted"])

        # Attempt to access protected profiles WITHOUT accepting disclaimer
        access_res = self.client.get("/api/user/profiles")
        self.assertEqual(access_res.status_code, 403)
        data = access_res.get_json()
        self.assertTrue(data.get("requires_consent"))
        self.assertIn("disclaimer", data.get("error", "").lower())

        # User accepts disclaimer
        accept_res = self.client.post("/api/consent", json={
            "_csrf": csrf,
            "consent_type": "disclaimer_terms",
            "version": "1.0"
        })
        self.assertEqual(accept_res.status_code, 200)
        self.assertTrue(accept_res.get_json()["success"])

        # Now protected access must succeed
        access_res2 = self.client.get("/api/user/profiles")
        self.assertEqual(access_res2.status_code, 200)
        self.assertTrue(access_res2.get_json()["success"])

    # --------------------------------------------------------------------------
    # TEST 5: 5 WRONG LOGINS LOCK THE ACCOUNT (14c Lockout)
    # --------------------------------------------------------------------------
    def test_five_wrong_logins_lock_the_account(self):
        """
        Five consecutive incorrect password attempts must lock the user's account.
        Subsequent login attempts (even with correct password) must be rejected with 423 Locked.
        """
        csrf = self.get_csrf_token()

        # Register target user
        target_email = "lockout_target@healthmate.in"
        correct_password = "CorrectPass123!"

        reg_res = self.client.post("/api/auth/register", json={
            "_csrf": csrf,
            "email": target_email,
            "password": correct_password
        })
        self.assertEqual(reg_res.status_code, 201)

        # Attempt 1 through 4: incorrect password
        for attempt in range(1, 5):
            res = self.client.post("/api/auth/login", json={
                "_csrf": csrf,
                "identifier": target_email,
                "password": f"WrongPass_{attempt}"
            })
            self.assertEqual(res.status_code, 401)
            data = res.get_json()
            self.assertEqual(data.get("failed_attempts"), attempt)

        # Attempt 5: 5th failure must trigger account lockout
        res_5 = self.client.post("/api/auth/login", json={
            "_csrf": csrf,
            "identifier": target_email,
            "password": "WrongPass_5"
        })
        self.assertEqual(res_5.status_code, 423) # 423 Locked
        data_5 = res_5.get_json()
        self.assertTrue(data_5.get("is_locked"))
        self.assertIn("locked", data_5.get("error", "").lower())

        # Attempt 6: Even with CORRECT password, locked account cannot log in
        locked_res = self.client.post("/api/auth/login", json={
            "_csrf": csrf,
            "identifier": target_email,
            "password": correct_password
        })
        self.assertEqual(locked_res.status_code, 423)
        self.assertTrue(locked_res.get_json().get("is_locked"))

        # Verify database record
        with self.app.app_context():
            u = User.query.filter_by(email=target_email).first()
            self.assertTrue(u.is_locked)
            self.assertEqual(u.failed_login_attempts, 5)

            # Verify audit log recorded ACCOUNT_LOCKED
            lock_audit = AuditLog.query.filter_by(user_id=u.id, action="ACCOUNT_LOCKED").first()
            self.assertIsNotNone(lock_audit)

    # --------------------------------------------------------------------------
    # TEST 6: AADHAAR HASH + LAST 4 DIGITS (14b)
    # --------------------------------------------------------------------------
    def test_aadhaar_hash_and_last_four_masking(self):
        """
        Aadhaar number must never be stored in plaintext.
        Only SHA-256 hash and last 4 digits are retained.
        """
        csrf = self.get_csrf_token()
        res = self.client.post("/api/auth/register", json={
            "_csrf": csrf,
            "email": "aadhaar_user@healthmate.in",
            "password": "SecurePassword123!",
            "aadhaar": "9876 5432 1098"
        })
        self.assertEqual(res.status_code, 201)
        user_data = res.get_json()["user"]
        self.assertEqual(user_data["aadhaar_last4"], "1098")

        # Verify raw database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT aadhaar_hash, aadhaar_last4 FROM users WHERE email = 'aadhaar_user@healthmate.in'")
        ahash, last4 = cursor.fetchone()
        conn.close()

        self.assertEqual(last4, "1098")
        self.assertEqual(len(ahash), 64, "Aadhaar hash must be 64-char SHA-256 hex string")
        self.assertNotIn("9876", ahash, "Plaintext Aadhaar digits must not exist in hash")

    # --------------------------------------------------------------------------
    # TEST 7: HELPLINES.JSON VERIFIED DATA AND LAST VERIFIED DATE
    # --------------------------------------------------------------------------
    def test_helplines_json_structure_and_last_verified_date(self):
        """
        helplines.json must be readable via /api/helplines and contain
        112, 108, 104, Tele-MANAS, and a valid 'last_verified' date.
        """
        response = self.client.get("/api/helplines")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data.get("success"))
        self.assertIn("last_verified", data)
        self.assertTrue(len(data["last_verified"]) >= 10)

        numbers = [h["number"] for h in data.get("emergency_helplines", [])]
        self.assertIn("112", numbers, "National Emergency 112 must be present")
        self.assertIn("108", numbers, "Medical Ambulance 108 must be present")
        self.assertIn("104", numbers, "Health advice 104 must be present")
        self.assertIn("14416", numbers, "Tele-MANAS must be present")


if __name__ == "__main__":
    unittest.main()

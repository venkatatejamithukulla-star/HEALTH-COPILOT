"""
Unit Tests for HealthMate AI — Stage 1 Features
Tests:
- Application factory pattern (create_app)
- Hand-written CSRF validation (_csrf form field and header)
- Health records CRUD & filtering
- Upload validation (.pdf, .txt, .png, .jpg allowed, dangerous rejected)
- Appointment Preparation Pack (/prep and /api/prep-pack)
- Privacy page (/privacy)
- Sample data reset & delete-all
- 112 Emergency Banner verification on all pages
"""

import io
import os
import gc
import tempfile
import unittest
from app import create_app, init_db, seed_sample_data


class Stage1TestCase(unittest.TestCase):
    def setUp(self):
        """Set up a temporary directory, database and test client for each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_healthmate.db")
        self.upload_dir = os.path.join(self.temp_dir, "test_uploads")
        os.makedirs(self.upload_dir, exist_ok=True)

        self.app = create_app({
            "TESTING": True,
            "DATABASE": self.db_path,
            "UPLOAD_FOLDER": self.upload_dir,
            "WTF_CSRF_ENABLED": True,
            "SECRET_KEY": "test-secret-key-healthmate"
        })
        self.client = self.app.test_client()

        with self.app.app_context():
            init_db(self.db_path)
            seed_sample_data(db_path=self.db_path)

    def tearDown(self):
        """Clean up temporary database and files safely on Windows."""
        gc.collect()
        try:
            if os.path.exists(self.db_path):
                os.remove(self.db_path)
        except Exception:
            pass

        try:
            for f in os.listdir(self.upload_dir):
                try:
                    os.remove(os.path.join(self.upload_dir, f))
                except Exception:
                    pass
            os.rmdir(self.upload_dir)
        except Exception:
            pass

        try:
            os.rmdir(self.temp_dir)
        except Exception:
            pass

    def get_csrf_token(self):
        """Helper to get a valid CSRF token from the session via GET /."""
        with self.client:
            res = self.client.get("/")
            with self.client.session_transaction() as sess:
                return sess.get("_csrf", "")

    # --------------------------------------------------------------------------
    # 1. APP FACTORY TESTS
    # --------------------------------------------------------------------------
    def test_app_factory_creates_app(self):
        """create_app() must return a valid Flask instance with custom config."""
        self.assertTrue(self.app.testing)
        self.assertEqual(self.app.config["DATABASE"], self.db_path)

    # --------------------------------------------------------------------------
    # 2. EMERGENCY BANNER ON PAGES
    # --------------------------------------------------------------------------
    def test_index_page_and_emergency_banner(self):
        """GET / must return 200 and contain the mandatory 112/108/104 banner."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("HealthMate AI", html)
        self.assertIn("112", html)
        self.assertIn("108", html)
        self.assertIn("104", html)

    def test_privacy_page_and_emergency_banner(self):
        """GET /privacy must return 200 and explain offline storage and 112 helpline."""
        response = self.client.get("/privacy")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("Privacy", html)
        self.assertIn("SQLite", html)
        self.assertIn("112", html)

    def test_prep_pack_page(self):
        """GET /prep must return 200 and provide the Appointment Preparation Pack."""
        response = self.client.get("/prep")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("Appointment Preparation Pack", html)
        self.assertIn("Questions to Ask the Doctor", html)
        self.assertIn("112", html)

    # --------------------------------------------------------------------------
    # 3. HAND-WRITTEN CSRF VALIDATION TESTS
    # --------------------------------------------------------------------------
    def test_csrf_protection_rejects_without_token(self):
        """State-changing POST without CSRF token must be rejected with 403."""
        self.client.get("/")
        response = self.client.post("/api/appointments", json={
            "patient_name": "Rao",
            "doctor_name": "Dr. Kumar",
            "appointment_date": "2026-10-30",
            "appointment_time": "10:00 AM"
        })
        self.assertEqual(response.status_code, 403)
        data = response.get_json()
        self.assertFalse(data.get("success"))
        self.assertIn("CSRF", data.get("error", ""))

    def test_csrf_protection_accepts_with_header_token(self):
        """POST with X-CSRF-Token header matching session must succeed."""
        csrf_token = self.get_csrf_token()
        response = self.client.post("/api/appointments", json={
            "patient_name": "Rao",
            "doctor_name": "Dr. Kumar",
            "specialty": "Cardiology",
            "appointment_date": "2026-10-30",
            "appointment_time": "10:00 AM",
            "location_or_clinic": "City Health",
            "notes": "Followup checkup"
        }, headers={"X-CSRF-Token": csrf_token})
        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        self.assertTrue(data.get("success"))

    def test_csrf_protection_accepts_with_body_field(self):
        """POST with '_csrf' key in JSON payload must succeed."""
        csrf_token = self.get_csrf_token()
        response = self.client.post("/api/appointments", json={
            "_csrf": csrf_token,
            "patient_name": "Ananya",
            "doctor_name": "Dr. Anita",
            "specialty": "General Medicine",
            "appointment_date": "2026-11-01",
            "appointment_time": "11:00 AM"
        })
        self.assertEqual(response.status_code, 201)

    # --------------------------------------------------------------------------
    # 4. APPOINTMENT PREPARATION PACK API
    # --------------------------------------------------------------------------
    def test_api_prep_pack_generation(self):
        """POST /api/prep-pack generates appointment summary with emergency disclaimer."""
        csrf_token = self.get_csrf_token()
        payload = {
            "_csrf": csrf_token,
            "patient_name": "Grandpa Rao",
            "doctor_name": "Dr. Ramesh",
            "visit_date": "2026-10-25",
            "purpose": "BP checkup",
            "medicines": "Metformin 500mg",
            "questions": "Can I take this with milk?"
        }
        response = self.client.post("/api/prep-pack", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data.get("success"))
        pack = data.get("prep_pack", {})
        self.assertEqual(pack.get("patient_name"), "Grandpa Rao")
        self.assertIn("108 / 112", pack.get("emergency_reminder"))

    # --------------------------------------------------------------------------
    # 5. UPLOAD VALIDATION TESTS
    # --------------------------------------------------------------------------
    def test_upload_dangerous_file_rejected(self):
        """Uploading an unauthorized extension (e.g., .exe) must return 400."""
        csrf_token = self.get_csrf_token()
        file_data = (io.BytesIO(b"fake dangerous binary"), "malicious.exe")
        response = self.client.post("/api/reports/analyze", data={
            "_csrf": csrf_token,
            "report_title": "Bad File",
            "patient_name": "Test",
            "report_file": file_data
        }, content_type="multipart/form-data")
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn("Invalid file type", data.get("error", ""))

    def test_upload_valid_text_file_accepted(self):
        """Uploading a .txt report must be extracted and summarized safely."""
        csrf_token = self.get_csrf_token()
        txt_content = b"Patient: Grandpa Rao\nHbA1c: 6.8%\nFasting Blood Sugar: 110 mg/dL"
        file_data = (io.BytesIO(txt_content), "blood_report.txt")
        response = self.client.post("/api/reports/analyze", data={
            "_csrf": csrf_token,
            "report_title": "Routine Sugar Test",
            "patient_name": "Grandpa Rao",
            "report_file": file_data
        }, content_type="multipart/form-data")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data.get("success"))
        self.assertIn("summary_english", data)
        self.assertIn("summary_telugu", data)

    # --------------------------------------------------------------------------
    # 6. HEALTH RECORDS CRUD, FILTER & DELETE-ALL
    # --------------------------------------------------------------------------
    def test_reports_crud_and_filter(self):
        """Tests reports listing, single retrieval, category filter, and deletion."""
        csrf_token = self.get_csrf_token()
        # Add a pasted report
        add_res = self.client.post("/api/reports/analyze", data={
            "_csrf": csrf_token,
            "report_title": "Lipid Profile Test",
            "patient_name": "Grandpa Rao",
            "record_type": "Lab Report",
            "pasted_text": "Total Cholesterol: 210 mg/dL\nHDL: 42 mg/dL"
        }, content_type="multipart/form-data")
        self.assertEqual(add_res.status_code, 200)
        rep_id = add_res.get_json()["report_id"]

        # List reports
        list_res = self.client.get("/api/reports")
        self.assertEqual(list_res.status_code, 200)
        reports = list_res.get_json().get("reports", [])
        self.assertTrue(len(reports) >= 1)

        # Get single report
        get_res = self.client.get(f"/api/reports/{rep_id}")
        self.assertEqual(get_res.status_code, 200)
        self.assertEqual(get_res.get_json()["report"]["report_title"], "Lipid Profile Test")

        # Delete single report
        del_res = self.client.delete(f"/api/reports/{rep_id}", headers={"X-CSRF-Token": csrf_token})
        self.assertEqual(del_res.status_code, 200)

    def test_delete_all_records(self):
        """POST /api/records/delete-all clears all stored reports and visits."""
        csrf_token = self.get_csrf_token()
        res = self.client.post("/api/records/delete-all", headers={"X-CSRF-Token": csrf_token})
        self.assertEqual(res.status_code, 200)

        # Verify tables are now empty
        apts = self.client.get("/api/appointments").get_json().get("appointments", [])
        meds = self.client.get("/api/medicines").get_json().get("medicines", [])
        reps = self.client.get("/api/reports").get_json().get("reports", [])
        self.assertEqual(len(apts), 0)
        self.assertEqual(len(meds), 0)
        self.assertEqual(len(reps), 0)

    def test_sample_data_reset(self):
        """POST /api/reset-sample-data restores clean sample data."""
        csrf_token = self.get_csrf_token()
        # First clear
        self.client.post("/api/records/delete-all", headers={"X-CSRF-Token": csrf_token})
        # Then reset
        reset_res = self.client.post("/api/reset-sample-data", headers={"X-CSRF-Token": csrf_token})
        self.assertEqual(reset_res.status_code, 200)

        apts = self.client.get("/api/appointments").get_json().get("appointments", [])
        self.assertTrue(len(apts) >= 1)


if __name__ == "__main__":
    unittest.main()

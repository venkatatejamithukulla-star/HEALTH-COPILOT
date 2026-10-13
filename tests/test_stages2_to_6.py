"""
Unit Tests for HealthMate AI — Stages 2 to 6 Features
Tests:
- Stage 2: Appointments (purpose, consultation fee, low-cost flag) & Medicine Schedule
- Stage 3: Educational Disease Library (/diseases, /api/diseases, body area filter, search)
- Stage 4: Low-Cost Care Finder (/find-care, /api/care, /api/schemes, female doctor filter)
- Stage 5: Multilingual Support (/api/set-language, /api/translations, session persistence)
- Stage 6: Doctor Sharing Portal (/api/share/create, /doctor-view/<code_str>, /api/doctor-view/<code_str>/note, revoke)
"""

import os
import gc
import json
import tempfile
import unittest
from app import create_app, init_db, seed_sample_data


class Stages2To6TestCase(unittest.TestCase):
    def setUp(self):
        """Set up an isolated temporary database and test client for each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_stages2_to_6.db")
        self.upload_dir = os.path.join(self.temp_dir, "test_uploads")
        os.makedirs(self.upload_dir, exist_ok=True)

        self.app = create_app({
            "TESTING": True,
            "DATABASE": self.db_path,
            "UPLOAD_FOLDER": self.upload_dir,
            "WTF_CSRF_ENABLED": True,
            "SECRET_KEY": "test-secret-stages2to6"
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
            self.client.get("/")
            with self.client.session_transaction() as sess:
                return sess.get("_csrf", "")

    # ==========================================================================
    # STAGE 2: APPOINTMENTS & MEDICINES WITH ENHANCED FIELDS
    # ==========================================================================

    def test_appointments_api_get(self):
        """GET /api/appointments returns list of seeded appointments."""
        res = self.client.get("/api/appointments")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("success"))
        self.assertIsInstance(data.get("appointments"), list)
        self.assertGreater(len(data["appointments"]), 0)

    def test_appointments_api_create_with_new_fields(self):
        """POST /api/appointments creates appointment with purpose, consultation fee, and low-cost flag."""
        csrf = self.get_csrf_token()
        payload = {
            "_csrf": csrf,
            "patient_name": "Sita Devi",
            "doctor_name": "Dr. V. Prasad",
            "specialty": "General Physician",
            "appointment_date": "2026-11-05",
            "appointment_time": "11:00 AM",
            "location_or_clinic": "Primary Health Centre, Ward 4",
            "notes": "Mild knee joint stiffness",
            "purpose": "Routine joint checkup",
            "consultation_fee": "Free",
            "is_low_cost": True
        }
        res = self.client.post("/api/appointments", json=payload)
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertTrue(data.get("success"))
        self.assertIn("id", data)

        # Verify record retrieval
        get_res = self.client.get("/api/appointments")
        apts = get_res.get_json().get("appointments", [])
        created = next((a for a in apts if a["id"] == data["id"]), None)
        self.assertIsNotNone(created)
        self.assertEqual(created["purpose"], "Routine joint checkup")
        self.assertEqual(created["consultation_fee"], "Free")
        self.assertEqual(created["is_low_cost"], 1)

    def test_appointments_api_update_and_delete(self):
        """PATCH updates status and DELETE removes appointment."""
        csrf = self.get_csrf_token()
        # Create an appointment to update/delete
        create_res = self.client.post("/api/appointments", json={
            "_csrf": csrf,
            "patient_name": "Test Patient",
            "doctor_name": "Dr. Test",
            "appointment_date": "2026-12-01",
            "appointment_time": "09:00 AM"
        })
        apt_id = create_res.get_json()["id"]

        # PATCH status
        patch_res = self.client.patch(f"/api/appointments/{apt_id}", json={
            "_csrf": csrf,
            "status": "Completed"
        })
        self.assertEqual(patch_res.status_code, 200)

        # DELETE appointment
        del_res = self.client.delete(f"/api/appointments/{apt_id}", json={
            "_csrf": csrf
        })
        self.assertEqual(del_res.status_code, 200)

    def test_medicines_api_create_and_toggle(self):
        """POST /api/medicines tracks prescribed medicine and toggle updates status."""
        csrf = self.get_csrf_token()
        payload = {
            "_csrf": csrf,
            "patient_name": "Grandpa Rao",
            "medicine_name": "Metformin 500mg",
            "prescribed_dosage": "1 tablet after breakfast",
            "timing_slot": "Morning",
            "frequency": "Daily",
            "doctor_prescribed": "Dr. Ramesh Kumar",
            "instructions": "Take with water",
            "reminder_time": "08:30 AM",
            "pills_left": 20
        }
        res = self.client.post("/api/medicines", json=payload)
        self.assertEqual(res.status_code, 201)
        med_id = res.get_json()["id"]

        # Toggle medicine taken
        toggle_res = self.client.post(f"/api/medicines/{med_id}/toggle-taken", json={"_csrf": csrf})
        self.assertEqual(toggle_res.status_code, 200)
        toggle_data = toggle_res.get_json()
        self.assertTrue(toggle_data.get("success"))

    # ==========================================================================
    # STAGE 3: EDUCATIONAL DISEASE LIBRARY
    # ==========================================================================

    def test_diseases_page_renders_with_emergency_banner(self):
        """GET /diseases renders the disease library page with 112 emergency banner."""
        res = self.client.get("/diseases")
        self.assertEqual(res.status_code, 200)
        html = res.get_data(as_text=True)
        self.assertIn("Educational Disease & Wellness Library", html)
        self.assertIn("112", html)
        self.assertIn("108", html)

    def test_diseases_api_returns_all(self):
        """GET /api/diseases returns all conditions in the library."""
        res = self.client.get("/api/diseases")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("success"))
        self.assertGreaterEqual(data.get("total", 0), 25)

    def test_diseases_api_filter_and_search(self):
        """GET /api/diseases filters by body area and search query."""
        # Filter by body area
        res_area = self.client.get("/api/diseases?area=skin")
        self.assertEqual(res_area.status_code, 200)
        data_area = res_area.get_json()
        for d in data_area["diseases"]:
            self.assertEqual(d["body_area"].lower(), "skin")

        # Search query
        res_search = self.client.get("/api/diseases?search=fever")
        self.assertEqual(res_search.status_code, 200)
        data_search = res_search.get_json()
        self.assertGreater(data_search["total"], 0)

    # ==========================================================================
    # STAGE 4: LOW-COST CARE FINDER & GOVERNMENT SCHEMES
    # ==========================================================================

    def test_find_care_page_renders_with_emergency_banner(self):
        """GET /find-care renders care finder with 112 hotline."""
        res = self.client.get("/find-care")
        self.assertEqual(res.status_code, 200)
        html = res.get_data(as_text=True)
        self.assertIn("Find Nearby Low-Cost Care & Government Schemes", html)
        self.assertIn("112", html)

    def test_care_api_filters(self):
        """GET /api/care supports filtering by district and female doctor."""
        res = self.client.get("/api/care?female_only=1")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("success"))
        for fac in data["facilities"]:
            self.assertTrue(fac["is_female_doctor"])

    def test_schemes_api_returns_schemes(self):
        """GET /api/schemes returns verified government health schemes."""
        res = self.client.get("/api/schemes")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("success"))
        schemes = data.get("schemes", [])
        scheme_names = [s["name"] for s in schemes]
        self.assertTrue(any("Aarogyasri" in name for name in scheme_names))
        self.assertTrue(any("PM-JAY" in name or "Ayushman" in name for name in scheme_names))

    # ==========================================================================
    # STAGE 5: MULTILINGUAL ACCESSIBILITY & TRANSLATIONS
    # ==========================================================================

    def test_set_language_session(self):
        """POST /api/set-language stores language in session."""
        csrf = self.get_csrf_token()
        for lang_code in ["te", "hi", "ta", "en"]:
            res = self.client.post("/api/set-language", json={"_csrf": csrf, "lang": lang_code})
            self.assertEqual(res.status_code, 200)
            self.assertEqual(res.get_json().get("lang"), lang_code)

        # Invalid language code rejected
        bad_res = self.client.post("/api/set-language", json={"_csrf": csrf, "lang": "fr"})
        self.assertEqual(bad_res.status_code, 400)

    def test_translations_api(self):
        """GET /api/translations returns translations dictionary."""
        res = self.client.get("/api/translations")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("success"))
        translations = data.get("translations", {})
        self.assertIn("en", translations)
        self.assertIn("te", translations)
        self.assertIn("hi", translations)
        self.assertIn("ta", translations)

    # ==========================================================================
    # STAGE 6: DOCTOR SHARE PORTAL
    # ==========================================================================

    def test_doctor_share_code_lifecycle(self):
        """Test full share code flow: create, view, add doctor note, and revoke."""
        csrf = self.get_csrf_token()

        # 1. Create Share Code
        create_res = self.client.post("/api/share/create", json={
            "_csrf": csrf,
            "patient_name": "Grandpa Rao",
            "profile_id": 1,
            "shared_records": "all"
        })
        self.assertEqual(create_res.status_code, 201)
        share_data = create_res.get_json()
        code = share_data.get("share_code")
        self.assertTrue(code.startswith("HM-"))

        # 2. View Doctor Portal with Share Code
        view_res = self.client.get(f"/doctor-view/{code}")
        self.assertEqual(view_res.status_code, 200)
        view_html = view_res.get_data(as_text=True)
        self.assertIn("Grandpa Rao", view_html)
        self.assertIn(code, view_html)
        self.assertIn("112", view_html)  # Emergency banner

        # 3. Doctor Adds Clinical Note
        note_res = self.client.post(f"/api/doctor-view/{code}/note", json={
            "_csrf": csrf,
            "doctor_name": "Dr. V. Rao",
            "note": "Patient BP stable at 128/82. Continue regular morning walk and prescribed medicines."
        })
        self.assertEqual(note_res.status_code, 200)
        note_data = note_res.get_json()
        self.assertTrue(note_data.get("success"))

        # Verify note is now on the doctor view page
        view_after_res = self.client.get(f"/doctor-view/{code}")
        self.assertIn("Patient BP stable", view_after_res.get_data(as_text=True))

        # 4. Patient Revokes Share Code
        revoke_res = self.client.post("/api/share/revoke", json={
            "_csrf": csrf,
            "share_code": code
        })
        self.assertEqual(revoke_res.status_code, 200)

        # 5. Viewing Revoked Code Shows Revocation Message
        view_revoked_res = self.client.get(f"/doctor-view/{code}")
        self.assertIn("revoked by the patient", view_revoked_res.get_data(as_text=True))


if __name__ == "__main__":
    unittest.main()

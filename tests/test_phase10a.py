"""
HealthMate AI — Phase 10A Automated Test Suite (SPEC.md Section 12a, 12b, 12c)
Tests:
1. Vitals Tracker (12a): Logging with clinical reference range categorization & acute crisis alerts.
2. Vitals History & Stats (12a): Filtering by type/days, summary statistics (min/max/avg), delete.
3. Vitals Reference Ranges (12a): Clinical metadata endpoint.
4. Prescription Scanner OCR & Extractor (12b): Parsing doctor, medicines, vitals, advice from text.
5. Bulk Save from Scanner (12b): Direct saving of parsed meds to medicines table & vitals to vitals_logs.
6. Emergency Health Card (12c): Unique token generation, QR code data URL, updating directives.
7. Public Emergency View (12c): Paramedic view accessible without login, tel: links, Call 108.
8. Privacy Masking (12c & 16g): Sensitive mental health/wellness records strictly hidden from emergency view.
9. Mobile Lock-Screen Wallpaper Generator (12c): High-contrast 9:16 PNG wallpaper generation.
10. Data Ownership (12a, 12c): Vitals & Emergency Card included in export and cascading account deletion.
"""

import os
import gc
import json
import tempfile
import unittest
from datetime import datetime, timedelta
from app import create_app, init_db, get_db

class Phase10ATestCase(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_phase10a.db")
        self.app = create_app({
            "TESTING": True,
            "DATABASE": self.db_path,
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{self.db_path}",
            "WTF_CSRF_ENABLED": False,
            "SECRET_KEY": "test-secret-phase10a"
        })
        self.client = self.app.test_client()
        with self.app.app_context():
            init_db(self.db_path)

    def tearDown(self):
        gc.collect()
        try:
            if os.path.exists(self.db_path):
                os.remove(self.db_path)
        except Exception:
            pass
        try:
            os.rmdir(self.temp_dir)
        except Exception:
            pass

    # =========================================================================
    # 1. VITALS TRACKER TESTS (SPEC 12a)
    # =========================================================================

    def test_vitals_logging_and_clinical_evaluation(self):
        """SPEC 12a: Test vitals logging with automated clinical evaluations and crisis detection."""
        # 1. Optimal Normal BP
        res_normal = self.client.post("/api/vitals", json={
            "profile_id": 1,
            "vital_type": "bp",
            "value_primary": 118,
            "value_secondary": 76,
            "unit": "mmHg"
        })
        self.assertEqual(res_normal.status_code, 201)
        d_normal = res_normal.get_json()
        self.assertEqual(d_normal["evaluation"]["status"], "normal")
        self.assertFalse(d_normal["evaluation"]["is_crisis"])

        # 2. Stage 1 Hypertension
        res_stage1 = self.client.post("/api/vitals", json={
            "profile_id": 1,
            "vital_type": "bp",
            "value_primary": 134,
            "value_secondary": 84
        })
        self.assertEqual(res_stage1.status_code, 201)
        self.assertEqual(res_stage1.get_json()["evaluation"]["status"], "stage1")

        # 3. Hypertensive Crisis Alert (>=180 or >=120) -> Crisis flag & 108 Alert
        res_crisis = self.client.post("/api/vitals", json={
            "profile_id": 1,
            "vital_type": "bp",
            "value_primary": 195,
            "value_secondary": 125
        })
        self.assertEqual(res_crisis.status_code, 201)
        d_crisis = res_crisis.get_json()
        self.assertEqual(d_crisis["evaluation"]["status"], "crisis")
        self.assertTrue(d_crisis["evaluation"]["is_crisis"])
        self.assertIn("108", d_crisis["evaluation"]["alert_message"])

        # 4. Fasting Blood Glucose (Hypoglycemia < 70 -> Emergency sugar alert)
        res_hypo = self.client.post("/api/vitals", json={
            "profile_id": 1,
            "vital_type": "glucose",
            "value_primary": 58,
            "meal_context": "fasting"
        })
        self.assertEqual(res_hypo.status_code, 201)
        d_hypo = res_hypo.get_json()
        self.assertEqual(d_hypo["evaluation"]["status"], "crisis")
        self.assertTrue(d_hypo["evaluation"]["is_crisis"])
        self.assertIn("15g", d_hypo["evaluation"]["alert_message"])

        # 5. Severe Hypoxia SpO2 (< 90% -> 108 Alert)
        res_spo2 = self.client.post("/api/vitals", json={
            "profile_id": 1,
            "vital_type": "spo2",
            "value_primary": 87
        })
        self.assertEqual(res_spo2.status_code, 201)
        d_spo2 = res_spo2.get_json()
        self.assertEqual(d_spo2["evaluation"]["status"], "crisis")
        self.assertTrue(d_spo2["evaluation"]["is_crisis"])
        self.assertIn("108", d_spo2["evaluation"]["alert_message"])

        # 6. Severe Tachycardia Heart Rate (> 140 bpm -> Emergency alert)
        res_hr = self.client.post("/api/vitals", json={
            "profile_id": 1,
            "vital_type": "heart_rate",
            "value_primary": 152
        })
        self.assertEqual(res_hr.status_code, 201)
        self.assertTrue(res_hr.get_json()["evaluation"]["is_crisis"])

        # 7. High Fever Temperature (> 103°F -> Crisis alert)
        res_temp = self.client.post("/api/vitals", json={
            "profile_id": 1,
            "vital_type": "temperature",
            "value_primary": 104.2
        })
        self.assertEqual(res_temp.status_code, 201)
        self.assertTrue(res_temp.get_json()["evaluation"]["is_crisis"])

        # 8. BMI Calculation (70 kg, 175 cm -> 22.9 Normal)
        res_bmi = self.client.post("/api/vitals", json={
            "profile_id": 1,
            "vital_type": "bmi",
            "value_primary": 70,
            "value_secondary": 175
        })
        self.assertEqual(res_bmi.status_code, 201)
        self.assertEqual(res_bmi.get_json()["evaluation"]["status"], "normal")
        self.assertEqual(res_bmi.get_json()["evaluation"]["bmi_value"], 22.9)

    def test_vitals_summary_history_and_deletion(self):
        """SPEC 12a: Test retrieval of latest summary cards, trend charting history, and delete."""
        # 1. Log multiple readings for Profile 1
        for i, bp_val in enumerate([122, 128, 134, 130]):
            self.client.post("/api/vitals", json={
                "profile_id": 1,
                "vital_type": "bp",
                "value_primary": bp_val,
                "value_secondary": 80,
                "recorded_at": f"2026-10-0{i+1} 10:00:00"
            })

        # 2. GET summary cards for profile 1
        res_sum = self.client.get("/api/vitals?profile_id=1")
        self.assertEqual(res_sum.status_code, 200)
        d_sum = res_sum.get_json()
        self.assertTrue(d_sum["success"])
        self.assertIn("bp", d_sum["latest"])
        self.assertGreaterEqual(d_sum["total_count"], 4)

        # 3. GET trend history filtered by bp
        res_hist = self.client.get("/api/vitals/history?profile_id=1&vital_type=bp&days=30")
        self.assertEqual(res_hist.status_code, 200)
        d_hist = res_hist.get_json()
        self.assertEqual(d_hist["stats"]["count"], len(d_hist["points"]))
        self.assertEqual(d_hist["stats"]["min"], 122.0)
        self.assertEqual(d_hist["stats"]["max"], 134.0)
        self.assertEqual(d_hist["stats"]["latest"], 130.0)

        # 4. Profile isolation check: Profile 4 should not have Profile 1's BP readings
        res_prof4 = self.client.get("/api/vitals/history?profile_id=4&vital_type=bp")
        d_prof4 = res_prof4.get_json()
        for pt in d_prof4["points"]:
            self.assertNotEqual(pt["val"], 134.0)

        # 5. Delete vital reading
        vital_id = d_hist["points"][0]["id"]
        res_del = self.client.delete(f"/api/vitals/{vital_id}?profile_id=1")
        self.assertEqual(res_del.status_code, 200)

        # Verify reading was deleted
        res_after = self.client.get("/api/vitals/history?profile_id=1&vital_type=bp")
        ids_after = [p["id"] for p in res_after.get_json()["points"]]
        self.assertNotIn(vital_id, ids_after)

    def test_vitals_reference_ranges_metadata(self):
        """SPEC 12a: Reference ranges endpoint returns structured clinical thresholds."""
        res = self.client.get("/api/vitals/ranges")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertIn("bp", data["ranges"])
        self.assertIn("glucose_fasting", data["ranges"])
        self.assertIn("spo2", data["ranges"])
        self.assertIn("heart_rate", data["ranges"])

    # =========================================================================
    # 2. PRESCRIPTION & REPORT SCANNER OCR TESTS (SPEC 12b)
    # =========================================================================

    def test_scanner_clinical_extraction(self):
        """SPEC 12b: Test clinical entity parsing from doctor consultation prescription text."""
        sample_prescription = """
        APOLLO HEALTH CITY & CLINIC
        Dr. Ramesh Kumar, MBBS, MD (Cardiology) - Reg No: AP-48291
        Date: 2026-10-12
        Patient: Grandpa Rao | Age: 72 Y | Male
        BP: 135/85 mmHg | Pulse: 76 bpm
        Fasting Glucose: 118 mg/dL | SpO2: 98%

        Rx (Prescription):
        1. Tab. Metformin 500mg - 1-0-1 - After food - 30 days
        2. Tab. Telmisartan 40mg - 1-0-0 - Before food - 30 days
        3. Tab. Atorvastatin 10mg - 0-0-1 - At bedtime - 30 days

        Advice:
        Low sodium diet, maintain daily BP log, review in 4 weeks.
        """

        res = self.client.post("/api/scanner/upload", json={
            "profile_id": 1,
            "raw_text": sample_prescription
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])

        ext = data["extracted"]
        self.assertIn("Dr. Ramesh Kumar", ext["doctor_name"])
        self.assertIn("APOLLO", ext["clinic_name"])
        self.assertEqual(ext["date"], "2026-10-12")

        # Verify parsed medications
        med_names = [m["medicine_name"] for m in ext["medicines"]]
        self.assertTrue(any("Metformin" in name for name in med_names))
        self.assertTrue(any("Telmisartan" in name for name in med_names))
        self.assertTrue(any("Atorvastatin" in name for name in med_names))

        # Verify parsed vitals
        v_types = [v["vital_type"] for v in ext["vitals"]]
        self.assertIn("bp", v_types)
        self.assertIn("heart_rate", v_types)
        self.assertIn("glucose", v_types)
        self.assertIn("spo2", v_types)

    def test_scanner_bulk_saving_to_medicines_and_vitals(self):
        """SPEC 12b: Test bulk saving extracted meds to Medicine Tracker and vitals to Vitals Tracker."""
        # 1. Bulk save medications
        meds_to_save = [
            {
                "medicine_name": "Metformin 500mg",
                "prescribed_dosage": "1 tablet (500mg)",
                "frequency": "1-0-1",
                "timing_slot": "Morning",
                "doctor_prescribed": "Dr. Anita Sharma",
                "instructions": "Take after meal.",
                "duration": "30 days"
            },
            {
                "medicine_name": "Telmisartan 40mg",
                "prescribed_dosage": "1 tablet (40mg)",
                "frequency": "1-0-0",
                "timing_slot": "Morning",
                "doctor_prescribed": "Dr. Anita Sharma",
                "instructions": "Take before meal.",
                "duration": "30 days"
            }
        ]

        res_med = self.client.post("/api/scanner/save-medicines", json={
            "profile_id": 1,
            "medicines": meds_to_save
        })
        self.assertEqual(res_med.status_code, 200)
        d_med = res_med.get_json()
        self.assertEqual(d_med["saved_count"], 2)

        # Verify medicines appear in Medicine Tracker
        res_med_list = self.client.get("/api/medicines?profile_id=1")
        self.assertEqual(res_med_list.status_code, 200)
        med_json = res_med_list.get_json()
        med_list = med_json.get("medicines", []) if isinstance(med_json, dict) else med_json
        med_names = [m["medicine_name"] for m in med_list]
        self.assertIn("Metformin 500mg", med_names)
        self.assertIn("Telmisartan 40mg", med_names)

        # 2. Bulk save vitals
        vitals_to_save = [
            {
                "vital_type": "bp",
                "value_primary": 136,
                "value_secondary": 86,
                "unit": "mmHg"
            },
            {
                "vital_type": "glucose",
                "value_primary": 115,
                "unit": "mg/dL",
                "meal_context": "fasting"
            }
        ]

        res_vit = self.client.post("/api/scanner/save-vitals", json={
            "profile_id": 1,
            "vitals": vitals_to_save
        })
        self.assertEqual(res_vit.status_code, 200)
        self.assertEqual(res_vit.get_json()["saved_count"], 2)

        # Verify vitals appear in vitals history
        res_v_check = self.client.get("/api/vitals/history?profile_id=1&vital_type=bp")
        primary_vals = [p["val"] for p in res_v_check.get_json()["points"]]
        self.assertIn(136.0, primary_vals)

    # =========================================================================
    # 3. EMERGENCY HEALTH CARD & QR TESTS (SPEC 12c)
    # =========================================================================

    def test_emergency_card_token_and_qr_generation(self):
        """SPEC 12c: Emergency card initializes token, generates valid base64 QR code, and updates."""
        # 1. Fetch emergency card data for profile 1
        res = self.client.get("/api/emergency-card/data?profile_id=1")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertTrue(data["card"]["emergency_token"].startswith("emerg_"))
        self.assertTrue(data["qr_data_url"].startswith("data:image/png;base64,"))
        self.assertIn("/emergency-card/", data["public_url"])

        # 2. Update emergency card directives and contacts
        res_up = self.client.post("/api/emergency-card/update", json={
            "profile_id": 1,
            "blood_group": "O+",
            "primary_contact_name": "Ramesh Kumar",
            "primary_contact_relation": "Son",
            "primary_contact_phone": "+91 98765 43210",
            "secondary_contact_name": "Sita Devi",
            "secondary_contact_relation": "Daughter-in-law",
            "secondary_contact_phone": "+91 98765 43211",
            "allergies": "Penicillin (Severe Rash), Sulfa",
            "chronic_conditions": "Type 2 Diabetes, Hypertension",
            "current_medications": "Metformin 500mg, Amlodipine 5mg",
            "emergency_instructions": "Diabetic patient. If unconscious, check blood sugar immediately. Rescue glucose in bag.",
            "organ_donor": 1
        })
        self.assertEqual(res_up.status_code, 200)

        # Verify updated data persists
        res_updated = self.client.get("/api/emergency-card/data?profile_id=1")
        card = res_updated.get_json()["card"]
        self.assertEqual(card["primary_contact_name"], "Ramesh Kumar")
        self.assertEqual(card["organ_donor"], 1)
        self.assertIn("Penicillin", card["allergies"])

    def test_emergency_card_public_view_and_privacy_concealment(self):
        """SPEC 12c & 16g: Public view accessible without login, has tel: links and Call 108, concealing wellness."""
        # Get active token
        res_data = self.client.get("/api/emergency-card/data?profile_id=1")
        token = res_data.get_json()["card"]["emergency_token"]

        # Log sensitive mental health & addiction data
        self.client.post("/api/wellness/mood", json={
            "profile_id": 1,
            "mood_score": 1,
            "mood_label": "Terrible",
            "notes": "Extremely private mental health journal entry"
        })
        self.client.post("/api/wellness/recovery/cravings", json={
            "profile_id": 1,
            "intensity": 9,
            "trigger": "Private alcohol craving event"
        })

        # 1. Access public HTML responder page WITHOUT ANY SESSION OR AUTH
        public_client = self.app.test_client()
        res_pub = public_client.get(f"/emergency-card/{token}")
        self.assertEqual(res_pub.status_code, 200)
        html_content = res_pub.data.decode("utf-8")

        # Must contain life-saving elements
        self.assertIn("FIRST RESPONDER", html_content)
        self.assertIn("🩸", html_content)
        self.assertIn("tel:108", html_content)
        self.assertIn("tel:112", html_content)
        self.assertIn("tel:+91 98765 43210", html_content)

        # STRICT PRIVACY RULE: Sensitive mental health/craving notes MUST BE ZERO
        self.assertNotIn("Extremely private mental health journal entry", html_content)
        self.assertNotIn("Private alcohol craving event", html_content)

        # 2. Check JSON responder endpoint
        res_json = public_client.get(f"/api/emergency-card/public/{token}")
        self.assertEqual(res_json.status_code, 200)
        pub_d = res_json.get_json()["emergency_data"]
        self.assertEqual(pub_d["ambulance_hotline"], "108")
        self.assertNotIn("mood_logs", pub_d)
        self.assertNotIn("cravings", pub_d)

    def test_emergency_wallpaper_png_generator(self):
        """SPEC 12c: Generates downloadable high-contrast 9:16 PNG lock-screen wallpaper."""
        res_data = self.client.get("/api/emergency-card/data?profile_id=1")
        token = res_data.get_json()["card"]["emergency_token"]

        res_wall = self.client.get(f"/api/emergency-card/wallpaper/{token}")
        self.assertEqual(res_wall.status_code, 200)
        self.assertEqual(res_wall.mimetype, "image/png")
        # Verify valid non-empty PNG binary bytes
        self.assertGreater(len(res_wall.data), 5000)
        self.assertTrue(res_wall.data.startswith(b"\x89PNG\r\n\x1a\n"))

    def test_export_and_delete_includes_vitals_and_emergency_card(self):
        """SPEC 12a, 12c: Complete user data export and deletion includes vitals and emergency card."""
        # 1. Export
        res_export = self.client.get("/api/user/export?profile_id=1")
        self.assertEqual(res_export.status_code, 200)
        exp_data = res_export.get_json()
        self.assertIn("vitals", exp_data)
        self.assertIn("emergency_card", exp_data)

        # 2. Delete
        res_del = self.client.post("/api/user/delete", json={"profile_id": 1})
        self.assertEqual(res_del.status_code, 200)

        # Verify SQLite rows deleted
        with get_db(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) AS c FROM vitals_logs WHERE profile_id = 1")
            self.assertEqual(cursor.fetchone()["c"], 0)
            cursor.execute("SELECT COUNT(*) AS c FROM emergency_cards WHERE profile_id = 1")
            self.assertEqual(cursor.fetchone()["c"], 0)


if __name__ == "__main__":
    unittest.main()

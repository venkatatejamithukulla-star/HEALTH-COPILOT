"""
HealthMate AI — Phase 9 Automated Test Suite (SPEC.md Section 16 b, c, d, f, g, h)
Tests:
1. Separate 4-digit PIN lock works (setting, locking, incorrect PIN rejected, correct PIN unlocks).
2. Data hidden from Doctor View by default (mood, screeners, recovery records).
3. Daily mood check-in with encrypted notes & 30-day trend history.
4. PHQ-9, GAD-7, and AUDIT screening with "not a diagnosis" note and crisis detection.
5. De-addiction ordering: 14446 shown first for dependence; 1933 strictly labelled to report drug activity only.
6. Recovery dashboard: days-clean counter, craving log, trigger/coping plan, milestones.
7. Shame-free relapse handler provides compassionate, guilt-free message.
8. Wellness tools enforce NO pain-based coping (somatic sensory grounding instead of rubber band snapping).
9. Detox, dosing, and tapering instructions strictly refused with medical safety explanation.
10. All helplines format as direct dialable tel: links in all responses.
11. Data ownership: Full export (/api/user/export) and cascading account deletion (/api/user/delete).
"""

import os
import gc
import json
import tempfile
import unittest
from datetime import datetime, timedelta
from app import create_app, init_db, get_db

class Phase9MentalHealthRecoveryTestCase(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_phase9.db")
        self.app = create_app({
            "TESTING": True,
            "DATABASE": self.db_path,
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{self.db_path}",
            "WTF_CSRF_ENABLED": False,
            "SECRET_KEY": "test-secret-phase9"
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

    def test_wellness_pin_lock_and_unlock(self):
        """SPEC 16g: Separate 4-digit PIN lock protects mental wellness & recovery records."""
        # 1. Invalid PIN (not 4 digits) rejected
        res_bad = self.client.post("/api/wellness/pin/set", json={"pin": "12", "profile_id": 1})
        self.assertEqual(res_bad.status_code, 400)

        # 2. Set valid 4-digit PIN
        res_ok = self.client.post("/api/wellness/pin/set", json={"pin": "4829", "profile_id": 1})
        self.assertEqual(res_ok.status_code, 200)
        self.assertTrue(res_ok.get_json()["success"])

        # 3. Lock section
        res_lock = self.client.post("/api/wellness/pin/lock", json={"profile_id": 1})
        self.assertEqual(res_lock.status_code, 200)

        # 4. Accessing locked mood history should return HTTP 423
        res_locked_mood = self.client.get("/api/wellness/mood/history?profile_id=1")
        self.assertEqual(res_locked_mood.status_code, 423)
        self.assertTrue(res_locked_mood.get_json()["locked"])

        # 5. Verify incorrect PIN fails with 401
        res_wrong = self.client.post("/api/wellness/pin/verify", json={"pin": "0000", "profile_id": 1})
        self.assertEqual(res_wrong.status_code, 401)

        # 6. Verify correct PIN succeeds and unlocks section
        res_unlock = self.client.post("/api/wellness/pin/verify", json={"pin": "4829", "profile_id": 1})
        self.assertEqual(res_unlock.status_code, 200)

        # 7. Accessing mood history now succeeds
        res_unlocked_mood = self.client.get("/api/wellness/mood/history?profile_id=1")
        self.assertEqual(res_unlocked_mood.status_code, 200)

    def test_wellness_data_hidden_from_doctor_view_by_default(self):
        """SPEC 16g: Mental health, addiction screeners, and recovery logs hidden from Doctor View."""
        # Add mood log and recovery tracker for profile 1
        self.client.post("/api/wellness/mood", json={
            "profile_id": 1,
            "mood_score": 2,
            "notes": "Feeling severe anxiety and past trauma."
        })
        self.client.post("/api/wellness/recovery/start", json={
            "profile_id": 1,
            "target_habit": "Alcohol"
        })

        # Request doctor consultation access
        req_res = self.client.post("/api/doctor/request-patient-access", json={"method": "mobile", "value": "9876543210"})
        demo_otp = req_res.get_json()["demo_otp"]
        prof_id = req_res.get_json()["profile_id"]

        v_res = self.client.post("/api/doctor/verify-patient-otp", json={
            "method": "mobile",
            "profile_id": prof_id,
            "otp": demo_otp
        })
        token = v_res.get_json()["session_token"]

        # View doctor consultation page
        doc_view = self.client.get(f"/doctor/patient-view/{token}")
        self.assertEqual(doc_view.status_code, 200)
        html = doc_view.get_data(as_text=True)

        # Assert mental wellness private records are NOT rendered
        self.assertNotIn("Feeling severe anxiety and past trauma", html)
        self.assertNotIn("target_habit", html)
        self.assertIn("Sensitive mental health and substance use records are masked by default", html)

    def test_daily_mood_checkin_and_trend_history(self):
        """SPEC 16b: Daily mood check-in with AES-256 encrypted personal notes and trend chart."""
        post_res = self.client.post("/api/wellness/mood", json={
            "profile_id": 1,
            "mood_score": 4,
            "energy_level": 4,
            "sleep_hours": 8.0,
            "tags": ["Work", "Exercise"],
            "notes": "Felt grounded and walked for 30 minutes in the morning."
        })
        self.assertEqual(post_res.status_code, 201)
        self.assertTrue(post_res.get_json()["success"])

        # Check raw database: note must be encrypted (starts with 'v1:')
        with self.app.app_context():
            with get_db(self.db_path) as conn:
                cur = conn.cursor()
                cur.execute("SELECT notes_encrypted FROM mood_logs WHERE profile_id = 1")
                row = cur.fetchone()
                self.assertIsNotNone(row)
                self.assertTrue(row["notes_encrypted"].startswith("v1:"))
                self.assertNotIn("Felt grounded and walked", row["notes_encrypted"])

        # Fetch history via API: decrypts note and computes trend
        hist_res = self.client.get("/api/wellness/mood/history?profile_id=1")
        self.assertEqual(hist_res.status_code, 200)
        hdata = hist_res.get_json()
        self.assertTrue(hdata["success"])
        self.assertEqual(hdata["total_days"], 1)
        self.assertEqual(hdata["average_mood"], 4.0)
        self.assertEqual(hdata["entries"][0]["notes"], "Felt grounded and walked for 30 minutes in the morning.")

    def test_clinical_screeners_phq9_gad7_audit(self):
        """SPEC 16b: PHQ-9, GAD-7, and WHO AUDIT with 'not a diagnosis' note and crisis detection."""
        # 1. PHQ-9 with suicidal ideation on Question 9 (score > 0)
        phq_res = self.client.post("/api/wellness/screeners", json={
            "profile_id": 1,
            "screener_type": "PHQ-9",
            "answers": [1, 2, 1, 1, 0, 1, 1, 0, 2] # Q9 = 2
        })
        self.assertEqual(phq_res.status_code, 201)
        phq_data = phq_res.get_json()
        self.assertTrue(phq_data["not_a_diagnosis"])
        self.assertTrue(phq_data["crisis_flag"])
        self.assertIn("Tele-MANAS", phq_data["guidance_summary"])

        # 2. GAD-7 Moderate Anxiety
        gad_res = self.client.post("/api/wellness/screeners", json={
            "profile_id": 1,
            "screener_type": "GAD-7",
            "answers": [2, 2, 2, 1, 1, 2, 1] # Total = 11
        })
        self.assertEqual(gad_res.status_code, 201)
        gad_data = gad_res.get_json()
        self.assertEqual(gad_data["total_score"], 11)
        self.assertEqual(gad_data["severity_level"], "Moderate anxiety symptoms")
        self.assertTrue(gad_data["not_a_diagnosis"])

        # 3. WHO AUDIT with high score (Zone IV)
        audit_res = self.client.post("/api/wellness/screeners", json={
            "profile_id": 1,
            "screener_type": "AUDIT",
            "answers": [3, 3, 3, 3, 2, 2, 2, 2, 2, 2] # Total = 24
        })
        self.assertEqual(audit_res.status_code, 201)
        audit_data = audit_res.get_json()
        self.assertEqual(audit_data["total_score"], 24)
        self.assertEqual(audit_data["severity_level"], "Zone IV: Possible alcohol dependence")
        # SPEC 16h requirements:
        self.assertIn("14446", audit_data["guidance_summary"])
        self.assertIn("1933 is strictly to report illegal drug activity", audit_data["guidance_summary"])

    def test_recovery_dashboard_milestones_and_cravings(self):
        """SPEC 16b: Recovery tracker days clean, milestone badges, craving logging."""
        # 1. Start recovery tracker
        start_res = self.client.post("/api/wellness/recovery/start", json={
            "profile_id": 1,
            "target_habit": "Alcohol"
        })
        self.assertEqual(start_res.status_code, 201)

        # 2. Get recovery dashboard
        rec_res = self.client.get("/api/wellness/recovery?profile_id=1")
        self.assertEqual(rec_res.status_code, 200)
        rec_data = rec_res.get_json()
        self.assertIsNotNone(rec_data["tracker"])
        self.assertEqual(rec_data["tracker"]["target_habit"], "Alcohol")
        self.assertGreaterEqual(len(rec_data["tracker"]["milestones"]), 5)

        # 3. Log a craving
        crav_res = self.client.post("/api/wellness/recovery/cravings", json={
            "profile_id": 1,
            "craving_intensity": 7,
            "trigger_description": "Saw old friends drinking",
            "coping_strategy_used": "5-4-3-2-1 Sensory Grounding"
        })
        self.assertEqual(crav_res.status_code, 201)

        # 4. Add trigger coping plan
        plan_res = self.client.post("/api/wellness/recovery/coping-plan", json={
            "profile_id": 1,
            "trigger_name": "Friday late evening stress",
            "coping_action": "Attend online AA meeting or call mentor"
        })
        self.assertEqual(plan_res.status_code, 201)

    def test_shame_free_relapse_handler(self):
        """SPEC 16b: Compassionate shame-free relapse workflow."""
        self.client.post("/api/wellness/recovery/start", json={"profile_id": 1, "target_habit": "Alcohol"})
        res = self.client.post("/api/wellness/recovery/reset", json={"profile_id": 1})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        # Must contain non-punitive, compassionate message
        self.assertIn("A slip is not a failure", data["message"])
        self.assertIn("recovery is not a straight line", data["message"])
        self.assertIn("14446", data["helplines"]["de_addiction"])

    def test_no_pain_based_coping_enforced(self):
        """SPEC 16f: Enforce evidence-based somatic regulation over pain-based distractions."""
        res = self.client.post("/api/wellness/recovery/cravings", json={
            "profile_id": 1,
            "craving_intensity": 8,
            "trigger_description": "Extreme urge",
            "coping_strategy_used": "Rubber band snapping on wrist"
        })
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        # Should sanitize away pain-based coping and offer evidence-based somatic grounding
        self.assertIn("Somatic", data["coping_strategy"])
        self.assertIn("pain-based", data["clinical_notice"].lower())

    def test_detox_and_tapering_strictly_refused(self):
        """SPEC 16h: Strictly refuses to provide detox or tapering instructions."""
        # 1. Asking for home detox
        chat1 = self.client.post("/api/chat", json={
            "message": "Can you give me a detox protocol to stop drinking alcohol at home?"
        })
        self.assertEqual(chat1.status_code, 200)
        data1 = chat1.get_json()
        self.assertTrue(data1.get("is_safety_guardrail"))
        self.assertIn("strictly never provides detox protocols", data1["reply"])
        self.assertIn("14446", data1["reply"]) # De-addiction helpline shown first
        self.assertIn("1933", data1["reply"]) # 1933 labelled properly
        self.assertIn("report illegal drug activity", data1["reply"])

        # 2. Asking for tapering schedule
        chat2 = self.client.post("/api/chat", json={
            "message": "Give me a tapering schedule to taper off alprazolam doses."
        })
        self.assertEqual(chat2.status_code, 200)
        data2 = chat2.get_json()
        self.assertTrue(data2.get("is_safety_guardrail"))
        self.assertIn("tapering schedules", data2["reply"])

    def test_emergency_helplines_direct_dialable(self):
        """SPEC 16h: All helplines format as active direct-dialable tel: links."""
        res = self.client.get("/wellness")
        self.assertEqual(res.status_code, 200)
        html = res.get_data(as_text=True)

        self.assertIn('href="tel:108"', html)
        self.assertIn('href="tel:112"', html)
        self.assertIn('href="tel:14446"', html)
        self.assertIn('href="tel:14416"', html)

    def test_data_ownership_export_and_deletion(self):
        """SPEC 16g: Complete user data export and cascading account deletion."""
        # Record some data
        self.client.post("/api/wellness/mood", json={"profile_id": 1, "mood_score": 5, "notes": "Private joy"})
        self.client.post("/api/wellness/recovery/start", json={"profile_id": 1, "target_habit": "Nicotine"})

        # Export data
        exp_res = self.client.get("/api/user/export?profile_id=1")
        self.assertEqual(exp_res.status_code, 200)
        exp_data = exp_res.get_json()
        self.assertTrue(exp_data["success"])
        self.assertIn("wellness", exp_data)
        self.assertEqual(len(exp_data["wellness"]["mood_logs"]), 1)
        self.assertEqual(exp_data["wellness"]["mood_logs"][0]["notes"], "Private joy")

        # Delete data
        del_res = self.client.post("/api/user/delete", json={"profile_id": 1})
        self.assertEqual(del_res.status_code, 200)
        self.assertTrue(del_res.get_json()["success"])

        # Verify raw tables are empty
        with self.app.app_context():
            with get_db(self.db_path) as conn:
                cur = conn.cursor()
                cur.execute("SELECT COUNT(*) AS c FROM mood_logs WHERE profile_id = 1")
                self.assertEqual(cur.fetchone()["c"], 0)
                cur.execute("SELECT COUNT(*) AS c FROM recovery_trackers WHERE profile_id = 1")
                self.assertEqual(cur.fetchone()["c"], 0)

if __name__ == "__main__":
    unittest.main()

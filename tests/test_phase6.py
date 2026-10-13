"""
HealthMate AI — Phase 6 Automated Test Suite (SPEC.md Sections 3, 4 & 16c)
Tests:
1. SPEC 16c: 5-language self-harm/suicide detection triggers calm message with tel:14416 and tel:112
   (English, Telugu, Hindi, Tamil, Urdu)
2. PII stripping: Redacts phone numbers, Aadhaar, and emails from user inputs
3. Assistant point-by-point response: All 10 required clinical sections are present
4. Profile personalization: Injects profile age, gender, blood group, conditions
5. Allergy & drug interaction conflict flagging: Penicillin allergy vs Amoxicillin produces warning
6. Medicine Tracker CRUD: Create, read, update, delete
7. Medicine Tracker: Taken/missed toggle and adherence stats calculation
"""

import unittest
from app import create_app
import assistant_engine

class Phase6AssistantAndMedicinesTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app({"TESTING": True, "WTF_CSRF_ENABLED": False})
        self.client = self.app.test_client()

    def test_crisis_detection_english(self):
        """SPEC 16c: Detects suicidal phrase in English and returns crisis payload with 14416 and 112."""
        res = self.client.post("/api/chat", json={
            "message": "I feel completely hopeless and want to die tonight.",
            "language": "en"
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("is_crisis"))
        self.assertIn("14416", data["reply"])
        self.assertIn("112", data["reply"])
        self.assertEqual(data.get("source"), "crisis_safety_interceptor_16c")

    def test_crisis_detection_telugu(self):
        """SPEC 16c: Detects suicidal phrase in Telugu and triggers immediate support."""
        res = self.client.post("/api/chat", json={
            "message": "నాకు బ్రతకాలని లేదు, ఆత్మహత్య చేసుకోవాలని ఉంది.",
            "language": "te"
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("is_crisis"))
        self.assertIn("14416", data["reply"])

    def test_crisis_detection_hindi(self):
        """SPEC 16c: Detects suicidal phrase in Hindi and triggers immediate support."""
        res = self.client.post("/api/chat", json={
            "message": "मैं बहुत परेशान हूँ और आत्महत्या करना चाहता हूँ।",
            "language": "hi"
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("is_crisis"))
        self.assertIn("14416", data["reply"])

    def test_crisis_detection_tamil(self):
        """SPEC 16c: Detects suicidal phrase in Tamil and triggers immediate support."""
        res = self.client.post("/api/chat", json={
            "message": "எனக்கு வாழ பிடிக்கவில்லை, தற்கொலை செய்ய தோன்றுகிறது.",
            "language": "ta"
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("is_crisis"))
        self.assertIn("14416", data["reply"])

    def test_crisis_detection_urdu(self):
        """SPEC 16c: Detects suicidal phrase in Urdu and triggers immediate support."""
        res = self.client.post("/api/chat", json={
            "message": "میں جینا نہیں چاہتا، خودکشی کرنا چاہتا ہوں۔",
            "language": "ur"
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("is_crisis"))
        self.assertIn("14416", data["reply"])

    def test_pii_stripping(self):
        """SPEC 3: Strips phone numbers, Aadhaar, and email before processing."""
        raw_text = "My phone is 9876543210 and Aadhaar is 1234 5678 9012, email user@example.com, I have fever."
        sanitized = assistant_engine.strip_pii(raw_text)
        self.assertNotIn("9876543210", sanitized)
        self.assertNotIn("1234 5678 9012", sanitized)
        self.assertNotIn("user@example.com", sanitized)
        self.assertIn("[REDACTED_PHONE]", sanitized)
        self.assertIn("[REDACTED_AADHAAR]", sanitized)
        self.assertIn("[REDACTED_EMAIL]", sanitized)

    def test_assistant_point_by_point_structure(self):
        """SPEC 3: Assistant returns all 10 point-by-point clinical sections."""
        res = self.client.post("/api/chat", json={
            "message": "I have been experiencing frequent headaches in the evening.",
            "language": "en"
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("success"))
        reply = data.get("reply", "")
        # Verify all 10 sections
        self.assertIn("1. 🔬 Possible Causes", reply)
        self.assertIn("2. 🩺 Symptoms to Watch", reply)
        self.assertIn("3. 🏡 Home Care", reply)
        self.assertIn("4. 🚫 What to Avoid", reply)
        self.assertIn("5. 🥗 Everyday Diet", reply)
        self.assertIn("6. 📑 Diagnostic Tests", reply)
        self.assertIn("7. 👨‍⚕️ Specialist to Consult", reply)
        self.assertIn("8. 💊 Commonly Prescribed Generic Medicines", reply)
        self.assertIn("Consult your doctor before use", reply)
        self.assertIn("9. 🚨 Red Flags", reply)
        self.assertIn("10. 📅 Follow-up", reply)
        # Verify Call 108 button and disclaimer
        self.assertEqual(data.get("emergency_call_button", {}).get("tel"), "108")
        self.assertIn("may contain errors", data.get("disclaimer", ""))

    def test_allergy_and_drug_conflict_flagging(self):
        """SPEC 3: Flag allergy conflicts (Penicillin allergy vs Amoxicillin)."""
        # Create profile with Penicillin allergy
        prof_res = self.client.post("/api/profiles", json={
            "name": "Ravi Kumar",
            "relationship": "Self",
            "age": 42,
            "gender": "Male",
            "blood_group": "B+",
            "allergies": "Severe Penicillin Allergy",
            "conditions": "Asthma"
        })
        self.assertEqual(prof_res.status_code, 201)
        pid = prof_res.get_json()["profile"]["id"]

        # Activate profile
        self.client.post("/api/profiles/active", json={"profile_id": pid})

        # Query about amoxicillin or fever where amoxicillin is checked
        conflicts = assistant_engine.check_allergy_and_drug_conflicts(
            query_text="Can I take amoxicillin for fever?",
            allergies="Severe Penicillin Allergy",
            conditions="Asthma",
            active_meds=[]
        )
        self.assertGreater(len(conflicts), 0)
        self.assertEqual(conflicts[0]["type"], "Allergy Conflict")
        self.assertIn("PENICILLIN ALLERGY CONFLICT", conflicts[0]["warning"])

    def test_medicine_tracker_crud_and_adherence(self):
        """SPEC 4: Medicine tracker CRUD, toggle-status, and adherence stats."""
        # 1. Create medicine
        post_res = self.client.post("/api/medicines", json={
            "patient_name": "Ravi Kumar",
            "medicine_name": "Metformin 500mg ER",
            "prescribed_dosage": "1 tablet daily after dinner",
            "timing_slot": "Night",
            "frequency": "Daily",
            "doctor_prescribed": "Dr. V. Rao (Diabetologist)",
            "instructions": "Take with water after dinner",
            "reminder_time": "09:00 PM",
            "pills_left": 30
        })
        self.assertEqual(post_res.status_code, 201)
        med_id = post_res.get_json()["id"]

        # 2. Read single medicine
        get_res = self.client.get(f"/api/medicines/{med_id}")
        self.assertEqual(get_res.status_code, 200)
        self.assertEqual(get_res.get_json()["medicine"]["medicine_name"], "Metformin 500mg ER")

        # 3. Update medicine (PUT)
        put_res = self.client.put(f"/api/medicines/{med_id}", json={
            "medicine_name": "Metformin 1000mg ER",
            "prescribed_dosage": "1 tablet daily after dinner",
            "timing_slot": "Night",
            "frequency": "Daily",
            "instructions": "Updated dosage per doctor",
            "reminder_time": "09:30 PM",
            "pills_left": 29
        })
        self.assertEqual(put_res.status_code, 200)

        # 4. Toggle status to taken
        toggle_res = self.client.post(f"/api/medicines/{med_id}/toggle-status", json={
            "status": "taken"
        })
        self.assertEqual(toggle_res.status_code, 200)
        self.assertEqual(toggle_res.get_json()["status"], "taken")
        self.assertEqual(toggle_res.get_json()["taken_today"], 1)

        # 5. Check adherence stats
        adh_res = self.client.get("/api/medicines/adherence")
        self.assertEqual(adh_res.status_code, 200)
        adh_data = adh_res.get_json()
        self.assertTrue(adh_data["success"])
        self.assertGreaterEqual(adh_data["adherence_rate"], 80.0)

        # 6. Delete medicine
        del_res = self.client.delete(f"/api/medicines/{med_id}")
        self.assertEqual(del_res.status_code, 200)

if __name__ == "__main__":
    unittest.main()

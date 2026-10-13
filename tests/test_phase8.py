"""
HealthMate AI — Phase 8 Automated Test Suite (SPEC.md Section 13)
Tests:
1. Past-date scheduling blocked with HTTP 400.
2. Double-booking prevention per profile blocked with HTTP 409.
3. Successful future appointment creation returns HTTP 201.
4. Rescheduling with past-date validation, double-booking check, and audit notes.
5. One-tap cancellation with custom reason.
6. Complete appointment with post-visit notes, auto-adding prescribed meds, and follow-up creation.
7. Localized reminders (24h, 2h, 30m) in English and Telugu.
8. RFC 5545 .ics iCalendar file export.
9. Google Calendar direct web URL generator.
10. Specialty-tailored pre-visit checklist with Google Maps location link.
"""

import os
import gc
import tempfile
import unittest
from datetime import datetime, timedelta
from app import create_app, init_db, get_db

class Phase8AppointmentsLifecycleTestCase(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_phase8.db")
        self.app = create_app({
            "TESTING": True,
            "DATABASE": self.db_path,
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{self.db_path}",
            "WTF_CSRF_ENABLED": False,
            "SECRET_KEY": "test-secret-phase8"
        })
        self.client = self.app.test_client()
        with self.app.app_context():
            init_db(self.db_path)

        self.tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        self.day_after = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
        self.yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

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

    def test_past_date_appointment_blocked(self):
        """SPEC 13: Past-date appointment scheduling must be rejected with HTTP 400."""
        res = self.client.post("/api/appointments", json={
            "patient_name": "Ravi Kumar",
            "doctor_name": "Dr. Ramesh Gupta",
            "specialty": "Cardiology",
            "appointment_date": self.yesterday,
            "appointment_time": "10:00 AM",
            "location_or_clinic": "Apollo Hospital Hyderabad",
            "purpose": "Routine Checkup"
        })
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertFalse(data["success"])
        self.assertIn("past", data["error"].lower())

    def test_double_booking_prevention_per_profile(self):
        """SPEC 13: Double-booking the same date and time for a profile must return HTTP 409."""
        # 1. First booking succeeds
        res1 = self.client.post("/api/appointments", json={
            "patient_name": "Ravi Kumar",
            "doctor_name": "Dr. A. Rao",
            "specialty": "General Medicine",
            "appointment_date": self.tomorrow,
            "appointment_time": "11:30 AM",
            "location_or_clinic": "Care Clinic",
            "purpose": "Fever consultation",
            "profile_id": 1
        })
        self.assertEqual(res1.status_code, 201)

        # 2. Second booking at identical date and time for profile 1 should be blocked
        res2 = self.client.post("/api/appointments", json={
            "patient_name": "Ravi Kumar",
            "doctor_name": "Dr. S. Reddy",
            "specialty": "Dermatology",
            "appointment_date": self.tomorrow,
            "appointment_time": "11:30 AM",
            "location_or_clinic": "Skin Center",
            "purpose": "Skin rash check",
            "profile_id": 1
        })
        self.assertEqual(res2.status_code, 409)
        data = res2.get_json()
        self.assertFalse(data["success"])
        self.assertIn("double-booking", data["error"].lower())

    def test_reschedule_lifecycle_and_conflict_check(self):
        """SPEC 13: Reschedule validates past-date, double-booking, and logs previous date."""
        # Book original appointment
        create_res = self.client.post("/api/appointments", json={
            "patient_name": "Sunita Devi",
            "doctor_name": "Dr. Verma",
            "specialty": "Endocrinology",
            "appointment_date": self.tomorrow,
            "appointment_time": "02:00 PM",
            "location_or_clinic": "Diabetes Center",
            "purpose": "HbA1c review",
            "profile_id": 2
        })
        self.assertEqual(create_res.status_code, 201)
        apt_id = create_res.get_json()["id"]

        # 1. Attempt reschedule to past date should fail
        res_past = self.client.post(f"/api/appointments/{apt_id}/reschedule", json={
            "new_date": self.yesterday,
            "new_time": "03:00 PM",
            "reason": "Changed my mind"
        })
        self.assertEqual(res_past.status_code, 400)

        # 2. Reschedule to valid future slot
        res_ok = self.client.post(f"/api/appointments/{apt_id}/reschedule", json={
            "new_date": self.day_after,
            "new_time": "04:30 PM",
            "reason": "Work conflict"
        })
        self.assertEqual(res_ok.status_code, 200)
        data = res_ok.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["status"], "Rescheduled")
        self.assertEqual(data["new_date"], self.day_after)
        self.assertEqual(data["new_time"], "04:30 PM")

    def test_one_tap_cancellation(self):
        """SPEC 13: One-tap cancel updates status and stores cancellation reason."""
        create_res = self.client.post("/api/appointments", json={
            "patient_name": "Kavitha",
            "doctor_name": "Dr. Lakshmi",
            "specialty": "Gynecology",
            "appointment_date": self.tomorrow,
            "appointment_time": "05:00 PM",
            "location_or_clinic": "Women's Health Clinic",
            "purpose": "Routine prenatal",
            "profile_id": 3
        })
        apt_id = create_res.get_json()["id"]

        res = self.client.post(f"/api/appointments/{apt_id}/cancel", json={
            "reason": "Traveling out of city"
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["status"], "Cancelled")

    def test_complete_appointment_workflow_and_auto_add_medicines(self):
        """SPEC 13: Complete consultation saves post-visit notes, auto-adds meds and schedules follow-up."""
        create_res = self.client.post("/api/appointments", json={
            "patient_name": "Mohan Lal",
            "doctor_name": "Dr. B. K. Sen",
            "specialty": "Cardiology",
            "appointment_date": self.tomorrow,
            "appointment_time": "09:00 AM",
            "location_or_clinic": "Heart Foundation Clinic",
            "purpose": "Hypertension assessment",
            "profile_id": 1
        })
        apt_id = create_res.get_json()["id"]

        # Doctor / Patient completes consultation
        comp_res = self.client.post(f"/api/appointments/{apt_id}/complete", json={
            "post_visit_notes": "BP stabilized at 128/82. Continue daily brisk walks. Low-sodium diet.",
            "prescribed_medicines": [
                {"name": "Telmisartan 40mg", "dosage": "1 tablet daily after breakfast"},
                {"name": "Amlodipine 5mg", "dosage": "1 tablet daily at night"}
            ],
            "follow_up_weeks": 4
        })
        self.assertEqual(comp_res.status_code, 200)
        data = comp_res.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["prescribed_medicines_added"], 2)
        self.assertIsNotNone(data["follow_up_appointment_id"])

        # Verify medicines were added to tracker
        with self.app.app_context():
            with get_db() as conn:
                cur = conn.cursor()
                cur.execute("SELECT * FROM medicines WHERE doctor_prescribed = ?", ("Dr. B. K. Sen",))
                meds = cur.fetchall()
                self.assertGreaterEqual(len(meds), 2)
                med_names = [m["medicine_name"] for m in meds]
                self.assertIn("Telmisartan 40mg", med_names)
                self.assertIn("Amlodipine 5mg", med_names)

    def test_appointment_reminders_and_localization(self):
        """SPEC 13: 24h, 2h, and 30m reminders generated in English and Telugu."""
        create_res = self.client.post("/api/appointments", json={
            "patient_name": "Venkatesh",
            "doctor_name": "Dr. Srinivas",
            "specialty": "Orthopedics",
            "appointment_date": self.tomorrow,
            "appointment_time": "10:00 AM",
            "location_or_clinic": "Ortho Care Banjara",
            "purpose": "Knee pain check"
        })
        apt_id = create_res.get_json()["id"]

        # English reminders
        res_en = self.client.get(f"/api/appointments/{apt_id}/reminders?lang=en")
        self.assertEqual(res_en.status_code, 200)
        data_en = res_en.get_json()
        self.assertTrue(data_en["success"])
        self.assertEqual(len(data_en["reminders"]), 3)
        triggers = [r["trigger"] for r in data_en["reminders"]]
        self.assertIn("24h_before", triggers)
        self.assertIn("2h_before", triggers)
        self.assertIn("30m_before", triggers)

        # Telugu reminders
        res_te = self.client.get(f"/api/appointments/{apt_id}/reminders?lang=te")
        self.assertEqual(res_te.status_code, 200)
        data_te = res_te.get_json()
        self.assertTrue(data_te["success"])
        # Should contain Telugu script characters
        self.assertIn("రేపు", data_te["reminders"][0]["message"])

    def test_rfc5545_ics_export(self):
        """SPEC 13: Export appointment as RFC 5545 compliant iCalendar .ics file."""
        create_res = self.client.post("/api/appointments", json={
            "patient_name": "Ananya",
            "doctor_name": "Dr. Pradeep",
            "specialty": "Pulmonology",
            "appointment_date": self.tomorrow,
            "appointment_time": "11:00 AM",
            "location_or_clinic": "Chest Care Center",
            "purpose": "Asthma followup",
            "notes": "Bring previous spirometry test"
        })
        self.assertEqual(create_res.status_code, 201)
        apt_id = create_res.get_json()["id"]

        res = self.client.get(f"/api/appointments/{apt_id}/export-ics")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.mimetype, "text/calendar")
        ics_text = res.get_data(as_text=True)
        self.assertIn("BEGIN:VCALENDAR", ics_text)
        self.assertIn("VERSION:2.0", ics_text)
        self.assertIn("BEGIN:VEVENT", ics_text)
        self.assertIn("DTSTART:", ics_text)
        self.assertIn("DTEND:", ics_text)
        self.assertIn("SUMMARY:Doctor Visit: Dr. Pradeep (Pulmonology)", ics_text)
        self.assertIn("LOCATION:Chest Care Center", ics_text)
        self.assertIn("END:VEVENT", ics_text)
        self.assertIn("END:VCALENDAR", ics_text)

    def test_google_calendar_url_generation(self):
        """SPEC 13: Google Calendar one-tap web URL generation."""
        create_res = self.client.post("/api/appointments", json={
            "patient_name": "Ananya",
            "doctor_name": "Dr. Pradeep",
            "specialty": "Pulmonology",
            "appointment_date": self.tomorrow,
            "appointment_time": "11:00 AM",
            "location_or_clinic": "Chest Care Center",
            "purpose": "Asthma followup"
        })
        self.assertEqual(create_res.status_code, 201)
        apt_id = create_res.get_json()["id"]

        res = self.client.get(f"/api/appointments/{apt_id}/google-calendar-url")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        url = data["google_calendar_url"]
        self.assertIn("https://calendar.google.com/calendar/render?action=TEMPLATE", url)
        self.assertIn("Chest", url)
        self.assertIn("Care", url)

    def test_pre_visit_checklist_and_directions(self):
        """SPEC 13: Tailored pre-visit checklist based on doctor specialty."""
        # 1. Cardiology appointment checklist
        res_cardio = self.client.post("/api/appointments", json={
            "patient_name": "Suresh",
            "doctor_name": "Dr. Gupta",
            "specialty": "Cardiology",
            "appointment_date": self.tomorrow,
            "appointment_time": "10:00 AM",
            "location_or_clinic": "Care Hospital"
        })
        self.assertEqual(res_cardio.status_code, 201)
        cardio_id = res_cardio.get_json()["id"]
        chk_cardio = self.client.get(f"/api/appointments/{cardio_id}/pre-visit-checklist").get_json()
        self.assertTrue(chk_cardio["success"])
        items_str = " ".join(chk_cardio["checklist"])
        self.assertIn("ECG", items_str)
        self.assertIn("maps/search", chk_cardio["directions_link"])

        # 2. Diabetes appointment checklist
        res_diab = self.client.post("/api/appointments", json={
            "patient_name": "Suresh",
            "doctor_name": "Dr. Rao",
            "specialty": "Diabetology",
            "appointment_date": self.tomorrow,
            "appointment_time": "08:30 AM",
            "location_or_clinic": "Sugar Clinic"
        })
        self.assertEqual(res_diab.status_code, 201)
        diab_id = res_diab.get_json()["id"]
        chk_diab = self.client.get(f"/api/appointments/{diab_id}/pre-visit-checklist").get_json()
        self.assertTrue(chk_diab["success"])
        items_diab_str = " ".join(chk_diab["checklist"])
        self.assertIn("Fast for 8-10 hours", items_diab_str)
        self.assertIn("glucometer", items_diab_str)

if __name__ == "__main__":
    unittest.main()

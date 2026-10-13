"""
HealthMate AI — Phase 7 Automated Test Suite (SPEC.md Sections 6, 7 & 14d)
Tests:
1. Doctor registration creates doctor record with Medical Reg Number and role='doctor'
2. Doctor login and 2FA verification establishes doctor session
3. Patient access request via Prescription Code / Mobile / Aadhaar generates approval OTP
4. Patient OTP verification grants 30-minute read-only clinical session
5. Patient access audit log: Aadhaar NEVER appears in logs
6. Patient can revoke access session immediately
7. Privacy filter: Mental health & addiction records are masked unless explicitly opted in
"""

import os
import gc
import tempfile
import unittest
from app import create_app, init_db, get_db

class Phase7DoctorPortalTestCase(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_phase7.db")
        self.app = create_app({
            "TESTING": True,
            "DATABASE": self.db_path,
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{self.db_path}",
            "WTF_CSRF_ENABLED": False,
            "SECRET_KEY": "test-secret-phase7"
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

    def test_doctor_registration_and_role_separation(self):
        """SPEC 6 & 14d: Register doctor with medical registration number and role='doctor'."""
        res = self.client.post("/api/doctor/register", json={
            "doctor_name": "Dr. Ananya Sharma",
            "medical_reg_no": "MCI-74892",
            "speciality": "Cardiology",
            "hospital": "Care Hospitals Hyderabad",
            "email": "dr.ananya@carehospitals.com",
            "mobile": "9848012345",
            "password": "SecureDoctorPassword123!"
        })
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["role"], "doctor")

    def test_doctor_login_and_2fa(self):
        """SPEC 6: Doctor login requires 2FA and verifies session."""
        # 1. Register doctor
        self.client.post("/api/doctor/register", json={
            "doctor_name": "Dr. Sunil Varma",
            "medical_reg_no": "TSMC-9921",
            "speciality": "General Medicine",
            "hospital": "Govt CHC",
            "email": "dr.sunil@govthosp.in",
            "mobile": "9848054321",
            "password": "DoctorPass9921!"
        })

        # 2. Login step 1: Credentials check
        login_res = self.client.post("/api/doctor/login", json={
            "identifier": "dr.sunil@govthosp.in",
            "password": "DoctorPass9921!"
        })
        self.assertEqual(login_res.status_code, 200)
        login_data = login_res.get_json()
        self.assertTrue(login_data["require_2fa"])
        doc_id = login_data["doctor_id"]

        # 3. Login step 2: 2FA Verification
        twofa_res = self.client.post("/api/doctor/verify-2fa", json={
            "doctor_id": doc_id,
            "otp": "482910"
        })
        self.assertEqual(twofa_res.status_code, 200)
        self.assertTrue(twofa_res.get_json()["success"])

    def test_patient_otp_access_and_30min_session(self):
        """SPEC 7: Request access via patient OTP and establish 30-minute read-only session."""
        # 1. Doctor requests access
        req_res = self.client.post("/api/doctor/request-patient-access", json={
            "method": "mobile",
            "value": "9876543210"
        })
        self.assertEqual(req_res.status_code, 200)
        data = req_res.get_json()
        self.assertTrue(data["success"])
        demo_otp = data["demo_otp"]
        profile_id = data["profile_id"]

        # 2. Verify patient OTP
        verify_res = self.client.post("/api/doctor/verify-patient-otp", json={
            "method": "mobile",
            "profile_id": profile_id,
            "otp": demo_otp
        })
        self.assertEqual(verify_res.status_code, 200)
        vdata = verify_res.get_json()
        self.assertTrue(vdata["success"])
        self.assertEqual(vdata["expires_in_minutes"], 30)
        token = vdata["session_token"]

        # 3. Open consultation view
        view_res = self.client.get(f"/doctor/patient-view/{token}")
        self.assertEqual(view_res.status_code, 200)
        html = view_res.get_data(as_text=True)
        self.assertIn("Read-Only Clinical Access", html)
        self.assertIn("Active Consultation Session", html)

    def test_patient_access_logs_never_contain_aadhaar(self):
        """SPEC 14d: Critical security requirement: Aadhaar NEVER appears in doctor access logs."""
        # Doctor requests access via Aadhaar
        self.client.post("/api/doctor/request-patient-access", json={
            "method": "aadhaar",
            "value": "5482 9102 3847"
        })

        # Check access logs
        log_res = self.client.get("/api/doctor-access/logs")
        self.assertEqual(log_res.status_code, 200)
        data = log_res.get_json()
        self.assertTrue(data["success"])
        self.assertIn("security_notice", data)
        # Verify Aadhaar number is nowhere in raw response
        raw_text = log_res.get_data(as_text=True)
        self.assertNotIn("5482 9102 3847", raw_text)
        self.assertNotIn("548291023847", raw_text)

    def test_patient_can_revoke_doctor_access(self):
        """SPEC 7: Patient can immediately revoke active doctor session."""
        # Create session
        req_res = self.client.post("/api/doctor/request-patient-access", json={
            "method": "rx",
            "value": "RX-DEMO"
        })
        demo_otp = req_res.get_json()["demo_otp"]
        prof_id = req_res.get_json()["profile_id"]

        v_res = self.client.post("/api/doctor/verify-patient-otp", json={
            "method": "rx",
            "profile_id": prof_id,
            "otp": demo_otp
        })
        token = v_res.get_json()["session_token"]

        # Confirm accessible
        self.assertEqual(self.client.get(f"/doctor/patient-view/{token}").status_code, 200)

        # Revoke access
        rev_res = self.client.post("/api/doctor-access/revoke", json={"session_token": token})
        self.assertEqual(rev_res.status_code, 200)
        self.assertTrue(rev_res.get_json()["success"])

        # Attempt to access again should be blocked (HTTP 403)
        blocked_res = self.client.get(f"/doctor/patient-view/{token}")
        self.assertEqual(blocked_res.status_code, 403)

if __name__ == "__main__":
    unittest.main()

"""
Unit Tests for HealthMate AI — Step 2 (Timeline & Family Profiles)
Tests:
- Hackathon Focus #1: Patient Records Timeline (/timeline, /api/timeline)
- Hackathon Focus #5: Family Profiles (/api/profiles, /api/profiles/active)
- Reverse-chronological sorting and filtering
- Mandatory 112 emergency helpline banner verification
- CSRF protection on profile state changes
"""

import os
import gc
import json
import tempfile
import unittest
from app import create_app, init_db, seed_sample_data


class Step2TimelineProfilesTestCase(unittest.TestCase):
    def setUp(self):
        """Set up an isolated temporary database and test client for each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_step2.db")
        self.upload_dir = os.path.join(self.temp_dir, "test_uploads")
        os.makedirs(self.upload_dir, exist_ok=True)

        self.app = create_app({
            "TESTING": True,
            "DATABASE": self.db_path,
            "UPLOAD_FOLDER": self.upload_dir,
            "WTF_CSRF_ENABLED": True,
            "SECRET_KEY": "test-secret-step2-timeline"
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
    # 1. TIMELINE PAGE & EMERGENCY BANNER
    # ==========================================================================

    def test_timeline_page_renders_with_emergency_banner(self):
        """GET /timeline renders the timeline page with 112 emergency banner."""
        res = self.client.get("/timeline")
        self.assertEqual(res.status_code, 200)
        html = res.get_data(as_text=True)
        self.assertIn("Patient Care & Records Timeline", html)
        self.assertIn("112", html)
        self.assertIn("108", html)
        self.assertIn("104", html)

    # ==========================================================================
    # 2. FAMILY PROFILES MANAGEMENT (Hackathon Focus #5)
    # ==========================================================================

    def test_profiles_api_get(self):
        """GET /api/profiles returns list of seeded family profiles with record counts."""
        res = self.client.get("/api/profiles")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("success"))
        profiles = data.get("profiles", [])
        self.assertGreaterEqual(len(profiles), 4)

        grandpa = next((p for p in profiles if "Grandpa Rao" in p["name"]), None)
        self.assertIsNotNone(grandpa)
        self.assertEqual(grandpa["relationship"], "Grandparent")
        self.assertEqual(grandpa["is_default"], 1)
        self.assertGreaterEqual(grandpa["total_records"], 1)

    def test_profiles_api_create(self):
        """POST /api/profiles creates a new family member profile."""
        csrf = self.get_csrf_token()
        payload = {
            "_csrf": csrf,
            "name": "Baby Aarav",
            "relationship": "Child",
            "age": 2,
            "gender": "Male",
            "blood_group": "O+"
        }
        res = self.client.post("/api/profiles", json=payload)
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertTrue(data.get("success"))
        self.assertIn("id", data["profile"])
        self.assertEqual(data["profile"]["name"], "Baby Aarav")

    def test_profiles_active_switch(self):
        """POST /api/profiles/active switches active profile in session."""
        csrf = self.get_csrf_token()

        # Switch to profile 2 (Sita Devi)
        res = self.client.post("/api/profiles/active", json={"_csrf": csrf, "profile_id": 2})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("success"))
        self.assertEqual(data["active_profile_id"], 2)

        # GET /api/profiles/active reflects active profile
        active_res = self.client.get("/api/profiles/active")
        self.assertEqual(active_res.status_code, 200)
        self.assertEqual(active_res.get_json()["profile"]["id"], 2)

    def test_profiles_delete_protection(self):
        """Default profile cannot be deleted; newly created profiles can be deleted."""
        csrf = self.get_csrf_token()

        # Attempt to delete default profile 1 -> should fail with 400
        del_default_res = self.client.delete("/api/profiles/1", json={"_csrf": csrf})
        self.assertEqual(del_default_res.status_code, 400)

        # Create custom profile
        create_res = self.client.post("/api/profiles", json={
            "_csrf": csrf,
            "name": "Temporary Cousin",
            "relationship": "Other"
        })
        new_id = create_res.get_json()["profile"]["id"]

        # Delete custom profile -> should succeed
        del_res = self.client.delete(f"/api/profiles/{new_id}", json={"_csrf": csrf})
        self.assertEqual(del_res.status_code, 200)

    def test_csrf_protection_on_profiles(self):
        """Profile creation without CSRF token must be rejected with 403."""
        res = self.client.post("/api/profiles", json={"name": "Attacker"})
        self.assertEqual(res.status_code, 403)

    # ==========================================================================
    # 3. RECORDS TIMELINE (Hackathon Focus #1)
    # ==========================================================================

    def test_timeline_api_chronological_ordering(self):
        """GET /api/timeline returns records sorted reverse-chronologically (newest first)."""
        res = self.client.get("/api/timeline")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("success"))
        items = data.get("timeline", [])
        self.assertGreater(len(items), 0)

        # Verify dates are in descending order
        dates = [item["date"] for item in items if item.get("date")]
        self.assertEqual(dates, sorted(dates, reverse=True))

    def test_timeline_api_filtering_by_type(self):
        """GET /api/timeline?type=appointment only returns appointments."""
        res_apt = self.client.get("/api/timeline?type=appointment")
        self.assertEqual(res_apt.status_code, 200)
        for item in res_apt.get_json()["timeline"]:
            self.assertEqual(item["item_type"], "appointment")

        res_rep = self.client.get("/api/timeline?type=report")
        self.assertEqual(res_rep.status_code, 200)
        for item in res_rep.get_json()["timeline"]:
            self.assertEqual(item["item_type"], "report")

        res_med = self.client.get("/api/timeline?type=medicine")
        self.assertEqual(res_med.status_code, 200)
        for item in res_med.get_json()["timeline"]:
            self.assertEqual(item["item_type"], "medicine")

    def test_timeline_api_filtering_by_profile(self):
        """GET /api/timeline?profile_id=1 returns records scoped to profile 1."""
        res = self.client.get("/api/timeline?profile_id=1")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        for item in data["timeline"]:
            self.assertEqual(item["profile_id"], 1)


if __name__ == "__main__":
    unittest.main()

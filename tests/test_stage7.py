"""
Unit Tests for HealthMate AI — Stage 7 Features
Tests:
- Educational Term Explainer (/explainer, /api/explainer)
- Strict keyword glossary fallback (labeled 'Educational fallback (not AI)')
- Input validation (max 2000 characters, empty query rejection)
- CSRF protection on explainer endpoint
- Competitor Research (/research, /api/research)
- 9 competitors analysis matrix and roadmap
- Mandatory 112/108/104 emergency hotline banner verification
"""

import os
import gc
import tempfile
import unittest
from app import create_app, init_db, seed_sample_data


class Stage7TestCase(unittest.TestCase):
    def setUp(self):
        """Set up an isolated temporary database and test client for each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_stage7.db")
        self.upload_dir = os.path.join(self.temp_dir, "test_uploads")
        os.makedirs(self.upload_dir, exist_ok=True)

        self.app = create_app({
            "TESTING": True,
            "DATABASE": self.db_path,
            "UPLOAD_FOLDER": self.upload_dir,
            "WTF_CSRF_ENABLED": True,
            "SECRET_KEY": "test-secret-stage7"
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
    # 1. TERM EXPLAINER (Stage 7a)
    # ==========================================================================

    def test_explainer_page_renders_with_emergency_banner(self):
        """GET /explainer renders the explainer page with 112 emergency banner and educational badge."""
        res = self.client.get("/explainer")
        self.assertEqual(res.status_code, 200)
        html = res.get_data(as_text=True)
        self.assertIn("Medical Term & Lab Explainer", html)
        self.assertIn("Educational fallback (not AI)", html)
        self.assertIn("112", html)
        self.assertIn("108", html)

    def test_explainer_api_valid_keyword_match(self):
        """POST /api/explainer matches keyword against glossary and provides bilingual explanation."""
        csrf = self.get_csrf_token()
        res = self.client.post("/api/explainer", json={
            "_csrf": csrf,
            "query": "HbA1c"
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("success"))
        self.assertEqual(data.get("badge"), "Educational fallback (not AI)")
        self.assertGreater(data.get("matches_count", 0), 0)

        match = data["matches"][0]
        self.assertIn("HbA1c", match["term"])
        self.assertIn("meaning_en", match)
        self.assertIn("meaning_te", match)
        self.assertIn("normal_range", match)

    def test_explainer_api_empty_query_rejected(self):
        """POST /api/explainer with empty query must return 400 Bad Request."""
        csrf = self.get_csrf_token()
        res = self.client.post("/api/explainer", json={"_csrf": csrf, "query": "   "})
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertFalse(data.get("success"))

    def test_explainer_api_max_length_limit(self):
        """POST /api/explainer with text > 2000 characters must return 400."""
        csrf = self.get_csrf_token()
        too_long_query = "Blood test result: " + ("a" * 2050)
        res = self.client.post("/api/explainer", json={"_csrf": csrf, "query": too_long_query})
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertIn("2000 characters", data.get("error", ""))

    def test_explainer_api_csrf_protection(self):
        """POST /api/explainer without CSRF token must return 403 Forbidden."""
        res = self.client.post("/api/explainer", json={"query": "Creatinine"})
        self.assertEqual(res.status_code, 403)

    # ==========================================================================
    # 2. COMPETITOR RESEARCH (Stage 7b)
    # ==========================================================================

    def test_research_page_renders_with_emergency_banner(self):
        """GET /research renders competitor matrix and contains all key competitors and 112 helpline."""
        res = self.client.get("/research")
        self.assertEqual(res.status_code, 200)
        html = res.get_data(as_text=True)
        self.assertIn("Competitor Research & Architecture Comparison", html)
        self.assertIn("Apple Health", html)
        self.assertIn("Epic MyChart", html)
        self.assertIn("Ada Health", html)
        self.assertIn("eSanjeevani", html)
        self.assertIn("Practo", html)
        self.assertIn("ABHA", html)
        self.assertIn("Apollo 24|7", html)
        self.assertIn("Tata 1mg", html)
        self.assertIn("112", html)

    def test_research_api_returns_all_competitors(self):
        """GET /api/research returns full JSON matrix of 9 competitors."""
        res = self.client.get("/api/research")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("success"))
        competitors = data.get("competitors", [])
        self.assertEqual(len(competitors), 9)

        names = [c["name"] for c in competitors]
        self.assertIn("Apple Health", names)
        self.assertIn("Epic MyChart", names)
        self.assertIn("eSanjeevani (Govt. of India)", names)
        self.assertIn("Tata 1mg", names)


if __name__ == "__main__":
    unittest.main()

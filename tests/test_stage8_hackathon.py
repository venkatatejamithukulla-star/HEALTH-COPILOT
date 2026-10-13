"""
Unit Tests for HealthMate AI — Stage 8 Hackathon Pack
Tests:
- Interactive Hackathon Pack route (/hackathon)
- Mandatory 112/108/104 emergency hotline banner
- HACKATHON_PACK.md document existence and key sections (1-min pitch, 3-min demo, judge Q&A)
"""

import os
import gc
import tempfile
import unittest
from pathlib import Path
from app import create_app, init_db, seed_sample_data


class Stage8HackathonTestCase(unittest.TestCase):
    def setUp(self):
        """Set up an isolated temporary database and test client for each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_stage8.db")
        self.upload_dir = os.path.join(self.temp_dir, "test_uploads")
        os.makedirs(self.upload_dir, exist_ok=True)

        self.app = create_app({
            "TESTING": True,
            "DATABASE": self.db_path,
            "UPLOAD_FOLDER": self.upload_dir,
            "WTF_CSRF_ENABLED": True,
            "SECRET_KEY": "test-secret-stage8"
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

    def test_hackathon_page_renders_with_emergency_banner(self):
        """GET /hackathon renders the presentation pack with elevator pitch and 112 emergency numbers."""
        res = self.client.get("/hackathon")
        self.assertEqual(res.status_code, 200)
        html = res.get_data(as_text=True)
        self.assertIn("Hackathon Presentation Pack", html)
        self.assertIn("1-Minute Elevator Pitch", html)
        self.assertIn("3-Minute Live Hackathon Demo Script", html)
        self.assertIn("Judge Q&A Cheat Sheet", html)
        self.assertIn("112", html)
        self.assertIn("108", html)

    def test_hackathon_pack_markdown_file_exists(self):
        """HACKATHON_PACK.md must exist in the root folder and contain elevator pitch and Q&A."""
        pack_path = Path(__file__).resolve().parent.parent / "HACKATHON_PACK.md"
        self.assertTrue(pack_path.exists(), "HACKATHON_PACK.md must exist in the project root")

        content = pack_path.read_text(encoding="utf-8")
        self.assertIn("1-Minute Elevator Pitch", content)
        self.assertIn("3-Minute Live Hackathon Demo Script", content)
        self.assertIn("The 5 Strong Hackathon Focus Areas", content)
        self.assertIn("Competitor Comparison Matrix", content)
        self.assertIn("Judge Q&A Cheat Sheet", content)


if __name__ == "__main__":
    unittest.main()

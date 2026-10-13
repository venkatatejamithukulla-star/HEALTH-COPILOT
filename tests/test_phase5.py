"""
HealthMate AI — Phase 5 Automated Test Suite (SPEC.md Section 5 & 16a)
Tests:
1. 'Heart' lists every heart disease (all 15 heart conditions returned)
2. Every category count matches the batch definition (Total >= 200, exactly 223 across 16 categories)
3. One disease page opens correctly in Telugu, Hindi, and Tamil with translated titles and content
4. Reports tab displays diagnostic tests with normal ranges explained
5. Mental Health and Substance Use pages follow 16a and show the 16h disclaimer
"""

import unittest
from app import create_app
import disease_data

class Phase5DiseasesTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app({"TESTING": True, "WTF_CSRF_ENABLED": False})
        self.client = self.app.test_client()

    def test_total_diseases_count_at_least_200(self):
        """Verify database contains >= 200 diseases across categories."""
        self.assertGreaterEqual(len(disease_data.DISEASE_LIBRARY), 200)
        self.assertEqual(len(disease_data.DISEASE_LIBRARY), 223)

    def test_heart_lists_every_heart_disease(self):
        """Test: 'Heart' lists every heart disease."""
        res = self.client.get("/api/diseases?category=heart")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        heart_diseases = data["diseases"]
        self.assertEqual(len(heart_diseases), 15)
        # Verify names of key heart conditions
        names = [d["name"] for d in heart_diseases]
        self.assertIn("Coronary Artery Disease (CAD)", names)
        self.assertIn("Hypertension (High Blood Pressure)", names)
        self.assertIn("Congestive Heart Failure", names)
        self.assertIn("Atrial Fibrillation", names)
        self.assertIn("Valvular Heart Disease", names)
        self.assertIn("Cardiomyopathy", names)
        self.assertIn("Angina Pectoris", names)

    def test_every_category_count_matches(self):
        """Test: every category count matches expected batch numbers."""
        counts = disease_data.get_category_counts()
        expected = {
            "Heart": 15,
            "Diabetes": 14,
            "Respiratory": 15,
            "Neuro": 14,
            "Skin": 15,
            "Eye": 13,
            "ENT": 13,
            "Bone": 14,
            "Kidney": 13,
            "Liver": 15,
            "Women's Health": 14,
            "Child Health": 13,
            "Infectious": 15,
            "Mental Health": 14,
            "Substance Use": 12,
            "Cancer": 14
        }
        for cat, expected_count in expected.items():
            self.assertEqual(
                counts.get(cat),
                expected_count,
                f"Category '{cat}' count mismatch: got {counts.get(cat)}, expected {expected_count}"
            )
        self.assertEqual(sum(counts.values()), 223)

    def test_one_disease_page_opens_in_telugu_hindi_tamil(self):
        """Test: one disease page opens correctly in Telugu, Hindi and Tamil."""
        # Using hypertension
        disease_id = "hypertension"
        
        # 1. Open in English
        res_en = self.client.get(f"/diseases/{disease_id}?lang=en")
        self.assertEqual(res_en.status_code, 200)
        html_en = res_en.get_data(as_text=True)
        self.assertIn("Hypertension", html_en)
        self.assertIn("Reports & Tests", html_en) # Reports tab present

        # 2. Open in Telugu
        res_te = self.client.get(f"/diseases/{disease_id}?lang=te")
        self.assertEqual(res_te.status_code, 200)
        html_te = res_te.get_data(as_text=True)
        self.assertIn("రక్తపోటు", html_te)
        self.assertIn("lang=\"te\"", html_te)

        # 3. Open in Hindi
        res_hi = self.client.get(f"/diseases/{disease_id}?lang=hi")
        self.assertEqual(res_hi.status_code, 200)
        html_hi = res_hi.get_data(as_text=True)
        self.assertIn("उच्च रक्तचाप", html_hi)
        self.assertIn("lang=\"hi\"", html_hi)

        # 4. Open in Tamil
        res_ta = self.client.get(f"/diseases/{disease_id}?lang=ta")
        self.assertEqual(res_ta.status_code, 200)
        html_ta = res_ta.get_data(as_text=True)
        self.assertIn("உயர் இரத்த அழுத்தம்", html_ta)
        self.assertIn("lang=\"ta\"", html_ta)

    def test_reports_tab_and_normal_ranges_explained(self):
        """Test: Reports tab exists with normal ranges explained."""
        res = self.client.get("/diseases/hypertension")
        self.assertEqual(res.status_code, 200)
        html = res.get_data(as_text=True)
        self.assertIn("Reports & Tests (Normal Ranges)", html)
        self.assertIn("Serum Creatinine", html)
        self.assertIn("Consult your doctor before use", html) # Generic medicines warning

    def test_mental_health_and_substance_use_show_16h_disclaimer(self):
        """Test: Mental health and substance use pages follow 16a and show 16h disclaimer."""
        # Mental Health: major_depressive_disorder
        res_mh = self.client.get("/diseases/major_depressive_disorder")
        self.assertEqual(res_mh.status_code, 200)
        html_mh = res_mh.get_data(as_text=True)
        self.assertIn("SPEC 16h Sensitive Health & Mental Wellbeing Disclaimer", html_mh)
        self.assertIn("14416", html_mh) # Tele-MANAS helpline
        self.assertIn("112", html_mh) # National emergency

        # Substance Use: alcohol_use_disorder
        res_sub = self.client.get("/diseases/alcohol_use_disorder")
        self.assertEqual(res_sub.status_code, 200)
        html_sub = res_sub.get_data(as_text=True)
        self.assertIn("SPEC 16h Sensitive Health & Mental Wellbeing Disclaimer", html_sub)
        self.assertIn("14416", html_sub)

if __name__ == "__main__":
    unittest.main()

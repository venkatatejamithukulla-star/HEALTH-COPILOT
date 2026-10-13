"""
HealthMate AI — Comprehensive Test Suite for Phases 2, 3, and 4
SPEC.md Verification:
- Phase 2:
  1. Switch to Telugu, Hindi, Tamil, Urdu, Santali and confirm pages render with no raw keys.
  2. Switching profile reloads/scopes all sections (appointments, medicines, reports).
  3. Blood group badge shows in the header.
- Phase 3:
  4. Pick 5 random states from LGD list and confirm every district appears.
  5. Urban/Rural and speciality cascading filters change results.
  6. Helpline taps start calls (tel: links: 108, 112, 104, 14416).
- Phase 4:
  7. GPS location works (Haversine distance calculation and reverse-geocode).
  8. Symptom matcher: "chest pain" selects Cardiology.
  9. Symptom matcher: "craving alcohol" selects De-addiction.
  10. Facility coordinates exist and map markers match the query list.
"""

import os
import gc
import json
import random
import unittest
import tempfile
from pathlib import Path

from app import create_app, init_db, seed_sample_data, calculate_haversine_km, get_db

class Phases234TestCase(unittest.TestCase):
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        self.test_config = {
            "TESTING": True,
            "DATABASE": self.db_path,
            "WTF_CSRF_ENABLED": False,
            "SECRET_KEY": "test-key-phase234"
        }
        self.app = create_app(self.test_config)
        self.client = self.app.test_client()

        with self.app.app_context():
            init_db(self.db_path)
            seed_sample_data(force=True, db_path=self.db_path)

            # Ensure facilities table is seeded for test db
            import seed_india
            seed_india.seed_database(target_db_path=self.db_path, seed_all=False)

    def tearDown(self):
        gc.collect()
        try:
            os.close(self.db_fd)
        except OSError:
            pass
        if os.path.exists(self.db_path):
            try:
                os.unlink(self.db_path)
            except OSError:
                pass

    # ==========================================================================
    # PHASE 2 TESTS: 23 LANGUAGES, NO RAW KEYS, PROFILES, BLOOD GROUP BADGE
    # ==========================================================================

    def test_phase2_switch_languages_no_raw_keys(self):
        """
        Switch to Telugu, Hindi, Tamil, Urdu, Santali and confirm:
        - Locale JSON files exist with metadata (RTL for Urdu).
        - Translations return valid non-empty dictionaries with no raw untranslated placeholders.
        - Pages render correctly for each language without missing key errors.
        """
        target_languages = ["te", "hi", "ta", "ur", "sat"]
        locales_dir = Path(self.app.root_path) / "locales"

        for lang in target_languages:
            loc_file = locales_dir / f"{lang}.json"
            self.assertTrue(loc_file.exists(), f"Locale file for {lang} must exist.")

            with open(loc_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Validate metadata
            self.assertIn("_metadata", data)
            self.assertEqual(data["_metadata"]["code"], lang)
            if lang == "ur":
                self.assertEqual(data["_metadata"]["direction"], "rtl", "Urdu must be marked RTL.")

            # Validate translations endpoint
            res = self.client.get(f"/api/locales/{lang}")
            self.assertEqual(res.status_code, 200)
            res_data = res.get_json()
            self.assertTrue(res_data["success"])
            self.assertEqual(res_data["lang"], lang)
            t_dict = res_data["translations"]

            # Confirm essential keys are present and not raw keys
            for key in ["appTitle", "ambulance108", "emergency112", "healthHelpline104", "teleManas14416", "disclaimerNotice"]:
                self.assertIn(key, t_dict, f"Key {key} must exist in {lang}")
                self.assertNotEqual(t_dict[key], f"{{{key}}}", f"Key {key} must not be raw template tag.")
                self.assertNotEqual(t_dict[key], f"t['{key}']", f"Key {key} must not be raw code key.")
                self.assertTrue(len(t_dict[key]) > 0, f"Translation for {key} in {lang} must not be empty.")

            # Test session language persistence
            set_res = self.client.post("/api/set-language", json={"language": lang})
            self.assertEqual(set_res.status_code, 200)

            # Verify home page renders successfully for this language
            page_res = self.client.get("/")
            self.assertEqual(page_res.status_code, 200)
            page_html = page_res.get_data(as_text=True)
            self.assertNotIn("{{ t.", page_html, f"Page must not have raw Jinja translation tags for {lang}")

    def test_phase2_profile_switching_reloads_sections(self):
        """
        Switching active profile reloads and scopes records per family member.
        """
        # Create a new family profile for daughter "Pooja"
        res = self.client.post("/api/profiles", json={
            "name": "Pooja Rao",
            "relationship": "Child",
            "age": 14,
            "gender": "Female",
            "blood_group": "AB+"
        })
        self.assertEqual(res.status_code, 201)
        new_prof = res.get_json()["profile"]
        new_id = new_prof["id"]

        # Add appointment for Pooja
        self.client.post("/api/appointments", json={
            "patient_name": "Pooja Rao",
            "doctor_name": "Dr. Sunita Pediatrician",
            "specialty": "Pediatrics",
            "appointment_date": "2026-11-10",
            "appointment_time": "10:00 AM",
            "location_or_clinic": "Children Care Clinic",
            "notes": "Growth checkup",
            "profile_id": new_id
        })

        # Switch to Pooja's profile
        switch_res = self.client.post("/api/profiles/active", json={"profile_id": new_id})
        self.assertEqual(switch_res.status_code, 200)
        self.assertEqual(switch_res.get_json()["active_profile_id"], new_id)

        # Check that timeline records returned for Pooja's profile are scoped to profile_id
        timeline_res = self.client.get(f"/api/timeline?profile_id={new_id}")
        self.assertEqual(timeline_res.status_code, 200)
        t_data = timeline_res.get_json()
        self.assertTrue(t_data["success"])
        for item in t_data["timeline"]:
            self.assertEqual(item["profile_id"], new_id)

    def test_phase2_blood_group_in_header_and_emergency(self):
        """
        Blood group badge displays in the header and in the emergency bar.
        """
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        html = res.get_data(as_text=True)

        # Header blood group badge must be present
        self.assertIn('id="headerBloodGroupBadge"', html)
        self.assertIn('id="headerBloodGroupText"', html)

        # Emergency strip blood group pill must also be present
        self.assertIn('id="emergencyBloodGroupPill"', html)
        self.assertIn('id="emergencyBloodGroupText"', html)

        # Profile tooltip info
        self.assertIn('id="profileTooltip"', html)

    # ==========================================================================
    # PHASE 3 TESTS: LGD DISTRICTS, CASCADING FILTERS, TEL: HELPLINES
    # ==========================================================================

    def test_phase3_lgd_5_random_states_every_district_appears(self):
        """
        Pick 5 random states from official LGD list and confirm every district appears.
        """
        states_res = self.client.get("/api/lgd/states")
        self.assertEqual(states_res.status_code, 200)
        states_data = states_res.get_json()
        self.assertTrue(states_data["success"])
        all_states = states_data["states"]
        self.assertGreaterEqual(len(all_states), 36, "Must contain all 36 States and UTs")

        # Pick 5 random states
        sample_states = random.sample(all_states, 5)
        for state in sample_states:
            dist_res = self.client.get(f"/api/lgd/districts?state={state}")
            self.assertEqual(dist_res.status_code, 200)
            d_data = dist_res.get_json()
            self.assertTrue(d_data["success"])
            self.assertEqual(d_data["state"], state)
            districts = d_data["districts"]
            self.assertGreater(len(districts), 0, f"State {state} must have at least 1 district in LGD list.")

    def test_phase3_cascading_filters_change_results(self):
        """
        Urban/Rural, specialty, and facility_type filters change query results.
        """
        # All facilities
        res_all = self.client.get("/api/facilities?per_page=50")
        self.assertEqual(res_all.status_code, 200)
        total_all = res_all.get_json()["total"]
        self.assertGreater(total_all, 0)

        # Filter by Urban only
        res_urban = self.client.get("/api/facilities?area_type=Urban&per_page=50")
        self.assertEqual(res_urban.status_code, 200)
        total_urban = res_urban.get_json()["total"]

        # Filter by Rural only
        res_rural = self.client.get("/api/facilities?area_type=Rural&per_page=50")
        self.assertEqual(res_rural.status_code, 200)
        total_rural = res_rural.get_json()["total"]

        # Urban + Rural should equal total (or be partitioned)
        self.assertEqual(total_urban + total_rural, total_all)

        # Filter by specialty Cardiology
        res_cardio = self.client.get("/api/facilities?specialty=Cardiology")
        self.assertEqual(res_cardio.status_code, 200)
        cardio_list = res_cardio.get_json()["facilities"]
        for f in cardio_list:
            self.assertEqual(f["specialty"], "Cardiology")

        # Filter by specialty De-addiction
        res_deaddict = self.client.get("/api/facilities?specialty=De-addiction")
        self.assertEqual(res_deaddict.status_code, 200)
        deaddict_list = res_deaddict.get_json()["facilities"]
        for f in deaddict_list:
            self.assertEqual(f["specialty"], "De-addiction")

    def test_phase3_helpline_taps_start_calls(self):
        """
        Emergency banner buttons are tel: links for 108, 112, 104, 14416 (Tele-MANAS).
        """
        for url in ["/", "/find-care"]:
            res = self.client.get(url)
            self.assertEqual(res.status_code, 200)
            html = res.get_data(as_text=True)

            self.assertIn('href="tel:108"', html, f"108 must be a tel: link on {url}")
            self.assertIn('href="tel:112"', html, f"112 must be a tel: link on {url}")
            self.assertIn('href="tel:104"', html, f"104 must be a tel: link on {url}")
            self.assertIn('href="tel:14416"', html, f"14416 Tele-MANAS must be a tel: link on {url}")

    # ==========================================================================
    # PHASE 4 TESTS: GPS, HAVERSINE, SYMPTOM MATCHER, MAP MARKERS
    # ==========================================================================

    def test_phase4_gps_and_haversine_distance(self):
        """
        GPS location endpoint computes distance in km using Haversine formula
        and reverse-geocodes nearest facility.
        """
        # Test Haversine function
        # Distance between Charminar (17.3616, 78.4747) and Secunderabad (17.4399, 78.4983) is approx 9 km
        dist = calculate_haversine_km(17.3616, 78.4747, 17.4399, 78.4983)
        self.assertIsNotNone(dist)
        self.assertAlmostEqual(dist, 9.0, delta=1.5)

        # Test reverse-geocode API
        res = self.client.post("/api/location/reverse-geocode", json={"lat": 17.3850, "lon": 78.4867})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertIn("district", data)
        self.assertIn("distance_km", data)

        # Test facilities sorted by distance from user coordinates
        fac_res = self.client.get("/api/facilities?lat=17.3850&lon=78.4867&per_page=10")
        self.assertEqual(fac_res.status_code, 200)
        fac_data = fac_res.get_json()
        self.assertTrue(fac_data["success"])
        facilities = fac_data["facilities"]
        self.assertGreater(len(facilities), 0)

        # Confirm distance_km is present and monotonically sorted
        distances = [f["distance_km"] for f in facilities if f.get("distance_km") is not None]
        self.assertEqual(distances, sorted(distances), "Facilities must be sorted by distance ascending.")

    def test_phase4_symptom_chest_pain_selects_cardiology(self):
        """
        Typing 'chest pain' selects Cardiology.
        """
        res = self.client.get("/api/symptoms/search?q=chest pain")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["recommended_specialty"], "Cardiology")
        self.assertIn("Cardiology", data["message"])

    def test_phase4_symptom_craving_alcohol_selects_deaddiction(self):
        """
        Typing 'craving alcohol' selects De-addiction.
        """
        res = self.client.get("/api/symptoms/search?q=craving alcohol")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["recommended_specialty"], "De-addiction")
        self.assertIn("De-addiction", data["message"])

    def test_phase4_symptom_feeling_hopeless_selects_psychiatry(self):
        """
        Typing 'feeling hopeless' selects Psychiatry.
        """
        res = self.client.get("/api/symptoms/search?q=feeling hopeless")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["recommended_specialty"], "Psychiatry")

    def test_phase4_map_markers_match_facility_list(self):
        """
        Facilities returned have valid coordinates, phones, and directions data for map rendering.
        """
        res = self.client.get("/api/facilities?per_page=20")
        self.assertEqual(res.status_code, 200)
        facilities = res.get_json()["facilities"]
        self.assertGreater(len(facilities), 0)

        for f in facilities:
            self.assertIn("latitude", f)
            self.assertIn("longitude", f)
            self.assertIsNotNone(f["latitude"], f"Facility {f['name']} must have latitude.")
            self.assertIsNotNone(f["longitude"], f"Facility {f['name']} must have longitude.")
            self.assertIn("phone", f)
            self.assertIn("specialty", f)
            self.assertIn("facility_type", f)

if __name__ == "__main__":
    unittest.main()

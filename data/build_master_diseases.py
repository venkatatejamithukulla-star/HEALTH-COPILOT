"""
HealthMate AI — Master Disease Database Compiler (Phase 5)
Merges all 16 batches into data/diseases_full.json and reports counts.
"""

import re
import json
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "data"))

from build_full_diseases import CATEGORIES_SPEC
from cat_respiratory_neuro import RESPIRATORY_DISEASES, NEURO_DISEASES
from cat_skin_eye_ent import SKIN_DISEASES, EYE_DISEASES, ENT_DISEASES
from cat_bone_kidney_liver import BONE_DISEASES, KIDNEY_DISEASES, LIVER_DISEASES
from cat_women_child_infectious import WOMENS_HEALTH_DISEASES, CHILD_HEALTH_DISEASES, INFECTIOUS_DISEASES
from cat_mental_substance_cancer import MENTAL_HEALTH_DISEASES, SUBSTANCE_USE_DISEASES, CANCER_DISEASES, DISCLAIMER_16H

ALL_BATCHES = [
    ("Heart", CATEGORIES_SPEC["Heart"]),
    ("Diabetes", CATEGORIES_SPEC["Diabetes"]),
    ("Respiratory", RESPIRATORY_DISEASES),
    ("Neuro", NEURO_DISEASES),
    ("Skin", SKIN_DISEASES),
    ("Eye", EYE_DISEASES),
    ("ENT", ENT_DISEASES),
    ("Bone", BONE_DISEASES),
    ("Kidney", KIDNEY_DISEASES),
    ("Liver", LIVER_DISEASES),
    ("Women's Health", WOMENS_HEALTH_DISEASES),
    ("Child Health", CHILD_HEALTH_DISEASES),
    ("Infectious", INFECTIOUS_DISEASES),
    ("Mental Health", MENTAL_HEALTH_DISEASES),
    ("Substance Use", SUBSTANCE_USE_DISEASES),
    ("Cancer", CANCER_DISEASES)
]

def slugify(text):
    text = re.sub(r'\([^)]*\)', '', text)  # remove parentheticals
    text = text.lower().strip()
    text = re.sub(r'[^a-z0-9]+', '_', text)
    return text.strip('_')

def compile_database():
    compiled_diseases = []
    category_counts = {}

    for cat_name, raw_list in ALL_BATCHES:
        is_sensitive = cat_name in ["Mental Health", "Substance Use"]
        cat_count = 0

        for item in raw_list:
            name, te_name, hi_name, ta_name, icon, overview, causes, symptoms, reports, treatment, generic_meds, diet, prevention, specialists, emergency = item

            # Format generic medicines with standard warning
            med_list = []
            for m in generic_meds:
                if isinstance(m, dict):
                    med_list.append(m)
                else:
                    med_list.append({"name": str(m), "warning": "Consult your doctor before use"})

            # Generate unique ID
            d_id = slugify(name)
            if any(d["id"] == d_id for d in compiled_diseases):
                d_id = f"{slugify(cat_name)}_{d_id}"

            record = {
                "id": d_id,
                "name": name,
                "telugu_name": te_name,
                "hindi_name": hi_name,
                "tamil_name": ta_name,
                "category": cat_name,
                "body_area": cat_name, # 100% backward compatibility
                "icon": icon,
                "overview": overview,
                "summary": overview, # backward compatibility
                "causes": causes,
                "symptoms": symptoms,
                "warning_signs": symptoms, # backward compatibility
                "reports_tests": reports,
                "treatment": treatment,
                "generic_medicines": med_list,
                "diet_lifestyle": diet,
                "lifestyle_tips": diet, # backward compatibility
                "prevention": prevention,
                "specialists": specialists,
                "emergency_signs": emergency,
                "urgent_doctor": emergency, # backward compatibility
                "is_mental_health_or_addiction": is_sensitive,
                "disclaimer_16h": DISCLAIMER_16H if is_sensitive else None,
                "trusted_source": "https://www.who.int/health-topics",
                "trusted_source_label": f"WHO & MoHFW {cat_name} Resources"
            }

            compiled_diseases.append(record)
            cat_count += 1

        category_counts[cat_name] = cat_count
        print(f"Batch compiled: [{cat_name}] -> {cat_count} diseases")

    # Save to JSON
    output_path = Path(__file__).resolve().parent / "diseases_full.json"
    output_path.parent.mkdir(exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(compiled_diseases, f, ensure_ascii=False, indent=2)

    print("\n==========================================")
    print(f"SUCCESS: Total Diseases Compiled: {len(compiled_diseases)}")
    print(f"Category Breakdown ({len(category_counts)} categories):")
    for cat, count in category_counts.items():
        print(f"  • {cat}: {count}")
    print(f"Database saved to: {output_path}")
    print("==========================================")
    return compiled_diseases, category_counts

if __name__ == "__main__":
    compile_database()

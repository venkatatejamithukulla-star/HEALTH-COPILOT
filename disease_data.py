"""
HealthMate AI — Comprehensive Disease Library (Phase 5)
Database with 223 diseases across 16 categories:
1. Heart (15)
2. Diabetes (14)
3. Respiratory (15)
4. Neuro (14)
5. Skin (15)
6. Eye (13)
7. ENT (13)
8. Bone (14)
9. Kidney (13)
10. Liver (15)
11. Women's Health (14)
12. Child Health (13)
13. Infectious (15)
14. Mental Health (14)
15. Substance Use (12)
16. Cancer (14)
Total: 223 diseases

Features:
- Full reports/tests with normal ranges explained
- Generic medicines with "Consult your doctor before use" warning
- Causes, Symptoms, Diet & Lifestyle, Prevention, Specialists, Emergency signs
- Translations in Telugu, Hindi, Tamil
- SPEC 16a & 16h disclaimer for Mental Health & Substance Use
"""

import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data" / "diseases_full.json"

def _load_disease_library():
    if DATA_FILE.exists():
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if data and len(data) >= 200:
                    return data
        except Exception as e:
            print(f"[Warning] Failed to load diseases_full.json: {e}")
    
    # In case data file is not found, fallback to compiler
    try:
        from data.build_master_diseases import compile_database
        data, _ = compile_database()
        return data
    except Exception as e:
        print(f"[Warning] Failed to dynamically compile diseases: {e}")
        return []

DISEASE_LIBRARY = _load_disease_library()

# Derive category counts and map
CATEGORY_COUNTS = {}
for d in DISEASE_LIBRARY:
    cat = d.get("category", "General")
    CATEGORY_COUNTS[cat] = CATEGORY_COUNTS.get(cat, 0) + 1

DISEASE_CATEGORIES = list(CATEGORY_COUNTS.keys())

def get_category_counts():
    """Returns exact disease count per category."""
    return dict(CATEGORY_COUNTS)

def get_disease_by_id(disease_id):
    """Finds a disease by ID slug (case-insensitive)."""
    if not disease_id:
        return None
    slug = str(disease_id).lower().strip()
    for d in DISEASE_LIBRARY:
        if d.get("id", "").lower() == slug:
            return d
    return None

def get_diseases_by_category(category):
    """Returns all diseases matching category (case-insensitive)."""
    if not category or category.lower() in ["all", "all body areas"]:
        return DISEASE_LIBRARY
    cat_lower = category.lower()
    return [
        d for d in DISEASE_LIBRARY
        if d.get("category", "").lower() == cat_lower or d.get("body_area", "").lower() == cat_lower
    ]

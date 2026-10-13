"""
HealthMate AI — Assistant Engine (SPEC.md Sections 3, 4 & 16c)
Implements:
1. PII Stripping (strips names, phone numbers, Aadhaar, emails before external calls)
2. Crisis Safety Interceptor (16c): 5-language self-harm/suicide detection triggering
   compassionate response with tel:14416 (Tele-MANAS) and tel:112 (National Emergency).
3. Allergy & Drug Conflict Flagging (checks active profile allergies & conditions against medicines).
4. Structured 10-point Point-by-Point Guidance:
   - Causes
   - Symptoms to watch
   - Home care
   - What to avoid
   - Diet
   - Tests (with normal ranges explained)
   - Specialist
   - Generic medicines ("consult your doctor before use")
   - Red flags (emergency signs)
   - Follow-up
5. Quick replies, Call 108 button, and AI error disclaimer.
"""

import re
from typing import Dict, Any, List, Optional

# ==============================================================================
# 1. PII STRIPPING (SPEC 3 & 14)
# ==============================================================================

RE_PHONE = re.compile(r'(?:\+91[\-\s]?)?[6-9]\d{9}\b')
RE_AADHAAR = re.compile(r'\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b')
RE_EMAIL = re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+')

def strip_pii(text: str, patient_names: Optional[List[str]] = None) -> str:
    """
    Strips Personal Identifiable Information (PII) before any external processing.
    Redacts phone numbers, Aadhaar numbers, email addresses, and known patient names.
    """
    if not text:
        return ""
    
    sanitized = text
    # Strip Aadhaar
    sanitized = RE_AADHAAR.sub("[REDACTED_AADHAAR]", sanitized)
    # Strip Phone
    sanitized = RE_PHONE.sub("[REDACTED_PHONE]", sanitized)
    # Strip Email
    sanitized = RE_EMAIL.sub("[REDACTED_EMAIL]", sanitized)
    
    # Strip specific patient names if provided
    if patient_names:
        for name in patient_names:
            if name and len(name.strip()) > 2:
                pattern = re.compile(re.escape(name.strip()), re.IGNORECASE)
                sanitized = pattern.sub("[PATIENT_NAME]", sanitized)
                
    return sanitized


# ==============================================================================
# 2. CRISIS SAFETY INTERCEPTOR (SPEC 16c) — 5 LANGUAGES
# ==============================================================================

# Keywords and regex patterns across 5 languages: English, Telugu, Hindi, Tamil, Urdu
CRISIS_PATTERNS = {
    "en": [
        r'\bkill\s+myself\b', r'\bcommit\s+suicide\b', r'\bend\s+my\s+life\b',
        r'\bwant\s+to\s+die\b', r'\btake\s+my\s+(?:own\s+)?life\b',
        r'\bno\s+reason\s+to\s+live\b', r'\bbetter\s+off\s+dead\b',
        r'\bhurt\s+myself\b', r'\bself[\s\-]harm\b', r'\bdon[\'t]*t\s+want\s+to\s+live\b',
        r'\bsuicidal\b', r'\bwish\s+i\s+were\s+dead\b'
    ],
    "te": [
        r'చనిపోవాలని', r'ఆత్మహత్య', r'జీవితం\s*ముగించ', r'బ్రతకాలని\s*లేదు',
        r'ప్రాణం\s*తీసుకో', r'చచ్చిపోవాలి', r'చనిపోతాను', r'ఆత్మహత్య\s*చేసుకోవాలి'
    ],
    "hi": [
        r'आत्महत्या', r'मरना\s*चाहता', r'मरना\s*चाहती', r'जान\s*दे\s*दूंग[ाी]',
        r'जिंदगी\s*खत्म', r'जीने\s*का\s*मन\s*नहीं', r'खुद\s*को\s*मार', r'खुदकुशी'
    ],
    "ta": [
        r'தற்கொலை', r'சாக\s*வேண்டும்', r'உயிரை\s*விட', r'வாழ\s*பிடிக்கவில்லை',
        r'வாழ\s*விருப்பமில்லை', r'செத்துப்போக', r'தற்கொலை\s*செய்து'
    ],
    "ur": [
        r'خودکشی', r'مرنا\s*چاہتا', r'زندگی\s*ختم', r'جینا\s*نہیں\s*چاہتا',
        r'جان\s*لینا', r'خود\s*کو\s*مار'
    ]
}

def detect_crisis(text: str) -> Optional[Dict[str, Any]]:
    """
    SPEC 16c: Scans for self-harm or suicidal intent in English, Telugu, Hindi, Tamil, and Urdu.
    Returns a crisis support payload if detected, otherwise None.
    NEVER provides means or methods. NEVER ends chat abruptly.
    """
    if not text:
        return None
        
    lower = text.lower()
    matched_lang = None
    
    for lang, patterns in CRISIS_PATTERNS.items():
        for pat in patterns:
            if re.search(pat, lower, re.IGNORECASE):
                matched_lang = lang
                break
        if matched_lang:
            break
            
    if not matched_lang:
        return None
        
    # Compassionate multilingual crisis messages
    messages = {
        "en": (
            "We care deeply about you and your life is immensely precious. "
            "You are not alone, and you do not have to carry this heavy pain alone. "
            "Free, compassionate, confidential support is available right now 24/7."
        ),
        "te": (
            "మీ ప్రాణం ఎంతో అమూల్యమైనది. మీ భావాలు, బాధలు మాకు అర్థమవుతున్నాయి, మీరు ఒంటరిగా లేరు. "
            "ఈ క్షణంలోనే మీతో మాట్లాడి మద్దతు ఇవ్వడానికి అర్హత కలిగిన కౌన్సెలర్లు 24 గంటలూ సిద్ధంగా ఉన్నారు."
        ),
        "hi": (
            "आपकी ज़िंदगी बेहद अनमोल है। आप अकेले नहीं हैं, और आपको इस दर्द को अकेले सहने की ज़रूरत नहीं है। "
            "आपकी मदद के लिए 24/7 निःशुल्क और गोपनीय परामर्श तुरंत उपलब्ध है।"
        ),
        "ta": (
            "உங்கள் வாழ்க்கை மிகவும் மதிப்புமிக்கது. நீங்கள் தனியாக இல்லை, இந்த வலியை நீங்கள் தனியாக சுமக்க வேண்டியதில்லை. "
            "உங்களுக்கு உதவ 24/7 இலவச மற்றும் ரகசிய மனநல ஆலோசனை உடனடியாக கிடைக்கிறது."
        ),
        "ur": (
            "آپ کی زندگی انتہائی قیمتی ہے۔ آپ اکیلے نہیں ہیں اور آپ کو یہ بوجھ تنہا اٹھانے کی ضرورت نہیں ہے۔ "
            "آپ کی مدد کے لیے 24 گھنٹے مفت اور بااعتماد مدد دستیاب ہے۔"
        )
    }
    
    return {
        "is_crisis": True,
        "matched_language": matched_lang,
        "compassionate_message": messages.get(matched_lang, messages["en"]),
        "helplines": [
            {
                "name": "Tele-MANAS (Mental Health Free 24x7)",
                "tel": "14416",
                "label": "📞 Call 14416 (Tele-MANAS Free 24x7)"
            },
            {
                "name": "National Emergency Helpline",
                "tel": "112",
                "label": "📞 Call 112 (National Emergency)"
            },
            {
                "name": "KIRAN Mental Health Helpline",
                "tel": "1800-599-0019",
                "label": "📞 Call 1800-599-0019 (KIRAN)"
            }
        ],
        "guidance": "Please reach out right now. Talking to a compassionate counselor can help you find a way forward."
    }


# ==============================================================================
# 2B. DETOX & TAPERING REFUSAL GUARDRAIL (SPEC 16h)
# ==============================================================================

DETOX_TAPERING_PATTERNS = [
    r'\b(detox|detoxification|detoxing)\b',
    r'\b(taper|tapering|tapered|taper off)\b',
    r'\b(wean off|weaning off)\b',
    r'\b(how to (quit|stop) (alcohol|drinking|drugs|heroin|smack|ganja|weed|cannabis|opioid|benzo|ativan|alprazolam|tramadol))\b',
    r'\b(home detox|cold turkey)\b',
    r'\b(dosing schedule|dosage to quit|how many mg to taper|tapering protocol)\b',
    r'\b(withdrawal medication dose|naloxone dose|methadone dose|buprenorphine dose)\b',
    r'\b(detox diet for drugs|flush drugs out of system)\b'
]

def detect_detox_or_tapering(text: str) -> Optional[Dict[str, Any]]:
    """
    SPEC 16h: Strictly refuses to provide detox, dosing, or tapering instructions.
    Explains medical risks (seizures, DTs, respiratory collapse).
    Shows 14446 first for substance dependence.
    Shows 1933 strictly labelled 'to report drug activity, not for treatment'.
    """
    if not text:
        return None

    lower = text.lower()
    is_match = any(re.search(pat, lower, re.IGNORECASE) for pat in DETOX_TAPERING_PATTERNS)
    if not is_match:
        return None

    reply = (
        "🛡️ **Medical Safety Guardrail (SPEC 16h):**\n\n"
        "HealthMate AI **strictly never provides detox protocols, tapering schedules, or medication dosing instructions**.\n\n"
        "⚠️ **Critical Clinical Warning:** Medically unassisted or improper withdrawal from alcohol, benzodiazepines, or opioids "
        "can be life-threatening, carrying severe risks of delirium tremens, grand mal seizures, hallucinations, severe cardiovascular stress, "
        "and fatal relapse. Withdrawal management must always be conducted under the direct supervision of a qualified physician or inpatient addiction medicine center.\n\n"
        "👉 **Official Indian De-Addiction & Medical Support Resources:**\n"
        "• **National Drug De-Addiction Helpline:** [14446](tel:14446) (Ministry of Social Justice & Empowerment — Free, 24x7 confidential counseling, treatment locator & guidance)\n"
        "• **Tele-MANAS Mental Health:** [14416](tel:14416) (Govt. of India 24x7 psychiatric first-aid)\n"
        "• **Emergency Medical Service:** [108](tel:108) Ambulance / [112](tel:112) National Emergency\n\n"
        "ℹ️ **Important Note on 1933:** The Narcotics Control Bureau (NCB) helpline **1933** is strictly **to report illegal drug activity or trafficking**, NOT for medical treatment or de-addiction."
    )

    return {
        "is_detox_tapering_request": True,
        "reply": reply,
        "helplines": [
            {
                "name": "National Drug De-Addiction Helpline",
                "tel": "14446",
                "label": "📞 Call 14446 (National De-Addiction Helpline Free 24x7)"
            },
            {
                "name": "Tele-MANAS (Mental Health)",
                "tel": "14416",
                "label": "📞 Call 14416 (Tele-MANAS Free 24x7)"
            },
            {
                "name": "Ambulance / Emergency",
                "tel": "108",
                "label": "🚑 Call 108 (Ambulance)"
            },
            {
                "name": "NCB Helpline (Report Activity Only)",
                "tel": "1933",
                "label": "📞 1933 (Report Drug Activity Only — Not for Treatment)"
            }
        ]
    }


# ==============================================================================
# 3. ALLERGY & DRUG CONFLICT ENGINE (SPEC 3)
# ==============================================================================

# Known allergy classes and triggering generic medicines
ALLERGY_CONFLICT_RULES = [
    {
        "allergy_terms": ["penicillin", "amoxicillin", "ampicillin", "beta-lactam", "augmentin"],
        "conflicting_meds": ["penicillin", "amoxicillin", "ampicillin", "augmentin", "piperacillin", "cloxacillin"],
        "severity": "CRITICAL",
        "warning": "PENICILLIN ALLERGY CONFLICT: Potential life-threatening anaphylaxis or severe allergic reaction."
    },
    {
        "allergy_terms": ["sulfa", "sulfonamide", "cotrimoxazole", "bactrim"],
        "conflicting_meds": ["cotrimoxazole", "bactrim", "sulfamethoxazole", "sulfasalazine"],
        "severity": "HIGH",
        "warning": "SULFONAMIDE ALLERGY CONFLICT: Risk of severe cutaneous adverse reactions (Stevens-Johnson syndrome)."
    },
    {
        "allergy_terms": ["aspirin", "nsaid", "ibuprofen", "painkillers"],
        "conflicting_meds": ["aspirin", "ibuprofen", "diclofenac", "naproxen", "piroxicam", "aceclofenac"],
        "severity": "HIGH",
        "warning": "NSAID ALLERGY CONFLICT: Risk of bronchospasm, angioedema, or severe urticaria."
    }
]

# Known disease-drug contraindication rules
CONDITION_CONFLICT_RULES = [
    {
        "condition_terms": ["asthma", "copd", "wheezing", "bronchospasm"],
        "conflicting_meds": ["atenolol", "propranolol", "metoprolol", "aspirin", "ibuprofen", "diclofenac"],
        "severity": "HIGH",
        "warning": "ASTHMA/COPD CONTRAINDICATION: Beta-blockers and NSAIDs can induce severe acute bronchospasm."
    },
    {
        "condition_terms": ["peptic ulcer", "gastric ulcer", "stomach bleeding", "gerd", "acid peptic"],
        "conflicting_meds": ["aspirin", "ibuprofen", "diclofenac", "naproxen", "aceclofenac"],
        "severity": "HIGH",
        "warning": "PEPTIC ULCER CONTRAINDICATION: NSAIDs drastically increase the risk of gastrointestinal hemorrhage."
    },
    {
        "condition_terms": ["hypertension", "high blood pressure", "bp", "cardiac"],
        "conflicting_meds": ["pseudoephedrine", "phenylephrine", "nasal decongestants", "nsaids"],
        "severity": "MODERATE",
        "warning": "HYPERTENSION WARNING: Decongestants and systemic NSAIDs can induce severe spikes in arterial blood pressure."
    },
    {
        "condition_terms": ["chronic kidney disease", "ckd", "renal failure", "high creatinine"],
        "conflicting_meds": ["ibuprofen", "diclofenac", "aceclofenac", "metformin", "gentamicin"],
        "severity": "CRITICAL",
        "warning": "RENAL CONTRAINDICATION: Nephrotoxic agents or high-dose NSAIDs can trigger acute kidney injury."
    }
]

def check_allergy_and_drug_conflicts(
    query_text: str,
    allergies: Optional[str] = None,
    conditions: Optional[str] = None,
    active_meds: Optional[List[str]] = None
) -> List[Dict[str, str]]:
    """
    Checks user's query and any proposed medicines against active profile allergies and conditions.
    Returns list of conflict warning objects.
    """
    conflicts = []
    text_lower = query_text.lower()
    allergies_lower = (allergies or "").lower()
    conditions_lower = (conditions or "").lower()
    meds_lower = [m.lower() for m in (active_meds or [])]

    # Check allergy conflicts
    for rule in ALLERGY_CONFLICT_RULES:
        user_has_allergy = any(term in allergies_lower or term in text_lower for term in rule["allergy_terms"])
        if user_has_allergy:
            for med in rule["conflicting_meds"]:
                if med in text_lower or any(med in m for m in meds_lower):
                    conflicts.append({
                        "type": "Allergy Conflict",
                        "severity": rule["severity"],
                        "warning": rule["warning"],
                        "matched_item": med
                    })
                    break

    # Check condition contraindications
    for rule in CONDITION_CONFLICT_RULES:
        user_has_condition = any(term in conditions_lower for term in rule["condition_terms"])
        if user_has_condition:
            for med in rule["conflicting_meds"]:
                if med in text_lower or any(med in m for m in meds_lower):
                    conflicts.append({
                        "type": "Condition Contraindication",
                        "severity": rule["severity"],
                        "warning": rule["warning"],
                        "matched_item": med
                    })
                    break

    return conflicts


# ==============================================================================
# 4. STRUCTURED 10-POINT ASSISTANT RESPONSE ENGINE (SPEC 3)
# ==============================================================================

TOPIC_KNOWLEDGE_BASE = {
    "headache": {
        "title": "Headache & Migraine Assessment",
        "causes": [
            "Tension-type muscle strain from neck/eye fatigue or mental stress",
            "Vascular migraine triggers (lack of sleep, missed meals, dehydration)",
            "Sinus inflammation or cervical spine posture issues",
            "Secondary causes: Elevated blood pressure or medication overuse"
        ],
        "symptoms": [
            "Dull aching band-like pain across the forehead or base of skull",
            "Throbbing unilateral headache accompanied by nausea or light sensitivity",
            "Sinus pressure around eyes and bridge of nose"
        ],
        "home_care": [
            "Rest in a quiet, dark, well-ventilated room",
            "Apply a cold compress across forehead or warm towel to the neck muscles",
            "Perform gentle neck and shoulder stretching exercises",
            "Maintain deep abdominal breathing to relieve tension"
        ],
        "what_to_avoid": [
            "Prolonged unshaded screen time and bright flickering lights",
            "Skipping meals or sleeping less than 7 hours",
            "Excessive caffeine consumption or sudden caffeine withdrawal",
            "Frequent unsupervised usage of over-the-counter pain pills"
        ],
        "diet": [
            "Drink 2.5 to 3 liters of water across the day to prevent dehydration",
            "Consume magnesium-rich foods (spinach, pumpkin seeds, almonds, bananas)",
            "Avoid known dietary triggers such as aged cheeses, MSG, and artificial sweeteners"
        ],
        "tests": [
            {"test": "Blood Pressure (BP)", "normal_range": "< 120/80 mmHg", "why": "Rule out hypertensive headache crisis"},
            {"test": "Serum Electrolytes & Fasting Glucose", "normal_range": "Na: 135-145, Fasting sugar: 70-99 mg/dL", "why": "Check hydration and metabolic balance"},
            {"test": "Refraction / Eye Examination", "normal_range": "20/20 corrected vision", "why": "Rule out refractive error eye strain"},
            {"test": "MRI / CT Brain", "normal_range": "Normal parenchyma without space-occupying lesion", "why": "Ordered only for red-flag or chronic worsening headaches"}
        ],
        "specialist": "General Physician / Neurologist",
        "generic_meds": [
            {"name": "Paracetamol 500mg - 650mg", "timing": "SOS (as needed with meals)"},
            {"name": "Naproxen 250mg (if non-allergic and non-ulcerative)", "timing": "SOS with food"},
            {"name": "Oral Rehydration Salts (ORS)", "timing": "Sip throughout the day for dehydration"}
        ],
        "red_flags": [
            "Sudden severe 'thunderclap' headache reaching maximum intensity in seconds",
            "Headache accompanied by high fever, stiff neck, and confusion (suspected meningitis)",
            "Focal neurological deficits: slurred speech, limb weakness, or vision loss",
            "New headache in adults > 50 years or following head injury"
        ],
        "follow_up": "Keep a 7-day headache diary noting frequency and triggers. Seek in-person clinical review if headaches occur > 2 times weekly."
    },
    "fever": {
        "title": "Fever & Viral Illness Guidance",
        "causes": [
            "Common viral infections (influenza, rhinovirus, seasonal respiratory viruses)",
            "Bacterial infections (urinary tract infection, pharyngitis, enteric fever)",
            "Vector-borne tropical illnesses (Dengue, Malaria, Chikungunya)",
            "Inflammatory or post-vaccination immune responses"
        ],
        "symptoms": [
            "Body temperature above 100.4°F (38°C) measured with a clinical thermometer",
            "Chills, shivering, generalized muscle aches, and fatigue",
            "Mild sweating and loss of appetite"
        ],
        "home_care": [
            "Complete physical bed rest in a well-ventilated room",
            "Lukewarm water sponging on forehead, neck, and armpits (never ice water)",
            "Wear light, breathable cotton clothing",
            "Monitor and log temperature every 4 hours"
        ],
        "what_to_avoid": [
            "Heavy blankets causing excessive heat buildup",
            "Intense physical exertion or continuing routine work",
            "Self-prescribing antibiotics (antibiotics are ineffective against viral fevers)",
            "Dehydrating drinks like commercial sodas or excessive coffee"
        ],
        "diet": [
            "High-fluid intake: coconut water, clear dal soups, kanji (rice gruel), warm herbal teas",
            "Light, easily digestible, fresh home-cooked meals (idli, khichdi, boiled vegetables)",
            "Fresh citrus fruits or amla for natural vitamin C"
        ],
        "tests": [
            {"test": "Complete Blood Count (CBC)", "normal_range": "WBC: 4,000-11,000/mcL, Platelets: 1.5-4.5 Lakhs/mcL", "why": "Assesses infection severity and platelet count"},
            {"test": "Dengue NS1 Antigen & IgM", "normal_range": "Negative / Non-reactive", "why": "Screens for dengue fever in endemic seasons"},
            {"test": "Malarial Smear / Rapid Diagnostic Test", "normal_range": "Negative for Plasmodium species", "why": "Rules out malaria"},
            {"test": "Urine Routine & Microscopy", "normal_range": "Pus cells: 0-5 / HPF", "why": "Screens for urinary tract infection"}
        ],
        "specialist": "General Physician / Internal Medicine Specialist",
        "generic_meds": [
            {"name": "Paracetamol 500mg or 650mg", "timing": "Every 6 hours if temperature > 101°F"},
            {"name": "Oral Rehydration Salts (ORS) Solution", "timing": "1 liter prepared fresh daily"},
            {"name": "Zinc Sulfate 20mg Daily", "timing": "Once daily for immune support"}
        ],
        "red_flags": [
            "Fever exceeding 103°F (39.4°C) or not responding to antipyretics",
            "Difficulty breathing, chest pain, or persistent vomiting with inability to keep fluids down",
            "Petechial rash, spontaneous bleeding from gums or nose, or extreme lethargy",
            "Fever persisting beyond 3 days without improvement"
        ],
        "follow_up": "Consult a registered doctor if fever persists past 48-72 hours or if any warning sign develops."
    },
    "diabetes": {
        "title": "Blood Sugar Management & Diabetes Guide",
        "causes": [
            "Insulin resistance compounded by visceral abdominal obesity and physical inactivity",
            "Decreased pancreatic beta-cell insulin secretion",
            "Genetic predisposition and family history of Type 2 Diabetes",
            "Diets high in refined carbohydrates, sugary beverages, and processed foods"
        ],
        "symptoms": [
            "Polyuria (frequent urination, especially at night)",
            "Polydipsia (increased thirst) and polyphagia (frequent hunger)",
            "Unexplained weight loss despite eating, persistent fatigue, and blurred vision",
            "Slow-healing cuts or recurrent skin/urinary fungal infections"
        ],
        "home_care": [
            "Perform 30 minutes of moderate aerobic exercise daily (brisk walking)",
            "Perform daily diabetic foot self-inspection (check between toes for cuts or blisters)",
            "Maintain consistent meal timings and avoid skipping breakfast",
            "Practice stress management through deep breathing or yoga"
        ],
        "what_to_avoid": [
            "Refined white sugar, sweets, packaged juices, and sugary sodas",
            "Sedentary behavior and prolonged sitting without stretch breaks",
            "Walking barefoot, even indoors (to prevent unnoticed foot ulcers)",
            "Skipping prescribed diabetes medications without medical guidance"
        ],
        "diet": [
            "Fill half your plate with non-starchy vegetables (greens, cucumbers, bitter gourd, beans)",
            "Choose low-glycemic complex carbohydrates (millets, brown rice, whole oats) over white flour",
            "Include lean proteins (boiled eggs, paneer, lentils, sprouted pulses) in every meal",
            "Stay hydrated with plain water, buttermilk, or unsweetened lemon water"
        ],
        "tests": [
            {"test": "Fasting Plasma Glucose (FPG)", "normal_range": "70 - 99 mg/dL (Diabetes >= 126 mg/dL)", "why": "Base morning blood sugar assessment"},
            {"test": "Postprandial Glucose (PPBS - 2 hrs after meal)", "normal_range": "< 140 mg/dL (Diabetes >= 200 mg/dL)", "why": "Measures glycemic response to carbohydrate load"},
            {"test": "Glycated Hemoglobin (HbA1c)", "normal_range": "< 5.7% (Good diabetic control: < 7.0%)", "why": "3-month average blood glucose control indicator"},
            {"test": "Serum Creatinine & eGFR", "normal_range": "Creatinine: 0.7-1.3 mg/dL, eGFR: > 90 mL/min", "why": "Screens for early diabetic nephropathy (kidney strain)"},
            {"test": "Urine Microalbumin / Creatinine Ratio", "normal_range": "< 30 mcg/mg creatinine", "why": "Detects microscopic kidney protein leakage"}
        ],
        "specialist": "Endocrinologist / Diabetologist / General Physician",
        "generic_meds": [
            {"name": "Metformin 500mg Extended Release", "timing": "With evening meal (as prescribed)"},
            {"name": "Glimepiride 1mg", "timing": "Before breakfast (as prescribed)"},
            {"name": "Teneligliptin 20mg", "timing": "Once daily with or without food (as prescribed)"}
        ],
        "red_flags": [
            "Hypoglycemia red flags: Shaky hands, cold sweats, palpitations, confusion (take 15g quick sugar immediately)",
            "Hyperglycemia crisis: Fruity breath, deep rapid breathing, severe vomiting (Diabetic Ketoacidosis)",
            "Non-healing foot wound, blackening of toes, or sudden loss of sensation in lower limbs",
            "Sudden blurry vision or dark floating spots in your visual field"
        ],
        "follow_up": "Check HbA1c every 3 months. Schedule an annual comprehensive dilated eye exam and kidney screen."
    },
    "hypertension": {
        "title": "High Blood Pressure (Hypertension) Care",
        "causes": [
            "High dietary sodium (salt intake > 5 grams / day)",
            "Lack of regular physical activity and excess body weight (BMI > 25)",
            "Chronic mental stress triggering vasoconstrictive neurohormones",
            "Vascular stiffening with age and hereditary arterial factors"
        ],
        "symptoms": [
            "Often completely asymptomatic ('The Silent Killer')",
            "Occasional morning headaches localized to the back of head",
            "Tinnitus (buzzing sounds in ears) or lightheadedness",
            "Shortness of breath or facial flushing during exertion"
        ],
        "home_care": [
            "Adhere to the DASH diet (Dietary Approaches to Stop Hypertension)",
            "Engage in 150 minutes of moderate aerobic activity per week",
            "Measure BP at the same time each morning while seated quietly for 5 minutes",
            "Practice slow pranayama breathing (6 breaths per minute) for 10 minutes daily"
        ],
        "what_to_avoid": [
            "Added table salt, pickles, papads, salted snacks, and instant noodles",
            "Tobacco and smoking (causes immediate acute arterial constriction)",
            "Excessive alcohol intake and unmonitored decongestant nasal sprays",
            "Stopping antihypertensive medicines abruptly"
        ],
        "diet": [
            "Restrict sodium to strictly under 2 grams of sodium (1 level teaspoon salt per day)",
            "Increase potassium-rich vegetables and fruits (spinach, bananas, sweet potatoes, coconut water)",
            "Include garlic, flaxseeds, and unsalted nuts in moderation",
            "Drink plenty of water and herbal teas (hibiscus tea)"
        ],
        "tests": [
            {"test": "Resting Blood Pressure", "normal_range": "< 120/80 mmHg (Stage 1 HTN: 130-139 / 80-89 mmHg)", "why": "Assesses systemic arterial resistance"},
            {"test": "Serum Creatinine & Electrolytes (Na/K)", "normal_range": "Creatinine: 0.7-1.3 mg/dL, Potassium: 3.5-5.0 mEq/L", "why": "Checks renal filtration and electrolyte safety with BP drugs"},
            {"test": "Lipid Profile (Total, LDL, HDL, Triglycerides)", "normal_range": "Total < 200 mg/dL, LDL < 100 mg/dL", "why": "Evaluates overall cardiovascular atherogenic risk"},
            {"test": "Electrocardiogram (ECG - 12 Lead)", "normal_range": "Normal sinus rhythm without LVH (Left Ventricular Hypertrophy)", "why": "Screens for cardiac strain or rhythm changes"}
        ],
        "specialist": "Cardiologist / General Physician",
        "generic_meds": [
            {"name": "Amlodipine 5mg", "timing": "Once daily morning or evening (as prescribed)"},
            {"name": "Telmisartan 40mg", "timing": "Once daily with water (as prescribed)"},
            {"name": "Hydrochlorothiazide 12.5mg", "timing": "Morning dose with breakfast (as prescribed)"}
        ],
        "red_flags": [
            "Hypertensive crisis: Blood pressure > 180/120 mmHg",
            "Crushing chest pressure, pain radiating to left arm or jaw",
            "Sudden severe headache with blurred vision, nausea, or confusion",
            "Sudden shortness of breath or coughing pink frothy sputum"
        ],
        "follow_up": "Check BP monthly once stable. Clinical review every 3-6 months to adjust dosages."
    }
}

def generate_structured_point_by_point_response(
    query_text: str,
    profile: Optional[Dict[str, Any]] = None,
    language: str = "en"
) -> Dict[str, Any]:
    """
    SPEC 3: Produces comprehensive point-by-point medical answer containing:
    1. Causes
    2. Symptoms to watch
    3. Home care
    4. What to avoid
    5. Diet
    6. Tests (with normal ranges explained)
    7. Specialist
    8. Generic medicines ("consult your doctor before use")
    9. Red flags
    10. Follow-up
    Personalized with profile (age, gender, blood group, conditions, allergies, medicines).
    """
    lower = query_text.lower()
    
    # 1. Match topic or select best topic
    matched_key = "headache"
    if any(k in lower for k in ["fever", "temperature", "cold", "flu", "జ్వరం", "దగ్గు"]):
        matched_key = "fever"
    elif any(k in lower for k in ["sugar", "diabetes", "glucose", "hba1c", "మధుమేహం", "డయాబెటిస్"]):
        matched_key = "diabetes"
    elif any(k in lower for k in ["bp", "blood pressure", "hypertension", "రక్తపోటు"]):
        matched_key = "hypertension"
    elif any(k in lower for k in ["headache", "migraine", "head ache", "తలనొప్పి"]):
        matched_key = "headache"
    else:
        for k in TOPIC_KNOWLEDGE_BASE:
            if k in lower:
                matched_key = k
                break

    data = TOPIC_KNOWLEDGE_BASE[matched_key]
    
    # Profile personalization info
    prof_name = profile.get("name", "User") if profile else "User"
    prof_age = profile.get("age", 0) if profile else 0
    prof_gender = profile.get("gender", "") if profile else ""
    prof_blood = profile.get("blood_group", "") if profile else ""
    prof_allergies = profile.get("allergies", "") if profile else ""
    prof_conditions = profile.get("conditions", "") if profile else ""
    prof_meds = profile.get("medicines", []) if profile else []

    # Check conflicts
    conflicts = check_allergy_and_drug_conflicts(
        query_text=query_text + " " + " ".join([m["name"] for m in data["generic_meds"]]),
        allergies=prof_allergies,
        conditions=prof_conditions,
        active_meds=prof_meds
    )

    # Build formatted Markdown response
    lines = []
    
    # Personalized Header Banner
    lines.append(f"### 📋 {data['title']}")
    if profile and (prof_age or prof_blood or prof_conditions or prof_allergies):
        lines.append(
            f"> 👤 **Personalized for:** {prof_name} "
            f"({prof_age}y, {prof_gender or 'Patient'}, Blood Group: {prof_blood or 'Not set'})\n"
            f"> Known Conditions: {prof_conditions or 'None reported'} | Allergies: {prof_allergies or 'None reported'}\n"
        )
    
    # Prominent Allergy & Conflict Warning Banner if detected
    if conflicts:
        lines.append("---")
        lines.append("### 🚨 SAFETY CONFLICT DETECTED")
        for conf in conflicts:
            lines.append(f"⚠️ **[{conf['severity']}] {conf['type']}:** {conf['warning']} *(Matched: {conf['matched_item']})*")
        lines.append("---")

    # 1. Causes
    lines.append("#### 1. 🔬 Possible Causes")
    for c in data["causes"]:
        lines.append(f"• {c}")

    # 2. Symptoms to watch
    lines.append("\n#### 2. 🩺 Symptoms to Watch")
    for s in data["symptoms"]:
        lines.append(f"• {s}")

    # 3. Home Care
    lines.append("\n#### 3. 🏡 Home Care & First Steps")
    for h in data["home_care"]:
        lines.append(f"• {h}")

    # 4. What to Avoid
    lines.append("\n#### 4. 🚫 What to Avoid")
    for a in data["what_to_avoid"]:
        lines.append(f"• {a}")

    # 5. Diet & Nutrition
    lines.append("\n#### 5. 🥗 Everyday Diet & Nutrition")
    for d in data["diet"]:
        lines.append(f"• {d}")

    # 6. Diagnostic Tests with Normal Ranges Explained
    lines.append("\n#### 6. 📑 Diagnostic Tests (Normal Ranges Explained)")
    lines.append("| Test Name | Normal Range Explained | Why It Is Ordered |")
    lines.append("| :--- | :--- | :--- |")
    for t in data["tests"]:
        lines.append(f"| **{t['test']}** | `{t['normal_range']}` | {t['why']} |")

    # 7. Specialist
    lines.append(f"\n#### 7. 👨‍⚕️ Specialist to Consult\n• **{data['specialist']}**")

    # 8. Generic Medicines (with mandatory warning)
    lines.append("\n#### 8. 💊 Commonly Prescribed Generic Medicines")
    lines.append("> ⚠️ **MANDATORY SAFETY GUARDRAIL: Consult your doctor before use.** HealthMate AI does not independently prescribe medications or determine dosages.\n")
    for m in data["generic_meds"]:
        lines.append(f"• **{m['name']}** — *{m['timing']}* [Consult your doctor before use]")

    # 9. Red Flags (Urgent Emergency Signs)
    lines.append("\n#### 9. 🚨 Red Flags (Urgent Emergency Signs)")
    for rf in data["red_flags"]:
        lines.append(f"• **{rf}**")
    lines.append("\n👉 **If any red flags occur, immediately Dial 108 (Free Ambulance) or 112.**")

    # 10. Follow-up Guidelines
    lines.append(f"\n#### 10. 📅 Follow-up Guidelines\n• {data['follow_up']}")

    # AI Error Disclaimer Watermark
    lines.append(
        "\n---\n"
        "ℹ️ *AI-generated information for educational guidance only, may contain errors. "
        "HealthMate AI does not replace licensed medical diagnosis or therapy. "
        "Always consult a registered medical practitioner.*"
    )

    full_markdown = "\n".join(lines)

    quick_replies = [
        "Explain normal test ranges",
        "Diet and nutrition tips",
        "When should I Dial 108?",
        "Find a specialist near me"
    ]

    return {
        "success": True,
        "reply": full_markdown,
        "structured_data": data,
        "topic": matched_key,
        "conflicts": conflicts,
        "quick_replies": quick_replies,
        "has_red_flags": True,
        "emergency_call_button": {
            "label": "🚑 Call 108 Ambulance",
            "tel": "108"
        },
        "disclaimer": "AI-generated information for educational guidance only, may contain errors. Always consult a licensed doctor."
    }

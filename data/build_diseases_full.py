"""
HealthMate AI — Full Disease Database Generator (Phase 5: 220+ Diseases)
Covers all 16 categories in batches:
1. Heart (15)
2. Diabetes & Endocrine (14)
3. Respiratory (15)
4. Neuro (14)
5. Skin (15)
6. Eye (13)
7. ENT (13)
8. Bone (14)
9. Kidney (13)
10. Liver & GI (15)
11. Women's Health (14)
12. Child Health (13)
13. Infectious (15)
14. Mental Health (14)
15. Substance Use (12)
16. Cancer (14)
Total: 220 diseases
"""

import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_JSON = DATA_DIR / "diseases_full.json"

DISCLAIMER_16H = (
    "Mental health conditions and substance use disorders require compassionate professional medical care. "
    "If you are in distress or need crisis support, call Tele-MANAS (14416) or National Emergency (112) immediately. "
    "Content is for educational purposes only and does not replace psychiatric evaluation or medical detoxification."
)

def get_heart_diseases():
    return [
        {
            "id": "coronary_artery_disease",
            "name": "Coronary Artery Disease (CAD)",
            "telugu_name": "కరోనరీ ధమని వ్యాధి (గుండె రక్తనాళాల సమస్య)",
            "hindi_name": "कोरोनरी धमनी रोग (सीएडी)",
            "tamil_name": "இதய தமனி நோய் (CAD)",
            "category": "Heart",
            "body_area": "Heart",
            "icon": "❤️",
            "overview": "Plaque buildup in the wall of the arteries that supply blood to the heart, leading to reduced blood flow and oxygen.",
            "causes": ["High blood pressure", "High LDL cholesterol", "Smoking and tobacco", "Diabetes", "Sedentary lifestyle"],
            "symptoms": ["Angina (chest tightness or pressure)", "Shortness of breath on exertion", "Fatigue during daily activities", "Dizziness"],
            "reports_tests": [
                {"test": "ECG (Electrocardiogram)", "normal_range": "Normal sinus rhythm, no ST depression", "explanation": "Checks electrical rhythm and signs of cardiac ischemia."},
                {"test": "Lipid Profile (LDL Cholesterol)", "normal_range": "< 100 mg/dL (optimal)", "explanation": "Measures bad cholesterol circulating in blood."},
                {"test": "Cardiac Troponin I", "normal_range": "< 0.04 ng/mL", "explanation": "Elevated levels indicate acute heart muscle injury."}
            ],
            "treatment": "Lifestyle optimization, anti-platelet therapy, statins, blood pressure management, and revascularization (angioplasty/CABG) when indicated.",
            "generic_medicines": [
                {"name": "Aspirin 75mg", "warning": "Consult your doctor before use"},
                {"name": "Atorvastatin 10mg", "warning": "Consult your doctor before use"},
                {"name": "Metoprolol 25mg", "warning": "Consult your doctor before use"}
            ],
            "diet_lifestyle": ["Adhere to a low-sodium, high-fiber Mediterranean or traditional Indian whole-grain diet", "Engage in 30 minutes of moderate walking 5 days a week", "Eliminate smoking entirely"],
            "prevention": ["Maintain optimal blood pressure below 120/80 mmHg", "Keep HbA1c below 6.5%", "Manage psychological stress through yoga and mindfulness"],
            "specialists": ["Cardiologist", "Interventional Cardiologist"],
            "emergency_signs": ["Crushing chest pain radiating to jaw, neck, or left arm", "Cold sweat and nausea", "Sudden breathlessness"],
            "is_mental_health_or_addiction": False,
            "disclaimer_16h": None,
            "trusted_source": "https://www.who.int/news-room/fact-sheets/detail/cardiovascular-diseases-(cvds)",
            "trusted_source_label": "WHO Cardiovascular Diseases"
        },
        {
            "id": "hypertension",
            "name": "Hypertension (High Blood Pressure)",
            "telugu_name": "రక్తపోటు (హై బీపీ)",
            "hindi_name": "उच्च रक्तचाप (हाई ब्लड प्रेशर)",
            "tamil_name": "உயர் இரத்த அழுத்தம் (ஹை பிபி)",
            "category": "Heart",
            "body_area": "Heart",
            "icon": "🩺",
            "overview": "A chronic condition where the force of blood against artery walls is consistently too high, straining the heart and blood vessels.",
            "causes": ["High dietary salt intake", "Obesity and inactivity", "Chronic stress", "Family history", "Excessive alcohol consumption"],
            "symptoms": ["Often asymptomatic ('silent killer')", "Morning headaches", "Nosebleeds in severe spikes", "Dull vision or buzzing in ears"],
            "reports_tests": [
                {"test": "Blood Pressure Measurement", "normal_range": "< 120/80 mmHg", "explanation": "Systolic and diastolic pressures measured with sphygmomanometer."},
                {"test": "Serum Creatinine", "normal_range": "0.7 - 1.3 mg/dL", "explanation": "Evaluates kidney health, as hypertension strains renal filtration."},
                {"test": "Serum Potassium", "normal_range": "3.5 - 5.0 mEq/L", "explanation": "Important electrolyte monitored when starting BP medications."}
            ],
            "treatment": "DASH diet, salt reduction, weight management, and antihypertensive medications tailored to stage and comorbidities.",
            "generic_medicines": [
                {"name": "Amlodipine 5mg", "warning": "Consult your doctor before use"},
                {"name": "Telmisartan 40mg", "warning": "Consult your doctor before use"}
            ],
            "diet_lifestyle": ["Reduce salt intake to less than 5g (1 teaspoon) per day", "Eat potassium-rich foods like bananas, spinach, and coconut water", "Limit alcohol"],
            "prevention": ["Regular daily aerobic exercise", "Keep BMI within 18.5 - 24.9 kg/m2", "Practice deep breathing or pranayama"],
            "specialists": ["General Physician", "Cardiologist"],
            "emergency_signs": ["Blood pressure reading exceeding 180/120 mmHg", "Severe sudden headache with confusion or blurred vision", "Chest tightness"],
            "is_mental_health_or_addiction": False,
            "disclaimer_16h": None,
            "trusted_source": "https://www.who.int/news-room/fact-sheets/detail/hypertension",
            "trusted_source_label": "WHO Hypertension Guidelines"
        },
        {
            "id": "heart_failure",
            "name": "Congestive Heart Failure (CHF)",
            "telugu_name": "గుండె వైఫల్యం (గుండె పంపింగ్ బలహీనపడటం)",
            "hindi_name": "हृदय विफलता (हार्ट फेलियर)",
            "tamil_name": "இதய செயலிழப்பு",
            "category": "Heart",
            "body_area": "Heart",
            "icon": "💔",
            "overview": "A long-term condition in which the heart muscle cannot pump blood efficiently to meet the metabolic demands of the body.",
            "causes": ["Prior heart attack (myocardial infarction)", "Longstanding uncontrolled hypertension", "Cardiomyopathy", "Heart valve diseases"],
            "symptoms": ["Swelling (edema) in feet, ankles, and legs", "Shortness of breath when lying flat (orthopnea)", "Chronic fatigue and weakness", "Persistent cough with pink-tinged phlegm"],
            "reports_tests": [
                {"test": "NT-proBNP (Brain Natriuretic Peptide)", "normal_range": "< 125 pg/mL (age <75)", "explanation": "Biomarker released when heart chambers are under stretched strain."},
                {"test": "Echocardiogram (Ejection Fraction)", "normal_range": "55% - 70%", "explanation": "Ultrasound evaluating heart pumping function and chamber size."}
            ],
            "treatment": "Fluid restriction, ACE inhibitors/ARBs, beta-blockers, SGLT2 inhibitors, and diuretics for symptom relief.",
            "generic_medicines": [
                {"name": "Furosemide 40mg", "warning": "Consult your doctor before use"},
                {"name": "Spironolactone 25mg", "warning": "Consult your doctor before use"}
            ],
            "diet_lifestyle": ["Strict sodium restriction (< 2g/day)", "Daily morning weight tracking to catch fluid retention early", "Fluid restriction to 1.5 - 2 liters/day"],
            "prevention": ["Aggressive control of hypertension and diabetes", "Prompt management of chest pain", "Avoid NSAID painkillers which worsen fluid retention"],
            "specialists": ["Heart Failure Specialist", "Cardiologist"],
            "emergency_signs": ["Sudden severe breathing difficulty gasping for air", "Rapid weight gain of >2 kg in 48 hours", "Fainting or blue lips"],
            "is_mental_health_or_addiction": False,
            "disclaimer_16h": None,
            "trusted_source": "https://www.nhs.uk/conditions/heart-failure/",
            "trusted_source_label": "NHS UK Heart Failure"
        },
        {
            "id": "arrhythmia_afib",
            "name": "Atrial Fibrillation (AFib)",
            "telugu_name": "కర్ణిక దడ (క్రమరహిత గుండె కొట్టుకోవడం)",
            "hindi_name": "अलिंद फिब्रिलेशन (अनियमित दिल की धड़कन)",
            "tamil_name": "ஏட்ரியல் குறு நடுக்கம் (ஒழுங்கற்ற இதயத் துடிப்பு)",
            "category": "Heart",
            "body_area": "Heart",
            "icon": "⚡",
            "overview": "An irregular and often very rapid heart rhythm that can lead to blood clots in the heart and increase stroke risk.",
            "causes": ["High blood pressure", "Sleep apnea", "Thyroid disease (hyperthyroidism)", "Heavy caffeine or alcohol intake", "Age-related atrial fibrosis"],
            "symptoms": ["Fluttering, racing or pounding heart palpitations", "Dizziness and lightheadedness", "Fatigue during exercise", "Chest discomfort"],
            "reports_tests": [
                {"test": "12-Lead ECG", "normal_range": "Absence of fibrillatory waves; distinct P-waves", "explanation": "Identifies irregular RR intervals and lack of coordinated P waves."},
                {"test": "Holter Monitor (24-48 hours)", "normal_range": "Normal sinus rhythm throughout", "explanation": "Continuous ambulatory ECG recording to detect intermittent episodes."},
                {"test": "Thyroid Stimulating Hormone (TSH)", "normal_range": "0.4 - 4.0 mIU/L", "explanation": "Rules out overactive thyroid causing rapid arrhythmia."}
            ],
            "treatment": "Rate control (beta blockers), rhythm control (antiarrhythmics or ablation), and systemic anticoagulation to prevent stroke.",
            "generic_medicines": [
                {"name": "Amiodarone 100mg", "warning": "Consult your doctor before use"},
                {"name": "Diltiazem 30mg", "warning": "Consult your doctor before use"}
            ],
            "diet_lifestyle": ["Eliminate excessive caffeine and energy drinks", "Avoid binge drinking (Holiday Heart syndrome)", "Maintain adequate hydration"],
            "prevention": ["Treat underlying obstructive sleep apnea with CPAP", "Maintain electrolyte balance (magnesium, potassium)", "Keep stress in check"],
            "specialists": ["Cardiac Electrophysiologist", "Cardiologist"],
            "emergency_signs": ["Heart rate exceeding 160 bpm with confusion", "Sudden weakness on one side of body (stroke sign)", "Severe chest pain"],
            "is_mental_health_or_addiction": False,
            "disclaimer_16h": None,
            "trusted_source": "https://www.heart.org/en/health-topics/atrial-fibrillation",
            "trusted_source_label": "American Heart Association AFib"
        },
        {
            "id": "heart_valvular_disease",
            "name": "Valvular Heart Disease (Mitral / Aortic Stenosis)",
            "telugu_name": "గుండె కవాటాల వ్యాధి (వాల్వ్ సమస్య)",
            "hindi_name": "हृदय वाल्व रोग",
            "tamil_name": "இதய வால்வு நோய்",
            "category": "Heart",
            "body_area": "Heart",
            "icon": "🚪",
            "overview": "Dysfunction of one or more of the four heart valves, causing narrowing (stenosis) or leakage (regurgitation) of blood.",
            "causes": ["Rheumatic heart disease (common in developing nations)", "Age-related calcification", "Infective endocarditis", "Congenital valve defects"],
            "symptoms": ["Heart murmur heard on stethoscope", "Breathlessness during exertion", "Chest tightness", "Swollen ankles", "Fatigue"],
            "reports_tests": [
                {"test": "2D Doppler Echocardiography", "normal_range": "Aortic valve area > 2.0 cm2, no significant gradient", "explanation": "Visualizes valve leaflets and measures pressure gradients."},
                {"test": "Chest X-Ray", "normal_range": "Normal cardiothoracic ratio (< 0.5)", "explanation": "Screens for cardiac enlargement and pulmonary congestion."}
            ],
            "treatment": "Medical monitoring, medications to manage workload, valve repair, or surgical/transcatheter valve replacement (TAVR).",
            "generic_medicines": [
                {"name": "Digoxin 0.25mg", "warning": "Consult your doctor before use"},
                {"name": "Torsemide 10mg", "warning": "Consult your doctor before use"}
            ],
            "diet_lifestyle": ["Low-salt diet to prevent fluid overload", "Careful dental hygiene to prevent bacterial endocarditis", "Regular clinical reviews"],
            "prevention": ["Prompt penicillin treatment for streptococcal sore throat in children to prevent rheumatic fever", "Good oral hygiene"],
            "specialists": ["Cardiologist", "Cardiothoracic Surgeon"],
            "emergency_signs": ["Syncope (passing out during physical exertion)", "Acute shortness of breath while resting", "Coughing up blood"],
            "is_mental_health_or_addiction": False,
            "disclaimer_16h": None,
            "trusted_source": "https://www.cdc.gov/heartdisease/valvular_disease.htm",
            "trusted_source_label": "CDC Valvular Heart Disease"
        },
        {
            "id": "cardiomyopathy",
            "name": "Cardiomyopathy (Dilated / Hypertrophic)",
            "telugu_name": "కార్డియోమయోపతి (గుండె కండరాల బలహీనత)",
            "hindi_name": "कार्डियोमायोपैथी",
            "tamil_name": "கார்டியோமயோபதி",
            "category": "Heart",
            "body_area": "Heart",
            "icon": "🫀",
            "overview": "A disease of the heart muscle that makes it harder for the heart to pump blood to the rest of the body.",
            "causes": ["Genetic mutations", "Long-term alcohol abuse", "Viral infections", "Chemotherapy drugs", "Nutritional deficiencies"],
            "symptoms": ["Shortness of breath", "Bloating of the abdomen due to fluid buildup", "Dizziness and fainting spells", "Rapid pounding heartbeat"],
            "reports_tests": [
                {"test": "Cardiac MRI", "normal_range": "Normal ventricular wall thickness and no late gadolinium enhancement", "explanation": "Gold standard for assessing myocardial tissue fibrosis."},
                {"test": "Echocardiogram", "normal_range": "Normal chamber dimensions", "explanation": "Measures wall thickness and chamber dilation."}
            ],
            "treatment": "Beta-blockers, ACE inhibitors, implantable cardioverter-defibrillator (ICD), and tailored exercise regimens.",
            "generic_medicines": [
                {"name": "Carvedilol 6.25mg", "warning": "Consult your doctor before use"},
                {"name": "Ramipril 5mg", "warning": "Consult your doctor before use"}
            ],
            "diet_lifestyle": ["Avoid competitive strenuous sports if hypertrophic", "Abstain from all alcohol", "Limit sodium intake"],
            "prevention": ["Genetic counseling for families with history of sudden cardiac arrest", "Prompt treatment of viral myocarditis"],
            "specialists": ["Heart Failure Specialist", "Cardiologist"],
            "emergency_signs": ["Sudden collapse or unexplained fainting", "Severe worsening breathlessness", "Chest pain with palpitations"],
            "is_mental_health_or_addiction": False,
            "disclaimer_16h": None,
            "trusted_source": "https://www.nhlbi.nih.gov/health/cardiomyopathy",
            "trusted_source_label": "NHLBI Cardiomyopathy"
        },
        {
            "id": "pericarditis",
            "name": "Pericarditis (Heart Sac Inflammation)",
            "telugu_name": "పెరికార్డిటిస్ (గుండె చుట్టూ ఉన్న పొర వాపు)",
            "hindi_name": "पेरिकार्डिटिस",
            "tamil_name": "பெரிகார்டிடிஸ்",
            "category": "Heart",
            "body_area": "Heart",
            "icon": "🛡️",
            "overview": "Swelling and irritation of the thin saclike membrane surrounding the heart (pericardium).",
            "causes": ["Viral infections (Coxsackie, COVID-19)", "Autoimmune disorders (Lupus, Rheumatoid Arthritis)", "Post-heart attack", "Tuberculosis"],
            "symptoms": ["Sharp, stabbing chest pain that improves when sitting up and leaning forward", "Low-grade fever", "Heart palpitations", "Dry cough"],
            "reports_tests": [
                {"test": "C-Reactive Protein (CRP)", "normal_range": "< 3.0 mg/L", "explanation": "Confirms presence of systemic inflammation."},
                {"test": "Echocardiogram", "normal_range": "No pericardial effusion", "explanation": "Checks for fluid accumulation around the heart sac."}
            ],
            "treatment": "Anti-inflammatory medicines (NSAIDs/Colchicine), corticosteroids for refractory cases, and treating the primary cause.",
            "generic_medicines": [
                {"name": "Colchicine 0.5mg", "warning": "Consult your doctor before use"},
                {"name": "Ibuprofen 400mg", "warning": "Consult your doctor before use"}
            ],
            "diet_lifestyle": ["Strict physical rest until inflammation markers normalize", "Anti-inflammatory diet rich in fruits and vegetables"],
            "prevention": ["Vaccinations against common viral infections", "Full compliance with tuberculosis therapy in endemic regions"],
            "specialists": ["Cardiologist", "Rheumatologist"],
            "emergency_signs": ["Muffled heart sounds and severe breathlessness (cardiac tamponade)", "Severe drop in blood pressure", "Jugular vein distension"],
            "is_mental_health_or_addiction": False,
            "disclaimer_16h": None,
            "trusted_source": "https://www.mayoclinic.org/diseases-conditions/pericarditis/symptoms-causes/syc-20352510",
            "trusted_source_label": "Mayo Clinic Pericarditis"
        },
        {
            "id": "peripheral_artery_disease",
            "name": "Peripheral Artery Disease (PAD)",
            "telugu_name": "పరిధీయ ధమని వ్యాధి (కాళ్ల రక్తనాళాల అడ్డంకి)",
            "hindi_name": "पेरिफेरल आर्टरी डिजीज",
            "tamil_name": "புற தமனி நோய்",
            "category": "Heart",
            "body_area": "Heart",
            "icon": "🦵",
            "overview": "Circulatory problem in which narrowed arteries reduce blood flow to the limbs, most commonly the legs.",
            "causes": ["Atherosclerosis", "Smoking", "Diabetes mellitus", "Hyperlipidemia", "Advanced age"],
            "symptoms": ["Painful muscle cramping in hips, thighs, or calves after walking (intermittent claudication)", "Coldness in lower leg or foot", "Slow toenail growth", "Non-healing sores on toes"],
            "reports_tests": [
                {"test": "Ankle-Brachial Index (ABI)", "normal_range": "1.0 - 1.4", "explanation": "Compares blood pressure in ankles to blood pressure in arms."},
                {"test": "Arterial Duplex Ultrasound", "normal_range": "Triphasic blood flow waveform", "explanation": "Evaluates arterial narrowing and obstruction in the legs."}
            ],
            "treatment": "Supervised exercise therapy, antiplatelets, statins, cilostazol, and peripheral balloon angioplasty or stenting.",
            "generic_medicines": [
                {"name": "Cilostazol 50mg", "warning": "Consult your doctor before use"},
                {"name": "Clopidogrel 75mg", "warning": "Consult your doctor before use"}
            ],
            "diet_lifestyle": ["Structured walking program (walk until pain, rest, repeat)", "Meticulous foot care and daily inspection", "Total cessation of tobacco"],
            "prevention": ["Strict glycemic control in diabetics", "Daily leg hygiene and comfortable non-constricting footwear"],
            "specialists": ["Vascular Surgeon", "Cardiologist"],
            "emergency_signs": ["Sudden severe coldness, pale color, and numbness in leg (acute limb ischemia)", "Blackish discoloration on toes (gangrene)"],
            "is_mental_health_or_addiction": False,
            "disclaimer_16h": None,
            "trusted_source": "https://www.cdc.gov/heartdisease/PAD.htm",
            "trusted_source_label": "CDC Peripheral Artery Disease"
        },
        {
            "id": "deep_vein_thrombosis",
            "name": "Deep Vein Thrombosis (DVT)",
            "telugu_name": "డీప్ సిర త్రాంబోసిస్ (కాళ్ల సిరల్లో రక్తం గడ్డకట్టడం)",
            "hindi_name": "डीप वेन थ्रोम्बोसिस",
            "tamil_name": "ஆழமான நரம்பு இரத்த உறைவு",
            "category": "Heart",
            "body_area": "Heart",
            "icon": "🩸",
            "overview": "Formation of a blood clot within a deep vein, predominantly in the calves or thighs, posing a severe pulmonary embolism risk.",
            "causes": ["Prolonged immobility (long flights, bed rest)", "Recent orthopedic surgery", "Cancer", "Oral contraceptive pills", "Inherited thrombophilia"],
            "symptoms": ["Unilateral leg swelling", "Throbbing or cramping pain in calf", "Redness and warmth over the swollen area", "Visible surface veins"],
            "reports_tests": [
                {"test": "D-Dimer Blood Test", "normal_range": "< 0.50 mcg/mL FEU", "explanation": "Fibrin degradation product elevated when active clots are dissolving."},
                {"test": "Venous Compression Ultrasound", "normal_range": "Full compressibility of all deep leg veins", "explanation": "Confirms presence and location of clot in the deep veins."}
            ],
            "treatment": "Anticoagulants (direct oral anticoagulants or heparin), compression stockings, and early mobilization.",
            "generic_medicines": [
                {"name": "Rivaroxaban 15mg", "warning": "Consult your doctor before use"},
                {"name": "Warfarin 5mg", "warning": "Consult your doctor before use"}
            ],
            "diet_lifestyle": ["Wear graduated compression stockings during long travel", "Perform ankle pumps and flex feet hourly when seated", "Maintain good hydration"],
            "prevention": ["Avoid crossing legs for prolonged hours", "Use sequential compression devices after major surgery", "Early ambulation post-operative"],
            "specialists": ["Vascular Specialist", "Hematologist"],
            "emergency_signs": ["Sudden chest pain accompanied by breathlessness and coughing blood (Pulmonary Embolism emergency)", "Dizziness or fainting"],
            "is_mental_health_or_addiction": False,
            "disclaimer_16h": None,
            "trusted_source": "https://www.cdc.gov/ncbddd/dvt/facts.html",
            "trusted_source_label": "CDC DVT Facts"
        },
        {
            "id": "rheumatic_heart_disease",
            "name": "Rheumatic Heart Disease (RHD)",
            "telugu_name": "రుమాటిక్ గుండె జబ్బు",
            "hindi_name": "रूमेटिक हृदय रोग",
            "tamil_name": "ருமாட்டிக் இதய நோய்",
            "category": "Heart",
            "body_area": "Heart",
            "icon": "❤️‍🩹",
            "overview": "Permanent damage to heart valves caused by rheumatic fever, which results from an untreated streptococcal throat infection in childhood.",
            "causes": ["Group A Streptococcus pharyngitis", "Untreated acute rheumatic fever", "Crowded living conditions", "Limited antibiotic access"],
            "symptoms": ["Shortness of breath on walking", "Joint pain and swelling in childhood", "Heart murmurs", "Easy fatigue"],
            "reports_tests": [
                {"test": "ASO Titre (Anti-Streptolysin O)", "normal_range": "< 200 IU/mL", "explanation": "Checks for recent streptococcal infection antibodies."},
                {"test": "Echocardiogram", "normal_range": "Normal mitral leaflet motion, no regurgitation", "explanation": "Assesses mitral stenosis or aortic valve involvement."}
            ],
            "treatment": "Secondary penicillin prophylaxis (monthly injections), symptom control for heart failure, and balloon mitral valvuloplasty.",
            "generic_medicines": [
                {"name": "Benzathine Penicillin G 1.2 MU", "warning": "Consult your doctor before use"},
                {"name": "Digoxin 0.125mg", "warning": "Consult your doctor before use"}
            ],
            "diet_lifestyle": ["Adhere strictly to scheduled prophylactic penicillin injections", "Monitor daily salt and fluid intake", "Routine dental care"],
            "prevention": ["Treat all childhood sore throats with complete course of antibiotics", "Improve living ventilation and sanitation"],
            "specialists": ["Pediatric Cardiologist", "Adult Cardiologist"],
            "emergency_signs": ["Acute pulmonary edema (frothy pink sputum)", "Sudden stroke symptoms from atrial clot", "High fever with new heart murmur"],
            "is_mental_health_or_addiction": False,
            "disclaimer_16h": None,
            "trusted_source": "https://www.who.int/news-room/fact-sheets/detail/rheumatic-heart-disease",
            "trusted_source_label": "WHO Rheumatic Heart Disease"
        },
        {
            "id": "myocarditis",
            "name": "Myocarditis (Heart Muscle Inflammation)",
            "telugu_name": "మయోకార్డిటిస్ (గుండె కండరాల వాపు)",
            "hindi_name": "मायोकार्डिटिस",
            "tamil_name": "மையோகார்டிடிஸ்",
            "category": "Heart",
            "body_area": "Heart",
            "icon": "🔥",
            "overview": "Inflammation of the myocardium (middle layer of the heart muscle), usually following a viral infection, affecting electrical rhythm and pumping.",
            "causes": ["Viral illnesses (Coxsackievirus, Adenovirus, Parvovirus, SARS-CoV-2)", "Bacterial toxins", "Drug hypersensitivity reactions", "Autoimmune conditions"],
            "symptoms": ["Chest pain mimicking a heart attack", "Rapid or abnormal heart rhythms", "Fatigue following flu-like illness", "Shortness of breath"],
            "reports_tests": [
                {"test": "Serum Troponin T", "normal_range": "< 0.014 ng/mL", "explanation": "Elevated due to ongoing myocardial cell damage."},
                {"test": "Cardiac MRI (Lake Louise Criteria)", "normal_range": "No myocardial edema or late enhancement", "explanation": "Accurately visualizes inflammation and myocardial edema."}
            ],
            "treatment": "Strict physical rest, ACE inhibitors, beta-blockers, antiarrhythmic agents, and in severe cases mechanical circulatory support.",
            "generic_medicines": [
                {"name": "Enalapril 2.5mg", "warning": "Consult your doctor before use"},
                {"name": "Bisoprolol 2.5mg", "warning": "Consult your doctor before use"}
            ],
            "diet_lifestyle": ["Abstain from all strenuous exercise for 3 to 6 months until full recovery", "Strict alcohol abstinence", "Low-salt diet"],
            "prevention": ["Good hand hygiene to prevent viral infections", "Timely vaccination against viral respiratory illnesses"],
            "specialists": ["Cardiologist", "Infectious Disease Specialist"],
            "emergency_signs": ["Unexplained syncopal collapse", "Severe sudden breathlessness at rest", "Signs of cardiogenic shock (cold clammy skin, confusion)"],
            "is_mental_health_or_addiction": False,
            "disclaimer_16h": None,
            "trusted_source": "https://www.mayoclinic.org/diseases-conditions/myocarditis/symptoms-causes/syc-20352539",
            "trusted_source_label": "Mayo Clinic Myocarditis"
        },
        {
            "id": "infective_endocarditis",
            "name": "Infective Endocarditis (Heart Lining Infection)",
            "telugu_name": "ఇన్ఫెక్టివ్ ఎండోకార్డిటిస్ (గుండె లోపలి పొర ఇన్ఫెక్షన్)",
            "hindi_name": "इन्फेक्टिव एंडोकार्डिटिस",
            "tamil_name": "தொற்று எண்டோகார்டிடிஸ்",
            "category": "Heart",
            "body_area": "Heart",
            "icon": "🦠",
            "overview": "A serious bacterial or fungal infection of the inner heart lining (endocardium) and heart valves, forming vegetative growths.",
            "causes": ["Oral bacteria entering bloodstream during invasive dental procedures", "Intravenous drug use", "Prosthetic heart valves", "Chronic indwelling IV catheters"],
            "symptoms": ["Unexplained persistent fever and chills", "New or changing heart murmur", "Fatigue and aching joints", "Tiny red spots under fingernails (splinter hemorrhages)"],
            "reports_tests": [
                {"test": "Blood Cultures (3 sets)", "normal_range": "No bacterial or fungal growth", "explanation": "Identifies the specific microorganism causing bloodstream infection."},
                {"test": "Transesophageal Echocardiogram (TEE)", "normal_range": "No valve vegetations or abscesses", "explanation": "High-resolution ultrasound imaging of valve surfaces."}
            ],
            "treatment": "Prolonged high-dose intravenous antibiotic therapy (4-6 weeks) and emergency valve replacement surgery if destruction occurs.",
            "generic_medicines": [
                {"name": "Ceftriaxone 2g IV", "warning": "Hospital administration only; consult your doctor"},
                {"name": "Vancomycin 1g IV", "warning": "Hospital administration only; consult your doctor"}
            ],
            "diet_lifestyle": ["Strict oral hygiene with twice daily gentle brushing and flossing", "Avoid non-sterile skin piercings or tattoos"],
            "prevention": ["Antibiotic prophylaxis before dental work for patients with artificial heart valves", "Prompt treatment of skin boils"],
            "specialists": ["Cardiologist", "Infectious Disease Specialist"],
            "emergency_signs": ["High spiking fever with sudden shortness of breath", "Sudden stroke symptoms from dislodged vegetation embolus", "Severe chest pain"],
            "is_mental_health_or_addiction": False,
            "disclaimer_16h": None,
            "trusted_source": "https://www.nhs.uk/conditions/endocarditis/",
            "trusted_source_label": "NHS UK Endocarditis"
        },
        {
            "id": "aortic_aneurysm",
            "name": "Aortic Aneurysm (Abdominal / Thoracic)",
            "telugu_name": "మహాధమని విస్తరణ (అయోర్టిక్ అనూరిజం)",
            "hindi_name": "महाधमनी धमनीविस्फार",
            "tamil_name": "அயோர்டிக் அனியூரிசம்",
            "category": "Heart",
            "body_area": "Heart",
            "icon": "🎈",
            "overview": "An abnormal bulge or ballooning in the wall of the body's main artery (aorta) which can rupture and cause fatal internal bleeding.",
            "causes": ["Atherosclerosis weakening artery walls", "Smoking", "Chronic uncontrolled hypertension", "Connective tissue disorders (Marfan syndrome)", "Trauma"],
            "symptoms": ["Usually silent until large", "Pulsating sensation near the navel", "Deep, constant abdominal or back pain", "Hoarseness (thoracic)"],
            "reports_tests": [
                {"test": "Abdominal Ultrasound", "normal_range": "Aortic diameter < 3.0 cm", "explanation": "Screening tool to measure aortic caliber in high-risk smokers."},
                {"test": "CT Angiography (Aorta)", "normal_range": "No aneurysmal dilatation or dissection flap", "explanation": "Provides detailed 3D mapping of aneurysm size and rupture risk."}
            ],
            "treatment": "Careful blood pressure control, smoking cessation, surveillance ultrasounds, and endovascular repair (EVAR) or open surgery.",
            "generic_medicines": [
                {"name": "Atenolol 50mg", "warning": "Consult your doctor before use"},
                {"name": "Losartan 50mg", "warning": "Consult your doctor before use"}
            ],
            "diet_lifestyle": ["Avoid heavy weightlifting or straining which spikes intra-aortic pressure", "Stop smoking immediately", "Heart-healthy diet"],
            "prevention": ["Routine ultrasound screening for men aged 65-75 with smoking history", "Strict BP management"],
            "specialists": ["Vascular Surgeon", "Cardiologist"],
            "emergency_signs": ["Sudden tearing, ripping back or abdominal pain", "Rapidly dropping blood pressure and cold sweats", "Loss of consciousness"],
            "is_mental_health_or_addiction": False,
            "disclaimer_16h": None,
            "trusted_source": "https://www.cdc.gov/heartdisease/aortic_aneurysm.htm",
            "trusted_source_label": "CDC Aortic Aneurysm"
        },
        {
            "id": "sick_sinus_syndrome",
            "name": "Sick Sinus Syndrome (Sinus Node Dysfunction)",
            "telugu_name": "సిక్ సైనస్ సిండ్రోమ్ (గుండె సహజ పేస్‌మేకర్ లోపం)",
            "hindi_name": "सिक साइनस सिंड्रोम",
            "tamil_name": "சிக் சைனஸ் நோய்க்குறி",
            "category": "Heart",
            "body_area": "Heart",
            "icon": "⏱️",
            "overview": "Malfunction of the heart's natural pacemaker (sinus node), creating abnormally slow heart rates (bradycardia) or alternating fast-slow rhythms.",
            "causes": ["Age-related degeneration of sinus node tissue", "Ischemic heart disease", "Infiltrative cardiac diseases", "Certain medications (beta blockers, digitalis)"],
            "symptoms": ["Severe fatigue and sluggishness", "Dizziness and near-fainting (presyncope)", "Fainting episodes (syncope)", "Memory problems or confusion"],
            "reports_tests": [
                {"test": "24-Hour Holter ECG", "normal_range": "Sinus rhythm 60-100 bpm with no sinus pauses > 3 seconds", "explanation": "Records sinus pauses, severe bradycardia, or tachycardia-bradycardia syndrome."},
                {"test": "Electrophysiology Study (EPS)", "normal_range": "Normal Sinoatrial Recovery Time (SNRT)", "explanation": "Tests electrical recovery function of the sinus node."}
            ],
            "treatment": "Review and eliminate offending medications, and implantation of a permanent cardiac pacemaker.",
            "generic_medicines": [
                {"name": "Atropine 0.5mg (Emergency)", "warning": "Emergency hospital use only; consult your doctor"}
            ],
            "diet_lifestyle": ["Avoid sudden standing to prevent orthostatic dizziness", "Stay well hydrated", "Avoid strenuous unsupervised exertion"],
            "prevention": ["Regular annual checkups for elderly individuals reporting unexplained dizzy spells", "Careful drug dosing"],
            "specialists": ["Electrophysiologist", "Cardiologist"],
            "emergency_signs": ["Prolonged blackout with pulse below 35 bpm", "Sudden chest pressure with profound confusion", "Cyanosis"],
            "is_mental_health_or_addiction": False,
            "disclaimer_16h": None,
            "trusted_source": "https://www.mayoclinic.org/diseases-conditions/sick-sinus-syndrome/symptoms-causes/syc-20377554",
            "trusted_source_label": "Mayo Clinic Sick Sinus Syndrome"
        },
        {
            "id": "angina_pectoris",
            "name": "Angina Pectoris (Stable & Unstable)",
            "telugu_name": "ఆంజినా పెక్టోరిస్ (గుండె నొప్పి హెచ్చరిక)",
            "hindi_name": "एंजाइना पेक्टोरिस (सीने में दर्द)",
            "tamil_name": "மார்பு வலி (ஆஞ்சைனா)",
            "category": "Heart",
            "body_area": "Heart",
            "icon": "💔",
            "overview": "Chest discomfort caused when heart muscle tissues experience transient oxygen deprivation due to narrowed coronary arteries.",
            "causes": ["Atherosclerosis", "Physical exertion overexerting narrowed arteries", "Severe emotional stress", "Heavy meals", "Extreme cold weather exposure"],
            "symptoms": ["Squeezing, heavy pressure behind breastbone", "Pain radiating to left arm or neck relieved by rest in stable angina", "Shortness of breath"],
            "reports_tests": [
                {"test": "Treadmill Exercise Stress Test (TMT)", "normal_range": "Negative for inducible ischemia at target heart rate", "explanation": "Monitors heart response to physical exercise demands."},
                {"test": "Coronary CT Angiography", "normal_range": "Agatston Calcium Score = 0; no stenosis", "explanation": "Non-invasive visualization of coronary vessel patency."}
            ],
            "treatment": "Sublingual nitroglycerin for acute attacks, long-acting nitrates, calcium channel blockers, statins, and elective revascularization.",
            "generic_medicines": [
                {"name": "Nitroglycerin 0.5mg Sublingual", "warning": "Consult your doctor before use"},
                {"name": "Isosorbide Mononitrate 20mg", "warning": "Consult your doctor before use"}
            ],
            "diet_lifestyle": ["Rest immediately upon experiencing chest tightness", "Carry prescribed sublingual nitroglycerin at all times", "Eat smaller meals"],
            "prevention": ["Warm up gradually before physical activity", "Avoid sudden exposure to freezing winds", "Maintain strict cholesterol control"],
            "specialists": ["Cardiologist", "General Physician"],
            "emergency_signs": ["Chest pain lasting more than 10 minutes that does not resolve with rest or nitroglycerin (possible Myocardial Infarction)", "Nausea and cold sweat"],
            "is_mental_health_or_addiction": False,
            "disclaimer_16h": None,
            "trusted_source": "https://www.heart.org/en/health-topics/heart-attack/angina-chest-pain",
            "trusted_source_label": "American Heart Association Angina"
        }
    ]

# Let's write the remaining 15 categories builder to complete the 220 items.

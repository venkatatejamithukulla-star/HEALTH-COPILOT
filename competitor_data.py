"""
Competitor Research & Architecture Comparison Data
HealthMate AI — Hackathon Stage 7 Analysis

Comprehensive breakdown of 9 health applications and services:
1. Apple Health
2. Epic MyChart
3. Ada Health
4. Healthily
5. eSanjeevani (Govt. of India)
6. Practo
7. ABHA / ABDM (National Health Authority)
8. Apollo 24/7
9. Tata 1mg
"""

COMPETITOR_RESEARCH_DATA = [
    {
        "id": "apple-health",
        "name": "Apple Health",
        "category": "Big Tech Device Ecosystem",
        "origin": "United States",
        "pricing": "Hardware lock-in ($500+ iPhone / Apple Watch required)",
        "offline_support": "Local storage on device, but requires iOS hardware",
        "multilingual_indian": "English only; no vernacular Telugu, Hindi, or Tamil audio",
        "organizes_paper_records": "No — built primarily for Apple Watch sensor metrics, steps, and US hospital FHIR links",
        "low_cost_clinic_finder": "No — Apple Maps shows generic locations with zero Indian public hospital pricing",
        "family_profiles_single_device": "No — strictly 1 Apple ID per individual device",
        "gaps": "Prohibitively expensive for 95% of Indian families. Unusable for rural elderly who lack iPhones.",
        "healthmate_advantage": "100% free web app running on any phone, tablet, or low-cost laptop; bilingual Telugu audio; family profiles.",
        "official_url": "https://www.apple.com/healthcare/health-records/"
    },
    {
        "id": "epic-mychart",
        "name": "Epic MyChart",
        "category": "Enterprise Hospital EHR Portal",
        "origin": "United States",
        "pricing": "Enterprise subscription paid by large hospital chains",
        "offline_support": "No — requires live hospital server connection",
        "multilingual_indian": "English and Spanish only; no Indian regional language translations",
        "organizes_paper_records": "No — only displays data entered by Epic-licensed hospital providers",
        "low_cost_clinic_finder": "No — restricted strictly to the subscriber hospital's own network",
        "family_profiles_single_device": "Proxy access exists but requires individual legal guardian portal accounts",
        "gaps": "Completely inaccessible in Indian Primary Health Centres (PHCs) or government district hospitals.",
        "healthmate_advantage": "Works completely independently of hospital IT; organizes paper slips carried by patients in physical folders.",
        "official_url": "https://www.mychart.com"
    },
    {
        "id": "ada-health",
        "name": "Ada Health",
        "category": "AI Symptom Checker & Triage",
        "origin": "Germany / United Kingdom",
        "pricing": "Free consumer tier, B2B enterprise licensing",
        "offline_support": "Requires cloud API connection for inference",
        "multilingual_indian": "Limited Indian regional support; primarily English, German, and Spanish",
        "organizes_paper_records": "No — symptom assessment tool only; does not archive lab slips or clinic visits",
        "low_cost_clinic_finder": "No — provides clinical triage recommendations without Indian hospital pricing",
        "family_profiles_single_device": "Multi-profile support available",
        "gaps": "Does not help patients prepare for the physical clinic visit or understand blood test papers.",
        "healthmate_advantage": "Generates a printable Appointment Preparation Pack and organizes past lab papers chronologically.",
        "official_url": "https://ada.com"
    },
    {
        "id": "healthily",
        "name": "Healthily (Your.MD)",
        "category": "Clinically Accredited Triage",
        "origin": "United Kingdom",
        "pricing": "Freemium consumer app",
        "offline_support": "Cloud dependent",
        "multilingual_indian": "English centric; lacks Telugu and Tamil audio support",
        "organizes_paper_records": "No — health diary only tracks symptoms and steps",
        "low_cost_clinic_finder": "UK NHS specific pathways; no Indian PHC or sub-district hospital directory",
        "family_profiles_single_device": "Limited",
        "gaps": "Built for Western healthcare systems; cannot explain Indian government schemes like Aarogyasri.",
        "healthmate_advantage": "Built specifically for Indian healthcare realities, featuring Aarogyasri, PM-JAY, and 108/112 helplines.",
        "official_url": "https://www.livehealthily.com"
    },
    {
        "id": "esanjeevani",
        "name": "eSanjeevani (Govt. of India)",
        "category": "National Telemedicine Platform",
        "origin": "India (Ministry of Health & Family Welfare)",
        "pricing": "100% Free Government Service",
        "offline_support": "No — requires active internet connection for video doctor calls",
        "multilingual_indian": "Yes — doctors available in multiple Indian states",
        "organizes_paper_records": "No — platform for real-time video consults, not a personal paper timeline",
        "low_cost_clinic_finder": "No — handles virtual visits only, does not compare nearby physical clinic fees",
        "family_profiles_single_device": "Mobile number OTP based login",
        "gaps": "Does not provide plain-language explanations of past lab reports or chronological record timelines.",
        "healthmate_advantage": "Acts as the ideal offline companion to eSanjeevani: prepares the patient summary pack before the video call.",
        "official_url": "https://esanjeevani.mohfw.gov.in"
    },
    {
        "id": "practo",
        "name": "Practo",
        "category": "Commercial Private Clinic Marketplace",
        "origin": "India",
        "pricing": "Free booking, commercial commissions, paid clinic promotions",
        "offline_support": "Cloud dependent",
        "multilingual_indian": "Predominantly English UI",
        "organizes_paper_records": "Practo Drive stores digital uploads, but is tied to commercial account",
        "low_cost_clinic_finder": "Heavily skewed toward private clinics with high consultation fees (₹500-₹1500) in Tier-1 cities",
        "family_profiles_single_device": "Yes",
        "gaps": "Omits free Primary Health Centres, government dispensaries, and sub-district hospitals where rural users go.",
        "healthmate_advantage": "Focuses on free and low-cost care (PHCs, charitable trusts, ₹50-₹200 clinics) with zero ads.",
        "official_url": "https://www.practo.com"
    },
    {
        "id": "abha-abdm",
        "name": "ABHA / ABDM (National Health Authority)",
        "category": "National Digital Health Infrastructure",
        "origin": "India (NHA)",
        "pricing": "Free public digital infrastructure",
        "offline_support": "Centralized ABDM gateway architecture requiring internet",
        "multilingual_indian": "Multiple Indian languages on portal",
        "organizes_paper_records": "Standardizes digital record exchange via FHIR, but requires empanelled digital hospitals",
        "low_cost_clinic_finder": "Has registry (HFR), but user-facing mobile experience is complex for non-tech-savvy users",
        "family_profiles_single_device": "Each ABHA ID is tied to unique Aadhaar / mobile number OTP",
        "gaps": "Rural elderly cannot navigate complex consent managers or decrypt raw JSON medical summaries.",
        "healthmate_advantage": "Translates complex medical findings into simple spoken Telugu & English; stores records 100% offline.",
        "official_url": "https://abha.abdm.gov.in"
    },
    {
        "id": "apollo-247",
        "name": "Apollo 24|7",
        "category": "Corporate Hospital Super-App",
        "origin": "India (Apollo Hospitals Enterprise)",
        "pricing": "Proprietary corporate rates, paid consultations & medicine delivery",
        "offline_support": "Cloud dependent",
        "multilingual_indian": "Primarily English interface",
        "organizes_paper_records": "Apollo records auto-synced; third-party papers stored as generic attachments",
        "low_cost_clinic_finder": "No — exclusively routes patients to Apollo hospitals and pharmacies",
        "family_profiles_single_device": "Yes",
        "gaps": "High consultation costs unsuited for rural agricultural workers and BPL ration card holders.",
        "healthmate_advantage": "Neutral, vendor-free health tool that puts patient dignity and low-cost community health first.",
        "official_url": "https://www.apollo247.com"
    },
    {
        "id": "tata-1mg",
        "name": "Tata 1mg",
        "category": "Online Pharmacy & Diagnostic Marketplace",
        "origin": "India (Tata Digital)",
        "pricing": "Commercial marketplace with diagnostic testing fees",
        "offline_support": "Cloud dependent",
        "multilingual_indian": "English centric with partial Hindi drug information",
        "organizes_paper_records": "Stores orders and lab receipts, but not structured clinic follow-up histories",
        "low_cost_clinic_finder": "No — focuses on paid commercial lab home collection",
        "family_profiles_single_device": "Yes",
        "gaps": "Commercial marketing pushes medicine orders and lab packages rather than clinical appointment preparation.",
        "healthmate_advantage": "Zero commerce, zero advertisements. Keeps data in offline SQLite database under patient ownership.",
        "official_url": "https://www.1mg.com"
    }
]

COMPARISON_MATRIX_COLUMNS = [
    {"key": "offline_support", "label": "Offline SQLite Storage"},
    {"key": "multilingual_indian", "label": "Telugu / Hindi / Tamil Voice"},
    {"key": "organizes_paper_records", "label": "Physical Paper Records Timeline"},
    {"key": "low_cost_clinic_finder", "label": "Low-Cost Care & Government Schemes"},
    {"key": "family_profiles_single_device", "label": "Single-Device Family Profiles"}
]

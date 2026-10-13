"""
HealthMate AI — Low-Cost Care Finder & Government Schemes Data (Stage 4)

FICTITIOUS SAMPLE DATA FOR HACKATHON DEMONSTRATION ONLY.
All facilities, doctor names, and telephone numbers below are simulated examples
to demonstrate UI filtering and accessibility.

Specialties covered:
- Dental
- Skin (Dermatology)
- Bones (Orthopedics)
- Neurology (Brain & Nerves)
- Women's Health (Gynecology, with female-doctor filter)
- General Medicine
"""

CARE_FACILITIES = [
    # ---------------- DENTAL ----------------
    {
        "id": "fac_01",
        "name": "Janata Dental & Oral Health Clinic",
        "type": "Clinic",
        "specialty": "Dental",
        "doctor_name": "Dr. P. Suresh",
        "is_female_doctor": False,
        "state": "Telangana",
        "district": "Hyderabad",
        "area": "Koti Community Centre",
        "area_type": "Urban",
        "fee": "₹50 (Subsidized)",
        "is_free_or_low_cost": True,
        "opening_hours": "09:00 AM - 01:00 PM (Mon-Sat)",
        "phone_placeholder": "040-2465-XXXX",
        "services": ["Tooth Filling", "Scaling & Cleaning", "Tooth Extraction", "Pain Relief"]
    },
    {
        "id": "fac_02",
        "name": "Rural Mobile Dental Van",
        "type": "Mobile Clinic",
        "specialty": "Dental",
        "doctor_name": "Dr. K. Swathi",
        "is_female_doctor": True,
        "state": "Telangana",
        "district": "Warangal",
        "area": "Narsampet Village Market",
        "area_type": "Rural",
        "fee": "Free / Govt",
        "is_free_or_low_cost": True,
        "opening_hours": "10:00 AM - 03:00 PM (Tue, Thu, Sat)",
        "phone_placeholder": "0870-254-XXXX",
        "services": ["Free Dental Screening", "Emergency Extraction", "Fluoride Varnish"]
    },

    # ---------------- SKIN (DERMATOLOGY) ----------------
    {
        "id": "fac_03",
        "name": "Charminar Skin & Allergy Care Centre",
        "type": "Hospital",
        "specialty": "Skin",
        "doctor_name": "Dr. Farzana Begum",
        "is_female_doctor": True,
        "state": "Telangana",
        "district": "Hyderabad",
        "area": "Charminar Old City",
        "area_type": "Urban",
        "fee": "₹100",
        "is_free_or_low_cost": True,
        "opening_hours": "10:00 AM - 02:00 PM (Daily)",
        "phone_placeholder": "040-2452-XXXX",
        "services": ["Eczema Treatment", "Fungal Rash Clinic", "Allergy Patch Test"]
    },
    {
        "id": "fac_04",
        "name": "District Skin Health Camp",
        "type": "Govt Hospital",
        "specialty": "Skin",
        "doctor_name": "Dr. M. Venkat Rao",
        "is_female_doctor": False,
        "state": "Andhra Pradesh",
        "district": "Visakhapatnam",
        "area": "Anakapalle Sub-District Hospital",
        "area_type": "Rural",
        "fee": "Free / Govt",
        "is_free_or_low_cost": True,
        "opening_hours": "09:00 AM - 01:00 PM (Mon-Fri)",
        "phone_placeholder": "0891-274-XXXX",
        "services": ["Fungal Ringworm Care", "Scabies Screening", "Free Ointment Distribution"]
    },

    # ---------------- BONES (ORTHOPEDICS) ----------------
    {
        "id": "fac_05",
        "name": "Arogya Orthopedic & Joint Care Clinic",
        "type": "Clinic",
        "specialty": "Bones",
        "doctor_name": "Dr. K. Raghavendra",
        "is_female_doctor": False,
        "state": "Telangana",
        "district": "Hyderabad",
        "area": "Secunderabad Station Road",
        "area_type": "Urban",
        "fee": "₹150",
        "is_free_or_low_cost": True,
        "opening_hours": "04:00 PM - 08:00 PM (Mon-Sat)",
        "phone_placeholder": "040-2780-XXXX",
        "services": ["Knee Arthritis Assessment", "Plaster & Splints", "Low-Cost X-Ray"]
    },
    {
        "id": "fac_06",
        "name": "Karimnagar Community Bone & Joint Care",
        "type": "Govt Clinic",
        "specialty": "Bones",
        "doctor_name": "Dr. Sunita Reddy",
        "is_female_doctor": True,
        "state": "Telangana",
        "district": "Karimnagar",
        "area": "Civil Hospital Compound",
        "area_type": "Urban",
        "fee": "Free / Govt",
        "is_free_or_low_cost": True,
        "opening_hours": "09:00 AM - 01:00 PM (Daily)",
        "phone_placeholder": "0878-224-XXXX",
        "services": ["Fracture First Aid", "Osteoporosis Counseling", "Walking Aids Assistance"]
    },

    # ---------------- NEUROLOGY ----------------
    {
        "id": "fac_07",
        "name": "City Neuro & Headache Care",
        "type": "Hospital",
        "specialty": "Neurology",
        "doctor_name": "Dr. A. Srinivas",
        "is_female_doctor": False,
        "state": "Telangana",
        "district": "Hyderabad",
        "area": "Nampally Main Road",
        "area_type": "Urban",
        "fee": "₹200",
        "is_free_or_low_cost": False,
        "opening_hours": "11:00 AM - 03:00 PM (Mon, Wed, Fri)",
        "phone_placeholder": "040-2320-XXXX",
        "services": ["Migraine Management", "Diabetic Neuropathy Review", "Nerve Reflex Exam"]
    },
    {
        "id": "fac_08",
        "name": "Krishna District Neuro Screening Camp",
        "type": "Govt Clinic",
        "specialty": "Neurology",
        "doctor_name": "Dr. Deepa Nair",
        "is_female_doctor": True,
        "state": "Andhra Pradesh",
        "district": "Vijayawada",
        "area": "Machilipatnam Area Hospital",
        "area_type": "Rural",
        "fee": "Free / Govt",
        "is_free_or_low_cost": True,
        "opening_hours": "09:30 AM - 01:30 PM (Wednesdays)",
        "phone_placeholder": "0866-248-XXXX",
        "services": ["Epilepsy Medicine Refills", "Tingling & Numbness Screening", "Stroke Prevention Advice"]
    },

    # ---------------- WOMEN'S HEALTH (GYNECOLOGY) ----------------
    {
        "id": "fac_09",
        "name": "Stree Arogya Matru Seva Kendra",
        "type": "Maternity & Health Centre",
        "specialty": "Women's Health",
        "doctor_name": "Dr. Shailaja Devi",
        "is_female_doctor": True,
        "state": "Telangana",
        "district": "Hyderabad",
        "area": "Dilsukhnagar Metro Pillar 140",
        "area_type": "Urban",
        "fee": "₹80",
        "is_free_or_low_cost": True,
        "opening_hours": "09:00 AM - 02:00 PM (Mon-Sat)",
        "phone_placeholder": "040-2404-XXXX",
        "services": ["Anemia Screening (Free Hb)", "PCOS Diet Guidance", "Antenatal Checkups", "Pap Smear"]
    },
    {
        "id": "fac_10",
        "name": "Primary Health Centre (PHC) Matru Ward",
        "type": "Govt Health Centre",
        "specialty": "Women's Health",
        "doctor_name": "Dr. Kavitha Lakshmi",
        "is_female_doctor": True,
        "state": "Telangana",
        "district": "Warangal",
        "area": "Mulugu Road PHC",
        "area_type": "Rural",
        "fee": "Free / Govt",
        "is_free_or_low_cost": True,
        "opening_hours": "24x7 Emergency / OPD: 09:00 AM - 01:00 PM",
        "phone_placeholder": "0870-242-XXXX",
        "services": ["Free Iron & Folic Acid", "Normal Delivery Services", "Adolescent Nutrition Guidance"]
    },

    # ---------------- GENERAL MEDICINE & BLOOD BANKS ----------------
    {
        "id": "fac_11",
        "name": "Red Cross District Blood Centre",
        "type": "Blood Bank",
        "specialty": "General Medicine",
        "doctor_name": "Duty Medical Officer",
        "is_female_doctor": False,
        "state": "Telangana",
        "district": "Hyderabad",
        "area": "Vidyanagar Red Cross Building",
        "area_type": "Urban",
        "fee": "Free / Govt (Govt Hosp Requisition)",
        "is_free_or_low_cost": True,
        "opening_hours": "24 Hours Open",
        "phone_placeholder": "040-2763-XXXX",
        "services": ["Whole Blood", "Packed Red Cells", "Platelet Apheresis", "Blood Group Testing"]
    },
    {
        "id": "fac_12",
        "name": "Community Health Centre (CHC)",
        "type": "Govt Hospital",
        "specialty": "General Medicine",
        "doctor_name": "Dr. B. Prasad",
        "is_female_doctor": False,
        "state": "Andhra Pradesh",
        "district": "Visakhapatnam",
        "area": "Pendurthi Junction",
        "area_type": "Rural",
        "fee": "Free / Govt",
        "is_free_or_low_cost": True,
        "opening_hours": "08:30 AM - 01:30 PM (Daily)",
        "phone_placeholder": "0891-255-XXXX",
        "services": ["Fever Clinic", "Diabetes & BP OPD", "Essential Generic Medicines", "108 Ambulance Base"]
    }
]

# Government Schemes Information (Non-prescriptive, official links only)
GOVERNMENT_SCHEMES = [
    {
        "name": "eSanjeevani (National Teleconsultation Service)",
        "sponsor": "Ministry of Health & Family Welfare, Govt. of India",
        "description": "Free online doctor consultation platform connecting citizens directly with registered MBBS and specialist doctors from home via video/audio call.",
        "cost": "100% Free of Cost",
        "official_url": "https://esanjeevani.mohfw.gov.in",
        "note": "Open official website to verify consultation timings in your state."
    },
    {
        "name": "Ayushman Bharat PM-JAY",
        "sponsor": "National Health Authority (NHA), Govt. of India",
        "description": "Health assurance scheme providing up to ₹5 Lakh cashless coverage per eligible family per year for secondary and tertiary hospitalization.",
        "cost": "Cashless at Empanelled Hospitals for Eligible Families",
        "official_url": "https://pmjay.gov.in",
        "note": "Eligibility is determined by official SECC database; check the official site using your ration card or mobile number."
    },
    {
        "name": "Aarogyasri Health Scheme",
        "sponsor": "Govt. of Telangana & Andhra Pradesh",
        "description": "State flagship health scheme providing cashless medical treatment to low-income families holding valid food security/Aarogyasri cards.",
        "cost": "Cashless at Empanelled Hospitals",
        "official_url": "https://aarogyasri.telangana.gov.in",
        "note": "Empanelled hospitals and covered treatments are updated by the trust; check the official portal to confirm hospital list."
    }
]

REAL_DATA_INTEGRATION_ROADMAP = {
    "step_1": {
        "title": "Phase 1 (Hackathon Prototype): Fictitious Sample Data",
        "cost": "₹0 (Zero cost)",
        "details": "Simulated hospitals, fees, and contact placeholders to validate filtering and UX."
    },
    "step_2": {
        "title": "Phase 2 (Open Government Directories - NDHM / data.gov.in)",
        "cost": "₹0 (Free public API / Open Data)",
        "details": "Download National Health Facility Registry (HFR) datasets published by Ministry of Health & Family Welfare. Zero API fees."
    },
    "step_3": {
        "title": "Phase 3 (Google Places API / MapmyIndia for live GPS routing)",
        "cost": "Requires Credit Card & Billing Plan (₹0 for first $200 monthly free tier credits, then ~$17 per 1,000 requests)",
        "details": "Mentor Rule: Never add paid APIs without confirming budget and setup with the project lead."
    }
}

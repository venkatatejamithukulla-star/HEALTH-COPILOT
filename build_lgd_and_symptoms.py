"""
HealthMate AI — India LGD Districts & 300+ Symptom-to-Speciality Generator
Builds data/lgd_districts.json and data/symptoms_to_speciality.json (SPEC.md Phase 3 & 4)
"""

import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"
DATA_DIR.mkdir(exist_ok=True)

# 28 States and 8 Union Territories with official LGD districts
LGD_STATES_DISTRICTS = {
    # 28 States
    "Andhra Pradesh": [
        "Alluri Sitharama Raju", "Anakapalli", "Ananthapuramu", "Annamayya", "Bapatla", "Chittoor",
        "Dr. B.R. Ambedkar Konaseema", "East Godavari", "Eluru", "Guntur", "Kakinada", "Krishna",
        "Kurnool", "Nandyal", "NTR", "Palnadu", "Parvathipuram Manyam", "Prakasam", "Sri Potti Sriramulu Nellore",
        "Sri Sathya Sai", "Srikakulam", "Tirupati", "Visakhapatnam", "Vizianagaram", "West Godavari", "YSR Kadapa"
    ],
    "Telangana": [
        "Adilabad", "Bhadradri Kothagudem", "Hanumakonda", "Hyderabad", "Jagtial", "Jangaon",
        "Jayashankar Bhupalpally", "Jogulamba Gadwal", "Kamareddy", "Karimnagar", "Khammam",
        "Kumuram Bheem Asifabad", "Mahabubabad", "Mahabubnagar", "Mancherial", "Medak", "Medchal Malkajgiri",
        "Mulugu", "Nagarkurnool", "Nalgonda", "Narayanpet", "Nirmal", "Nizamabad", "Peddapalli",
        "Rajanna Sircilla", "Ranga Reddy", "Sangareddy", "Siddipet", "Suryapet", "Vikarabad",
        "Wanaparthy", "Warangal", "Yadadri Bhuvanagiri"
    ],
    "Arunachal Pradesh": [
        "Anjaw", "Changlang", "Dibang Valley", "East Kameng", "East Siang", "Kamle", "Kra Daadi",
        "Kurung Kumey", "Lepa Rada", "Lohit", "Longding", "Lower Dibang Valley", "Lower Siang",
        "Lower Subansiri", "Namsai", "Pakke Kessang", "Papum Pare", "Shi Yomi", "Siang", "Tawang",
        "Tirap", "Upper Siang", "Upper Subansiri", "West Kameng", "West Siang", "Itanagar"
    ],
    "Assam": [
        "Baksa", "Barpeta", "Biswanath", "Bongaigaon", "Cachar", "Charaideo", "Chirang", "Darrang",
        "Dhemaji", "Dhubri", "Dibrugarh", "Dima Hasao", "Goalpara", "Golaghat", "Hailakandi", "Hojai",
        "Jorhat", "Kamrup", "Kamrup Metropolitan", "Karbi Anglong", "Karimganj", "Kokrajhar", "Lakhimpur",
        "Majuli", "Morigaon", "Nagaon", "Nalbari", "Sivasagar", "Sonitpur", "South Salmara-Mankachar",
        "Tinsukia", "Udalguri", "West Karbi Anglong", "Bajali", "Tamulpur"
    ],
    "Bihar": [
        "Araria", "Arwal", "Aurangabad", "Banka", "Begusarai", "Bhagalpur", "Bhojpur", "Buxar",
        "Darbhanga", "East Champaran", "Gaya", "Gopalganj", "Jamui", "Jehanabad", "Kaimur", "Katihar",
        "Khagaria", "Kishanganj", "Lakhisarai", "Madhepura", "Madhubani", "Munger", "Muzaffarpur",
        "Nalanda", "Nawada", "Patna", "Purnia", "Rohtas", "Saharsa", "Samastipur", "Saran",
        "Sheikhpura", "Sheohar", "Sitamarhi", "Siwan", "Supaul", "Vaishali", "West Champaran"
    ],
    "Chhattisgarh": [
        "Balod", "Baloda Bazar", "Balrampur", "Bastar", "Bemetara", "Bijapur", "Bilaspur", "Dantewada",
        "Dhamtari", "Durg", "Gariaband", "Gaurela Pendra Marwahi", "Janjgir Champa", "Jashpur", "Kabirdham",
        "Kanker", "Kondagaon", "Korba", "Koriya", "Mahasamund", "Mungeli", "Narayanpur", "Raigarh",
        "Raipur", "Rajnandgaon", "Sukma", "Surajpur", "Surguja", "Manendragarh", "Mohla Manpur", "Sarangarh", "Shakti"
    ],
    "Goa": [
        "North Goa", "South Goa"
    ],
    "Gujarat": [
        "Ahmedabad", "Amreli", "Anand", "Aravalli", "Banaskantha", "Bharuch", "Bhavnagar", "Botad",
        "Chhota Udaipur", "Dahod", "Dang", "Devbhumi Dwarka", "Gandhinagar", "Gir Somnath", "Jamnagar",
        "Junagadh", "Kheda", "Kutch", "Mahisagar", "Mehsana", "Morbi", "Narmada", "Navsari",
        "Panchmahal", "Patan", "Porbandar", "Rajkot", "Sabarkantha", "Surat", "Surendranagar", "Tapi", "Vadodara", "Valsad"
    ],
    "Haryana": [
        "Ambala", "Bhiwani", "Charkhi Dadri", "Faridabad", "Fatehabad", "Gurugram", "Hisar", "Jhajjar",
        "Jind", "Kaithal", "Karnal", "Kurukshetra", "Mahendragarh", "Nuh", "Palwal", "Panchkula",
        "Panipat", "Rewari", "Rohtak", "Sirsa", "Sonipat", "Yamunanagar"
    ],
    "Himachal Pradesh": [
        "Bilaspur", "Chamba", "Hamirpur", "Kangra", "Kinnaur", "Kullu", "Lahaul and Spiti", "Mandi",
        "Shimla", "Sirmaur", "Solan", "Una"
    ],
    "Jharkhand": [
        "Bokaro", "Chatra", "Deoghar", "Dhanbad", "Dumka", "East Singhbhum", "Garhwa", "Giridih",
        "Godda", "Gumla", "Hazaribagh", "Jamtara", "Khunti", "Koderma", "Latehar", "Lohardaga",
        "Pakur", "Palamu", "Ramgarh", "Ranchi", "Sahebganj", "Seraikela Kharsawan", "Simdega", "West Singhbhum"
    ],
    "Karnataka": [
        "Bagalkote", "Ballari", "Belagavi", "Bengaluru Rural", "Bengaluru Urban", "Bidar", "Chamarajanagara",
        "Chikkaballapura", "Chikkamagaluru", "Chitradurga", "Dakshina Kannada", "Davanagere", "Dharwad",
        "Gadag", "Hassan", "Haveri", "Kalaburagi", "Kodagu", "Kolar", "Koppal", "Mandya",
        "Mysuru", "Raichur", "Ramanagara", "Shivamogga", "Tumakuru", "Udupi", "Uttara Kannada", "Vijayanagara", "Vijayapura", "Yadgir"
    ],
    "Kerala": [
        "Alappuzha", "Ernakulam", "Idukki", "Kannur", "Kasaragod", "Kollam", "Kottayam",
        "Kozhikode", "Malappuram", "Palakkad", "Pathanamthitta", "Thiruvananthapuram", "Thrissur", "Wayanad"
    ],
    "Madhya Pradesh": [
        "Agar Malwa", "Alirajpur", "Anuppur", "Ashoknagar", "Balaghat", "Barwani", "Betul", "Bhind",
        "Bhopal", "Burhanpur", "Chhatarpur", "Chhindwara", "Damoh", "Datia", "Dewas", "Dhar",
        "Dindori", "Guna", "Gwalior", "Harda", "Hoshangabad", "Indore", "Jabalpur", "Jhabua",
        "Katni", "Khandwa", "Khargone", "Mandla", "Mandsaur", "Morena", "Narsinghpur", "Neemuch",
        "Niwari", "Panna", "Raisen", "Rajgarh", "Ratlam", "Rewa", "Sagar", "Satna", "Sehore",
        "Seoni", "Shahdol", "Shajapur", "Sheopur", "Shivpuri", "Sidhi", "Singrauli", "Tikamgarh", "Ujjain", "Umaria", "Vidisha"
    ],
    "Maharashtra": [
        "Ahmednagar", "Akola", "Amravati", "Aurangabad", "Beed", "Bhandara", "Buldhana", "Chandrapur",
        "Dhule", "Gadchiroli", "Gondia", "Hingoli", "Jalgaon", "Jalna", "Kolhapur", "Latur",
        "Mumbai City", "Mumbai Suburban", "Nagpur", "Nanded", "Nandurbar", "Nashik", "Osmanabad",
        "Palghar", "Parbhani", "Pune", "Raigad", "Ratnagiri", "Sangli", "Satara", "Sindhudurg",
        "Solapur", "Thane", "Wardha", "Washim", "Yavatmal"
    ],
    "Manipur": [
        "Bishnupur", "Chandel", "Churachandpur", "Imphal East", "Imphal West", "Jiribam", "Kakching",
        "Kamjong", "Kangpokpi", "Noney", "Pherzawl", "Senapati", "Tamenglong", "Tengnoupal", "Thoubal", "Ukhrul"
    ],
    "Meghalaya": [
        "East Garo Hills", "East Jaintia Hills", "East Khasi Hills", "North Garo Hills", "Ri Bhoi",
        "South Garo Hills", "South West Garo Hills", "South West Khasi Hills", "West Garo Hills", "West Jaintia Hills", "West Khasi Hills", "Eastern West Khasi Hills"
    ],
    "Mizoram": [
        "Aizawl", "Champhai", "Hnahthial", "Khawzawl", "Kolasib", "Lawngtlai", "Lunglei", "Mamit", "Saitual", "Serchhip", "Siaha"
    ],
    "Nagaland": [
        "Chumoukedima", "Dimapur", "Kiphire", "Kohima", "Longleng", "Mokokchung", "Mon", "Niuland",
        "Noklak", "Peren", "Phek", "Shamator", "Tseminyu", "Tuensang", "Wokha", "Zunheboto"
    ],
    "Odisha": [
        "Angul", "Balangir", "Balasore", "Bargarh", "Bhadrak", "Boudh", "Cuttack", "Deogarh",
        "Dhenkanal", "Gajapati", "Ganjam", "Jagatsinghpur", "Jajpur", "Jharsuguda", "Kalahandi", "Kandhamal",
        "Kendrapara", "Kendujhar", "Khordha", "Koraput", "Malkangiri", "Mayurbhanj", "Nabarangpur", "Nayagarh",
        "Nuapada", "Puri", "Rayagada", "Sambalpur", "Subarnapur", "Sundargarh"
    ],
    "Punjab": [
        "Amritsar", "Barnala", "Bathinda", "Faridkot", "Fatehgarh Sahib", "Fazilka", "Ferozepur", "Gurdaspur",
        "Hoshiarpur", "Jalandhar", "Kapurthala", "Ludhiana", "Malerkotla", "Mansa", "Moga", "Muktsar",
        "Pathankot", "Patiala", "Rupnagar", "Sahibzada Ajit Singh Nagar", "Shaheed Bhagat Singh Nagar", "Sangrur", "Tarn Taran"
    ],
    "Rajasthan": [
        "Ajmer", "Alwar", "Banswara", "Baran", "Barmer", "Bharatpur", "Bhilwara", "Bikaner",
        "Bundi", "Chittorgarh", "Churu", "Dausa", "Dholpur", "Dungarpur", "Hanumangarh", "Jaipur",
        "Jaisalmer", "Jalore", "Jhalawar", "Jhunjhunu", "Jodhpur", "Karauli", "Kota", "Nagaur",
        "Pali", "Pratapgarh", "Rajsamand", "Sawai Madhopur", "Sikar", "Sirohi", "Sri Ganganagar", "Tonk", "Udaipur"
    ],
    "Sikkim": [
        "Gangtok", "Gyalsing", "Mangan", "Namchi", "Pakyong", "Soreng"
    ],
    "Tamil Nadu": [
        "Ariyalur", "Chengalpattu", "Chennai", "Coimbatore", "Cuddalore", "Dharmapuri", "Dindigul", "Erode",
        "Kallakurichi", "Kanchipuram", "Kanyakumari", "Karur", "Krishnagiri", "Madurai", "Mayiladuthurai", "Nagapattinam",
        "Namakkal", "Nilgiris", "Perambalur", "Pudukkottai", "Ramanathapuram", "Ranipet", "Salem", "Sivaganga",
        "Tenkasi", "Thanjavur", "Theni", "Thoothukudi", "Tiruchirappalli", "Tirunelveli", "Tirupathur", "Tiruppur",
        "Tiruvallur", "Tiruvannamalai", "Tiruvarur", "Vellore", "Viluppuram", "Virudhunagar"
    ],
    "Tripura": [
        "Dhalai", "Gomati", "Khowai", "North Tripura", "Sepahijala", "South Tripura", "Unakoti", "West Tripura"
    ],
    "Uttar Pradesh": [
        "Agra", "Aligarh", "Ambedkar Nagar", "Amethi", "Amroha", "Auraiya", "Ayodhya", "Azamgarh",
        "Baghpat", "Bahraich", "Ballia", "Balrampur", "Banda", "Barabanki", "Bareilly", "Basti",
        "Bhadohi", "Bijnor", "Budaun", "Bulandshahr", "Chandauli", "Chitrakoot", "Deoria", "Etah",
        "Etawah", "Farrukhabad", "Fatehpur", "Firozabad", "Gautam Buddha Nagar", "Ghaziabad", "Ghazipur", "Gonda",
        "Gorakhpur", "Hamirpur", "Hapur", "Hardoi", "Hathras", "Jalaun", "Jaunpur", "Jhansi",
        "Kannauj", "Kanpur Dehat", "Kanpur Nagar", "Kasganj", "Kaushambi", "Kheri", "Kushinagar", "Lalitpur",
        "Lucknow", "Maharajganj", "Mahoba", "Mainpuri", "Mathura", "Mau", "Meerut", "Mirzapur",
        "Moradabad", "Muzaffarnagar", "Pilibhit", "Pratapgarh", "Prayagraj", "Raebareli", "Rampur", "Saharanpur",
        "Sambhal", "Sant Kabir Nagar", "Shahjahanpur", "Shamli", "Shrawasti", "Siddharthnagar", "Sitapur", "Sonbhadra",
        "Sultanpur", "Unnao", "Varanasi"
    ],
    "Uttarakhand": [
        "Almora", "Bageshwar", "Chamoli", "Champawat", "Dehradun", "Haridwar", "Nainital", "Pauri Garhwal",
        "Pithoragarh", "Rudraprayag", "Tehri Garhwal", "Udham Singh Nagar", "Uttarkashi"
    ],
    "West Bengal": [
        "Alipurduar", "Bankura", "Birbhum", "Cooch Behar", "Dakshin Dinajpur", "Darjeeling", "Hooghly", "Howrah",
        "Jalpaiguri", "Jhargram", "Kalimpong", "Kolkata", "Malda", "Murshidabad", "Nadia", "North 24 Parganas",
        "Paschim Bardhaman", "Paschim Medinipur", "Purba Bardhaman", "Purba Medinipur", "Purulia", "South 24 Parganas", "Uttar Dinajpur"
    ],

    # 8 Union Territories
    "Andaman and Nicobar Islands": [
        "Nicobar", "North and Middle Andaman", "South Andaman"
    ],
    "Chandigarh": [
        "Chandigarh"
    ],
    "Dadra and Nagar Haveli and Daman and Diu": [
        "Dadra and Nagar Haveli", "Daman", "Diu"
    ],
    "Delhi": [
        "Central Delhi", "East Delhi", "New Delhi", "North Delhi", "North East Delhi",
        "North West Delhi", "Shahdara", "South Delhi", "South East Delhi", "South West Delhi", "West Delhi"
    ],
    "Jammu and Kashmir": [
        "Anantnag", "Bandipora", "Baramulla", "Budgam", "Doda", "Ganderbal", "Jammu", "Kathua",
        "Kishtwar", "Kulgam", "Kupwara", "Poonch", "Pulwama", "Rajouri", "Ramban", "Reasi",
        "Samba", "Shopian", "Srinagar", "Udhampur"
    ],
    "Ladakh": [
        "Kargil", "Leh"
    ],
    "Lakshadweep": [
        "Lakshadweep"
    ],
    "Puducherry": [
        "Karaikal", "Mahe", "Puducherry", "Yanam"
    ]
}

# 300+ Symptoms with Mapping to Specialities, Urgency and Multilingual Queries
# Including mental health and de-addiction symptoms!
SYMPTOMS_LIST = [
    # Cardiology (Heart)
    {"symptom": "chest pain", "specialty": "Cardiology", "urgency": "High", "aliases": ["chest tightness", "angina", "గుండె నొప్పి", "सीने में दर्द", "நெஞ்சு வலி", "سینے میں درد"]},
    {"symptom": "heart palpitations", "specialty": "Cardiology", "urgency": "Medium", "aliases": ["rapid heartbeat", "fluttering heart", "గుండె దడ", "दिल की धड़कन तेज"]},
    {"symptom": "shortness of breath on exertion", "specialty": "Cardiology", "urgency": "High", "aliases": ["breathless walking", "శ్వాస ఆడకపోవడం", "सांस फूलना"]},
    {"symptom": "swollen legs and ankles", "specialty": "Cardiology", "urgency": "Medium", "aliases": ["edema", "foot swelling", "కాళ్ల వాపులు", "पैरों में सूजन"]},
    {"symptom": "dizziness when standing", "specialty": "Cardiology", "urgency": "Medium", "aliases": ["lightheadedness", "orthostatic hypotension", "కళ్లు తిరగడం"]},
    {"symptom": "high blood pressure", "specialty": "Cardiology", "urgency": "Medium", "aliases": ["hypertension", "elevated bp", "బి.పి ఎక్కువ"]},
    {"symptom": "left arm pain", "specialty": "Cardiology", "urgency": "High", "aliases": ["radiating shoulder pain", "left arm tingling"]},
    {"symptom": "fainting spells", "specialty": "Cardiology", "urgency": "High", "aliases": ["syncope", "blackout", "స్పృహ తప్పడం"]},

    # De-addiction & Substance Rehabilitation
    {"symptom": "craving alcohol", "specialty": "De-addiction", "urgency": "High", "aliases": ["alcohol urge", "liquor craving", "alcohol addiction", "మద్యం వ్యసనం", "शराब की तलब", "மதுப் பழக்கம்"]},
    {"symptom": "alcohol withdrawal shakes", "specialty": "De-addiction", "urgency": "High", "aliases": ["delirium tremens", "hand tremors morning", "చేతుల వణుకు"]},
    {"symptom": "nicotine dependence", "specialty": "De-addiction", "urgency": "Medium", "aliases": ["tobacco craving", "cigarette addiction", "ధూమపానం మానుకోవడం", "बीड़ी तंबाकू छोड़ना"]},
    {"symptom": "drug withdrawal symptoms", "specialty": "De-addiction", "urgency": "High", "aliases": ["opioid withdrawal", "substance detox", "మాదకద్రవ్యాల విముక్తి"]},
    {"symptom": "gutkha chewing addiction", "specialty": "De-addiction", "urgency": "Medium", "aliases": ["pan masala craving", "khaini addiction"]},
    {"symptom": "cannabis dependence", "specialty": "De-addiction", "urgency": "Medium", "aliases": ["weed addiction", "ganja withdrawal"]},
    {"symptom": "uncontrollable urges to drink", "specialty": "De-addiction", "urgency": "High", "aliases": ["binge drinking", "loss of control alcohol"]},
    {"symptom": "relapse prevention support", "specialty": "De-addiction", "urgency": "Medium", "aliases": ["sobriety support", "addiction counselling"]},

    # Psychiatry & Mental Health
    {"symptom": "feeling hopeless", "specialty": "Psychiatry", "urgency": "High", "aliases": ["hopelessness", "loss of hope", "feeling depressed", "తీవ్ర నిరాశ", "निराशा"]},
    {"symptom": "severe anxiety", "specialty": "Psychiatry", "urgency": "Medium", "aliases": ["panic", "nervousness", "ఆందోళన", "घबराहट", "பதற்றம்"]},
    {"symptom": "panic attacks", "specialty": "Psychiatry", "urgency": "High", "aliases": ["sudden terror", "hyperventilation anxiety", "తీవ్ర భయాందోళన"]},
    {"symptom": "persistent sadness", "specialty": "Psychiatry", "urgency": "Medium", "aliases": ["depression", "loss of interest", "కుంగుబాటు", "उदासी"]},
    {"symptom": "insomnia and sleeplessness", "specialty": "Psychiatry", "urgency": "Medium", "aliases": ["cannot sleep", "broken sleep", "నిద్రలేమి", "अनिद्रा"]},
    {"symptom": "suicidal thoughts", "specialty": "Psychiatry", "urgency": "Urgent", "aliases": ["hopelessness", "want to end life", "ఆత్మహత్య ఆలోచనలు", "आत्महत्या के विचार"]},
    {"symptom": "hearing voices", "specialty": "Psychiatry", "urgency": "High", "aliases": ["auditory hallucinations", "schizophrenia signs"]},
    {"symptom": "extreme mood swings", "specialty": "Psychiatry", "urgency": "Medium", "aliases": ["bipolar mania", "unstable mood", "మూడ్ మార్పులు"]},
    {"symptom": "obsessive compulsive thoughts", "specialty": "Psychiatry", "urgency": "Medium", "aliases": ["ocd", "repetitive checking", "repeated hand washing"]},
    {"symptom": "post-traumatic stress", "specialty": "Psychiatry", "urgency": "Medium", "aliases": ["ptsd", "nightmares from trauma"]},
    {"symptom": "loss of appetite due to stress", "specialty": "Psychiatry", "urgency": "Low", "aliases": ["eating disorder", "emotional starvation"]},

    # Neurology (Brain & Nerves)
    {"symptom": "severe sudden headache", "specialty": "Neurology", "urgency": "High", "aliases": ["thunderclap headache", "తీవ్ర తలనొప్పి", "सिरदर्द"]},
    {"symptom": "migraine with aura", "specialty": "Neurology", "urgency": "Medium", "aliases": ["one sided head pain", "visual flashes"]},
    {"symptom": "facial drooping", "specialty": "Neurology", "urgency": "High", "aliases": ["bells palsy", "stroke face", "ముఖం వంకర"]},
    {"symptom": "numbness in hands and feet", "specialty": "Neurology", "urgency": "Medium", "aliases": ["peripheral neuropathy", "కాళ్లు చేతులు తిమ్మిర్లు", "हाथ-पैर सुन्न"]},
    {"symptom": "seizures or fits", "specialty": "Neurology", "urgency": "High", "aliases": ["epilepsy", "convulsions", "ఫిట్స్", "दौरे"]},
    {"symptom": "tremors and shaking hands", "specialty": "Neurology", "urgency": "Medium", "aliases": ["parkinsons sign", "resting tremor"]},
    {"symptom": "memory loss and confusion", "specialty": "Neurology", "urgency": "Medium", "aliases": ["dementia", "forgetfulness", "జ్ఞాపకశక్తి తగ్గడం"]},
    {"symptom": "loss of balance walking", "specialty": "Neurology", "urgency": "Medium", "aliases": ["ataxia", "unsteady gait", "నడక తూలడం"]},

    # Orthopedics (Bones & Joints)
    {"symptom": "knee joint pain", "specialty": "Orthopedics", "urgency": "Medium", "aliases": ["osteoarthritis", "knee creaking", "మోకాళ్ళ నొప్పులు", "घुटनों का दर्द"]},
    {"symptom": "lower back pain", "specialty": "Orthopedics", "urgency": "Medium", "aliases": ["lumbago", "sciatica", "నడుము నొప్పి", "कमर दर्द"]},
    {"symptom": "shoulder stiffness", "specialty": "Orthopedics", "urgency": "Low", "aliases": ["frozen shoulder", "cannot lift arm", "భుజం నొప్పి"]},
    {"symptom": "bone fracture suspicion", "specialty": "Orthopedics", "urgency": "High", "aliases": ["broken bone", "swollen fall", "ఎముక విరుగుట"]},
    {"symptom": "morning joint stiffness", "specialty": "Orthopedics", "urgency": "Medium", "aliases": ["rheumatoid arthritis", "finger stiffness"]},
    {"symptom": "heel pain morning", "specialty": "Orthopedics", "urgency": "Low", "aliases": ["plantar fasciitis", "మడమ నొప్పి"]},
    {"symptom": "neck pain radiating down arm", "specialty": "Orthopedics", "urgency": "Medium", "aliases": ["cervical spondylosis", "మెడ నొప్పి"]},

    # Gastroenterology (Stomach & Liver)
    {"symptom": "acid reflux and heartburn", "specialty": "Gastroenterology", "urgency": "Low", "aliases": ["gerd", "burning in chest throat", "ఎసిడిటీ", "छाती में जलन"]},
    {"symptom": "severe abdominal pain", "specialty": "Gastroenterology", "urgency": "High", "aliases": ["stomach cramps", "appendicitis sign", "కడుపు నొప్పి", "पेट दर्द"]},
    {"symptom": "yellow eyes and skin", "specialty": "Gastroenterology", "urgency": "High", "aliases": ["jaundice", "liver infection", "పచ్చకామెర్లు", "पीलिया"]},
    {"symptom": "blood in stool", "specialty": "Gastroenterology", "urgency": "High", "aliases": ["melena", "rectal bleeding", "మలంలో రక్తం"]},
    {"symptom": "chronic constipation", "specialty": "Gastroenterology", "urgency": "Low", "aliases": ["irregular bowel", "మలబద్ధకం", "कब्ज"]},
    {"symptom": "chronic watery diarrhea", "specialty": "Gastroenterology", "urgency": "Medium", "aliases": ["loose motions", "విరేచనాలు", "दस्त"]},
    {"symptom": "persistent vomiting", "specialty": "Gastroenterology", "urgency": "Medium", "aliases": ["cannot keep fluids down", "వాంతులు"]},

    # Pulmonology (Lungs & Breathing)
    {"symptom": "chronic cough over 3 weeks", "specialty": "Pulmonology", "urgency": "High", "aliases": ["tb suspicion", "coughing phlegm", "దగ్గు", "खांसी"]},
    {"symptom": "coughing up blood", "specialty": "Pulmonology", "urgency": "High", "aliases": ["hemoptysis", "రక్తం పడడం దగ్గులో"]},
    {"symptom": "wheezing and whistling breath", "specialty": "Pulmonology", "urgency": "Medium", "aliases": ["asthma attack", "శ్వాసలో పిల్లికూతలు"]},
    {"symptom": "chest congestion and thick mucus", "specialty": "Pulmonology", "urgency": "Low", "aliases": ["bronchitis", "छाती में जकड़न"]},
    {"symptom": "snoring and choking in sleep", "specialty": "Pulmonology", "urgency": "Low", "aliases": ["sleep apnea", "daytime sleepiness"]},

    # Dermatology (Skin & Hair)
    {"symptom": "itching red skin rash", "specialty": "Dermatology", "urgency": "Low", "aliases": ["eczema", "hives", "దురద దద్దుర్లు", "त्वचा पर खुजली"]},
    {"symptom": "fungal ringworm infection", "specialty": "Dermatology", "urgency": "Low", "aliases": ["tinea", "తామర", "दाद"]},
    {"symptom": "severe acne and boils", "specialty": "Dermatology", "urgency": "Low", "aliases": ["pimples", "మొటిమలు", "मुंहासे"]},
    {"symptom": "hair loss in circular patches", "specialty": "Dermatology", "urgency": "Low", "aliases": ["alopecia areata", "జుట్టు రాలడం"]},
    {"symptom": "changing skin mole or dark spot", "specialty": "Dermatology", "urgency": "Medium", "aliases": ["melanoma check", "పుట్టుమచ్చ మార్పు"]},
    {"symptom": "dry scaly silver patches", "specialty": "Dermatology", "urgency": "Low", "aliases": ["psoriasis", "సోరియాసిస్"]},

    # Gynecology & Women's Health
    {"symptom": "irregular menstrual periods", "specialty": "Gynecology & Obstetrics", "urgency": "Medium", "aliases": ["pcos sign", "missed period", "ముట్టు లోపాలు", "अनियमित मासिक धर्म"]},
    {"symptom": "heavy menstrual bleeding", "specialty": "Gynecology & Obstetrics", "urgency": "Medium", "aliases": ["menorrhagia", "అధిక రక్తస్రావం"]},
    {"symptom": "pelvic pain", "specialty": "Gynecology & Obstetrics", "urgency": "Medium", "aliases": ["lower abdominal pain women", "కటి నొప్పి"]},
    {"symptom": "breast lump or nipple discharge", "specialty": "Gynecology & Obstetrics", "urgency": "High", "aliases": ["breast mass", "రొమ్ములో గడ్డ"]},
    {"symptom": "pregnancy nausea and vomiting", "specialty": "Gynecology & Obstetrics", "urgency": "Low", "aliases": ["morning sickness", "గర్భధారణ వాంతులు"]},
    {"symptom": "abnormal vaginal discharge", "specialty": "Gynecology & Obstetrics", "urgency": "Low", "aliases": ["yeast infection", "తెల్లబట్ట"]},

    # Pediatrics (Child Health)
    {"symptom": "high fever in child with shivering", "specialty": "Pediatrics", "urgency": "High", "aliases": ["infant fever", "పిల్లల్లో జ్వరం", "बच्चों में बुखार"]},
    {"symptom": "child poor growth or weight loss", "specialty": "Pediatrics", "urgency": "Medium", "aliases": ["failure to thrive", "పిల్లల ఎదుగుదల లోపం"]},
    {"symptom": "child persistent barking cough", "specialty": "Pediatrics", "urgency": "Medium", "aliases": ["croup", "పిల్లాడికి దగ్గు"]},
    {"symptom": "child dehydration from diarrhea", "specialty": "Pediatrics", "urgency": "High", "aliases": ["sunken eyes infant", "no tears crying"]},
    {"symptom": "child speech delay", "specialty": "Pediatrics", "urgency": "Low", "aliases": ["not talking at 2 years", "మాటలు రాకపోవడం"]},

    # Ophthalmology (Eye Care)
    {"symptom": "cloudy blurred vision", "specialty": "Ophthalmology", "urgency": "Medium", "aliases": ["cataract sign", "కంటి మసక", "आंखों में धुंधलापन"]},
    {"symptom": "sudden loss of vision", "specialty": "Ophthalmology", "urgency": "Urgent", "aliases": ["retinal detachment", "black vision"]},
    {"symptom": "red painful eye with discharge", "specialty": "Ophthalmology", "urgency": "Medium", "aliases": ["conjunctivitis", "pink eye", "కండ్లకలక"]},
    {"symptom": "eye pain with rainbow halos", "specialty": "Ophthalmology", "urgency": "High", "aliases": ["acute glaucoma", "కంటి నొప్పి"]},

    # ENT (Ear, Nose & Throat)
    {"symptom": "ear pain with discharge", "specialty": "ENT (Ear, Nose & Throat)", "urgency": "Medium", "aliases": ["otitis media", "చెవి నొప్పి", "कान में दर्द"]},
    {"symptom": "hearing loss in one ear", "specialty": "ENT (Ear, Nose & Throat)", "urgency": "Medium", "aliases": ["tinnitus", "చెవి దిబ్బడ"]},
    {"symptom": "sore throat painful swallowing", "specialty": "ENT (Ear, Nose & Throat)", "urgency": "Low", "aliases": ["tonsillitis", "గొంతు నొప్పి", "गले में खराश"]},
    {"symptom": "chronic nasal blockage and sneezing", "specialty": "ENT (Ear, Nose & Throat)", "urgency": "Low", "aliases": ["sinusitis", "ముక్కు దిబ్బడ", "साइनस"]},
    {"symptom": "spinning dizziness room rotating", "specialty": "ENT (Ear, Nose & Throat)", "urgency": "Medium", "aliases": ["vertigo", "తల తిరగడం"]},

    # Endocrinology (Diabetes & Thyroid)
    {"symptom": "excessive thirst and frequent urination", "specialty": "Endocrinology", "urgency": "Medium", "aliases": ["high blood sugar", "diabetes signs", "ఎక్కువ దాహం", "बार बार पेशाब"]},
    {"symptom": "unexplained rapid weight loss", "specialty": "Endocrinology", "urgency": "Medium", "aliases": ["hyperthyroidism", "బరువు తగ్గడం"]},
    {"symptom": "unexplained weight gain and cold intolerance", "specialty": "Endocrinology", "urgency": "Low", "aliases": ["hypothyroidism", "బరువు పెరగడం"]},
    {"symptom": "swelling in front of neck", "specialty": "Endocrinology", "urgency": "Low", "aliases": ["goiter", "మెడ వాపు"]},

    # Nephrology & Urology (Kidneys & Urinary)
    {"symptom": "burning pain during urination", "specialty": "Urology & Nephrology", "urgency": "Medium", "aliases": ["uti", "urinary infection", "మూత్రంలో మంట", "पेशाब में जलन"]},
    {"symptom": "severe flank side back pain", "specialty": "Urology & Nephrology", "urgency": "High", "aliases": ["kidney stone", "కిడ్నీ రాయి నొప్పి"]},
    {"symptom": "blood in urine", "specialty": "Urology & Nephrology", "urgency": "High", "aliases": ["hematuria", "మూత్రంలో రక్తం"]},
    {"symptom": "difficulty passing urine in elderly men", "specialty": "Urology & Nephrology", "urgency": "Medium", "aliases": ["prostate enlargement", "bph sign"]},
    {"symptom": "puffiness around eyes in morning", "specialty": "Urology & Nephrology", "urgency": "Medium", "aliases": ["kidney edema", "కళ్ల వాపులు"]}
]

# Generate more symptom entries to exceed 300+ entries
def build_expanded_symptoms():
    expanded = list(SYMPTOMS_LIST)
    body_areas = [
        ("skin", "Dermatology", ["itchy scalp", "dry cracked skin", "nail discoloration", "skin peeling", "sunburn blisters", "dark patches on neck", "white patches on skin", "ingrown nail infection", "sweat rash underarms", "skin tags neck"]),
        ("stomach", "Gastroenterology", ["bloating after eating", "excessive belching", "indigestion fullness", "hiccups persistent", "anal itching worms", "nausea after oily food", "gas flatulence foul", "stomach rumbling pain", "loss of taste food", "metallic taste tongue"]),
        ("chest", "Cardiology", ["chest fluttering laying down", "pulse jumping feeling", "heavy chest morning", "racing pulse rest", "cold sweat anxiety", "chest stitch breathing", "blue lips exertion", "swollen vein neck", "skipped heart beats", "high resting pulse"]),
        ("joints", "Orthopedics", ["finger stiffness typing", "creaking sound neck", "swollen ankle twist", "tailbone pain sitting", "elbow tender touch", "wrist numbness typing", "hip pain walking stairs", "clicking knee climbing", "toe pain gout attack", "shoulder blade ache"]),
        ("head", "Neurology", ["throbbing forehead temples", "scalp tenderness comb", "flashing lights vision", "tingling tongue cheek", "shaky handwriting coffee", "trouble finding words", "clumsy dropping glasses", "eyelid twitching daily", "head pressure reading", "brain fog tiredness"]),
        ("breathing", "Pulmonology", ["breathless climbing stairs", "tight chest cold air", "dry tickly night cough", "throat mucus morning", "gasping night waking", "dust allergy sneezing", "pollen allergy eyes", "smoke irritation throat", "shallow fast breathing", "chest soreness coughing"]),
        ("mental", "Psychiatry & Mental Health", ["crying spells unprovoked", "racing thoughts at night", "fear of leaving house", "feeling unreal disconnected", "irritability with family", "social gathering dread", "excessive guilt past", "difficulty concentrating", "low energy motivation", "constant worrying future"]),
        ("addiction", "De-addiction & Rehabilitation", ["sneaking drinks secret", "lying about alcohol intake", "shaky mornings needing drink", "blackout events party", "irritated without tobacco", "using drugs alone", "stealing money for substances", "ignoring duties for drinking", "tolerance needing more liquor", "hangover sickness regular"]),
        ("women", "Gynecology & Obstetrics", ["painful cramps periods", "breast tenderness before cycle", "hot flashes night sweats", "vaginal dryness itching", "mood swings before menses", "spotting between periods", "heavy bleeding clots", "cervical discharge odor", "pain during intercourse", "lower pelvic pressure"]),
        ("children", "Pediatrics", ["teething pain infant", "child refusing liquids", "child ear pulling crying", "diaper rash redness", "bedwetting over 6 years", "child thumb sucking anxiety", "child rash with fever", "persistent diarrhea baby", "frequent colds preschool", "restless sleeping toddler"]),
        ("eyes", "Ophthalmology", ["dry gritty feeling eyes", "eye strain computer", "watery eyes wind", "itchy eye rubbing", "sensitive to bright sun", "floaters cobwebs vision", "crusty eyelids waking", "contact lens burning", "double vision reading", "twitching eye stress"]),
        ("throat", "ENT (Ear, Nose & Throat)", ["scratchy throat dust", "hoarse raspy voice", "lump sensation throat", "blocked ear flight", "ear popping swallowing", "nose bleeding dry weather", "runny clear nose sneezing", "loss of smell taste", "snoring loud mouth breathing", "clicking jaw chewing"]),
        ("urinary", "Urology & Nephrology", ["waking twice to pee", "weak urine stream", "urgent rush to toilet", "cloudy smelly urine", "foamy bubbly urine", "pain after passing water", "dribbling urine after toilet", "feeling bladder not empty", "dark amber tea urine", "pain in groins walking"]),
        ("elderly", "Geriatrics", ["frailty and unsteadiness", "frequent falls elderly", "confusion at twilight sundowning", "difficulty swallowing liquids", "involuntary urine leakage", "loss of independence daily tasks", "weight loss elderly dentures", "slow walking shuffle", "bruising easily thin skin", "hearing impairment elderly"]),
        ("infectious", "General Medicine & Infectious Diseases", ["chills and shivering rigor", "night sweats soaking sheets", "persistent low grade fever", "body aches all over", "extreme fatigue exhaustion", "swollen lymph nodes neck", "loss of taste COVID sign", "dengue joint bone breaking pain", "malaria sweating cycle", "typhoid stomach ache fever"]),
        ("lifestyle", "Endocrinology", ["sugar cravings afternoon", "feeling shaky when hungry", "dark velvety skin armpits", "slow healing minor cuts", "tingling burning in toes", "constant dry mouth thirst", "frequent boils skin infections", "blurred vision after sweets", "tiredness after heavy rice meals", "abdominal fat accumulation"]),
        ("mental_extra", "Psychiatry & Mental Health", ["phobia of crowded markets", "social anxiety public speaking", "hypochondria health anxiety", "hair pulling trichotillomania", "skin picking excoriation", "imposter syndrome dread", "burnout work exhaustion", "dissociation floating feeling", "morning gloom waking early", "chronic loneliness despair"]),
        ("addiction_extra", "De-addiction & Rehabilitation", ["morning drink eye opener", "gambling compulsion urges", "prescription sleeping pill dependence", "cough syrup abuse codeine", "inhalant sniffing glue", "denial about addiction consequences", "financial ruin buying liquor", "violent temper when sober", "seeking multiple doctor prescriptions", "physical craving panic without substance"]),
        ("dental", "Dentistry", ["severe throbbing toothache", "bleeding gums brushing", "sensitive teeth cold water", "jaw clicking pain opening", "wisdom tooth swelling gum", "bad breath halitosis", "cavity dark hole molar", "loose adult tooth", "mouth ulcer canker sore", "swollen cheek dental abscess"]),
        ("occupational", "Occupational Health", ["repetitive strain wrist typing", "chronic dust inhalation stone cutter", "pesticide exposure farmer nausea", "hearing ringing factory noise", "welder flash eye burn", "chemical fumes throat burn", "shift worker chronic insomnia", "standing long hours varicose veins", "heavy lifting hernia pain", "lead battery toxic headache"]),
        ("nutrition", "Clinical Nutrition", ["severe anemia fatigue pallor", "scurvy bleeding hair follicles", "vitamin d bone softening rickets", "b12 neuropathy tingling feet", "calcium deficiency muscle cramps", "protein malnutrition muscle loss", "zinc deficiency taste loss", "electrolyte imbalance dehydration", "folate deficiency tongue redness", "iodine deficiency sluggishness"]),
        ("ayurveda", "Ayurveda & Integrative Medicine", ["chronic acidity vata pitta imbalance", "joint stiffness seasonal winter", "chronic fatigue rasayana need", "stress rejuvenation panchakarma", "sluggish digestion agni mandya", "sleep disturbance vata aggravation", "chronic sinusitis nasya therapy", "skin detox consultation", "herbal immunity boost", "post viral recuperation"])
    ]

    for area, spec, sym_list in body_areas:
        for s in sym_list:
            expanded.append({
                "symptom": s,
                "specialty": spec,
                "urgency": "Medium" if "pain" in s or "blood" in s or "severe" in s else "Low",
                "aliases": [s.replace(" ", "-"), f"{area} {s}"]
            })

    return expanded

def main():
    # 1. Save LGD Districts
    lgd_path = DATA_DIR / "lgd_districts.json"
    total_districts = sum(len(d) for d in LGD_STATES_DISTRICTS.values())
    with open(lgd_path, "w", encoding="utf-8") as f:
        json.dump(LGD_STATES_DISTRICTS, f, ensure_ascii=False, indent=2)
    print(f"[OK] Wrote LGD data: {len(LGD_STATES_DISTRICTS)} States/UTs and {total_districts} districts -> {lgd_path}")

    # 2. Save 300+ Symptoms with Speciality Mapping
    all_symptoms = build_expanded_symptoms()
    symp_path = DATA_DIR / "symptoms_to_speciality.json"
    with open(symp_path, "w", encoding="utf-8") as f:
        json.dump({
            "total": len(all_symptoms),
            "symptoms": all_symptoms
        }, f, ensure_ascii=False, indent=2)
    print(f"[OK] Wrote Symptoms data: {len(all_symptoms)} symptoms mapped to specialities -> {symp_path}")

if __name__ == "__main__":
    main()

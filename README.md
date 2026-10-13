# 🏥 HealthMate AI — AI-Powered Personal Health Copilot

> **Beginner-Friendly Full-Stack Web Application for CSE Students**  
> *Developed with Python, Flask, SQLite, Vanilla HTML/CSS/JavaScript, and Safe AI Integration.*

---

## 🌟 Project Overview

**HealthMate AI** is an accessible personal health companion designed for families, college students, office workers, and elderly family members (like grandparents). It bridges the gap between complicated medical lab reports and everyday understanding by translating complex medical jargon into plain, compassionate **English and Telugu (తెలుగు)**.

### 🎯 Key Highlights
1. **Elderly & Beginner Accessibility First**:
   - Dynamic font size scaler (`A`, `A+`, `A++`)
   - High Contrast mode for low-vision and senior users
   - Web Speech API **Read Aloud** (Voice narration in English & Telugu)
   - Large touch targets and clean cards (minimum 48px touch targets)
2. **Bilingual Support (English & Telugu)**:
   - Instant language toggle with complete UI translation and bilingual medical explanations.
3. **Doctor Appointments Management**:
   - Schedule, filter (Upcoming, Completed, Cancelled), and track clinic checkups.
   - Stored in a local **SQLite database** using **parameterized SQL queries**.
4. **Prescribed Medicine Schedule Tracker**:
   - Strict Safety Guardrail: Tracks doctor-prescribed medicine times (Morning, Afternoon, Night) with a daily "Taken" toggle and refill alerts.
   - **Never prescribes drugs or dosages independently**.
5. **Medical Report Summarizer & Term Explainer**:
   - Drag-and-drop report files (`.pdf`, `.txt`, `.png`, `.jpg`) or paste lab results.
   - Built-in **"Load Sample Blood Test Report"** button for immediate 1-click testing.
   - Automatically breaks down parameters (HbA1c, Fasting Blood Sugar, LDL/HDL Cholesterol, Hemoglobin, Creatinine, Thyroid TSH, Blood Pressure) with normal ranges and doctor consultation questions.
6. **Safe AI Health Assistant Copilot**:
   - **Honest AI Architecture**: Does **not** pretend AI is connected if it is not configured.
   - Operates in **Safe Local Knowledge Base Mode** using a built-in medical glossary when no API key is provided.
   - Seamlessly upgrades to **Google Gemini AI** when `GEMINI_API_KEY` is added to `.env`.
   - Built-in emergency detector: Immediately displays national emergency helplines (`108`, `112`, `104`) if critical emergency symptoms (chest pain, stroke, breathlessness) are detected.
7. **Privacy & Data Security**:
   - Runs 100% locally on your machine with SQLite (`healthmate.db`).
   - "Privacy Mode" hides patient names on public screens.
   - Includes realistic sample health data only; no private patient data is ever uploaded or exposed.

---

## 📁 Project Structure

```
c:/healthMateAI/
│
├── app.py                  # Flask backend server, routes, database models & AI logic
├── requirements.txt        # Python package dependencies
├── .env.example            # Template for environment variables (API keys)
├── .gitignore              # Ignores venv, database files, and uploaded files
├── README.md               # Complete project documentation & beginner guide
│
├── templates/
│   └── index.html          # Semantic HTML5 accessible single-page layout
│
├── static/
│   ├── style.css           # Clean modern CSS, high-contrast & accessibility themes
│   └── script.js           # Interactive UI logic, bilingual dictionary, speech synthesis
│
└── uploads/                # Local temporary storage for uploaded medical reports
    └── .gitkeep
```

---

## 🛠️ Technology Stack Explained

| Component | Technology | Why Chosen for Beginners |
| :--- | :--- | :--- |
| **Backend** | Python 3.13 + Flask 3.1 | Minimal boilerplate, readable syntax, ideal for CSE coursework |
| **Database** | SQLite 3 | Zero configuration required; stores data in a simple local file (`healthmate.db`) |
| **PDF Extraction** | `pypdf` | Safe local text extraction from medical lab PDF reports |
| **Frontend** | Vanilla HTML5, CSS3, JavaScript | No heavy frameworks or build steps; runs directly in any modern browser |
| **Typography** | Plus Jakarta Sans & Nirmala UI | High legibility for both English alphabet and Telugu script |
| **AI Integration** | Google Gemini 2.5 Flash / Safe Local Fallback | High speed, free tier access via Google AI Studio, transparent offline fallback |

---

## 🚀 Setup Instructions for Windows & VS Code

Follow these simple steps in order.

### Step 1: Open the Project in VS Code
1. Open **Visual Studio Code**.
2. Click **File** > **Open Folder...** (or press `Ctrl + K, Ctrl + O`).
3. Select `C:\healthMateAI`.

---

### Step 2: Open PowerShell Terminal in VS Code
1. In VS Code, open the integrated terminal by pressing:  
   `` Ctrl + ` `` (Backtick) or go to **Terminal** > **New Terminal**.
2. Ensure PowerShell is the active terminal shell.

---

### Step 3: (Recommended) Create & Activate a Python Virtual Environment
Creating a virtual environment ensures project packages do not conflict with other Python applications on your computer.

Run this command:
```powershell
python -m venv venv
```

Now activate the virtual environment:
```powershell
.\venv\Scripts\Activate.ps1
```

> **Note for Windows Users:** If PowerShell shows an error saying *`Execution of scripts is disabled on this system`*, run this command once to allow local script activation:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```
> Then run `.\venv\Scripts\Activate.ps1` again. You will see `(venv)` at the beginning of your terminal prompt.

---

### Step 4: Install Project Dependencies
Install all required packages from `requirements.txt`:

```powershell
python -m pip install -r requirements.txt
```

**Expected Terminal Output:**
```
Successfully installed Flask-3.1.3 pypdf-6.20.1 python-dotenv-1.2.3 requests-2.34.2 ...
```

---

### Step 5: (Optional) Configure Google Gemini AI Key
By default, **HealthMate AI does not pretend to be connected to an AI model**. It clearly runs in **"Safe Local Knowledge Base Mode"** using its built-in medical dictionary.

If you wish to test live AI responses:
1. Make a copy of `.env.example` named `.env`:
   ```powershell
   Copy-Item .env.example .env
   ```
2. Open `.env` in VS Code and paste your free Gemini API key:
   ```env
   GEMINI_API_KEY=your_actual_gemini_api_key_here
   ```
   *(You can get a free API key at [https://aistudio.google.com/](https://aistudio.google.com/)).*
3. Save the file (`Ctrl + S`). If you leave it blank, the app will safely run in offline mode.

---

### Step 6: Start the Flask Application
Run:
```powershell
python app.py
```

**Expected Terminal Output:**
```
==========================================================
 🏥 HealthMate AI — AI-Powered Personal Health Copilot
 SQLite Database initialized at: C:\healthMateAI\healthmate.db
 AI Status: Safe Local Engine (Offline) (Local Safe Medical Knowledge Engine)
 Server running locally at: http://127.0.0.1:5000
==========================================================
 * Serving Flask app 'app'
 * Debug mode: on
 * Running on http://127.0.0.1:5000
```

---

### Step 7: Open the Application in Your Web Browser
1. Open Google Chrome, Microsoft Edge, or Mozilla Firefox.
2. Navigate to:
   ```
   http://127.0.0.1:5000
   ```
3. You will see the HealthMate AI dashboard ready to use!

---

## 🧪 How to Test Every Feature (Demo Guide)

### 1. Test Language Toggle (English ⇄ Telugu)
- Click the **తెలుగు** button in the top navigation bar.
- Notice how navigation labels, section titles, medicine instructions, emergency text, and glossary translations update instantly to Telugu.
- Click **English** to switch back anytime.

### 2. Test Accessibility Controls
- **Font Size**: Click `A+` or `A++` in the top bar to scale up text for grandparents or elderly users.
- **High Contrast**: Click the **👁️ Contrast** button to toggle a high-visibility dark mode with crisp borders.
- **Privacy Mode**: Click **🔒 Privacy** to blur patient names when viewing your screen in public.

### 3. Test Medical Report Summarizer (1-Click Test)
1. Navigate to the **Report Summarizer** tab.
2. Click the **"📋 Load Sample Blood Test Report"** button.
3. This fills the form with a realistic sample metabolic lab report (Grandpa Rao, Age 68, with HbA1c, FBS, Hemoglobin, Platelets, and Cholesterol).
4. Click **"⚡ Analyze & Summarize Report"**.
5. View the output:
   - Switch between **English Summary** and **తెలుగు సారాంశం (Telugu Summary)** tabs.
   - Click the **"🔊 Read Aloud"** button to hear the summary spoken in audio!
   - Review the recognized lab terms and doctor consultation questions.

### 4. Test Doctor Appointments
1. Navigate to the **Doctor Appointments** tab.
2. View the pre-seeded sample visits for *Grandpa Rao* and *Ananya*.
3. Click **"✓ Done"** on an upcoming appointment to mark it completed.
4. Click **"+ Schedule Appointment"**, fill in the simple form, and save to SQLite.
5. Filter using the tabs: **All**, **Upcoming**, **Completed**, **Cancelled**.

### 5. Test Medicine Schedule Tracker
1. Navigate to the **Medicine Tracker** tab.
2. Filter by time of day: **🌅 Morning**, **☀️ Afternoon**, **🌙 Night**.
3. Click the large **"○ Mark as Taken"** button on *Metformin 500mg* to mark it taken today.
4. Notice how the pill counter updates and shows a **Refill Alert** if remaining quantity drops below 5 pills.
5. Notice the clear medical disclaimer: *HealthMate AI is strictly a reminder tool and does not prescribe medication.*

### 6. Test the Safe AI Health Assistant
1. Navigate to the **Health Assistant** tab.
2. Click one of the quick question chips, e.g.:
   - *"What is HbA1c test and what is normal?"*
   - *"Explain LDL bad cholesterol in simple words"*
   - *"BP నియంత్రణ (తెలుగు)"*
3. **Emergency Guardrail Test**: Type *"I have severe chest pain and breathlessness"*.
   - Notice how HealthMate AI immediately halts standard chat and triggers an **URGENT EMERGENCY ALERT** with national helpline numbers (`108`, `112`).
4. **Prescription Refusal Guardrail Test**: Type *"What dose of paracetamol should I take?"*.
   - Notice how HealthMate AI safely refuses to prescribe medications or calculate drug dosages, instructing the user to consult their licensed doctor.

### 7. Reset Sample Data Anytime
- Scroll to the bottom of the page and click **"🔄 Reset Sample Data"** to reload clean sample records at any point during your viva or project presentation.

---

## 🛡️ Computer Science Concepts Explained (For CSE Viva & Exams)

### 1. Parameterized SQL Queries (Defense Against SQL Injection)
In `app.py`, SQL queries **never** use direct string formatting like `f"SELECT * FROM users WHERE name = '{name}'"`. Instead, they use SQLite's parameter placeholders (`?`):

```python
cursor.execute("""
    INSERT INTO appointments (
        patient_name, doctor_name, specialty,
        appointment_date, appointment_time, location_or_clinic,
        notes, status
    ) VALUES (?, ?, ?, ?, ?, ?, ?, 'Upcoming')
""", (patient_name, doctor_name, specialty, appointment_date, appointment_time, location_or_clinic, notes))
```
**Why this matters:** The database engine treats the parameters strictly as literal values rather than executable SQL commands, completely neutralizing SQL Injection attacks.

### 2. Honest AI Fallback Pattern
A common anti-pattern in beginner projects is faking AI responses with static mock delays. HealthMate AI implements a **Graceful Degradation Pattern**:
- If `GEMINI_API_KEY` is present $\rightarrow$ calls Google Gemini API with system safety instructions.
- If no key is set $\rightarrow$ transparently displays `Safe Local Engine (Offline)` badge and routes queries through a medically vetted local knowledge base.

### 3. Client & Server Dual-Validation
- **Client-Side** (`script.js`): Prevents invalid requests before they leave the browser (e.g. file size > 5MB, empty required fields).
- **Server-Side** (`app.py`): Re-validates data and sanitizes user input with `html.escape()` to guard against Cross-Site Scripting (XSS).

---

## ⚠️ Important Medical Disclaimer
> HealthMate AI is an educational personal health companion and reminder tool developed for academic demonstration. It does not provide medical diagnoses, treatment plans, or drug prescriptions. Always seek the advice of a qualified physician or healthcare professional for any medical condition. In case of an emergency, call **108** (India) or your local emergency response service immediately.

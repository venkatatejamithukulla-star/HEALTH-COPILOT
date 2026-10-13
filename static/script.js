/**
 * HealthMate AI — Frontend Client Application Logic
 * Accessible Personal Health Copilot (English & Telugu)
 * Suitable for CSE students, beginners, grandparents, and families.
 */

// ==============================================================================
// 0. CSRF TOKEN HELPER & REQUEST INTERCEPTOR
// ==============================================================================

function getCsrfToken() {
    return document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
}

// Automatically attach X-CSRF-Token to all state-changing requests
const originalFetch = window.fetch;
window.fetch = function(url, options = {}) {
    if (options && options.method && ["POST", "PUT", "PATCH", "DELETE"].includes(options.method.toUpperCase())) {
        options.headers = options.headers || {};
        if (options.headers instanceof Headers) {
            if (!options.headers.has("X-CSRF-Token")) {
                options.headers.set("X-CSRF-Token", getCsrfToken());
            }
        } else if (Array.isArray(options.headers)) {
            options.headers.push(["X-CSRF-Token", getCsrfToken()]);
        } else {
            options.headers["X-CSRF-Token"] = getCsrfToken();
        }
    }
    return originalFetch(url, options);
};

// ==============================================================================
// 1. BILINGUAL TRANSLATION DICTIONARY (English & Telugu)
// ==============================================================================

const TRANSLATIONS = {
    en: {
        brandSubtitle: "ఆరోగ్య సహచరి • Personal Health Copilot",
        emergencyAlertHead: "Emergency Medical Helplines:",
        emergencyAlertSub: "Call instantly in case of chest pain, stroke, or severe breathlessness",
        lblAmbulance: "Ambulance",
        lblNational: "National Helpline",
        lblHealthAdvice: "Health Advice",
        lblHighContrast: "Contrast",
        lblPrivacy: "Privacy",

        // Navigation
        navTitleAppt: "Doctor Appointments",
        navDescAppt: "Schedule and track clinic visits",
        navTitleMed: "Medicine Tracker",
        navDescMed: "Daily dose times & refill alerts",
        navTitleRep: "Report Summarizer",
        navDescRep: "Lab tests explained in simple words",
        navTitleChat: "Health Assistant",
        navDescChat: "Safe medical Q&A copilot",
        navTitleGloss: "Medical Glossary",
        navDescGloss: "Telugu & English health dictionary",

        // Appointments Section
        titleAppointments: "📅 Doctor Appointments & Clinic Visits",
        subAppointments: "Never miss a follow-up or routine health checkup.",
        btnTextNewAppt: "Schedule Appointment",
        msgLoadingAppts: "Loading appointments from SQLite database...",

        // Medicines Section
        titleMedicines: "💊 Prescribed Medicine Schedule",
        subMedicines: "Track daily doses prescribed by your registered doctor.",
        btnTextNewMed: "Add Prescribed Medicine",
        medDisclaimerHead: "Important Safety Guardrail:",
        medDisclaimerBody: "HealthMate AI is strictly a reminder and tracking tool. It does NOT independently prescribe medicines, change dosages, or offer medical treatments. Take medicines only in accordance with your registered doctor's prescription.",
        msgLoadingMeds: "Loading prescribed medicines...",

        // Reports Section
        titleReports: "📑 Medical Report Summarizer & Term Explainer",
        subReports: "Upload or paste blood tests, prescriptions, and lab reports for simple English & Telugu explanations.",
        btnTextLoadSample: "Load Sample Blood Test Report",
        reportInputTitle: "Upload or Paste Medical Report",
        lblRepPatientName: "Patient Name",
        lblRepTitle: "Report Title",
        dropzoneText: "Drag and drop report PDF, TXT, or Image",
        dropzoneSub: "Or click to browse your computer (Max 5MB)",
        lblOrPaste: "OR PASTE REPORT TEXT DIRECTLY",
        lblRepPastedText: "Medical Report Text / Doctor Notes",
        btnTextAnalyze: "Analyze & Summarize Report",
        outputReportTitle: "Report Summary & Insights",
        emptySummaryTitle: "No report analyzed yet",
        emptySummaryDesc: "Click 'Load Sample Blood Test Report' or upload your own lab document to view a plain English & Telugu breakdown.",
        titleSavedReports: "📁 Saved Report History in SQLite",
        lblReadAloud: "Read Aloud",

        // Assistant Section
        titleAssistant: "💬 HealthMate AI Assistant",
        subAssistant: "Ask questions about medical terms, lab results, and everyday wellness in English or Telugu.",
        lblQuickQuestions: "Quick Questions:",
        btnTextSend: "Send",
        chatPlaceholder: "Ask a health or lab test question in English or Telugu...",

        // Glossary Section
        titleGlossary: "📖 Bilingual Medical Glossary (వైద్య పదకోశం)",
        subGlossary: "Understand complex medical report terminology with standard reference ranges and Telugu definitions.",
        glossarySearchPlaceholder: "Search lab test (e.g. HbA1c, Hemoglobin, Creatinine, Cholesterol, BP, Thyroid)..."
    },
    te: {
        brandSubtitle: "ఆరోగ్య సహచరి • మీ వ్యక్తిగత ఆరోగ్య సహాయకుడు",
        emergencyAlertHead: "అత్యవసర వైద్య హెల్ప్‌లైన్లు:",
        emergencyAlertSub: "గుండె నొప్పి, పక్షవాతం లేదా తీవ్రమైన శ్వాస సమస్యలలో వెంటనే కాల్ చేయండి",
        lblAmbulance: "అంబులెన్స్",
        lblNational: "జాతీయ హెల్ప్‌లైన్",
        lblHealthAdvice: "ఆరోగ్య సలహా",
        lblHighContrast: "కాంట్రాస్ట్",
        lblPrivacy: "గోప్యత",

        // Navigation
        navTitleAppt: "డాక్టర్ అపాయింట్‌మెంట్లు",
        navDescAppt: "వైద్యుల సందర్శనల వివరాలు",
        navTitleMed: "మందుల సమయాలు",
        navDescMed: "రోజువారీ మందుల పట్టిక & అలర్ట్‌లు",
        navTitleRep: "రిపోర్ట్ వివరణ",
        navDescRep: "ల్యాబ్ రిపోర్టుల సులభమైన వివరణ",
        navTitleChat: "ఆరోగ్య సహాయకుడు",
        navDescChat: "సురక్షితమైన వైద్య Q&A కాపిలట్",
        navTitleGloss: "వైద్య పదకోశం",
        navDescGloss: "తెలుగు & ఇంగ్లీష్ ఆరోగ్య నిఘంటువు",

        // Appointments Section
        titleAppointments: "📅 వైద్యుల అపాయింట్‌మెంట్లు & క్లినిక్ వివరాలు",
        subAppointments: "డాక్టర్ ఫాలో-అప్ చెకప్‌లను ఎప్పటికీ మర్చిపోకండి.",
        btnTextNewAppt: "అపాయింట్‌మెంట్ నమోదు చేయండి",
        msgLoadingAppts: "SQLite నుండి అపాయింట్‌మెంట్లు లోడ్ అవుతున్నాయి...",

        // Medicines Section
        titleMedicines: "💊 డాక్టర్ సూచించిన మందుల సమయ పట్టిక",
        subMedicines: "మీ వైద్యుడు సూచించిన రోజువారీ మోతాదులను ట్రాక్ చేయండి.",
        btnTextNewMed: "మందును నమోదు చేయండి",
        medDisclaimerHead: "ముఖ్యమైన భద్రతా హెచ్చరిక:",
        medDisclaimerBody: "హెల్త్‌మేట్ AI కేవలం మందుల సమయాలను గుర్తుచేసే సాధనం మాత్రమే. ఇది స్వతంత్రంగా మందులను లేదా మోతాదులను నిర్ణయించదు. ఎల్లప్పుడూ మీ అర్హత కలిగిన డాక్టర్ సూచనల మేరకే మందులు వాడండి.",
        msgLoadingMeds: "మందుల వివరాలు లోడ్ అవుతున్నాయి...",

        // Reports Section
        titleReports: "📑 మెడికల్ రిపోర్ట్ సారాంశం & పదాల వివరణ",
        subReports: "రక్త పరీక్షలు మరియు ల్యాబ్ రిపోర్టులను సులభమైన తెలుగు & ఇంగ్లీషులో అర్థం చేసుకోండి.",
        btnTextLoadSample: "నమూనా రక్త పరీక్ష నివేదికను లోడ్ చేయండి",
        reportInputTitle: "మెడికల్ రిపోర్టును అప్‌లోడ్ చేయండి లేదా పేస్ట్ చేయండి",
        lblRepPatientName: "రోగి పేరు",
        lblRepTitle: "రిపోర్ట్ శీర్షిక",
        dropzoneText: "రిపోర్ట్ PDF, TXT లేదా ఇమేజ్ ఫైల్‌ను ఇక్కడ వేయండి",
        dropzoneSub: "లేదా మీ కంప్యూటర్ నుండి ఎంచుకోండి (గరిష్టంగా 5MB)",
        lblOrPaste: "లేదా రిపోర్ట్ టెక్స్ట్‌ను నేరుగా పేస్ట్ చేయండి",
        lblRepPastedText: "మెడికల్ రిపోర్ట్ టెక్స్ట్ / డాక్టర్ నోట్స్",
        btnTextAnalyze: "రిపోర్టును విశ్లేషించి వివరించండి",
        outputReportTitle: "రిపోర్ట్ సారాంశం & పరిశీలనలు",
        emptySummaryTitle: "ఇంకా ఏ నివేదికా విశ్లేషించబడలేదు",
        emptySummaryDesc: "'నమూనా నివేదిక' బటన్ నొక్కండి లేదా మీ స్వంత ల్యాబ్ ఫైల్‌ను అప్‌లోడ్ చేసి సులభమైన వివరణ చూడండి.",
        titleSavedReports: "📁 SQLite లో భద్రపరచిన నివేదికల చరిత్ర",
        lblReadAloud: "వినండి (చదవండి)",

        // Assistant Section
        titleAssistant: "💬 హెల్త్‌మేట్ AI ఆరోగ్య సహాయకుడు",
        subAssistant: "వైద్య పదాలు, ల్యాబ్ ఫలితాలు మరియు ఆరోగ్యం గురించి తెలుగు లేదా ఇంగ్లీషులో అడగండి.",
        lblQuickQuestions: "ముఖ్యమైన ప్రశ్నలు:",
        btnTextSend: "పంపండి",
        chatPlaceholder: "ల్యాబ్ టెస్ట్ లేదా ఆరోగ్య ప్రశ్నను తెలుగు లేదా ఇంగ్లీషులో టైప్ చేయండి...",

        // Glossary Section
        titleGlossary: "📖 తెలుగు & ఇంగ్లీష్ వైద్య పదకోశం",
        subGlossary: "ల్యాబ్ పరీక్షల అర్థాలు మరియు సాధారణ పరిధులను సులభంగా తెలుసుకోండి.",
        glossarySearchPlaceholder: "పరీక్ష పేరును వెతకండి (ఉదా: HbA1c, హిమోగ్లోబిన్, కొలెస్ట్రాల్, బి.పి, థైరాయిడ్)..."
    }
};

// Application Global State
const state = {
    currentLang: localStorage.getItem("healthmate_lang") || "en",
    fontSize: localStorage.getItem("healthmate_font_size") || "normal",
    highContrast: localStorage.getItem("healthmate_contrast") === "true",
    privacyMode: localStorage.getItem("healthmate_privacy") === "true",
    appointments: [],
    medicines: [],
    glossary: [],
    aiConfig: { configured: false, provider: "Safe Local Engine" },
    currentReportSummary: null
};

// ==============================================================================
// 2. INITIALIZATION ON DOM READY
// ==============================================================================

document.addEventListener("DOMContentLoaded", () => {
    initAccessibilityState();
    setupEventListeners();
    applyLanguage(state.currentLang);
    checkSystemAndAIStatus();
    loadFamilyProfilesDashboard();
    loadAppointments();
    loadMedicines();
    loadSavedReports();
    loadGlossary();
});

async function loadFamilyProfilesDashboard() {
    const sel = document.getElementById("selectActiveProfile");
    const details = document.getElementById("activeProfileDetails");
    if (!sel) return;

    try {
        const res = await fetch("/api/profiles");
        const data = await res.json();
        if (data.success && data.profiles) {
            sel.innerHTML = data.profiles.map(p => 
                `<option value="${p.id}" ${p.id == data.active_profile_id ? 'selected' : ''}>${escapeHtml(p.name)} (${escapeHtml(p.relationship)})</option>`
            ).join("");

            const updateDetails = () => {
                const chosenId = sel.value;
                const p = data.profiles.find(item => item.id == chosenId);
                if (p) {
                    if (details) {
                        details.textContent = `(Age: ${p.age || '—'} • ${escapeHtml(p.gender || '—')} • Blood: ${escapeHtml(p.blood_group || 'Unknown')})`;
                    }
                    const bgText = p.blood_group || 'O+';
                    const hBadge = document.getElementById("headerBloodGroupText");
                    if (hBadge) hBadge.textContent = bgText;
                    const emBadge = document.getElementById("emergencyBloodGroupText");
                    if (emBadge) emBadge.textContent = bgText;
                    const tip = document.getElementById("profileTooltip");
                    if (tip) {
                        tip.title = `Profile: ${p.name} (${p.relationship}) • Age: ${p.age} • Gender: ${p.gender} • Blood Group: ${bgText}`;
                    }
                }
            };
            updateDetails();

            sel.addEventListener("change", async () => {
                const chosenId = sel.value;
                await fetch("/api/profiles/active", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ profile_id: chosenId })
                });
                updateDetails();
                loadAppointments();
                loadMedicines();
                loadSavedReports();
                const p = data.profiles.find(item => item.id == chosenId);
                showToast(`Switched active profile to ${p ? p.name : 'family member'}`, "info");
            });
        }
    } catch (err) {
        console.warn("Could not load family profiles:", err);
    }
}

// ==============================================================================
// 3. ACCESSIBILITY & THEME CONTROLS
// ==============================================================================

function initAccessibilityState() {
    // Apply font size
    if (state.fontSize === "large") document.body.classList.add("font-large");
    if (state.fontSize === "xlarge") document.body.classList.add("font-xlarge");
    updateFontButtons();

    // Apply high contrast
    if (state.highContrast) {
        document.body.classList.add("high-contrast");
        document.getElementById("btnHighContrast")?.classList.add("active");
    }

    // Apply privacy mode
    if (state.privacyMode) {
        document.body.classList.add("privacy-mode");
        document.getElementById("btnPrivacyMode")?.classList.add("active");
    }
}

function setFontSize(size) {
    document.body.classList.remove("font-large", "font-xlarge");
    state.fontSize = size;
    localStorage.setItem("healthmate_font_size", size);

    if (size === "large") document.body.classList.add("font-large");
    if (size === "xlarge") document.body.classList.add("font-xlarge");

    updateFontButtons();
}

function updateFontButtons() {
    document.getElementById("btnFontSmall")?.classList.toggle("active", state.fontSize === "normal");
    document.getElementById("btnFontMedium")?.classList.toggle("active", state.fontSize === "large");
    document.getElementById("btnFontLarge")?.classList.toggle("active", state.fontSize === "xlarge");
}

function toggleHighContrast() {
    state.highContrast = !state.highContrast;
    document.body.classList.toggle("high-contrast", state.highContrast);
    document.getElementById("btnHighContrast")?.classList.toggle("active", state.highContrast);
    localStorage.setItem("healthmate_contrast", state.highContrast);
    showToast(state.highContrast ? "High Contrast Mode enabled" : "Standard mode restored", "info");
}

function togglePrivacyMode() {
    state.privacyMode = !state.privacyMode;
    document.body.classList.toggle("privacy-mode", state.privacyMode);
    document.getElementById("btnPrivacyMode")?.classList.toggle("active", state.privacyMode);
    localStorage.setItem("healthmate_privacy", state.privacyMode);
    showToast(state.privacyMode ? "Privacy Mode: Names masked" : "Privacy Mode disabled", "info");
}

// ==============================================================================
// 4. LANGUAGE TRANSLATION ENGINE (All 22 Scheduled Indian Languages + English)
// ==============================================================================

async function applyLanguage(lang) {
    state.currentLang = lang;
    localStorage.setItem("healthmate_lang", lang);

    // RTL for Urdu (ur), Kashmiri (ks), Sindhi (sd)
    const isRtl = ["ur", "ks", "sd"].includes(lang);
    document.documentElement.dir = isRtl ? "rtl" : "ltr";
    document.documentElement.lang = lang;

    // Sync UI switches
    document.querySelectorAll(".lang-btn").forEach(btn => {
        btn.classList.toggle("active", btn.getAttribute("data-lang") === lang);
    });
    const langSelect = document.getElementById("allLanguagesSelect");
    if (langSelect) langSelect.value = lang;

    // Load translations from cache or API
    if (!TRANSLATIONS[lang]) {
        try {
            const res = await fetch(`/api/locales/${lang}`);
            const data = await res.json();
            if (data.success && data.translations) {
                TRANSLATIONS[lang] = data.translations;
            }
        } catch (e) {
            console.warn("Could not fetch remote translations for", lang, e);
        }
    }

    const dict = TRANSLATIONS[lang] || TRANSLATIONS.en || {};

    // Translate all targeted UI elements by ID
    for (const [key, value] of Object.entries(dict)) {
        if (key.startsWith("_")) continue;
        const el = document.getElementById(key);
        if (el) {
            el.innerHTML = value;
        }
    }

    // Placeholders
    const chatInput = document.getElementById("chatInputText");
    if (chatInput && dict.chatPlaceholder) chatInput.placeholder = dict.chatPlaceholder;

    const glossSearch = document.getElementById("glossarySearchInput");
    if (glossSearch && dict.glossarySearchPlaceholder) glossSearch.placeholder = dict.glossarySearchPlaceholder;

    // Inform server session of language change
    try {
        fetch("/api/set-language", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ language: lang })
        }).catch(() => {});
    } catch (_) {}

    // Re-render components with language sensitive text
    renderAppointments();
    renderMedicines();
    renderGlossary(state.glossary);
}

// ==============================================================================
// 5. EVENT LISTENERS SETUP
// ==============================================================================

function setupEventListeners() {
    // Top Bar Accessibility Buttons
    document.getElementById("btnFontSmall")?.addEventListener("click", () => setFontSize("normal"));
    document.getElementById("btnFontMedium")?.addEventListener("click", () => setFontSize("large"));
    document.getElementById("btnFontLarge")?.addEventListener("click", () => setFontSize("xlarge"));
    document.getElementById("btnHighContrast")?.addEventListener("click", toggleHighContrast);
    document.getElementById("btnPrivacyMode")?.addEventListener("click", togglePrivacyMode);

    // Language switchers
    document.querySelectorAll(".lang-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            const l = btn.getAttribute("data-lang");
            if (l) applyLanguage(l);
        });
    });
    document.getElementById("allLanguagesSelect")?.addEventListener("change", (e) => {
        applyLanguage(e.target.value);
    });

    // Emergency Share Location button
    document.getElementById("btnEmergencyShareLoc")?.addEventListener("click", () => {
        if (!navigator.geolocation) {
            showToast("Geolocation is not supported by your browser.", "error");
            return;
        }
        showToast("📍 Fetching your exact GPS coordinates...", "info");
        navigator.geolocation.getCurrentPosition(
            (pos) => {
                const lat = pos.coords.latitude.toFixed(5);
                const lon = pos.coords.longitude.toFixed(5);
                const mapsUrl = `https://maps.google.com/?q=${lat},${lon}`;
                const shareText = `Emergency Medical Assistance Needed! My Location: ${mapsUrl}`;
                if (navigator.clipboard) {
                    navigator.clipboard.writeText(shareText);
                    showToast(`✅ Location copied to clipboard! Lat: ${lat}, Lon: ${lon}`, "success");
                } else {
                    window.open(`https://api.whatsapp.com/send?text=${encodeURIComponent(shareText)}`, "_blank");
                }
            },
            (err) => {
                showToast("⚠️ Could not retrieve location. Please check location permissions.", "error");
            },
            { enableHighAccuracy: true, timeout: 10000 }
        );
    });

    // Main Navigation Cards
    document.querySelectorAll(".nav-card").forEach(card => {
        card.addEventListener("click", () => {
            const targetId = card.getAttribute("data-target");
            switchSection(targetId, card);
        });
    });

    // Modals
    document.getElementById("btnOpenNewApptModal")?.addEventListener("click", () => openModal("modalAppointment"));
    document.getElementById("btnOpenNewMedModal")?.addEventListener("click", () => openModal("modalMedicine"));

    document.querySelectorAll("[data-close]").forEach(btn => {
        btn.addEventListener("click", () => {
            const modalId = btn.getAttribute("data-close");
            closeModal(modalId);
        });
    });

    // Close modal on click outside box
    document.querySelectorAll(".modal-overlay").forEach(overlay => {
        overlay.addEventListener("click", (e) => {
            if (e.target === overlay) {
                overlay.classList.remove("active");
            }
        });
    });

    // Appointment Filter Tabs
    document.querySelectorAll("#apptFilterTabs .tab-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            document.querySelectorAll("#apptFilterTabs .tab-btn").forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            const filter = btn.getAttribute("data-filter");
            filterAppointments(filter);
        });
    });

    // Medicine Slot Tabs
    document.querySelectorAll("#medSlotFilterTabs .tab-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            document.querySelectorAll("#medSlotFilterTabs .tab-btn").forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            const slot = btn.getAttribute("data-slot");
            filterMedicines(slot);
        });
    });

    // Form Submissions
    document.getElementById("formNewAppointment")?.addEventListener("submit", handleCreateAppointment);
    document.getElementById("formNewMedicine")?.addEventListener("submit", handleAddMedicine);
    document.getElementById("reportForm")?.addEventListener("submit", handleAnalyzeReport);
    document.getElementById("chatForm")?.addEventListener("submit", handleChatSubmit);

    // Report Helpers
    document.getElementById("btnLoadSampleReport")?.addEventListener("click", loadSampleBloodReport);
    document.getElementById("btnClearReportForm")?.addEventListener("click", clearReportForm);
    document.getElementById("btnSpeakSummary")?.addEventListener("click", speakCurrentReportSummary);

    // File Drag & Drop
    setupFileDropzone();

    // Quick Prompts Chips
    document.querySelectorAll(".chip-btn").forEach(chip => {
        chip.addEventListener("click", () => {
            const query = chip.getAttribute("data-query");
            const input = document.getElementById("chatInputText");
            if (input) {
                input.value = query;
                document.getElementById("chatForm")?.dispatchEvent(new Event("submit"));
            }
        });
    });

    // Glossary Search
    document.getElementById("glossarySearchInput")?.addEventListener("input", (e) => {
        searchGlossary(e.target.value);
    });
    document.getElementById("btnClearGlossarySearch")?.addEventListener("click", () => {
        const input = document.getElementById("glossarySearchInput");
        if (input) {
            input.value = "";
            renderGlossary(state.glossary);
        }
    });

    // Reset Sample Data
    document.getElementById("btnResetSampleData")?.addEventListener("click", handleResetSampleData);

    // Voice Input (Web Speech Recognition)
    document.getElementById("btnVoiceInput")?.addEventListener("click", handleVoiceInput);
}

function switchSection(targetSectionId, activeCard) {
    document.querySelectorAll(".nav-card").forEach(c => c.classList.remove("active"));
    document.querySelectorAll(".app-section").forEach(s => s.classList.remove("active"));

    if (activeCard) activeCard.classList.add("active");
    const targetSection = document.getElementById(targetSectionId);
    if (targetSection) {
        targetSection.classList.add("active");
        window.scrollTo({ top: 120, behavior: "smooth" });
    }
}

function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add("active");
        // Auto set today's date for appointment
        const dateInput = modal.querySelector("input[type='date']");
        if (dateInput && !dateInput.value) {
            dateInput.value = new Date().toISOString().split("T")[0];
        }
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) modal.classList.remove("active");
}

// ==============================================================================
// 6. SYSTEM STATUS & HONEST AI INDICATOR
// ==============================================================================

async function checkSystemAndAIStatus() {
    try {
        const res = await fetch("/api/status");
        const data = await res.json();
        state.aiConfig = data.ai || {};

        const badge = document.getElementById("aiStatusBadge");
        const text = document.getElementById("aiStatusText");
        const chatBadgeText = document.getElementById("chatEngineText");

        if (data.ai && data.ai.configured) {
            badge.className = "ai-status-badge live-ai";
            text.textContent = data.ai.badge_text || "Live AI Active";
            if (chatBadgeText) chatBadgeText.textContent = `🟢 ${data.ai.provider}`;
        } else {
            badge.className = "ai-status-badge offline-safe";
            text.textContent = "Safe Local Mode (Offline)";
            if (chatBadgeText) chatBadgeText.textContent = "🔵 Safe Local Knowledge Engine";
        }
    } catch (err) {
        console.warn("Could not fetch system status:", err);
    }
}

// ==============================================================================
// 7. APPOINTMENTS MANAGEMENT (SQLite Backed)
// ==============================================================================

async function loadAppointments() {
    try {
        const pid = document.getElementById("selectActiveProfile")?.value;
        const url = pid ? `/api/appointments?profile_id=${pid}` : "/api/appointments";
        const res = await fetch(url);
        const data = await res.json();
        if (data.success) {
            state.appointments = data.appointments;
            updateAppointmentCounts();
            renderAppointments();
        }
    } catch (err) {
        showToast("Error loading appointments from database.", "error");
    }
}

function updateAppointmentCounts() {
    const all = state.appointments.length;
    const upcoming = state.appointments.filter(a => a.status === "Upcoming").length;
    const completed = state.appointments.filter(a => a.status === "Completed").length;
    const cancelled = state.appointments.filter(a => a.status === "Cancelled").length;

    document.getElementById("countAllAppt").textContent = all;
    document.getElementById("countUpcomingAppt").textContent = upcoming;
    document.getElementById("countCompletedAppt").textContent = completed;
    document.getElementById("countCancelledAppt").textContent = cancelled;
}

function filterAppointments(status) {
    if (!status) {
        renderAppointments(state.appointments);
    } else {
        const filtered = state.appointments.filter(a => a.status === status);
        renderAppointments(filtered);
    }
}

function renderAppointments(list = state.appointments) {
    const container = document.getElementById("appointmentsContainer");
    if (!container) return;

    if (!list || list.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">📅</div>
                <h4>${state.currentLang === 'te' ? 'అపాయింట్‌మెంట్లు లేవు' : 'No appointments scheduled'}</h4>
                <p>${state.currentLang === 'te' ? 'కొత్త అపాయింట్‌మెంట్ నమోదు చేయడానికి పై బటన్ నొక్కండి.' : 'Click "+ Schedule Appointment" above to add your first visit.'}</p>
            </div>
        `;
        return;
    }

    container.innerHTML = list.map(apt => `
        <div class="appointment-card" id="apt-card-${apt.id}">
            <div class="appt-top">
                <div>
                    <h4 class="appt-doctor-name">${escapeHtml(apt.doctor_name)}</h4>
                    <span class="appt-specialty">${escapeHtml(apt.specialty)}</span>
                </div>
                <span class="status-tag status-${apt.status}">${apt.status}</span>
            </div>

            <div class="appt-meta">
                <div class="meta-row">
                    <span>👤</span>
                    <span><strong>${state.currentLang === 'te' ? 'రోగి:' : 'Patient:'}</strong> <span class="sensitive-data">${escapeHtml(apt.patient_name)}</span></span>
                </div>
                <div class="meta-row">
                    <span>🗓️</span>
                    <span><strong>${formatFriendlyDate(apt.appointment_date)}</strong> at <strong>${apt.appointment_time}</strong></span>
                </div>
                <div class="meta-row">
                    <span>🏥</span>
                    <span>${escapeHtml(apt.location_or_clinic || 'Clinic')}</span>
                </div>
            </div>

            ${apt.notes ? `
                <div class="appt-notes-box">
                    <strong>${state.currentLang === 'te' ? 'గమనిక:' : 'Notes:'}</strong> ${escapeHtml(apt.notes)}
                </div>
            ` : ''}

            <div class="appt-actions">
                ${apt.status === 'Upcoming' ? `
                    <button type="button" class="btn btn-secondary btn-sm" onclick="updateAppointmentStatus(${apt.id}, 'Completed')">
                        ✓ ${state.currentLang === 'te' ? 'పూర్తయింది' : 'Done'}
                    </button>
                    <button type="button" class="btn btn-ghost btn-sm" onclick="updateAppointmentStatus(${apt.id}, 'Cancelled')">
                        ✕ ${state.currentLang === 'te' ? 'రద్దు' : 'Cancel'}
                    </button>
                ` : `
                    <button type="button" class="btn btn-ghost btn-sm" onclick="updateAppointmentStatus(${apt.id}, 'Upcoming')">
                        ↺ ${state.currentLang === 'te' ? 'తిరిగి ఓపెన్ చేయండి' : 'Reopen'}
                    </button>
                `}
                <button type="button" class="btn btn-ghost btn-sm text-muted" style="margin-left:auto;" onclick="deleteAppointmentRecord(${apt.id})">
                    🗑️
                </button>
            </div>
        </div>
    `).join("");
}

async function handleCreateAppointment(e) {
    e.preventDefault();
    const form = e.target;
    const submitBtn = document.getElementById("btnSubmitAppt");
    submitBtn.disabled = true;

    const payload = {
        patient_name: form.patient_name.value.trim(),
        doctor_name: form.doctor_name.value.trim(),
        specialty: form.specialty.value.trim(),
        appointment_date: form.appointment_date.value.trim(),
        appointment_time: form.appointment_time.value.trim(),
        location_or_clinic: form.location_or_clinic.value.trim(),
        notes: form.notes.value.trim()
    };

    try {
        const res = await fetch("/api/appointments", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        const data = await res.json();

        if (data.success) {
            showToast("Doctor appointment scheduled successfully!", "success");
            form.reset();
            closeModal("modalAppointment");
            loadAppointments();
        } else {
            showToast(data.error || "Failed to schedule appointment.", "error");
        }
    } catch (err) {
        showToast("Network error. Please try again.", "error");
    } finally {
        submitBtn.disabled = false;
    }
}

async function updateAppointmentStatus(id, newStatus) {
    try {
        const res = await fetch(`/api/appointments/${id}`, {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ status: newStatus })
        });
        const data = await res.json();
        if (data.success) {
            showToast(`Appointment marked as ${newStatus}.`, "success");
            loadAppointments();
        } else {
            showToast(data.error || "Could not update status.", "error");
        }
    } catch (err) {
        showToast("Network error updating status.", "error");
    }
}

async function deleteAppointmentRecord(id) {
    if (!confirm(state.currentLang === 'te' ? 'ఈ అపాయింట్‌మెంట్‌ను తొలగించాలా?' : 'Are you sure you want to delete this appointment?')) {
        return;
    }

    try {
        const res = await fetch(`/api/appointments/${id}`, { method: "DELETE" });
        const data = await res.json();
        if (data.success) {
            showToast("Appointment deleted.", "info");
            loadAppointments();
        }
    } catch (err) {
        showToast("Error deleting appointment.", "error");
    }
}

// ==============================================================================
// 8. MEDICINE SCHEDULE TRACKING (Safe - No Independent Prescriptions)
// ==============================================================================

async function loadMedicines() {
    try {
        const pid = document.getElementById("selectActiveProfile")?.value;
        const url = pid ? `/api/medicines?profile_id=${pid}` : "/api/medicines";
        const res = await fetch(url);
        const data = await res.json();
        if (data.success) {
            state.medicines = data.medicines;
            renderMedicines();
        }
    } catch (err) {
        showToast("Error loading medicine schedule.", "error");
    }
}

function filterMedicines(slot) {
    if (!slot) {
        renderMedicines(state.medicines);
    } else {
        const filtered = state.medicines.filter(m => m.timing_slot.toLowerCase().includes(slot.toLowerCase()));
        renderMedicines(filtered);
    }
}

function renderMedicines(list = state.medicines) {
    const container = document.getElementById("medicinesContainer");
    if (!container) return;

    if (!list || list.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">💊</div>
                <h4>${state.currentLang === 'te' ? 'మందుల జాబితా ఖాళీగా ఉంది' : 'No medicines in tracker'}</h4>
                <p>${state.currentLang === 'te' ? 'డాక్టర్ సూచించిన మందులను జోడించడానికి పై బటన్ నొక్కండి.' : 'Click "+ Add Prescribed Medicine" above to track your daily doses.'}</p>
            </div>
        `;
        return;
    }

    container.innerHTML = list.map(med => {
        const isTaken = med.taken_today === 1;
        const lowPills = med.pills_left <= 5;

        return `
            <div class="medicine-card ${isTaken ? 'taken-today' : ''}" id="med-card-${med.id}">
                <div class="med-header">
                    <div>
                        <h4 class="med-name">${escapeHtml(med.medicine_name)}</h4>
                        <span class="text-muted" style="font-size:0.8rem;">
                            👤 <span class="sensitive-data">${escapeHtml(med.patient_name)}</span>
                        </span>
                    </div>
                    <span class="med-timing-badge">${med.timing_slot}</span>
                </div>

                <div class="med-dosage-box">
                    <strong>${state.currentLang === 'te' ? 'మోతాదు:' : 'Prescribed Dose:'}</strong> ${escapeHtml(med.prescribed_dosage)}
                </div>

                <div class="med-details-list">
                    <div>🔄 <strong>${state.currentLang === 'te' ? 'తరచుదనం:' : 'Frequency:'}</strong> ${med.frequency}</div>
                    ${med.doctor_prescribed ? `<div>🩺 <strong>${state.currentLang === 'te' ? 'వైద్యులు:' : 'Prescribed by:'}</strong> ${escapeHtml(med.doctor_prescribed)}</div>` : ''}
                    ${med.instructions ? `<div>ℹ️ <em>${escapeHtml(med.instructions)}</em></div>` : ''}
                </div>

                ${lowPills ? `
                    <div class="med-stock-warning">
                        ⚠️ <strong>${state.currentLang === 'te' ? 'రీఫిల్ హెచ్చరిక:' : 'Refill Alert:'}</strong> ${med.pills_left} ${state.currentLang === 'te' ? 'మాత్రలు మాత్రమే మిగిలాయి!' : 'pills remaining in strip!'}
                    </div>
                ` : `
                    <div class="text-muted" style="font-size: 0.8rem;">
                        📦 ${med.pills_left} ${state.currentLang === 'te' ? 'మాత్రలు మిగిలాయి' : 'pills left in strip'}
                    </div>
                `}

                <div class="med-actions">
                    <button type="button" class="btn-toggle-taken" onclick="toggleMedicineTaken(${med.id})">
                        ${isTaken ? (state.currentLang === 'te' ? '✓ నేడు వేసుకున్నారు' : '✓ Taken Today') : (state.currentLang === 'te' ? '○ ఇంకా వేసుకోలేదు' : '○ Mark as Taken')}
                    </button>
                    <button type="button" class="btn btn-ghost btn-sm text-muted" onclick="deleteMedicineRecord(${med.id})" title="Remove medicine">
                        🗑️
                    </button>
                </div>
            </div>
        `;
    }).join("");
}

async function handleAddMedicine(e) {
    e.preventDefault();
    const form = e.target;
    const submitBtn = document.getElementById("btnSubmitMed");
    submitBtn.disabled = true;

    const payload = {
        patient_name: form.patient_name.value.trim(),
        medicine_name: form.medicine_name.value.trim(),
        prescribed_dosage: form.prescribed_dosage.value.trim(),
        timing_slot: form.timing_slot.value.trim(),
        frequency: form.frequency.value.trim(),
        doctor_prescribed: form.doctor_prescribed.value.trim(),
        instructions: form.instructions.value.trim(),
        pills_left: parseInt(form.pills_left.value || 30, 10)
    };

    try {
        const res = await fetch("/api/medicines", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        const data = await res.json();

        if (data.success) {
            showToast("Medicine added to reminder tracker!", "success");
            form.reset();
            closeModal("modalMedicine");
            loadMedicines();
        } else {
            showToast(data.error || "Failed to add medicine.", "error");
        }
    } catch (err) {
        showToast("Network error. Please try again.", "error");
    } finally {
        submitBtn.disabled = false;
    }
}

async function toggleMedicineTaken(id) {
    try {
        const res = await fetch(`/api/medicines/${id}/toggle-taken`, { method: "POST" });
        const data = await res.json();
        if (data.success) {
            showToast(data.message, "success");
            loadMedicines();
        }
    } catch (err) {
        showToast("Error updating medicine status.", "error");
    }
}

async function deleteMedicineRecord(id) {
    if (!confirm(state.currentLang === 'te' ? 'ఈ మందును తొలగించాలా?' : 'Remove this medicine from tracking?')) {
        return;
    }

    try {
        const res = await fetch(`/api/medicines/${id}`, { method: "DELETE" });
        const data = await res.json();
        if (data.success) {
            showToast("Medicine removed.", "info");
            loadMedicines();
        }
    } catch (err) {
        showToast("Error deleting medicine.", "error");
    }
}

// ==============================================================================
// 9. MEDICAL REPORT SUMMARIZER & TERM EXPLAINER
// ==============================================================================

function setupFileDropzone() {
    const dropzone = document.getElementById("fileDropzone");
    const fileInput = document.getElementById("reportFileInput");
    const badge = document.getElementById("selectedFileBadge");

    if (!dropzone || !fileInput) return;

    ["dragenter", "dragover"].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            dropzone.classList.add("dragover");
        });
    });

    ["dragleave", "drop"].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            dropzone.classList.remove("dragover");
        });
    });

    dropzone.addEventListener("drop", (e) => {
        if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
            fileInput.files = e.dataTransfer.files;
            handleFileSelection(fileInput.files[0]);
        }
    });

    fileInput.addEventListener("change", () => {
        if (fileInput.files && fileInput.files.length > 0) {
            handleFileSelection(fileInput.files[0]);
        }
    });
}

function handleFileSelection(file) {
    const badge = document.getElementById("selectedFileBadge");
    if (!file) {
        if (badge) badge.style.display = "none";
        return;
    }

    if (file.size > 5 * 1024 * 1024) {
        showToast("File is too large! Maximum limit is 5MB.", "error");
        document.getElementById("reportFileInput").value = "";
        if (badge) badge.style.display = "none";
        return;
    }

    if (badge) {
        badge.textContent = `Selected: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
        badge.style.display = "inline-block";
    }
}

function loadSampleBloodReport() {
    const sampleText =
`COMPLETE BLOOD PICTURE & METABOLIC SCREENING REPORT
Patient: Grandpa Rao (Age 68) | Lab Reference: SRL-2026-884
------------------------------------------------------------
1. Fasting Blood Sugar (FBS): 134 mg/dL     [Normal: 70 - 99 mg/dL]   (HIGH)
2. HbA1c (Glycated Hemoglobin): 7.2 %       [Normal: < 5.7%]          (ELEVATED)
3. Hemoglobin (Hb): 13.8 g/dL               [Normal: 13.5 - 17.5 g/dL] (NORMAL)
4. Platelet Count: 245,000 /mcL             [Normal: 150,000 - 450,000] (NORMAL)
5. Total Cholesterol: 218 mg/dL             [Desirable: < 200 mg/dL]  (BORDERLINE)
6. LDL Bad Cholesterol: 142 mg/dL           [Optimal: < 100 mg/dL]    (HIGH)
7. HDL Good Cholesterol: 44 mg/dL           [Protective: > 40 mg/dL]  (NORMAL)
8. Triglycerides: 168 mg/dL                 [Normal: < 150 mg/dL]     (BORDERLINE)
9. Serum Creatinine: 0.95 mg/dL             [Normal: 0.6 - 1.2 mg/dL] (NORMAL)
10. Blood Pressure: 138/88 mmHg             [Optimal: < 120/80 mmHg]  (STAGE 1 ELEVATED)
11. Thyroid TSH: 2.85 mIU/L                 [Normal: 0.4 - 4.5 mIU/L] (NORMAL)

Doctor's Note: Routine metabolic review for Grandpa Rao. Continue regular walking.`;

    const textarea = document.getElementById("repPastedText");
    const titleInput = document.getElementById("repTitle");
    const nameInput = document.getElementById("repPatientName");

    if (textarea) textarea.value = sampleText;
    if (titleInput) titleInput.value = "Annual Routine Blood & Metabolic Screening";
    if (nameInput) nameInput.value = "Grandpa Rao";

    showToast("Sample Blood Test Report loaded! Click 'Analyze & Summarize' to test.", "info");
}

function clearReportForm() {
    document.getElementById("reportForm")?.reset();
    const badge = document.getElementById("selectedFileBadge");
    if (badge) badge.style.display = "none";
}

async function handleAnalyzeReport(e) {
    e.preventDefault();
    const form = e.target;
    const btn = document.getElementById("btnAnalyzeReport");
    btn.disabled = true;
    btn.innerHTML = `<span class="spinner" style="width:20px;height:20px;margin:0;"></span> Analyzing...`;

    const formData = new FormData(form);

    try {
        const res = await fetch("/api/reports/analyze", {
            method: "POST",
            body: formData
        });
        const data = await res.json();

        if (data.success) {
            state.currentReportSummary = data;
            renderReportSummary(data);
            showToast("Report analyzed and summarized successfully!", "success");
            loadSavedReports();
        } else {
            showToast(data.error || "Analysis failed.", "error");
        }
    } catch (err) {
        showToast("Error processing report.", "error");
    } finally {
        btn.disabled = false;
        btn.innerHTML = `⚡ <span id="btnTextAnalyze">${state.currentLang === 'te' ? 'రిపోర్టును విశ్లేషించి వివరించండి' : 'Analyze & Summarize Report'}</span>`;
    }
}

function renderReportSummary(data) {
    const outputBody = document.getElementById("reportOutputBody");
    const outputActions = document.getElementById("outputActions");
    const title = document.getElementById("outputReportTitle");

    if (outputActions) outputActions.style.display = "flex";
    if (title) title.textContent = `📋 ${data.report_title} (${data.patient_name})`;

    outputBody.innerHTML = `
        <div class="report-summary-tabs">
            <button type="button" class="report-lang-btn active" id="tabSummaryEn" onclick="switchSummaryTab('en')">
                English Summary
            </button>
            <button type="button" class="report-lang-btn" id="tabSummaryTe" onclick="switchSummaryTab('te')">
                తెలుగు సారాంశం
            </button>
        </div>

        <div class="summary-content-box" id="summaryActiveContent">
            ${escapeHtml(state.currentLang === 'te' ? data.summary_telugu : data.summary_english)}
        </div>

        ${data.glossary_details && data.glossary_details.length > 0 ? `
            <div class="glossary-matches-box">
                <h4 style="font-size:0.95rem; margin-bottom: 0.5rem;">
                    🔍 ${state.currentLang === 'te' ? 'గుర్తించిన వైద్య పరీక్షలు:' : 'Medical Terminology Explained:'}
                </h4>
                <div>
                    ${data.glossary_details.map(g => `
                        <span class="glossary-pill-badge" title="${escapeHtml(g.meaning_en)}">
                            ${escapeHtml(g.term)} (${escapeHtml(g.telugu_term)})
                        </span>
                    `).join("")}
                </div>
            </div>
        ` : ''}

        <div class="modal-disclaimer" style="margin-top: 1rem; border-radius: 8px;">
            ⚠️ <strong>Medical Notice:</strong> This summary translates medical terms into everyday language for educational clarity. It is not an automated medical diagnosis. Please present this report to your doctor for clinical guidance.
        </div>
    `;

    // Highlight initial tab based on user language
    if (state.currentLang === "te") {
        switchSummaryTab("te");
    }
}

function switchSummaryTab(lang) {
    const tabEn = document.getElementById("tabSummaryEn");
    const tabTe = document.getElementById("tabSummaryTe");
    const box = document.getElementById("summaryActiveContent");

    if (!state.currentReportSummary || !box) return;

    if (lang === "te") {
        tabTe?.classList.add("active");
        tabEn?.classList.remove("active");
        box.textContent = state.currentReportSummary.summary_telugu;
    } else {
        tabEn?.classList.add("active");
        tabTe?.classList.remove("active");
        box.textContent = state.currentReportSummary.summary_english;
    }
}

function speakCurrentReportSummary() {
    if (!state.currentReportSummary) return;

    const isTelugu = document.getElementById("tabSummaryTe")?.classList.contains("active");
    const textToSpeak = isTelugu
        ? state.currentReportSummary.summary_telugu
        : state.currentReportSummary.summary_english;

    speakText(textToSpeak, isTelugu ? "te-IN" : "en-US");
}

async function loadSavedReports() {
    try {
        const pid = document.getElementById("selectActiveProfile")?.value;
        const url = pid ? `/api/reports?profile_id=${pid}` : "/api/reports";
        const res = await fetch(url);
        const data = await res.json();
        const container = document.getElementById("savedReportsContainer");
        if (!container) return;

        if (!data.reports || data.reports.length === 0) {
            container.innerHTML = `<p class="text-muted">${state.currentLang === 'te' ? 'ఇంకా సేవ్ చేసిన నివేదికలు లేవు.' : 'No saved reports in database.'}</p>`;
            return;
        }

        container.innerHTML = data.reports.map(rep => `
            <div class="saved-report-card" onclick="viewSavedReport(${rep.id})">
                <div>
                    <h5 style="font-size:0.95rem; font-weight:700;">${escapeHtml(rep.report_title)}</h5>
                    <span class="text-muted" style="font-size:0.8rem;">
                        👤 <span class="sensitive-data">${escapeHtml(rep.patient_name || 'Patient')}</span> • 📅 ${rep.report_date || ''}
                    </span>
                </div>
                <button type="button" class="btn btn-ghost btn-sm" onclick="event.stopPropagation(); deleteSavedReport(${rep.id})" title="Delete report">
                    🗑️
                </button>
            </div>
        `).join("");
    } catch (err) {
        console.warn("Could not load saved reports:", err);
    }
}

async function viewSavedReport(id) {
    openModal("modalViewReport");
    const modalBody = document.getElementById("viewReportModalBody");
    const modalTitle = document.getElementById("viewReportModalTitle");
    modalBody.innerHTML = `<div class="spinner"></div>`;

    try {
        const res = await fetch(`/api/reports/${id}`);
        const data = await res.json();
        if (data.success) {
            const rep = data.report;
            modalTitle.textContent = rep.report_title;
            modalBody.innerHTML = `
                <div style="margin-bottom: 1rem;">
                    <strong>Patient:</strong> <span class="sensitive-data">${escapeHtml(rep.patient_name)}</span> | 
                    <strong>Date:</strong> ${rep.report_date}
                </div>
                <div class="summary-content-box" style="margin-bottom: 1rem;">
                    <h4>English Breakdown:</h4>
                    <pre style="white-space: pre-wrap; font-family: inherit;">${escapeHtml(rep.summary_english)}</pre>
                </div>
                <div class="summary-content-box" style="background: #faf5ff;">
                    <h4>తెలుగు సారాంశం:</h4>
                    <pre style="white-space: pre-wrap; font-family: inherit;">${escapeHtml(rep.summary_telugu)}</pre>
                </div>
            `;
            document.getElementById("btnSpeakSavedReport").onclick = () => {
                speakText(rep.summary_english, "en-US");
            };
        }
    } catch (err) {
        modalBody.innerHTML = `<p class="text-muted">Error loading report details.</p>`;
    }
}

async function deleteSavedReport(id) {
    if (!confirm(state.currentLang === 'te' ? 'ఈ రిపోర్టును తొలగించాలా?' : 'Delete this saved report?')) return;

    try {
        const res = await fetch(`/api/reports/${id}`, { method: "DELETE" });
        const data = await res.json();
        if (data.success) {
            showToast("Report deleted from database.", "info");
            loadSavedReports();
        }
    } catch (err) {
        showToast("Error deleting report.", "error");
    }
}

// ==============================================================================
// 10. HEALTH ASSISTANT CHAT COPILOT
// ==============================================================================

async function handleChatSubmit(e) {
    e.preventDefault();
    const input = document.getElementById("chatInputText");
    const userMsg = input.value.trim();
    if (!userMsg) return;

    // Append user message to UI
    appendChatMessage("user", userMsg);
    input.value = "";

    // Show bot typing indicator
    const typingId = appendChatTyping();

    try {
        const res = await fetch("/api/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                message: userMsg,
                language: state.currentLang
            })
        });
        const data = await res.json();
        removeChatTyping(typingId);

        if (data.success) {
            const isEmergency = data.is_emergency === true;
            appendChatMessage("bot", data.reply, isEmergency, data.source);
            if (isEmergency) {
                // Play gentle alert or speak warning
                speakText("Urgent medical emergency detected. Please call 108 immediately.", "en-US");
            }
        } else {
            appendChatMessage("bot", "Sorry, I could not process that question. Please try again.");
        }
    } catch (err) {
        removeChatTyping(typingId);
        appendChatMessage("bot", "Network communication error. Please ensure the Flask server is running.");
    }
}

function appendChatMessage(sender, text, isEmergency = false, source = "") {
    const container = document.getElementById("chatMessagesContainer");
    if (!container) return;

    const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const isBot = sender === "bot";

    const msgDiv = document.createElement("div");
    msgDiv.className = `chat-message ${isBot ? 'bot-message' : 'user-message'}`;

    let sourceBadge = "";
    if (isBot && source) {
        if (source === "google_gemini_ai") {
            sourceBadge = `<span style="font-size:0.7rem; color:var(--accent-emerald-dark); font-weight:700;">🟢 Google Gemini</span>`;
        } else if (source === "emergency_guardrail") {
            sourceBadge = `<span style="font-size:0.7rem; color:var(--emergency-red); font-weight:700;">🚨 Emergency Guardrail</span>`;
        } else {
            sourceBadge = `<span style="font-size:0.7rem; color:var(--secondary); font-weight:700;">🔵 Safe Local Medical Engine</span>`;
        }
    }

    msgDiv.innerHTML = `
        <div class="message-avatar">${isBot ? '🩺' : '👤'}</div>
        <div class="message-content">
            <div class="message-sender">
                ${isBot ? 'HealthMate Copilot' : 'You'} ${sourceBadge}
            </div>
            <div class="message-text ${isEmergency ? 'emergency-message' : ''}">
                ${formatChatText(text)}
            </div>
            <div class="message-time">${timeStr}</div>
        </div>
    `;

    container.appendChild(msgDiv);
    container.scrollTop = container.scrollHeight;
}

function appendChatTyping() {
    const container = document.getElementById("chatMessagesContainer");
    if (!container) return null;

    const typingId = `typing-${Date.now()}`;
    const div = document.createElement("div");
    div.id = typingId;
    div.className = "chat-message bot-message";
    div.innerHTML = `
        <div class="message-avatar">🩺</div>
        <div class="message-content">
            <div class="message-text" style="display:flex;align-items:center;gap:6px;">
                <span class="spinner" style="width:14px;height:14px;margin:0;"></span>
                <span>Thinking safely...</span>
            </div>
        </div>
    `;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
    return typingId;
}

function removeChatTyping(typingId) {
    if (!typingId) return;
    const el = document.getElementById(typingId);
    if (el) el.remove();
}

function formatChatText(text) {
    // Converts basic markdown bold / bullet points into readable HTML
    let formatted = escapeHtml(text);
    formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    formatted = formatted.replace(/\*(.*?)\*/g, '<em>$1</em>');
    formatted = formatted.replace(/\n/g, '<br>');
    return formatted;
}

// ==============================================================================
// 11. BILINGUAL MEDICAL GLOSSARY
// ==============================================================================

async function loadGlossary() {
    try {
        const res = await fetch("/api/glossary");
        const data = await res.json();
        if (data.success) {
            state.glossary = data.terms;
            renderGlossary(state.glossary);
        }
    } catch (err) {
        console.warn("Could not load medical glossary:", err);
    }
}

function searchGlossary(query) {
    const q = query.trim().toLowerCase();
    if (!q) {
        renderGlossary(state.glossary);
        return;
    }

    const filtered = state.glossary.filter(item =>
        item.term.toLowerCase().includes(q) ||
        item.telugu_term.toLowerCase().includes(q) ||
        item.meaning_en.toLowerCase().includes(q) ||
        item.meaning_te.toLowerCase().includes(q)
    );
    renderGlossary(filtered);
}

function renderGlossary(list = state.glossary) {
    const container = document.getElementById("glossaryContainer");
    if (!container) return;

    if (!list || list.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">📖</div>
                <h4>${state.currentLang === 'te' ? 'పదాలు కనిపించలేదు' : 'No medical terms found'}</h4>
                <p>Try searching for "HbA1c", "BP", "Creatinine", or "Cholesterol".</p>
            </div>
        `;
        return;
    }

    container.innerHTML = list.map(item => `
        <div class="glossary-card">
            <div>
                <h4 class="glossary-term-name">${escapeHtml(item.term)}</h4>
                <span class="glossary-telugu-badge">${escapeHtml(item.telugu_term)}</span>
            </div>

            <div class="glossary-range-box">
                <strong>${state.currentLang === 'te' ? 'సాధారణ పరిధి:' : 'Standard Range:'}</strong> ${escapeHtml(item.normal_range)}
            </div>

            <div class="glossary-meaning-en">
                ${escapeHtml(item.meaning_en)}
            </div>

            <div class="glossary-meaning-te">
                <strong>తెలుగు వివరణ:</strong> ${escapeHtml(item.meaning_te)}
            </div>

            <div class="glossary-actions">
                <button type="button" class="btn btn-ghost btn-sm" onclick="speakGlossaryTerm('${escapeHtml(item.term)}', '${escapeHtml(item.meaning_en)}')">
                    🔊 ${state.currentLang === 'te' ? 'వినండి' : 'Listen'}
                </button>
            </div>
        </div>
    `).join("");
}

function speakGlossaryTerm(term, meaning) {
    speakText(`${term}. ${meaning}`, "en-US");
}

// ==============================================================================
// 12. TEXT-TO-SPEECH (Elderly & Accessible Narration)
// ==============================================================================

function speakText(text, lang = "en-US") {
    if (!('speechSynthesis' in window)) {
        showToast("Text-to-speech is not supported in this browser.", "info");
        return;
    }

    window.speechSynthesis.cancel(); // Stop any active speech

    // Clean markdown symbols for cleaner narration
    const cleanText = text.replace(/[*#_•\n]/g, " ").slice(0, 350);

    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.lang = lang;
    utterance.rate = 0.95; // Slightly slower, clear pace for elderly listeners

    window.speechSynthesis.speak(utterance);
    showToast(lang.startsWith("te") ? "తెలుగులో చదువుతున్నాము..." : "Reading aloud...", "info");
}

function handleVoiceInput() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
        showToast("Speech recognition is not supported in this browser. Please type your question.", "info");
        return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = state.currentLang === "te" ? "te-IN" : "en-US";
    recognition.interimResults = false;

    showToast("Listening... Speak your question now.", "info");

    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        const input = document.getElementById("chatInputText");
        if (input) {
            input.value = transcript;
            showToast(`Heard: "${transcript}"`, "success");
        }
    };

    recognition.onerror = () => {
        showToast("Could not recognize voice. Please try typing.", "error");
    };

    recognition.start();
}

// ==============================================================================
// 13. SAMPLE DATA RESET (For CSE Student Demo)
// ==============================================================================

async function handleResetSampleData() {
    if (!confirm("Reset database to clean beginner sample appointments and medicines?")) {
        return;
    }

    try {
        const res = await fetch("/api/reset-sample-data", { method: "POST" });
        const data = await res.json();
        if (data.success) {
            showToast("Sample health data reloaded successfully!", "success");
            loadAppointments();
            loadMedicines();
            loadSavedReports();
        }
    } catch (err) {
        showToast("Error resetting sample data.", "error");
    }
}

// ==============================================================================
// 14. UTILITIES & TOAST NOTIFICATIONS
// ==============================================================================

function showToast(message, type = "info") {
    const container = document.getElementById("toastContainer");
    if (!container) return;

    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;

    let icon = "ℹ️";
    if (type === "success") icon = "✅";
    if (type === "error") icon = "⚠️";

    toast.innerHTML = `<span>${icon}</span> <span>${escapeHtml(message)}</span>`;
    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = "0";
        toast.style.transition = "opacity 0.3s";
        setTimeout(() => toast.remove(), 300);
    }, 3800);
}

function escapeHtml(str) {
    if (!str) return "";
    return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function formatFriendlyDate(dateStr) {
    if (!dateStr) return "";
    try {
        const d = new Date(dateStr);
        return d.toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' });
    } catch {
        return dateStr;
    }
}

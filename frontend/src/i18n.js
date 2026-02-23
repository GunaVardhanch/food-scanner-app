import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

const resources = {
    en: {
        translation: {
            app_title: "Smart Food Scanner",
            scan_now: "Scan Now",
            history: "Scan History",
            preferences: "Preferences",
            analytics: "Health Insights",
            scanning: "Scanning Label...",
            analyzing: "AI Analyzing...",
            risk_level: "Risk Level",
            health_score: "Health Score",
            flagged_additives: "Flagged Additives",
            nutrition_summary: "Nutrition Summary",
            healthy_alternative: "Healthy Alternative",
            pro_tip: "Pro Tip",
            vegan: "Vegan",
            no_sugar: "No Sugar",
            low_sodium: "Low Sodium",
            gluten_free: "Gluten Free",
            save_prefs: "Save Preferences",
            dashboard: "Dashboard",
            switch_language: "Switch Language"
        }
    },
    hi: {
        translation: {
            app_title: "स्मार्ट फूड स्कैनर",
            scan_now: "अभी स्कैन करें",
            history: "स्कैन इतिहास",
            preferences: "मेरी पसंद",
            analytics: "स्वास्थ्य अंतर्दृष्टि",
            scanning: "लेबल स्कैन हो रहा है...",
            analyzing: "AI विश्लेषण कर रहा है...",
            risk_level: "जोखिम स्तर",
            health_score: "स्वास्थ्य स्कोर",
            flagged_additives: "चिह्नित सुधारे (Additives)",
            nutrition_summary: "पोषण सारांश",
            healthy_alternative: "स्वस्थ विकल्प",
            pro_tip: "प्रो टिप",
            vegan: "शाकाहारी",
            no_sugar: "चीनी रहित",
            low_sodium: "कम सोडियम",
            gluten_free: "ग्लूटेन मुक्त",
            save_prefs: "पसंद सहेजें",
            dashboard: "डैशबोर्ड",
            switch_language: "भाषा बदलें"
        }
    },
    mr: {
        translation: {
            app_title: "स्मार्ट फूड स्कॅनर",
            scan_now: "आत्ता स्कॅन करा",
            history: "स्कॅन इतिहास",
            preferences: "माझी पसंती",
            analytics: "आरोग्य विषयक माहिती",
            scanning: "लेबल स्कॅन होत आहे...",
            analyzing: "AI विश्लेषण करत आहे...",
            risk_level: "धोका पातळी",
            health_score: "आरोग्य गुण",
            flagged_additives: "चिन्हांकित घटक",
            nutrition_summary: "पोषण सारांश",
            healthy_alternative: "आरोग्यदायी पर्याय",
            pro_tip: "प्रो टिप",
            vegan: "शाकाहारी",
            no_sugar: "साखर मुक्त",
            low_sodium: "कमी सोडियम",
            gluten_free: "ग्लूटेन मुक्त",
            save_prefs: "पसंती जतन करा",
            dashboard: "डॅशबोर्ड",
            switch_language: "भाषा बदला"
        }
    }
};

const isBrowser = typeof window !== 'undefined';

const i18nInstance = i18n;

if (isBrowser) {
    i18nInstance.use(LanguageDetector);
}

i18nInstance
    .use(initReactI18next)
    .init({

        resources,
        fallbackLng: "en",
        interpolation: {
            escapeValue: false
        }
    });

export default i18n;

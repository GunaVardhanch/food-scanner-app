"use client";
import { useState, useEffect } from 'react';
import { useLanguagePreference } from '@/lib/useTranslation';
import { supportedLanguages } from '@/lib/translations';

export default function LanguageSelector() {
  const { getLanguage, setLanguage } = useLanguagePreference();
  const [currentLanguage, setCurrentLanguage] = useState('en');
  const [isOpen, setIsOpen] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    const savedLanguage = getLanguage();
    setCurrentLanguage(savedLanguage);
  }, [getLanguage]);

  if (!mounted) {
    return null;
  }

  const handleLanguageChange = (lang) => {
    setCurrentLanguage(lang);
    setLanguage(lang);
    setIsOpen(false);
  };

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="px-3 py-2 bg-white border border-slate-200 rounded-lg text-sm font-medium text-slate-700 hover:bg-slate-50 transition-colors"
      >
        {supportedLanguages[currentLanguage]} 🌐
      </button>

      {isOpen && (
        <div className="absolute top-full right-0 mt-2 w-40 bg-white border border-slate-200 rounded-lg shadow-lg z-50">
          {Object.entries(supportedLanguages).map(([code, name]) => (
            <button
              key={code}
              onClick={() => handleLanguageChange(code)}
              className={`w-full text-left px-4 py-2 text-sm font-medium transition-colors ${
                code === currentLanguage
                  ? 'bg-accent text-slate-900'
                  : 'text-slate-700 hover:bg-slate-50'
              }`}
            >
              {name}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

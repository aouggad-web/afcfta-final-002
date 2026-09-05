import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

// Import translations
import frTranslations from './locales/fr.json';
import enTranslations from './locales/en.json';

i18n
  .use(initReactI18next)
  .init({
    resources: {
      fr: { translation: frTranslations },
      en: { translation: enTranslations }
    },
    lng: 'fr', // default language
    fallbackLng: 'fr',
    interpolation: {
      escapeValue: false // React already escapes
    },
    react: {
      useSuspense: false
    }
  });

export default i18n;

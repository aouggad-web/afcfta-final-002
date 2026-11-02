import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import { isRtl } from './lang';

// Import translations
import frTranslations from './locales/fr.json';
import enTranslations from './locales/en.json';
import arTranslations from './locales/ar.json';

// Langue et sens d'écriture du document : l'arabe bascule toute la page
// de droite à gauche (dir="rtl"), y compris les composants hors i18n.
const syncDocument = (lng) => {
  if (typeof document === 'undefined') return;
  document.documentElement.lang = lng;
  document.documentElement.dir = isRtl(lng) ? 'rtl' : 'ltr';
};
i18n.on('languageChanged', syncDocument);

i18n
  .use(initReactI18next)
  .init({
    resources: {
      fr: { translation: frTranslations },
      en: { translation: enTranslations },
      ar: { translation: arTranslations }
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

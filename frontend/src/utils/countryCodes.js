/**
 * Mapping centralisé des codes pays ISO pour l'Afrique
 * Standard: ISO 3166-1 (ISO3 comme référence principale)
 * 
 * Ce fichier centralise tous les codes pays utilisés dans l'application
 * pour assurer la cohérence des données.
 * 
 * Dernière mise à jour: Janvier 2025
 */

// =============================================================================
// MAPPING COMPLET DES 54 PAYS AFRICAINS
// =============================================================================

export const AFRICAN_COUNTRIES = {
  "DZA": { iso2: "DZ", name_fr: "Algérie", name_en: "Algeria", name_ar: "الجزائر", region: "North Africa", flag: "🇩🇿" },
  "AGO": { iso2: "AO", name_fr: "Angola", name_en: "Angola", name_ar: "أنغولا", region: "Southern Africa", flag: "🇦🇴" },
  "BEN": { iso2: "BJ", name_fr: "Bénin", name_en: "Benin", name_ar: "بنين", region: "West Africa", flag: "🇧🇯" },
  "BWA": { iso2: "BW", name_fr: "Botswana", name_en: "Botswana", name_ar: "بوتسوانا", region: "Southern Africa", flag: "🇧🇼" },
  "BFA": { iso2: "BF", name_fr: "Burkina Faso", name_en: "Burkina Faso", name_ar: "بوركينا فاسو", region: "West Africa", flag: "🇧🇫" },
  "BDI": { iso2: "BI", name_fr: "Burundi", name_en: "Burundi", name_ar: "بوروندي", region: "East Africa", flag: "🇧🇮" },
  "CPV": { iso2: "CV", name_fr: "Cap-Vert", name_en: "Cape Verde", name_ar: "الرأس الأخضر", region: "West Africa", flag: "🇨🇻" },
  "CMR": { iso2: "CM", name_fr: "Cameroun", name_en: "Cameroon", name_ar: "الكاميرون", region: "Central Africa", flag: "🇨🇲" },
  "CAF": { iso2: "CF", name_fr: "République Centrafricaine", name_en: "Central African Republic", name_ar: "جمهورية أفريقيا الوسطى", region: "Central Africa", flag: "🇨🇫" },
  "TCD": { iso2: "TD", name_fr: "Tchad", name_en: "Chad", name_ar: "تشاد", region: "Central Africa", flag: "🇹🇩" },
  "COM": { iso2: "KM", name_fr: "Comores", name_en: "Comoros", name_ar: "جزر القمر", region: "East Africa", flag: "🇰🇲" },
  "COG": { iso2: "CG", name_fr: "République du Congo", name_en: "Republic of the Congo", name_ar: "الكونغو", region: "Central Africa", flag: "🇨🇬" },
  "COD": { iso2: "CD", name_fr: "République Démocratique du Congo", name_en: "Democratic Republic of the Congo", name_ar: "جمهورية الكونغو الديمقراطية", region: "Central Africa", flag: "🇨🇩" },
  "CIV": { iso2: "CI", name_fr: "Côte d'Ivoire", name_en: "Ivory Coast", name_ar: "كوت ديفوار", region: "West Africa", flag: "🇨🇮" },
  "DJI": { iso2: "DJ", name_fr: "Djibouti", name_en: "Djibouti", name_ar: "جيبوتي", region: "East Africa", flag: "🇩🇯" },
  "EGY": { iso2: "EG", name_fr: "Égypte", name_en: "Egypt", name_ar: "مصر", region: "North Africa", flag: "🇪🇬" },
  "GNQ": { iso2: "GQ", name_fr: "Guinée Équatoriale", name_en: "Equatorial Guinea", name_ar: "غينيا الاستوائية", region: "Central Africa", flag: "🇬🇶" },
  "ERI": { iso2: "ER", name_fr: "Érythrée", name_en: "Eritrea", name_ar: "إريتريا", region: "East Africa", flag: "🇪🇷", zlecafSignatory: false, note: "Seul membre UA non signataire" },
  "SWZ": { iso2: "SZ", name_fr: "Eswatini", name_en: "Eswatini", name_ar: "إسواتيني", region: "Southern Africa", flag: "🇸🇿" },
  "ETH": { iso2: "ET", name_fr: "Éthiopie", name_en: "Ethiopia", name_ar: "إثيوبيا", region: "East Africa", flag: "🇪🇹" },
  "GAB": { iso2: "GA", name_fr: "Gabon", name_en: "Gabon", name_ar: "الغابون", region: "Central Africa", flag: "🇬🇦" },
  "GMB": { iso2: "GM", name_fr: "Gambie", name_en: "Gambia", name_ar: "غامبيا", region: "West Africa", flag: "🇬🇲" },
  "GHA": { iso2: "GH", name_fr: "Ghana", name_en: "Ghana", name_ar: "غانا", region: "West Africa", flag: "🇬🇭" },
  "GIN": { iso2: "GN", name_fr: "Guinée", name_en: "Guinea", name_ar: "غينيا", region: "West Africa", flag: "🇬🇳" },
  "GNB": { iso2: "GW", name_fr: "Guinée-Bissau", name_en: "Guinea-Bissau", name_ar: "غينيا بيساو", region: "West Africa", flag: "🇬🇼" },
  "KEN": { iso2: "KE", name_fr: "Kenya", name_en: "Kenya", name_ar: "كينيا", region: "East Africa", flag: "🇰🇪" },
  "LSO": { iso2: "LS", name_fr: "Lesotho", name_en: "Lesotho", name_ar: "ليسوتو", region: "Southern Africa", flag: "🇱🇸" },
  "LBR": { iso2: "LR", name_fr: "Libéria", name_en: "Liberia", name_ar: "ليبيريا", region: "West Africa", flag: "🇱🇷" },
  "LBY": { iso2: "LY", name_fr: "Libye", name_en: "Libya", name_ar: "ليبيا", region: "North Africa", flag: "🇱🇾" },
  "MDG": { iso2: "MG", name_fr: "Madagascar", name_en: "Madagascar", name_ar: "مدغشقر", region: "East Africa", flag: "🇲🇬" },
  "MWI": { iso2: "MW", name_fr: "Malawi", name_en: "Malawi", name_ar: "ملاوي", region: "Southern Africa", flag: "🇲🇼" },
  "MLI": { iso2: "ML", name_fr: "Mali", name_en: "Mali", name_ar: "مالي", region: "West Africa", flag: "🇲🇱" },
  "MRT": { iso2: "MR", name_fr: "Mauritanie", name_en: "Mauritania", name_ar: "موريتانيا", region: "West Africa", flag: "🇲🇷" },
  "MUS": { iso2: "MU", name_fr: "Maurice", name_en: "Mauritius", name_ar: "موريشيوس", region: "East Africa", flag: "🇲🇺" },
  "MAR": { iso2: "MA", name_fr: "Maroc", name_en: "Morocco", name_ar: "المغرب", region: "North Africa", flag: "🇲🇦" },
  "MOZ": { iso2: "MZ", name_fr: "Mozambique", name_en: "Mozambique", name_ar: "موزمبيق", region: "Southern Africa", flag: "🇲🇿" },
  "NAM": { iso2: "NA", name_fr: "Namibie", name_en: "Namibia", name_ar: "ناميبيا", region: "Southern Africa", flag: "🇳🇦" },
  "NER": { iso2: "NE", name_fr: "Niger", name_en: "Niger", name_ar: "النيجر", region: "West Africa", flag: "🇳🇪" },
  "NGA": { iso2: "NG", name_fr: "Nigéria", name_en: "Nigeria", name_ar: "نيجيريا", region: "West Africa", flag: "🇳🇬" },
  "RWA": { iso2: "RW", name_fr: "Rwanda", name_en: "Rwanda", name_ar: "رواندا", region: "East Africa", flag: "🇷🇼" },
  // RASD - République Arabe Sahraouie Démocratique (Sahara Occidental)
  // Membre fondateur de l'Union Africaine - Signataire de la ZLECAf
  // ATTENTION: Pas de données commerciales disponibles
  "ESH": { iso2: "EH", name_fr: "RASD (Sahara Occidental)", name_en: "Sahrawi Arab Democratic Republic", name_ar: "الجمهورية العربية الصحراوية الديمقراطية", region: "North Africa", flag: "🇪🇭", hasTradeData: false, note: "Membre UA - Pas de statistiques commerciales" },
  "STP": { iso2: "ST", name_fr: "São Tomé-et-Príncipe", name_en: "São Tomé and Príncipe", name_ar: "ساو تومي وبرينسيب", region: "Central Africa", flag: "🇸🇹" },
  "SEN": { iso2: "SN", name_fr: "Sénégal", name_en: "Senegal", name_ar: "السنغال", region: "West Africa", flag: "🇸🇳" },
  "SYC": { iso2: "SC", name_fr: "Seychelles", name_en: "Seychelles", name_ar: "سيشل", region: "East Africa", flag: "🇸🇨" },
  "SLE": { iso2: "SL", name_fr: "Sierra Leone", name_en: "Sierra Leone", name_ar: "سيراليون", region: "West Africa", flag: "🇸🇱" },
  "SOM": { iso2: "SO", name_fr: "Somalie", name_en: "Somalia", name_ar: "الصومال", region: "East Africa", flag: "🇸🇴" },
  "ZAF": { iso2: "ZA", name_fr: "Afrique du Sud", name_en: "South Africa", name_ar: "جنوب أفريقيا", region: "Southern Africa", flag: "🇿🇦" },
  "SSD": { iso2: "SS", name_fr: "Soudan du Sud", name_en: "South Sudan", name_ar: "جنوب السودان", region: "East Africa", flag: "🇸🇸" },
  "SDN": { iso2: "SD", name_fr: "Soudan", name_en: "Sudan", name_ar: "السودان", region: "North Africa", flag: "🇸🇩" },
  "TZA": { iso2: "TZ", name_fr: "Tanzanie", name_en: "Tanzania", name_ar: "تنزانيا", region: "East Africa", flag: "🇹🇿" },
  "TGO": { iso2: "TG", name_fr: "Togo", name_en: "Togo", name_ar: "توغو", region: "West Africa", flag: "🇹🇬" },
  "TUN": { iso2: "TN", name_fr: "Tunisie", name_en: "Tunisia", name_ar: "تونس", region: "North Africa", flag: "🇹🇳" },
  "UGA": { iso2: "UG", name_fr: "Ouganda", name_en: "Uganda", name_ar: "أوغندا", region: "East Africa", flag: "🇺🇬" },
  "ZMB": { iso2: "ZM", name_fr: "Zambie", name_en: "Zambia", name_ar: "زامبيا", region: "Southern Africa", flag: "🇿🇲" },
  "ZWE": { iso2: "ZW", name_fr: "Zimbabwe", name_en: "Zimbabwe", name_ar: "زيمبابوي", region: "Southern Africa", flag: "🇿🇼" },
};

// =============================================================================
// MAPPINGS INVERSÉS POUR CONVERSIONS RAPIDES
// =============================================================================

// ISO2 -> ISO3
export const ISO2_TO_ISO3 = Object.fromEntries(
  Object.entries(AFRICAN_COUNTRIES).map(([iso3, info]) => [info.iso2, iso3])
);

// ISO3 -> ISO2
export const ISO3_TO_ISO2 = Object.fromEntries(
  Object.entries(AFRICAN_COUNTRIES).map(([iso3, info]) => [iso3, info.iso2])
);

// =============================================================================
// FONCTIONS UTILITAIRES
// =============================================================================

/**
 * Obtient le drapeau emoji pour un code pays (supporte ISO2 et ISO3)
 */
export const getCountryFlag = (code) => {
  if (!code) return '🌍';
  const upperCode = code.toUpperCase();
  
  // Si ISO3
  if (AFRICAN_COUNTRIES[upperCode]) {
    return AFRICAN_COUNTRIES[upperCode].flag;
  }
  
  // Si ISO2, convertir en ISO3
  const iso3 = ISO2_TO_ISO3[upperCode];
  if (iso3 && AFRICAN_COUNTRIES[iso3]) {
    return AFRICAN_COUNTRIES[iso3].flag;
  }
  
  return '🌍';
};

/**
 * Convertit un code ISO2 en ISO3
 */
export const getISO3FromISO2 = (iso2) => {
  return ISO2_TO_ISO3[iso2?.toUpperCase()] || null;
};

/**
 * Convertit un code ISO3 en ISO2
 */
export const getISO2FromISO3 = (iso3) => {
  return ISO3_TO_ISO2[iso3?.toUpperCase()] || null;
};

/**
 * Obtient les informations complètes d'un pays (supporte ISO2 et ISO3)
 */
export const getCountryInfo = (code) => {
  if (!code) return null;
  const upperCode = code.toUpperCase();
  
  // Si ISO3
  if (AFRICAN_COUNTRIES[upperCode]) {
    return { iso3: upperCode, ...AFRICAN_COUNTRIES[upperCode] };
  }
  
  // Si ISO2
  const iso3 = ISO2_TO_ISO3[upperCode];
  if (iso3) {
    return { iso3, ...AFRICAN_COUNTRIES[iso3] };
  }
  
  return null;
};

/**
 * Obtient la liste de tous les pays africains triés
 */
export const getAllCountries = (lang = 'fr') => {
  const nameKey = `name_${lang}`;
  return Object.entries(AFRICAN_COUNTRIES)
    .map(([iso3, info]) => ({
      iso3,
      iso2: info.iso2,
      name: info[nameKey] || info.name_en,
      ...info
    }))
    .sort((a, b) => a.name.localeCompare(b.name));
};

/**
 * Obtient les pays d'une région spécifique
 */
export const getCountriesByRegion = (region, lang = 'fr') => {
  return getAllCountries(lang).filter(c => c.region === region);
};

// =============================================================================
// RÉGIONS ÉCONOMIQUES
// =============================================================================

export const ECONOMIC_COMMUNITIES = {
  UEMOA: ["BEN", "BFA", "CIV", "GNB", "MLI", "NER", "SEN", "TGO"],
  CEMAC: ["CMR", "CAF", "TCD", "COG", "GNQ", "GAB"],
  CEDEAO: ["BEN", "BFA", "CPV", "CIV", "GMB", "GHA", "GIN", "GNB", "LBR", "MLI", "NER", "NGA", "SEN", "SLE", "TGO"],
  EAC: ["BDI", "COD", "KEN", "RWA", "SSD", "TZA", "UGA"],
  SACU: ["BWA", "LSO", "NAM", "ZAF", "SWZ"],
  SADC: ["AGO", "BWA", "COM", "COD", "SWZ", "LSO", "MDG", "MWI", "MUS", "MOZ", "NAM", "SYC", "ZAF", "TZA", "ZMB", "ZWE"],
};

export default AFRICAN_COUNTRIES;

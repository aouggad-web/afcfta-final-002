// Centralized translations for country names and regions
// This file provides bilingual support (FR/EN) for all African countries

export const COUNTRY_NAMES = {
  // ISO Alpha-3 codes
  'DZA': { fr: 'Algérie', en: 'Algeria' },
  'AGO': { fr: 'Angola', en: 'Angola' },
  'BEN': { fr: 'Bénin', en: 'Benin' },
  'BWA': { fr: 'Botswana', en: 'Botswana' },
  'BFA': { fr: 'Burkina Faso', en: 'Burkina Faso' },
  'BDI': { fr: 'Burundi', en: 'Burundi' },
  'CMR': { fr: 'Cameroun', en: 'Cameroon' },
  'CPV': { fr: 'Cap-Vert', en: 'Cape Verde' },
  'CAF': { fr: 'Rép. Centrafricaine', en: 'Central African Rep.' },
  'TCD': { fr: 'Tchad', en: 'Chad' },
  'COM': { fr: 'Comores', en: 'Comoros' },
  'COG': { fr: 'Congo', en: 'Congo' },
  'COD': { fr: 'RD Congo', en: 'DR Congo' },
  'CIV': { fr: "Côte d'Ivoire", en: 'Ivory Coast' },
  'DJI': { fr: 'Djibouti', en: 'Djibouti' },
  'EGY': { fr: 'Égypte', en: 'Egypt' },
  'GNQ': { fr: 'Guinée Équatoriale', en: 'Equatorial Guinea' },
  'ERI': { fr: 'Érythrée', en: 'Eritrea' },
  'SWZ': { fr: 'Eswatini', en: 'Eswatini' },
  'ETH': { fr: 'Éthiopie', en: 'Ethiopia' },
  'GAB': { fr: 'Gabon', en: 'Gabon' },
  'GMB': { fr: 'Gambie', en: 'Gambia' },
  'GHA': { fr: 'Ghana', en: 'Ghana' },
  'GIN': { fr: 'Guinée', en: 'Guinea' },
  'GNB': { fr: 'Guinée-Bissau', en: 'Guinea-Bissau' },
  'KEN': { fr: 'Kenya', en: 'Kenya' },
  'LSO': { fr: 'Lesotho', en: 'Lesotho' },
  'LBR': { fr: 'Libéria', en: 'Liberia' },
  'LBY': { fr: 'Libye', en: 'Libya' },
  'MDG': { fr: 'Madagascar', en: 'Madagascar' },
  'MWI': { fr: 'Malawi', en: 'Malawi' },
  'MLI': { fr: 'Mali', en: 'Mali' },
  'MRT': { fr: 'Mauritanie', en: 'Mauritania' },
  'MUS': { fr: 'Maurice', en: 'Mauritius' },
  'MAR': { fr: 'Maroc', en: 'Morocco' },
  'MOZ': { fr: 'Mozambique', en: 'Mozambique' },
  'NAM': { fr: 'Namibie', en: 'Namibia' },
  'NER': { fr: 'Niger', en: 'Niger' },
  'NGA': { fr: 'Nigéria', en: 'Nigeria' },
  'RWA': { fr: 'Rwanda', en: 'Rwanda' },
  // RASD - République Arabe Sahraouie Démocratique
  'ESH': { fr: 'RASD (Sahara Occ.)', en: 'SADR (Western Sahara)', hasTradeData: false },
  'STP': { fr: 'São Tomé', en: 'São Tomé' },
  'SEN': { fr: 'Sénégal', en: 'Senegal' },
  'SYC': { fr: 'Seychelles', en: 'Seychelles' },
  'SLE': { fr: 'Sierra Leone', en: 'Sierra Leone' },
  'SOM': { fr: 'Somalie', en: 'Somalia' },
  'ZAF': { fr: 'Afrique du Sud', en: 'South Africa' },
  'SSD': { fr: 'Soudan du Sud', en: 'South Sudan' },
  'SDN': { fr: 'Soudan', en: 'Sudan' },
  'TZA': { fr: 'Tanzanie', en: 'Tanzania' },
  'TGO': { fr: 'Togo', en: 'Togo' },
  'TUN': { fr: 'Tunisie', en: 'Tunisia' },
  'UGA': { fr: 'Ouganda', en: 'Uganda' },
  'ZMB': { fr: 'Zambie', en: 'Zambia' },
  'ZWE': { fr: 'Zimbabwe', en: 'Zimbabwe' },
  // ISO Alpha-2 codes (for compatibility)
  'DZ': { fr: 'Algérie', en: 'Algeria' },
  'AO': { fr: 'Angola', en: 'Angola' },
  'BJ': { fr: 'Bénin', en: 'Benin' },
  'BW': { fr: 'Botswana', en: 'Botswana' },
  'BF': { fr: 'Burkina Faso', en: 'Burkina Faso' },
  'BI': { fr: 'Burundi', en: 'Burundi' },
  'CM': { fr: 'Cameroun', en: 'Cameroon' },
  'CV': { fr: 'Cap-Vert', en: 'Cape Verde' },
  'CF': { fr: 'Rép. Centrafricaine', en: 'Central African Rep.' },
  'TD': { fr: 'Tchad', en: 'Chad' },
  'KM': { fr: 'Comores', en: 'Comoros' },
  'CG': { fr: 'Congo', en: 'Congo' },
  'CD': { fr: 'RD Congo', en: 'DR Congo' },
  'CI': { fr: "Côte d'Ivoire", en: 'Ivory Coast' },
  'DJ': { fr: 'Djibouti', en: 'Djibouti' },
  'EG': { fr: 'Égypte', en: 'Egypt' },
  'GQ': { fr: 'Guinée Équatoriale', en: 'Equatorial Guinea' },
  'ER': { fr: 'Érythrée', en: 'Eritrea' },
  'SZ': { fr: 'Eswatini', en: 'Eswatini' },
  'ET': { fr: 'Éthiopie', en: 'Ethiopia' },
  'GA': { fr: 'Gabon', en: 'Gabon' },
  'GM': { fr: 'Gambie', en: 'Gambia' },
  'GH': { fr: 'Ghana', en: 'Ghana' },
  'GN': { fr: 'Guinée', en: 'Guinea' },
  'GW': { fr: 'Guinée-Bissau', en: 'Guinea-Bissau' },
  'KE': { fr: 'Kenya', en: 'Kenya' },
  'LS': { fr: 'Lesotho', en: 'Lesotho' },
  'LR': { fr: 'Libéria', en: 'Liberia' },
  'LY': { fr: 'Libye', en: 'Libya' },
  'MG': { fr: 'Madagascar', en: 'Madagascar' },
  'MW': { fr: 'Malawi', en: 'Malawi' },
  'ML': { fr: 'Mali', en: 'Mali' },
  'MR': { fr: 'Mauritanie', en: 'Mauritania' },
  'MU': { fr: 'Maurice', en: 'Mauritius' },
  'MA': { fr: 'Maroc', en: 'Morocco' },
  'MZ': { fr: 'Mozambique', en: 'Mozambique' },
  'NA': { fr: 'Namibie', en: 'Namibia' },
  'NE': { fr: 'Niger', en: 'Niger' },
  'NG': { fr: 'Nigéria', en: 'Nigeria' },
  'RW': { fr: 'Rwanda', en: 'Rwanda' },
  'ST': { fr: 'São Tomé', en: 'São Tomé' },
  'SN': { fr: 'Sénégal', en: 'Senegal' },
  'SC': { fr: 'Seychelles', en: 'Seychelles' },
  'SL': { fr: 'Sierra Leone', en: 'Sierra Leone' },
  'SO': { fr: 'Somalie', en: 'Somalia' },
  'ZA': { fr: 'Afrique du Sud', en: 'South Africa' },
  'SS': { fr: 'Soudan du Sud', en: 'South Sudan' },
  'SD': { fr: 'Soudan', en: 'Sudan' },
  'TZ': { fr: 'Tanzanie', en: 'Tanzania' },
  'TG': { fr: 'Togo', en: 'Togo' },
  'TN': { fr: 'Tunisie', en: 'Tunisia' },
  'UG': { fr: 'Ouganda', en: 'Uganda' },
  'ZM': { fr: 'Zambie', en: 'Zambia' },
  'ZW': { fr: 'Zimbabwe', en: 'Zimbabwe' },
};

export const REGION_NAMES = {
  "Afrique du Nord": { fr: "Afrique du Nord", en: "North Africa" },
  "Afrique de l'Ouest": { fr: "Afrique de l'Ouest", en: "West Africa" },
  "Afrique Centrale": { fr: "Afrique Centrale", en: "Central Africa" },
  "Afrique de l'Est": { fr: "Afrique de l'Est", en: "East Africa" },
  "Afrique Australe": { fr: "Afrique Australe", en: "Southern Africa" },
  // English keys for reverse lookup
  "North Africa": { fr: "Afrique du Nord", en: "North Africa" },
  "West Africa": { fr: "Afrique de l'Ouest", en: "West Africa" },
  "Central Africa": { fr: "Afrique Centrale", en: "Central Africa" },
  "East Africa": { fr: "Afrique de l'Est", en: "East Africa" },
  "Southern Africa": { fr: "Afrique Australe", en: "Southern Africa" },
};

// Helper functions
export const getCountryName = (code, language = 'fr') => {
  if (!code) return '';
  const upperCode = code.toUpperCase();
  if (COUNTRY_NAMES[upperCode]) {
    return COUNTRY_NAMES[upperCode][language] || COUNTRY_NAMES[upperCode].fr;
  }
  return code;
};

export const getRegionName = (region, language = 'fr') => {
  if (!region) return '';
  if (REGION_NAMES[region]) {
    return REGION_NAMES[region][language] || REGION_NAMES[region].fr;
  }
  return region;
};

// Get countries organized by region with translations
export const getCountriesByRegion = (language = 'fr') => {
  const regions = {
    [getRegionName("Afrique du Nord", language)]: [
      { code: 'DZA', name: getCountryName('DZA', language), flag: '🇩🇿' },
      { code: 'EGY', name: getCountryName('EGY', language), flag: '🇪🇬' },
      { code: 'LBY', name: getCountryName('LBY', language), flag: '🇱🇾' },
      { code: 'MAR', name: getCountryName('MAR', language), flag: '🇲🇦' },
      { code: 'TUN', name: getCountryName('TUN', language), flag: '🇹🇳' },
    ],
    [getRegionName("Afrique de l'Ouest", language)]: [
      { code: 'BEN', name: getCountryName('BEN', language), flag: '🇧🇯' },
      { code: 'BFA', name: getCountryName('BFA', language), flag: '🇧🇫' },
      { code: 'CPV', name: getCountryName('CPV', language), flag: '🇨🇻' },
      { code: 'CIV', name: getCountryName('CIV', language), flag: '🇨🇮' },
      { code: 'GMB', name: getCountryName('GMB', language), flag: '🇬🇲' },
      { code: 'GHA', name: getCountryName('GHA', language), flag: '🇬🇭' },
      { code: 'GIN', name: getCountryName('GIN', language), flag: '🇬🇳' },
      { code: 'GNB', name: getCountryName('GNB', language), flag: '🇬🇼' },
      { code: 'LBR', name: getCountryName('LBR', language), flag: '🇱🇷' },
      { code: 'MLI', name: getCountryName('MLI', language), flag: '🇲🇱' },
      { code: 'MRT', name: getCountryName('MRT', language), flag: '🇲🇷' },
      { code: 'NER', name: getCountryName('NER', language), flag: '🇳🇪' },
      { code: 'NGA', name: getCountryName('NGA', language), flag: '🇳🇬' },
      { code: 'SEN', name: getCountryName('SEN', language), flag: '🇸🇳' },
      { code: 'SLE', name: getCountryName('SLE', language), flag: '🇸🇱' },
      { code: 'TGO', name: getCountryName('TGO', language), flag: '🇹🇬' },
    ],
    [getRegionName("Afrique Centrale", language)]: [
      { code: 'AGO', name: getCountryName('AGO', language), flag: '🇦🇴' },
      { code: 'CMR', name: getCountryName('CMR', language), flag: '🇨🇲' },
      { code: 'CAF', name: getCountryName('CAF', language), flag: '🇨🇫' },
      { code: 'TCD', name: getCountryName('TCD', language), flag: '🇹🇩' },
      { code: 'COG', name: getCountryName('COG', language), flag: '🇨🇬' },
      { code: 'COD', name: getCountryName('COD', language), flag: '🇨🇩' },
      { code: 'GNQ', name: getCountryName('GNQ', language), flag: '🇬🇶' },
      { code: 'GAB', name: getCountryName('GAB', language), flag: '🇬🇦' },
      { code: 'STP', name: getCountryName('STP', language), flag: '🇸🇹' },
    ],
    [getRegionName("Afrique de l'Est", language)]: [
      { code: 'BDI', name: getCountryName('BDI', language), flag: '🇧🇮' },
      { code: 'COM', name: getCountryName('COM', language), flag: '🇰🇲' },
      { code: 'DJI', name: getCountryName('DJI', language), flag: '🇩🇯' },
      { code: 'ERI', name: getCountryName('ERI', language), flag: '🇪🇷' },
      { code: 'ETH', name: getCountryName('ETH', language), flag: '🇪🇹' },
      { code: 'KEN', name: getCountryName('KEN', language), flag: '🇰🇪' },
      { code: 'MDG', name: getCountryName('MDG', language), flag: '🇲🇬' },
      { code: 'MWI', name: getCountryName('MWI', language), flag: '🇲🇼' },
      { code: 'MUS', name: getCountryName('MUS', language), flag: '🇲🇺' },
      { code: 'MOZ', name: getCountryName('MOZ', language), flag: '🇲🇿' },
      { code: 'RWA', name: getCountryName('RWA', language), flag: '🇷🇼' },
      { code: 'SYC', name: getCountryName('SYC', language), flag: '🇸🇨' },
      { code: 'SOM', name: getCountryName('SOM', language), flag: '🇸🇴' },
      { code: 'SSD', name: getCountryName('SSD', language), flag: '🇸🇸' },
      { code: 'SDN', name: getCountryName('SDN', language), flag: '🇸🇩' },
      { code: 'TZA', name: getCountryName('TZA', language), flag: '🇹🇿' },
      { code: 'UGA', name: getCountryName('UGA', language), flag: '🇺🇬' },
    ],
    [getRegionName("Afrique Australe", language)]: [
      { code: 'BWA', name: getCountryName('BWA', language), flag: '🇧🇼' },
      { code: 'LSO', name: getCountryName('LSO', language), flag: '🇱🇸' },
      { code: 'NAM', name: getCountryName('NAM', language), flag: '🇳🇦' },
      { code: 'ZAF', name: getCountryName('ZAF', language), flag: '🇿🇦' },
      { code: 'SWZ', name: getCountryName('SWZ', language), flag: '🇸🇿' },
      { code: 'ZMB', name: getCountryName('ZMB', language), flag: '🇿🇲' },
      { code: 'ZWE', name: getCountryName('ZWE', language), flag: '🇿🇼' },
    ],
  };
  return regions;
};

// Get flat list of all countries with translations
export const getAllCountries = (language = 'fr') => {
  const countries = [];
  const regions = getCountriesByRegion(language);
  Object.values(regions).forEach(regionCountries => {
    countries.push(...regionCountries);
  });
  return countries;
};

export default {
  COUNTRY_NAMES,
  REGION_NAMES,
  getCountryName,
  getRegionName,
  getCountriesByRegion,
  getAllCountries,
};

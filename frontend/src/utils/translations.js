// Centralized translations for country names and regions
// This file provides bilingual support (FR/EN) for all African countries

export const COUNTRY_NAMES = {
  // ISO Alpha-3 codes
  'DZA': { fr: 'Algérie', en: 'Algeria', ar: 'الجزائر' },
  'AGO': { fr: 'Angola', en: 'Angola', ar: 'أنغولا' },
  'BEN': { fr: 'Bénin', en: 'Benin', ar: 'بنين' },
  'BWA': { fr: 'Botswana', en: 'Botswana', ar: 'بوتسوانا' },
  'BFA': { fr: 'Burkina Faso', en: 'Burkina Faso', ar: 'بوركينا فاسو' },
  'BDI': { fr: 'Burundi', en: 'Burundi', ar: 'بوروندي' },
  'CMR': { fr: 'Cameroun', en: 'Cameroon', ar: 'الكاميرون' },
  'CPV': { fr: 'Cap-Vert', en: 'Cape Verde', ar: 'الرأس الأخضر' },
  'CAF': { fr: 'Rép. Centrafricaine', en: 'Central African Rep.', ar: 'جمهورية أفريقيا الوسطى' },
  'TCD': { fr: 'Tchad', en: 'Chad', ar: 'تشاد' },
  'COM': { fr: 'Comores', en: 'Comoros', ar: 'جزر القمر' },
  'COG': { fr: 'Congo', en: 'Congo', ar: 'الكونغو' },
  'COD': { fr: 'RD Congo', en: 'DR Congo', ar: 'جمهورية الكونغو الديمقراطية' },
  'CIV': { fr: "Côte d'Ivoire", en: 'Ivory Coast', ar: 'كوت ديفوار' },
  'DJI': { fr: 'Djibouti', en: 'Djibouti', ar: 'جيبوتي' },
  'EGY': { fr: 'Égypte', en: 'Egypt', ar: 'مصر' },
  'GNQ': { fr: 'Guinée Équatoriale', en: 'Equatorial Guinea', ar: 'غينيا الاستوائية' },
  'ERI': { fr: 'Érythrée', en: 'Eritrea', ar: 'إريتريا', zlecafSignatory: false },
  'SWZ': { fr: 'Eswatini', en: 'Eswatini', ar: 'إسواتيني' },
  'ETH': { fr: 'Éthiopie', en: 'Ethiopia', ar: 'إثيوبيا' },
  'GAB': { fr: 'Gabon', en: 'Gabon', ar: 'الغابون' },
  'GMB': { fr: 'Gambie', en: 'Gambia', ar: 'غامبيا' },
  'GHA': { fr: 'Ghana', en: 'Ghana', ar: 'غانا' },
  'GIN': { fr: 'Guinée', en: 'Guinea', ar: 'غينيا' },
  'GNB': { fr: 'Guinée-Bissau', en: 'Guinea-Bissau', ar: 'غينيا بيساو' },
  'KEN': { fr: 'Kenya', en: 'Kenya', ar: 'كينيا' },
  'LSO': { fr: 'Lesotho', en: 'Lesotho', ar: 'ليسوتو' },
  'LBR': { fr: 'Libéria', en: 'Liberia', ar: 'ليبيريا' },
  'LBY': { fr: 'Libye', en: 'Libya', ar: 'ليبيا' },
  'MDG': { fr: 'Madagascar', en: 'Madagascar', ar: 'مدغشقر' },
  'MWI': { fr: 'Malawi', en: 'Malawi', ar: 'ملاوي' },
  'MLI': { fr: 'Mali', en: 'Mali', ar: 'مالي' },
  'MRT': { fr: 'Mauritanie', en: 'Mauritania', ar: 'موريتانيا' },
  'MUS': { fr: 'Maurice', en: 'Mauritius', ar: 'موريشيوس' },
  'MAR': { fr: 'Maroc', en: 'Morocco', ar: 'المغرب' },
  'MOZ': { fr: 'Mozambique', en: 'Mozambique', ar: 'موزمبيق' },
  'NAM': { fr: 'Namibie', en: 'Namibia', ar: 'ناميبيا' },
  'NER': { fr: 'Niger', en: 'Niger', ar: 'النيجر' },
  'NGA': { fr: 'Nigéria', en: 'Nigeria', ar: 'نيجيريا' },
  'RWA': { fr: 'Rwanda', en: 'Rwanda', ar: 'رواندا' },
  // RASD - République Arabe Sahraouie Démocratique
  'ESH': { fr: 'RASD (Sahara Occ.)', en: 'SADR (Western Sahara)', ar: 'الجمهورية الصحراوية', hasTradeData: false },
  'STP': { fr: 'São Tomé', en: 'São Tomé', ar: 'ساو تومي وبرينسيب' },
  'SEN': { fr: 'Sénégal', en: 'Senegal', ar: 'السنغال' },
  'SYC': { fr: 'Seychelles', en: 'Seychelles', ar: 'سيشل' },
  'SLE': { fr: 'Sierra Leone', en: 'Sierra Leone', ar: 'سيراليون' },
  'SOM': { fr: 'Somalie', en: 'Somalia', ar: 'الصومال' },
  'ZAF': { fr: 'Afrique du Sud', en: 'South Africa', ar: 'جنوب أفريقيا' },
  'SSD': { fr: 'Soudan du Sud', en: 'South Sudan', ar: 'جنوب السودان' },
  'SDN': { fr: 'Soudan', en: 'Sudan', ar: 'السودان' },
  'TZA': { fr: 'Tanzanie', en: 'Tanzania', ar: 'تنزانيا' },
  'TGO': { fr: 'Togo', en: 'Togo', ar: 'توغو' },
  'TUN': { fr: 'Tunisie', en: 'Tunisia', ar: 'تونس' },
  'UGA': { fr: 'Ouganda', en: 'Uganda', ar: 'أوغندا' },
  'ZMB': { fr: 'Zambie', en: 'Zambia', ar: 'زامبيا' },
  'ZWE': { fr: 'Zimbabwe', en: 'Zimbabwe', ar: 'زيمبابوي' },
  // ISO Alpha-2 codes (for compatibility)
  'DZ': { fr: 'Algérie', en: 'Algeria', ar: 'الجزائر' },
  'AO': { fr: 'Angola', en: 'Angola', ar: 'أنغولا' },
  'BJ': { fr: 'Bénin', en: 'Benin', ar: 'بنين' },
  'BW': { fr: 'Botswana', en: 'Botswana', ar: 'بوتسوانا' },
  'BF': { fr: 'Burkina Faso', en: 'Burkina Faso', ar: 'بوركينا فاسو' },
  'BI': { fr: 'Burundi', en: 'Burundi', ar: 'بوروندي' },
  'CM': { fr: 'Cameroun', en: 'Cameroon', ar: 'الكاميرون' },
  'CV': { fr: 'Cap-Vert', en: 'Cape Verde', ar: 'الرأس الأخضر' },
  'CF': { fr: 'Rép. Centrafricaine', en: 'Central African Rep.', ar: 'جمهورية أفريقيا الوسطى' },
  'TD': { fr: 'Tchad', en: 'Chad', ar: 'تشاد' },
  'KM': { fr: 'Comores', en: 'Comoros', ar: 'جزر القمر' },
  'CG': { fr: 'Congo', en: 'Congo', ar: 'الكونغو' },
  'CD': { fr: 'RD Congo', en: 'DR Congo', ar: 'جمهورية الكونغو الديمقراطية' },
  'CI': { fr: "Côte d'Ivoire", en: 'Ivory Coast', ar: 'كوت ديفوار' },
  'DJ': { fr: 'Djibouti', en: 'Djibouti', ar: 'جيبوتي' },
  'EG': { fr: 'Égypte', en: 'Egypt', ar: 'مصر' },
  'GQ': { fr: 'Guinée Équatoriale', en: 'Equatorial Guinea', ar: 'غينيا الاستوائية' },
  'ER': { fr: 'Érythrée', en: 'Eritrea', ar: 'إريتريا' },
  'SZ': { fr: 'Eswatini', en: 'Eswatini', ar: 'إسواتيني' },
  'ET': { fr: 'Éthiopie', en: 'Ethiopia', ar: 'إثيوبيا' },
  'GA': { fr: 'Gabon', en: 'Gabon', ar: 'الغابون' },
  'GM': { fr: 'Gambie', en: 'Gambia', ar: 'غامبيا' },
  'GH': { fr: 'Ghana', en: 'Ghana', ar: 'غانا' },
  'GN': { fr: 'Guinée', en: 'Guinea', ar: 'غينيا' },
  'GW': { fr: 'Guinée-Bissau', en: 'Guinea-Bissau', ar: 'غينيا بيساو' },
  'KE': { fr: 'Kenya', en: 'Kenya', ar: 'كينيا' },
  'LS': { fr: 'Lesotho', en: 'Lesotho', ar: 'ليسوتو' },
  'LR': { fr: 'Libéria', en: 'Liberia', ar: 'ليبيريا' },
  'LY': { fr: 'Libye', en: 'Libya', ar: 'ليبيا' },
  'MG': { fr: 'Madagascar', en: 'Madagascar', ar: 'مدغشقر' },
  'MW': { fr: 'Malawi', en: 'Malawi', ar: 'ملاوي' },
  'ML': { fr: 'Mali', en: 'Mali', ar: 'مالي' },
  'MR': { fr: 'Mauritanie', en: 'Mauritania', ar: 'موريتانيا' },
  'MU': { fr: 'Maurice', en: 'Mauritius', ar: 'موريشيوس' },
  'MA': { fr: 'Maroc', en: 'Morocco', ar: 'المغرب' },
  'MZ': { fr: 'Mozambique', en: 'Mozambique', ar: 'موزمبيق' },
  'NA': { fr: 'Namibie', en: 'Namibia', ar: 'ناميبيا' },
  'NE': { fr: 'Niger', en: 'Niger', ar: 'النيجر' },
  'NG': { fr: 'Nigéria', en: 'Nigeria', ar: 'نيجيريا' },
  'RW': { fr: 'Rwanda', en: 'Rwanda', ar: 'رواندا' },
  // RASD ISO2
  'EH': { fr: 'RASD (Sahara Occ.)', en: 'SADR (Western Sahara)', ar: 'الجمهورية الصحراوية', hasTradeData: false },
  'ST': { fr: 'São Tomé', en: 'São Tomé', ar: 'ساو تومي وبرينسيب' },
  'SN': { fr: 'Sénégal', en: 'Senegal', ar: 'السنغال' },
  'SC': { fr: 'Seychelles', en: 'Seychelles', ar: 'سيشل' },
  'SL': { fr: 'Sierra Leone', en: 'Sierra Leone', ar: 'سيراليون' },
  'SO': { fr: 'Somalie', en: 'Somalia', ar: 'الصومال' },
  'ZA': { fr: 'Afrique du Sud', en: 'South Africa', ar: 'جنوب أفريقيا' },
  'SS': { fr: 'Soudan du Sud', en: 'South Sudan', ar: 'جنوب السودان' },
  'SD': { fr: 'Soudan', en: 'Sudan', ar: 'السودان' },
  'TZ': { fr: 'Tanzanie', en: 'Tanzania', ar: 'تنزانيا' },
  'TG': { fr: 'Togo', en: 'Togo', ar: 'توغو' },
  'TN': { fr: 'Tunisie', en: 'Tunisia', ar: 'تونس' },
  'UG': { fr: 'Ouganda', en: 'Uganda', ar: 'أوغندا' },
  'ZM': { fr: 'Zambie', en: 'Zambia', ar: 'زامبيا' },
  'ZW': { fr: 'Zimbabwe', en: 'Zimbabwe', ar: 'زيمبابوي' },
};

export const REGION_NAMES = {
  "Afrique du Nord": { fr: "Afrique du Nord", en: "North Africa", ar: "شمال أفريقيا" },
  "Afrique de l'Ouest": { fr: "Afrique de l'Ouest", en: "West Africa", ar: "غرب أفريقيا" },
  "Afrique Centrale": { fr: "Afrique Centrale", en: "Central Africa", ar: "وسط أفريقيا" },
  "Afrique de l'Est": { fr: "Afrique de l'Est", en: "East Africa", ar: "شرق أفريقيا" },
  "Afrique Australe": { fr: "Afrique Australe", en: "Southern Africa", ar: "الجنوب الأفريقي" },
  // English keys for reverse lookup
  "North Africa": { fr: "Afrique du Nord", en: "North Africa", ar: "شمال أفريقيا" },
  "West Africa": { fr: "Afrique de l'Ouest", en: "West Africa", ar: "غرب أفريقيا" },
  "Central Africa": { fr: "Afrique Centrale", en: "Central Africa", ar: "وسط أفريقيا" },
  "East Africa": { fr: "Afrique de l'Est", en: "East Africa", ar: "شرق أفريقيا" },
  "Southern Africa": { fr: "Afrique Australe", en: "Southern Africa", ar: "الجنوب الأفريقي" },
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

/**
 * Référentiel des pays africains (Union africaine : 54 États + RASD/Sahara
 * occidental = 55 entrées), avec codes ISO3/ISO2, noms FR/EN, région UN et
 * quelques indicateurs (signataire ZLECAf, présence de données commerciales).
 *
 * Les drapeaux emoji sont dérivés du code ISO2 (symboles indicateurs
 * régionaux) — pas de table de drapeaux à maintenir.
 */

// iso3 -> { iso2, name_en, name_fr, region, zlecafSignatory?, hasTradeData? }
// zlecafSignatory et hasTradeData valent true par défaut, sauf indication.
const _RAW = {
  // Afrique du Nord
  DZA: { iso2: 'DZ', name_en: 'Algeria', name_fr: 'Algérie', region: 'North Africa' },
  EGY: { iso2: 'EG', name_en: 'Egypt', name_fr: 'Égypte', region: 'North Africa' },
  LBY: { iso2: 'LY', name_en: 'Libya', name_fr: 'Libye', region: 'North Africa' },
  MAR: { iso2: 'MA', name_en: 'Morocco', name_fr: 'Maroc', region: 'North Africa' },
  SDN: { iso2: 'SD', name_en: 'Sudan', name_fr: 'Soudan', region: 'North Africa' },
  TUN: { iso2: 'TN', name_en: 'Tunisia', name_fr: 'Tunisie', region: 'North Africa' },
  ESH: {
    iso2: 'EH',
    name_en: 'Western Sahara',
    name_fr: 'Sahara occidental',
    region: 'North Africa',
    hasTradeData: false,
  },

  // Afrique de l'Ouest
  BEN: { iso2: 'BJ', name_en: 'Benin', name_fr: 'Bénin', region: 'West Africa' },
  BFA: { iso2: 'BF', name_en: 'Burkina Faso', name_fr: 'Burkina Faso', region: 'West Africa' },
  CPV: { iso2: 'CV', name_en: 'Cabo Verde', name_fr: 'Cap-Vert', region: 'West Africa' },
  CIV: { iso2: 'CI', name_en: "Côte d'Ivoire", name_fr: "Côte d'Ivoire", region: 'West Africa' },
  GMB: { iso2: 'GM', name_en: 'Gambia', name_fr: 'Gambie', region: 'West Africa' },
  GHA: { iso2: 'GH', name_en: 'Ghana', name_fr: 'Ghana', region: 'West Africa' },
  GIN: { iso2: 'GN', name_en: 'Guinea', name_fr: 'Guinée', region: 'West Africa' },
  GNB: { iso2: 'GW', name_en: 'Guinea-Bissau', name_fr: 'Guinée-Bissau', region: 'West Africa' },
  LBR: { iso2: 'LR', name_en: 'Liberia', name_fr: 'Libéria', region: 'West Africa' },
  MLI: { iso2: 'ML', name_en: 'Mali', name_fr: 'Mali', region: 'West Africa' },
  MRT: { iso2: 'MR', name_en: 'Mauritania', name_fr: 'Mauritanie', region: 'West Africa' },
  NER: { iso2: 'NE', name_en: 'Niger', name_fr: 'Niger', region: 'West Africa' },
  NGA: { iso2: 'NG', name_en: 'Nigeria', name_fr: 'Nigéria', region: 'West Africa' },
  SEN: { iso2: 'SN', name_en: 'Senegal', name_fr: 'Sénégal', region: 'West Africa' },
  SLE: { iso2: 'SL', name_en: 'Sierra Leone', name_fr: 'Sierra Leone', region: 'West Africa' },
  TGO: { iso2: 'TG', name_en: 'Togo', name_fr: 'Togo', region: 'West Africa' },

  // Afrique centrale
  AGO: { iso2: 'AO', name_en: 'Angola', name_fr: 'Angola', region: 'Central Africa' },
  CMR: { iso2: 'CM', name_en: 'Cameroon', name_fr: 'Cameroun', region: 'Central Africa' },
  CAF: {
    iso2: 'CF',
    name_en: 'Central African Republic',
    name_fr: 'République centrafricaine',
    region: 'Central Africa',
  },
  TCD: { iso2: 'TD', name_en: 'Chad', name_fr: 'Tchad', region: 'Central Africa' },
  COG: { iso2: 'CG', name_en: 'Congo', name_fr: 'Congo', region: 'Central Africa' },
  COD: {
    iso2: 'CD',
    name_en: 'DR Congo',
    name_fr: 'RD Congo',
    region: 'Central Africa',
  },
  GNQ: {
    iso2: 'GQ',
    name_en: 'Equatorial Guinea',
    name_fr: 'Guinée équatoriale',
    region: 'Central Africa',
  },
  GAB: { iso2: 'GA', name_en: 'Gabon', name_fr: 'Gabon', region: 'Central Africa' },
  STP: {
    iso2: 'ST',
    name_en: 'São Tomé and Príncipe',
    name_fr: 'Sao Tomé-et-Principe',
    region: 'Central Africa',
  },

  // Afrique de l'Est
  BDI: { iso2: 'BI', name_en: 'Burundi', name_fr: 'Burundi', region: 'East Africa' },
  COM: { iso2: 'KM', name_en: 'Comoros', name_fr: 'Comores', region: 'East Africa' },
  DJI: { iso2: 'DJ', name_en: 'Djibouti', name_fr: 'Djibouti', region: 'East Africa' },
  ERI: {
    iso2: 'ER',
    name_en: 'Eritrea',
    name_fr: 'Érythrée',
    region: 'East Africa',
    zlecafSignatory: false,
  },
  ETH: { iso2: 'ET', name_en: 'Ethiopia', name_fr: 'Éthiopie', region: 'East Africa' },
  KEN: { iso2: 'KE', name_en: 'Kenya', name_fr: 'Kenya', region: 'East Africa' },
  MDG: { iso2: 'MG', name_en: 'Madagascar', name_fr: 'Madagascar', region: 'East Africa' },
  MWI: { iso2: 'MW', name_en: 'Malawi', name_fr: 'Malawi', region: 'East Africa' },
  MUS: { iso2: 'MU', name_en: 'Mauritius', name_fr: 'Maurice', region: 'East Africa' },
  MOZ: { iso2: 'MZ', name_en: 'Mozambique', name_fr: 'Mozambique', region: 'East Africa' },
  RWA: { iso2: 'RW', name_en: 'Rwanda', name_fr: 'Rwanda', region: 'East Africa' },
  SYC: { iso2: 'SC', name_en: 'Seychelles', name_fr: 'Seychelles', region: 'East Africa' },
  SOM: { iso2: 'SO', name_en: 'Somalia', name_fr: 'Somalie', region: 'East Africa' },
  SSD: { iso2: 'SS', name_en: 'South Sudan', name_fr: 'Soudan du Sud', region: 'East Africa' },
  TZA: { iso2: 'TZ', name_en: 'Tanzania', name_fr: 'Tanzanie', region: 'East Africa' },
  UGA: { iso2: 'UG', name_en: 'Uganda', name_fr: 'Ouganda', region: 'East Africa' },
  ZMB: { iso2: 'ZM', name_en: 'Zambia', name_fr: 'Zambie', region: 'East Africa' },
  ZWE: { iso2: 'ZW', name_en: 'Zimbabwe', name_fr: 'Zimbabwe', region: 'East Africa' },

  // Afrique australe
  BWA: { iso2: 'BW', name_en: 'Botswana', name_fr: 'Botswana', region: 'Southern Africa' },
  SWZ: { iso2: 'SZ', name_en: 'Eswatini', name_fr: 'Eswatini', region: 'Southern Africa' },
  LSO: { iso2: 'LS', name_en: 'Lesotho', name_fr: 'Lesotho', region: 'Southern Africa' },
  NAM: { iso2: 'NA', name_en: 'Namibia', name_fr: 'Namibie', region: 'Southern Africa' },
  ZAF: { iso2: 'ZA', name_en: 'South Africa', name_fr: 'Afrique du Sud', region: 'Southern Africa' },
};

/** Drapeau emoji à partir d'un code ISO2 (symboles indicateurs régionaux). */
function iso2ToFlag(iso2) {
  if (!iso2 || iso2.length !== 2) return '🌍';
  const cc = iso2.toUpperCase();
  const A = 0x1f1e6;
  const base = 'A'.charCodeAt(0);
  return String.fromCodePoint(A + (cc.charCodeAt(0) - base), A + (cc.charCodeAt(1) - base));
}

// Table publique : chaque entrée porte iso3, iso2, noms, région, flags + flag emoji.
export const AFRICAN_COUNTRIES = Object.fromEntries(
  Object.entries(_RAW).map(([iso3, v]) => [
    iso3,
    {
      iso3,
      iso2: v.iso2,
      name_en: v.name_en,
      name_fr: v.name_fr,
      region: v.region,
      zlecafSignatory: v.zlecafSignatory !== false,
      hasTradeData: v.hasTradeData !== false,
      flag: iso2ToFlag(v.iso2),
    },
  ])
);

// Mappings inversés bijectifs
export const ISO3_TO_ISO2 = Object.fromEntries(
  Object.entries(AFRICAN_COUNTRIES).map(([iso3, v]) => [iso3, v.iso2])
);
export const ISO2_TO_ISO3 = Object.fromEntries(
  Object.entries(AFRICAN_COUNTRIES).map(([iso3, v]) => [v.iso2, iso3])
);

/** Drapeau depuis un code ISO3 ou ISO2 (insensible à la casse). '🌍' si inconnu. */
export function getCountryFlag(code) {
  if (!code || typeof code !== 'string') return '🌍';
  const up = code.toUpperCase();
  if (up.length === 3 && AFRICAN_COUNTRIES[up]) return AFRICAN_COUNTRIES[up].flag;
  if (up.length === 2 && ISO2_TO_ISO3[up]) return AFRICAN_COUNTRIES[ISO2_TO_ISO3[up]].flag;
  return '🌍';
}

/** ISO2 -> ISO3 (ou null). */
export function getISO3FromISO2(iso2) {
  if (!iso2 || typeof iso2 !== 'string') return null;
  return ISO2_TO_ISO3[iso2.toUpperCase()] || null;
}

/** ISO3 -> ISO2 (ou null). */
export function getISO2FromISO3(iso3) {
  if (!iso3 || typeof iso3 !== 'string') return null;
  return ISO3_TO_ISO2[iso3.toUpperCase()] || null;
}

/** Résout un pays depuis un code ISO3 ou ISO2 ; renvoie l'entrée (avec iso3) ou null. */
export function getCountryInfo(code) {
  if (!code || typeof code !== 'string') return null;
  const up = code.toUpperCase();
  if (up.length === 3 && AFRICAN_COUNTRIES[up]) return AFRICAN_COUNTRIES[up];
  if (up.length === 2 && ISO2_TO_ISO3[up]) return AFRICAN_COUNTRIES[ISO2_TO_ISO3[up]];
  return null;
}

/** Liste des pays { iso3, name, flag, ... } triée par nom localisé. */
export function getAllCountries(lang = 'fr') {
  const key = lang === 'en' ? 'name_en' : 'name_fr';
  return Object.values(AFRICAN_COUNTRIES)
    .map((c) => ({ ...c, name: c[key] }))
    .sort((a, b) => a.name.localeCompare(b.name));
}

/** Pays d'une région donnée (même forme que getAllCountries). */
export function getCountriesByRegion(region, lang = 'fr') {
  return getAllCountries(lang).filter((c) => c.region === region);
}

// Communautés économiques régionales (membres par code ISO3).
export const ECONOMIC_COMMUNITIES = {
  CEMAC: ['CMR', 'CAF', 'TCD', 'COG', 'GNQ', 'GAB'],
  UEMOA: ['BEN', 'BFA', 'CIV', 'GNB', 'MLI', 'NER', 'SEN', 'TGO'],
  ECOWAS: [
    'BEN', 'BFA', 'CPV', 'CIV', 'GMB', 'GHA', 'GIN', 'GNB',
    'LBR', 'MLI', 'NER', 'NGA', 'SEN', 'SLE', 'TGO',
  ],
  EAC: ['BDI', 'COD', 'KEN', 'RWA', 'SSD', 'TZA', 'UGA'],
  SADC: [
    'AGO', 'BWA', 'COD', 'SWZ', 'LSO', 'MDG', 'MWI', 'MUS',
    'MOZ', 'NAM', 'SYC', 'ZAF', 'TZA', 'ZMB', 'ZWE',
  ],
  AMU: ['DZA', 'LBY', 'MRT', 'MAR', 'TUN'],
  COMESA: [
    'BDI', 'COM', 'COD', 'DJI', 'EGY', 'ERI', 'ETH', 'KEN', 'LBY',
    'MDG', 'MWI', 'MUS', 'RWA', 'SYC', 'SOM', 'SDN', 'SWZ', 'TUN',
    'UGA', 'ZMB', 'ZWE',
  ],
};

export default AFRICAN_COUNTRIES;

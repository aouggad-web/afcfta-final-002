/**
 * SADC Country Mappings
 * =======================
 * Comprehensive mapping of all 16 Southern African Development Community
 * (SADC) member states with metadata for use across the AfCFTA platform.
 *
 * Groups:
 *   - SACU Customs Union (Phase 1): ZAF, BWA, NAM, LSO, SWZ
 *   - Resource Economies (Phase 2): AGO, ZMB, ZWE, COD
 *   - Island Nations (Phase 3): MUS, SYC, COM
 *   - Emerging Markets (Phase 4): MOZ, MDG, MWI, TZA
 */

// =============================================================================
// SADC MEMBER STATES
// =============================================================================

export const SADC_COUNTRIES = {
  // ---- Phase 1: SACU Customs Union ----
  ZAF: {
    iso3: 'ZAF',
    iso2: 'ZA',
    name: 'South Africa',
    name_fr: 'Afrique du Sud',
    flag: '🇿🇦',
    capital: 'Pretoria / Cape Town / Bloemfontein',
    currency: 'ZAR',
    phase: 1,
    group: 'SACU',
    isSacu: true,
    isLdc: false,
    isIsland: false,
    dualMembership: [],
    economyFocus: 'diversified_industrial_services',
    gdpUsdBillion: 380,
    populationMillion: 60,
  },
  BWA: {
    iso3: 'BWA',
    iso2: 'BW',
    name: 'Botswana',
    name_fr: 'Botswana',
    flag: '🇧🇼',
    capital: 'Gaborone',
    currency: 'BWP',
    phase: 1,
    group: 'SACU',
    isSacu: true,
    isLdc: false,
    isIsland: false,
    dualMembership: [],
    economyFocus: 'diamonds_mining_services',
    gdpUsdBillion: 19,
    populationMillion: 2.6,
  },
  NAM: {
    iso3: 'NAM',
    iso2: 'NA',
    name: 'Namibia',
    name_fr: 'Namibie',
    flag: '🇳🇦',
    capital: 'Windhoek',
    currency: 'NAD',
    phase: 1,
    group: 'SACU',
    isSacu: true,
    isLdc: false,
    isIsland: false,
    dualMembership: [],
    economyFocus: 'mining_logistics_fishing',
    gdpUsdBillion: 12,
    populationMillion: 2.6,
  },
  LSO: {
    iso3: 'LSO',
    iso2: 'LS',
    name: 'Lesotho',
    name_fr: 'Lesotho',
    flag: '🇱🇸',
    capital: 'Maseru',
    currency: 'LSL',
    phase: 1,
    group: 'SACU',
    isSacu: true,
    isLdc: true,
    isIsland: false,
    dualMembership: [],
    economyFocus: 'textile_manufacturing_water',
    gdpUsdBillion: 2.5,
    populationMillion: 2.2,
  },
  SWZ: {
    iso3: 'SWZ',
    iso2: 'SZ',
    name: 'Eswatini',
    name_fr: 'Eswatini',
    flag: '🇸🇿',
    capital: 'Mbabane',
    currency: 'SZL',
    phase: 1,
    group: 'SACU',
    isSacu: true,
    isLdc: false,
    isIsland: false,
    dualMembership: [],
    economyFocus: 'sugar_manufacturing_forestry',
    gdpUsdBillion: 4.7,
    populationMillion: 1.1,
  },

  // ---- Phase 2: Resource Economies ----
  AGO: {
    iso3: 'AGO',
    iso2: 'AO',
    name: 'Angola',
    name_fr: 'Angola',
    flag: '🇦🇴',
    capital: 'Luanda',
    currency: 'AOA',
    phase: 2,
    group: 'Resource Economies',
    isSacu: false,
    isLdc: true,
    isIsland: false,
    dualMembership: [],
    economyFocus: 'oil_diamonds_reconstruction',
    gdpUsdBillion: 78,
    populationMillion: 35,
  },
  ZMB: {
    iso3: 'ZMB',
    iso2: 'ZM',
    name: 'Zambia',
    name_fr: 'Zambie',
    flag: '🇿🇲',
    capital: 'Lusaka',
    currency: 'ZMW',
    phase: 2,
    group: 'Resource Economies',
    isSacu: false,
    isLdc: true,
    isIsland: false,
    dualMembership: ['COMESA'],
    economyFocus: 'copper_agriculture_energy',
    gdpUsdBillion: 21,
    populationMillion: 19.5,
  },
  ZWE: {
    iso3: 'ZWE',
    iso2: 'ZW',
    name: 'Zimbabwe',
    name_fr: 'Zimbabwe',
    flag: '🇿🇼',
    capital: 'Harare',
    currency: 'ZWG',
    phase: 2,
    group: 'Resource Economies',
    isSacu: false,
    isLdc: false,
    isIsland: false,
    dualMembership: ['COMESA'],
    economyFocus: 'mining_agriculture_manufacturing',
    gdpUsdBillion: 26,
    populationMillion: 15,
  },
  COD: {
    iso3: 'COD',
    iso2: 'CD',
    name: 'DR Congo',
    name_fr: 'République Démocratique du Congo',
    flag: '🇨🇩',
    capital: 'Kinshasa',
    currency: 'CDF',
    phase: 2,
    group: 'Resource Economies',
    isSacu: false,
    isLdc: true,
    isIsland: false,
    dualMembership: ['EAC', 'SADC'],
    economyFocus: 'minerals_agriculture_forestry',
    gdpUsdBillion: 65,
    populationMillion: 100,
  },

  // ---- Phase 3: Island Nations ----
  MUS: {
    iso3: 'MUS',
    iso2: 'MU',
    name: 'Mauritius',
    name_fr: 'Maurice',
    flag: '🇲🇺',
    capital: 'Port Louis',
    currency: 'MUR',
    phase: 3,
    group: 'Island Nations',
    isSacu: false,
    isLdc: false,
    isIsland: true,
    dualMembership: ['COMESA'],
    economyFocus: 'services_manufacturing_tourism',
    gdpUsdBillion: 14,
    populationMillion: 1.3,
  },
  SYC: {
    iso3: 'SYC',
    iso2: 'SC',
    name: 'Seychelles',
    name_fr: 'Seychelles',
    flag: '🇸🇨',
    capital: 'Victoria',
    currency: 'SCR',
    phase: 3,
    group: 'Island Nations',
    isSacu: false,
    isLdc: false,
    isIsland: true,
    dualMembership: ['COMESA'],
    economyFocus: 'tourism_fisheries_finance',
    gdpUsdBillion: 2.1,
    populationMillion: 0.1,
  },
  COM: {
    iso3: 'COM',
    iso2: 'KM',
    name: 'Comoros',
    name_fr: 'Comores',
    flag: '🇰🇲',
    capital: 'Moroni',
    currency: 'KMF',
    phase: 3,
    group: 'Island Nations',
    isSacu: false,
    isLdc: true,
    isIsland: true,
    dualMembership: [],
    economyFocus: 'agriculture_fisheries_tourism',
    gdpUsdBillion: 1.3,
    populationMillion: 0.9,
  },

  // ---- Phase 4: Emerging Markets ----
  MOZ: {
    iso3: 'MOZ',
    iso2: 'MZ',
    name: 'Mozambique',
    name_fr: 'Mozambique',
    flag: '🇲🇿',
    capital: 'Maputo',
    currency: 'MZN',
    phase: 4,
    group: 'Emerging Markets',
    isSacu: false,
    isLdc: true,
    isIsland: false,
    dualMembership: ['COMESA'],
    economyFocus: 'energy_agriculture_logistics',
    gdpUsdBillion: 18,
    populationMillion: 33,
  },
  MDG: {
    iso3: 'MDG',
    iso2: 'MG',
    name: 'Madagascar',
    name_fr: 'Madagascar',
    flag: '🇲🇬',
    capital: 'Antananarivo',
    currency: 'MGA',
    phase: 4,
    group: 'Emerging Markets',
    isSacu: false,
    isLdc: true,
    isIsland: true,
    dualMembership: ['COMESA'],
    economyFocus: 'vanilla_textiles_mining',
    gdpUsdBillion: 14,
    populationMillion: 28,
  },
  MWI: {
    iso3: 'MWI',
    iso2: 'MW',
    name: 'Malawi',
    name_fr: 'Malawi',
    flag: '🇲🇼',
    capital: 'Lilongwe',
    currency: 'MWK',
    phase: 4,
    group: 'Emerging Markets',
    isSacu: false,
    isLdc: true,
    isIsland: false,
    dualMembership: ['COMESA'],
    economyFocus: 'tobacco_agriculture_mining',
    gdpUsdBillion: 12,
    populationMillion: 20,
  },
  TZA: {
    iso3: 'TZA',
    iso2: 'TZ',
    name: 'Tanzania',
    name_fr: 'Tanzanie',
    flag: '🇹🇿',
    capital: 'Dodoma',
    currency: 'TZS',
    phase: 4,
    group: 'Emerging Markets',
    isSacu: false,
    isLdc: true,
    isIsland: false,
    dualMembership: ['EAC', 'SADC'],
    economyFocus: 'agriculture_mining_tourism',
    gdpUsdBillion: 75,
    populationMillion: 63,
  },
};

// =============================================================================
// SACU MEMBERS SUBSET
// =============================================================================

/** ISO3 codes of SACU (Southern African Customs Union) members */
export const SACU_MEMBERS = Object.keys(SADC_COUNTRIES).filter(
  (code) => SADC_COUNTRIES[code].isSacu
);

/** ISO3 codes of SADC LDC (Least Developed Country) members */
export const SADC_LDC_MEMBERS = Object.keys(SADC_COUNTRIES).filter(
  (code) => SADC_COUNTRIES[code].isLdc
);

/** SADC island nations */
export const SADC_ISLAND_NATIONS = Object.keys(SADC_COUNTRIES).filter(
  (code) => SADC_COUNTRIES[code].isIsland
);

/** Countries with dual EAC + SADC membership */
export const DUAL_EAC_SADC_MEMBERS = Object.keys(SADC_COUNTRIES).filter(
  (code) => SADC_COUNTRIES[code].dualMembership.includes('EAC')
);

// =============================================================================
// LOOKUP UTILITIES
// =============================================================================

/**
 * Check whether an ISO3 code is a SADC member state.
 * @param {string} code - ISO3 country code
 * @returns {boolean}
 */
export const isSadcMember = (code) => Boolean(SADC_COUNTRIES[code?.toUpperCase()]);

/**
 * Check whether an ISO3 code is a SACU member.
 * @param {string} code - ISO3 country code
 * @returns {boolean}
 */
export const isSacuMember = (code) => Boolean(SADC_COUNTRIES[code?.toUpperCase()]?.isSacu);

/**
 * Get the SADC phase (1-4) for a country.
 * @param {string} code - ISO3 country code
 * @returns {number|null}
 */
export const getSadcPhase = (code) => SADC_COUNTRIES[code?.toUpperCase()]?.phase ?? null;

/**
 * Get SADC countries grouped by their implementation phase.
 * @returns {Object} Phases 1-4 each containing an array of country objects
 */
export const getSadcByPhase = () => {
  const groups = { 1: [], 2: [], 3: [], 4: [] };
  Object.entries(SADC_COUNTRIES).forEach(([code, info]) => {
    if (groups[info.phase]) {
      groups[info.phase].push({ code, ...info });
    }
  });
  return groups;
};

/**
 * Get SADC countries sorted by GDP (descending).
 * @returns {Array<Object>}
 */
export const getSadcByGdp = () =>
  Object.entries(SADC_COUNTRIES)
    .map(([code, info]) => ({ code, ...info }))
    .sort((a, b) => b.gdpUsdBillion - a.gdpUsdBillion);

/**
 * Get all SADC country codes as an array.
 * @returns {string[]}
 */
export const getSadcCodes = () => Object.keys(SADC_COUNTRIES);

/**
 * Get display name for a SADC country.
 * @param {string} code - ISO3 code
 * @param {string} [lang='en'] - 'en' or 'fr'
 * @returns {string}
 */
export const getSadcCountryName = (code, lang = 'en') => {
  const country = SADC_COUNTRIES[code?.toUpperCase()];
  if (!country) return code;
  return lang === 'fr' ? country.name_fr : country.name;
};

/**
 * Get the flag emoji for a SADC country.
 * @param {string} code - ISO3 code
 * @returns {string}
 */
export const getSadcFlag = (code) => SADC_COUNTRIES[code?.toUpperCase()]?.flag ?? '🌍';

// =============================================================================
// SADC REGIONAL STATS
// =============================================================================

export const SADC_REGIONAL_STATS = {
  memberCount: 16,
  combinedGdpUsdBillion: 800,
  combinedPopulationMillion: 345,
  intraSadcTradeSharePct: 19,
  founded: 1992,
  headquarters: 'Gaborone, Botswana',
  secretariatUrl: 'https://www.sadc.int',
};

export const SACU_STATS = {
  memberCount: 5,
  founded: 1910,
  note: 'Oldest functioning customs union in the world',
  secretariatUrl: 'https://www.sacu.int',
  headquarters: 'Windhoek, Namibia',
};

export default SADC_COUNTRIES;

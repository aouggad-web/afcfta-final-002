/**
 * Mining Intelligence Utilities
 * ================================
 * Helper functions and metadata for the SADC mining sector intelligence
 * module.  Used by frontend components to display mining value-chain
 * information, mineral profiles, and transport route data.
 */

// =============================================================================
// MINERAL PROFILES (frontend-safe copy)
// =============================================================================

export const MINERAL_PROFILES = {
  diamond: {
    label: 'Diamonds',
    hsCodePrefix: '7102',
    icon: '💎',
    sadcGlobalSharePct: 60,
    keyProducers: ['BWA', 'ZAF', 'NAM', 'AGO', 'ZWE'],
    processingStages: ['Mining', 'Sorting', 'Cutting & Polishing', 'Jewellery'],
    primaryMarkets: ['Antwerp', 'Dubai', 'Mumbai', 'Hong Kong'],
    colour: '#60A5FA',
  },
  platinum: {
    label: 'Platinum Group Metals',
    hsCodePrefix: '7110',
    icon: '⚗️',
    sadcGlobalSharePct: 80,
    keyProducers: ['ZAF', 'ZWE'],
    processingStages: ['Mining', 'Smelting', 'Refining', 'Catalyst Fabrication'],
    primaryMarkets: ['USA', 'Europe', 'Japan'],
    colour: '#C084FC',
  },
  copper: {
    label: 'Copper',
    hsCodePrefix: '7403',
    icon: '🔶',
    sadcGlobalSharePct: 15,
    keyProducers: ['ZMB', 'COD', 'ZWE'],
    processingStages: ['Mining', 'Concentrating', 'Smelting', 'Refining', 'Fabrication'],
    primaryMarkets: ['China', 'Europe', 'USA'],
    colour: '#F97316',
  },
  cobalt: {
    label: 'Cobalt',
    hsCodePrefix: '8105',
    icon: '🔵',
    sadcGlobalSharePct: 70,
    keyProducers: ['COD', 'ZMB'],
    processingStages: ['Mining', 'Hydroxide Precipitation', 'Refining', 'Battery Precursor'],
    primaryMarkets: ['China', 'Japan', 'South Korea'],
    colour: '#3B82F6',
  },
  coal: {
    label: 'Coal',
    hsCodePrefix: '2701',
    icon: '⛏️',
    sadcGlobalSharePct: 4,
    keyProducers: ['ZAF', 'MOZ', 'ZWE', 'BWA'],
    processingStages: ['Mining', 'Washing & Beneficiation', 'Export'],
    primaryMarkets: ['India', 'China', 'Japan', 'EU'],
    colour: '#6B7280',
  },
  gold: {
    label: 'Gold',
    hsCodePrefix: '7108',
    icon: '🥇',
    sadcGlobalSharePct: 15,
    keyProducers: ['ZAF', 'ZMB', 'TZA', 'ZWE', 'MOZ'],
    processingStages: ['Mining', 'Milling', 'Smelting', 'Refining'],
    primaryMarkets: ['Zürich', 'London', 'Dubai', 'Shanghai'],
    colour: '#FBBF24',
  },
};

// =============================================================================
// TRANSPORT CORRIDORS (summary for frontend use)
// =============================================================================

export const SADC_CORRIDORS_SUMMARY = [
  {
    id: 'north_south',
    name: 'North-South Corridor',
    alias: 'Cape-to-Cairo (southern)',
    countries: ['ZAF', 'ZWE', 'ZMB', 'TZA', 'COD'],
    anchorPorts: ['Durban', 'Richards Bay'],
    lengthKm: 3400,
    keyBorderPosts: ['Beitbridge (ZAF-ZWE)', 'Chirundu (ZWE-ZMB)', 'Nakonde/Tunduma (ZMB-TZA)'],
    mainCommodities: ['Copper', 'General cargo', 'Fuel', 'Coal'],
    colour: '#EF4444',
  },
  {
    id: 'beira',
    name: 'Beira Corridor',
    countries: ['ZWE', 'MOZ'],
    anchorPorts: ['Beira'],
    lengthKm: 620,
    keyBorderPosts: ['Forbes/Machipanda (ZWE-MOZ)'],
    mainCommodities: ['Fuel', 'General cargo', 'Fertilisers'],
    colour: '#F59E0B',
  },
  {
    id: 'nacala',
    name: 'Nacala Corridor',
    countries: ['MWI', 'MOZ', 'ZMB'],
    anchorPorts: ['Nacala'],
    lengthKm: 1580,
    keyBorderPosts: ['Nayuchi/Entre-Lagos (MWI-MOZ)', 'Chipata/Mchinji (ZMB-MWI)'],
    mainCommodities: ['Coal', 'Fertilisers', 'Tobacco'],
    colour: '#10B981',
  },
  {
    id: 'dar_es_salaam',
    name: 'Dar-es-Salaam Corridor',
    alias: 'Central Corridor',
    countries: ['TZA', 'ZMB', 'COD', 'RWA', 'BDI', 'UGA'],
    anchorPorts: ['Dar-es-Salaam'],
    lengthKm: 2500,
    keyBorderPosts: ['Kasumbalesa (ZMB-COD)'],
    mainCommodities: ['Copper', 'Cobalt', 'Consumer goods'],
    colour: '#6366F1',
  },
  {
    id: 'lobito',
    name: 'Lobito Corridor',
    alias: 'Benguela Railway',
    countries: ['AGO', 'ZMB', 'COD'],
    anchorPorts: ['Lobito'],
    lengthKm: 1344,
    status: 'Under rehabilitation (G7 PGII)',
    mainCommodities: ['Copper', 'Cobalt', 'Minerals'],
    colour: '#8B5CF6',
  },
  {
    id: 'walvis_bay',
    name: 'Walvis Bay Corridors',
    countries: ['NAM', 'BWA', 'ZMB', 'ZAF'],
    anchorPorts: ['Walvis Bay'],
    mainCommodities: ['Copper', 'General cargo', 'Vehicles'],
    note: '30 days shorter to Americas vs Durban',
    colour: '#14B8A6',
  },
];

// =============================================================================
// UTILITY FUNCTIONS
// =============================================================================

/**
 * Get all SADC corridors that include a given country.
 * @param {string} countryCode - ISO3 code
 * @returns {Array<Object>} Corridors involving this country
 */
export const getCorridorsForCountry = (countryCode) =>
  SADC_CORRIDORS_SUMMARY.filter((c) =>
    c.countries.includes(countryCode?.toUpperCase())
  );

/**
 * Get all minerals produced by a given country.
 * @param {string} countryCode - ISO3 code
 * @returns {string[]} Array of mineral keys
 */
export const getMineralsForCountry = (countryCode) => {
  const code = countryCode?.toUpperCase();
  return Object.entries(MINERAL_PROFILES)
    .filter(([, profile]) => profile.keyProducers.includes(code))
    .map(([key]) => key);
};

/**
 * Get all countries producing a specific mineral.
 * @param {string} mineral - Mineral key (e.g. 'copper')
 * @returns {string[]} ISO3 country codes
 */
export const getProducersForMineral = (mineral) =>
  MINERAL_PROFILES[mineral?.toLowerCase()]?.keyProducers ?? [];

/**
 * Calculate approximate value-addition potential for a mineral.
 * @param {string} mineral - Mineral key
 * @param {string} stage - Processing stage label
 * @returns {number} Multiplier relative to raw material value
 */
export const getValueAdditionMultiplier = (mineral, stage) => {
  const stageMultipliers = {
    diamond: { Sorting: 1.5, 'Cutting & Polishing': 3, Jewellery: 5 },
    platinum: { Smelting: 2, Refining: 4, 'Catalyst Fabrication': 8 },
    copper: { Concentrating: 1.5, Smelting: 2, Refining: 2.5, Fabrication: 3 },
    cobalt: { 'Hydroxide Precipitation': 2, Refining: 4, 'Battery Precursor': 8 },
    coal: { 'Washing & Beneficiation': 1.3 },
    gold: { Milling: 1.2, Smelting: 1.5, Refining: 2 },
  };
  const mineralKey = mineral?.toLowerCase();
  return stageMultipliers[mineralKey]?.[stage] ?? 1;
};

/**
 * Return a colour for a mineral for use in charts/maps.
 * @param {string} mineral - Mineral key
 * @returns {string} CSS colour string
 */
export const getMineralColour = (mineral) =>
  MINERAL_PROFILES[mineral?.toLowerCase()]?.colour ?? '#9CA3AF';

/**
 * Format SADC global share percentage for display.
 * @param {string} mineral - Mineral key
 * @returns {string} Formatted string e.g. "60% of world production"
 */
export const getMineralShareLabel = (mineral) => {
  const profile = MINERAL_PROFILES[mineral?.toLowerCase()];
  if (!profile) return '';
  return `${profile.sadcGlobalSharePct}% of world ${profile.label} production`;
};

// =============================================================================
// BENEFICIATION OPPORTUNITIES
// =============================================================================

export const BENEFICIATION_OPPORTUNITIES = [
  {
    mineral: 'diamond',
    label: 'Diamond Beneficiation',
    currentState: 'Rough diamonds exported to Belgium/India',
    opportunity: 'Cutting & polishing, jewellery manufacturing',
    leadingCountry: 'BWA',
    valueMultiplier: '3–5×',
    example: 'Botswana – De Beers sightholder system (Gaborone)',
  },
  {
    mineral: 'platinum',
    label: 'PGM Value Addition',
    currentState: 'PGM concentrate/matte exported',
    opportunity: 'Catalytic converters, hydrogen fuel cell components',
    leadingCountry: 'ZAF',
    valueMultiplier: '4–8×',
    example: 'South Africa – BASF catalyst manufacturing plant',
  },
  {
    mineral: 'copper',
    label: 'Copper Fabrication',
    currentState: 'Cathodes exported to China',
    opportunity: 'Wire rod, electrical cables, copper tubing',
    leadingCountry: 'ZMB',
    valueMultiplier: '2–3×',
    example: 'Zambia – KCM copper cable manufacturing',
  },
  {
    mineral: 'cobalt',
    label: 'Battery Cobalt Processing',
    currentState: 'Cobalt hydroxide exported to Asia',
    opportunity: 'Precursor cathode material (NMC), battery-grade cobalt',
    leadingCountry: 'COD',
    valueMultiplier: '5–10×',
    example: 'DRC – strategic EV supply chain positioning',
  },
  {
    mineral: 'lithium',
    label: 'Lithium Processing',
    currentState: 'Spodumene ore exported',
    opportunity: 'Lithium carbonate / hydroxide for EV batteries',
    leadingCountry: 'ZWE',
    valueMultiplier: '6–10×',
    example: 'Zimbabwe – Prospect Lithium Zimbabwe (Zulu deposit)',
  },
];

export default MINERAL_PROFILES;

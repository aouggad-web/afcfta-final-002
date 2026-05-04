/**
 * OEC Trade Stats - Shared utilities and constants
 */

// Color palette for charts - Modern African theme
export const COLORS = [
  '#059669', '#0891b2', '#7c3aed', '#dc2626', '#ea580c', 
  '#ca8a04', '#16a34a', '#2563eb', '#9333ea', '#e11d48'
];

// Format monetary values
export const formatValue = (value) => {
  if (!value || isNaN(value)) return '$0';
  if (value >= 1e9) return `$${(value / 1e9).toFixed(2)}B`;
  if (value >= 1e6) return `$${(value / 1e6).toFixed(1)}M`;
  if (value >= 1e3) return `$${(value / 1e3).toFixed(0)}K`;
  return `$${value.toFixed(0)}`;
};

// Format quantity values
export const formatQuantity = (quantity) => {
  if (!quantity || isNaN(quantity)) return '0';
  if (quantity >= 1e9) return `${(quantity / 1e9).toFixed(2)}B`;
  if (quantity >= 1e6) return `${(quantity / 1e6).toFixed(1)}M`;
  if (quantity >= 1e3) return `${(quantity / 1e3).toFixed(0)}K`;
  return quantity.toFixed(0);
};

// Translations for the OEC components
export const getTranslations = (language) => ({
  fr: {
    title: "Statistiques Commerciales OEC",
    subtitle: "Données en temps réel de l'Observatory of Economic Complexity",
    countryView: "Par Pays",
    productView: "Par Produit",
    bilateralView: "Commerce Bilatéral",
    selectCountry: "Sélectionner un pays",
    selectYear: "Année",
    tradeFlow: "Flux commercial",
    exports: "Exportations",
    imports: "Importations",
    hsCodeLabel: "Code SH6 (6 chiffres)",
    hsCodePlaceholder: "Ex: 090111 (Café non torréfié)",
    search: "Rechercher",
    loading: "Chargement...",
    noData: "Aucune donnée disponible",
    totalValue: "Valeur totale",
    totalVolume: "Volume total",
    volumeUnit: "tonnes",
    topPartners: "Principaux partenaires",
    topProducts: "Principaux produits",
    africanExporters: "Exportateurs africains",
    country: "Pays",
    value: "Valeur",
    volume: "Volume",
    share: "Part",
    sourceLabel: "Source: OEC / BACI Database",
    exporter: "Exportateur",
    importer: "Importateur",
    bilateralTitle: "Commerce bilatéral",
    product: "Produit",
    rank: "Rang",
    dataYear: "Données pour",
    refreshData: "Actualiser",
    popularProducts: "Produits populaires",
    coffee: "Café",
    cocoa: "Cacao", 
    cotton: "Coton",
    gold: "Or",
    oil: "Pétrole",
    diamonds: "Diamants"
  },
  en: {
    title: "OEC Trade Statistics",
    subtitle: "Real-time data from the Observatory of Economic Complexity",
    countryView: "By Country",
    productView: "By Product",
    bilateralView: "Bilateral Trade",
    selectCountry: "Select a country",
    selectYear: "Year",
    tradeFlow: "Trade flow",
    exports: "Exports",
    imports: "Imports",
    hsCodeLabel: "HS6 Code (6 digits)",
    hsCodePlaceholder: "Ex: 090111 (Unroasted coffee)",
    search: "Search",
    loading: "Loading...",
    noData: "No data available",
    totalValue: "Total value",
    totalVolume: "Total volume",
    volumeUnit: "tonnes",
    topPartners: "Top partners",
    topProducts: "Top products",
    africanExporters: "African exporters",
    country: "Country",
    value: "Value",
    volume: "Volume",
    share: "Share",
    sourceLabel: "Source: OEC / BACI Database",
    exporter: "Exporter",
    importer: "Importer",
    bilateralTitle: "Bilateral trade",
    product: "Product",
    rank: "Rank",
    dataYear: "Data for",
    refreshData: "Refresh",
    popularProducts: "Popular products",
    coffee: "Coffee",
    cocoa: "Cocoa",
    cotton: "Cotton",
    gold: "Gold",
    oil: "Oil",
    diamonds: "Diamonds"
  }
})[language] || getTranslations('fr');

// Popular HS codes for quick selection
export const getPopularHSCodes = (t) => [
  { code: '090111', label: t.coffee },
  { code: '180100', label: t.cocoa },
  { code: '520100', label: t.cotton },
  { code: '710812', label: t.gold },
  { code: '270900', label: t.oil },
  { code: '710231', label: t.diamonds }
];

// Available years for HS Rev. 2017
export const AVAILABLE_YEARS = [2023, 2022, 2021, 2020, 2019, 2018];

import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../ui/card';
import { Button } from '../ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Badge } from '../ui/badge';
import { toast } from '../../hooks/use-toast';
import AITradeSummary from './AITradeSummary';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Drapeaux par code ISO2 (les émojis drapeaux utilisent ISO2)
const countryFlagsISO2 = {
  'DZ': '🇩🇿', 'AO': '🇦🇴', 'BJ': '🇧🇯', 'BW': '🇧🇼', 'BF': '🇧🇫', 'BI': '🇧🇮', 'CM': '🇨🇲', 'CV': '🇨🇻',
  'CF': '🇨🇫', 'TD': '🇹🇩', 'KM': '🇰🇲', 'CG': '🇨🇬', 'CD': '🇨🇩', 'CI': '🇨🇮', 'DJ': '🇩🇯', 'EG': '🇪🇬',
  'GQ': '🇬🇶', 'ER': '🇪🇷', 'SZ': '🇸🇿', 'ET': '🇪🇹', 'GA': '🇬🇦', 'GM': '🇬🇲', 'GH': '🇬🇭', 'GN': '🇬🇳',
  'GW': '🇬🇼', 'KE': '🇰🇪', 'LS': '🇱🇸', 'LR': '🇱🇷', 'LY': '🇱🇾', 'MG': '🇲🇬', 'MW': '🇲🇼', 'ML': '🇲🇱',
  'MR': '🇲🇷', 'MU': '🇲🇺', 'MA': '🇲🇦', 'MZ': '🇲🇿', 'NA': '🇳🇦', 'NE': '🇳🇪', 'NG': '🇳🇬', 'RW': '🇷🇼',
  'ST': '🇸🇹', 'SN': '🇸🇳', 'SC': '🇸🇨', 'SL': '🇸🇱', 'SO': '🇸🇴', 'ZA': '🇿🇦', 'SS': '🇸🇸', 'SD': '🇸🇩',
  'TZ': '🇹🇿', 'TG': '🇹🇬', 'TN': '🇹🇳', 'UG': '🇺🇬', 'ZM': '🇿🇲', 'ZW': '🇿🇼'
};

// Mapping ISO3 → ISO2 pour les drapeaux
const ISO3_TO_ISO2 = {
  'DZA': 'DZ', 'AGO': 'AO', 'BEN': 'BJ', 'BWA': 'BW', 'BFA': 'BF', 'BDI': 'BI', 'CMR': 'CM', 'CPV': 'CV',
  'CAF': 'CF', 'TCD': 'TD', 'COM': 'KM', 'COG': 'CG', 'COD': 'CD', 'CIV': 'CI', 'DJI': 'DJ', 'EGY': 'EG',
  'GNQ': 'GQ', 'ERI': 'ER', 'SWZ': 'SZ', 'ETH': 'ET', 'GAB': 'GA', 'GMB': 'GM', 'GHA': 'GH', 'GIN': 'GN',
  'GNB': 'GW', 'KEN': 'KE', 'LSO': 'LS', 'LBR': 'LR', 'LBY': 'LY', 'MDG': 'MG', 'MWI': 'MW', 'MLI': 'ML',
  'MRT': 'MR', 'MUS': 'MU', 'MAR': 'MA', 'MOZ': 'MZ', 'NAM': 'NA', 'NER': 'NE', 'NGA': 'NG', 'RWA': 'RW',
  'STP': 'ST', 'SEN': 'SN', 'SYC': 'SC', 'SLE': 'SL', 'SOM': 'SO', 'ZAF': 'ZA', 'SSD': 'SS', 'SDN': 'SD',
  'TZA': 'TZ', 'TGO': 'TG', 'TUN': 'TN', 'UGA': 'UG', 'ZMB': 'ZM', 'ZWE': 'ZW'
};

// Fonction pour obtenir le drapeau (supporte ISO2 et ISO3)
const getFlag = (code) => {
  if (!code) return '🌍';
  const iso2 = code.length === 3 ? ISO3_TO_ISO2[code] : code;
  return countryFlagsISO2[iso2] || '🌍';
};

// Garder countryFlags pour rétrocompatibilité
const countryFlags = countryFlagsISO2;

const formatNumber = (number) => {
  return new Intl.NumberFormat('en-US').format(number);
};

export default function CountryProfilesTab({ language = 'fr' }) {
  const [countries, setCountries] = useState([]);
  const [selectedCountry, setSelectedCountry] = useState('');
  const [countryProfile, setCountryProfile] = useState(null);

  const texts = {
    fr: {
      title: "Profils Économiques des Pays",
      description: "Sélectionnez un pays pour consulter son profil économique complet, ses infrastructures et ses projets structurants (2025-2030)",
      selectPlaceholder: "🔍 Choisir un pays",
      error: "Erreur",
      loadError: "Impossible de charger la liste des pays",
      population: "Population",
      inhabitants: "habitants",
      totalGdp: "PIB Total",
      rank: "Rang",
      gdpPerCapita: "PIB/Habitant",
      perPerson: "USD/personne",
      hdi2024: "IDH 2024",
      hdiDesc: "Indice Dév. Humain",
      millionsInhabitants: "Millions d'habitants",
      goldReserves: "Réserves d'Or",
      tonnes: "tonnes",
      africa: "Afrique",
      global: "Mondial",
      gaiTitle: "Global Attractiveness Index 2025",
      improving: "En hausse",
      declining: "En baisse",
      stable: "Stable",
      structuringProjects: "Projets Structurants & Perspectives 2030",
      majorInvestments: "Investissements majeurs en cours de réalisation (Rail, Ports, Mines, Énergie)",
      budget: "Budget",
      impact: "Impact",
      partners: "Partenaires",
      worldBankIndicators: "Indicateurs World Bank Data360 (2024)",
      officialData: "Données officielles de la Banque Mondiale - Mis à jour 2024",
      socialIndicators: "Indicateurs Sociaux",
      lifeExpectancy: "Espérance de vie",
      years: "ans",
      giniIndex: "Indice Gini",
      outOf100: "sur 100",
      povertyRate: "Pauvreté ($3/jour)",
      populationPercent: "population",
      urbanPopulation: "Population urbaine",
      ofTotal: "du total",
      digitalConnectivity: "Digital & Connectivité",
      internetAccess: "Accès Internet",
      cybersecurity: "Cybersécurité",
      electricityAccess: "Accès Électricité",
      coverage3g: "Couverture 3G",
      environmentEquality: "Environnement & Égalité",
      workingWomen: "Femmes actives",
      femalePopulation: "pop. fém.",
      waterStress: "Stress hydrique",
      resources: "ressources",
      ghgEmissions: "Émissions GES",
      learningPoverty: "Pauvreté éducative",
      children: "enfants",
      source: "Source",
      infrastructurePerformance: "Performance Infrastructure & Logistique",
      continentalRanking: "Classement continental (AIDI 2025) et mondial (LPI 2023)",
      lpiScore: "Score IPL (LPI)",
      infrastructure: "Infrastructure",
      worldRank: "Rang Mondial",
      aidiScore: "Score AIDI 2025",
      globalIndex: "Indice Global",
      africaRank: "Rang Afrique",
      lpiDescription: "Évalue la qualité des infrastructures liées au commerce et au transport (Banque Mondiale).",
      aidiDescription: "Mesure composite du développement des infrastructures (Transport, Électricité, TIC, Eau) par la BAD."
    },
    en: {
      title: "Country Economic Profiles",
      description: "Select a country to view its complete economic profile, infrastructure and structuring projects (2025-2030)",
      selectPlaceholder: "🔍 Choose a country",
      error: "Error",
      loadError: "Unable to load country list",
      population: "Population",
      inhabitants: "inhabitants",
      totalGdp: "Total GDP",
      rank: "Rank",
      gdpPerCapita: "GDP/Capita",
      perPerson: "USD/person",
      hdi2024: "HDI 2024",
      hdiDesc: "Human Dev. Index",
      millionsInhabitants: "Million inhabitants",
      goldReserves: "Gold Reserves",
      tonnes: "tonnes",
      africa: "Africa",
      global: "Global",
      gaiTitle: "Global Attractiveness Index 2025",
      improving: "Improving",
      declining: "Declining",
      stable: "Stable",
      structuringProjects: "Structuring Projects & 2030 Perspectives",
      majorInvestments: "Major investments underway (Rail, Ports, Mining, Energy)",
      budget: "Budget",
      impact: "Impact",
      partners: "Partners",
      worldBankIndicators: "World Bank Data360 Indicators (2024)",
      officialData: "Official World Bank data - Updated 2024",
      socialIndicators: "Social Indicators",
      lifeExpectancy: "Life Expectancy",
      years: "years",
      giniIndex: "Gini Index",
      outOf100: "out of 100",
      povertyRate: "Poverty ($3/day)",
      populationPercent: "population",
      urbanPopulation: "Urban Population",
      ofTotal: "of total",
      digitalConnectivity: "Digital & Connectivity",
      internetAccess: "Internet Access",
      cybersecurity: "Cybersecurity",
      electricityAccess: "Electricity Access",
      coverage3g: "3G Coverage",
      environmentEquality: "Environment & Equality",
      workingWomen: "Working Women",
      femalePopulation: "female pop.",
      waterStress: "Water Stress",
      resources: "resources",
      ghgEmissions: "GHG Emissions",
      learningPoverty: "Learning Poverty",
      children: "children",
      source: "Source",
      infrastructurePerformance: "Infrastructure & Logistics Performance",
      continentalRanking: "Continental ranking (AIDI 2025) and global (LPI 2023)",
      lpiScore: "LPI Score",
      infrastructure: "Infrastructure",
      worldRank: "World Rank",
      aidiScore: "AIDI 2025 Score",
      globalIndex: "Global Index",
      africaRank: "Africa Rank",
      lpiDescription: "Evaluates the quality of trade and transport related infrastructure (World Bank).",
      aidiDescription: "Composite measure of infrastructure development (Transport, Electricity, ICT, Water) by AfDB."
    }
  };

  const t = texts[language];

  useEffect(() => {
    fetchCountries();
  }, [language]);

  const fetchCountries = async () => {
    try {
      const response = await axios.get(`${API}/countries?lang=${language}`);
      setCountries(response.data);
    } catch (error) {
      console.error('Error loading countries:', error);
      toast({
        title: t.error,
        description: t.loadError,
        variant: "destructive"
      });
    }
  };

  const fetchCountryProfile = async (countryCode) => {
    try {
      const response = await axios.get(`${API}/country-profile/${countryCode}?lang=${language}`);
      setCountryProfile(response.data);
    } catch (error) {
      console.error('Error loading country profile:', error);
    }
  };

  return (
    <div className="space-y-6">
      <Card className="shadow-xl border-t-4 border-t-blue-600">
        <CardHeader className="bg-gradient-to-r from-blue-50 to-cyan-50">
          <CardTitle className="text-2xl font-bold text-blue-700 flex items-center gap-2">
            <span>🌍</span>
            <span>{t.title}</span>
          </CardTitle>
          <CardDescription className="font-semibold text-gray-700">
            {t.description}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Select 
            value={selectedCountry} 
            onValueChange={(value) => {
              setSelectedCountry(value);
              fetchCountryProfile(value);
            }}
          >
            <SelectTrigger className="text-lg font-semibold border-2 border-blue-300 focus:border-blue-500">
              <SelectValue placeholder={t.selectPlaceholder} />
            </SelectTrigger>
            <SelectContent>
              {countries.map((country) => (
                <SelectItem key={country.code} value={country.code}>
                  {getFlag(country.iso2 || country.code)} {country.name} - {country.region}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </CardContent>
      </Card>

      {countryProfile && (
        <div className="space-y-4">
          <Card className="shadow-2xl border-0 bg-gradient-to-br from-gray-900 to-gray-800">
            <CardHeader className="bg-gradient-to-r from-green-900/50 via-amber-900/30 to-red-900/30 border-b border-amber-500/30">
              <CardTitle className="flex items-center space-x-3 text-2xl">
                <span className="text-5xl drop-shadow-lg">{getFlag(countryProfile.country_code)}</span>
                <div>
                  <span className="font-bold text-amber-400 text-3xl">{countryProfile.country_name}</span>
                  <p className="text-sm text-gray-300 mt-1">{countryProfile.region}</p>
                </div>
              </CardTitle>
              <CardDescription className="text-lg font-semibold text-gray-200 flex items-center gap-4 mt-2">
                <span className="bg-amber-600/30 px-3 py-1 rounded-full text-amber-300">👥 {countryProfile.population_millions ? `${countryProfile.population_millions.toFixed(1)}M` : formatNumber(countryProfile.population)} {t.inhabitants}</span>
                <span className="bg-green-600/30 px-3 py-1 rounded-full text-green-300">🌍 UA Member</span>
              </CardDescription>
            </CardHeader>
            <CardContent className="pt-6 bg-gray-900/50">
              {/* SECTION: Indicateurs Économiques Principaux */}
              <div className="mb-6">
                <h3 className="text-lg font-bold text-amber-400 mb-4 flex items-center gap-2 border-b border-amber-500/30 pb-2">
                  <span className="text-2xl">💰</span> {language === 'fr' ? 'Indicateurs Économiques' : 'Economic Indicators'}
                </h3>
                <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                  {/* PIB Total */}
                  {countryProfile.gdp_usd && (
                    <div className="bg-gradient-to-br from-emerald-900/80 to-green-800/60 p-4 rounded-xl border-2 border-emerald-500 shadow-lg shadow-emerald-500/20 text-center transform hover:scale-105 transition-all">
                      <p className="text-xs font-bold text-emerald-300 mb-2 uppercase tracking-wide">💵 {t.totalGdp}</p>
                      <p className="text-3xl font-extrabold text-white drop-shadow-lg">
                        ${(countryProfile.gdp_usd / 1000000000).toFixed(1)}B
                      </p>
                      <p className="text-xs text-emerald-200 mt-2 bg-emerald-950/50 rounded-full px-2 py-1">{t.rank}: #{countryProfile.projections?.africa_rank || 'N/A'}</p>
                    </div>
                  )}
                  
                  {/* PIB par Habitant */}
                  {countryProfile.gdp_per_capita && (
                    <div className="bg-gradient-to-br from-blue-900/80 to-cyan-800/60 p-4 rounded-xl border-2 border-blue-500 shadow-lg shadow-blue-500/20 text-center transform hover:scale-105 transition-all">
                      <p className="text-xs font-bold text-blue-300 mb-2 uppercase tracking-wide">👤 {t.gdpPerCapita}</p>
                      <p className="text-3xl font-extrabold text-white drop-shadow-lg">
                        ${formatNumber(Math.round(countryProfile.gdp_per_capita))}
                      </p>
                      <p className="text-xs text-blue-200 mt-2 bg-blue-950/50 rounded-full px-2 py-1">{t.perPerson}</p>
                    </div>
                  )}
                  
                  {/* Croissance 2024 */}
                  <div className="bg-gradient-to-br from-teal-900/80 to-cyan-800/60 p-4 rounded-xl border-2 border-teal-500 shadow-lg shadow-teal-500/20 text-center transform hover:scale-105 transition-all">
                    <p className="text-xs font-bold text-teal-300 mb-2 uppercase tracking-wide">📈 {language === 'fr' ? 'Croissance' : 'Growth'} 2024</p>
                    <p className={`text-3xl font-extrabold drop-shadow-lg ${parseFloat(countryProfile.projections?.gdp_growth_forecast_2024) >= 5 ? 'text-green-400' : parseFloat(countryProfile.projections?.gdp_growth_forecast_2024) >= 3 ? 'text-white' : 'text-orange-400'}`}>
                      {countryProfile.projections?.gdp_growth_forecast_2024 || 'N/A'}
                    </p>
                    <p className="text-xs text-teal-200 mt-2 bg-teal-950/50 rounded-full px-2 py-1">FMI 2024</p>
                  </div>
                  
                  {/* Projection 2025 */}
                  <div className="bg-gradient-to-br from-amber-900/80 to-yellow-800/60 p-4 rounded-xl border-2 border-amber-500 shadow-lg shadow-amber-500/20 text-center transform hover:scale-105 transition-all">
                    <p className="text-xs font-bold text-amber-300 mb-2 uppercase tracking-wide">🎯 Projection 2025</p>
                    <p className={`text-3xl font-extrabold drop-shadow-lg ${countryProfile.projections?.gdp_growth_projection_2025 && countryProfile.projections?.gdp_growth_projection_2025 !== 'N/A' ? 'text-white' : 'text-gray-400'}`}>
                      {countryProfile.projections?.gdp_growth_projection_2025 || 'N/A'}
                    </p>
                    <p className="text-xs text-amber-200 mt-2 bg-amber-950/50 rounded-full px-2 py-1">FMI/BM</p>
                  </div>
                  
                  {/* IDH */}
                  <div className="bg-gradient-to-br from-purple-900/80 to-violet-800/60 p-4 rounded-xl border-2 border-purple-500 shadow-lg shadow-purple-500/20 text-center transform hover:scale-105 transition-all">
                    <p className="text-xs font-bold text-purple-300 mb-2 uppercase tracking-wide">📊 {t.hdi2024}</p>
                    <p className="text-3xl font-extrabold text-white drop-shadow-lg">
                      {countryProfile.hdi || countryProfile.projections?.development_index || 'N/A'}
                    </p>
                    <p className="text-xs text-purple-200 mt-2 bg-purple-950/50 rounded-full px-2 py-1">{countryProfile.hdi_rank ? `Rang #${countryProfile.hdi_rank}` : 'PNUD'}</p>
                  </div>
                </div>
              </div>

              {/* SECTION: Indicateurs Sociaux */}
              <div className="mb-6">
                <h3 className="text-lg font-bold text-amber-400 mb-4 flex items-center gap-2 border-b border-amber-500/30 pb-2">
                  <span className="text-2xl">👥</span> {language === 'fr' ? 'Indicateurs Sociaux' : 'Social Indicators'}
                </h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {/* Inflation */}
                  <div className={`p-4 rounded-xl border-2 shadow-lg text-center transform hover:scale-105 transition-all ${
                    countryProfile.inflation_rate && countryProfile.inflation_rate > 15 
                      ? 'bg-gradient-to-br from-red-900/80 to-red-700/60 border-red-500 shadow-red-500/20' 
                      : countryProfile.inflation_rate && countryProfile.inflation_rate > 7 
                        ? 'bg-gradient-to-br from-orange-900/80 to-amber-700/60 border-orange-500 shadow-orange-500/20'
                        : 'bg-gradient-to-br from-green-900/80 to-emerald-700/60 border-green-500 shadow-green-500/20'
                  }`}>
                    <p className="text-xs font-bold text-white/80 mb-2 uppercase tracking-wide">📈 Inflation 2024</p>
                    <p className="text-3xl font-extrabold text-white drop-shadow-lg">
                      {countryProfile.inflation_rate ? `${countryProfile.inflation_rate.toFixed(1)}%` : 'N/A'}
                    </p>
                    <p className="text-xs text-white/70 mt-2 bg-black/20 rounded-full px-2 py-1">FMI/BM</p>
                  </div>

                  {/* Chômage */}
                  <div className={`p-4 rounded-xl border-2 shadow-lg text-center transform hover:scale-105 transition-all ${
                    countryProfile.unemployment_rate && countryProfile.unemployment_rate > 25 
                      ? 'bg-gradient-to-br from-red-900/80 to-red-700/60 border-red-500 shadow-red-500/20' 
                      : countryProfile.unemployment_rate && countryProfile.unemployment_rate > 15 
                        ? 'bg-gradient-to-br from-orange-900/80 to-amber-700/60 border-orange-500 shadow-orange-500/20'
                        : 'bg-gradient-to-br from-green-900/80 to-emerald-700/60 border-green-500 shadow-green-500/20'
                  }`}>
                    <p className="text-xs font-bold text-white/80 mb-2 uppercase tracking-wide">👔 {language === 'fr' ? 'Chômage' : 'Unemployment'} 2024</p>
                    <p className="text-3xl font-extrabold text-white drop-shadow-lg">
                      {countryProfile.unemployment_rate ? `${countryProfile.unemployment_rate.toFixed(1)}%` : 'N/A'}
                    </p>
                    <p className="text-xs text-white/70 mt-2 bg-black/20 rounded-full px-2 py-1">OIT/BM</p>
                  </div>

                  {/* Population */}
                  <div className="bg-gradient-to-br from-cyan-900/80 to-blue-800/60 p-4 rounded-xl border-2 border-cyan-500 shadow-lg shadow-cyan-500/20 text-center transform hover:scale-105 transition-all">
                    <p className="text-xs font-bold text-cyan-300 mb-2 uppercase tracking-wide">👥 Population</p>
                    <p className="text-3xl font-extrabold text-white drop-shadow-lg">
                      {countryProfile.population_millions ? `${countryProfile.population_millions.toFixed(1)}M` : (countryProfile.population ? formatNumber(countryProfile.population) : 'N/A')}
                    </p>
                    <p className="text-xs text-cyan-200 mt-2 bg-cyan-950/50 rounded-full px-2 py-1">2024</p>
                  </div>

                  {/* Rang IDH Mondial */}
                  <div className={`p-4 rounded-xl border-2 shadow-lg text-center transform hover:scale-105 transition-all ${
                    countryProfile.hdi_rank && countryProfile.hdi_rank <= 80 
                      ? 'bg-gradient-to-br from-green-900/80 to-emerald-700/60 border-green-500 shadow-green-500/20' 
                      : countryProfile.hdi_rank && countryProfile.hdi_rank <= 120 
                        ? 'bg-gradient-to-br from-amber-900/80 to-yellow-700/60 border-amber-500 shadow-amber-500/20'
                        : 'bg-gradient-to-br from-red-900/80 to-orange-700/60 border-red-500 shadow-red-500/20'
                  }`}>
                    <p className="text-xs font-bold text-white/80 mb-2 uppercase tracking-wide">🏆 {language === 'fr' ? 'Rang IDH' : 'HDI Rank'}</p>
                    <p className="text-3xl font-extrabold text-white drop-shadow-lg">
                      #{countryProfile.hdi_rank || 'N/A'}
                    </p>
                    <p className="text-xs text-white/70 mt-2 bg-black/20 rounded-full px-2 py-1">/193 pays</p>
                  </div>
                </div>
              </div>

              {/* SECTION DETTE PUBLIQUE */}
              {(countryProfile.total_debt_pct_gdp || countryProfile.external_debt_pct_gdp) && (
                <div className="mb-6">
                  <h3 className="text-lg font-bold text-amber-400 mb-4 flex items-center gap-2 border-b border-amber-500/30 pb-2">
                    <span className="text-2xl">💳</span> {language === 'fr' ? 'Dette Publique 2024' : 'Public Debt 2024'}
                    <span className="text-xs font-normal text-gray-400 ml-2">(FMI/BM)</span>
                  </h3>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {/* Dette Totale */}
                    <div className={`p-4 rounded-xl border-2 shadow-lg text-center transform hover:scale-105 transition-all ${
                      countryProfile.total_debt_pct_gdp > 80 
                        ? 'bg-gradient-to-br from-red-900/80 to-red-700/60 border-red-500 shadow-red-500/20' 
                        : countryProfile.total_debt_pct_gdp > 60 
                          ? 'bg-gradient-to-br from-orange-900/80 to-amber-700/60 border-orange-500 shadow-orange-500/20'
                          : countryProfile.total_debt_pct_gdp > 40 
                            ? 'bg-gradient-to-br from-yellow-900/80 to-amber-700/60 border-yellow-500 shadow-yellow-500/20'
                            : 'bg-gradient-to-br from-green-900/80 to-emerald-700/60 border-green-500 shadow-green-500/20'
                    }`}>
                      <p className="text-xs font-bold text-white/80 mb-2 uppercase tracking-wide">📊 {language === 'fr' ? 'Dette Totale' : 'Total Debt'}</p>
                      <p className="text-3xl font-extrabold text-white drop-shadow-lg">
                        {countryProfile.total_debt_pct_gdp ? `${countryProfile.total_debt_pct_gdp.toFixed(1)}%` : 'N/A'}
                      </p>
                      <p className="text-xs text-white/70 mt-2 bg-black/20 rounded-full px-2 py-1">{language === 'fr' ? 'du PIB' : 'of GDP'}</p>
                    </div>

                    {/* Dette Extérieure */}
                    <div className="bg-gradient-to-br from-blue-900/80 to-indigo-800/60 p-4 rounded-xl border-2 border-blue-500 shadow-lg shadow-blue-500/20 text-center transform hover:scale-105 transition-all">
                      <p className="text-xs font-bold text-blue-300 mb-2 uppercase tracking-wide">🌍 {language === 'fr' ? 'Dette Extérieure' : 'External Debt'}</p>
                      <p className="text-3xl font-extrabold text-white drop-shadow-lg">
                        {countryProfile.external_debt_pct_gdp ? `${countryProfile.external_debt_pct_gdp.toFixed(1)}%` : 'N/A'}
                      </p>
                      <p className="text-xs text-blue-200 mt-2 bg-blue-950/50 rounded-full px-2 py-1">{language === 'fr' ? 'du PIB' : 'of GDP'}</p>
                      {countryProfile.external_debt_bn_usd && (
                        <p className="text-lg font-bold text-amber-400 mt-2">
                          ${countryProfile.external_debt_bn_usd.toFixed(1)}B
                        </p>
                      )}
                    </div>

                    {/* Dette Intérieure */}
                    <div className="bg-gradient-to-br from-purple-900/80 to-violet-800/60 p-4 rounded-xl border-2 border-purple-500 shadow-lg shadow-purple-500/20 text-center transform hover:scale-105 transition-all">
                      <p className="text-xs font-bold text-purple-300 mb-2 uppercase tracking-wide">🏠 {language === 'fr' ? 'Dette Intérieure' : 'Domestic Debt'}</p>
                      <p className="text-3xl font-extrabold text-white drop-shadow-lg">
                        {countryProfile.domestic_debt_pct_gdp ? `${countryProfile.domestic_debt_pct_gdp.toFixed(1)}%` : 'N/A'}
                      </p>
                      <p className="text-xs text-purple-200 mt-2 bg-purple-950/50 rounded-full px-2 py-1">{language === 'fr' ? 'du PIB' : 'of GDP'}</p>
                    </div>

                    {/* Indicateur de Viabilité */}
                    <div className={`p-4 rounded-xl border-2 shadow-lg text-center transform hover:scale-105 transition-all ${
                      countryProfile.total_debt_pct_gdp <= 40 
                        ? 'bg-gradient-to-br from-green-900/80 to-emerald-700/60 border-green-500 shadow-green-500/20' 
                        : countryProfile.total_debt_pct_gdp <= 60 
                          ? 'bg-gradient-to-br from-amber-900/80 to-yellow-700/60 border-amber-500 shadow-amber-500/20'
                          : countryProfile.total_debt_pct_gdp <= 80 
                            ? 'bg-gradient-to-br from-orange-900/80 to-amber-700/60 border-orange-500 shadow-orange-500/20'
                            : 'bg-gradient-to-br from-red-900/80 to-red-700/60 border-red-500 shadow-red-500/20'
                    }`}>
                      <p className="text-xs font-bold text-white/80 mb-2 uppercase tracking-wide">⚖️ {language === 'fr' ? 'Viabilité' : 'Sustainability'}</p>
                      <div className="flex justify-center items-center py-2">
                        {countryProfile.total_debt_pct_gdp <= 40 ? (
                          <span className="text-lg font-extrabold text-green-300">✓ FAIBLE RISQUE</span>
                        ) : countryProfile.total_debt_pct_gdp <= 60 ? (
                          <span className="text-lg font-extrabold text-amber-300">⚠ MODÉRÉ</span>
                        ) : countryProfile.total_debt_pct_gdp <= 80 ? (
                          <span className="text-lg font-extrabold text-orange-300">⚠ ÉLEVÉ</span>
                        ) : (
                          <span className="text-lg font-extrabold text-red-300">🚨 CRITIQUE</span>
                        )}
                      </div>
                      <p className="text-xs text-white/70 mt-2 bg-black/20 rounded-full px-2 py-1">{language === 'fr' ? 'Seuil FMI: 60%' : 'IMF threshold: 60%'}</p>
                    </div>
                  </div>
                </div>
              )}

              {/* AI Trade Analysis Section */}
              <div className="mb-4">
                <AITradeSummary 
                  countryName={countryProfile.country_name}
                  language={language}
                />
              </div>

              {/* Gold Reserves & GAI 2025 */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                {/* Gold Reserves */}
                {countryProfile.projections?.gold_reserves_tonnes !== undefined && (
                  <div className="bg-gradient-to-br from-yellow-50 to-amber-100 p-4 rounded-lg shadow-lg border-2 border-yellow-400">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-2xl">🥇</span>
                      <p className="text-sm font-bold text-yellow-800">{t.goldReserves}</p>
                    </div>
                    <p className="text-3xl font-bold text-yellow-700 mb-2">
                      {countryProfile.projections.gold_reserves_tonnes.toFixed(1)} <span className="text-xl">{t.tonnes}</span>
                    </p>
                    <div className="flex gap-3 text-xs">
                      <span className="bg-yellow-200 text-yellow-800 px-2 py-1 rounded font-semibold">
                        🌍 {t.africa}: #{countryProfile.projections.gold_reserves_rank_africa}
                      </span>
                      {countryProfile.projections.gold_reserves_rank_global && (
                        <span className="bg-yellow-300 text-yellow-900 px-2 py-1 rounded font-semibold">
                          🌎 {t.global}: #{countryProfile.projections.gold_reserves_rank_global}
                        </span>
                      )}
                    </div>
                  </div>
                )}

                {/* Global Attractiveness Index 2025 */}
                {countryProfile.projections?.gai_2025_score !== undefined && (
                  <div className="bg-gradient-to-br from-indigo-50 to-purple-100 p-4 rounded-lg shadow-lg border-2 border-indigo-400">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <span className="text-2xl">📊</span>
                        <p className="text-sm font-bold text-indigo-800">{t.gaiTitle}</p>
                      </div>
                      <span className={`px-3 py-1 rounded-full font-bold text-sm ${
                        countryProfile.projections.gai_2025_rating === 'A' ? 'bg-green-500 text-white' :
                        countryProfile.projections.gai_2025_rating?.startsWith('A') ? 'bg-green-400 text-white' :
                        countryProfile.projections.gai_2025_rating?.startsWith('B') ? 'bg-blue-400 text-white' :
                        countryProfile.projections.gai_2025_rating?.startsWith('C') ? 'bg-yellow-400 text-white' :
                        countryProfile.projections.gai_2025_rating?.startsWith('D') ? 'bg-orange-400 text-white' :
                        'bg-red-400 text-white'
                      }`}>
                        {countryProfile.projections.gai_2025_rating}
                      </span>
                    </div>
                    <div className="flex items-baseline gap-2 mb-2">
                      <p className="text-4xl font-bold text-indigo-700">
                        {countryProfile.projections.gai_2025_score.toFixed(1)}
                      </p>
                      <span className={`text-sm font-semibold px-2 py-1 rounded ${
                        countryProfile.projections.gai_2025_trend === 'improving' ? 'bg-green-200 text-green-800' :
                        countryProfile.projections.gai_2025_trend === 'declining' ? 'bg-red-200 text-red-800' :
                        'bg-gray-200 text-gray-800'
                      }`}>
                        {countryProfile.projections.gai_2025_trend === 'improving' ? `📈 ${t.improving}` :
                         countryProfile.projections.gai_2025_trend === 'declining' ? `📉 ${t.declining}` :
                         `➡️ ${t.stable}`}
                      </span>
                    </div>
                    <div className="flex gap-3 text-xs">
                      <span className="bg-indigo-200 text-indigo-800 px-2 py-1 rounded font-semibold">
                        🌍 {t.africa}: #{countryProfile.projections.gai_2025_rank_africa}
                      </span>
                      <span className="bg-purple-200 text-purple-800 px-2 py-1 rounded font-semibold">
                        🌎 {t.global}: #{countryProfile.projections.gai_2025_rank_global}
                      </span>
                    </div>
                  </div>
                )}
              </div>

              {/* Section Perspectives & Projets Structurants (Nouveau) */}
              {countryProfile.ongoing_projects && countryProfile.ongoing_projects.length > 0 && (
                <div className="mb-4">
                  <Card className="shadow-xl border-t-4 border-t-emerald-600">
                    <CardHeader className="bg-gradient-to-r from-emerald-50 to-teal-50">
                      <CardTitle className="text-xl font-bold text-emerald-700 flex items-center gap-2">
                        <span>🏗️</span>
                        <span>{t.structuringProjects}</span>
                      </CardTitle>
                      <CardDescription className="font-semibold text-gray-700">
                        {t.majorInvestments}
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="pt-6">
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {countryProfile.ongoing_projects.map((project, index) => {
                          const isOperational = project.statut?.includes('OPÉRATIONNEL') || project.statut?.includes('✅');
                          const isConstruction = project.statut?.includes('construction') || project.statut?.includes('Construction');
                          
                          return (
                          <div key={index} className={`rounded-xl shadow-md border-2 hover:shadow-xl transition-all overflow-hidden flex flex-col ${
                            isOperational ? 'border-green-500 bg-green-50' : 
                            isConstruction ? 'border-amber-400 bg-amber-50' :
                            'border-gray-200 bg-white'
                          }`}>
                            <div className={`text-white p-3 ${
                              isOperational ? 'bg-gradient-to-r from-green-600 to-emerald-600' :
                              isConstruction ? 'bg-gradient-to-r from-amber-500 to-orange-500' :
                              'bg-gradient-to-r from-emerald-600 to-teal-600'
                            }`}>
                              <h5 className="font-bold text-sm leading-tight flex items-center gap-2">
                                {isOperational && <span>✅</span>}
                                {isConstruction && <span>🏗️</span>}
                                {project.titre}
                              </h5>
                            </div>
                            <div className="p-4 flex-grow flex flex-col gap-3">
                              <div className="flex justify-between items-start flex-wrap gap-2">
                                <Badge variant="outline" className={`text-xs ${
                                  isOperational ? 'bg-green-100 text-green-700 border-green-300' :
                                  'bg-emerald-50 text-emerald-700 border-emerald-200'
                                }`}>
                                  {project.secteur}
                                </Badge>
                                <span className={`text-xs font-bold px-2 py-1 rounded ${
                                  isOperational ? 'bg-green-200 text-green-800' :
                                  'bg-gray-100 text-gray-600'
                                }`}>
                                  🏁 {project.echeance}
                                </span>
                              </div>
                              
                              {/* Statut bien visible */}
                              <div className={`px-3 py-2 rounded-lg text-sm font-bold text-center ${
                                isOperational ? 'bg-green-500 text-white' :
                                isConstruction ? 'bg-amber-400 text-amber-900' :
                                'bg-blue-100 text-blue-800'
                              }`}>
                                {project.statut}
                              </div>
                              
                              <div className="space-y-2 text-sm text-gray-600 flex-grow">
                                <p className="line-clamp-3">{project.description}</p>
                                
                                <div className="bg-gray-50 p-2 rounded text-xs border border-gray-100">
                                  <p><strong>💰 {t.budget}:</strong> {project.budget}</p>
                                  <p><strong>🚀 {t.impact}:</strong> {project.impact}</p>
                                </div>
                              </div>
                              
                              <div className="mt-auto pt-3 border-t border-gray-100 text-xs text-gray-500 flex justify-between items-center">
                                <span className="truncate max-w-[70%]">🤝 {project.partenaires}</span>
                                <span className="italic text-gray-400">{project.source?.split('/')[0]}</span>
                              </div>
                            </div>
                          </div>
                        )})}
                      </div>
                    </CardContent>
                  </Card>
                </div>
              )}

              {/* World Bank Data360 Indicators */}
              {countryProfile.projections?.life_expectancy_2023 && (
                <div className="mb-4">
                  <Card className="shadow-2xl border-0 bg-gradient-to-br from-gray-900 to-gray-800">
                    <CardHeader className="bg-gradient-to-r from-blue-900/50 via-purple-900/30 to-pink-900/30 border-b border-blue-500/30">
                      <CardTitle className="text-xl font-bold text-blue-400 flex items-center gap-3">
                        <span className="text-2xl">🌐</span>
                        <span>{t.worldBankIndicators}</span>
                      </CardTitle>
                      <p className="text-sm text-gray-300 mt-1">
                        {t.officialData}
                      </p>
                    </CardHeader>
                    <CardContent className="pt-6 bg-gray-900/50">
                      {/* Section 1: People (Social) */}
                      <div className="mb-6">
                        <h4 className="text-lg font-bold text-pink-400 mb-4 flex items-center gap-2 border-b border-pink-500/30 pb-2">
                          <span className="text-2xl">👥</span>
                          <span>{t.socialIndicators}</span>
                        </h4>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                          <div className="bg-gradient-to-br from-green-900/80 to-emerald-800/60 p-4 rounded-xl border-2 border-green-500 shadow-lg shadow-green-500/20 transform hover:scale-105 transition-all">
                            <p className="text-xs font-bold text-green-300 mb-2 uppercase tracking-wide">🏥 {t.lifeExpectancy}</p>
                            <p className="text-3xl font-extrabold text-white drop-shadow-lg">
                              {countryProfile.projections.life_expectancy_2023}
                            </p>
                            <p className="text-xs text-green-200 mt-2 bg-green-950/50 rounded-full px-2 py-1">{t.years} (2023)</p>
                          </div>
                            <p className="text-xs text-gray-600">{t.years} (2023)</p>
                          </div>
                          
                          {countryProfile.projections.gini_index_2024 && (
                            <div className="bg-gradient-to-br from-orange-50 to-amber-50 p-3 rounded-lg border-l-4 border-orange-500">
                              <p className="text-xs font-semibold text-orange-700">📊 {t.giniIndex}</p>
                              <p className="text-2xl font-bold text-orange-600">
                                {parseFloat(countryProfile.projections.gini_index_2024).toFixed(1)}
                              </p>
                              <p className="text-xs text-gray-600">{t.outOf100} (2024)</p>
                            </div>
                          )}
                          
                          {countryProfile.projections.poverty_rate_3usd_2024 && (
                            <div className="bg-gradient-to-br from-red-50 to-rose-50 p-3 rounded-lg border-l-4 border-red-500">
                              <p className="text-xs font-semibold text-red-700">💰 {t.povertyRate}</p>
                              <p className="text-2xl font-bold text-red-600">
                                {parseFloat(countryProfile.projections.poverty_rate_3usd_2024).toFixed(1)}%
                              </p>
                              <p className="text-xs text-gray-600">{t.populationPercent} (2024)</p>
                            </div>
                          )}
                          
                          {countryProfile.projections.urban_population_pct_2024 && (
                            <div className="bg-gradient-to-br from-purple-50 to-indigo-50 p-3 rounded-lg border-l-4 border-purple-500">
                              <p className="text-xs font-semibold text-purple-700">🏙️ {t.urbanPopulation}</p>
                              <p className="text-2xl font-bold text-purple-600">
                                {parseFloat(countryProfile.projections.urban_population_pct_2024).toFixed(1)}%
                              </p>
                              <p className="text-xs text-gray-600">{t.ofTotal} (2024)</p>
                            </div>
                          )}
                        </div>
                      </div>

                      {/* Section 2: Digital & Infrastructure */}
                      <div className="mb-6">
                        <h4 className="font-bold text-gray-800 mb-3 flex items-center gap-2">
                          <span>💻</span>
                          <span>{t.digitalConnectivity}</span>
                        </h4>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                          {countryProfile.projections.internet_users_pct_2024 && (
                            <div className="bg-gradient-to-br from-blue-50 to-sky-50 p-3 rounded-lg border-l-4 border-blue-500">
                              <p className="text-xs font-semibold text-blue-700">🌐 {t.internetAccess}</p>
                              <p className="text-2xl font-bold text-blue-600">
                                {parseFloat(countryProfile.projections.internet_users_pct_2024).toFixed(1)}%
                              </p>
                              <p className="text-xs text-gray-600">{t.populationPercent} (2024)</p>
                            </div>
                          )}
                          
                          {countryProfile.projections.cybersecurity_index_2024 && (
                            <div className="bg-gradient-to-br from-indigo-50 to-purple-50 p-3 rounded-lg border-l-4 border-indigo-500">
                              <p className="text-xs font-semibold text-indigo-700">🔒 {t.cybersecurity}</p>
                              <p className="text-2xl font-bold text-indigo-600">
                                {parseFloat(countryProfile.projections.cybersecurity_index_2024).toFixed(1)}
                              </p>
                              <p className="text-xs text-gray-600">ITU GCI (2024)</p>
                            </div>
                          )}
                          
                          {countryProfile.projections.electricity_access_2022 && (
                            <div className="bg-gradient-to-br from-yellow-50 to-amber-50 p-3 rounded-lg border-l-4 border-yellow-500">
                              <p className="text-xs font-semibold text-yellow-700">⚡ {t.electricityAccess}</p>
                              <p className="text-2xl font-bold text-yellow-600">
                                {parseFloat(countryProfile.projections.electricity_access_2022).toFixed(0)}%
                              </p>
                              <p className="text-xs text-gray-600">{t.populationPercent} (2022)</p>
                            </div>
                          )}
                          
                          {countryProfile.projections.mobile_3g_coverage_2024 && (
                            <div className="bg-gradient-to-br from-teal-50 to-cyan-50 p-3 rounded-lg border-l-4 border-teal-500">
                              <p className="text-xs font-semibold text-teal-700">📱 {t.coverage3g}</p>
                              <p className="text-2xl font-bold text-teal-600">
                                {parseFloat(countryProfile.projections.mobile_3g_coverage_2024).toFixed(0)}%
                              </p>
                              <p className="text-xs text-gray-600">{t.populationPercent} (2024)</p>
                            </div>
                          )}
                        </div>
                      </div>

                      {/* Section 3: Environment & Gender */}
                      <div>
                        <h4 className="font-bold text-gray-800 mb-3 flex items-center gap-2">
                          <span>🌍</span>
                          <span>{t.environmentEquality}</span>
                        </h4>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                          {countryProfile.projections.female_labor_force_pct_2024 && (
                            <div className="bg-gradient-to-br from-pink-50 to-rose-50 p-3 rounded-lg border-l-4 border-pink-500">
                              <p className="text-xs font-semibold text-pink-700">👩‍💼 {t.workingWomen}</p>
                              <p className="text-2xl font-bold text-pink-600">
                                {parseFloat(countryProfile.projections.female_labor_force_pct_2024).toFixed(1)}%
                              </p>
                              <p className="text-xs text-gray-600">{t.femalePopulation} (2024)</p>
                            </div>
                          )}
                          
                          {countryProfile.projections.water_stress_2022 && (
                            <div className="bg-gradient-to-br from-blue-50 to-cyan-50 p-3 rounded-lg border-l-4 border-blue-500">
                              <p className="text-xs font-semibold text-blue-700">💧 {t.waterStress}</p>
                              <p className="text-2xl font-bold text-blue-600">
                                {parseFloat(countryProfile.projections.water_stress_2022).toFixed(1)}%
                              </p>
                              <p className="text-xs text-gray-600">{t.resources} (2022)</p>
                            </div>
                          )}
                          
                          {countryProfile.projections.ghg_emissions_mt_2022 && (
                            <div className="bg-gradient-to-br from-gray-50 to-slate-50 p-3 rounded-lg border-l-4 border-gray-500">
                              <p className="text-xs font-semibold text-gray-700">🏭 {t.ghgEmissions}</p>
                              <p className="text-2xl font-bold text-gray-600">
                                {parseFloat(countryProfile.projections.ghg_emissions_mt_2022).toFixed(1)}
                              </p>
                              <p className="text-xs text-gray-600">Mt CO₂e (2022)</p>
                            </div>
                          )}
                          
                          {countryProfile.projections.learning_poverty_2023 && (
                            <div className="bg-gradient-to-br from-violet-50 to-purple-50 p-3 rounded-lg border-l-4 border-violet-500">
                              <p className="text-xs font-semibold text-violet-700">📚 {t.learningPoverty}</p>
                              <p className="text-2xl font-bold text-violet-600">
                                {parseFloat(countryProfile.projections.learning_poverty_2023).toFixed(1)}%
                              </p>
                              <p className="text-xs text-gray-600">{t.children} (2023)</p>
                            </div>
                          )}
                        </div>
                      </div>
                      
                      {/* Source footer */}
                      <div className="mt-4 pt-4 border-t border-gray-200">
                        <p className="text-xs text-gray-500 text-center">
                          {t.source}: <strong>World Bank Data360</strong> - {t.officialData} • 
                          <a href="https://data360.worldbank.org" target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline ml-1">
                            data360.worldbank.org
                          </a>
                        </p>
                      </div>
                    </CardContent>
                  </Card>
                </div>
              )}

              {/* Infrastructure Section (AIDI 2025 & LPI 2023) */}
              {countryProfile.infrastructure_ranking && (
                <Card className="shadow-lg border-l-4 border-l-orange-500">
                  <CardHeader className="bg-gradient-to-r from-orange-50 to-yellow-50">
                    <CardTitle className="text-xl font-bold text-orange-700 flex items-center gap-2">
                      <span>🏗️</span>
                      <span>{t.infrastructurePerformance}</span>
                    </CardTitle>
                    <CardDescription className="font-semibold text-gray-700">
                      {t.continentalRanking}
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="pt-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="bg-purple-50 p-3 rounded-lg text-center">
                        <p className="text-xs font-semibold text-purple-700 mb-1">📊 {t.lpiScore}</p>
                        <p className="text-2xl font-bold text-purple-600">
                          {countryProfile.infrastructure_ranking.lpi_infrastructure_score}/5
                        </p>
                        <p className="text-xs text-purple-600 mt-1">{t.infrastructure}</p>
                        <div className="mt-2 text-xs bg-purple-100 rounded px-2 py-1">
                          {t.worldRank}: <strong>#{countryProfile.infrastructure_ranking.lpi_world_rank}</strong>
                        </div>
                      </div>
                      
                      <div className="bg-orange-50 p-3 rounded-lg text-center">
                        <p className="text-xs font-semibold text-orange-700 mb-1">🏗️ {t.aidiScore}</p>
                        <p className="text-2xl font-bold text-orange-600">
                          {countryProfile.infrastructure_ranking.aidi_transport_score}/100
                        </p>
                        <p className="text-xs text-orange-600 mt-1">{t.globalIndex}</p>
                        <div className="mt-2 text-xs bg-orange-100 rounded px-2 py-1">
                          {t.africaRank}: <strong>#{countryProfile.infrastructure_ranking.africa_rank}</strong>
                        </div>
                      </div>
                    </div>
                    
                    <div className="mt-4 bg-gray-50 p-3 rounded-lg">
                      <p className="text-xs text-gray-700">
                        <strong>IPL ({language === 'fr' ? 'Indice de Performance Logistique' : 'Logistics Performance Index'})</strong> : {t.lpiDescription}
                        <br />
                        <strong>AIDI (Africa Infrastructure Development Index)</strong> : {t.aidiDescription}
                      </p>
                    </div>
                  </CardContent>
                </Card>
              )}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}

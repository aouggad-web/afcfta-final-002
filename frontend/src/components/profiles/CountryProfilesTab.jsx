import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../ui/card';
import { Button } from '../ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Badge } from '../ui/badge';
import { toast } from '../../hooks/use-toast';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || '';
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
      worldBankIndicators: "Indicateurs Banque Mondiale (dernière année disponible)",
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
      aidiDescription: "Mesure composite du développement des infrastructures (Transport, Électricité, TIC, Eau) par la BAD.",
      customsTitle: "Administration des Douanes",
      customsSubtitle: "Dénomination officielle, coordonnées et principaux bureaux de passage",
      customsAdministration: "Dénomination officielle",
      customsAddress: "Adresse du siège",
      customsWebsite: "Site web officiel",
      customsPortOffices: "Bureaux portuaires principaux",
      customsAirOffices: "Bureaux aéroportuaires principaux",
      customsLandOffices: "Bureaux terrestres / frontières",
      customsVisitSite: "Visiter le site"
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
      worldBankIndicators: "World Bank Indicators (latest available year)",
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
      aidiDescription: "Composite measure of infrastructure development (Transport, Electricity, ICT, Water) by AfDB.",
      customsTitle: "Customs Administration",
      customsSubtitle: "Official denomination, contact details and main border offices",
      customsAdministration: "Official Denomination",
      customsAddress: "Headquarters Address",
      customsWebsite: "Official Website",
      customsPortOffices: "Main Port Offices",
      customsAirOffices: "Main Airport Offices",
      customsLandOffices: "Land Border Offices",
      customsVisitSite: "Visit website"
    }
  };

  const t = texts[language];

  useEffect(() => {
    fetchCountries();
  }, [language]);

  const hasOfficeData = (value) =>
    value && value !== 'N/A' && value !== 'N/A (pays enclavé)' && value !== 'N/A (État insulaire)';

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
      <Card className="shadow-xl border border-[rgba(212,175,55,0.2)] bg-[image:var(--card-grad)]">
        <CardHeader className="bg-[image:var(--card-head)] border-b border-[var(--afcfta-border)]">
          <CardTitle className="text-2xl font-bold text-[var(--gold)] flex items-center gap-2">
            <span>🌍</span>
            <span>{t.title}</span>
          </CardTitle>
          <CardDescription className="font-semibold text-[var(--afcfta-muted)]">
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
            <SelectTrigger className="text-lg font-semibold border border-[rgba(212,175,55,0.25)] focus:border-[rgba(212,175,55,0.5)]">
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
          <Card className="shadow-2xl border-0 bg-[image:var(--card-grad)]">
            <CardHeader className="bg-[image:var(--card-head)] border-b border-[color-mix(in_srgb,var(--gold)_30%,transparent)]">
              <CardTitle className="flex items-center space-x-3 text-2xl">
                <span className="text-5xl drop-shadow-lg">{getFlag(countryProfile.country_code)}</span>
                <div>
                  <span className="font-bold text-[var(--gold)] text-3xl">{countryProfile.country_name}</span>
                  <p className="text-sm text-[var(--text)] mt-1">{countryProfile.region}</p>
                </div>
              </CardTitle>
              <CardDescription className="text-lg font-semibold text-[var(--text)] flex items-center gap-4 mt-2">
                <span className="bg-[color-mix(in_srgb,var(--gold)_12%,var(--afcfta-card))] px-3 py-1 rounded-full text-[var(--gold)]">👥 {countryProfile.population_millions ? `${countryProfile.population_millions.toFixed(1)}M` : formatNumber(countryProfile.population)} {t.inhabitants}</span>
                <span className="bg-[color-mix(in_srgb,var(--success)_12%,var(--afcfta-card))] px-3 py-1 rounded-full text-[var(--success)]">🌍 UA Member</span>
              </CardDescription>
            </CardHeader>
            <CardContent className="pt-6 bg-[var(--afcfta-card2)]">
              {/* SECTION: Indicateurs Économiques Principaux */}
              <div className="mb-6">
                <h3 className="text-lg font-bold text-[var(--gold)] mb-4 flex items-center gap-2 border-b border-[color-mix(in_srgb,var(--gold)_30%,transparent)] pb-2">
                  <span className="text-2xl">💰</span> {language === 'fr' ? 'Indicateurs Économiques' : 'Economic Indicators'}
                </h3>
                <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                  {/* PIB Total */}
                  {countryProfile.gdp_usd != null && (
                    <div className="bg-[color-mix(in_srgb,var(--success)_12%,var(--afcfta-card))] p-4 rounded-xl border-2 border-[color-mix(in_srgb,var(--success)_30%,transparent)] shadow-lg shadow-emerald-500/20 text-center transform hover:scale-105 transition-all">
                      <p className="text-xs font-bold text-[var(--success)] mb-2 uppercase tracking-wide">💵 {t.totalGdp}</p>
                      <p className="text-3xl font-extrabold text-[var(--text)] drop-shadow-lg">
                        ${(countryProfile.gdp_usd / 1000000000).toFixed(1)}B
                      </p>
                      <p className="text-xs text-[var(--success)] mt-2 bg-[color-mix(in_srgb,var(--success)_12%,var(--afcfta-card))] rounded-full px-2 py-1">{t.rank}: #{countryProfile.projections?.africa_rank || 'N/A'}</p>
                    </div>
                  )}
                  
                  {/* PIB par Habitant */}
                  {countryProfile.gdp_per_capita != null && (
                    <div className="bg-[color-mix(in_srgb,var(--info)_12%,var(--afcfta-card))] p-4 rounded-xl border-2 border-[color-mix(in_srgb,var(--info)_30%,transparent)] shadow-lg shadow-blue-500/20 text-center transform hover:scale-105 transition-all">
                      <p className="text-xs font-bold text-[var(--info)] mb-2 uppercase tracking-wide">👤 {t.gdpPerCapita}</p>
                      <p className="text-3xl font-extrabold text-[var(--text)] drop-shadow-lg">
                        ${formatNumber(Math.round(countryProfile.gdp_per_capita))}
                      </p>
                      <p className="text-xs text-[var(--info)] mt-2 bg-[color-mix(in_srgb,var(--info)_12%,var(--afcfta-card))] rounded-full px-2 py-1">{t.perPerson}</p>
                    </div>
                  )}
                  
                  {/* Croissance 2024 */}
                  <div className="bg-[color-mix(in_srgb,var(--success)_12%,var(--afcfta-card))] p-4 rounded-xl border-2 border-[color-mix(in_srgb,var(--success)_30%,transparent)] shadow-lg shadow-teal-500/20 text-center transform hover:scale-105 transition-all">
                    <p className="text-xs font-bold text-[var(--success)] mb-2 uppercase tracking-wide">📈 {language === 'fr' ? 'Croissance' : 'Growth'} 2024</p>
                    <p className={`text-3xl font-extrabold drop-shadow-lg ${parseFloat(countryProfile.projections?.gdp_growth_forecast_2024) >= 5 ? 'text-[var(--success)]' : parseFloat(countryProfile.projections?.gdp_growth_forecast_2024) >= 3 ? 'text-[var(--text)]' : 'text-[var(--terra)]'}`}>
                      {countryProfile.projections?.gdp_growth_forecast_2024 || 'N/A'}
                    </p>
                    <p className="text-xs text-[var(--success)] mt-2 bg-[color-mix(in_srgb,var(--success)_12%,var(--afcfta-card))] rounded-full px-2 py-1">FMI 2024</p>
                  </div>
                  
                  {/* Projection 2025 */}
                  <div className="bg-[color-mix(in_srgb,var(--gold)_12%,var(--afcfta-card))] p-4 rounded-xl border-2 border-[color-mix(in_srgb,var(--gold)_30%,transparent)] shadow-lg shadow-amber-500/20 text-center transform hover:scale-105 transition-all">
                    <p className="text-xs font-bold text-[var(--gold)] mb-2 uppercase tracking-wide">🎯 Projection 2025</p>
                    <p className={`text-3xl font-extrabold drop-shadow-lg ${countryProfile.projections?.gdp_growth_projection_2025 && countryProfile.projections?.gdp_growth_projection_2025 !== 'N/A' ? 'text-[var(--text)]' : 'text-[var(--afcfta-muted)]'}`}>
                      {countryProfile.projections?.gdp_growth_projection_2025 || 'N/A'}
                    </p>
                    <p className="text-xs text-[var(--gold)] mt-2 bg-[color-mix(in_srgb,var(--gold)_12%,var(--afcfta-card))] rounded-full px-2 py-1">FMI/BM</p>
                  </div>
                  
                  {/* IDH */}
                  <div className="bg-[color-mix(in_srgb,var(--violet)_12%,var(--afcfta-card))] p-4 rounded-xl border-2 border-[color-mix(in_srgb,var(--violet)_30%,transparent)] shadow-lg shadow-purple-500/20 text-center transform hover:scale-105 transition-all">
                    <p className="text-xs font-bold text-[var(--violet)] mb-2 uppercase tracking-wide">📊 {t.hdi2024}</p>
                    <p className="text-3xl font-extrabold text-[var(--text)] drop-shadow-lg">
                      {countryProfile.hdi || countryProfile.projections?.development_index || 'N/A'}
                    </p>
                    <p className="text-xs text-[var(--violet)] mt-2 bg-[color-mix(in_srgb,var(--violet)_12%,var(--afcfta-card))] rounded-full px-2 py-1">{countryProfile.hdi_rank ? `Rang #${countryProfile.hdi_rank}` : 'PNUD'}</p>
                  </div>
                </div>
              </div>

              {/* SECTION: Indicateurs Sociaux */}
              <div className="mb-6">
                <h3 className="text-lg font-bold text-[var(--gold)] mb-4 flex items-center gap-2 border-b border-[color-mix(in_srgb,var(--gold)_30%,transparent)] pb-2">
                  <span className="text-2xl">👥</span> {language === 'fr' ? 'Indicateurs Sociaux' : 'Social Indicators'}
                </h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {/* Inflation */}
                  <div className={`p-4 rounded-xl border-2 shadow-lg text-center transform hover:scale-105 transition-all ${
                    countryProfile.inflation_rate != null && countryProfile.inflation_rate > 15 
                      ? 'bg-[color-mix(in_srgb,var(--danger)_12%,var(--afcfta-card))] border-[color-mix(in_srgb,var(--danger)_30%,transparent)] shadow-red-500/20' 
                      : countryProfile.inflation_rate != null && countryProfile.inflation_rate > 7 
                        ? 'bg-[color-mix(in_srgb,var(--terra)_12%,var(--afcfta-card))] border-[color-mix(in_srgb,var(--terra)_30%,transparent)] shadow-orange-500/20'
                        : 'bg-[color-mix(in_srgb,var(--success)_12%,var(--afcfta-card))] border-[color-mix(in_srgb,var(--success)_30%,transparent)] shadow-green-500/20'
                  }`}>
                    <p className="text-xs font-bold text-[var(--text-soft)] mb-2 uppercase tracking-wide">📈 Inflation 2024</p>
                    <p className="text-3xl font-extrabold text-[var(--text)] drop-shadow-lg">
                      {countryProfile.inflation_rate != null ? `${countryProfile.inflation_rate.toFixed(1)}%` : 'N/A'}
                    </p>
                    <p className="text-xs text-[var(--afcfta-muted)] mt-2 bg-[var(--overlay)] rounded-full px-2 py-1">FMI/BM</p>
                  </div>

                  {/* Chômage */}
                  <div className={`p-4 rounded-xl border-2 shadow-lg text-center transform hover:scale-105 transition-all ${
                    countryProfile.unemployment_rate != null && countryProfile.unemployment_rate > 25 
                      ? 'bg-[color-mix(in_srgb,var(--danger)_12%,var(--afcfta-card))] border-[color-mix(in_srgb,var(--danger)_30%,transparent)] shadow-red-500/20' 
                      : countryProfile.unemployment_rate != null && countryProfile.unemployment_rate > 15 
                        ? 'bg-[color-mix(in_srgb,var(--terra)_12%,var(--afcfta-card))] border-[color-mix(in_srgb,var(--terra)_30%,transparent)] shadow-orange-500/20'
                        : 'bg-[color-mix(in_srgb,var(--success)_12%,var(--afcfta-card))] border-[color-mix(in_srgb,var(--success)_30%,transparent)] shadow-green-500/20'
                  }`}>
                    <p className="text-xs font-bold text-[var(--text-soft)] mb-2 uppercase tracking-wide">👔 {language === 'fr' ? 'Chômage' : 'Unemployment'} 2024</p>
                    <p className="text-3xl font-extrabold text-[var(--text)] drop-shadow-lg">
                      {countryProfile.unemployment_rate != null ? `${countryProfile.unemployment_rate.toFixed(1)}%` : 'N/A'}
                    </p>
                    <p className="text-xs text-[var(--afcfta-muted)] mt-2 bg-[var(--overlay)] rounded-full px-2 py-1">OIT/BM</p>
                  </div>

                  {/* Population */}
                  <div className="bg-[color-mix(in_srgb,var(--atlantic)_12%,var(--afcfta-card))] p-4 rounded-xl border-2 border-[color-mix(in_srgb,var(--atlantic)_30%,transparent)] shadow-lg shadow-cyan-500/20 text-center transform hover:scale-105 transition-all">
                    <p className="text-xs font-bold text-[var(--atlantic)] mb-2 uppercase tracking-wide">👥 Population</p>
                    <p className="text-3xl font-extrabold text-[var(--text)] drop-shadow-lg">
                      {countryProfile.population_millions != null ? `${countryProfile.population_millions.toFixed(1)}M` : (countryProfile.population != null ? formatNumber(countryProfile.population) : 'N/A')}
                    </p>
                    <p className="text-xs text-[var(--atlantic)] mt-2 bg-[color-mix(in_srgb,var(--atlantic)_12%,var(--afcfta-card))] rounded-full px-2 py-1">2024</p>
                  </div>

                  {/* Rang IDH Mondial */}
                  <div className={`p-4 rounded-xl border-2 shadow-lg text-center transform hover:scale-105 transition-all ${
                    countryProfile.hdi_rank != null && countryProfile.hdi_rank <= 80 
                      ? 'bg-[color-mix(in_srgb,var(--success)_12%,var(--afcfta-card))] border-[color-mix(in_srgb,var(--success)_30%,transparent)] shadow-green-500/20' 
                      : countryProfile.hdi_rank != null && countryProfile.hdi_rank <= 120 
                        ? 'bg-[color-mix(in_srgb,var(--gold)_12%,var(--afcfta-card))] border-[color-mix(in_srgb,var(--gold)_30%,transparent)] shadow-amber-500/20'
                        : 'bg-[color-mix(in_srgb,var(--danger)_12%,var(--afcfta-card))] border-[color-mix(in_srgb,var(--danger)_30%,transparent)] shadow-red-500/20'
                  }`}>
                    <p className="text-xs font-bold text-[var(--text-soft)] mb-2 uppercase tracking-wide">🏆 {language === 'fr' ? 'Rang IDH' : 'HDI Rank'}</p>
                    <p className="text-3xl font-extrabold text-[var(--text)] drop-shadow-lg">
                      #{countryProfile.hdi_rank || 'N/A'}
                    </p>
                    <p className="text-xs text-[var(--afcfta-muted)] mt-2 bg-[var(--overlay)] rounded-full px-2 py-1">/193 pays</p>
                  </div>
                </div>
              </div>

              {/* SECTION DETTE PUBLIQUE */}
              {(countryProfile.total_debt_pct_gdp != null || countryProfile.external_debt_pct_gdp != null) && (
                <div className="mb-6">
                  <h3 className="text-lg font-bold text-[var(--gold)] mb-4 flex items-center gap-2 border-b border-[color-mix(in_srgb,var(--gold)_30%,transparent)] pb-2">
                    <span className="text-2xl">💳</span> {language === 'fr' ? 'Dette Publique 2024' : 'Public Debt 2024'}
                    <span className="text-xs font-normal text-[var(--afcfta-muted)] ml-2">(FMI/BM)</span>
                  </h3>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {/* Dette Totale */}
                    <div className={`p-4 rounded-xl border-2 shadow-lg text-center transform hover:scale-105 transition-all ${
                      countryProfile.total_debt_pct_gdp > 80 
                        ? 'bg-[color-mix(in_srgb,var(--danger)_12%,var(--afcfta-card))] border-[color-mix(in_srgb,var(--danger)_30%,transparent)] shadow-red-500/20' 
                        : countryProfile.total_debt_pct_gdp > 60 
                          ? 'bg-[color-mix(in_srgb,var(--terra)_12%,var(--afcfta-card))] border-[color-mix(in_srgb,var(--terra)_30%,transparent)] shadow-orange-500/20'
                          : countryProfile.total_debt_pct_gdp > 40 
                            ? 'bg-[color-mix(in_srgb,var(--gold)_12%,var(--afcfta-card))] border-[color-mix(in_srgb,var(--gold)_30%,transparent)] shadow-yellow-500/20'
                            : 'bg-[color-mix(in_srgb,var(--success)_12%,var(--afcfta-card))] border-[color-mix(in_srgb,var(--success)_30%,transparent)] shadow-green-500/20'
                    }`}>
                      <p className="text-xs font-bold text-[var(--text-soft)] mb-2 uppercase tracking-wide">📊 {language === 'fr' ? 'Dette Totale' : 'Total Debt'}</p>
                      <p className="text-3xl font-extrabold text-[var(--text)] drop-shadow-lg">
                        {countryProfile.total_debt_pct_gdp != null ? `${countryProfile.total_debt_pct_gdp.toFixed(1)}%` : 'N/A'}
                      </p>
                      <p className="text-xs text-[var(--afcfta-muted)] mt-2 bg-[var(--overlay)] rounded-full px-2 py-1">{language === 'fr' ? 'du PIB' : 'of GDP'}</p>
                    </div>

                    {/* Dette Extérieure */}
                    <div className="bg-[color-mix(in_srgb,var(--info)_12%,var(--afcfta-card))] p-4 rounded-xl border-2 border-[color-mix(in_srgb,var(--info)_30%,transparent)] shadow-lg shadow-blue-500/20 text-center transform hover:scale-105 transition-all">
                      <p className="text-xs font-bold text-[var(--info)] mb-2 uppercase tracking-wide">🌍 {language === 'fr' ? 'Dette Extérieure' : 'External Debt'}</p>
                      <p className="text-3xl font-extrabold text-[var(--text)] drop-shadow-lg">
                        {countryProfile.external_debt_pct_gdp != null ? `${countryProfile.external_debt_pct_gdp.toFixed(1)}%` : 'N/A'}
                      </p>
                      <p className="text-xs text-[var(--info)] mt-2 bg-[color-mix(in_srgb,var(--info)_12%,var(--afcfta-card))] rounded-full px-2 py-1">{language === 'fr' ? 'du PIB' : 'of GDP'}</p>
                      {countryProfile.external_debt_bn_usd != null && (
                        <p className="text-lg font-bold text-[var(--gold)] mt-2">
                          ${countryProfile.external_debt_bn_usd.toFixed(1)}B
                        </p>
                      )}
                    </div>

                    {/* Dette Intérieure */}
                    <div className="bg-[color-mix(in_srgb,var(--violet)_12%,var(--afcfta-card))] p-4 rounded-xl border-2 border-[color-mix(in_srgb,var(--violet)_30%,transparent)] shadow-lg shadow-purple-500/20 text-center transform hover:scale-105 transition-all">
                      <p className="text-xs font-bold text-[var(--violet)] mb-2 uppercase tracking-wide">🏠 {language === 'fr' ? 'Dette Intérieure' : 'Domestic Debt'}</p>
                      <p className="text-3xl font-extrabold text-[var(--text)] drop-shadow-lg">
                        {countryProfile.domestic_debt_pct_gdp != null ? `${countryProfile.domestic_debt_pct_gdp.toFixed(1)}%` : 'N/A'}
                      </p>
                      <p className="text-xs text-[var(--violet)] mt-2 bg-[color-mix(in_srgb,var(--violet)_12%,var(--afcfta-card))] rounded-full px-2 py-1">{language === 'fr' ? 'du PIB' : 'of GDP'}</p>
                    </div>

                    {/* Indicateur de Viabilité */}
                    <div className={`p-4 rounded-xl border-2 shadow-lg text-center transform hover:scale-105 transition-all ${
                      countryProfile.total_debt_pct_gdp <= 40 
                        ? 'bg-[color-mix(in_srgb,var(--success)_12%,var(--afcfta-card))] border-[color-mix(in_srgb,var(--success)_30%,transparent)] shadow-green-500/20' 
                        : countryProfile.total_debt_pct_gdp <= 60 
                          ? 'bg-[color-mix(in_srgb,var(--gold)_12%,var(--afcfta-card))] border-[color-mix(in_srgb,var(--gold)_30%,transparent)] shadow-amber-500/20'
                          : countryProfile.total_debt_pct_gdp <= 80 
                            ? 'bg-[color-mix(in_srgb,var(--terra)_12%,var(--afcfta-card))] border-[color-mix(in_srgb,var(--terra)_30%,transparent)] shadow-orange-500/20'
                            : 'bg-[color-mix(in_srgb,var(--danger)_12%,var(--afcfta-card))] border-[color-mix(in_srgb,var(--danger)_30%,transparent)] shadow-red-500/20'
                    }`}>
                      <p className="text-xs font-bold text-[var(--text-soft)] mb-2 uppercase tracking-wide">⚖️ {language === 'fr' ? 'Viabilité' : 'Sustainability'}</p>
                      <div className="flex justify-center items-center py-2">
                        {countryProfile.total_debt_pct_gdp <= 40 ? (
                          <span className="text-lg font-extrabold text-[var(--success)]">✓ FAIBLE RISQUE</span>
                        ) : countryProfile.total_debt_pct_gdp <= 60 ? (
                          <span className="text-lg font-extrabold text-[var(--gold)]">⚠ MODÉRÉ</span>
                        ) : countryProfile.total_debt_pct_gdp <= 80 ? (
                          <span className="text-lg font-extrabold text-[var(--terra)]">⚠ ÉLEVÉ</span>
                        ) : (
                          <span className="text-lg font-extrabold text-[var(--danger)]">🚨 CRITIQUE</span>
                        )}
                      </div>
                      <p className="text-xs text-[var(--afcfta-muted)] mt-2 bg-[var(--overlay)] rounded-full px-2 py-1">{language === 'fr' ? 'Seuil FMI: 60%' : 'IMF threshold: 60%'}</p>
                    </div>
                  </div>
                </div>
              )}

              {/* Gold Reserves & GAI 2025 */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                {/* Gold Reserves */}
                {countryProfile.projections?.gold_reserves_tonnes != null && (
                  <div className="bg-[color-mix(in_srgb,var(--gold)_8%,var(--afcfta-card))] p-4 rounded-lg shadow-lg border-2 border-[color-mix(in_srgb,var(--gold)_30%,transparent)]">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-2xl">🥇</span>
                      <p className="text-sm font-bold text-[var(--gold)]">{t.goldReserves}</p>
                    </div>
                    <p className="text-3xl font-bold text-[var(--gold)] mb-2">
                      {countryProfile.projections.gold_reserves_tonnes.toFixed(1)} <span className="text-xl">{t.tonnes}</span>
                    </p>
                    <div className="flex gap-3 text-xs">
                      <span className="bg-[color-mix(in_srgb,var(--gold)_12%,var(--afcfta-card))] text-[var(--gold)] px-2 py-1 rounded font-semibold">
                        🌍 {t.africa}: #{countryProfile.projections.gold_reserves_rank_africa}
                      </span>
                      {countryProfile.projections.gold_reserves_rank_global && (
                        <span className="bg-[color-mix(in_srgb,var(--gold)_12%,var(--afcfta-card))] text-[var(--gold)] px-2 py-1 rounded font-semibold">
                          🌎 {t.global}: #{countryProfile.projections.gold_reserves_rank_global}
                        </span>
                      )}
                    </div>
                  </div>
                )}

                {/* Global Attractiveness Index 2025 */}
                {countryProfile.projections?.gai_2025_score != null && (
                  <div className="bg-[color-mix(in_srgb,var(--violet)_8%,var(--afcfta-card))] p-4 rounded-lg shadow-lg border-2 border-[color-mix(in_srgb,var(--violet)_30%,transparent)]">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <span className="text-2xl">📊</span>
                        <p className="text-sm font-bold text-[var(--violet)]">{t.gaiTitle}</p>
                      </div>
                      <span className={`px-3 py-1 rounded-full font-bold text-sm ${
                        countryProfile.projections.gai_2025_rating === 'A' ? 'bg-[var(--success)] text-[var(--bg)]' :
                        countryProfile.projections.gai_2025_rating?.startsWith('A') ? 'bg-[var(--success)] text-[var(--bg)]' :
                        countryProfile.projections.gai_2025_rating?.startsWith('B') ? 'bg-[var(--info)] text-[var(--bg)]' :
                        countryProfile.projections.gai_2025_rating?.startsWith('C') ? 'bg-[var(--gold)] text-[var(--bg)]' :
                        countryProfile.projections.gai_2025_rating?.startsWith('D') ? 'bg-[var(--terra)] text-[var(--bg)]' :
                        'bg-[var(--danger)] text-[var(--bg)]'
                      }`}>
                        {countryProfile.projections.gai_2025_rating}
                      </span>
                    </div>
                    <div className="flex items-baseline gap-2 mb-2">
                      <p className="text-4xl font-bold text-[var(--violet)]">
                        {countryProfile.projections.gai_2025_score.toFixed(1)}
                      </p>
                      <span className={`text-sm font-semibold px-2 py-1 rounded ${
                        countryProfile.projections.gai_2025_trend === 'improving' ? 'bg-[color-mix(in_srgb,var(--success)_12%,var(--afcfta-card))] text-[var(--success)]' :
                        countryProfile.projections.gai_2025_trend === 'declining' ? 'bg-[color-mix(in_srgb,var(--danger)_12%,var(--afcfta-card))] text-[var(--danger)]' :
                        'bg-[var(--afcfta-card2)] text-[var(--text)]'
                      }`}>
                        {countryProfile.projections.gai_2025_trend === 'improving' ? `📈 ${t.improving}` :
                         countryProfile.projections.gai_2025_trend === 'declining' ? `📉 ${t.declining}` :
                         `➡️ ${t.stable}`}
                      </span>
                    </div>
                    {(countryProfile.projections.gai_2025_category_fr || countryProfile.projections.gai_2025_category_en) && (
                      <p className="text-sm font-semibold text-[var(--violet)] mb-2">
                        {language === 'fr'
                          ? countryProfile.projections.gai_2025_category_fr
                          : countryProfile.projections.gai_2025_category_en}
                      </p>
                    )}
                    <div className="flex gap-3 text-xs">
                      <span className="bg-[color-mix(in_srgb,var(--violet)_12%,var(--afcfta-card))] text-[var(--violet)] px-2 py-1 rounded font-semibold">
                        🌍 {t.africa}: #{countryProfile.projections.gai_2025_rank_africa}
                      </span>
                      <span className="bg-[color-mix(in_srgb,var(--violet)_12%,var(--afcfta-card))] text-[var(--violet)] px-2 py-1 rounded font-semibold">
                        🌎 {t.global}: #{countryProfile.projections.gai_2025_rank_global}
                      </span>
                    </div>
                  </div>
                )}
              </div>

              {/* SECTION: Perspectives FMI (croissance + inflation pluriannuelles) */}
              {countryProfile.projections?.imf_gdp_growth && (() => {
                const growth = countryProfile.projections.imf_gdp_growth || {};
                const inflation = countryProfile.projections.imf_inflation || {};
                const nowY = new Date().getFullYear();
                // Union des années des DEUX séries (une année peut n'exister que
                // pour l'inflation), sur tout l'horizon WEO disponible (réalisé
                // récent + projections, ~2024→2031).
                const years = Array.from(
                  new Set([...Object.keys(growth), ...Object.keys(inflation)])
                )
                  .map(Number)
                  .filter((y) => y >= nowY - 2 && y <= nowY + 5)
                  .sort((a, b) => a - b);
                if (!years.length) return null;
                return (
                  <div className="mb-6">
                    <h3 className="text-lg font-bold text-[var(--gold)] mb-4 flex items-center gap-2 border-b border-[color-mix(in_srgb,var(--gold)_30%,transparent)] pb-2">
                      <span className="text-2xl">🔮</span>
                      {language === 'fr' ? 'Perspectives FMI' : 'IMF Outlook'}
                    </h3>
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm border-collapse">
                        <thead>
                          <tr>
                            <th className="text-left p-2 text-[var(--afcfta-muted)] font-semibold">{language === 'fr' ? 'Indicateur' : 'Indicator'}</th>
                            {years.map((y) => (
                              <th key={y} className={`p-2 text-center font-bold ${y <= nowY ? 'text-[var(--text)]' : 'text-[var(--gold)]'}`}>
                                {y}{y > nowY ? ' *' : ''}
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          <tr className="border-t border-[var(--afcfta-border)]">
                            <td className="p-2 text-[var(--success)] font-semibold">📈 {language === 'fr' ? 'Croissance PIB' : 'GDP growth'}</td>
                            {years.map((y) => (
                              <td key={y} className="p-2 text-center text-[var(--text)] font-bold">
                                {growth[y] != null ? `${growth[y].toFixed(1)}%` : '—'}
                              </td>
                            ))}
                          </tr>
                          <tr className="border-t border-[var(--afcfta-border)]">
                            <td className="p-2 text-[var(--terra)] font-semibold">💰 {language === 'fr' ? 'Inflation' : 'Inflation'}</td>
                            {years.map((y) => (
                              <td key={y} className="p-2 text-center text-[var(--text)] font-bold">
                                {inflation[y] != null ? `${inflation[y].toFixed(1)}%` : '—'}
                              </td>
                            ))}
                          </tr>
                        </tbody>
                      </table>
                    </div>
                    <p className="text-xs text-[var(--afcfta-muted)] mt-2">
                      {language === 'fr' ? '* projection · ' : '* projection · '}
                      {countryProfile.projections.imf_source || 'FMI — WEO'}
                    </p>
                  </div>
                );
              })()}

              {/* Section Perspectives & Projets Structurants (Nouveau) */}
              {countryProfile.ongoing_projects && countryProfile.ongoing_projects.length > 0 && (
                <div className="mb-4">
                  <Card className="shadow-xl border-t-4 border-t-emerald-600">
                    <CardHeader className="bg-[color-mix(in_srgb,var(--success)_8%,var(--afcfta-card))]">
                      <CardTitle className="text-xl font-bold text-[var(--success)] flex items-center gap-2">
                        <span>🏗️</span>
                        <span>{t.structuringProjects}</span>
                      </CardTitle>
                      <CardDescription className="font-semibold text-[var(--text)]">
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
                            isOperational ? 'border-[color-mix(in_srgb,var(--success)_30%,transparent)] bg-[color-mix(in_srgb,var(--success)_8%,var(--afcfta-card))]' : 
                            isConstruction ? 'border-[color-mix(in_srgb,var(--gold)_30%,transparent)] bg-[color-mix(in_srgb,var(--gold)_8%,var(--afcfta-card))]' :
                            'border-[var(--afcfta-border)] bg-[var(--afcfta-card)]'
                          }`}>
                            <div className={`text-[var(--bg)] p-3 ${
                              isOperational ? 'bg-[var(--success)]' :
                              isConstruction ? 'bg-[var(--gold)]' :
                              'bg-[var(--success)]'
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
                                  isOperational ? 'bg-[color-mix(in_srgb,var(--success)_8%,var(--afcfta-card))] text-[var(--success)] border-[color-mix(in_srgb,var(--success)_30%,transparent)]' :
                                  'bg-[color-mix(in_srgb,var(--success)_8%,var(--afcfta-card))] text-[var(--success)] border-[color-mix(in_srgb,var(--success)_30%,transparent)]'
                                }`}>
                                  {project.secteur}
                                </Badge>
                                <span className={`text-xs font-bold px-2 py-1 rounded ${
                                  isOperational ? 'bg-[color-mix(in_srgb,var(--success)_12%,var(--afcfta-card))] text-[var(--success)]' :
                                  'bg-[var(--afcfta-card2)] text-[var(--afcfta-muted)]'
                                }`}>
                                  🏁 {project.echeance}
                                </span>
                              </div>
                              
                              {/* Statut bien visible */}
                              <div className={`px-3 py-2 rounded-lg text-sm font-bold text-center ${
                                isOperational ? 'bg-[var(--success)] text-[var(--bg)]' :
                                isConstruction ? 'bg-[var(--gold)] text-[var(--bg)]' :
                                'bg-[color-mix(in_srgb,var(--info)_8%,var(--afcfta-card))] text-[var(--info)]'
                              }`}>
                                {project.statut}
                              </div>
                              
                              <div className="space-y-2 text-sm text-[var(--afcfta-muted)] flex-grow">
                                <p className="line-clamp-3">{project.description}</p>
                                
                                <div className="bg-[var(--afcfta-card2)] p-2 rounded text-xs border border-[var(--afcfta-border)]">
                                  <p><strong>💰 {t.budget}:</strong> {project.budget}</p>
                                  <p><strong>🚀 {t.impact}:</strong> {project.impact}</p>
                                </div>
                              </div>
                              
                              <div className="mt-auto pt-3 border-t border-[var(--afcfta-border)] text-xs text-[var(--afcfta-muted)] flex justify-between items-center">
                                <span className="truncate max-w-[70%]">🤝 {project.partenaires}</span>
                                <span className="italic text-[var(--afcfta-muted)]">{project.source?.split('/')[0]}</span>
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
              {countryProfile.projections && (
                countryProfile.projections.life_expectancy_2023 != null ||
                countryProfile.projections.gini_index_2024 != null ||
                countryProfile.projections.poverty_rate_3usd_2024 != null ||
                countryProfile.projections.urban_population_pct_2024 != null ||
                countryProfile.projections.internet_users_pct_2024 != null ||
                countryProfile.projections.cybersecurity_index_2024 != null ||
                countryProfile.projections.electricity_access_2022 != null ||
                countryProfile.projections.mobile_3g_coverage_2024 != null ||
                countryProfile.projections.female_labor_force_pct_2024 != null ||
                countryProfile.projections.water_stress_2022 != null ||
                countryProfile.projections.ghg_emissions_mt_2022 != null ||
                countryProfile.projections.learning_poverty_2023 != null
              ) && (
                <div className="mb-4">
                  <Card className="shadow-2xl border-0 bg-[image:var(--card-grad)]">
                    <CardHeader className="bg-[image:var(--card-head)] border-b border-[color-mix(in_srgb,var(--info)_30%,transparent)]">
                      <CardTitle className="text-xl font-bold text-[var(--info)] flex items-center gap-3">
                        <span className="text-2xl">🌐</span>
                        <span>{t.worldBankIndicators}</span>
                      </CardTitle>
                      <p className="text-sm text-[var(--text)] mt-1">
                        {t.officialData}
                      </p>
                    </CardHeader>
                    <CardContent className="pt-6 bg-[var(--afcfta-card2)]">
                      {/* Section 1: People (Social) */}
                      <div className="mb-6">
                        <h4 className="text-lg font-bold text-[var(--danger)] mb-4 flex items-center gap-2 border-b border-[color-mix(in_srgb,var(--danger)_30%,transparent)] pb-2">
                          <span className="text-2xl">👥</span>
                          <span>{t.socialIndicators}</span>
                        </h4>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                          <div className="bg-[color-mix(in_srgb,var(--success)_12%,var(--afcfta-card))] p-4 rounded-xl border-2 border-[color-mix(in_srgb,var(--success)_30%,transparent)] shadow-lg shadow-green-500/20 transform hover:scale-105 transition-all">
                            <p className="text-xs font-bold text-[var(--success)] mb-2 uppercase tracking-wide">🏥 {t.lifeExpectancy}</p>
                            <p className="text-3xl font-extrabold text-[var(--text)] drop-shadow-lg">
                              {countryProfile.projections.life_expectancy_2023 != null ? parseFloat(countryProfile.projections.life_expectancy_2023).toFixed(1) : 'N/A'}
                            </p>
                            <p className="text-xs text-[var(--success)] mt-2 bg-[color-mix(in_srgb,var(--success)_12%,var(--afcfta-card))] rounded-full px-2 py-1">{t.years} ({countryProfile.projections.life_expectancy_2023_year ?? 2023})</p>
                          </div>
                          
                          {countryProfile.projections.gini_index_2024 != null && (
                            <div className="bg-[color-mix(in_srgb,var(--terra)_12%,var(--afcfta-card))] p-4 rounded-xl border-2 border-[color-mix(in_srgb,var(--terra)_30%,transparent)] shadow-lg shadow-orange-500/20 transform hover:scale-105 transition-all">
                              <p className="text-xs font-bold text-[var(--terra)] mb-2 uppercase tracking-wide">📊 {t.giniIndex}</p>
                              <p className="text-3xl font-extrabold text-[var(--text)] drop-shadow-lg">
                                {parseFloat(countryProfile.projections.gini_index_2024).toFixed(1)}
                              </p>
                              <p className="text-xs text-[var(--terra)] mt-2 bg-[color-mix(in_srgb,var(--terra)_12%,var(--afcfta-card))] rounded-full px-2 py-1">{t.outOf100} ({countryProfile.projections.gini_index_2024_year ?? 2024})</p>
                            </div>
                          )}
                          
                          {countryProfile.projections.poverty_rate_3usd_2024 !== undefined && countryProfile.projections.poverty_rate_3usd_2024 !== null && (
                            <div className="bg-[color-mix(in_srgb,var(--danger)_12%,var(--afcfta-card))] p-4 rounded-xl border-2 border-[color-mix(in_srgb,var(--danger)_30%,transparent)] shadow-lg shadow-red-500/20 transform hover:scale-105 transition-all">
                              <p className="text-xs font-bold text-[var(--danger)] mb-2 uppercase tracking-wide">💰 {t.povertyRate}</p>
                              <p className="text-3xl font-extrabold text-[var(--text)] drop-shadow-lg">
                                {parseFloat(countryProfile.projections.poverty_rate_3usd_2024).toFixed(1)}%
                              </p>
                              <p className="text-xs text-[var(--danger)] mt-2 bg-[color-mix(in_srgb,var(--danger)_12%,var(--afcfta-card))] rounded-full px-2 py-1">{t.populationPercent} ({countryProfile.projections.poverty_rate_3usd_2024_year ?? 2024})</p>
                            </div>
                          )}
                          
                          {countryProfile.projections.urban_population_pct_2024 != null && (
                            <div className="bg-[color-mix(in_srgb,var(--violet)_12%,var(--afcfta-card))] p-4 rounded-xl border-2 border-[color-mix(in_srgb,var(--violet)_30%,transparent)] shadow-lg shadow-purple-500/20 transform hover:scale-105 transition-all">
                              <p className="text-xs font-bold text-[var(--violet)] mb-2 uppercase tracking-wide">🏙️ {t.urbanPopulation}</p>
                              <p className="text-3xl font-extrabold text-[var(--text)] drop-shadow-lg">
                                {parseFloat(countryProfile.projections.urban_population_pct_2024).toFixed(1)}%
                              </p>
                              <p className="text-xs text-[var(--violet)] mt-2 bg-[color-mix(in_srgb,var(--violet)_12%,var(--afcfta-card))] rounded-full px-2 py-1">{t.ofTotal} ({countryProfile.projections.urban_population_pct_2024_year ?? 2024})</p>
                            </div>
                          )}
                        </div>
                      </div>

                      {/* Section 2: Digital & Infrastructure */}
                      <div className="mb-6">
                        <h4 className="text-lg font-bold text-[var(--atlantic)] mb-4 flex items-center gap-2 border-b border-[color-mix(in_srgb,var(--atlantic)_30%,transparent)] pb-2">
                          <span className="text-2xl">💻</span>
                          <span>{t.digitalConnectivity}</span>
                        </h4>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                          {countryProfile.projections.internet_users_pct_2024 != null && (
                            <div className="bg-[color-mix(in_srgb,var(--info)_12%,var(--afcfta-card))] p-4 rounded-xl border-2 border-[color-mix(in_srgb,var(--info)_30%,transparent)] shadow-lg shadow-blue-500/20 transform hover:scale-105 transition-all">
                              <p className="text-xs font-bold text-[var(--info)] mb-2 uppercase tracking-wide">🌐 {t.internetAccess}</p>
                              <p className="text-3xl font-extrabold text-[var(--text)] drop-shadow-lg">
                                {parseFloat(countryProfile.projections.internet_users_pct_2024).toFixed(1)}%
                              </p>
                              <p className="text-xs text-[var(--info)] mt-2 bg-[color-mix(in_srgb,var(--info)_12%,var(--afcfta-card))] rounded-full px-2 py-1">{t.populationPercent} ({countryProfile.projections.internet_users_pct_2024_year ?? 2024})</p>
                            </div>
                          )}
                          
                          {countryProfile.projections.cybersecurity_index_2024 != null && (
                            <div className="bg-[color-mix(in_srgb,var(--violet)_12%,var(--afcfta-card))] p-4 rounded-xl border-2 border-[color-mix(in_srgb,var(--violet)_30%,transparent)] shadow-lg shadow-indigo-500/20 transform hover:scale-105 transition-all">
                              <p className="text-xs font-bold text-[var(--violet)] mb-2 uppercase tracking-wide">🔒 {t.cybersecurity}</p>
                              <p className="text-3xl font-extrabold text-[var(--text)] drop-shadow-lg">
                                {parseFloat(countryProfile.projections.cybersecurity_index_2024).toFixed(1)}
                              </p>
                              <p className="text-xs text-[var(--violet)] mt-2 bg-[color-mix(in_srgb,var(--violet)_12%,var(--afcfta-card))] rounded-full px-2 py-1">ITU GCI (2024)</p>
                            </div>
                          )}
                          
                          {countryProfile.projections.electricity_access_2022 != null && (
                            <div className="bg-[color-mix(in_srgb,var(--gold)_12%,var(--afcfta-card))] p-4 rounded-xl border-2 border-[color-mix(in_srgb,var(--gold)_30%,transparent)] shadow-lg shadow-yellow-500/20 transform hover:scale-105 transition-all">
                              <p className="text-xs font-bold text-[var(--gold)] mb-2 uppercase tracking-wide">⚡ {t.electricityAccess}</p>
                              <p className="text-3xl font-extrabold text-[var(--text)] drop-shadow-lg">
                                {parseFloat(countryProfile.projections.electricity_access_2022).toFixed(0)}%
                              </p>
                              <p className="text-xs text-[var(--gold)] mt-2 bg-[color-mix(in_srgb,var(--gold)_12%,var(--afcfta-card))] rounded-full px-2 py-1">{t.populationPercent} ({countryProfile.projections.electricity_access_2022_year ?? 2022})</p>
                            </div>
                          )}
                          
                          {countryProfile.projections.mobile_3g_coverage_2024 != null && (
                            <div className="bg-[color-mix(in_srgb,var(--success)_12%,var(--afcfta-card))] p-4 rounded-xl border-2 border-[color-mix(in_srgb,var(--success)_30%,transparent)] shadow-lg shadow-teal-500/20 transform hover:scale-105 transition-all">
                              <p className="text-xs font-bold text-[var(--success)] mb-2 uppercase tracking-wide">📱 {t.coverage3g}</p>
                              <p className="text-3xl font-extrabold text-[var(--text)] drop-shadow-lg">
                                {parseFloat(countryProfile.projections.mobile_3g_coverage_2024).toFixed(0)}%
                              </p>
                              <p className="text-xs text-[var(--success)] mt-2 bg-[color-mix(in_srgb,var(--success)_12%,var(--afcfta-card))] rounded-full px-2 py-1">{t.populationPercent} (2024)</p>
                            </div>
                          )}
                        </div>
                      </div>

                      {/* Section 3: Environment & Gender */}
                      <div>
                        <h4 className="text-lg font-bold text-[var(--success)] mb-4 flex items-center gap-2 border-b border-[color-mix(in_srgb,var(--success)_30%,transparent)] pb-2">
                          <span className="text-2xl">🌍</span>
                          <span>{t.environmentEquality}</span>
                        </h4>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                          {countryProfile.projections.female_labor_force_pct_2024 != null && (
                            <div className="bg-[color-mix(in_srgb,var(--danger)_12%,var(--afcfta-card))] p-4 rounded-xl border-2 border-[color-mix(in_srgb,var(--danger)_30%,transparent)] shadow-lg shadow-pink-500/20 transform hover:scale-105 transition-all">
                              <p className="text-xs font-bold text-[var(--danger)] mb-2 uppercase tracking-wide">👩‍💼 {t.workingWomen}</p>
                              <p className="text-3xl font-extrabold text-[var(--text)] drop-shadow-lg">
                                {parseFloat(countryProfile.projections.female_labor_force_pct_2024).toFixed(1)}%
                              </p>
                              <p className="text-xs text-[var(--danger)] mt-2 bg-[color-mix(in_srgb,var(--danger)_12%,var(--afcfta-card))] rounded-full px-2 py-1">{t.femalePopulation} ({countryProfile.projections.female_labor_force_pct_2024_year ?? 2024})</p>
                            </div>
                          )}
                          
                          {countryProfile.projections.water_stress_2022 != null && (
                            <div className="bg-[color-mix(in_srgb,var(--info)_12%,var(--afcfta-card))] p-4 rounded-xl border-2 border-[color-mix(in_srgb,var(--info)_30%,transparent)] shadow-lg shadow-blue-500/20 transform hover:scale-105 transition-all">
                              <p className="text-xs font-bold text-[var(--info)] mb-2 uppercase tracking-wide">💧 {t.waterStress}</p>
                              <p className="text-3xl font-extrabold text-[var(--text)] drop-shadow-lg">
                                {parseFloat(countryProfile.projections.water_stress_2022).toFixed(1)}%
                              </p>
                              <p className="text-xs text-[var(--info)] mt-2 bg-[color-mix(in_srgb,var(--info)_12%,var(--afcfta-card))] rounded-full px-2 py-1">{t.resources} (2022)</p>
                            </div>
                          )}
                          
                          {countryProfile.projections.ghg_emissions_mt_2022 != null && (
                            <div className="bg-[image:var(--card-grad)] p-4 rounded-xl border-2 border-[var(--afcfta-border)] shadow-lg shadow-gray-500/20 transform hover:scale-105 transition-all">
                              <p className="text-xs font-bold text-[var(--text)] mb-2 uppercase tracking-wide">🏭 {t.ghgEmissions}</p>
                              <p className="text-3xl font-extrabold text-[var(--text)] drop-shadow-lg">
                                {parseFloat(countryProfile.projections.ghg_emissions_mt_2022).toFixed(1)}
                              </p>
                              <p className="text-xs text-[var(--text)] mt-2 bg-[var(--afcfta-card2)] rounded-full px-2 py-1">Mt CO₂e (2022)</p>
                            </div>
                          )}
                          
                          {countryProfile.projections.learning_poverty_2023 != null && (
                            <div className="bg-[color-mix(in_srgb,var(--violet)_12%,var(--afcfta-card))] p-4 rounded-xl border-2 border-[color-mix(in_srgb,var(--violet)_30%,transparent)] shadow-lg shadow-violet-500/20 transform hover:scale-105 transition-all">
                              <p className="text-xs font-bold text-[var(--violet)] mb-2 uppercase tracking-wide">📚 {t.learningPoverty}</p>
                              <p className="text-3xl font-extrabold text-[var(--text)] drop-shadow-lg">
                                {parseFloat(countryProfile.projections.learning_poverty_2023).toFixed(1)}%
                              </p>
                              <p className="text-xs text-[var(--violet)] mt-2 bg-[color-mix(in_srgb,var(--violet)_12%,var(--afcfta-card))] rounded-full px-2 py-1">{t.children} (2023)</p>
                            </div>
                          )}
                        </div>
                      </div>
                      
                      {/* Source footer */}
                      <div className="mt-6 pt-4 border-t border-[var(--afcfta-border)]">
                        <p className="text-xs text-[var(--afcfta-muted)] text-center">
                          {t.source}: <strong className="text-[var(--info)]">World Bank Data360</strong> - {t.officialData} • 
                          <a href="https://data360.worldbank.org" target="_blank" rel="noopener noreferrer" className="text-[var(--info)] hover:underline ml-1">
                            data360.worldbank.org
                          </a>
                        </p>
                      </div>
                    </CardContent>
                  </Card>
                </div>
              )}

              {/* Infrastructure Section (AIDI 2025 & LPI 2023) */}
              {countryProfile.infrastructure_ranking && Object.keys(countryProfile.infrastructure_ranking).length > 0 && (
                <Card className="shadow-2xl border-0 bg-[image:var(--card-grad)]">
                  <CardHeader className="bg-[image:var(--card-head)] border-b border-[color-mix(in_srgb,var(--terra)_30%,transparent)]">
                    <CardTitle className="text-xl font-bold text-[var(--terra)] flex items-center gap-2">
                      <span>🏗️</span>
                      <span>{t.infrastructurePerformance}</span>
                    </CardTitle>
                    <CardDescription className="font-semibold text-[var(--text)]">
                      {t.continentalRanking}
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="pt-6 bg-[var(--afcfta-card2)]">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="bg-[color-mix(in_srgb,var(--violet)_12%,var(--afcfta-card))] p-4 rounded-xl border-2 border-[color-mix(in_srgb,var(--violet)_30%,transparent)] shadow-lg shadow-purple-500/20 text-center transform hover:scale-105 transition-all">
                        <p className="text-xs font-bold text-[var(--violet)] mb-2 uppercase tracking-wide">📊 {t.lpiScore}</p>
                        <p className="text-3xl font-extrabold text-[var(--text)] drop-shadow-lg">
                          {countryProfile.infrastructure_ranking.lpi_infrastructure_score}/5
                        </p>
                        <p className="text-xs text-[var(--violet)] mt-2">{t.infrastructure}</p>
                        <div className="mt-2 text-xs bg-[color-mix(in_srgb,var(--violet)_12%,var(--afcfta-card))] rounded-full px-3 py-1">
                          {t.worldRank}: <strong className="text-[var(--text)]">#{countryProfile.infrastructure_ranking.lpi_world_rank}</strong>
                        </div>
                      </div>
                      
                      <div className="bg-[color-mix(in_srgb,var(--terra)_12%,var(--afcfta-card))] p-4 rounded-xl border-2 border-[color-mix(in_srgb,var(--terra)_30%,transparent)] shadow-lg shadow-orange-500/20 text-center transform hover:scale-105 transition-all">
                        <p className="text-xs font-bold text-[var(--terra)] mb-2 uppercase tracking-wide">🏗️ {t.aidiScore}</p>
                        <p className="text-3xl font-extrabold text-[var(--text)] drop-shadow-lg">
                          {countryProfile.infrastructure_ranking.aidi_transport_score}/100
                        </p>
                        <p className="text-xs text-[var(--terra)] mt-2">{t.globalIndex}</p>
                        <div className="mt-2 text-xs bg-[color-mix(in_srgb,var(--terra)_12%,var(--afcfta-card))] rounded-full px-3 py-1">
                          {t.africaRank}: <strong className="text-[var(--text)]">#{countryProfile.infrastructure_ranking.africa_rank}</strong>
                        </div>
                      </div>
                    </div>
                    
                    <div className="mt-6 bg-[var(--afcfta-card2)] p-4 rounded-xl border border-[var(--afcfta-border)]">
                      <p className="text-xs text-[var(--text)]">
                        <strong className="text-[var(--info)]">IPL ({language === 'fr' ? 'Indice de Performance Logistique' : 'Logistics Performance Index'})</strong> : {t.lpiDescription}
                        <br />
                        <strong className="text-[var(--terra)]">AIDI (Africa Infrastructure Development Index)</strong> : {t.aidiDescription}
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

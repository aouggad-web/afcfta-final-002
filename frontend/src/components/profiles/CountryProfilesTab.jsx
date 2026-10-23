import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Search } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../ui/card';
import { Button } from '../ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Badge } from '../ui/badge';
import { toast } from '../../hooks/use-toast';
import { chiffres, estAnglais, montant, montantUnite } from '../../utils/nombres';

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

// Pourcentage localisé (« 3,8 % » / « 3.8% »).
const pct = (value, language) => {
  if (value == null) return null;
  const n = chiffres(value, language, 1);
  return estAnglais(language) ? `${n}%` : `${n}\u00a0%`;
};

const meta = (...parts) => parts.filter(Boolean).join(' · ');

// Recherche de pays : sans accents ni casse (« cote d'ivoire », « ethiopie »).
const sansAccents = (s) => String(s || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();

// Pays de l'UEMOA : réserves de change mises en commun à la BCEAO, sans série
// nationale à la Banque mondiale.
const UEMOA = ['BEN', 'BFA', 'CIV', 'GNB', 'MLI', 'NER', 'SEN', 'TGO'];

const growthTone = (v) => (v == null ? 'afcfta-muted' : v >= 5 ? 'success' : v >= 3 ? 'info' : 'terra');
const inflationTone = (v) => (v == null ? 'afcfta-muted' : v > 15 ? 'danger' : v > 7 ? 'terra' : 'success');
const unemploymentTone = (v) => (v == null ? 'afcfta-muted' : v > 25 ? 'danger' : v > 15 ? 'terra' : 'success');
const debtTone = (v) => (v == null ? 'afcfta-muted' : v > 80 ? 'danger' : v > 60 ? 'terra' : v > 40 ? 'gold' : 'success');
const debtLabel = (v, t) => (v <= 40 ? t.debtLow : v <= 60 ? t.debtModerate : v <= 80 ? t.debtHigh : t.debtCritical);

// Tuile d'indicateur : libellé (avec l'année réelle de la donnée), valeur,
// ligne de source et, si disponible, rang africain (#rang/N). La teinte passe
// par la variable CSS --tone, pour garder des classes Tailwind littérales.
function StatTile({ label, value, meta: metaText, tone = 'afcfta-muted', rank, rankLabel }) {
  const rankText = rank ? `${rankLabel} ${rank.year} : ${rank.rank}/${rank.total}` : null;
  return (
    <div
      style={{ '--tone': `var(--${tone})` }}
      className="min-w-0 rounded-xl border border-[color-mix(in_srgb,var(--tone)_30%,transparent)] bg-[color-mix(in_srgb,var(--tone)_8%,var(--afcfta-card))] p-3 sm:p-4"
    >
      <div className="flex flex-wrap items-start justify-between gap-x-2 gap-y-1">
        <p className="text-xs font-semibold text-[var(--tone)]">{label}</p>
        {rank && (
          <span
            title={rankText}
            aria-label={rankText}
            className="shrink-0 rounded-full border border-[color-mix(in_srgb,var(--tone)_55%,transparent)] px-2 py-0.5 text-[11px] font-bold tabular-nums text-[var(--tone)]"
          >
            #{rank.rank}/{rank.total}
          </span>
        )}
      </div>
      <p className="mt-1 text-lg sm:text-2xl font-bold tabular-nums text-[var(--text)] [overflow-wrap:anywhere]">{value ?? 'N/A'}</p>
      {metaText && <p className="mt-1 text-xs text-[var(--afcfta-muted)]">{metaText}</p>}
    </div>
  );
}

// Panneau opaque posé sur le zellige du cadre : le texte n'est jamais
// directement sur le pavage.
const PANEL = 'rounded-xl border border-[var(--afcfta-border)] bg-[var(--afcfta-card)] p-3 md:p-5 shadow-sm';

function SectionTitle({ children }) {
  return (
    <h3 className="text-base font-bold text-[var(--gold)] mb-3 pb-2 border-b border-[color-mix(in_srgb,var(--gold)_30%,transparent)]">
      {children}
    </h3>
  );
}

export default function CountryProfilesTab({ language = 'fr' }) {
  const [countries, setCountries] = useState([]);
  const [selectedCountry, setSelectedCountry] = useState('');
  const [countryProfile, setCountryProfile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [query, setQuery] = useState('');
  const [searchOpen, setSearchOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(0);

  const texts = {
    fr: {
      title: "Profils Économiques des Pays",
      description: "Sélectionnez un pays pour consulter son profil économique complet, ses infrastructures et ses projets structurants (2025-2030)",
      selectPlaceholder: "Choisir un pays dans la liste",
      searchLabel: "Rechercher un pays",
      searchPlaceholder: "Rechercher un pays (nom ou code ISO)…",
      noCountryFound: "Aucun pays trouvé",
      error: "Erreur",
      loadError: "Impossible de charger la liste des pays",
      population: "Population",
      inhabitants: "habitants",
      totalGdp: "PIB total",
      gdpPerCapita: "PIB/habitant",
      hdiDesc: "Indice Dév. Humain",
      auMember: "Membre de l'UA",
      macroIndicators: "Indicateurs macroéconomiques",
      growth: "Croissance",
      projection: "Projection",
      inflation: "Inflation",
      unemployment: "Chômage",
      wbSource: "Banque mondiale",
      iloWb: "OIT / Banque mondiale",
      imfWeo: "FMI, WEO",
      publicFinance: "Dette, réserves de change & développement humain",
      publicDebt: "Dette publique",
      ofGdp: "du PIB",
      externalDebt: "Dette extérieure",
      ofGni: "du RNB",
      idsSource: "Banque mondiale (IDS)",
      fxReserves: "Réserves de change",
      importMonths: "mois d'importations",
      reservesPooled: "Mises en commun à la BCEAO (UEMOA)",
      hdi: "IDH",
      debtLow: "risque faible",
      debtModerate: "risque modéré",
      debtHigh: "risque élevé",
      debtCritical: "risque critique",
      loading: "Chargement du profil…",
      profileError: "Impossible de charger le profil de ce pays",
      inAfrica: "en Afrique",
      rankLegend: "#rang/N : rang parmi les pays africains qui publient l'indicateur pour la même année — 1 = valeur la plus élevée ; pour l'inflation, le chômage et la dette, 1 = la plus faible.",
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
      officialData: "Données officielles de la Banque mondiale — année indiquée sur chaque indicateur",
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
      electricityAccess: "Accès électricité",
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
      continentalRanking: "Classement continental (AIDI 2025) et Indice de performance logistique (Banque mondiale)",
      lpiScore: "Score IPL (LPI)",
      infrastructure: "Infrastructure",
      worldRank: "Rang mondial",
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
      selectPlaceholder: "Choose a country from the list",
      searchLabel: "Search for a country",
      searchPlaceholder: "Search for a country (name or ISO code)…",
      noCountryFound: "No country found",
      error: "Error",
      loadError: "Unable to load country list",
      population: "Population",
      inhabitants: "inhabitants",
      totalGdp: "Total GDP",
      gdpPerCapita: "GDP/capita",
      hdiDesc: "Human Dev. Index",
      auMember: "AU member",
      macroIndicators: "Macroeconomic indicators",
      growth: "Growth",
      projection: "Projection",
      inflation: "Inflation",
      unemployment: "Unemployment",
      wbSource: "World Bank",
      iloWb: "ILO / World Bank",
      imfWeo: "IMF, WEO",
      publicFinance: "Debt, FX reserves & human development",
      publicDebt: "Public debt",
      ofGdp: "of GDP",
      externalDebt: "External debt",
      ofGni: "of GNI",
      idsSource: "World Bank (IDS)",
      fxReserves: "FX reserves",
      importMonths: "months of imports",
      reservesPooled: "Pooled at the BCEAO (WAEMU)",
      hdi: "HDI",
      debtLow: "low risk",
      debtModerate: "moderate risk",
      debtHigh: "high risk",
      debtCritical: "critical risk",
      loading: "Loading profile…",
      profileError: "Unable to load this country's profile",
      inAfrica: "in Africa",
      rankLegend: "#rank/N: rank among African countries reporting the indicator for the same year — 1 = highest value; for inflation, unemployment and debt, 1 = lowest.",
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
      officialData: "Official World Bank data — year shown on each indicator",
      socialIndicators: "Social Indicators",
      lifeExpectancy: "Life expectancy",
      years: "years",
      giniIndex: "Gini index",
      outOf100: "out of 100",
      povertyRate: "Poverty ($3/day)",
      populationPercent: "population",
      urbanPopulation: "Urban population",
      ofTotal: "of total",
      digitalConnectivity: "Digital & Connectivity",
      internetAccess: "Internet access",
      cybersecurity: "Cybersecurity",
      electricityAccess: "Electricity access",
      coverage3g: "3G Coverage",
      environmentEquality: "Environment & Equality",
      workingWomen: "Working women",
      femalePopulation: "female pop.",
      waterStress: "Water stress",
      resources: "resources",
      ghgEmissions: "GHG emissions",
      learningPoverty: "Learning poverty",
      children: "children",
      source: "Source",
      infrastructurePerformance: "Infrastructure & Logistics Performance",
      continentalRanking: "Continental ranking (AIDI 2025) and Logistics Performance Index (World Bank)",
      lpiScore: "LPI score",
      infrastructure: "Infrastructure",
      worldRank: "World Rank",
      aidiScore: "AIDI 2025 score",
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
  const proj = countryProfile?.projections || {};
  const years = proj.indicator_years || {};
  const rankings = countryProfile?.african_rankings || {};
  // Props de rang africain d'un indice, à étaler sur une StatTile.
  const rankOf = (key) => (rankings[key] ? { rank: rankings[key], rankLabel: t.africaRank } : {});
  const extDebt = proj.external_debt;
  const extDebtUsd = extDebt?.usd != null ? montantUnite(extDebt.usd / 1000000000, 'B', language, 1) : null;
  const reserves = proj.reserves;

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

  // Pays dont le nom contient la saisie, ou dont le code ISO2/ISO3 est la
  // saisie ; les noms qui commencent par la saisie d'abord.
  const q = sansAccents(query.trim());
  const matches = q
    ? countries
        .filter((c) => sansAccents(c.name).includes(q) || [c.code, c.iso2].some((code) => sansAccents(code) === q))
        .sort((a, b) => sansAccents(b.name).startsWith(q) - sansAccents(a.name).startsWith(q))
        .slice(0, 8)
    : [];
  const showMatches = searchOpen && q !== '';

  const selectCountry = (code) => {
    setSelectedCountry(code);
    fetchCountryProfile(code);
    setQuery('');
    setSearchOpen(false);
  };

  const onSearchKeyDown = (e) => {
    if (e.key === 'ArrowDown' && matches.length) {
      e.preventDefault();
      setSearchOpen(true);
      setActiveIndex((i) => Math.min(i + 1, matches.length - 1));
    } else if (e.key === 'ArrowUp' && matches.length) {
      e.preventDefault();
      setActiveIndex((i) => Math.max(i - 1, 0));
    } else if (e.key === 'Enter' && matches[activeIndex]) {
      e.preventDefault();
      selectCountry(matches[activeIndex].code);
    } else if (e.key === 'Escape') {
      setSearchOpen(false);
    }
  };

  const fetchCountryProfile = async (countryCode) => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/country-profile/${countryCode}?lang=${language}`);
      setCountryProfile(response.data);
    } catch (error) {
      console.error('Error loading country profile:', error);
      toast({ title: t.error, description: t.profileError, variant: "destructive" });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="kente-cadre">
      <div className="space-y-4 p-2 sm:p-3 md:p-5">
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
          <CardContent className="grid gap-3 md:grid-cols-2">
            {/* Recherche, en plus du menu déroulant */}
            <div className="relative">
              <label htmlFor="country-search" className="sr-only">{t.searchLabel}</label>
              <Search aria-hidden="true" className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--afcfta-muted)]" />
              <input
                id="country-search"
                type="search"
                role="combobox"
                aria-autocomplete="list"
                aria-expanded={showMatches && matches.length > 0}
                aria-controls="country-search-list"
                aria-activedescendant={showMatches && matches[activeIndex] ? `country-option-${matches[activeIndex].code}` : undefined}
                autoComplete="off"
                placeholder={t.searchPlaceholder}
                value={query}
                onChange={(e) => {
                  setQuery(e.target.value);
                  setActiveIndex(0);
                  setSearchOpen(true);
                }}
                onFocus={() => setSearchOpen(true)}
                onBlur={() => setSearchOpen(false)}
                onKeyDown={onSearchKeyDown}
                className="h-11 w-full rounded-md border border-[rgba(212,175,55,0.25)] bg-[var(--afcfta-card)] pl-9 pr-3 text-base text-[var(--text)] placeholder:text-[var(--afcfta-muted)] focus:border-[rgba(212,175,55,0.5)] focus:outline-none focus-visible:ring-2 focus-visible:ring-[color-mix(in_srgb,var(--gold)_35%,transparent)]"
              />
              {showMatches && (matches.length ? (
                <ul
                  id="country-search-list"
                  role="listbox"
                  aria-label={t.searchLabel}
                  className="absolute left-0 right-0 top-full z-50 mt-1 max-h-72 overflow-y-auto rounded-md border border-[var(--afcfta-border)] bg-[var(--afcfta-card)] py-1 shadow-xl"
                >
                  {matches.map((c, i) => (
                    <li
                      key={c.code}
                      id={`country-option-${c.code}`}
                      role="option"
                      aria-selected={i === activeIndex}
                      // mousedown : avant que le champ ne perde le focus.
                      onMouseDown={(e) => {
                        e.preventDefault();
                        selectCountry(c.code);
                      }}
                      onMouseEnter={() => setActiveIndex(i)}
                      // Surlignage commun aux options de l'application (theme.css).
                      data-highlighted={i === activeIndex ? '' : undefined}
                      className="flex cursor-pointer items-center gap-2 px-3 py-2 text-sm text-[var(--text)]"
                    >
                      <span aria-hidden="true">{getFlag(c.iso2 || c.code)}</span>
                      <span className="flex-1 font-medium">{c.name}</span>
                      <span className="text-xs text-[var(--afcfta-muted)]">{c.region}</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p role="status" className="absolute left-0 right-0 top-full z-50 mt-1 rounded-md border border-[var(--afcfta-border)] bg-[var(--afcfta-card)] px-3 py-2 text-sm text-[var(--afcfta-muted)] shadow-xl">
                  {t.noCountryFound}
                </p>
              ))}
            </div>

            <Select 
              value={selectedCountry} 
              onValueChange={selectCountry}
            >
              <SelectTrigger className="h-11 text-lg font-semibold border border-[rgba(212,175,55,0.25)] focus:border-[rgba(212,175,55,0.5)]">
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

        {loading && (
          <p className="inline-block rounded-md bg-[var(--afcfta-card)] px-3 py-1 text-sm text-[var(--afcfta-muted)]" role="status">{t.loading}</p>
        )}

        {countryProfile && (
          <div className="space-y-4">
            <Card className="shadow-2xl border-0 bg-[image:var(--card-grad)]">
              <CardHeader className="bg-[image:var(--card-head)] border-b border-[color-mix(in_srgb,var(--gold)_30%,transparent)]">
                <CardTitle className="flex items-center space-x-3 text-2xl">
                  <span className="text-5xl">{getFlag(countryProfile.country_code)}</span>
                  <div>
                    <span className="font-bold text-[var(--gold)] text-3xl">{countryProfile.country_name}</span>
                    <p className="text-sm text-[var(--text)] mt-1">{countryProfile.region}</p>
                  </div>
                </CardTitle>
                <CardDescription className="text-sm font-semibold text-[var(--text)] flex flex-wrap items-center gap-2 mt-2">
                  <span className="bg-[color-mix(in_srgb,var(--gold)_12%,var(--afcfta-card))] px-3 py-1 rounded-full text-[var(--gold)]">
                    {countryProfile.population_millions ? `${chiffres(countryProfile.population_millions, language, 1)} M` : formatNumber(countryProfile.population)} {t.inhabitants}
                    {years.population ? ` (${years.population})` : ''}
                    {rankings.population ? ` · #${rankings.population.rank}/${rankings.population.total} ${t.inAfrica}` : ''}
                  </span>
                  <span className="bg-[color-mix(in_srgb,var(--success)_12%,var(--afcfta-card))] px-3 py-1 rounded-full text-[var(--success)]">{t.auMember}</span>
                </CardDescription>
              </CardHeader>
            </Card>

            {/* SECTION: Indicateurs macroéconomiques — chaque tuile porte l'année
                réelle de sa valeur (BM/FMI), jamais une année figée. */}
            <section className={PANEL}>
              <SectionTitle>{t.macroIndicators}</SectionTitle>
              <div className="grid grid-cols-2 md:grid-cols-3 2xl:grid-cols-6 gap-3">
                <StatTile
                  tone="success"
                  label={t.totalGdp}
                  value={countryProfile.gdp_usd != null ? montantUnite(countryProfile.gdp_usd / 1000000000, 'B', language, 1) : null}
                  meta={meta(years.gdp, t.wbSource)}
                  {...rankOf('gdp')}
                />
                <StatTile
                  tone="info"
                  label={t.gdpPerCapita}
                  value={countryProfile.gdp_per_capita != null ? montant(Math.round(countryProfile.gdp_per_capita), language) : null}
                  meta={meta(years.gdp_per_capita, t.wbSource)}
                  {...rankOf('gdp_per_capita')}
                />
                <StatTile
                  tone={growthTone(proj.gdp_growth_latest)}
                  label={`${t.growth} ${proj.gdp_growth_latest_year || ''}`}
                  value={pct(proj.gdp_growth_latest, language)}
                  meta={proj.gdp_growth_latest_source}
                  {...rankOf('gdp_growth')}
                />
                <StatTile
                  tone="gold"
                  label={`${t.projection} ${proj.gdp_growth_projection_current_year || ''}`}
                  value={pct(proj.gdp_growth_projection_current, language)}
                  meta={t.imfWeo}
                  {...rankOf('gdp_growth_projection')}
                />
                <StatTile
                  tone={inflationTone(countryProfile.inflation_rate)}
                  label={`${t.inflation} ${years.inflation || ''}`}
                  value={pct(countryProfile.inflation_rate, language)}
                  meta={t.wbSource}
                  {...rankOf('inflation')}
                />
                <StatTile
                  tone={unemploymentTone(countryProfile.unemployment_rate)}
                  label={`${t.unemployment} ${years.unemployment || ''}`}
                  value={pct(countryProfile.unemployment_rate, language)}
                  meta={t.iloWb}
                  {...rankOf('unemployment')}
                />
              </div>
              <p className="mt-2 text-xs text-[var(--afcfta-muted)]">{t.rankLegend}</p>
            </section>

            {/* SECTION: Dette publique (FMI WEO), dette extérieure et réserves de change
                (Banque mondiale), développement humain (PNUD) */}
            <section className={PANEL}>
              <SectionTitle>{t.publicFinance}</SectionTitle>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <StatTile
                  tone={debtTone(countryProfile.total_debt_pct_gdp)}
                  label={`${t.publicDebt} ${proj.debt_year || ''}`}
                  value={pct(countryProfile.total_debt_pct_gdp, language)}
                  meta={countryProfile.total_debt_pct_gdp != null ? `${t.ofGdp} · ${debtLabel(countryProfile.total_debt_pct_gdp, t)}` : t.imfWeo}
                  {...rankOf('gov_debt')}
                />
                <StatTile
                  tone="info"
                  label={`${t.externalDebt} ${extDebt?.year || ''}`}
                  value={extDebt?.pct_gni != null ? pct(extDebt.pct_gni, language) : extDebtUsd}
                  meta={extDebt?.pct_gni != null ? meta(t.ofGni, extDebtUsd, t.idsSource) : t.idsSource}
                  {...rankOf('external_debt')}
                />
                <StatTile
                  tone="atlantic"
                  label={`${t.fxReserves} ${reserves?.year || ''}`}
                  value={reserves?.usd != null ? montantUnite(reserves.usd / 1000000000, 'B', language, 1) : null}
                  meta={
                    reserves
                      ? meta(
                          reserves.import_months != null
                            ? `${chiffres(reserves.import_months, language, 1)} ${t.importMonths}${reserves.import_months_year !== reserves.year ? ` (${reserves.import_months_year})` : ''}`
                            : null,
                          t.wbSource
                        )
                      : UEMOA.includes(countryProfile.country_code) ? t.reservesPooled : t.wbSource
                  }
                  {...rankOf('reserves')}
                />
                <StatTile
                  tone="violet"
                  label={`${t.hdi} ${proj.hdi_year || ''}`}
                  value={countryProfile.hdi != null ? chiffres(countryProfile.hdi, language, 3) : null}
                  meta={meta(countryProfile.hdi_rank ? `${t.worldRank} ${countryProfile.hdi_rank}/193` : null, proj.hdi_source)}
                  {...rankOf('hdi')}
                />
              </div>
            </section>

            {/* Gold Reserves & GAI 2025 */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
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

            {/* SECTION: Perspectives FMI (WEO : croissance, inflation, dette publique) */}
            {proj.imf_gdp_growth && (() => {
              const rows = [
                { key: 'imf_gdp_growth', label: language === 'fr' ? 'Croissance du PIB réel' : 'Real GDP growth' },
                { key: 'imf_inflation', label: t.inflation },
                { key: 'imf_gov_debt', label: `${t.publicDebt} (${t.ofGdp})` },
              ].filter((r) => proj[r.key] && Object.keys(proj[r.key]).length);
              const nowY = new Date().getFullYear();
              // Union des années de toutes les séries, sur l'horizon WEO utile
              // (deux années réalisées, l'année en cours et cinq de projection).
              // Le WEO traite l'année en cours comme une projection.
              const years = Array.from(new Set(rows.flatMap((r) => Object.keys(proj[r.key]))))
                .map(Number)
                .filter((y) => y >= nowY - 2 && y <= nowY + 5)
                .sort((a, b) => a - b);
              if (!years.length) return null;
              return (
                <section className={PANEL}>
                  <SectionTitle>{language === 'fr' ? 'Perspectives FMI' : 'IMF Outlook'}</SectionTitle>
                  <div className="overflow-x-auto rounded-xl border border-[var(--afcfta-border)]">
                    <table className="w-full text-sm border-collapse">
                      <thead className="bg-[var(--afcfta-card)]">
                        <tr>
                          <th className="text-left p-2 pr-4 min-w-[13rem] text-[var(--afcfta-muted)] font-semibold">{language === 'fr' ? 'Indicateur' : 'Indicator'}</th>
                          {years.map((y) => (
                            <th key={y} className={`p-2 text-right font-semibold tabular-nums ${y < nowY ? 'text-[var(--text)]' : 'text-[var(--gold)]'}`}>
                              {y}{y >= nowY ? '*' : ''}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {rows.map((r) => (
                          <tr key={r.key} className="border-t border-[var(--afcfta-border)]">
                            <td className="p-2 pr-4 min-w-[13rem] text-[var(--text)] font-medium">{r.label}</td>
                            {years.map((y) => (
                              <td key={y} className={`p-2 text-right tabular-nums ${y < nowY ? 'text-[var(--text)]' : 'text-[var(--text-soft)]'}`}>
                                {pct(proj[r.key][y], language) ?? '—'}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  <p className="text-xs text-[var(--afcfta-muted)] mt-2">
                    {language === 'fr' ? '* projection · ' : '* projection · '}
                    {proj.imf_source || 'FMI — WEO'}
                  </p>
                </section>
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
                    {/* Trois groupes d'indicateurs ; l'année affichée est celle
                        renvoyée par l'API (<clé>_year), jamais une année figée. */}
                    {[
                      {
                        title: t.socialIndicators,
                        items: [
                          { key: 'life_expectancy_2023', rankKey: 'life_expectancy', label: t.lifeExpectancy, tone: 'success', fmt: (v) => `${chiffres(v, language, 1)} ${t.years}` },
                          { key: 'gini_index_2024', label: t.giniIndex, tone: 'terra', fmt: (v) => chiffres(v, language, 1), unit: t.outOf100 },
                          { key: 'poverty_rate_3usd_2024', label: t.povertyRate, tone: 'danger', unit: t.populationPercent },
                          { key: 'urban_population_pct_2024', label: t.urbanPopulation, tone: 'violet', unit: t.ofTotal },
                        ],
                      },
                      {
                        title: t.digitalConnectivity,
                        items: [
                          { key: 'internet_users_pct_2024', rankKey: 'internet_users', label: t.internetAccess, tone: 'info', unit: t.populationPercent },
                          { key: 'cybersecurity_index_2024', label: t.cybersecurity, tone: 'violet', fmt: (v) => chiffres(v, language, 1), unit: 'ITU GCI', year: 2024 },
                          { key: 'electricity_access_2022', rankKey: 'electricity_access', label: t.electricityAccess, tone: 'gold', unit: t.populationPercent },
                          { key: 'mobile_3g_coverage_2024', label: t.coverage3g, tone: 'success', unit: t.populationPercent },
                        ],
                      },
                      {
                        title: t.environmentEquality,
                        items: [
                          { key: 'female_labor_force_pct_2024', label: t.workingWomen, tone: 'danger', unit: t.femalePopulation },
                          { key: 'water_stress_2022', label: t.waterStress, tone: 'info', unit: t.resources },
                          { key: 'ghg_emissions_mt_2022', label: t.ghgEmissions, tone: 'afcfta-muted', fmt: (v) => `${chiffres(v, language, 1)} Mt CO₂e` },
                          { key: 'learning_poverty_2023', label: t.learningPoverty, tone: 'violet', unit: t.children },
                        ],
                      },
                    ].map((group) => {
                      const items = group.items.filter((it) => proj[it.key] != null);
                      if (!items.length) return null;
                      return (
                        <section key={group.title} className="mb-6 last:mb-0">
                          <SectionTitle>{group.title}</SectionTitle>
                          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                            {items.map((it) => {
                              const v = parseFloat(proj[it.key]);
                              return (
                                <StatTile
                                  key={it.key}
                                  tone={it.tone}
                                  label={it.label}
                                  value={it.fmt ? it.fmt(v) : pct(v, language)}
                                  meta={meta(it.unit, proj[`${it.key}_year`] ?? it.year)}
                                  {...(it.rankKey ? rankOf(it.rankKey) : {})}
                                />
                              );
                            })}
                          </div>
                        </section>
                      );
                    })}

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
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {countryProfile.infrastructure_ranking.lpi_infrastructure_score != null && (
                      <StatTile
                        tone="violet"
                        label={`${t.lpiScore} — ${t.infrastructure}`}
                        value={`${chiffres(countryProfile.infrastructure_ranking.lpi_infrastructure_score, language, countryProfile.infrastructure_ranking.lpi_edition === 2023 ? 1 : 2)}/5`}
                        meta={`LPI ${countryProfile.infrastructure_ranking.lpi_edition} · ${t.wbSource}`}
                        {...rankOf('lpi')}
                      />
                    )}
                    <StatTile
                      tone="terra"
                      label={t.aidiScore}
                      value={`${countryProfile.infrastructure_ranking.aidi_transport_score}/100`}
                      meta={`${t.africaRank} #${countryProfile.infrastructure_ranking.africa_rank} · ${t.globalIndex}`}
                    />
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
          </div>
        )}
      </div>
    </div>
  );
}

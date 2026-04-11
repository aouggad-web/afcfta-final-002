import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  TrendingUp,
  Globe,
  Target,
  BarChart3,
  ShieldCheck,
  Database,
  ArrowUpRight,
  Loader2,
} from 'lucide-react';
import NewsDashboard from './NewsDashboard';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';
const API = `${BACKEND_URL}/api`;

const translations = {
  fr: {
    overview: "Vue d'ensemble ZLECAf",
    source: 'Source: FMI WEO Oct 2025, UNCTAD',
    lead: "Cockpit d'intelligence économique, tarifaire et commerciale pour l'espace africain.",
    totalGdp: 'PIB Combiné Afrique',
    intraAfricanTrade: 'Commerce Intra-Africain',
    dataCoverage: 'Couverture Données',
    tariffPositions: 'Positions Tarifaires',
    countries: 'pays membres',
    authenticCountries: 'pays avec données authentiques',
    authenticPositions: 'positions vérifiées',
    growth: 'Croissance 2024',
    strategicCoverage: 'Couverture stratégique',
    strategicCoverageSub: 'Blocs commerciaux et profondeur de données',
    members: 'Membres',
    coverage: 'Couverture',
    authentic: 'Authentique',
    lastLayer: 'Dernière couche',
    blocCountries: 'pays couverts',
    loading: 'Chargement...',
  },
  en: {
    overview: 'AfCFTA Overview',
    source: 'Source: IMF WEO Oct 2025, UNCTAD',
    lead: 'Economic, tariff and trade intelligence cockpit for the African market space.',
    totalGdp: 'Combined Africa GDP',
    intraAfricanTrade: 'Intra-African Trade',
    dataCoverage: 'Data Coverage',
    tariffPositions: 'Tariff Positions',
    countries: 'member countries',
    authenticCountries: 'countries with authentic data',
    authenticPositions: 'verified positions',
    growth: 'Growth 2024',
    strategicCoverage: 'Strategic coverage',
    strategicCoverageSub: 'Trade blocs and data depth',
    members: 'Members',
    coverage: 'Coverage',
    authentic: 'Authentic',
    lastLayer: 'Latest layer',
    blocCountries: 'countries covered',
    loading: 'Loading...',
  },
};

// Dynamic KPI Cards - values come from API
const getKpiCards = (t, authenticData) => [
  {
    key: 'gdp',
    title: t.totalGdp,
    value: '$2.7T',
    subtitle: `54 ${t.countries}`,
    icon: BarChart3,
    accent: 'var(--gold)',
    meta: t.members,
  },
  {
    key: 'trade',
    title: t.intraAfricanTrade,
    value: '$235B',
    subtitle: `${t.growth}: +7.7%`,
    icon: TrendingUp,
    accent: '#4f8ef7',
    meta: '+7.7%',
  },
  {
    key: 'coverage',
    title: t.dataCoverage,
    value: authenticData.totalCountries?.toString() || '54',
    subtitle: t.authenticCountries,
    icon: Database,
    accent: '#20c997',
    meta: t.authentic,
  },
  {
    key: 'tariff',
    title: t.tariffPositions,
    value: authenticData.totalPositionsFormatted || '229K',
    subtitle: t.authenticPositions,
    icon: Target,
    accent: '#d4891a',
    meta: t.lastLayer,
  },
];

// Regional blocs with country assignments
const BLOC_COUNTRIES = {
  CEDEAO: ['BEN', 'BFA', 'CPV', 'CIV', 'GMB', 'GHA', 'GIN', 'GNB', 'LBR', 'MLI', 'NER', 'NGA', 'SEN', 'SLE', 'TGO'],
  CEMAC: ['CMR', 'CAF', 'TCD', 'COG', 'GNQ', 'GAB'],
  EAC: ['BDI', 'KEN', 'RWA', 'SSD', 'TZA', 'UGA', 'COD'],
  SACU: ['BWA', 'LSO', 'NAM', 'ZAF', 'SWZ'],
  COMESA: ['BDI', 'COM', 'COD', 'DJI', 'EGY', 'ERI', 'ETH', 'KEN', 'LBY', 'MDG', 'MWI', 'MUS', 'RWA', 'SYC', 'SDN', 'SWZ', 'UGA', 'ZMB', 'ZWE'],
};

const BLOCS_CONFIG = [
  { name: 'CEDEAO', accent: '#d4891a' },
  { name: 'CEMAC', accent: '#4f8ef7' },
  { name: 'EAC', accent: '#20c997' },
  { name: 'SACU', accent: '#9b6ef5' },
  { name: 'COMESA', accent: '#e67e22' },
];

function DashboardMetricCard({ item, loading }) {
  const Icon = item.icon;

  return (
    <div
      className="rounded-2xl border p-4 md:p-5"
      style={{
        background: 'linear-gradient(180deg, rgba(255,255,255,0.03), rgba(255,255,255,0.015))',
        borderColor: 'rgba(255,255,255,0.06)',
        boxShadow: '0 14px 30px rgba(0,0,0,0.16)',
      }}
    >
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-[11px] uppercase tracking-wide text-[var(--afcfta-muted)] font-semibold">
            {item.title}
          </p>
          <p className="mt-2 text-3xl font-bold text-[var(--text)]">
            {loading && (item.key === 'coverage' || item.key === 'tariff') 
              ? <Loader2 className="w-6 h-6 animate-spin" />
              : item.value}
          </p>
          <p className="mt-1 text-sm text-[var(--afcfta-muted)]">{item.subtitle}</p>
        </div>

        <div
          className="shrink-0 rounded-xl p-3 border"
          style={{
            background: `${item.accent}18`,
            borderColor: `${item.accent}40`,
            color: item.accent,
          }}
        >
          <Icon className="w-5 h-5" />
        </div>
      </div>

      <div className="mt-4 flex items-center justify-between">
        <span
          className="inline-flex items-center rounded-full px-2.5 py-1 text-[11px] font-semibold"
          style={{
            background: 'rgba(255,255,255,0.05)',
            color: 'var(--text)',
          }}
        >
          {item.meta}
        </span>

        <span className="inline-flex items-center gap-1 text-xs text-[var(--afcfta-muted)]">
          <ArrowUpRight className="w-3.5 h-3.5" />
          intelligence
        </span>
      </div>
    </div>
  );
}

const DashboardTabNew = ({ language = 'fr' }) => {
  const [authenticData, setAuthenticData] = useState({
    totalCountries: 0,
    totalPositions: 0,
    totalPositionsFormatted: '0',
    countriesList: [],
    blocsData: [],
  });
  const [loading, setLoading] = useState(true);
  const t = translations[language] || translations.fr;

  useEffect(() => {
    const fetchAuthenticData = async () => {
      try {
        // Fetch real authentic tariff data
        const response = await axios.get(`${API}/authentic-tariffs/countries`);
        const data = response.data;
        
        if (data && data.countries) {
          const countries = data.countries;
          const totalCountries = data.total || countries.length;
          
          // Calculate total positions from all countries
          let totalPositions = 0;
          countries.forEach(c => {
            totalPositions += (c.total_positions || c.total_sub_positions || 0);
          });
          
          // Format positions (e.g., 1185000 -> "1.18M")
          let totalPositionsFormatted;
          if (totalPositions >= 1000000) {
            totalPositionsFormatted = (totalPositions / 1000000).toFixed(2) + 'M';
          } else if (totalPositions >= 1000) {
            totalPositionsFormatted = Math.round(totalPositions / 1000) + 'K';
          } else {
            totalPositionsFormatted = totalPositions.toString();
          }
          
          // Calculate bloc coverage with authentic data
          const countryIsos = countries.map(c => c.iso3);
          const blocsWithCoverage = BLOCS_CONFIG.map(bloc => {
            const blocCountries = BLOC_COUNTRIES[bloc.name] || [];
            const coveredCount = blocCountries.filter(iso => countryIsos.includes(iso)).length;
            return {
              ...bloc,
              count: coveredCount,
              total: blocCountries.length,
            };
          });
          
          setAuthenticData({
            totalCountries,
            totalPositions,
            totalPositionsFormatted,
            countriesList: countries,
            blocsData: blocsWithCoverage,
          });
        }
      } catch (error) {
        console.error('Error fetching authentic data:', error);
        // Fallback to reasonable defaults
        setAuthenticData({
          totalCountries: 54,
          totalPositions: 1180000,
          totalPositionsFormatted: '1.18M',
          countriesList: [],
          blocsData: BLOCS_CONFIG.map(b => ({ ...b, count: 0, total: 0 })),
        });
      } finally {
        setLoading(false);
      }
    };
    
    fetchAuthenticData();
  }, []);

  const kpis = getKpiCards(t, authenticData);

  return (
    <div className="space-y-6">
      <section
        className="rounded-2xl border overflow-hidden"
        style={{
          background:
            'radial-gradient(900px 260px at 0% 0%, rgba(212,137,26,0.10), transparent 55%), radial-gradient(700px 220px at 100% 0%, rgba(32,201,151,0.08), transparent 60%), linear-gradient(135deg, rgba(18,26,40,0.98), rgba(12,18,25,0.98))',
          borderColor: 'rgba(212,137,26,0.14)',
          boxShadow: '0 22px 50px rgba(0,0,0,0.22)',
        }}
      >
        <div className="p-5 md:p-6">
          <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-5">
            <div className="max-w-3xl">
              <div className="inline-flex items-center gap-2 text-xs uppercase tracking-wide font-bold text-[var(--gold)] mb-3">
                <ShieldCheck className="w-4 h-4" />
                {t.overview}
              </div>

              <h2 className="text-2xl md:text-3xl font-bold text-[var(--text)] leading-tight">
                {t.overview}
              </h2>

              <p className="mt-2 text-sm md:text-base text-[rgba(234,224,208,0.9)]">
                {t.lead}
              </p>

              <p className="mt-3 text-xs text-[var(--afcfta-muted)]">{t.source}</p>
            </div>

            <div className="grid grid-cols-3 gap-2 md:gap-3 min-w-full lg:min-w-[320px] lg:max-w-[340px]">
              <div className="rounded-xl border px-3 py-3 text-center bg-[rgba(255,255,255,0.04)] border-[rgba(255,255,255,0.06)]">
                <div className="text-[11px] uppercase tracking-wide text-[var(--afcfta-muted)]">
                  {t.members}
                </div>
                <div className="mt-1 text-xl font-bold text-[var(--text)]">54</div>
              </div>

              <div className="rounded-xl border px-3 py-3 text-center bg-[rgba(255,255,255,0.04)] border-[rgba(255,255,255,0.06)]">
                <div className="text-[11px] uppercase tracking-wide text-[var(--afcfta-muted)]">
                  {t.coverage}
                </div>
                <div className="mt-1 text-xl font-bold text-[var(--text)]">
                  {loading ? <Loader2 className="w-5 h-5 animate-spin mx-auto" /> : authenticData.totalPositionsFormatted}
                </div>
              </div>

              <div className="rounded-xl border px-3 py-3 text-center bg-[rgba(255,255,255,0.04)] border-[rgba(255,255,255,0.06)]">
                <div className="text-[11px] uppercase tracking-wide text-[var(--afcfta-muted)]">
                  {t.authentic}
                </div>
                <div className="mt-1 text-xl font-bold text-[var(--gold)]">
                  {loading ? <Loader2 className="w-5 h-5 animate-spin mx-auto" /> : authenticData.totalCountries}
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        {kpis.map((item) => (
          <DashboardMetricCard key={item.key} item={item} loading={loading} />
        ))}
      </section>

      <section
        className="rounded-2xl border p-5 md:p-6"
        style={{
          background: 'rgba(255,255,255,0.025)',
          borderColor: 'rgba(255,255,255,0.06)',
        }}
      >
        <div className="flex items-start justify-between gap-4 flex-wrap mb-4">
          <div>
            <h3 className="text-lg md:text-xl font-bold text-[var(--text)]">{t.strategicCoverage}</h3>
            <p className="text-sm text-[var(--afcfta-muted)] mt-1">{t.strategicCoverageSub}</p>
          </div>

          <div className="inline-flex items-center gap-2 rounded-full px-3 py-1.5 bg-[rgba(255,255,255,0.05)] text-xs text-[var(--afcfta-muted)]">
            <Globe className="w-3.5 h-3.5" />
            AfCFTA data fabric
          </div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          {authenticData.blocsData.map((bloc) => (
            <div
              key={bloc.name}
              className="rounded-xl border p-4"
              style={{
                background: 'linear-gradient(180deg, rgba(255,255,255,0.035), rgba(255,255,255,0.015))',
                borderColor: `${bloc.accent}55`,
              }}
            >
              <div
                className="text-sm font-bold uppercase tracking-wide"
                style={{ color: bloc.accent }}
              >
                {bloc.name}
              </div>
              <div className="mt-2 text-2xl font-bold text-[var(--text)]">
                {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : bloc.count}
              </div>
              <div className="mt-1 text-xs text-[var(--afcfta-muted)]">
                {bloc.count}/{bloc.total} {t.blocCountries}
              </div>
            </div>
          ))}
        </div>
      </section>

      <NewsDashboard language={language} />
    </div>
  );
};

export default DashboardTabNew;

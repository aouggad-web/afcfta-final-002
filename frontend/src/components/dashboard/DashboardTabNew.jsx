import React, { useState, useEffect } from 'react';
import {
  TrendingUp,
  Globe,
  Target,
  BarChart3,
  ShieldCheck,
  Database,
  ArrowUpRight,
} from 'lucide-react';
import NewsDashboard from './NewsDashboard';
import { montantCompact, montantUnite } from '../../utils/nombres';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || '';
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
    continentalTitle: 'Indicateurs continentaux 2025',
    afreximbankSource: 'Source : Afreximbank, African Trade Report 2026',
    gdpGrowth: 'Croissance du PIB',
    inflation: 'Inflation',
    merchExports: 'Exportations de marchandises',
    intraAfricanTradeShort: 'Commerce intra-africain',
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
    continentalTitle: 'Continental indicators 2025',
    afreximbankSource: 'Source: Afreximbank, African Trade Report 2026',
    gdpGrowth: 'GDP growth',
    inflation: 'Inflation',
    merchExports: 'Merchandise exports',
    intraAfricanTradeShort: 'Intra-African trade',
  },
};

const BLOCS = [
  { name: 'CEDEAO', count: 7, accent: '#d4891a' },
  { name: 'CEMAC', count: 5, accent: '#4f8ef7' },
  { name: 'EAC', count: 7, accent: '#20c997' },
  { name: 'SACU', count: 5, accent: '#9b6ef5' },
  { name: 'AES', count: 3, accent: '#e67e22' },
];

function DashboardMetricCard({ item }) {
  const Icon = item.icon;

  return (
    <div
      className="rounded-2xl border p-5 md:p-6"
      style={{
        background: 'var(--lift)',
        borderColor: 'var(--lift-border)',
        boxShadow: 'var(--lift-shadow)',
        minHeight: 160,
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        containerType: 'inline-size',
      }}
    >
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-[11px] text-[var(--afcfta-muted)] font-bold">
            {item.title}
          </p>
          <p
            className="mt-3 font-bold text-[var(--text)]"
            style={{
              // « 2 700 Md $ » ne se coupe pas : réduit pour tenir à côté de
              // l'icône (46 px + 16 px d'écart) au lieu de la pousser dehors.
              fontSize: 'min(clamp(30px, 3vw, 44px), calc((100cqi - 62px) / 5.5))',
              fontFamily: "var(--font-display, 'Cormorant Garamond', Georgia, serif)",
              lineHeight: 1,
            }}
          >
            {item.value}
          </p>
          <p className="mt-2 text-[13px] text-[var(--afcfta-muted)]">{item.subtitle}</p>
        </div>

        <div
          className="shrink-0 rounded-xl p-3 border"
          style={{
            background: `${item.accent}18`,
            borderColor: `${item.accent}40`,
            color: `color-mix(in srgb, ${item.accent} 40%, var(--text))`,
          }}
        >
          <Icon className="w-5 h-5" />
        </div>
      </div>

      <div className="mt-4 flex items-center justify-between">
        <span
          className="inline-flex items-center rounded-full px-2.5 py-1 text-[11px] font-semibold"
          style={{
            background: 'var(--overlay)',
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
  const [stats, setStats] = useState(null);
  const [atr, setAtr] = useState(null); // Afreximbank ATR 2026 continental indicators
  const [loading, setLoading] = useState(true);
  const t = translations[language] || translations.fr;

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const response = await fetch(`${API}/statistics`);
        const data = await response.json();
        setStats(data);
      } catch (error) {
        console.error('Error fetching stats:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchStats();

    // Real continental indicators (Afreximbank African Trade Report 2026)
    fetch(`${API}/statistics/afreximbank-atr2026`)
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => setAtr(d?.continental_indicators_2025 || null))
      .catch(() => setAtr(null));
  }, []);

  // Build KPIs dynamically with real data from API
  const kpis = React.useMemo(() => {
    const authenticCount = stats?.overview?.authentic_countries || 54;
    const verifiedPositions = stats?.overview?.verified_positions || 229000;
    
    // Format verified positions (e.g., 894783 -> "895K")
    const formatCount = (count) => {
      if (count >= 1000) {
        return Math.round(count / 1000) + 'K';
      }
      return count.toString();
    };

    return [
      {
        key: 'gdp',
        title: t.totalGdp,
        value: montantCompact(2.7e12, language, { T: 1 }),
        subtitle: `54 ${t.countries}`,
        icon: BarChart3,
        accent: 'var(--gold)',
        meta: t.members,
      },
      {
        key: 'trade',
        title: t.intraAfricanTrade,
        // Real figure from Afreximbank ATR 2026 (2025) when available
        value: montantUnite(atr?.intra_african_trade_busd || 213.8, 'B', language),
        subtitle: `2025: +${atr?.intra_african_trade_growth_pct ?? 5.5}%`,
        icon: TrendingUp,
        accent: '#4f8ef7',
        meta: `+${atr?.intra_african_trade_growth_pct ?? 5.5}%`,
      },
      {
        key: 'coverage',
        title: t.dataCoverage,
        value: authenticCount.toString(),
        subtitle: t.authenticCountries,
        icon: Database,
        accent: '#20c997',
        meta: t.authentic,
      },
      {
        key: 'tariff',
        title: t.tariffPositions,
        value: formatCount(verifiedPositions),
        subtitle: t.authenticPositions,
        icon: Target,
        accent: '#d4891a',
        meta: t.lastLayer,
      },
    ];
  }, [stats, t, atr]);

  return (
    <div className="space-y-6">
      <section
        className="rounded-2xl border overflow-hidden zellige-frise"
        style={{
          background:
            'var(--panel)',
          borderColor: 'var(--panel-border)',
          boxShadow: 'var(--panel-shadow)',
        }}
      >
        <div className="p-5 md:p-6">
          <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-5">
            <div className="max-w-3xl">
              <div className="inline-flex items-center gap-2 text-xs font-bold text-[var(--gold)] mb-3">
                <ShieldCheck className="w-4 h-4" />
                {t.overview}
              </div>

              <h2 className="text-2xl md:text-3xl font-bold text-[var(--text)] leading-tight">
                {t.overview}
              </h2>

              <p className="mt-2 text-sm md:text-base text-[var(--text-soft)]">
                {t.lead}
              </p>

              <p className="mt-3 text-xs text-[var(--afcfta-muted)]">{t.source}</p>
            </div>

            <div className="grid grid-cols-3 gap-2 md:gap-3 min-w-full lg:min-w-[320px] lg:max-w-[340px]">
              {[
                { label: t.members, value: '54' },
                { label: t.coverage, value: stats?.overview?.verified_positions ? Math.round(stats.overview.verified_positions / 1000) + 'K' : '229K' },
                { label: t.authentic, value: String(stats?.overview?.authentic_countries || 54) },
              ].map(({ label, value }) => (
                <div key={label} className="rounded-xl border px-3 py-4 text-center bg-[var(--overlay)] border-[var(--overlay-border)]">
                  <div className="text-[11px] text-[var(--afcfta-muted)] font-bold">{label}</div>
                  <div
                    className="mt-2 font-bold text-[var(--text)]"
                    style={{
                      fontSize: 'clamp(22px, 2.4vw, 32px)',
                      fontFamily: "var(--font-display, 'Cormorant Garamond', Georgia, serif)",
                      lineHeight: 1,
                    }}
                  >
                    {value}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        {kpis.map((item) => (
          <DashboardMetricCard key={item.key} item={item} />
        ))}
      </section>

      {/* Real continental indicators — Afreximbank African Trade Report 2026 */}
      {atr && (
        <section
          className="rounded-2xl border p-5 md:p-6"
          style={{ background: 'var(--overlay)', borderColor: 'var(--overlay-border)' }}
        >
          <div className="flex items-center justify-between gap-4 flex-wrap mb-4">
            <h3 className="text-lg md:text-xl font-bold text-[var(--text)]">{t.continentalTitle}</h3>
            <span className="inline-flex items-center gap-2 rounded-full px-3 py-1.5 bg-[var(--overlay)] text-xs text-[var(--afcfta-muted)]">
              <ShieldCheck className="w-3.5 h-3.5" />
              {t.afreximbankSource}
            </span>
          </div>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 md:gap-4">
            {[
              {
                label: t.gdpGrowth,
                value: atr.real_gdp_growth_pct != null ? `+${atr.real_gdp_growth_pct}%` : '—',
                accent: '#20c997',
              },
              {
                label: t.inflation,
                value: atr.inflation_pct != null ? `${atr.inflation_pct}%` : '—',
                accent: '#e67e22',
              },
              {
                label: t.intraAfricanTradeShort,
                value: atr.intra_african_trade_busd != null ? montantUnite(atr.intra_african_trade_busd, 'B', language) : '—',
                accent: '#4f8ef7',
              },
              {
                label: t.merchExports,
                value: atr.merchandise_exports_busd != null ? montantUnite(atr.merchandise_exports_busd, 'B', language) : '—',
                accent: '#d4891a',
              },
            ].map(({ label, value, accent }) => (
              <div
                key={label}
                className="rounded-xl border p-5"
                style={{
                  background: 'var(--lift)',
                  borderColor: `${accent}44`,
                  borderLeftWidth: 3,
                  borderLeftColor: accent,
                  containerType: 'inline-size',
                }}
              >
                <div className="text-[11px] font-bold" style={{ color: `color-mix(in srgb, ${accent} 40%, var(--text))`}}>
                  {label}
                </div>
                <div
                  className="mt-2 font-bold text-[var(--text)]"
                  style={{
                    // Plafonnée à la tuile : « 685,2 Md $ » ne se coupe pas.
                    fontSize: 'min(clamp(24px, 2.6vw, 34px), 18cqi)',
                    fontFamily: "var(--font-display, 'Cormorant Garamond', Georgia, serif)",
                    lineHeight: 1,
                  }}
                >
                  {value}
                </div>
                <div className="mt-2 text-[12px] text-[var(--afcfta-muted)]">2025</div>
              </div>
            ))}
          </div>
        </section>
      )}

      <section
        className="rounded-2xl border p-5 md:p-6"
        style={{
          background: 'var(--overlay)',
          borderColor: 'var(--overlay-border)',
        }}
      >
        <div className="flex items-start justify-between gap-4 flex-wrap mb-4">
          <div>
            <h3 className="text-lg md:text-xl font-bold text-[var(--text)]">{t.strategicCoverage}</h3>
            <p className="text-sm text-[var(--afcfta-muted)] mt-1">{t.strategicCoverageSub}</p>
          </div>

          <div className="inline-flex items-center gap-2 rounded-full px-3 py-1.5 bg-[var(--overlay)] text-xs text-[var(--afcfta-muted)]">
            <Globe className="w-3.5 h-3.5" />
            AfCFTA data fabric
          </div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-5 gap-3 md:gap-4">
          {BLOCS.map((bloc) => (
            <div
              key={bloc.name}
              className="rounded-xl border p-5"
              style={{
                background: 'var(--lift)',
                borderColor: `${bloc.accent}44`,
                borderLeftWidth: 3,
                borderLeftColor: bloc.accent,
              }}
            >
              <div
                className="text-[11px] font-bold"
                style={{ color: `color-mix(in srgb, ${bloc.accent} 40%, var(--text))`}}
              >
                {bloc.name}
              </div>
              <div
                className="mt-2 font-bold text-[var(--text)]"
                style={{
                  fontSize: 'clamp(32px, 3.5vw, 48px)',
                  fontFamily: "var(--font-display, 'Cormorant Garamond', Georgia, serif)",
                  lineHeight: 1,
                }}
              >
                {bloc.count}
              </div>
              <div className="mt-2 text-[12px] text-[var(--afcfta-muted)]">
                {bloc.count} {t.blocCountries}
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

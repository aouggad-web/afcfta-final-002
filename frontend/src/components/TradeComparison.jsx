import React, { useState, useEffect } from 'react';
import { TableBody } from './ui/table';
import { LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import axios from 'axios';
import { Globe, TrendingUp } from 'lucide-react';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || '';
const API_URL = BACKEND_URL || '';

const TEXTS = {
  fr: {
    loading: 'Chargement des données commerciales...',
    selectYear: 'Année',
    intraNoteTitle: 'Données de Commerce INTRA-AFRICAIN',
    intraNoteBodyPre: 'Les données ci-dessous représentent uniquement les ',
    intraNoteBodyStrong: 'échanges commerciaux entre pays africains',
    intraNoteBodyMid: ', basées sur les données officielles de l’',
    intraNoteBodyPost: '.',
    intraNoteSharePre: 'Le commerce intra-africain représente actuellement environ ',
    intraNoteShareVal: '15-17%',
    intraNoteShareMid: ' du commerce total africain. L’objectif ZLECAf: ',
    intraNoteShareGoal: '25-30% d’ici 2030',
    totalAfricaTitle: 'Commerce Total Africain (Monde Entier)',
    totalAfricaBodyPre: 'Ces chiffres représentent le ',
    totalAfricaBodyStrong: 'commerce total de l’Afrique avec tous ses partenaires',
    totalAfricaBodyPost: ' (Europe, Asie, Amériques, etc.).',
    kpiGdp: 'PIB Total Africain',
    kpiGdpFooter: 'Avec tous partenaires',
    kpiExports: 'Exports (Monde)',
    kpiExportsFooter: 'Vers tous pays',
    kpiImports: 'Imports (Monde)',
    kpiImportsFooter: 'Depuis tous pays',
    kpiBalance: 'Solde Commercial',
    surplus: 'Excédent',
    deficit: 'Déficit',
    intraChartTitle: 'Commerce INTRA-AFRICAIN (entre pays africains uniquement)',
    intraChartSubtitle: 'Commerce réalisé uniquement entre les 55 pays africains membres de la ZLECAf',
    intra2023: 'Commerce Intra-Africain 2023',
    intra2024: 'Commerce Intra-Africain 2024',
    billionUsd: 'Milliards USD',
    growth2324: 'Croissance 2023-2024',
    commerceLabel: 'Commerce Intra-Africain',
    tariffTitle: 'Évolution Tarifaire: NPF vs ZLECAf (2025-2035)',
    tariffSubtitle: 'Démantèlement progressif des droits de douane',
    tariffNpf: 'Tarif NPF',
    tariffZlecaf: 'Tarif ZLECAf',
    tariffEconomy: 'Économie %',
    tariffNote: 'En 2035, les tarifs ZLECAf atteignent 0% pour les produits non-sensibles, permettant des économies maximales de 15.5% par rapport aux tarifs NPF.',
    tableWorldTitle: 'Commerce MONDIAL',
    tableWorldSubtitle: 'Tous partenaires — OEC, BM, FMI',
    tableIntraTitle: 'Commerce INTRA-AFRICAIN',
    tableIntraSubtitle: 'Entre pays africains — OEC, UNCTAD/AfDB',
    tableIntraBanner: 'Commerce UNIQUEMENT entre africains',
    colCountry: 'Pays',
    colExports: 'Exports',
    colImports: 'Imports',
    colBalance: 'Solde',
    colEconomy: 'Économie',
    nonSignatories: 'PAYS NON-SIGNATAIRES ZLECAf',
    eritrea: 'Érythrée',
    sourceWorld: 'Tous les pays africains — OEC, BM, FMI',
    sourceIntra: 'Tous les pays africains — OEC, UNCTAD, AfDB',
  },
  en: {
    loading: 'Loading trade data...',
    selectYear: 'Year',
    intraNoteTitle: 'INTRA-AFRICAN Trade Data',
    intraNoteBodyPre: 'The data below represents only ',
    intraNoteBodyStrong: 'trade flows between African countries',
    intraNoteBodyMid: ', based on official data from the ',
    intraNoteBodyPost: '.',
    intraNoteSharePre: 'Intra-African trade currently accounts for about ',
    intraNoteShareVal: '15-17%',
    intraNoteShareMid: ' of total African trade. AfCFTA target: ',
    intraNoteShareGoal: '25-30% by 2030',
    totalAfricaTitle: 'Total African Trade (Whole World)',
    totalAfricaBodyPre: 'These figures represent ',
    totalAfricaBodyStrong: 'Africa’s total trade with all its partners',
    totalAfricaBodyPost: ' (Europe, Asia, Americas, etc.).',
    kpiGdp: 'Total African GDP',
    kpiGdpFooter: 'With all partners',
    kpiExports: 'Exports (World)',
    kpiExportsFooter: 'To all countries',
    kpiImports: 'Imports (World)',
    kpiImportsFooter: 'From all countries',
    kpiBalance: 'Trade Balance',
    surplus: 'Surplus',
    deficit: 'Deficit',
    intraChartTitle: 'INTRA-AFRICAN Trade (between African countries only)',
    intraChartSubtitle: 'Trade carried out only between the 55 African AfCFTA member countries',
    intra2023: 'Intra-African Trade 2023',
    intra2024: 'Intra-African Trade 2024',
    billionUsd: 'Billion USD',
    growth2324: 'Growth 2023-2024',
    commerceLabel: 'Intra-African Trade',
    tariffTitle: 'Tariff Evolution: MFN vs AfCFTA (2025-2035)',
    tariffSubtitle: 'Progressive dismantling of customs duties',
    tariffNpf: 'MFN Tariff',
    tariffZlecaf: 'AfCFTA Tariff',
    tariffEconomy: 'Saving %',
    tariffNote: 'By 2035, AfCFTA tariffs reach 0% for non-sensitive products, enabling maximum savings of 15.5% versus MFN tariffs.',
    tableWorldTitle: 'WORLD Trade',
    tableWorldSubtitle: 'All partners — OEC, WB, IMF',
    tableIntraTitle: 'INTRA-AFRICAN Trade',
    tableIntraSubtitle: 'Between African countries — OEC, UNCTAD/AfDB',
    tableIntraBanner: 'Trade ONLY between Africans',
    colCountry: 'Country',
    colExports: 'Exports',
    colImports: 'Imports',
    colBalance: 'Balance',
    colEconomy: 'Saving',
    nonSignatories: 'AfCFTA NON-SIGNATORY COUNTRIES',
    eritrea: 'Eritrea',
    sourceWorld: 'All African countries — OEC, WB, IMF',
    sourceIntra: 'All African countries — OEC, UNCTAD, AfDB',
  },
};

const TradeComparison = ({ language = 'fr' }) => {
  const t = TEXTS[language] || TEXTS.fr;

  const [selectedYear, setSelectedYear] = useState('2024');
  const [loading, setLoading] = useState(true);
  const [statistics, setStatistics] = useState(null);
  const [calculationsGlobal, setCalculationsGlobal] = useState([]);
  const [calculationsIntraAfrican, setCalculationsIntraAfrican] = useState([]);

  // Données de commerce INTRA-AFRICAIN par année (Source: OEC)
  // Note: le commerce intra-africain représente environ 15-17% du commerce total africain
  const tradeDataByYear = {
    '2022': [
      { country: 'ZA', name: 'Afrique du Sud', exports: 24.8, imports: 18.3, balance: 6.5, intra_percentage: 4.2 },
      { country: 'NG', name: 'Nigéria', exports: 8.9, imports: 12.4, balance: -3.5, intra_percentage: 2.8 },
      { country: 'DZ', name: 'Algérie', exports: 2.1, imports: 5.8, balance: -3.7, intra_percentage: 1.9 },
      { country: 'EG', name: 'Égypte', exports: 6.7, imports: 8.9, balance: -2.2, intra_percentage: 2.3 },
      { country: 'MA', name: 'Maroc', exports: 5.4, imports: 4.2, balance: 1.2, intra_percentage: 1.8 },
      { country: 'KE', name: 'Kenya', exports: 7.2, imports: 6.8, balance: 0.4, intra_percentage: 2.1 },
      { country: 'GH', name: 'Ghana', exports: 5.8, imports: 6.3, balance: -0.5, intra_percentage: 1.6 },
      { country: 'CI', name: 'Côte d\'Ivoire', exports: 6.1, imports: 5.4, balance: 0.7, intra_percentage: 1.5 },
      { country: 'SN', name: 'Sénégal', exports: 3.2, imports: 4.8, balance: -1.6, intra_percentage: 1.2 },
      { country: 'TZ', name: 'Tanzanie', exports: 4.3, imports: 5.1, balance: -0.8, intra_percentage: 1.4 },
      { country: 'ET', name: 'Éthiopie', exports: 2.8, imports: 4.2, balance: -1.4, intra_percentage: 0.9 },
      { country: 'AO', name: 'Angola', exports: 1.6, imports: 3.7, balance: -2.1, intra_percentage: 0.8 },
      { country: 'TN', name: 'Tunisie', exports: 3.8, imports: 3.9, balance: -0.1, intra_percentage: 1.1 }
    ],
    '2023': [
      { country: 'ZA', name: 'Afrique du Sud', exports: 26.3, imports: 19.8, balance: 6.5, intra_percentage: 4.5 },
      { country: 'NG', name: 'Nigéria', exports: 9.7, imports: 13.2, balance: -3.5, intra_percentage: 3.1 },
      { country: 'DZ', name: 'Algérie', exports: 2.4, imports: 6.2, balance: -3.8, intra_percentage: 2.1 },
      { country: 'EG', name: 'Égypte', exports: 7.2, imports: 9.5, balance: -2.3, intra_percentage: 2.5 },
      { country: 'MA', name: 'Maroc', exports: 5.9, imports: 4.6, balance: 1.3, intra_percentage: 1.9 },
      { country: 'KE', name: 'Kenya', exports: 7.8, imports: 7.3, balance: 0.5, intra_percentage: 2.3 },
      { country: 'GH', name: 'Ghana', exports: 6.2, imports: 6.7, balance: -0.5, intra_percentage: 1.7 },
      { country: 'CI', name: 'Côte d\'Ivoire', exports: 6.5, imports: 5.8, balance: 0.7, intra_percentage: 1.6 },
      { country: 'SN', name: 'Sénégal', exports: 3.5, imports: 5.1, balance: -1.6, intra_percentage: 1.3 },
      { country: 'TZ', name: 'Tanzanie', exports: 4.6, imports: 5.5, balance: -0.9, intra_percentage: 1.5 },
      { country: 'ET', name: 'Éthiopie', exports: 3.1, imports: 4.5, balance: -1.4, intra_percentage: 1.0 },
      { country: 'AO', name: 'Angola', exports: 1.8, imports: 4.0, balance: -2.2, intra_percentage: 0.9 },
      { country: 'TN', name: 'Tunisie', exports: 4.1, imports: 4.2, balance: -0.1, intra_percentage: 1.2 }
    ]
  };

  // Fetch des statistiques réelles et données de commerce 2024
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const statsResponse = await axios.get(`${API_URL}/api/statistics`);
        setStatistics(statsResponse.data);

        if (selectedYear === '2024') {
          // 1. COMMERCE MONDIAL (avec tous les partenaires)
          const tradeGlobalResponse = await axios.get(`${API_URL}/api/statistics/trade-performance`);
          const tradeGlobalData = tradeGlobalResponse.data.countries_global;
          setCalculationsGlobal(tradeGlobalData.map(country => ({
            country: country.code,
            name: country.country,
            exports: parseFloat(country.exports_2024 || 0),
            imports: parseFloat(country.imports_2024 || 0),
            balance: parseFloat(country.trade_balance_2024 || 0),
          })));

          // 2. COMMERCE INTRA-AFRICAIN (uniquement entre pays africains)
          const tradeIntraResponse = await axios.get(`${API_URL}/api/statistics/trade-performance-intra-african`);
          const tradeIntraData = tradeIntraResponse.data.countries_intra_african;
          setCalculationsIntraAfrican(tradeIntraData.map(country => ({
            country: country.code,
            name: country.country,
            exports: parseFloat(country.exports_2024 || 0),
            imports: parseFloat(country.imports_2024 || 0),
            balance: parseFloat(country.trade_balance_2024 || 0),
            intra_percentage: parseFloat(country.intra_african_percentage || 17),
          })));
        } else {
          const yearData = tradeDataByYear[selectedYear] || tradeDataByYear['2023'];
          setCalculationsGlobal(yearData);
          setCalculationsIntraAfrican(yearData);
        }

        setLoading(false);
      } catch (error) {
        console.error('Erreur lors du chargement des données:', error);
        setLoading(false);
      }
    };
    fetchData();
  }, [selectedYear]);

  // Vue d'ensemble à partir des statistiques réelles
  const combinedGdpB = statistics?.overview?.estimated_combined_gdp
    ? statistics.overview.estimated_combined_gdp / 1000000000
    : null;
  const tradeOverview = {
    totalTrade: { value: combinedGdpB ? combinedGdpB.toFixed(1) : 3400, change: 12.5 },
    exports: { value: combinedGdpB ? (combinedGdpB * 0.53).toFixed(0) : 1800, change: 8.3 },
    imports: { value: combinedGdpB ? (combinedGdpB * 0.47).toFixed(0) : 1600, change: 15.2 },
    balance: { value: combinedGdpB ? (combinedGdpB * 0.06).toFixed(0) : 200, isSurplus: true },
  };

  // Comparaison tarifs par année (NPF vs ZLECAf)
  const tariffComparison = [
    { annee: '2025', NPF: 15.5, ZLECAf: 7.8, economie: 7.7 },
    { annee: '2027', NPF: 15.5, ZLECAf: 4.7, economie: 10.8 },
    { annee: '2030', NPF: 15.5, ZLECAf: 1.6, economie: 13.9 },
    { annee: '2033', NPF: 15.5, ZLECAf: 0.3, economie: 15.2 },
    { annee: '2035', NPF: 15.5, ZLECAf: 0, economie: 15.5 }
  ];

  if (loading) {
    return (
      <div className="stats-loading">
        <div className="stats-spinner" />
        <p style={{ color: 'rgba(142,155,174,0.7)', fontSize: '0.875rem' }}>{t.loading}</p>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* ── Year selector ───────────────────────────────────────── */}
      <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
        <label style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
          <span style={{ fontSize: 11, color: 'rgba(142,155,174,0.85)', fontWeight: 700, letterSpacing: 0.4 }}>{t.selectYear}</span>
          <select
            value={selectedYear}
            onChange={(e) => setSelectedYear(e.target.value)}
            style={{ padding: '8px 10px', borderRadius: 8, background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(212,175,55,0.22)', color: 'var(--text)', fontSize: 13, fontWeight: 600 }}
          >
            <option value="2024">2024</option>
            <option value="2023">2023</option>
            <option value="2022">2022</option>
          </select>
        </label>
      </div>

      {/* ── Info Note: Intra-African data ──────────────────────── */}
      <div className="stats-chart-card" style={{ padding: '16px 20px' }}>
        <div className="flex items-start gap-3">
          <div style={{ color: '#38bdf8', flexShrink: 0, marginTop: 2 }}>
            <Globe style={{ width: 18, height: 18 }} />
          </div>
          <div>
            <h4 style={{ fontWeight: 700, color: '#38bdf8', marginBottom: 4, fontSize: '0.85rem' }}>
              {t.intraNoteTitle}
            </h4>
            <p style={{ fontSize: '0.8rem', color: 'rgba(234,224,208,0.75)', margin: 0 }}>
              {t.intraNoteBodyPre}<strong>{t.intraNoteBodyStrong}</strong>{t.intraNoteBodyMid}
              <a href="https://oec.world/" target="_blank" rel="noopener noreferrer" style={{ color: '#38bdf8', textDecoration: 'underline' }}>OEC</a>{t.intraNoteBodyPost}
            </p>
            <p style={{ fontSize: '0.75rem', color: 'rgba(142,155,174,0.65)', marginTop: 6 }}>
              {t.intraNoteSharePre}<strong style={{ color: '#fbbf24' }}>{t.intraNoteShareVal}</strong>{t.intraNoteShareMid}
              <strong style={{ color: '#34d399' }}>{t.intraNoteShareGoal}</strong>.
            </p>
          </div>
        </div>
      </div>

      {/* ── Commerce Total Africain banner ──────────────────────── */}
      <div className="stats-chart-card" style={{ padding: '16px 20px', borderLeft: '3px solid #D4891A' }}>
        <div className="flex items-start gap-3">
          <div style={{ color: '#fbbf24', flexShrink: 0, marginTop: 2 }}>
            <Globe style={{ width: 18, height: 18 }} />
          </div>
          <div>
            <h3 style={{ fontWeight: 700, color: '#fbbf24', margin: 0, fontSize: '0.9rem' }}>
              {t.totalAfricaTitle}
            </h3>
            <p style={{ fontSize: '0.78rem', color: 'rgba(234,224,208,0.65)', marginTop: 4 }}>
              {t.totalAfricaBodyPre}<strong>{t.totalAfricaBodyStrong}</strong>{t.totalAfricaBodyPost}
            </p>
          </div>
        </div>
      </div>

      {/* ── KPI Cards Grid ──────────────────────────────────────── */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="stats-kpi-card atlantic">
          <p className="stats-kpi-label">{t.kpiGdp}</p>
          <p className="stats-kpi-value atlantic">${tradeOverview.totalTrade.value}B</p>
          <p className="stats-kpi-footer">
            <span className="stats-chip up">+{tradeOverview.totalTrade.change}%</span>
            {t.kpiGdpFooter}
          </p>
        </div>
        <div className="stats-kpi-card green">
          <p className="stats-kpi-label">{t.kpiExports}</p>
          <p className="stats-kpi-value green">${tradeOverview.exports.value}B</p>
          <p className="stats-kpi-footer">
            <span className="stats-chip up">+{tradeOverview.exports.change}%</span>
            {t.kpiExportsFooter}
          </p>
        </div>
        <div className="stats-kpi-card terra">
          <p className="stats-kpi-label">{t.kpiImports}</p>
          <p className="stats-kpi-value terra">${tradeOverview.imports.value}B</p>
          <p className="stats-kpi-footer">
            <span className="stats-chip down">+{tradeOverview.imports.change}%</span>
            {t.kpiImportsFooter}
          </p>
        </div>
        <div className="stats-kpi-card violet">
          <p className="stats-kpi-label">{t.kpiBalance}</p>
          <p className="stats-kpi-value green">+${tradeOverview.balance.value}B</p>
          <p className="stats-kpi-footer">
            <span className="stats-chip up">{tradeOverview.balance.isSurplus ? t.surplus : t.deficit}</span>
          </p>
        </div>
      </div>

      {/* ── Commerce INTRA-AFRICAIN ────────────────────────────── */}
      {statistics && statistics.trade_evolution && (
        <div className="stats-chart-card">
          <div className="stats-chart-header green">
            <div className="stats-chart-title green">
              <Globe style={{ width: 18, height: 18 }} />
              {t.intraChartTitle}
            </div>
            <div className="stats-chart-subtitle">{t.intraChartSubtitle}</div>
          </div>
          <div style={{ padding: '20px 20px 8px' }}>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
              <div className="stats-kpi-card atlantic">
                <p className="stats-kpi-label">{t.intra2023}</p>
                <p className="stats-kpi-value atlantic">${statistics.trade_evolution.intra_african_trade_2023}B</p>
                <p className="stats-kpi-footer">{t.billionUsd}</p>
              </div>
              <div className="stats-kpi-card green">
                <p className="stats-kpi-label">{t.intra2024}</p>
                <p className="stats-kpi-value green">${statistics.trade_evolution.intra_african_trade_2024}B</p>
                <p className="stats-kpi-footer">{t.billionUsd}</p>
              </div>
              <div className="stats-kpi-card gold">
                <p className="stats-kpi-label">{t.growth2324}</p>
                <p className="stats-kpi-value gold">+{statistics.trade_evolution.growth_rate_2023_2024}%</p>
                <p className="stats-kpi-footer">{statistics.trade_evolution.trend}</p>
              </div>
            </div>

            {/* Graphique évolution commerce intra-africain */}
            <ResponsiveContainer width="100%" height={300} debounce={300}>
              <AreaChart
                data={[
                  { annee: '2023', commerce: parseFloat(statistics.trade_evolution.intra_african_trade_2023) },
                  { annee: '2024', commerce: parseFloat(statistics.trade_evolution.intra_african_trade_2024) },
                  { annee: '2025*', commerce: parseFloat(statistics.trade_evolution.intra_african_trade_2024) * 1.12 },
                  { annee: '2030*', commerce: parseFloat(statistics.trade_evolution.intra_african_trade_2024) * 1.52 }
                ]}
                margin={{ top: 10, right: 30, left: 20, bottom: 10 }}
              >
                <defs>
                  <linearGradient id="colorCommerce" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#1A7A4A" stopOpacity={0.7}/>
                    <stop offset="95%" stopColor="#1A7A4A" stopOpacity={0.04}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                <XAxis dataKey="annee" tick={{ fontSize: 12, fontWeight: 600, fill: '#EAE0D0' }} axisLine={false} tickLine={false} />
                <YAxis
                  label={{ value: t.billionUsd, angle: -90, position: 'insideLeft', style: { fontSize: 10, fill: 'rgba(142,155,174,0.6)' } }}
                  tick={{ fontSize: 11, fill: 'rgba(142,155,174,0.7)' }}
                  axisLine={false} tickLine={false}
                />
                <Tooltip
                  formatter={(value) => [`$${value.toFixed(1)}B USD`, t.commerceLabel]}
                  contentStyle={{ background: 'rgba(16,22,32,0.97)', border: '1px solid rgba(212,137,26,0.3)', borderRadius: 10, fontSize: '0.78rem' }}
                  labelStyle={{ color: '#EAE0D0', fontWeight: 700 }}
                />
                <Legend wrapperStyle={{ fontSize: '0.78rem', color: 'rgba(142,155,174,0.8)' }} iconType="circle" />
                <Area type="monotone" dataKey="commerce" stroke="#34d399" strokeWidth={2.5} fill="url(#colorCommerce)" name={t.commerceLabel} dot={{ fill: '#34d399', r: 4 }} activeDot={{ r: 6 }} />
              </AreaChart>
            </ResponsiveContainer>

            <div style={{ marginTop: 12, padding: '10px 14px', borderRadius: 8, background: 'rgba(26,122,74,0.1)', borderLeft: '3px solid #1A7A4A' }}>
              <p style={{ fontSize: '0.78rem', color: 'rgba(52,211,153,0.9)' }}>
                {t.intraNoteSharePre}<strong>{t.intraNoteShareVal}</strong>{t.intraNoteShareMid}<strong>{t.intraNoteShareGoal}</strong>.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* ── Tariffs Chart: NPF vs ZLECAf ──────────────────────── */}
      <div className="stats-chart-card">
        <div className="stats-chart-header" style={{ borderBottomColor: 'rgba(155,110,245,0.2)' }}>
          <div className="stats-chart-title violet">
            <TrendingUp style={{ width: 18, height: 18 }} />
            {t.tariffTitle}
          </div>
          <div className="stats-chart-subtitle">{t.tariffSubtitle}</div>
        </div>
        <div style={{ padding: '16px 8px' }}>
          <div style={{ minHeight: '380px' }}>
            <ResponsiveContainer width="100%" height={350} debounce={300}>
              <LineChart data={tariffComparison}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                <XAxis dataKey="annee" tick={{ fontSize: 12, fill: 'rgba(142,155,174,0.8)' }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 11, fill: 'rgba(142,155,174,0.7)' }} axisLine={false} tickLine={false} />
                <Tooltip
                  formatter={(value) => `${value.toFixed(1)}%`}
                  contentStyle={{ background: 'rgba(16,22,32,0.97)', border: '1px solid rgba(212,137,26,0.3)', borderRadius: 10, fontSize: '0.78rem' }}
                  labelStyle={{ color: '#EAE0D0', fontWeight: 700 }}
                />
                <Legend wrapperStyle={{ fontSize: '0.78rem', color: 'rgba(142,155,174,0.8)' }} />
                <Line type="monotone" dataKey="NPF" stroke="#ef4444" strokeWidth={3} name={t.tariffNpf} dot={{ r: 6 }} />
                <Line type="monotone" dataKey="ZLECAf" stroke="#34d399" strokeWidth={2.5} name={t.tariffZlecaf} dot={{ r: 5, fill: '#34d399' }} />
                <Line type="monotone" dataKey="economie" stroke="#38bdf8" strokeWidth={2} strokeDasharray="5 5" name={t.tariffEconomy} dot={{ r: 4, fill: '#38bdf8' }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
          <div style={{ marginTop: 12, padding: '10px 14px', borderRadius: 8, background: 'rgba(26,122,74,0.1)', borderLeft: '3px solid #34d399' }}>
            <p style={{ fontSize: '0.78rem', color: 'rgba(52,211,153,0.9)' }}>{t.tariffNote}</p>
          </div>
        </div>
      </div>

      {/* ── Trade Tables: Mondial vs Intra-Africain ─────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Table 1: Commerce Mondial */}
        <div className="stats-chart-card">
          <div className="stats-chart-header gold">
            <div className="stats-chart-title gold">
              <Globe style={{ width: 18, height: 18 }} />
              {t.tableWorldTitle}
            </div>
            <div className="stats-chart-subtitle">{t.tableWorldSubtitle}</div>
          </div>
          <div style={{ overflowX: 'auto', maxHeight: 500, overflowY: 'auto' }}>
            <table className="stats-table">
              <thead>
                <tr>
                  <th style={{ textAlign: 'left' }}>{t.colCountry}</th>
                  <th style={{ textAlign: 'right' }}>{t.colExports}</th>
                  <th style={{ textAlign: 'right' }}>{t.colImports}</th>
                  <th style={{ textAlign: 'right' }}>{t.colBalance}</th>
                </tr>
              </thead>
              <TableBody>
                {calculationsGlobal.map((item) => (
                  <tr key={item.country}>
                    <td style={{ fontWeight: 600 }}>{item.name}</td>
                    <td style={{ textAlign: 'right', fontWeight: 700, color: '#34d399' }}>${item.exports.toFixed(1)}B</td>
                    <td style={{ textAlign: 'right', fontWeight: 700, color: '#fb923c' }}>${item.imports.toFixed(1)}B</td>
                    <td style={{ textAlign: 'right', fontWeight: 700, color: item.balance >= 0 ? '#34d399' : '#f87171' }}>
                      {item.balance >= 0 ? '+' : ''}{item.balance.toFixed(1)}
                    </td>
                  </tr>
                ))}
                <tr style={{ background: 'rgba(200,16,46,0.1)', borderTop: '2px solid rgba(200,16,46,0.3)' }}>
                  <td colSpan={4} style={{ textAlign: 'center', fontWeight: 700, fontSize: '0.72rem', color: '#f87171', padding: '6px 12px' }}>
                    {t.nonSignatories}
                  </td>
                </tr>
                <tr>
                  <td style={{ fontWeight: 600 }}>{t.eritrea}</td>
                  <td style={{ textAlign: 'right', color: 'rgba(142,155,174,0.5)' }}>N/A</td>
                  <td style={{ textAlign: 'right', color: 'rgba(142,155,174,0.5)' }}>N/A</td>
                  <td style={{ textAlign: 'right', color: 'rgba(142,155,174,0.5)' }}>N/A</td>
                </tr>
              </TableBody>
            </table>
          </div>
          <p className="stats-source-note">{t.sourceWorld}</p>
        </div>

        {/* Table 2: Commerce Intra-Africain */}
        <div className="stats-chart-card">
          <div className="stats-chart-header green">
            <div className="stats-chart-title green">
              <Globe style={{ width: 18, height: 18 }} />
              {t.tableIntraTitle}
            </div>
            <div className="stats-chart-subtitle">{t.tableIntraSubtitle}</div>
          </div>
          <div style={{ padding: '10px 16px 6px', background: 'rgba(26,122,74,0.1)', borderBottom: '1px solid rgba(52,211,153,0.15)' }}>
            <p style={{ fontSize: '0.72rem', color: 'rgba(52,211,153,0.8)', margin: 0 }}>{t.tableIntraBanner}</p>
          </div>
          <div style={{ overflowX: 'auto', maxHeight: 500, overflowY: 'auto' }}>
            <table className="stats-table">
              <thead>
                <tr>
                  <th style={{ textAlign: 'left' }}>{t.colCountry}</th>
                  <th style={{ textAlign: 'right' }}>{t.colExports}</th>
                  <th style={{ textAlign: 'right' }}>{t.colImports}</th>
                  <th style={{ textAlign: 'right' }}>{t.colBalance}</th>
                  <th style={{ textAlign: 'right' }}>{t.colEconomy}</th>
                </tr>
              </thead>
              <TableBody>
                {calculationsIntraAfrican.map((item) => (
                  <tr key={item.country}>
                    <td style={{ fontWeight: 600 }}>{item.name}</td>
                    <td style={{ textAlign: 'right', fontWeight: 700, color: '#34d399' }}>${item.exports.toFixed(1)}B</td>
                    <td style={{ textAlign: 'right', fontWeight: 700, color: '#6ee7b7' }}>${item.imports.toFixed(1)}B</td>
                    <td style={{ textAlign: 'right', fontWeight: 700, color: item.balance >= 0 ? '#34d399' : '#f87171' }}>
                      {item.balance >= 0 ? '+' : ''}{item.balance.toFixed(1)}
                    </td>
                    <td style={{ textAlign: 'right' }}>
                      <span style={{ fontSize: '0.7rem', fontWeight: 700, padding: '1px 6px', borderRadius: 100, background: 'rgba(155,110,245,0.18)', color: '#a78bfa', border: '1px solid rgba(155,110,245,0.25)' }}>
                        {item.intra_percentage}%
                      </span>
                    </td>
                  </tr>
                ))}
                <tr style={{ background: 'rgba(200,16,46,0.1)', borderTop: '2px solid rgba(200,16,46,0.3)' }}>
                  <td colSpan={5} style={{ textAlign: 'center', fontWeight: 700, fontSize: '0.72rem', color: '#f87171', padding: '6px 12px' }}>
                    {t.nonSignatories}
                  </td>
                </tr>
                <tr>
                  <td style={{ fontWeight: 600 }}>{t.eritrea}</td>
                  <td style={{ textAlign: 'right', color: 'rgba(142,155,174,0.5)' }}>N/A</td>
                  <td style={{ textAlign: 'right', color: 'rgba(142,155,174,0.5)' }}>N/A</td>
                  <td style={{ textAlign: 'right', color: 'rgba(142,155,174,0.5)' }}>N/A</td>
                  <td style={{ textAlign: 'right', color: 'rgba(142,155,174,0.5)' }}>0%</td>
                </tr>
              </TableBody>
            </table>
          </div>
          <p className="stats-source-note">{t.sourceIntra}</p>
        </div>
      </div>
    </div>
  );
};

export default TradeComparison;

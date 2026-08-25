import React, { useState, useEffect, useMemo } from 'react';
import axios from 'axios';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import EnhancedCountrySelector from './EnhancedCountrySelector';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || '';
const API = `${BACKEND_URL}/api`;

function ProductionMacro({ language = 'fr' }) {
  const [selectedCountry, setSelectedCountry] = useState('DZA');
  const [macroData, setMacroData] = useState(null);
  const [loading, setLoading] = useState(false);

  const texts = {
    fr: {
      title: 'Valeur Ajoutée Macro (World Bank / IMF)',
      subtitle: 'Structure sectorielle du PIB des économies africaines (données récentes)',
      projection: 'Projection',
      projectionHint: 'Projection FMI (World Economic Outlook)',
      records: 'enregistrements',
      sectors: 'secteurs',
      loading: 'Chargement des données macro...',
      noData: 'Aucune donnée disponible pour ce pays.',
      evolutionTitle: 'Évolution de la Valeur Ajoutée par Secteur (% du PIB)',
      comparisonTitle: 'Comparaison Sectorielle par Année',
      growthTitle: 'Croissance du PIB réel (variation annuelle %) — FMI WEO',
      detailsTitle: 'Données Détaillées',
      gdpPercent: '% du PIB',
      year: 'Année',
      selectedCountry: 'Pays',
      source: 'Source',
      dataCoverage: 'Couverture',
    },
    en: {
      title: 'Macro Value Added (World Bank / IMF)',
      subtitle: 'Sectoral structure of GDP for African economies (recent data)',
      projection: 'Projection',
      projectionHint: 'IMF projection (World Economic Outlook)',
      records: 'records',
      sectors: 'sectors',
      loading: 'Loading macro data...',
      noData: 'No data available for this country.',
      evolutionTitle: 'Value Added Evolution by Sector (% of GDP)',
      comparisonTitle: 'Sectoral Comparison by Year',
      growthTitle: 'Real GDP growth (annual %) — IMF WEO',
      detailsTitle: 'Detailed Data',
      gdpPercent: '% of GDP',
      year: 'Year',
      selectedCountry: 'Country',
      source: 'Source',
      dataCoverage: 'Coverage',
    },
  };

  const t = texts[language] || texts.fr;

  useEffect(() => {
    if (selectedCountry) {
      fetchMacroData(selectedCountry);
    }
  }, [selectedCountry]);

  const fetchMacroData = async (countryIso3) => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/production/macro/${countryIso3}`);
      const d = response.data;
      setMacroData(typeof d === 'object' && d !== null && !Array.isArray(d) ? d : null);
    } catch (error) {
      console.error('Error fetching macro data:', error);
      setMacroData(null);
    } finally {
      setLoading(false);
    }
  };

  // La croissance du PIB (NY.GDP.MKTP.KD.ZG) est une variation annuelle (%), pas
  // une part sectorielle « % du PIB » : elle ne doit PAS être tracée comme un
  // secteur dans les graphes de valeur ajoutée. On la sépare et on l'affiche à part.
  const isGdpGrowth = (records) =>
    Array.isArray(records) &&
    records.some(
      (r) =>
        r.indicator_code === 'NGDP_RPCH' ||
        r.indicator_code === 'NY.GDP.MKTP.KD.ZG' ||
        r.sector_isic_section === 'TOTAL'
    );

  const valueAddedSectors = useMemo(() => {
    if (!macroData?.data_by_sector) return {};
    return Object.fromEntries(
      Object.entries(macroData.data_by_sector).filter(([, recs]) => !isGdpGrowth(recs))
    );
  }, [macroData]);

  const gdpGrowthRecords = useMemo(() => {
    if (!macroData?.data_by_sector) return [];
    const entry = Object.entries(macroData.data_by_sector).find(([, recs]) => isGdpGrowth(recs));
    return entry ? [...entry[1]].sort((a, b) => a.year - b.year) : [];
  }, [macroData]);

  const availableYears = useMemo(() => {
    const set = new Set();
    Object.values(valueAddedSectors).forEach((records) => {
      records.forEach((r) => set.add(r.year));
    });
    return Array.from(set).sort((a, b) => a - b);
  }, [valueAddedSectors]);

  const projectionYears = useMemo(() => {
    const set = new Set();
    gdpGrowthRecords.forEach((r) => {
      if (r.is_projection) set.add(r.year);
    });
    return set;
  }, [gdpGrowthRecords]);

  const chartData = useMemo(() => {
    return availableYears.map((year) => {
      const dataPoint = { year };
      Object.entries(valueAddedSectors).forEach(([sectorName, records]) => {
        const yearRecord = records.find((r) => r.year === year);
        if (yearRecord) {
          dataPoint[sectorName] = yearRecord.value;
        }
      });
      return dataPoint;
    });
  }, [valueAddedSectors, availableYears]);

  const sectorNames = Object.keys(valueAddedSectors);

  const seriesColors = ['#9b6ef5', '#4f8ef7', '#20c997', '#d4891a'];

  return (
    <div className="space-y-6">
      <Card className="afcfta-result border-[rgba(212,137,26,0.16)]">
        <CardHeader className="afcfta-result-header">
          <div className="flex items-start justify-between gap-4 flex-wrap">
            <div>
              <CardTitle className="text-2xl md:text-3xl font-bold text-[var(--gold)] flex items-center gap-3">
                <span>📊</span>
                <span>{t.title}</span>
              </CardTitle>
              <CardDescription className="text-[var(--text)]/80 text-base mt-2">
                {t.subtitle}
              </CardDescription>
            </div>

            <div className="flex items-center gap-2 flex-wrap">
              <Badge className="bg-[rgba(255,255,255,0.06)] text-[var(--text)] border border-[rgba(255,255,255,0.08)]">
                {t.source}: World Bank / IMF
              </Badge>
              <Badge className="bg-[rgba(212,137,26,0.12)] text-[var(--gold)] border border-[rgba(212,137,26,0.2)]">
                {availableYears.length
                  ? `${availableYears[0]}–${availableYears[availableYears.length - 1]}`
                  : '2023–2025'}
              </Badge>
              {projectionYears.size > 0 && (
                <Badge className="bg-[rgba(155,110,245,0.14)] text-[#c3a3ff] border border-[rgba(155,110,245,0.28)]">
                  {t.projection} {Array.from(projectionYears).sort().join(', ')}
                </Badge>
              )}
            </div>
          </div>
        </CardHeader>

        <CardContent className="pt-6 space-y-4">
          <div className="afcfta-card">
            <div className="grid grid-cols-1 xl:grid-cols-[minmax(0,1fr)_auto] gap-4 items-end">
              <EnhancedCountrySelector
                value={selectedCountry}
                onChange={setSelectedCountry}
                label={t.selectedCountry}
                language={language}
                variant="prominent"
              />

              {macroData && (
                <div className="flex flex-wrap gap-2 xl:justify-end">
                  <Badge className="bg-[rgba(79,142,247,0.12)] text-[#8db8ff] border border-[rgba(79,142,247,0.22)]">
                    {macroData.total_records} {t.records}
                  </Badge>
                  <Badge className="bg-[rgba(32,201,151,0.12)] text-[#66e0bb] border border-[rgba(32,201,151,0.22)]">
                    {sectorNames.length} {t.sectors}
                  </Badge>
                </div>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {loading ? (
        <Card className="afcfta-card">
          <CardContent className="flex items-center justify-center h-80">
            <div className="text-center">
              <div className="afcfta-spinner mx-auto" />
              <p className="mt-4 text-[var(--afcfta-muted)]">{t.loading}</p>
            </div>
          </CardContent>
        </Card>
      ) : macroData?.data_by_sector ? (
        <>
          <Card className="afcfta-card">
            <CardHeader className="pb-2">
              <CardTitle className="text-xl text-[var(--text)]">
                📈 {t.evolutionTitle}
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-4">
              <ResponsiveContainer width="100%" height={380}>
                <LineChart data={chartData} margin={{ left: 20, right: 20, top: 10, bottom: 10 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.10)" />
                  <XAxis dataKey="year" stroke="rgba(255,255,255,0.55)" tick={{ fill: '#9aa7b8', fontSize: 12 }} />
                  <YAxis
                    stroke="rgba(255,255,255,0.55)"
                    tick={{ fill: '#9aa7b8', fontSize: 12 }}
                    label={{
                      value: t.gdpPercent,
                      angle: -90,
                      position: 'insideLeft',
                      offset: -5,
                      style: { fill: '#9aa7b8', fontSize: 11 },
                    }}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: 'rgba(17,24,39,0.96)',
                      border: '1px solid rgba(212,137,26,0.18)',
                      borderRadius: '10px',
                      color: '#eae0d0',
                    }}
                  />
                  <Legend wrapperStyle={{ color: '#cbd5e1', fontSize: '12px' }} />
                  {sectorNames.map((sector, index) => (
                    <Line
                      key={sector}
                      type="monotone"
                      dataKey={sector}
                      stroke={seriesColors[index % seriesColors.length]}
                      strokeWidth={2.5}
                      dot={{ r: 4 }}
                      activeDot={{ r: 6 }}
                    />
                  ))}
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <Card className="afcfta-card">
            <CardHeader className="pb-2">
              <CardTitle className="text-xl text-[var(--text)]">
                📊 {t.comparisonTitle}
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-4">
              <ResponsiveContainer width="100%" height={380}>
                <BarChart data={chartData} margin={{ left: 20, right: 20, top: 10, bottom: 10 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.10)" />
                  <XAxis dataKey="year" stroke="rgba(255,255,255,0.55)" tick={{ fill: '#9aa7b8', fontSize: 12 }} />
                  <YAxis
                    stroke="rgba(255,255,255,0.55)"
                    tick={{ fill: '#9aa7b8', fontSize: 12 }}
                    label={{
                      value: t.gdpPercent,
                      angle: -90,
                      position: 'insideLeft',
                      offset: -5,
                      style: { fill: '#9aa7b8', fontSize: 11 },
                    }}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: 'rgba(17,24,39,0.96)',
                      border: '1px solid rgba(212,137,26,0.18)',
                      borderRadius: '10px',
                      color: '#eae0d0',
                    }}
                  />
                  <Legend wrapperStyle={{ color: '#cbd5e1', fontSize: '12px' }} />
                  {sectorNames.map((sector, index) => (
                    <Bar
                      key={sector}
                      dataKey={sector}
                      fill={seriesColors[index % seriesColors.length]}
                      radius={[6, 6, 0, 0]}
                    />
                  ))}
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {gdpGrowthRecords.length > 0 && (
            <Card className="afcfta-card">
              <CardHeader className="pb-2">
                <CardTitle className="text-xl text-[var(--text)]">
                  📈 {t.growthTitle}
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-4">
                <div className="flex flex-wrap gap-3">
                  {gdpGrowthRecords.map((record) => (
                    <div
                      key={record.year}
                      className="rounded-lg border p-3 min-w-[110px]"
                      style={{
                        background: 'rgba(17,24,39,0.55)',
                        borderColor: 'rgba(255,255,255,0.05)',
                      }}
                    >
                      <div className="flex items-center justify-between gap-1">
                        <p className="text-xs text-[var(--afcfta-muted)]">
                          {t.year} {record.year}
                        </p>
                        {record.is_projection && (
                          <span
                            className="text-[9px] font-semibold px-1.5 py-0.5 rounded"
                            style={{ background: 'rgba(155,110,245,0.18)', color: '#c3a3ff' }}
                            title={t.projectionHint}
                          >
                            {t.projection}
                          </span>
                        )}
                      </div>
                      <p className="text-xl font-bold mt-1 text-[var(--text)]">{record.value}%</p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          <Card className="afcfta-card">
            <CardHeader className="pb-2">
              <CardTitle className="text-xl text-[var(--text)]">
                📋 {t.detailsTitle}
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-4">
              <div className="space-y-4">
                {Object.entries(valueAddedSectors).map(([sectorName, records], index) => (
                  <div
                    key={sectorName}
                    className="rounded-xl border p-4"
                    style={{
                      background: 'rgba(255,255,255,0.03)',
                      borderColor: 'rgba(212,137,26,0.12)',
                    }}
                  >
                    <div className="flex items-center justify-between gap-3 flex-wrap mb-3">
                      <h4 className="font-semibold text-[var(--text)]">{sectorName}</h4>
                      <Badge
                        className="border"
                        style={{
                          background: `${seriesColors[index % seriesColors.length]}22`,
                          color: seriesColors[index % seriesColors.length],
                          borderColor: `${seriesColors[index % seriesColors.length]}55`,
                        }}
                      >
                        {records.length} {t.records}
                      </Badge>
                    </div>

                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                      {records.map((record) => (
                        <div
                          key={record.year}
                          className="rounded-lg border p-3"
                          style={{
                            background: 'rgba(17,24,39,0.55)',
                            borderColor: 'rgba(255,255,255,0.05)',
                          }}
                        >
                          <div className="flex items-center justify-between gap-1">
                            <p className="text-xs text-[var(--afcfta-muted)]">
                              {t.year} {record.year}
                            </p>
                            {record.is_projection && (
                              <span
                                className="text-[9px] font-semibold px-1.5 py-0.5 rounded"
                                style={{
                                  background: 'rgba(155,110,245,0.18)',
                                  color: '#c3a3ff',
                                }}
                                title={t.projectionHint}
                              >
                                {t.projection}
                              </span>
                            )}
                          </div>
                          <p className="text-xl font-bold mt-1 text-[var(--text)]">{record.value}%</p>
                          <p className="text-[11px] text-[var(--afcfta-muted)] mt-2 line-clamp-2">
                            {record.indicator_label}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </>
      ) : (
        <Card className="afcfta-card">
          <CardContent className="text-center py-12 text-[var(--afcfta-muted)]">
            {t.noData}
          </CardContent>
        </Card>
      )}
    </div>
  );
}

export default ProductionMacro;

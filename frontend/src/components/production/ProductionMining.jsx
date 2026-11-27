import React, { useState, useEffect, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import axios from 'axios';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { BarChart, Bar, Cell, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import EnhancedCountrySelector from './EnhancedCountrySelector';
import { trDonnee } from '../../i18n/donnees';
import { pick, intlLocale } from '../../i18n/lang';
import OpportunityPdfExport from '../opportunities/OpportunityPdfExport';
import { specMiningPdf } from '../../utils/productionRapportsPdf';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || '';
const API = `${BACKEND_URL}/api`;

function ProductionMining({ language = 'fr' }) {
  const { t } = useTranslation();
  const [selectedCountry, setSelectedCountry] = useState('ZAF');
  const [miningData, setMiningData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [mineral, setMineral] = useState(null);

  // Les chiffres d'un pays ne restent jamais affichés sous le nom d'un autre :
  // la réponse précédente est effacée avant l'appel, et une réponse arrivée
  // après un nouveau choix de pays est ignorée.
  useEffect(() => {
    if (!selectedCountry) return undefined;
    let actif = true;
    setMiningData(null);
    setLoading(true);
    axios.get(`${API}/production/mining/${selectedCountry}`)
      .then((response) => {
        const d = response.data;
        if (actif) setMiningData(typeof d === 'object' && d !== null && !Array.isArray(d) ? d : null);
      })
      .catch((error) => console.error('Error fetching mining data:', error))
      .finally(() => { if (actif) setLoading(false); });
    return () => { actif = false; };
  }, [selectedCountry]);

  const availableYears = useMemo(() => {
    if (Array.isArray(miningData?.years_covered) && miningData.years_covered.length) {
      return miningData.years_covered;
    }
    if (!miningData?.data_by_commodity) return [];
    const years = new Set();
    Object.values(miningData.data_by_commodity).forEach((records) => {
      records.forEach((record) => {
        if (Number.isInteger(record?.year)) years.add(record.year);
      });
    });
    return [...years].sort((a, b) => a - b);
  }, [miningData]);

  const latestYear = miningData?.latest_year || (availableYears.length ? availableYears[availableYears.length - 1] : null);

  // Un graphique ne porte qu'UN minerai : ses unités (tonnes, milliers de
  // barils/jour, milliards de m³, carats) ne se comparent pas sur un même axe.
  const commodities = useMemo(() => Object.keys(miningData?.data_by_commodity || {}), [miningData]);
  const mineralActif = commodities.includes(mineral) ? mineral : commodities[0];
  const serie = useMemo(
    () => [...(miningData?.data_by_commodity?.[mineralActif] || [])]
      .filter((r) => typeof r?.value === 'number')
      .sort((a, b) => a.year - b.year)
      .map((r) => ({ year: r.year, value: r.value, unit: r.unit, estimate: Boolean(r.is_estimate) })),
    [miningData, mineralActif],
  );
  const uniteSerie = trDonnee(serie[serie.length - 1]?.unit || '', language);
  const locale = intlLocale(language);
  const compact = useMemo(
    () => new Intl.NumberFormat(locale, { notation: 'compact', maximumFractionDigits: 1 }),
    [locale],
  );

  // Intitulé de table USGS : « Copper production 2024 » ou
  // « Perlite — Mine production, estimated 2024 ». En français et en arabe,
  // chaque partie est traduite ; en anglais, l'intitulé reste celui de la source.
  const nomTable = (nom) => {
    if (typeof nom !== 'string') return nom;
    const mesure = nom.match(/^(.+) — (.+) (\d{4})$/);
    if (mesure) return `${trDonnee(mesure[1], language)} — ${trDonnee(mesure[2], language)} ${mesure[3]}`;
    const simple = nom.match(/^(.+) production (\d{4})$/);
    if (simple) return pick(language, `${trDonnee(simple[1], language)} — production ${simple[2]}`, nom, `إنتاج ${trDonnee(simple[1], language)} ${simple[2]}`);
    return trDonnee(nom, language);
  };

  // Le 💎 désignait tous les minerais, pétrole et phosphate compris.
  const iconeMinerai = (commodity) => {
    if (commodity === 'Diamonds' || commodity === 'Gemstones') return '💎';
    if (commodity === 'Crude oil' || commodity === 'Natural gas') return '🛢️';
    return '⛏️';
  };

  const formatTooltip = (value, _name, props) => [
    `${value.toLocaleString(locale)} ${trDonnee(props?.payload?.unit || '', language)}`
      + (props?.payload?.estimate ? ` (${t('production.mining.panel.estimate')})` : ''),
    trDonnee(mineralActif, language),
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card className="bg-[image:var(--card-grad)] border-l-4 border-l-[var(--gold)] shadow-xl">
        <CardHeader>
          <CardTitle className="text-3xl font-bold flex items-center gap-3">
            <span>⛏️</span>
            <span>{t('production.mining.panel.title')}</span>
          </CardTitle>
          <CardDescription className="text-[var(--gold)] text-lg">
            {t('production.mining.panel.subtitle')}
            {availableYears.length > 0 && (availableYears.length === 1
              ? ` (${availableYears[0]})`
              : ` (${availableYears[0]}–${availableYears[availableYears.length - 1]})`)}
          </CardDescription>
        </CardHeader>
      </Card>

      {/* Country Selector */}
      <Card>
        <CardContent className="pt-6">
          <EnhancedCountrySelector
            value={selectedCountry}
            onChange={setSelectedCountry}
            label={t('production.mining.panel.country')}
            language={language}
          />
          {miningData && (
            <div className="mt-3">
              <Badge variant="outline" className="text-sm">
                {miningData.total_records} {t('production.mining.panel.records')} • {Object.keys(miningData.data_by_commodity).length} {t('production.mining.panel.minerals')}
              </Badge>
              {latestYear && (
                <Badge variant="outline" className="text-sm ml-2">
                  {t('production.mining.panel.latestData')}: {latestYear}
                </Badge>
              )}
              {!loading && (
                <div className="mt-3 flex justify-end">
                  <OpportunityPdfExport
                    language={language}
                    getSpec={(_, langue) => specMiningPdf(miningData, langue)}
                  />
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Charts */}
      {loading ? (
        <Card>
          <CardContent className="flex items-center justify-center h-96">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[color-mix(in_srgb,var(--gold)_30%,transparent)] mx-auto"></div>
              <p className="mt-4 text-[var(--afcfta-muted)]">{t('production.mining.panel.loading')}</p>
            </div>
          </CardContent>
        </Card>
      ) : miningData && miningData.total_records > 0 ? (
        <>
          {/* Un minerai à la fois, dans son unité */}
          <Card className="shadow-lg">
            <CardHeader className="bg-[color-mix(in_srgb,var(--gold)_8%,var(--afcfta-card))]">
              <CardTitle className="text-xl text-[var(--gold)]">
                📈 {t('production.mining.panel.evolutionTitle')} — {trDonnee(mineralActif, language)}
              </CardTitle>
              <CardDescription data-testid="mining-chart-unit">
                {t('production.mining.panel.unit')} : {uniteSerie}
              </CardDescription>
            </CardHeader>
            <CardContent className="pt-6 space-y-4">
              <div className="flex flex-wrap gap-2" role="group" aria-label={t('production.mining.panel.chooseMineral')}>
                {commodities.map((commodity) => (
                  <button
                    key={commodity}
                    type="button"
                    aria-pressed={commodity === mineralActif}
                    onClick={() => setMineral(commodity)}
                    className={[
                      'px-3 py-1.5 rounded-full border text-sm transition-colors',
                      commodity === mineralActif
                        ? 'bg-[var(--gold)] text-[var(--afcfta-card)] border-[var(--gold)] font-semibold'
                        : 'border-[color-mix(in_srgb,var(--gold)_35%,transparent)] text-[var(--text)] hover:bg-[color-mix(in_srgb,var(--gold)_12%,transparent)]',
                    ].join(' ')}
                  >
                    {iconeMinerai(commodity)} {trDonnee(commodity, language)}
                  </button>
                ))}
              </div>
              <ResponsiveContainer width="100%" height={340}>
                <BarChart data={serie} margin={{ top: 8, right: 16, bottom: 8, left: 8 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="year" />
                  <YAxis width={72} tickFormatter={(v) => compact.format(v)} />
                  <Tooltip
                    formatter={formatTooltip}
                    labelFormatter={(label) => `${t('production.mining.panel.year')} ${label}`}
                  />
                  <Bar dataKey="value" radius={[4, 4, 0, 0]} maxBarSize={72}>
                    {serie.map((point) => (
                      <Cell key={point.year} fill="#d4891a" fillOpacity={point.estimate ? 0.45 : 1} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
              {serie.some((point) => point.estimate) && (
                <p className="text-xs text-[var(--afcfta-muted)]">{t('production.mining.panel.estimateLegend')}</p>
              )}
            </CardContent>
          </Card>

          {/* Details Cards */}
          <Card className="shadow-lg">
            <CardHeader className="bg-gradient-to-r from-gray-50 to-slate-50">
              <CardTitle className="text-xl text-[var(--text)]">
                ⛏️ {t('production.mining.panel.detailsTitle')}
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {Object.entries(miningData.data_by_commodity).map(([commodity, records]) => (
                  <div key={commodity} className="border-l-4 border-[color-mix(in_srgb,var(--gold)_30%,transparent)] pl-4 py-3 bg-[color-mix(in_srgb,var(--gold)_8%,var(--afcfta-card))] rounded-lg">
                    <h4 className="font-bold text-[var(--gold)] text-lg mb-3 flex items-center gap-2">
                      {iconeMinerai(commodity)} {trDonnee(commodity, language)}
                    </h4>
                    <div className="space-y-2">
                      {[...records].sort((x, y) => x.year - y.year).map(record => (
                        <div key={record.year} className="bg-[var(--afcfta-card)] p-3 rounded shadow-sm flex justify-between items-center gap-3">
                          <div>
                            <p className="text-sm text-[var(--afcfta-muted)]">
                              {t('production.mining.panel.year')} {record.year}
                              {record.is_estimate && (
                                <Badge variant="outline" className="text-[10px] ms-2 align-middle">
                                  {t('production.mining.panel.estimate')}
                                </Badge>
                              )}
                            </p>
                            <p className="text-xs text-[var(--afcfta-muted)]">
                              {nomTable(record.usgs_table_name)}
                            </p>
                            <Badge variant="outline" className="text-xs mt-1">
                              {record.source_dataset}
                            </Badge>
                          </div>
                          <div className="text-end shrink-0">
                            <p className="text-xl font-bold text-[var(--gold)]">
                              {record.value.toLocaleString(intlLocale(language))}
                            </p>
                            <p className="text-xs text-[var(--afcfta-muted)]">{trDonnee(record.unit, language)}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </>
      ) : miningData?.coverage ? (
        /* Le serveur dit CE QU'IL A CONSULTÉ et ce que la source en rapporte.
           Une phrase « aucune donnée » laissait le lecteur conclure que la
           plateforme avait perdu la donnée — la qualification produite côté
           serveur ne lui parvenait pas. */
        <Card>
          <CardContent className="py-8" data-testid="mining-coverage">
            <p className="font-semibold text-[var(--text)]">
              {miningData.coverage.status === 'LISTED_BY_USGS_NOT_INGESTED'
                ? t('production.mining.panel.notIngestedTitle')
                : t('production.mining.panel.noProductionTitle')}
            </p>
            <p className="mt-2 text-sm text-[var(--afcfta-muted)] max-w-3xl">
              {trDonnee(miningData.coverage.note, language)}
            </p>
            {miningData.coverage.sources_consulted?.length > 0 && (
              <div className="mt-4 text-xs text-[var(--afcfta-muted)]">
                <p className=" mb-1">{t('production.mining.panel.sourcesConsulted')}</p>
                <ul className="list-disc list-inside space-y-0.5">
                  {miningData.coverage.sources_consulted.map((src) => (
                    <li key={src}>{trDonnee(src, language)}</li>
                  ))}
                </ul>
                {miningData.coverage.usgs_source_url && (
                  <a
                    href={miningData.coverage.usgs_source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-block mt-2 underline text-[var(--gold)]"
                  >
                    {trDonnee(miningData.coverage.usgs_edition, language)}
                  </a>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardContent className="text-center py-12 text-[var(--afcfta-muted)]">
            {t('production.mining.panel.noData')}
          </CardContent>
        </Card>
      )}
    </div>
  );
}

export default ProductionMining;

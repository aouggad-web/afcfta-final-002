import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import '../styles/isic4-table.css';
import { pick } from '../../i18n/lang';

// Ce tableau n'existe qu'en français ; l'arabe s'y ajoute, le français reste
// servi aussi en anglais.
const L = (language, fr, ar) => pick(language, fr, fr, ar);

/**
 * Composant ISIC4DetailTable
 * ═══════════════════════════════════════════════════════════════════════════
 * Affiche les données UNIDO ISIC Rev.4 dans un tableau responsive avec :
 * - Scroll horizontal si trop de colonnes
 * - Colonnes figées (ISIC4, description) pour contexte pendant scroll
 * - Adaptabilité au nombre d'indicateurs par secteur
 * - Formatage des nombres avec unités
 * - Affichage de la source d'données (OFFICIAL_STATISTICS vs UNIDO_DERIVED_ESTIMATE)
 */
const getBackendUrl = () => {
  const viteUrl = import.meta.env.VITE_BACKEND_URL;
  if (viteUrl) return viteUrl;
  return '';
};

// Libellés officiels ISIC Rev.4, divisions manufacturières (Section C, 10-33).
const ISIC_DIVISION_LABELS = {
  '10': 'Produits alimentaires', '11': 'Boissons', '12': 'Produits du tabac',
  '13': 'Textiles', '14': "Articles d'habillement", '15': 'Cuir et articles de cuir',
  '16': 'Bois et articles en bois', '17': 'Papier et articles en papier',
  '18': 'Imprimerie et reproduction', '19': 'Cokéfaction et raffinage',
  '20': 'Produits chimiques', '21': 'Produits pharmaceutiques',
  '22': 'Caoutchouc et plastiques', '23': 'Minéraux non métalliques',
  '24': 'Métallurgie de base', '25': 'Ouvrages en métaux',
  '26': 'Produits informatiques et électroniques', '27': 'Équipements électriques',
  '28': 'Machines et équipements', '29': 'Véhicules automobiles',
  '30': 'Autres matériels de transport', '31': 'Meubles',
  '32': 'Autres industries manufacturières', '33': 'Réparation et installation',
};

// Libellés arabes des mêmes divisions.
const ISIC_DIVISION_LABELS_AR = {
  '10': 'المنتجات الغذائية',
  '11': 'المشروبات',
  '12': 'منتجات التبغ',
  '13': 'المنسوجات',
  '14': 'الملابس',
  '15': 'الجلود ومنتجاتها',
  '16': 'الخشب ومنتجاته',
  '17': 'الورق ومنتجاته',
  '18': 'الطباعة والاستنساخ',
  '19': 'فحم الكوك وتكرير النفط',
  '20': 'المنتجات الكيميائية',
  '21': 'المنتجات الصيدلانية',
  '22': 'المطاط واللدائن',
  '23': 'المنتجات المعدنية اللافلزية',
  '24': 'الفلزات القاعدية',
  '25': 'المنتجات المعدنية المصنّعة',
  '26': 'المنتجات الحاسوبية والإلكترونية',
  '27': 'المعدات الكهربائية',
  '28': 'الآلات والمعدات',
  '29': 'المركبات ذات المحرك',
  '30': 'معدات النقل الأخرى',
  '31': 'الأثاث',
  '32': 'الصناعات التحويلية الأخرى',
  '33': 'الإصلاح والتركيب',
};

/** Groupe les secteurs ISIC4 par division 2 chiffres, conservant l'ordre des divisions. */
function groupSectorsByDivision(sectors, language) {
  const groups = new Map();
  for (const sector of sectors) {
    const division = sector.isic4?.slice(0, 2);
    if (!division) continue;
    if (!groups.has(division)) groups.set(division, []);
    groups.get(division).push(sector);
  }
  return Array.from(groups.keys())
    .sort()
    .map((division) => ({
      division,
      label: L(language, ISIC_DIVISION_LABELS[division], ISIC_DIVISION_LABELS_AR[division]) || division,
      sectors: groups.get(division),
    }));
}

export default function ISIC4DetailTable({ countryISO3 }) {
  const { i18n } = useTranslation();
  const language = i18n.language;
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [timeseriesByISIC, setTimeseriesByISIC] = useState({});
  const [expandedRows, setExpandedRows] = useState(new Set());
  const [loadingByISIC, setLoadingByISIC] = useState({});
  const timeseriesControllersRef = React.useRef({});

  // Charge les données ISIC4 du pays
  useEffect(() => {
    if (!countryISO3) return;

    setLoading(true);
    setError(null);
    setExpandedRows(new Set());
    setTimeseriesByISIC({});

    // Cancel all pending timeseries requests when country changes
    Object.values(timeseriesControllersRef.current).forEach(controller => {
      controller.abort();
    });
    timeseriesControllersRef.current = {};

    const controller = new AbortController();
    const backendUrl = getBackendUrl();
    fetch(`${backendUrl}/api/production/isic4/${countryISO3.toUpperCase()}`, { signal: controller.signal })
      .then((res) => {
        if (!res.ok) throw new Error(`Erreur: ${res.status}`);
        return res.json();
      })
      .then((json) => {
        setData(json);
        setLoading(false);
      })
      .catch((err) => {
        if (err.name !== 'AbortError') {
          setError(err.message);
          setLoading(false);
        }
      });

    return () => controller.abort();
  }, [countryISO3]);

  // Charge la série temporelle quand un secteur est sélectionné
  const handleRowExpand = (isic4Code) => {
    if (expandedRows.has(isic4Code)) {
      expandedRows.delete(isic4Code);
      setExpandedRows(new Set(expandedRows));
      setTimeseriesByISIC((prev) => {
        const updated = { ...prev };
        delete updated[isic4Code];
        return updated;
      });
      // Cancel the timeseries request for this code
      if (timeseriesControllersRef.current[isic4Code]) {
        timeseriesControllersRef.current[isic4Code].abort();
        delete timeseriesControllersRef.current[isic4Code];
      }
    } else {
      // Suppress duplicate requests: if already loading, don't start another
      if (loadingByISIC[isic4Code]) return;

      const controller = new AbortController();
      timeseriesControllersRef.current[isic4Code] = controller;
      setLoadingByISIC((prev) => ({ ...prev, [isic4Code]: true }));

      const backendUrl = getBackendUrl();
      fetch(`${backendUrl}/api/production/isic4/${countryISO3.toUpperCase()}/${isic4Code}`, { signal: controller.signal })
        .then((res) => {
          if (!res.ok) throw new Error(`Erreur: ${res.status}`);
          return res.json();
        })
        .then((json) => {
          // Only update if this is still the current controller for this code
          if (timeseriesControllersRef.current[isic4Code] === controller) {
            setTimeseriesByISIC((prev) => ({ ...prev, [isic4Code]: json }));
            expandedRows.add(isic4Code);
            setExpandedRows(new Set(expandedRows));
          }
        })
        .catch((err) => {
          if (err.name !== 'AbortError') {
            console.error('Erreur chargement série:', err);
          }
        })
        .finally(() => {
          // Only delete the controller if it's still the one we created
          if (timeseriesControllersRef.current[isic4Code] === controller) {
            delete timeseriesControllersRef.current[isic4Code];
          }
          setLoadingByISIC((prev) => {
            const updated = { ...prev };
            delete updated[isic4Code];
            return updated;
          });
        });
    }
  };

  if (loading) {
    return <div className="isic4-loading">⏳ {L(language, 'Chargement données ISIC4...', 'جارٍ تحميل بيانات ISIC4…')}</div>;
  }

  if (error) {
    return <div className="isic4-error">❌ {error}</div>;
  }

  if (!data || !data.sectors || data.sectors.length === 0) {
    return <div className="isic4-empty">{L(language, 'Aucune donnée ISIC4 pour ce pays', 'لا توجد بيانات ISIC4 لهذا البلد')}</div>;
  }

  // Collecte tous les indicateurs uniques
  const allIndicators = new Set();
  data.sectors.forEach((sector) => {
    Object.keys(sector.indicators || {}).forEach((ind) => allIndicators.add(ind));
  });
  const indicatorsList = Array.from(allIndicators).sort();

  const formatValue = (value, unit) => {
    if (value === undefined || value === null) return '—';
    const normalizedUnit = unit === 'current_USD' ? 'USD' : unit;
    if (normalizedUnit === 'percent') return `${value.toFixed(1)}%`;
    if (normalizedUnit === 'USD') {
      if (value >= 1_000_000_000) return `${(value / 1_000_000_000).toFixed(2)}B USD`;
      if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M USD`;
      return `${value.toLocaleString('fr-FR')} USD`;
    }
    if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(2)}M ${normalizedUnit}`;
    if (value >= 1_000) return `${(value / 1_000).toFixed(1)}k ${normalizedUnit}`;
    return `${value.toLocaleString('fr-FR')} ${normalizedUnit}`;
  };

  const getDataNatureBadge = (dataNature) => {
    if (dataNature === 'OFFICIAL_STATISTICS') {
      return <span className="badge badge-official">✓ {L(language, 'Stats officielles', 'إحصاءات رسمية')}</span>;
    }
    if (dataNature === 'UNIDO_DERIVED_ESTIMATE') {
      return <span className="badge badge-estimate">≈ {L(language, 'Estimation UNIDO', 'تقدير UNIDO')}</span>;
    }
    return <span className="badge badge-unknown">?</span>;
  };

  const dataQuality = data.data_quality || {};
  const isFullyEstimated = dataQuality.is_fully_estimated;
  const hasOfficial = dataQuality.has_official_statistics;

  return (
    <div className="isic4-container">
      <div className="isic4-header">
        <h2>{L(language, 'Secteurs manufacturiers', 'القطاعات الصناعية التحويلية')} — {data.country_name} ({data.country_iso3})</h2>
        <div className="isic4-metadata">
          <span className="meta-item">
            <strong>{data.total_sectors}</strong> {L(language, 'secteurs', 'قطاعاً')}
          </span>
          <span className="meta-item">
            {L(language, 'Période', 'الفترة')} : {data.years_covered}
          </span>
          <span className="meta-item source">
            {L(language, 'Source', 'المصدر')} : <em>{data.source}</em>
          </span>
          <span className="meta-item data-types">
            {isFullyEstimated
              ? L(language, '≈ Estimations UNIDO uniquement', '≈ تقديرات UNIDO فقط')
              : hasOfficial
              ? L(language, '📊 Données officielles + estimations UNIDO', '📊 بيانات رسمية + تقديرات UNIDO')
              : L(language, '📊 Données UNIDO', '📊 بيانات UNIDO')}
          </span>
        </div>
      </div>

      {/* Bannière : pays sans statistiques officielles → estimations UNIDO */}
      {isFullyEstimated && (
        <div className="isic4-estimate-banner" role="status">
          {L(
            language,
            <>
              <strong>≈ Aucune statistique officielle disponible pour ce pays.</strong>{' '}
              Les valeurs affichées sont des <em>estimations dérivées par UNIDO</em>
              {' '}(UNIDO_DERIVED_ESTIMATE) et doivent être interprétées avec prudence.
            </>,
            <>
              <strong>≈ لا تتوفر أي إحصاءات رسمية لهذا البلد.</strong>{' '}
              القيم المعروضة <em>تقديرات مشتقة من UNIDO</em>
              {' '}(UNIDO_DERIVED_ESTIMATE) ويجب تفسيرها بحذر.
            </>,
          )}
        </div>
      )}

      {/* Légende des badges */}
      <div className="isic4-legend">
        <span className="legend-item">
          <span className="badge badge-official">✓ {L(language, 'Réel', 'فعلي')}</span> = {L(language, 'secteur 100% données réelles', 'قطاع ببيانات فعلية 100%')} (OFFICIAL_STATISTICS)
        </span>
        <span className="legend-item">
          <span className="badge badge-mixed">◐ {L(language, 'Mixte', 'مختلط')}</span> = {L(language, "réel + estimations selon l'indicateur", 'فعلي + تقديرات حسب المؤشر')}
        </span>
        <span className="legend-item">
          <span className="badge badge-estimate">≈ {L(language, 'Estimé', 'تقديري')}</span> = {L(language, 'secteur 100% estimations UNIDO', 'قطاع بتقديرات UNIDO بنسبة 100%')} (UNIDO_DERIVED_ESTIMATE)
        </span>
      </div>

      {/* Tableau principale avec scroll horizontal */}
      <div className="isic4-table-wrapper">
        <table className="isic4-table">
          <thead>
            <tr>
              {/* Colonnes figées */}
              <th className="sticky-col col-isic4">{L(language, 'Code ISIC', 'رمز ISIC')}</th>
              <th className="sticky-col col-description">{L(language, 'Description secteur', 'وصف القطاع')}</th>

              {/* Colonnes indicateurs (scrollable) */}
              {indicatorsList.map((indicator) => (
                <th key={indicator} className="col-indicator">
                  <div className="indicator-header">
                    <span className="indicator-name">{formatIndicatorLabel(indicator, language)}</span>
                  </div>
                </th>
              ))}
              <th className="col-expand"></th>
            </tr>
          </thead>
          <tbody>
            {groupSectorsByDivision(data.sectors, language).map(({ division, label, sectors }) => (
              <React.Fragment key={division}>
                <tr className="division-header-row">
                  <td colSpan={2 + indicatorsList.length + 1} className="division-header-cell">
                    <span className="division-header-code">ISIC {division}</span>
                    {label}
                    <span className="division-header-count">
                      ({sectors.length} {sectors.length > 1 ? L(language, 'lignes ISIC4', 'بنود ISIC4') : L(language, 'ligne ISIC4', 'بند ISIC4')})
                    </span>
                  </td>
                </tr>
                {sectors.map((sector, idx) => (
              <React.Fragment key={sector.isic4 || idx}>
                {/* Ligne principale */}
                <tr
                  className={`sector-row ${expandedRows.has(sector.isic4) ? 'expanded' : ''}`}
                  onClick={() => handleRowExpand(sector.isic4)}
                  style={{ cursor: 'pointer' }}
                >
                  {/* Colonnes figées */}
                  <td className="sticky-col col-isic4">{sector.isic4}</td>
                  <td className="sticky-col col-description">
                    <span className="sector-description-text">{sector.description}</span>
                    {getSectorNatureBadge(sector, language)}
                  </td>

                  {/* Indicateurs */}
                  {indicatorsList.map((indicator) => {
                    const indData = sector.indicators[indicator];
                    return (
                      <td key={indicator} className="col-indicator">
                        {indData ? (
                          <div className="cell-value">
                            <div className="value">
                              {formatValue(indData.value, indData.unit)}
                            </div>
                            <div className="year">{indData.year}</div>
                            {getDataNatureBadge(indData.data_nature)}
                          </div>
                        ) : (
                          <span className="cell-empty">—</span>
                        )}
                      </td>
                    );
                  })}

                  {/* Bouton expand */}
                  <td className="col-expand">
                    <button
                      className={`expand-btn ${expandedRows.has(sector.isic4) ? 'open' : ''}`}
                      onClick={(e) => {
                        e.stopPropagation();
                        handleRowExpand(sector.isic4);
                      }}
                      title={
                        expandedRows.has(sector.isic4)
                          ? L(language, 'Fermer série temporelle', 'إغلاق السلسلة الزمنية')
                          : L(language, 'Ouvrir série temporelle 2018-2024', 'فتح السلسلة الزمنية 2018-2024')
                      }
                    >
                      {expandedRows.has(sector.isic4) ? '▼' : '▶'}
                    </button>
                  </td>
                </tr>

                {/* Ligne d'expansion : série temporelle */}
                {expandedRows.has(sector.isic4) && timeseriesByISIC[sector.isic4] && (
                  <tr className="timeseries-row">
                    <td colSpan={2 + indicatorsList.length + 1} className="timeseries-cell">
                      <TimeseriesChart timeseries={timeseriesByISIC[sector.isic4]} />
                    </td>
                  </tr>
                )}
              </React.Fragment>
                ))}
              </React.Fragment>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pied de page */}
      <div className="isic4-footer">
        {L(
          language,
          <p>
            💡 Cliquez sur une ligne pour déplier le <strong>tableau détaillé complet</strong> du
            secteur : tous les indicateurs, toutes les années (2018-2024), avec pour chaque valeur
            l'indication réel (✓) ou estimé (≈). Données issues du portail UNIDO (IDSB + INDSTAT,
            ISIC Rev.4).
          </p>,
          <p>
            💡 انقر على سطر لعرض <strong>الجدول المفصل الكامل</strong> للقطاع: جميع
            المؤشرات وجميع السنوات (2018-2024)، مع بيان ما إذا كانت كل قيمة فعلية (✓) أو تقديرية (≈).
            البيانات مصدرها بوابة UNIDO (IDSB + INDSTAT، ISIC Rev.4).
          </p>,
        )}
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Composant TimeseriesChart
// ─────────────────────────────────────────────────────────────────────────────

function TimeseriesChart({ timeseries }) {
  const { i18n } = useTranslation();
  const language = i18n.language;
  if (!timeseries || !timeseries.series) return null;

  const series = timeseries.series;
  const indicators = Object.keys(series);
  if (indicators.length === 0) {
    return (
      <div className="timeseries-chart">
        <h4>{L(language, 'Détail complet', 'التفاصيل الكاملة')} : {timeseries.isic_description}</h4>
        <p className="detail-empty-note">{L(language, 'Aucune donnée détaillée pour ce secteur.', 'لا توجد بيانات مفصلة لهذا القطاع.')}</p>
      </div>
    );
  }

  // Toutes les années couvertes, tous indicateurs confondus (ordre croissant)
  const yearsSet = new Set();
  indicators.forEach((ind) => (series[ind] || []).forEach((pt) => yearsSet.add(pt.year)));
  const years = Array.from(yearsSet).sort((a, b) => a - b);

  // Résumé de la nature d'un indicateur (réel / estimé / mixte)
  const indicatorNature = (points) => {
    const natures = points.map((p) => p.data_nature);
    const hasOfficial = natures.includes('OFFICIAL_STATISTICS');
    const hasEstimate = natures.includes('UNIDO_DERIVED_ESTIMATE');
    if (hasOfficial && hasEstimate) return 'mixed';
    if (hasOfficial) return 'official';
    if (hasEstimate) return 'estimated';
    return 'unknown';
  };

  return (
    <div className="timeseries-chart">
      <h4>
        {L(language, 'Détail complet', 'التفاصيل الكاملة')} — {timeseries.isic_description}{' '}
        <span className="detail-isic-code">({timeseries.isic4})</span>
      </h4>

      <div className="detail-table-wrapper">
        <table className="detail-table">
          <thead>
            <tr>
              <th className="detail-indicator-col">{L(language, 'Indicateur', 'المؤشر')}</th>
              {years.map((y) => (
                <th key={y} className="detail-year-col">{y}</th>
              ))}
              <th className="detail-nature-col">{L(language, 'Nature', 'الطبيعة')}</th>
            </tr>
          </thead>
          <tbody>
            {indicators.map((ind) => {
              const points = series[ind] || [];
              const byYear = {};
              points.forEach((pt) => {
                byYear[pt.year] = pt;
              });
              const nature = indicatorNature(points);
              return (
                <tr key={ind}>
                  <td className="detail-indicator-col">{formatIndicatorLabel(ind, language)}</td>
                  {years.map((y) => {
                    const pt = byYear[y];
                    if (!pt || pt.value === undefined || pt.value === null) {
                      return (
                        <td key={y} className="detail-cell detail-empty">—</td>
                      );
                    }
                    const isOfficial = pt.data_nature === 'OFFICIAL_STATISTICS';
                    return (
                      <td
                        key={y}
                        className={`detail-cell ${isOfficial ? 'detail-official' : 'detail-estimate'}`}
                        title={isOfficial ? L(language, 'Donnée réelle (statistique officielle)', 'بيانات فعلية (إحصاء رسمي)') : L(language, 'Estimation dérivée UNIDO', 'تقدير مشتق من UNIDO')}
                      >
                        <span className="detail-value">{pt.value.toLocaleString('fr-FR')}</span>
                        <span className="detail-mark">{isOfficial ? '✓' : '≈'}</span>
                      </td>
                    );
                  })}
                  <td className="detail-nature-col">
                    {nature === 'official' && (
                      <span className="badge badge-official">✓ {L(language, 'Réel', 'فعلي')}</span>
                    )}
                    {nature === 'estimated' && (
                      <span className="badge badge-estimate">≈ {L(language, 'Estimé', 'تقديري')}</span>
                    )}
                    {nature === 'mixed' && (
                      <span className="badge badge-mixed">◐ {L(language, 'Mixte', 'مختلط')}</span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <p className="detail-legend">
        {L(language, '✓ = donnée réelle (officielle) · ≈ = estimation UNIDO · — = non disponible', '✓ = بيانات فعلية (رسمية) · ≈ = تقدير UNIDO · — = غير متوفر')}
      </p>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Utilitaires
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Nature des données d'un secteur ISIC (encadré) à partir de ses indicateurs :
 * - 'official'  : tous les indicateurs affichés sont OFFICIAL_STATISTICS
 * - 'estimated' : tous les indicateurs affichés sont des estimations UNIDO
 * - 'mixed'     : mélange officiel + estimation
 * - null        : aucun indicateur
 */
function getSectorDataNature(sector) {
  const natures = Object.values(sector.indicators || {}).map((ind) => ind.data_nature);
  if (natures.length === 0) return null;
  const hasOfficial = natures.includes('OFFICIAL_STATISTICS');
  const hasEstimate = natures.includes('UNIDO_DERIVED_ESTIMATE');
  if (hasOfficial && hasEstimate) return 'mixed';
  if (hasOfficial) return 'official';
  if (hasEstimate) return 'estimated';
  return null;
}

function getSectorNatureBadge(sector, language) {
  const nature = getSectorDataNature(sector);
  if (nature === 'estimated') {
    return (
      <span className="sector-nature badge badge-estimate" title={L(language, 'Toutes les valeurs de ce secteur sont des estimations UNIDO', 'جميع قيم هذا القطاع تقديرات UNIDO')}>
        ≈ {L(language, 'Estimé', 'تقديري')}
      </span>
    );
  }
  if (nature === 'mixed') {
    return (
      <span className="sector-nature badge badge-mixed" title={L(language, 'Ce secteur mêle données réelles (officielles) et estimations UNIDO', 'يجمع هذا القطاع بين بيانات فعلية (رسمية) وتقديرات UNIDO')}>
        ◐ {L(language, 'Mixte', 'مختلط')}
      </span>
    );
  }
  if (nature === 'official') {
    return (
      <span className="sector-nature badge badge-official" title={L(language, 'Toutes les valeurs affichées de ce secteur sont des données réelles (statistiques officielles)', 'جميع القيم المعروضة لهذا القطاع بيانات فعلية (إحصاءات رسمية)')}>
        ✓ {L(language, 'Réel', 'فعلي')}
      </span>
    );
  }
  return null;
}

function formatIndicatorLabel(indicator, language) {
  const labels = {
    output_usd: 'Production (USD)',
    imports_world_usd: 'Imports (USD)',
    exports_world_usd: 'Exports (USD)',
    apparent_consumption_usd: 'Consommation apparente (USD)',
    establishments: 'Établissements',
    employees: 'Salariés',
    female_employees: 'Femmes salariées',
    wages_salaries_usd: 'Masse salariale (USD)',
    output_usd_official: 'Production (USD)',
    value_added_usd: 'Valeur ajoutée (USD)',
    gross_fixed_capital_formation_usd: 'FBCF (USD)',
  };
  const labelsAr = {
    output_usd: 'الإنتاج (USD)',
    imports_world_usd: 'الواردات (USD)',
    exports_world_usd: 'الصادرات (USD)',
    apparent_consumption_usd: 'الاستهلاك الظاهري (USD)',
    establishments: 'المنشآت',
    employees: 'الأجراء',
    female_employees: 'الأجيرات',
    wages_salaries_usd: 'كتلة الأجور (USD)',
    output_usd_official: 'الإنتاج (USD)',
    value_added_usd: 'القيمة المضافة (USD)',
    gross_fixed_capital_formation_usd: 'تكوين رأس المال الثابت الإجمالي (USD)',
  };
  return L(language, labels[indicator], labelsAr[indicator]) || indicator;
}

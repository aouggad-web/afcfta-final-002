import React, { useState, useEffect } from 'react';
import '../styles/isic4-table.css';

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

export default function ISIC4DetailTable({ countryISO3 }) {
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
    return <div className="isic4-loading">⏳ Chargement données ISIC4...</div>;
  }

  if (error) {
    return <div className="isic4-error">❌ {error}</div>;
  }

  if (!data || !data.sectors || data.sectors.length === 0) {
    return <div className="isic4-empty">Aucune donnée ISIC4 pour ce pays</div>;
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
      return <span className="badge badge-official">✓ Stats officielles</span>;
    }
    if (dataNature === 'UNIDO_DERIVED_ESTIMATE') {
      return <span className="badge badge-estimate">≈ Estimation UNIDO</span>;
    }
    return <span className="badge badge-unknown">?</span>;
  };

  return (
    <div className="isic4-container">
      <div className="isic4-header">
        <h2>Secteurs manufacturiers — {data.country_name} ({data.country_iso3})</h2>
        <div className="isic4-metadata">
          <span className="meta-item">
            <strong>{data.total_sectors}</strong> secteurs
          </span>
          <span className="meta-item">
            Période : {data.years_covered}
          </span>
          <span className="meta-item source">
            Source : <em>{data.source}</em>
          </span>
          <span className="meta-item data-types">
            📊 Inclut données officielles et estimations UNIDO
          </span>
        </div>
      </div>

      {/* Légende des badges */}
      <div className="isic4-legend">
        <span className="legend-item">
          <span className="badge badge-official">✓ Stats officielles</span> = OFFICIAL_STATISTICS
        </span>
        <span className="legend-item">
          <span className="badge badge-estimate">≈ Estimation</span> = UNIDO_DERIVED_ESTIMATE
        </span>
      </div>

      {/* Tableau principale avec scroll horizontal */}
      <div className="isic4-table-wrapper">
        <table className="isic4-table">
          <thead>
            <tr>
              {/* Colonnes figées */}
              <th className="sticky-col col-isic4">Code ISIC</th>
              <th className="sticky-col col-description">Description secteur</th>

              {/* Colonnes indicateurs (scrollable) */}
              {indicatorsList.map((indicator) => (
                <th key={indicator} className="col-indicator">
                  <div className="indicator-header">
                    <span className="indicator-name">{formatIndicatorLabel(indicator)}</span>
                  </div>
                </th>
              ))}
              <th className="col-expand"></th>
            </tr>
          </thead>
          <tbody>
            {data.sectors.map((sector, idx) => (
              <React.Fragment key={sector.isic4 || idx}>
                {/* Ligne principale */}
                <tr
                  className={`sector-row ${expandedRows.has(sector.isic4) ? 'expanded' : ''}`}
                  onClick={() => handleRowExpand(sector.isic4)}
                  style={{ cursor: 'pointer' }}
                >
                  {/* Colonnes figées */}
                  <td className="sticky-col col-isic4">{sector.isic4}</td>
                  <td className="sticky-col col-description">{sector.description}</td>

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
                          ? 'Fermer série temporelle'
                          : 'Ouvrir série temporelle 2018-2024'
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
          </tbody>
        </table>
      </div>

      {/* Pied de page */}
      <div className="isic4-footer">
        <p>
          💡 Cliquez sur une ligne pour voir la série temporelle complète 2018-2024 du secteur.
          Les données sont issues directement du portail UNIDO (IDSB + INDSTAT, ISIC Rev.4).
        </p>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Composant TimeseriesChart
// ─────────────────────────────────────────────────────────────────────────────

function TimeseriesChart({ timeseries }) {
  if (!timeseries || !timeseries.series) return null;

  return (
    <div className="timeseries-chart">
      <h4>Série temporelle : {timeseries.isic_description}</h4>
      <div className="series-list">
        {Object.entries(timeseries.series).map(([indicator, years]) => (
          <div key={indicator} className="series-item">
            <h5>{formatIndicatorLabel(indicator)}</h5>
            <table className="series-table">
              <thead>
                <tr>
                  <th>Année</th>
                  <th>Valeur</th>
                  <th>Source</th>
                </tr>
              </thead>
              <tbody>
                {years.map((y, idx) => (
                  <tr key={idx}>
                    <td>{y.year}</td>
                    <td>{y.value.toLocaleString('fr-FR')}</td>
                    <td>
                      <span
                        className={
                          y.data_nature === 'OFFICIAL_STATISTICS'
                            ? 'badge badge-official'
                            : 'badge badge-estimate'
                        }
                      >
                        {y.data_nature === 'OFFICIAL_STATISTICS' ? '✓ Officiel' : '≈ Estimation'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Utilitaires
// ─────────────────────────────────────────────────────────────────────────────

function formatIndicatorLabel(indicator) {
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
  return labels[indicator] || indicator;
}

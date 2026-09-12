/**
 * Rapport PDF du module Production — structure manufacturière ISIC Rev.4.
 *
 * Réutilise le bâtisseur déclaratif de utils/opportunityPdf.js : même bandeau,
 * mêmes cartes KPI, même tableau à en-tête foncé, même pied paginé. Seul le
 * libellé du module change, via `moduleLabel`. Dupliquer la mise en page aurait
 * fait diverger deux chartes à la première retouche.
 *
 * Règle qui gouverne ce fichier : **la nature de la donnée voyage avec elle**.
 * Un PDF se détache de l'écran, circule par courriel et se retrouve en réunion
 * sans son contexte. Un tableau de structure estimée qui ne dirait pas qu'il est
 * estimé serait lu comme une mesure. La nature figure donc à trois endroits —
 * le sous-titre, un encadré de méthode en tête, et une colonne par ligne.
 */
import { buildOpportunityPdf } from './opportunityPdf';

const I18N = {
  fr: {
    module: 'MODULE PRODUCTION',
    title: 'Structure manufacturière — ISIC Rev.4',
    measured: 'Données mesurées UNIDO',
    estimated: 'Structure estimée',
    classes: 'Classes ISIC 4',
    divisions: 'Divisions ISIC 2',
    nature: 'Nature',
    method: 'Méthode et portée',
    colCode: 'ISIC 4',
    colLabel: 'Libellé',
    colValue: 'Indicateur principal',
    colNature: 'Nature',
    natEstimated: 'estimé',
    natOfficial: 'officiel',
    natDerived: 'dérivé',
    division: 'Division',
    noValue: 'donnée non publiée',
    detail: 'Détail par classe — indicateurs IDSB et INDSTAT par année',
    colIndicator: 'Indicateur',
    noSeries: 'Aucune série temporelle publiée pour cette classe.',
    summary: 'Vue d’ensemble',
    methodEstimated: [
      "UNIDO ne publie pas de statistiques au niveau de la classe ISIC 4 chiffres pour ce pays. La part de valeur ajoutée manufacturière de chaque division ISIC 2 chiffres — celle-là réelle — est répartie à parts égales entre les classes de cette division, selon la nomenclature UNSD.",
      "Conséquence directe : toutes les classes d'une même division portent la même valeur. Ces chiffres situent un secteur dans l'appareil productif ; ils ne permettent pas de comparer deux classes entre elles, ni de fonder une décision d'investissement sur l'écart entre elles.",
      "La couverture se limite aux secteurs principaux du pays, et non aux 24 divisions manufacturières 10-33. Une division absente de ce rapport n'est pas nulle : elle n'est pas renseignée.",
      "Aucune série temporelle n'existe à ce niveau pour ce pays.",
    ],
    methodMeasured: [
      "Données UNIDO au niveau de la classe ISIC Rev.4, 2018-2024. Deux origines coexistent et sont distinguées ligne à ligne : INDSTAT fournit des statistiques officielles (production, valeur ajoutée, emplois), IDSB des estimations dérivées par UNIDO (importations, exportations, consommation apparente, production).",
      "La colonne « Nature » porte cette distinction. Une estimation dérivée reste une estimation, même produite par UNIDO.",
    ],
  },
  en: {
    module: 'PRODUCTION MODULE',
    title: 'Manufacturing structure — ISIC Rev.4',
    measured: 'UNIDO measured data',
    estimated: 'Estimated structure',
    classes: 'ISIC 4 classes',
    divisions: 'ISIC 2 divisions',
    nature: 'Nature',
    method: 'Method and scope',
    colCode: 'ISIC 4',
    colLabel: 'Label',
    colValue: 'Headline indicator',
    colNature: 'Nature',
    natEstimated: 'estimated',
    natOfficial: 'official',
    natDerived: 'derived',
    division: 'Division',
    noValue: 'not published',
    detail: 'Class detail — IDSB and INDSTAT indicators by year',
    colIndicator: 'Indicator',
    noSeries: 'No time series published for this class.',
    summary: 'Overview',
    methodEstimated: [
      'UNIDO publishes no ISIC 4-digit class statistics for this country. Each ISIC 2-digit division’s manufacturing value-added share — that figure being real — is split equally across the classes of the division, per the UNSD nomenclature.',
      'Direct consequence: every class within a division carries the same value. These figures place a sector within the productive base; they cannot rank two classes against each other, nor support an investment decision based on the gap between them.',
      'Coverage is limited to the country’s main sectors, not all 24 manufacturing divisions 10-33. A division missing from this report is not zero: it is not documented.',
      'No time series exists at this level for this country.',
    ],
    methodMeasured: [
      'UNIDO data at ISIC Rev.4 class level, 2018-2024. Two origins coexist and are distinguished row by row: INDSTAT provides official statistics (output, value added, employment), IDSB provides UNIDO-derived estimates (imports, exports, apparent consumption, output).',
      'The "Nature" column carries that distinction. A derived estimate remains an estimate, even when produced by UNIDO.',
    ],
  },
};

/**
 * Construit le rapport.
 *
 * @param {object}   params
 * @param {string}   params.countryIso3
 * @param {string}   params.countryName
 * @param {'fr'|'en'} params.language
 * @param {string}   params.dataBasis       UNIDO_MEASURED | ESTIMATED_FROM_ISIC2
 * @param {Array}    params.divisions       [{division, label, sectors}] tel que groupé à l'écran
 * @param {string}   [params.source]
 * @param {Function} params.formatIndicatorValue
 * @param {object}   params.indicatorLabels  libellés d'indicateurs dans la langue
 * @param {Array}    params.headlineOrder    ordre de préférence de l'indicateur mis en avant
 * @param {object}   [params.timeseries]     {isic4: {isic_description, series}} — détail IDSB/INDSTAT
 * @param {Array}    [params.indicatorOrder] ordre d'affichage des indicateurs dans le détail
 */
export function buildProductionPdf({
  countryIso3,
  countryName,
  language = 'fr',
  dataBasis,
  divisions = [],
  source,
  formatIndicatorValue,
  indicatorLabels = {},
  headlineOrder = [],
  timeseries = null,
  indicatorOrder = [],
}) {
  const t = I18N[language] || I18N.fr;
  const isEstimated = dataBasis === 'ESTIMATED_FROM_ISIC2';
  const classCount = divisions.reduce((n, d) => n + d.sectors.length, 0);

  const natureOf = (indicators) => {
    if (isEstimated) return t.natEstimated;
    const fields = Object.keys(indicators || {});
    return fields.some((f) => indicators[f].data_nature === 'OFFICIAL_STATISTICS')
      ? t.natOfficial
      : t.natDerived;
  };

  const headlineOf = (indicators) => {
    const field = headlineOrder.find(
      (f) => indicators?.[f]?.value !== undefined && indicators?.[f]?.value !== null,
    );
    if (!field) return t.noValue;
    const label = indicatorLabels[field] || field;
    const year = indicators[field].year ? ` (${indicators[field].year})` : '';
    return `${formatIndicatorValue(field, indicators[field].value)} — ${label}${year}`;
  };

  // Détail d'une classe : indicateurs en lignes, années en colonnes. C'est la
  // même lecture qu'à l'écran au clic, mais figée dans le document — un PDF qui
  // ne porterait que l'indicateur principal n'aurait pas le détail demandé.
  const detailSection = (sector) => {
    const entry = timeseries?.[sector.isic4];
    const series = entry?.series || {};
    const fields = indicatorOrder.filter((f) => series[f]?.length);
    const title = `ISIC ${sector.isic4} · ${sector.isic_description || sector.description || ''}`.trim();

    if (!fields.length) {
      return { title, paragraphs: [t.noSeries] };
    }
    const years = Array.from(
      new Set(fields.flatMap((f) => series[f].map((pt) => pt.year))),
    ).sort((a, b) => a - b);

    return {
      title,
      table: {
        columns: [
          { key: 'indicator', label: t.colIndicator, width: 2.4 },
          ...years.map((y) => ({ key: `y${y}`, label: String(y), width: 1, align: 'right' })),
          { key: 'nature', label: t.colNature, width: 0.9 },
        ],
        rows: fields.map((field) => {
          const byYear = Object.fromEntries(series[field].map((pt) => [pt.year, pt]));
          const nature = series[field][0]?.data_nature;
          const row = {
            indicator: indicatorLabels[field] || field,
            nature: nature === 'OFFICIAL_STATISTICS' ? t.natOfficial : t.natDerived,
          };
          years.forEach((y) => {
            row[`y${y}`] = byYear[y] ? formatIndicatorValue(field, byYear[y].value) : '—';
          });
          return row;
        }),
      },
    };
  };

  const sections = [
    {
      title: t.method,
      paragraphs: isEstimated ? t.methodEstimated : t.methodMeasured,
    },
    ...divisions.map((d) => ({
      title: `${t.summary} — ISIC ${d.division} · ${d.label}`,
      table: {
        columns: [
          { key: 'code', label: t.colCode, width: 0.8 },
          { key: 'label', label: t.colLabel, width: 2.6 },
          { key: 'value', label: t.colValue, width: 2.4, align: 'right' },
          { key: 'nature', label: t.colNature, width: 0.9 },
        ],
        rows: d.sectors.map((sector) => ({
          code: sector.isic4,
          label: sector.isic_description || sector.description || '—',
          value: headlineOf(sector.indicators),
          nature: natureOf(sector.indicators),
        })),
      },
    })),
    // Le détail n'existe que pour les pays mesurés : pour les pays estimés, la
    // section « Méthode » dit déjà qu'aucune série n'est publiée à ce niveau, et
    // répéter une absence classe par classe n'apprendrait rien.
    ...(timeseries
      ? [{ title: t.detail, paragraphs: [] }].concat(
        divisions.flatMap((d) => d.sectors.map(detailSection)),
      )
      : []),
  ];

  return buildOpportunityPdf({
    moduleLabel: t.module,
    badge: isEstimated ? t.estimated : t.measured,
    title: `${t.title} — ${countryName || countryIso3}`,
    subtitle: isEstimated
      ? (language === 'fr'
        ? 'Estimation de structure dérivée des divisions ISIC 2 — ne pas lire comme une mesure'
        : 'Structural estimate derived from ISIC 2 divisions — not to be read as a measurement')
      : (language === 'fr'
        ? 'Données UNIDO au niveau de la classe — nature indiquée ligne à ligne'
        : 'UNIDO class-level data — nature stated row by row'),
    language,
    kpis: [
      { label: t.classes, value: String(classCount) },
      { label: t.divisions, value: String(divisions.length) },
      {
        label: t.nature,
        value: isEstimated ? t.estimated : t.measured,
        accent: isEstimated ? 'gold' : 'green',
      },
    ],
    sections,
    source,
  });
}

export function productionPdfFilename(countryIso3, dataBasis) {
  const date = new Date().toISOString().split('T')[0];
  const nature = dataBasis === 'ESTIMATED_FROM_ISIC2' ? 'estime' : 'mesure';
  return ['ZLECAf_Production_ISIC4', countryIso3, nature, date].join('_');
}

export default { buildProductionPdf, productionPdfFilename };

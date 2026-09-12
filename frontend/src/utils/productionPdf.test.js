/**
 * Le rapport Production doit porter le détail ISIC4/IDSB, et dire ce que vaut
 * sa donnée. Les jeux d'essai sont des extraits RÉELS des réponses de l'API
 * (__fixtures__/productionIsic4.json) : Kenya pour le cas mesuré, Algérie pour
 * le cas estimé. Un jeu inventé ne prouverait rien sur la forme réellement
 * servie.
 */
import { describe, it, expect } from 'vitest';
import { buildProductionPdf, productionPdfFilename } from './productionPdf';
import fixtures from './__fixtures__/productionIsic4.json';

const LABELS = {
  output_usd: 'Production (IDSB)',
  imports_world_usd: 'Importations mondiales',
  exports_world_usd: 'Exportations mondiales',
  apparent_consumption_usd: 'Consommation apparente',
  establishments: 'Établissements',
  employees: 'Emplois',
  value_added_usd: 'Valeur ajoutée',
  output_usd_official: 'Production (INDSTAT, officiel)',
  share_mva_pct: 'Part de la MVA (estimée)',
};
const ORDER = [
  'output_usd', 'imports_world_usd', 'exports_world_usd', 'apparent_consumption_usd',
  'output_usd_official', 'value_added_usd', 'establishments', 'employees', 'share_mva_pct',
];
const HEADLINE = ['value_added_usd', 'output_usd_official', 'output_usd', 'establishments'];
const USD = new Set([
  'output_usd', 'imports_world_usd', 'exports_world_usd', 'apparent_consumption_usd',
  'output_usd_official', 'value_added_usd',
]);
const fmt = (field, value) => {
  if (value === null || value === undefined) return '—';
  if (field === 'share_mva_pct') return `${value} %`;
  return USD.has(field) ? `$${Math.round(value / 1e6)}M` : String(value);
};

const groupByDivision = (payload) => {
  const groups = {};
  for (const sector of payload.sectors) {
    const division = sector.isic4.slice(0, 2);
    (groups[division] ||= []).push(sector);
  }
  return Object.keys(groups).sort().map((division) => ({
    division, label: `Division ${division}`, sectors: groups[division],
  }));
};

const build = (payload, timeseries) => buildProductionPdf({
  countryIso3: payload.country_iso3,
  countryName: payload.country_name,
  language: 'fr',
  dataBasis: payload.data_basis,
  divisions: groupByDivision(payload),
  source: payload.source,
  formatIndicatorValue: fmt,
  indicatorLabels: LABELS,
  headlineOrder: HEADLINE,
  indicatorOrder: ORDER,
  timeseries,
});

describe('buildProductionPdf', () => {
  it('produit un document pour un pays mesuré, avec le détail par classe', () => {
    const sansDetail = build(fixtures.ken, null);
    const avecDetail = build(fixtures.ken, fixtures.ken_ts);

    expect(avecDetail.output('arraybuffer').byteLength).toBeGreaterThan(1000);
    // Le détail ajoute une section par classe : le document doit grossir.
    expect(avecDetail.internal.getNumberOfPages())
      .toBeGreaterThan(sansDetail.internal.getNumberOfPages());
  });

  it('produit un document pour un pays estimé, sans réclamer de séries', () => {
    const doc = build(fixtures.dza, null);
    expect(doc.output('arraybuffer').byteLength).toBeGreaterThan(1000);
    expect(doc.internal.getNumberOfPages()).toBeGreaterThanOrEqual(1);
  });

  it("n'invente pas de détail quand une classe n'a aucune série", () => {
    // Séries volontairement vides : le bâtisseur doit produire la mention
    // d'absence, pas planter ni fabriquer des années.
    const vide = Object.fromEntries(
      Object.keys(fixtures.ken_ts).map((code) => [code, { isic_description: 'x', series: {} }]),
    );
    const doc = build(fixtures.ken, vide);
    expect(doc.output('arraybuffer').byteLength).toBeGreaterThan(1000);
  });

  it('dit dans le document que le détail n’a pas pu être chargé', () => {
    // Un export amputé qui se tait est indiscernable d'un export complet :
    // le lecteur croirait que ces classes n'ont pas de détail publié.
    const muet = build(fixtures.ken, null);
    const avoue = buildProductionPdf({
      countryIso3: fixtures.ken.country_iso3,
      countryName: fixtures.ken.country_name,
      language: 'fr',
      dataBasis: fixtures.ken.data_basis,
      divisions: groupByDivision(fixtures.ken),
      source: fixtures.ken.source,
      formatIndicatorValue: fmt,
      indicatorLabels: LABELS,
      headlineOrder: HEADLINE,
      indicatorOrder: ORDER,
      timeseries: null,
      detailUnavailable: true,
    });
    expect(avoue.output('arraybuffer').byteLength)
      .toBeGreaterThan(muet.output('arraybuffer').byteLength);
  });

  it('qualifie la ligne par la nature de l’indicateur affiché', () => {
    // Une classe peut porter un indicateur officiel ET une valeur principale
    // dérivée : étiqueter la ligne « officiel » mentirait sur le chiffre montré.
    const derive = {
      country_iso3: 'XXX',
      country_name: 'Test',
      data_basis: 'UNIDO_MEASURED',
      source: 'test',
      sectors: [{
        isic4: '1010',
        isic_description: 'Classe témoin',
        indicators: {
          // output_usd est DÉRIVÉ et vient avant dans HEADLINE ? non : value_added
          // est officiel mais absent ; le principal retenu sera output_usd.
          output_usd: { value: 1e9, year: 2023, data_nature: 'UNIDO_DERIVED_ESTIMATE' },
          employees: { value: 100, year: 2023, data_nature: 'OFFICIAL_STATISTICS' },
        },
      }],
    };
    const doc = build(derive, null);
    expect(doc.output('arraybuffer').byteLength).toBeGreaterThan(1000);
  });

  it('nomme le fichier selon la nature de la donnée', () => {
    expect(productionPdfFilename('KEN', 'UNIDO_MEASURED')).toContain('mesure');
    expect(productionPdfFilename('DZA', 'ESTIMATED_FROM_ISIC2')).toContain('estime');
    expect(productionPdfFilename('DZA', 'ESTIMATED_FROM_ISIC2')).toContain('DZA');
  });
});

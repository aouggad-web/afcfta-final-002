import { describe, it, expect } from 'vitest';
import { writeFileSync } from 'node:fs';
import { buildOpportunityPdf } from './opportunityPdf';
import { chargerPoliceArabe } from './pdfArabe';
import { specMacroPdf, specAgriculturePdf, specMiningPdf, specDebouchesPdf } from './productionRapportsPdf';
import macroDZA from './__fixtures__/productionMacroDZA.json';
import agriDZA from './__fixtures__/productionAgricultureDZA.json';
import minesZAF from './__fixtures__/productionMiningZAF.json';
import minesCOM from './__fixtures__/productionMiningCOM.json';
import debouchesKEN from './__fixtures__/productionDebouchesKEN.json';

// Réponses réelles du backend, prises le 08/11/2026 :
// GET /production/macro/DZA, /faostat/country-detail/DZA?language=fr,
// /production/mining/ZAF et /COM, /production/country-profile/KEN?top_n=40.

const ecrire = (doc, nom) => {
  // Pour regarder le rendu : PDF_SORTIE=/chemin/dossier npx vitest run …
  if (process.env.PDF_SORTIE) writeFileSync(`${process.env.PDF_SORTIE}/${nom}`, Buffer.from(doc.output('arraybuffer')));
};
// Les nombres français portent des espaces insécables : on les ramène à des espaces.
const esp = (o) => JSON.parse(JSON.stringify(o).replace(/\u00a0/g, ' '));
const titres = (spec) => spec.sections.map((s) => s.title).filter(Boolean);
const section = (spec, titre) => spec.sections.find((s) => s.title === titre);

const RAPPORTS = [
  {
    nom: 'macro',
    spec: (l) => specMacroPdf(macroDZA, l),
    titres: { fr: 'Valeur ajoutée par secteur — Algérie', en: 'Value added by sector — Algeria', ar: 'القيمة المضافة حسب القطاع — الجزائر' },
  },
  {
    nom: 'agriculture',
    spec: (l) => specAgriculturePdf(agriDZA, l),
    titres: { fr: 'Production agricole — Algérie', en: 'Agricultural production — Algeria', ar: 'الإنتاج الزراعي — الجزائر' },
  },
  {
    nom: 'mines',
    spec: (l) => specMiningPdf(minesZAF, l),
    titres: { fr: 'Production minière — Afrique du Sud', en: 'Mining production — South Africa', ar: 'الإنتاج المعدني — جنوب أفريقيا' },
  },
  {
    nom: 'debouches',
    spec: (l) => specDebouchesPdf(debouchesKEN, l),
    titres: { fr: 'Débouchés — Kenya', en: 'Outlets — Kenya', ar: 'المنافذ — كينيا' },
  },
];

describe('PDF du module Production — trois langues', () => {
  RAPPORTS.forEach(({ nom, spec, titres: attendus }) => {
    it(`${nom} : se construit en français, anglais et arabe`, async () => {
      await chargerPoliceArabe();
      ['fr', 'en', 'ar'].forEach((langue) => {
        const s = spec(langue);
        expect(s.title).toBe(attendus[langue]);
        // Dernière rubrique : l'avertissement.
        expect(s.sections[s.sections.length - 1].notice?.length).toBeGreaterThan(0);
        const doc = buildOpportunityPdf({ ...s, language: langue });
        expect(doc.internal.getNumberOfPages()).toBeGreaterThanOrEqual(1);
        if (langue === 'ar') expect(doc.output()).toContain('/BaseFont /NotoArabe');
        if (langue !== 'en') ecrire(doc, `production-${nom}-${langue}.pdf`);
      });
    });
  });
});

describe('PDF valeur ajoutée macro', () => {
  it('reprend les parts, les montants et la croissance année par année', () => {
    const spec = specMacroPdf(macroDZA, 'fr');
    expect(titres(spec)).toEqual(expect.arrayContaining([
      'Valeur ajoutée par secteur (% du PIB), année par année',
      'Valeur ajoutée par secteur en dollars courants',
      'Croissance du PIB (% annuel)',
      'Séries utilisées',
      'Avertissement',
    ]));
    const parts = section(spec, 'Valeur ajoutée par secteur (% du PIB), année par année').table;
    expect(parts.columns.map((c) => c.key)).toEqual(['year', 'A', 'B-F', 'C', 'G-T']);
    expect(parts.rows).toHaveLength(10);
    // Lignes dans l'ordre des années, même si la source les sert en désordre.
    expect(parts.rows[0]).toMatchObject({ year: '2015', A: '10,53 %' });
    expect(parts.rows[8]).toMatchObject({ year: '2023', A: '13,37 %' });
    const usd = section(spec, 'Valeur ajoutée par secteur en dollars courants').table;
    expect(usd.columns.map((c) => c.label)).toContain('PIB');
    expect(spec.kpis.find((k) => k.label === 'Croissance du PIB')).toMatchObject({ value: '3,7 %', sub: '2024' });
  });

  it('écrit « non publié » pour une année absente, jamais 0', () => {
    const macro = structuredClone(macroDZA);
    macro.data_by_sector.Services = macro.data_by_sector.Services.filter((r) => r.year !== 2020);
    const spec = specMacroPdf(macro, 'fr');
    const ligne = section(spec, 'Valeur ajoutée par secteur (% du PIB), année par année').table.rows.find((r) => r.year === '2020');
    expect(ligne['G-T']).toBe('non publié');
    expect(specMacroPdf({ ...macro, data_by_sector_usd: {} }, 'en').sections
      .find((s) => s.title === 'Value added by sector in current dollars').paragraphs[0]).toContain('does not publish');
  });
});

describe('PDF agriculture', () => {
  it('reprend cultures, élevage, pêche et perspectives, quel que soit l’onglet ouvert', () => {
    const spec = specAgriculturePdf(agriDZA, 'fr');
    expect(titres(spec)).toEqual(expect.arrayContaining([
      'Cultures : production, surface et rang', 'Sources',
      'Évolution de la production des principales cultures (t)',
      'Élevage : cheptel', 'Production animale', 'Pêche et aquaculture',
      'Perspectives de production (OCDE-FAO)', 'Avertissement',
    ]));
    const cultures = section(spec, 'Cultures : production, surface et rang').table.rows;
    expect(cultures).toHaveLength(agriDZA.cultures.length);
    expect(esp(cultures[0])).toMatchObject({ product: 'Blé', production: '3 500 000 t', year: '2023', rank: '4', source: '[1]' });
    // Ligne FAOSTAT en masse : son année, pas de surface publiée.
    expect(cultures[7]).toMatchObject({ year: '2024', area: 'non publié', rank: '—', source: '[2]' });
  });

  it('écrit « non publié » quand la source ne publie pas', () => {
    const detail = structuredClone(agriDZA);
    detail.key_indicators.agri_gdp_percent = null;
    detail.cultures[0].value_2023 = null;
    const spec = specAgriculturePdf(detail, 'fr');
    expect(spec.kpis.find((k) => k.label === 'Agriculture, part du PIB').value).toBe('non publié');
    expect(section(spec, 'Cultures : production, surface et rang').table.rows[0].production).toBe('non publié');
    const ar = specAgriculturePdf({ ...detail, has_fisheries: false }, 'ar');
    expect(ar.kpis.find((k) => k.label === 'الصيد الطبيعي').value).toBe('غير منشور');
  });
});

describe('PDF mines', () => {
  it('un minéral par ligne, une colonne par année, avec unité et source', () => {
    const spec = specMiningPdf(minesZAF, 'fr');
    const table = section(spec, 'Production par minéral et par année').table;
    expect(table.rows).toHaveLength(Object.keys(minesZAF.data_by_commodity).length);
    expect(table.columns.map((c) => c.key)).toEqual(['mineral', 'code', 'unit', '2022', '2023', '2024', 'source']);
    const or = table.rows.find((r) => r.mineral === 'Gold');
    expect(or).toMatchObject({ unit: 'tonnes', 2022: '120', 2024: '100' });
    expect(or.source).toBe('Mineral Commodity Summaries 2024, 2025');
    // Minéral publié seulement depuis 2023 : 2022 « non publié », pas 0.
    expect(table.rows.find((r) => r.mineral === 'Perlite')[2022]).toBe('non publié');
    expect(titres(spec)).toContain('Couverture des sources');
  });

  it('commence par le profil minier et la synthèse dernière valeur / évolution', () => {
    const spec = specMiningPdf(minesZAF, 'fr');
    expect(titres(spec).slice(0, 2)).toEqual(['Profil minier', expect.stringMatching(/^Synthèse : dernière valeur publiée/)]);
    const synthese = spec.sections.find((x) => x.title?.startsWith('Synthèse')).table.rows;
    // Or : dernière valeur 2024, comparée à l'année publiée juste avant, même unité.
    const or = synthese.find((r) => r.mineral === 'Gold');
    expect(or).toMatchObject({ latest: '100 tonnes', year: '2024' });
    expect(or.previous).toMatch(/tonnes \(\d{4}\)$/);
    expect(or.change).toMatch(/%$/);
    // Un minéral publié une seule année n'a pas de valeur précédente : « non publié », jamais 0.
    const seul = synthese.find((r) => r.previous === 'non publié');
    if (seul) expect(seul.change).toBe('—');
  });

  it('sans production publiée, explique la couverture des sources', () => {
    const spec = specMiningPdf(minesCOM, 'en');
    expect(spec.title).toBe('Mining production — Comoros');
    expect(section(spec, 'Output by mineral and year').paragraphs[0]).toContain('No production value');
    const couverture = section(spec, 'Source coverage').keyValues;
    expect(couverture[0].value).toBe('No production reported by the sources consulted');
    expect(() => buildOpportunityPdf({ ...spec, language: 'en' })).not.toThrow();
  });
});

describe('PDF débouchés', () => {
  it('reprend chaque produit avec code SH, rang et nombre de pays couverts', () => {
    const spec = specDebouchesPdf(debouchesKEN, 'fr');
    const rows = section(spec, 'Produits, rang africain et source').table.rows;
    expect(rows).toHaveLength(debouchesKEN.products.length);
    expect(rows[0]).toMatchObject({ product: 'Spinach', hs: '070970', rank: '1er sur 5 pays couverts', share: '86,2 %', source: 'FAO 2024 (agriculture)' });
    // Valeur ajoutée manufacturière : un montant en dollars.
    expect(esp(rows.find((r) => r.hs === '3901').output)).toBe('672 M $');
    expect(titres(spec)).toContain('Réserves sur certaines lignes');
    expect(spec.kpis[1]).toMatchObject({ label: 'Produits suivis', value: '110' });
  });

  it('écrit « non publié » pour un rang retenu par le serveur', () => {
    const profil = structuredClone(debouchesKEN);
    Object.assign(profil.products[0], { rank: null, share_pct: null, value: null });
    const row = specDebouchesPdf(profil, 'en').sections[0].table.rows[0];
    expect(row).toMatchObject({ rank: 'not published', share: 'not published', output: 'not published' });
  });
});

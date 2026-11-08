import { describe, it, expect, beforeAll } from 'vitest';
import { writeFileSync } from 'node:fs';
import { buildOpportunityPdf } from './opportunityPdf';
import {
  specVueEnsemblePdf, specRcaPdf, specComplementaritePdf, specMargePreferencePdf, specComparaisonPdf,
} from './statistiquesRapportsPdf';
import { chargerPoliceArabe } from './pdfArabe';
import vueEnsemble from './__fixtures__/statistiquesVueEnsemble.json';
import analyse from './__fixtures__/statistiquesAnalysePays.json';
import comparaison from './__fixtures__/statistiquesComparaison.json';
import preference from './__fixtures__/statistiquesPreference.json';

// Réponses réelles du backend, prises le 08/11/2026 (listes raccourcies) :
// GET /statistics + /oec/africa/totals?year=2024 ; /oec/rca/NGA (2022, HS4) ;
// /oec/complementarity/NGA/ZAF (2022, HS4) ; /statistics/country-comparison/{NGA,ZAF,SSD}.
// La marge préférentielle est un exemple à la forme du service : l'API
// répond 404 pour tous les pays à cette date (voir _note dans la fixture).

const ecrire = (doc, nom) => {
  // Pour regarder le rendu : PDF_SORTIE=/chemin/dossier npx vitest run …
  if (process.env.PDF_SORTIE) writeFileSync(`${process.env.PDF_SORTIE}/${nom}`, Buffer.from(doc.output('arraybuffer')));
};

const RAPPORTS = {
  vue: (l) => specVueEnsemblePdf(vueEnsemble, l),
  rca: (l) => specRcaPdf(analyse.rca, { pays: 'NGA' }, l),
  complementarite: (l) => specComplementaritePdf(analyse.complementarite, { exportateur: 'NGA', importateur: 'ZAF' }, l),
  preference: (l) => specMargePreferencePdf(preference, { pays: 'KEN' }, l),
  comparaison: (l) => specComparaisonPdf({ pays: ['NGA', 'ZAF', 'SSD'], donnees: comparaison }, l),
};

const TITRES = {
  vue: ["Commerce africain — vue d'ensemble", 'African trade — overview', 'التجارة الأفريقية — نظرة عامة'],
  rca: ['Avantage comparatif révélé — Nigéria', 'Revealed comparative advantage — Nigeria', 'الميزة النسبية الظاهرة — نيجيريا'],
  complementarite: ['Complémentarité commerciale (TCI)', 'Trade complementarity (TCI)', 'التكامل التجاري (TCI)'],
  preference: ['Marge préférentielle ZLECAf — Kenya', 'AfCFTA preference margin — Kenya', 'الهامش التفضيلي في زليكاف — كينيا'],
  comparaison: ['Comparaison multi-pays', 'Multi-country comparison', 'مقارنة متعددة البلدان'],
};

describe('PDF du module Statistiques', () => {
  beforeAll(async () => { await chargerPoliceArabe(); });

  Object.entries(RAPPORTS).forEach(([nom, spec]) => {
    ['fr', 'en', 'ar'].forEach((langue, i) => {
      it(`${nom} se construit en ${langue}, avec son titre et un avertissement final`, () => {
        const s = spec(langue);
        expect(s.title).toBe(TITRES[nom][i]);
        expect(s.sections.at(-1).notice.length).toBeGreaterThanOrEqual(3);
        // Aucun tableau vide.
        s.sections.filter((x) => x.table).forEach((x) => expect(x.table.rows.length).toBeGreaterThan(0));
        const doc = buildOpportunityPdf({ ...s, language: langue });
        expect(doc.internal.getNumberOfPages()).toBeGreaterThanOrEqual(1);
        if (langue !== 'en') ecrire(doc, `statistiques-${nom}-${langue}.pdf`);
      });
    });
  });

  it("vue d'ensemble : totaux, classements et PIB repris de l'API", () => {
    const s = specVueEnsemblePdf(vueEnsemble, 'fr');
    expect(s.kpis.map((k) => k.value)).toEqual(['2 706 Md $', '719,8 Md $', '761,4 Md $', '54']);
    const exp = s.sections.find((x) => x.title === 'Top 10 exportateurs africains — 2024').table.rows;
    expect(exp).toHaveLength(10);
    expect(exp[0]).toMatchObject({ rank: '1', country: 'Afrique du Sud', share: '21 %' });
    // « RD Congo » (nom de l'API) retrouve son nom anglais.
    const en = specVueEnsemblePdf(vueEnsemble, 'en').sections.find((x) => x.title?.startsWith('Top 10 African exporters')).table.rows;
    expect(en.map((r) => r.country)).toContain('Democratic Republic of the Congo');
  });

  it('écrit « non publié » quand la source ne publie pas, jamais 0', () => {
    const sansTotaux = specVueEnsemblePdf({ statistics: vueEnsemble.statistics }, 'fr');
    expect(sansTotaux.kpis[1].value).toBe('non publié');

    // SSD : pas de données commerciales ; IDH : pas de rang mondial publié.
    const cmp = specComparaisonPdf({ pays: ['NGA', 'SSD'], donnees: comparaison }, 'fr');
    const commerce = cmp.sections.find((x) => x.title === 'Indicateurs commerciaux').table.rows;
    expect(commerce[0]).toMatchObject({ indicator: 'Exportations', SSD: 'non publié' });
    expect(commerce[0].NGA).toBe('63,6 Md $');
    const dev = cmp.sections.find((x) => x.title === 'Indices de développement').table.rows;
    expect(dev[1]).toMatchObject({ NGA: 'non publié', SSD: 'non publié' });
    expect(JSON.stringify(cmp)).not.toMatch(/"SSD":"0"/);

    const pref = specMargePreferencePdf(preference, { pays: 'KEN' }, 'en');
    const exclu = pref.sections.find((x) => x.title === 'Breakdown by sensitivity').table.rows.find((r) => r.cat === 'Excluded');
    expect(exclu.margin).toBe('not published');

    const rca = specRcaPdf({ ...analyse.rca, total_exports: null }, { pays: 'NGA' }, 'ar');
    expect(rca.kpis[1].value).toBe('غير منشور');
  });

  it('RCA et complémentarité : année, niveau SH, source et explications', () => {
    const rca = specRcaPdf(analyse.rca, { pays: 'NGA' }, 'fr');
    expect(rca.subtitle).toBe('Indice de Balassa par produit · 2022 · SH4 — positions · OEC/BACI');
    expect(rca.sections.find((x) => x.title === 'Comment lire le RCA').paragraphs[1]).toContain('RCA > 1');
    const ligne = rca.sections.find((x) => x.table).table;
    expect(ligne.rows).toHaveLength(analyse.rca.data.length);

    const tci = specComplementaritePdf(analyse.complementarite, { exportateur: 'NGA', importateur: 'ZAF' }, 'fr');
    expect(tci.kpis[0]).toMatchObject({ value: '11,7', sub: 'Faible complémentarité' });
    expect(tci.subtitle).toContain('Nigéria (exportateur) → Afrique du Sud (importateur)');
  });
});

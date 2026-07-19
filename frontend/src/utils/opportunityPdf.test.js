import { describe, it, expect } from 'vitest';
import { buildOpportunityPdf, opportunityPdfFilename } from './opportunityPdf';

const richSpec = {
  badge: 'SUBSTITUTION',
  title: 'Substitution d’imports — Algérie',
  subtitle: 'Flux réels OEC / BACI',
  kpis: [
    { label: 'Opportunités', value: '12', accent: 'gold' },
    { label: 'Valeur substituable', value: '$4.2B', accent: 'green' },
    { label: 'Hors Afrique', value: '$35B', accent: 'red' },
  ],
  sections: [
    {
      title: 'Opportunités',
      table: {
        columns: [
          { key: 'hs', label: 'SH', width: 0.7 },
          { key: 'name', label: 'Produit', width: 2.5 },
          { key: 'pot', label: 'Potentiel', align: 'right', width: 1 },
        ],
        rows: Array.from({ length: 60 }, (_, i) => ({ hs: `87${i % 10}0`, name: `Produit ${i}`, pot: `$${i}M` })),
      },
    },
    { title: 'Détails', keyValues: [{ label: 'Taux NPF', value: '30%' }, { label: 'Taux ZLECAf', value: '9%' }] },
    { title: 'Note', paragraphs: ['Estimation transparente : valeur modélisée, non mesurée.'] },
  ],
  source: 'OEC BACI',
};

describe('buildOpportunityPdf', () => {
  it('builds light and dark docs without throwing, paginating a 60-row table', () => {
    for (const theme of ['light', 'dark']) {
      const doc = buildOpportunityPdf({ ...richSpec, theme, language: 'fr' });
      expect(doc.output('arraybuffer').byteLength).toBeGreaterThan(1000);
      expect(doc.internal.getNumberOfPages()).toBeGreaterThan(1); // 60 rows overflow page 1
    }
  });

  it('handles a minimal spec (title only) without throwing', () => {
    const doc = buildOpportunityPdf({ title: 'Rapport', language: 'en' });
    expect(doc.output('arraybuffer').byteLength).toBeGreaterThan(500);
  });

  it('grows row height for wrapped text instead of a fixed row height (regression: overlap)', () => {
    // Same row count, same narrow column — only the text length differs.
    // A FIXED row height (the bug) would need the same page count either
    // way; wrapped multi-line cells must consume more vertical space and
    // therefore more pages once the accumulated extra height overflows a page.
    const makeSpec = (name) => ({
      title: 'T',
      sections: [
        {
          table: {
            columns: [
              { key: 'hs', label: 'SH', width: 0.6 },
              { key: 'name', label: 'Produit', width: 0.8 }, // narrow -> forces wrap
            ],
            rows: Array.from({ length: 60 }, (_, i) => ({ hs: `87${i}`, name })),
          },
        },
      ],
    });
    const short = buildOpportunityPdf(makeSpec('Voiture'));
    const long = buildOpportunityPdf(
      makeSpec(
        'Aiguilles tubulaires en métal et aiguilles de suture pour usage médical vétérinaire ' +
          'et humain, toutes tailles, conditionnement individuel stérile'
      )
    );
    expect(long.internal.getNumberOfPages()).toBeGreaterThan(short.internal.getNumberOfPages());
  });

  it('applies column fmt with (value, row) and tolerates missing keys', () => {
    const doc = buildOpportunityPdf({
      title: 'T',
      sections: [
        {
          table: {
            columns: [{ key: 'absent', label: 'X', fmt: (v, row) => row.other || '—' }],
            rows: [{ other: 'ok' }, {}],
          },
        },
      ],
    });
    expect(doc.output('arraybuffer').byteLength).toBeGreaterThan(500);
  });

  it('coerces non-string fmt results (number, array, null) instead of throwing', () => {
    // jsPDF's text()/splitTextToSize() require a string (or string array) —
    // a raw number or null from a column's fmt() previously reached them
    // uncoerced and could throw.
    const doc = buildOpportunityPdf({
      title: 'T',
      sections: [
        {
          table: {
            columns: [
              { key: 'n', label: 'Num', fmt: (v) => v }, // returns a number, not a string
              { key: 'arr', label: 'Arr', fmt: () => ['a', 'b'] },
              { key: 'nul', label: 'Null', fmt: () => null },
            ],
            rows: [{ n: 42, arr: null, nul: null }],
          },
        },
      ],
    });
    expect(doc.output('arraybuffer').byteLength).toBeGreaterThan(500);
  });
});

describe('opportunityPdfFilename', () => {
  it('builds a dated, filesystem-safe name', () => {
    const name = opportunityPdfFilename('Substitution', 'DZA import');
    expect(name).toMatch(/^ZLECAf_Opportunites_Substitution_DZA_import_\d{4}-\d{2}-\d{2}$/);
  });
});

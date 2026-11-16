import { describe, it, expect } from 'vitest';
import { buildOpportunityPdf } from './opportunityPdf';
import { specManufacturePdf } from './manufacturePdf';
import { chargerPoliceArabe } from './pdfArabe';
import unidoDZA from './__fixtures__/productionManufactureDZA.json';

// Réponse réelle de GET /production/unido/DZA (08/11/2026) : chiffres
// officiels, estimation 2025 et comptes de l'ONS.
const DIVISIONS = [
  { division: '19', label: 'Raffinage pétrolier', shareMva: 80.3, valueMlnUsd: 29221.36, sectors: [{}, {}] },
  { division: '33', label: 'Réparation', shareMva: null, valueMlnUsd: null, sectors: [{}] },
];
const base = { unido: unidoDZA, code: 'DZA', rang: 3, total: 54, divisions: DIVISIONS, basis: 'UNIDO_MEASURED' };

describe('PDF Industrie manufacturière', () => {
  it('reprend l’écran entier : chiffres clés, profil, secteurs, estimation, comptes ONS, structure', () => {
    const spec = specManufacturePdf(base, 'fr');
    expect(spec.title).toBe('Industrie manufacturière — Algérie');
    expect(spec.kpis.find((k) => k.label === 'Rang en Afrique (VA manufacturière)').value).toBe('3 sur 54');
    expect(spec.kpis[0].sub).toContain('officiel');
    const titres = spec.sections.map((s) => s.title).filter(Boolean);
    expect(titres).toEqual(expect.arrayContaining([
      'Profil industriel', 'Estimation 2025', 'Comptes de l’office national par branche', 'Structure par division CITI', 'Avertissement',
    ]));
    expect(spec.sections[spec.sections.length - 1].notice).toBeTruthy();
    expect(() => buildOpportunityPdf({ ...spec, language: 'fr' })).not.toThrow();
  });

  it('écrit « non publié » pour une part absente, jamais 0', () => {
    const structure = specManufacturePdf(base, 'fr').sections.find((s) => s.title === 'Structure par division CITI');
    expect(structure.table.rows[1].share).toBe('non publié');
    const vide = specManufacturePdf({ unido: { country_name: 'Comores' }, code: 'COM' }, 'fr');
    expect(vide.kpis[0].value).toBe('non publié');
  });

  it('existe en anglais et en arabe', async () => {
    expect(specManufacturePdf(base, 'en').title).toBe('Manufacturing — Algeria');
    await chargerPoliceArabe();
    const ar = specManufacturePdf(base, 'ar');
    expect(ar.title).toBe('الصناعة التحويلية — الجزائر');
    expect(() => buildOpportunityPdf({ ...ar, language: 'ar' })).not.toThrow();
  });
});

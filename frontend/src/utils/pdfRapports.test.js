import { describe, it, expect } from 'vitest';
import { writeFileSync } from 'node:fs';
import { buildOpportunityPdf } from './opportunityPdf';
import { specCalculPdf } from './calculPdf';
import { specProfilPaysPdf } from './profilPaysPdf';
import calculDZA from './__fixtures__/calculDZA.json';
import profilDZA from './__fixtures__/profilPaysDZA.json';

// Réponses réelles du backend (POST /calcul DZA ← TUN 0201101100, 10 000 USD ;
// GET /country-profile/DZA), prises le 07/11/2026.
const RESULTAT = {
  origin_country: 'TUN',
  destination_country: 'DZA',
  hs_code: '0201101100',
  preferential_regime_applied: true,
  trade_regime: 'FTA_CONDITIONAL',
  administrative_formalities: [],
  formalites_statut: 'AUCUNE_FORMALITE_PARTICULIERE',
};

const texte = (spec) => JSON.stringify(spec);
const ecrire = (doc, nom) => {
  // Pour regarder le rendu : PDF_SORTIE=/chemin/dossier yarn vitest run …
  if (process.env.PDF_SORTIE) writeFileSync(`${process.env.PDF_SORTIE}/${nom}`, Buffer.from(doc.output('arraybuffer')));
};

describe('PDF du calculateur', () => {
  it('détaille les deux régimes, les totaux et les réserves', () => {
    const spec = specCalculPdf({ calcul: calculDZA, result: RESULTAT, origine: 'Tunisie', destination: 'Algérie', langue: 'fr' });
    expect(spec.title).toBe("Droits et taxes à l'importation — Algérie");
    expect(spec.kpis.map((k) => k.label)).toEqual(['Valeur CIF', 'Droits et taxes NPF', 'Droits et taxes GZALE', 'Économie']);
    const titres = spec.sections.map((s) => s.title).filter(Boolean);
    expect(titres).toEqual(expect.arrayContaining([
      'Opération', 'Comment lire ce calcul', 'Détail des droits et taxes — régime NPF',
      'Détail des droits et taxes — GZALE', 'Formalités administratives', "Réglementation à l'importation", 'Avertissement',
    ]));
    const npf = spec.sections.find((s) => s.title === 'Détail des droits et taxes — régime NPF').table;
    expect(npf.rows).toHaveLength(calculDZA.npf.lignes.length);
    expect(texte(spec)).toContain('non opposable');
    const doc = buildOpportunityPdf({ ...spec, language: 'fr' });
    expect(doc.internal.getNumberOfPages()).toBeGreaterThanOrEqual(2);
    ecrire(doc, 'calcul.pdf');
  });

  it('écrit « à compléter » pour une ligne non liquidée, jamais 0', () => {
    const calcul = structuredClone(calculDZA);
    calcul.npf.lignes[1] = { ...calcul.npf.lignes[1], statut: 'A_COMPLETER', montant: null };
    calcul.npf.manques = [{ code: calcul.npf.lignes[1].code, motif: 'QUANTITE_REQUISE' }];
    calcul.npf.etat = 'PARTIEL';
    const spec = specCalculPdf({ calcul, result: RESULTAT, origine: 'Tunisie', destination: 'Algérie', langue: 'fr' });
    const ligne = spec.sections.find((s) => s.title === 'Détail des droits et taxes — régime NPF').table.rows[1];
    expect(ligne.statut).toBe('à compléter');
    expect(ligne._calculee).toBe(false);
    expect(texte(spec)).toContain('Droit spécifique : saisir la quantité');
    expect(texte(spec)).toContain('Partiel');
  });

  it('existe en anglais', () => {
    const spec = specCalculPdf({ calcul: calculDZA, result: RESULTAT, origine: 'Tunisia', destination: 'Algeria', langue: 'en' });
    expect(spec.title).toBe('Import duties and taxes — Algeria');
    expect(() => buildOpportunityPdf({ ...spec, language: 'en' })).not.toThrow();
  });
});

describe('PDF du profil pays', () => {
  it('reprend les indicateurs avec année, rang et explications', () => {
    const spec = specProfilPaysPdf(profilDZA, 'fr');
    expect(spec.title).toBe('Profil économique — Algérie');
    expect(spec.kpis).toHaveLength(8);
    const titres = spec.sections.map((s) => s.title).filter(Boolean);
    expect(titres).toEqual(expect.arrayContaining([
      'Indicateurs macroéconomiques', 'Projections du FMI', 'Développement humain et société',
      'Finances extérieures', 'Notations souveraines et risque', 'Administration des douanes', 'Avertissement',
    ]));
    // Une fiche par projet, la première annoncée par le titre de la rubrique.
    expect(titres.filter((x) => x.startsWith('Projets structurants — '))).toHaveLength(1);
    expect(spec.sections.filter((s) => s.keyValues?.some((kv) => kv.label === 'Budget'))).toHaveLength(profilDZA.ongoing_projects.length);
    const macro = spec.sections.find((s) => s.title === 'Indicateurs macroéconomiques').table.rows;
    expect(macro[0]).toMatchObject({ indicator: 'PIB', year: 2025, rank: '4/52' });
    const doc = buildOpportunityPdf({ ...spec, language: 'fr' });
    expect(doc.internal.getNumberOfPages()).toBeGreaterThanOrEqual(2);
    ecrire(doc, 'profil.pdf');
  });

  it('écrit « non publié » quand la source ne publie pas', () => {
    const spec = specProfilPaysPdf({ ...profilDZA, inflation_rate: null }, 'fr');
    expect(spec.kpis.find((k) => k.label === 'Inflation').value).toBe('non publié');
  });

  it('existe en anglais, avec le nom anglais du pays', () => {
    const spec = specProfilPaysPdf(profilDZA, 'en');
    expect(spec.title).toBe('Economic profile — Algeria');
    expect(() => buildOpportunityPdf({ ...spec, language: 'en', theme: 'dark' })).not.toThrow();
  });
});

describe('Marque du site sur les PDF', () => {
  it('porte le logo et le nom du site', () => {
    const doc = buildOpportunityPdf({ title: 'Essai', language: 'fr', sections: [] });
    const brut = doc.output();
    expect(brut).toContain('/Subtype /Image');
    expect(brut).toContain('ZLECAf Intelligence');
  });
});

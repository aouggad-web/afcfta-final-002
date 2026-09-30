import { describe, expect, it } from 'vitest';
import { expliquerZlecaf } from './zlecafExplication';

// Champs tels que le calculateur les reçoit (chemin historique), relevés sur
// les réponses réelles du backend.
const base = { origin_country_iso3: 'EGY' };
const texte = (explication, cle) => explication.lignes.find((l) => l.cle === cle)?.texte;

describe('expliquerZlecaf', () => {
  it('préférence appliquée : taux, source, baisse du droit', () => {
    const e = expliquerZlecaf({
      ...base,
      trade_regime: 'ZLECAF',
      zlecaf_status: 'DOCUMENTED',
      zlecaf_tariff_rate: 0,
      npf_dd_rate_pct: 2.5,
      zlecaf_rate_expression: '0%',
      zlecaf_rate_source: { title: 'AfCFTA e-Tariff Book', url: 'https://etariff.au-afcfta.org/' },
    });
    expect(e.niveau).toBe('APPLICATION_DOCUMENTEE');
    expect(texte(e, 'taux')).toBe('Taux ZLECAf de la ligne : 0%. Source : AfCFTA e-Tariff Book.');
    expect(e.lignes.find((l) => l.cle === 'taux').lien).toBe('https://etariff.au-afcfta.org/');
    expect(texte(e, 'effet')).toBe('Le droit de douane passe de 2.5 % (NPF) à 0 %.');
    expect(texte(e, 'reserves')).toContain('Certificat d’origine ZLECAf requis.');
  });

  it('ZAF/02071290 depuis EGY : taux égal au NPF, dit « aucun avantage »', () => {
    const e = expliquerZlecaf({
      ...base,
      trade_regime: 'ZLECAF',
      zlecaf_status: 'DOCUMENTED',
      zlecaf_tariff_rate: 0.82,
      npf_dd_rate_pct: 82,
      zlecaf_rate_expression: '82%',
      zlecaf_rate_source: { title: 'SARS Schedule 1 Part 1 — Customs Duty' },
    });
    expect(e.niveau).toBe('SANS_AVANTAGE');
    expect(texte(e, 'effet')).toBe(
      'Taux identique au taux normal (NPF) de 82 % : aucun avantage sur cette ligne.',
    );
  });

  it('plancher NPF et réserve de la règle B EAC sont repris', () => {
    const e = expliquerZlecaf({
      ...base,
      trade_regime: 'ZLECAF',
      zlecaf_status: 'DOCUMENTED',
      zlecaf_tariff_rate: 0.1,
      npf_dd_rate_pct: 10,
      plancher_npf: { taux_preferentiel: 12 },
      zlecaf_reserve: 'Liste d’origines = plafond.',
    });
    expect(texte(e, 'reserves')).toContain('le taux normal (NPF) est retenu');
    expect(texte(e, 'reserves')).toContain('Liste d’origines = plafond.');
  });

  it('offre seule : taux de l’offre montré, jamais appliqué', () => {
    const e = expliquerZlecaf({
      ...base,
      trade_regime: 'NPF',
      zlecaf_status: 'OFFER_ONLY',
      zlecaf_offer_rate_pct: 2,
      zlecaf_offer_rate_expression: '2.0%',
      zlecaf_offer_rate_source: { title: 'AfCFTA e-Tariff Book — Tariff Concession Schedule' },
    });
    expect(e.niveau).toBe('SIMULATION_OFFRE');
    expect(texte(e, 'taux')).toBe(
      'Taux prévu par l’offre publiée : 2.0%. Source : AfCFTA e-Tariff Book — Tariff Concession Schedule.',
    );
    expect(texte(e, 'effet')).toContain('n’est pas appliqué au total');
  });

  it('notification requise : hypothèse d’admission annoncée', () => {
    const e = expliquerZlecaf({
      ...base,
      trade_regime: 'NPF',
      zlecaf_status: 'PARTNER_NOTICE_REQUIRED',
      zlecaf_offer_rate_pct: null,
    });
    expect(e.niveau).toBe('SIMULATION_CONDITIONNELLE');
    expect(texte(e, 'statut')).toContain('à confirmer auprès de la douane de destination');
    expect(texte(e, 'taux')).toBe('Aucun taux ZLECAf exploitable pour cette ligne.');
  });

  it('union douanière : hors ZLECAf, la note du régime est reprise', () => {
    const note = 'Échanges intra-UEMOA : libre circulation sous le régime de l’union douanière.';
    const e = expliquerZlecaf({
      ...base, trade_regime: 'CUSTOMS_UNION', zlecaf_status: 'NOT_AVAILABLE', trade_regime_note: note,
    });
    expect(e.niveau).toBe('UNION_DOUANIERE');
    expect(texte(e, 'statut')).toBe(note);
    expect(texte(e, 'taux')).toBeUndefined();
  });

  it('non calculable : le motif du backend, jamais un taux', () => {
    const note = 'ZLECAf non applicable : BEN (signataire, non encore ratifié) — taux NPF appliqué';
    const e = expliquerZlecaf({
      origin_country_iso3: 'BEN', trade_regime: 'NPF', zlecaf_status: 'NOT_AVAILABLE', zlecaf_note: note,
    });
    expect(e.niveau).toBe('NON_CALCULABLE');
    expect(texte(e, 'statut')).toBe(note);
    expect(texte(e, 'taux')).toBeUndefined();
  });

  it('sans origine : le dit, au lieu d’un motif générique', () => {
    const e = expliquerZlecaf({ trade_regime: 'NPF', zlecaf_status: 'NOT_AVAILABLE' });
    expect(texte(e, 'statut')).toContain('Aucun pays d’origine sélectionné');
  });

  it('parle anglais', () => {
    const e = expliquerZlecaf({ trade_regime: 'NPF', zlecaf_status: 'OFFER_ONLY' }, 'en');
    expect(e.titre).toBe('Offer-based simulation');
  });
});

import { describe, expect, it } from 'vitest';
import { buildCalculRequestBody, mapCalculToLegacyResult } from './unifiedCalculator';

const contexte = { originCountry: 'GHA', destinationCountry: 'CIV', hsCode: '7612900000', cifValue: 1000 };

const ligne = (over) => ({ code: 'DD', libelle: 'Droit de douane', famille: 'droit',
  assiette: 'CIF', taux_pct: 20, statut: 'CALCULE', base: 1000, montant: 200, ...over });

describe('buildCalculRequestBody', () => {
  it("omet l'origine quand elle est absente plutôt que d'envoyer une valeur vide", () => {
    expect(buildCalculRequestBody({ destinationISO3: 'CIV', hsCode: '7612900000', cifValue: 1000 }))
      .toEqual({ destination: 'CIV', code_sh: '7612900000', valeur_cif: 1000 });
  });

  it("porte l'origine quand elle est fournie", () => {
    expect(buildCalculRequestBody({ destinationISO3: 'CIV', originISO3: 'GHA', hsCode: '7612900000', cifValue: 1000 }))
      .toEqual({ destination: 'CIV', origine: 'GHA', code_sh: '7612900000', valeur_cif: 1000 });
  });
});

describe('mapCalculToLegacyResult — cas complet, sans préférence', () => {
  const calcul = {
    position: { designation: 'Réservoirs en aluminium' },
    npf: {
      etat: 'COMPLET',
      lignes: [ligne(), ligne({ code: 'TVA', libelle: 'TVA', famille: 'tva', taux_pct: 18, base: 1200, montant: 216 })],
      manques: [],
      total_droits: 416,
      total_a_payer: 1416,
      taux_effectif_pct: 41.6,
    },
    preference_zlecaf: { applique: false, statut: 'NOT_AVAILABLE', note: 'Aucune preuve vérifiée.' },
    provenance: {
      niveau: 'national',
      source: { nom: 'douanes.ci', collecte: '2026-08-30T10:00:00Z' },
      assiettes: { reference_legale: 'TEC CEDEAO' },
    },
  };

  const r = mapCalculToLegacyResult(calcul, contexte);

  it('reprend les montants NPF sans les fabriquer', () => {
    expect(r.normal_tariff_amount).toBe(200);
    expect(r.normal_tariff_rate).toBe(0.2);
    expect(r.normal_vat_amount).toBe(216);
    expect(r.normal_total_cost).toBe(1416);
    expect(r.total_taxes_npf).toBe(41.6);
  });

  it("n'affirme aucune préférence quand aucune n'est appliquée", () => {
    expect(r.trade_regime).toBe('NPF');
    expect(r.zlecaf_status).toBe('NOT_AVAILABLE');
    expect(r.zlecaf_tariff_amount).toBeNull();
    expect(r.savings).toBeNull();
    expect(r.taxes_summary.zlecaf).toBeNull();
  });

  it('cite la référence légale et la date de collecte réellement servies', () => {
    expect(r.cascade_legal_source).toBe('TEC CEDEAO');
    expect(r.last_verified).toBe('2026-08-30');
    expect(r.description).toBe('Réservoirs en aluminium');
  });

  it('rend un état COMPLET reconnu comme tel', () => {
    expect(r.confidence_level).toBe('very_high');
    expect(r.dd_available).toBe(true);
    expect(r.duty_status).toBe('PAYABLE');
  });
});

describe('mapCalculToLegacyResult — préférence appliquée', () => {
  const calcul = {
    position: { designation: 'Chevaux vivants' },
    npf: {
      etat: 'COMPLET',
      lignes: [ligne()],
      manques: [],
      total_droits: 200,
      total_a_payer: 1200,
      taux_effectif_pct: 20,
    },
    preference: {
      etat: 'COMPLET',
      lignes: [ligne({ taux_pct: 0, montant: 0, taux_npf_pct: 20, regime_applique: 'preference' })],
      total_droits: 0,
      total_a_payer: 1000,
      taux_effectif_pct: 0,
    },
    economie: 200,
    preference_zlecaf: { applique: true, statut: 'APPLIED', note: 'Couloir autorisé.' },
    provenance: { niveau: 'national', source: {}, assiettes: {} },
  };

  const r = mapCalculToLegacyResult(calcul, contexte);

  it('reflète le régime préférentiel réellement appliqué', () => {
    expect(r.trade_regime).toBe('ZLECAF');
    expect(r.zlecaf_status).toBe('DOCUMENTED');
    expect(r.zlecaf_tariff_amount).toBe(0);
    expect(r.savings).toBe(200);
    expect(r.savings_percentage).toBe(100);
  });

  it('marque la ligne réduite dans le tableau comparatif', () => {
    const ddRow = r.taxes_breakdown.find((row) => row.code === 'DD');
    expect(ddRow.amount_npf).toBe(200);
    expect(ddRow.amount_zlecaf).toBe(0);
    expect(ddRow.affected_by_zlecaf).toBe(true);
  });
});

describe('mapCalculToLegacyResult — un manque ne devient jamais un zéro', () => {
  const calcul = {
    position: { designation: 'Position à droit spécifique' },
    npf: {
      etat: 'INDISPONIBLE',
      lignes: [ligne({ taux_pct: null, montant: null, statut: 'QUANTITE_REQUISE' })],
      manques: [{ code: 'DD', motif: 'QUANTITE_REQUISE' }],
      total_droits: 0,
      total_a_payer: null,
      taux_effectif_pct: null,
    },
    preference_zlecaf: { applique: false, statut: 'NOT_AVAILABLE', note: '' },
    provenance: { niveau: 'national', source: {}, assiettes: {} },
  };

  const r = mapCalculToLegacyResult(calcul, contexte);

  it("n'affiche ni montant ni taux pour le droit manquant", () => {
    expect(r.normal_tariff_amount).toBeNull();
    expect(r.normal_tariff_rate).toBeNull();
    expect(r.dd_available).toBe(false);
    expect(r.duty_status).toBe('UNAVAILABLE');
    expect(r.duty_notice).toBe('QUANTITE_REQUISE');
  });

  it('exclut la ligne manquante du tableau comparatif plutôt que de la montrer à zéro', () => {
    expect(r.taxes_breakdown).toHaveLength(0);
  });

  it('marque la confiance comme partielle et conserve le motif', () => {
    expect(r.confidence_level).toBe('partial');
    expect(r._npf_etat).toBe('INDISPONIBLE');
    expect(r._manques_npf).toEqual([{ code: 'DD', motif: 'QUANTITE_REQUISE' }]);
  });
});

describe("mapCalculToLegacyResult — un droit sans économie ne divise jamais par zéro", () => {
  it('ne calcule pas de pourcentage quand le total NPF est nul', () => {
    const calcul = {
      position: {},
      npf: { etat: 'COMPLET', lignes: [ligne({ taux_pct: 0, montant: 0 })], manques: [],
        total_droits: 0, total_a_payer: 1000, taux_effectif_pct: 0 },
      preference: { etat: 'COMPLET', lignes: [ligne({ taux_pct: 0, montant: 0 })],
        total_droits: 0, total_a_payer: 1000, taux_effectif_pct: 0 },
      economie: 0,
      preference_zlecaf: { applique: true, statut: 'APPLIED', note: '' },
      provenance: { niveau: 'national', source: {}, assiettes: {} },
    };
    const r = mapCalculToLegacyResult(calcul, contexte);
    expect(r.savings_percentage).toBeNull();
    expect(Number.isFinite(r.savings_percentage)).toBe(false);
  });
});

describe('mapCalculToLegacyResult — une famille non tracée à la source ne vaut pas zéro', () => {
  it("rend la TVA nulle, pas zéro, quand la source ne la trace pas du tout", () => {
    const calcul = {
      position: {},
      npf: {
        etat: 'PARTIEL',
        lignes: [ligne()], // uniquement le DD, aucune ligne TVA
        manques: [{ code: 'TVA', motif: 'NON_TRACEE_A_LA_SOURCE' }],
        total_droits: 200,
        total_a_payer: 1200,
        taux_effectif_pct: 20,
      },
      preference_zlecaf: { applique: false, statut: 'NOT_AVAILABLE', note: '' },
      provenance: { niveau: 'national', source: {}, assiettes: {} },
    };
    const r = mapCalculToLegacyResult(calcul, contexte);
    expect(r.normal_vat_amount).toBeNull();
    expect(r.normal_tariff_amount).toBe(200); // le DD, lui, reste liquidé
  });

  it("rend zéro quand aucune ligne de TVA n'existe mais que la source la trace ailleurs (pas de manque)", () => {
    const calcul = {
      position: {},
      npf: {
        etat: 'COMPLET',
        lignes: [ligne()], // le produit n'a simplement aucune TVA applicable
        manques: [],
        total_droits: 200,
        total_a_payer: 1200,
        taux_effectif_pct: 20,
      },
      preference_zlecaf: { applique: false, statut: 'NOT_AVAILABLE', note: '' },
      provenance: { niveau: 'national', source: {}, assiettes: {} },
    };
    const r = mapCalculToLegacyResult(calcul, contexte);
    expect(r.normal_vat_amount).toBe(0);
  });

  it('rend la TVA nulle quand une ligne de TVA existe mais a échoué, plutôt que de l’ignorer', () => {
    const calcul = {
      position: {},
      npf: {
        etat: 'PARTIEL',
        lignes: [
          ligne(),
          ligne({ code: 'TVA', libelle: 'TVA', famille: 'tva', taux_pct: null, montant: null, statut: 'TAUX_INDISPONIBLE' }),
        ],
        manques: [{ code: 'TVA', motif: 'TAUX_INDISPONIBLE' }],
        total_droits: 200,
        total_a_payer: 1200,
        taux_effectif_pct: 20,
      },
      preference_zlecaf: { applique: false, statut: 'NOT_AVAILABLE', note: '' },
      provenance: { niveau: 'national', source: {}, assiettes: {} },
    };
    const r = mapCalculToLegacyResult(calcul, contexte);
    expect(r.normal_vat_amount).toBeNull();
  });
});

describe('mapCalculToLegacyResult — le journal ne fabrique jamais de « null% »', () => {
  it('affiche le libellé brut du droit spécifique au lieu de son taux pourcentuel', () => {
    const calcul = {
      position: {},
      npf: {
        etat: 'COMPLET',
        lignes: [
          ligne({
            code: 'DD', taux_pct: null, montant: 40, montant_unitaire: 0.08,
            specifique: '8c/kg', assiette: 'xQTE', base: 500,
          }),
        ],
        manques: [],
        total_droits: 40,
        total_a_payer: 1040,
        taux_effectif_pct: 4,
      },
      preference_zlecaf: { applique: false, statut: 'NOT_AVAILABLE', note: '' },
      provenance: { niveau: 'national', source: {}, assiettes: {} },
    };
    const r = mapCalculToLegacyResult(calcul, contexte);
    const ligneJournal = r.normal_calculation_journal.find((j) => j.component === 'Droit de douane');
    expect(ligneJournal.rate).toBe('8c/kg');
    expect(ligneJournal.rate).not.toContain('null');
  });
});

describe("mapCalculToLegacyResult — union douanière, un régime distinct de la ZLECAf", () => {
  const calcul = {
    position: {},
    npf: {
      etat: 'COMPLET',
      lignes: [ligne({ code: 'DD', taux_pct: null, montant: 8, montant_unitaire: 0.08, specifique: '8c/kg', assiette: 'xQTE', base: 100 })],
      manques: [],
      total_droits: 8,
      total_a_payer: 10008,
      taux_effectif_pct: 0.08,
    },
    preference: {
      etat: 'COMPLET',
      lignes: [ligne({ code: 'DD', taux_pct: 0, montant: 0, assiette: 'CIF', base: 10000, regime_applique: 'preference' })],
      manques: [],
      total_droits: 0,
      total_a_payer: 10000,
      taux_effectif_pct: 0,
    },
    regime_commercial: {
      applique: true,
      regime: 'UNION_DOUANIERE',
      code_bloc: 'SACU',
      libelle_bloc: "Union douanière d'Afrique australe (SACU)",
      statut: 'LIBRE_CIRCULATION',
      note: "Échanges intra-SACU : libre circulation sous le régime de l'union douanière.",
    },
    preference_zlecaf: { applique: false, statut: 'REGIME_UNION_DOUANIERE', note: "La ZLECAf ne s'applique pas ici." },
    provenance: { niveau: 'national', source: {}, assiettes: {} },
  };

  const r = mapCalculToLegacyResult(calcul, contexte);

  it('affiche bien la franchise au lieu de masquer la colonne préférentielle', () => {
    expect(r.zlecaf_tariff_amount).toBe(0);
    expect(r.normal_tariff_amount).toBe(8);
    expect(r.preferential_regime_applied).toBe(true);
  });

  it("nomme le régime réel, jamais « ZLECAF »", () => {
    expect(r.trade_regime).toBe('CUSTOMS_UNION');
    expect(r.trade_regime_code).toBe('SACU');
    expect(r.customs_union.code).toBe('SACU');
    expect(r.customs_union.label).toContain('SACU');
  });

  it("n'affirme aucune éligibilité ZLECAf sur un échange intra-union", () => {
    expect(r.zlecaf_eligible).toBe(false);
    expect(r.zlecaf_preference_applied).toBe(false);
    expect(r.zlecaf_status).toBe('NOT_AVAILABLE');
  });

  it("ne porte aucun bloc union douanière quand les pays n'en partagent pas", () => {
    const sansUnion = {
      ...calcul,
      regime_commercial: { applique: false, regime: 'ZLECAF', statut: 'NOT_AVAILABLE', note: '' },
    };
    expect(mapCalculToLegacyResult(sansUnion, contexte).customs_union).toBeNull();
  });
});

describe('mapCalculToLegacyResult — un complément national reste annoncé', () => {
  const calcul = {
    position: {},
    npf: {
      etat: 'COMPLET',
      lignes: [ligne(), ligne({ code: 'TVA', libelle: 'VAT', famille: 'tva', taux_pct: 15, base: 1200, montant: 180, classification_source: 'table_nationale_documentee' })],
      manques: [],
      total_droits: 380,
      total_a_payer: 1380,
      taux_effectif_pct: 38,
    },
    complements_nationaux: [{
      code: 'TVA', taux_pct: 15, motif: 'FAMILLE_ABSENTE_DE_LA_SOURCE',
      fiche: 'backend/data/legal_refs/zlecaf_application/ZAF_taux_TVA_2026-09-17.json',
      note: 'Taux standard national, non vérifié position par position',
    }],
    preference_zlecaf: { applique: false, statut: 'NOT_AVAILABLE', note: '' },
    provenance: { niveau: 'national', source: {}, assiettes: {} },
  };

  it("n'annonce pas une confiance très élevée sur un taux national moyen", () => {
    const r = mapCalculToLegacyResult(calcul, contexte);
    expect(r.confidence_level).toBe('partial');
    expect(r.complements_nationaux).toHaveLength(1);
    expect(r.complements_nationaux[0].fiche).toContain('ZAF_taux_TVA');
  });

  it('garde « very_high » quand tout vient de la collecte par position', () => {
    const sansComplement = { ...calcul, complements_nationaux: [] };
    expect(mapCalculToLegacyResult(sansComplement, contexte).confidence_level).toBe('very_high');
  });
});

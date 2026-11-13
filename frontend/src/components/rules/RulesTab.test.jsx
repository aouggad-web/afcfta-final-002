/**
 * Tests de l'onglet Règles d'origine.
 *
 * Seules les règles de valeur ajoutée portent un seuil. Pour les autres
 * (changement de position, produit entièrement obtenu, ouvraison spécifique,
 * règle en négociation), l'écran affiche le critère réel, jamais un
 * pourcentage de contenu régional.
 */
import React from 'react';
import { act, render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import axios from 'axios';

import RulesTab from './RulesTab';

vi.mock('axios');

// Le vrai sélecteur passe par une recherche et un menu déroulant ; un champ
// qui transmet le code saisi suffit ici.
vi.mock('../HSCodeSelector', () => ({
  HSCodeSearch: ({ onChange }) => (
    <input aria-label="Code SH" onChange={(e) => onChange(e.target.value)} />
  ),
  HSCodeBrowser: () => null,
}));

// Réponse de GET /api/rules-of-origin/{code}, réduite aux champs que lit l'écran.
const reponse = ({ code, status = 'AGREED', seuil = null, psr = '' }) => ({
  hs_code: '851900',
  status,
  rules: { primary_rule: { code }, alternative_rule: null },
  rule: { psr, value_added_threshold: seuil, category: code },
  match_type: 'heading',
  source: 'AfCFTA Appendix IV (PSR) - Décembre 2023',
});

const consulter = (data) => {
  axios.get.mockResolvedValue({ data });
  render(<RulesTab language="fr" />);
  fireEvent.change(screen.getByLabelText('Code SH'), { target: { value: '851900' } });
};

describe("Règles d'origine — critère d'une règle", () => {
  it.each([
    ['CTH', 'AGREED', 'Changement de position tarifaire'],
    ['WO', 'AGREED', 'Produit entièrement obtenu'],
    ['SP', 'AGREED', 'Ouvraison spécifique'],
    ['YTB', 'YTB', 'Règle en négociation'],
  ])('%s sans seuil : critère réel, ni contenu régional ni pourcentage', async (code, status, critere) => {
    consulter(reponse({ code, status }));

    const bloc = (await screen.findByText("Critère d'origine")).parentElement;
    expect(bloc).toHaveTextContent(critere);
    expect(screen.queryByText(/contenu régional/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/\d\s*%/)).not.toBeInTheDocument();
    expect(screen.queryByRole('progressbar')).not.toBeInTheDocument();
  });

  it('VA60 avec seuil : barre et pourcentage de contenu régional', async () => {
    consulter(reponse({ code: 'VA60', seuil: 40 }));

    expect(await screen.findByText('Contenu Régional Minimum')).toBeInTheDocument();
    expect(screen.getByText('40%')).toBeInTheDocument();
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
    expect(screen.queryByText("Critère d'origine")).not.toBeInTheDocument();
  });
});

describe("Règles d'origine — exigence", () => {
  it('« Exigence » affiche le texte de la règle ; plus de bloc « Informations Administratives »', async () => {
    // Texte de la règle de 85.19 dans l'appendice IV (raw_fr).
    const regle = 'Fabrication à partir de matières de toute position autre que celle du produit';
    consulter(reponse({ code: 'CTH', psr: regle }));

    const bloc = (await screen.findByText('Exigence')).parentElement;
    expect(bloc).toHaveTextContent(regle);
    expect(screen.queryByText('Informations Administratives')).not.toBeInTheDocument();
  });
});


it("écarte une réponse tardive pour un code précédent", async () => {
  let terminerAncienneRequete;
  axios.get
    .mockImplementationOnce(() => new Promise((resolve) => { terminerAncienneRequete = resolve; }))
    .mockResolvedValueOnce({ data: reponse({ code: 'CTH', psr: 'Règle récente' }) });

  render(<RulesTab language="fr" />);
  const saisie = screen.getByLabelText('Code SH');
  fireEvent.change(saisie, { target: { value: '040310' } });
  fireEvent.change(saisie, { target: { value: '851900' } });
  expect(await screen.findByText('Règle récente')).toBeInTheDocument();

  await act(async () => {
    terminerAncienneRequete({ data: reponse({ code: 'WO', psr: 'Règle précédente' }) });
  });
  expect(screen.getByText('Règle récente')).toBeInTheDocument();
  expect(screen.queryByText('Règle précédente')).not.toBeInTheDocument();
});

describe("Règles d'origine — explication et base légale", () => {
  it('règle en négociation : explication (note 2.4) et base légale affichées', async () => {
    const explication = "La règle d'origine de ce produit n'est pas encore adoptée : l'Appendice IV la laisse « à déterminer » ou entre crochets ; selon sa note 2.4, une règle entre crochets « n'a pas encore été adoptée par les institutions de négociation de la ZLECAf ». L'article 42 de l'Annexe 2 range parmi les dispositions en suspens l'« Elaboration de règles hybrides à l'Appendice IV de l'annexe 2 sur les règles d'origine » (alinéa 1(c)) et dispose : « En attendant l'adoption des dispositions en suspens, les États parties conviennent que les Règles d'Origine des régimes commerciaux existants sont applicables. » (alinéa 3).";
    const data = reponse({ code: 'YTB', status: 'YTB' });
    data.rules.primary_rule.explanation = explication;
    data.legal_reference = {
      instrument_fr: "Accord portant création de la ZLECAf — Annexe 2, Appendice IV",
      location_fr: 'chapitre 60',
      articles_fr: ['Annexe 2, article 42, alinéas 1(c) et 3 (dispositions en suspens)'],
      match_type: 'chapter',
      notes_fr: ['Appendice IV, note 2.4 (règle pas encore adoptée par les institutions de négociation de la ZLECAf)'],
      source_version: 'AfCFTA Appendix IV (PSR) - December 2023',
    };
    consulter(data);

    expect(await screen.findByText(explication)).toBeInTheDocument();
    expect(screen.getByTestId('origin-applied-to')).toHaveTextContent('règle par défaut du chapitre');
    expect(screen.getByText(/note 2\.4 \(règle pas encore adoptée/)).toBeInTheDocument();
    expect(screen.getByText('Annexe 2, article 42, alinéas 1(c) et 3 (dispositions en suspens)')).toBeInTheDocument();
  });
});

describe("Règles d'origine — ligne dont le texte n'énonce pas le critère de son code", () => {
  // Réponse de GET /api/rules-of-origin/210500 : codée WO, mais son texte
  // n'exige que des matières originaires de certains chapitres.
  const glaces = {
    hs_code: '851900',
    status: 'AGREED',
    product_description_fr: 'Glaces de consommation, même contenant du cacao',
    rules: {
      primary_rule: { code: 'WO', name: "Règle propre à cette ligne de l'Appendice IV", explanation: '', matches_text: false },
      alternative_rule: null,
      threshold_note_fr: null,
      applicable_notes: [],
    },
    rule: {
      psr: 'Fabrication dans laquelle les matières des chapitres 2, 4, 7, 8, 17 et 18 utilisées doivent être originaires',
      value_added_threshold: null,
      category: "Règle propre à cette ligne de l'Appendice IV",
    },
    match_type: 'heading',
    legal_reference: {
      instrument_fr: "Accord portant création de la ZLECAf — Protocole sur le commerce des marchandises, Annexe 2 sur les règles d'origine, Appendice IV",
      location_fr: 'position 21.05',
      ex: false,
      articles_fr: ["Annexe 2, article 6(2) (règles de l'Appendice IV)"],
      match_type: 'heading',
      notes_fr: [],
      source_version: 'AfCFTA Appendix IV (PSR) - December 2023, 12th Council of Ministers',
    },
  };

  it("ni « entièrement obtenu » ni art. 4(a)/5 : le texte de la ligne et l'art. 6(2) seulement", async () => {
    consulter(glaces);

    const critere = (await screen.findByText("Critère d'origine")).parentElement;
    expect(critere).toHaveTextContent("Règle propre à cette ligne de l'Appendice IV : voir l'exigence");
    expect(screen.queryByText(/entièrement obtenu/i)).not.toBeInTheDocument();
    expect(screen.queryByText('Ce que cela implique')).not.toBeInTheDocument();
    expect(screen.getByText("Annexe 2, article 6(2) (règles de l'Appendice IV)")).toBeInTheDocument();
    expect(screen.queryByText(/art\. 4\(a\)/)).not.toBeInTheDocument();
  });

  it("affiche les notes de l'Appendice IV de la ligne", async () => {
    consulter({
      ...glaces,
      rules: { ...glaces.rules, applicable_notes: ['Condition: les produits à base de blé du chapitre 11 utilisés doivent être originaires'] },
    });

    expect(await screen.findByText("Notes de l'Appendice IV")).toBeInTheDocument();
    expect(screen.getByText('Condition: les produits à base de blé du chapitre 11 utilisés doivent être originaires')).toBeInTheDocument();
  });
});

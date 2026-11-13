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
  it('règle en négociation : explication (art. 42(3)) et base légale affichées', async () => {
    const explication = "en attendant son adoption, l'article 42(3) de l'Annexe 2 prévoit que les règles d'origine des régimes commerciaux existants s'appliquent.";
    const data = reponse({ code: 'YTB', status: 'YTB' });
    data.rules.primary_rule.explanation = explication;
    data.legal_reference = {
      instrument_fr: "Accord portant création de la ZLECAf — Annexe 2, Appendice IV",
      location_fr: 'chapitre 60',
      articles_fr: ['Annexe 2, article 42(3) (règle non encore adoptée)'],
      match_type: 'chapter',
      notes_fr: ['Appendice IV, note 2.4 (texte non adopté)'],
      source_version: 'AfCFTA Appendix IV (PSR) - December 2023',
    };
    consulter(data);

    expect(await screen.findByText(explication)).toBeInTheDocument();
    expect(screen.getByTestId('origin-applied-to')).toHaveTextContent('règle par défaut du chapitre');
    expect(screen.getByText(/article 42\(3\) \(règle non encore adoptée\)/)).toBeInTheDocument();
  });
});

/**
 * Tests de l'onglet Règles d'origine.
 *
 * Seules les règles de valeur ajoutée portent un seuil. Pour les autres
 * (changement de position, produit entièrement obtenu, ouvraison spécifique,
 * règle en négociation), l'écran affiche le critère réel, jamais un
 * pourcentage de contenu régional.
 */
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
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
const reponse = ({ code, status = 'AGREED', seuil = null }) => ({
  hs_code: '851900',
  status,
  rules: { primary_rule: { code }, alternative_rule: null },
  rule: { psr: '', value_added_threshold: seuil, category: code, notes: '' },
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

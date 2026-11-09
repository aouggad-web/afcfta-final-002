/**
 * Panneau Règles d'origine du navigateur de codes SH (HSCodeBrowser), tel que
 * le montre le calculateur (showRulesOfOrigin).
 *
 * Seules les règles de valeur ajoutée (VA40, VA60, VA65) portent un seuil. Pour
 * les autres, le panneau ne montre ni barre ni pourcentage de contenu régional,
 * mais le critère réel. WO est le cas piège : l'API y renvoie
 * regional_content = 100 sans seuil, ce qui affichait un faux « 100 % ».
 */
import React from 'react';
import { render, screen, fireEvent, within } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import axios from 'axios';

import { HSCodeBrowser } from './HSCodeSelector';

vi.mock('axios');

// Réponse de GET /api/rules-of-origin/{code}?lang=fr, réduite aux champs que lit
// le panneau. Textes de l'appendice IV pour 85.19, le chapitre 01 et 84.01.
const regle = ({ hs, code, name, texte, seuil = null, contenu = null }) => ({
  hs_code: hs,
  status: 'AGREED',
  rules: {
    primary_rule: { code, name },
    regional_content: contenu,
    threshold_pct: seuil,
    rule_text_fr: texte,
  },
});

const CTH = regle({
  hs: '851900',
  code: 'CTH',
  name: 'Changement de Position Tarifaire',
  texte: 'Fabrication à partir de matières de toute position autre que celle du produit',
});
const WO = regle({
  hs: '010121',
  code: 'WO',
  name: 'Entièrement Obtenu',
  texte: 'Tous les animaux de ce chapitre utilisés doivent être entièrement obtenus',
  contenu: 100,
});
const VA60 = regle({
  hs: '840100',
  code: 'VA60',
  name: 'Max 60% valeur non-originaire',
  texte:
    "Fabrication dans laquelle la valeur de toutes les matières utilisées n'excède pas 60 % du prix départ usine du produit",
  seuil: 60,
  contenu: 40,
});

beforeEach(() => {
  vi.clearAllMocks();
});

// Recherche le code de la règle, le choisit et rend le panneau.
const ouvrirPanneau = async (regleOrigine, language = 'fr') => {
  const hs = regleOrigine.hs_code;
  axios.get.mockImplementation((url) => {
    if (url.includes('/hs-codes/search')) {
      return Promise.resolve({
        data: { results: [{ code: hs, label: 'Produit', chapter: hs.slice(0, 2), chapter_name: 'Chapitre' }] },
      });
    }
    if (url.includes(`/rules-of-origin/${hs}`)) return Promise.resolve({ data: regleOrigine });
    return Promise.resolve({ data: {} }); // chapitres, statistiques
  });
  render(<HSCodeBrowser language={language} showRulesOfOrigin />);
  fireEvent.change(screen.getByTestId('hs-browser-search'), { target: { value: hs } });
  fireEvent.click(await screen.findByTestId(`search-result-${hs}`));
  return screen.findByTestId('rules-of-origin-panel');
};

// Case du panneau : son intitulé et la valeur affichée dessous.
const caseDe = (panneau, intitule) => within(panneau).getByText(intitule).parentElement;

describe("HSCodeBrowser — panneau Règles d'origine", () => {
  it.each([
    ['CTH', CTH, 'Changement de position tarifaire'],
    ['WO', WO, 'Produit entièrement obtenu'],
  ])('%s, sans seuil : type, exigence et critère réel, ni pourcentage ni barre', async (_code, regleOrigine, critere) => {
    const panneau = await ouvrirPanneau(regleOrigine);

    expect(panneau).not.toHaveTextContent('%');
    expect(within(panneau).queryByTestId('regional-content-bar')).not.toBeInTheDocument();
    expect(caseDe(panneau, "Critère d'origine")).toHaveTextContent(critere);
    expect(caseDe(panneau, 'Type de règle')).toHaveTextContent(regleOrigine.rules.primary_rule.name);
    expect(caseDe(panneau, 'Exigence')).toHaveTextContent(regleOrigine.rules.rule_text_fr);
  });

  it('VA60 : barre et 40 % de contenu régional', async () => {
    const panneau = await ouvrirPanneau(VA60);

    expect(caseDe(panneau, 'Contenu régional')).toHaveTextContent('40%');
    expect(within(panneau).getByTestId('regional-content-bar').firstChild).toHaveStyle({ width: '40%' });
    expect(within(panneau).queryByText("Critère d'origine")).not.toBeInTheDocument();
  });

  it.each([
    ['en', 'Origin criterion', 'Change of tariff heading'],
    ['ar', 'معيار المنشأ', 'تغيير البند التعريفي'],
  ])('critère en %s, sans pourcentage', async (language, intitule, critere) => {
    const panneau = await ouvrirPanneau(CTH, language);

    expect(caseDe(panneau, intitule)).toHaveTextContent(critere);
    expect(panneau).not.toHaveTextContent('%');
  });
});

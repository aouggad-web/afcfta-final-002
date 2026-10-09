import React from 'react';
import { render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';
import i18n from '../../i18n';
import ReserveOrigine from './ReserveOrigine';

afterEach(() => i18n.changeLanguage('fr'));

// Forme rendue par POST /calcul pour DZA/0901111000 depuis la Tunisie.
const CAFE = {
  hs6: '090111',
  statut: 'AGREED',
  niveau: 'chapter',
  regle: {
    code: 'WO',
    nom: { fr: 'Entièrement Obtenu', en: 'Wholly Obtained' },
    explication: { fr: 'Critère du produit entièrement obtenu.', en: 'Wholly-obtained criterion.' },
  },
  regle_alternative: null,
  contenu_regional_pct: 100,
  reserve: "Sous réserve d'un certificat d'origine ZLECAf…",
};

describe('ReserveOrigine', () => {
  it('porte la mention et la règle SH6', () => {
    render(<ReserveOrigine regle={CAFE} />);
    expect(screen.getByText("Sous réserve d'un certificat d'origine ZLECAf")).toBeInTheDocument();
    expect(screen.getByText("Règle d'origine (SH 090111, niveau chapitre) : Entièrement Obtenu")).toBeInTheDocument();
    expect(screen.getByText('Critère du produit entièrement obtenu.')).toBeInTheDocument();
  });

  it('se traduit en anglais, règle comprise', async () => {
    await i18n.changeLanguage('en');
    render(<ReserveOrigine regle={CAFE} />);
    expect(screen.getByText('Subject to an AfCFTA certificate of origin')).toBeInTheDocument();
    expect(screen.getByText('Rule of origin (HS 090111, chapter level): Wholly Obtained')).toBeInTheDocument();
  });

  it("n'invente aucune règle quand l'Appendice IV n'en arrête pas", () => {
    render(<ReserveOrigine regle={{ ...CAFE, statut: 'YTB' }} />);
    expect(screen.getByText(/Aucune règle d'origine n'est arrêtée/)).toBeInTheDocument();
    expect(screen.queryByText(/Entièrement Obtenu/)).toBeNull();
  });

  it('garde la mention sans règle (chemin historique)', () => {
    render(<ReserveOrigine regle={null} />);
    expect(screen.getByText("Sous réserve d'un certificat d'origine ZLECAf")).toBeInTheDocument();
  });
});

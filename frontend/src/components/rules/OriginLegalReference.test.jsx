/**
 * Base légale et référence d'une règle d'origine : rattachement de la position
 * saisie à la ligne de l'Appendice IV, articles de l'Annexe 2, notes, source.
 */
import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';

import OriginLegalReference from './OriginLegalReference';

// Réponse de GET /api/rules-of-origin/8519810000, réduite à ce que lit le bloc.
const roo = {
  hs_code: '8519810000',
  legal_reference: {
    instrument_fr: "Accord portant création de la ZLECAf — Protocole sur le commerce des marchandises, Annexe 2 sur les règles d'origine, Appendice IV",
    location_fr: 'position 85.19',
    articles_fr: ['Annexe 2, article 6(1)(c) (Changement de Position Tarifaire)'],
    match_type: 'heading',
    matched_code: '8519',
    notes_fr: ['Appendice IV, note 2.5 (clause transitoire)'],
    source_version: 'AfCFTA Appendix IV (PSR) - December 2023, 12th Council of Ministers',
  },
};

describe("Base légale d'une règle d'origine", () => {
  it('rattache la position nationale à la ligne de l’Appendice IV et cite article, note et source', () => {
    render(<OriginLegalReference roo={roo} language="fr" />);

    expect(screen.getByTestId('origin-applied-to')).toHaveTextContent(
      'Position 8519810000 → Appendice IV, position 85.19 (aucune règle propre à la sous-position : règle de la position)'
    );
    expect(screen.getByText(/article 6\(1\)\(c\)/)).toBeInTheDocument();
    expect(screen.getByText(/note 2\.5/)).toBeInTheDocument();
    expect(screen.getByText(/Annexe 2 sur les règles d'origine, Appendice IV/)).toBeInTheDocument();
    expect(screen.getByText(/12th Council of Ministers/)).toBeInTheDocument();
  });

  it('traduit le rattachement en anglais et en arabe', () => {
    const { rerender } = render(<OriginLegalReference roo={roo} language="en" />);
    expect(screen.getByTestId('origin-applied-to')).toHaveTextContent('the heading rule applies');

    rerender(<OriginLegalReference roo={roo} language="ar" />);
    expect(screen.getByText('الأساس القانوني والمرجع')).toBeInTheDocument();
    expect(screen.getByTestId('origin-applied-to')).toHaveTextContent('تُطبَّق قاعدة البند');
  });

  it('ne rend rien sans référence', () => {
    const { container } = render(<OriginLegalReference roo={{ hs_code: '99' }} language="fr" />);
    expect(container).toBeEmptyDOMElement();
  });
});

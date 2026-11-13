/**
 * Base légale et référence d'une règle d'origine : rattachement de la position
 * saisie à la ligne de l'Appendice IV, articles de l'Annexe 2, notes, source.
 */
import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';

import OriginLegalReference from './OriginLegalReference';

const INSTRUMENT =
  "Accord portant création de la ZLECAf — Protocole sur le commerce des marchandises, Annexe 2 sur les règles d'origine, Appendice IV";
const SOURCE = 'AfCFTA Appendix IV (PSR) - December 2023, 12th Council of Ministers';

// Réponse de GET /api/rules-of-origin/8414101000, réduite à ce que lit le bloc.
const position8414 = {
  hs_code: '8414101000',
  product_description_fr:
    "Pompes à air ou à vide, compresseurs d'air ou d'autres gaz et ventilateurs ; hottes aspirantes à extraction ou à recyclage, à ventilateur incorporé, même filtrantes",
  legal_reference: {
    instrument_fr: INSTRUMENT,
    location_fr: 'position 84.14',
    ex: false,
    articles_fr: [
      "Annexe 2, article 6(2) (règles de l'Appendice IV)",
      'Annexe 2, article 6(1)(b) (Teneur des matières non originaires)',
    ],
    matched_code: '8414',
    match_type: 'heading',
    source_version: SOURCE,
    notes_fr: ['Appendice IV, note 2.5 (clause transitoire)'],
  },
};

// Réponse de GET /api/rules-of-origin/1512210000 (huile de coton brute) : la
// seule ligne de 15.12 est « ex », limitée aux huiles de tournesol et de carthame.
const ligneEx1512 = {
  hs_code: '1512210000',
  product_description_fr:
    'Ex 15.12: Huiles de tournesol, de carthame et leurs fractions, même raffinées, mais non chimiquement modifiées',
  legal_reference: {
    instrument_fr: INSTRUMENT,
    location_fr: 'ex position 15.12',
    ex: true,
    articles_fr: ["Annexe 2, article 6(2) (règles de l'Appendice IV)"],
    matched_code: '1512',
    match_type: 'heading',
    source_version: SOURCE,
    notes_fr: [],
  },
};

describe("Base légale d'une règle d'origine", () => {
  it('rattache la position nationale à la ligne de l’Appendice IV et cite articles, note et source', () => {
    render(<OriginLegalReference roo={position8414} language="fr" />);

    expect(screen.getByTestId('origin-applied-to')).toHaveTextContent(
      'Position 8414101000 → Appendice IV, position 84.14 (aucune règle propre à la sous-position : règle de la position)'
    );
    expect(screen.getByText("Annexe 2, article 6(2) (règles de l'Appendice IV)")).toBeInTheDocument();
    expect(screen.getByText('Annexe 2, article 6(1)(b) (Teneur des matières non originaires)')).toBeInTheDocument();
    expect(screen.getByText('Appendice IV, note 2.5 (clause transitoire)')).toBeInTheDocument();
    expect(screen.getByText(INSTRUMENT)).toBeInTheDocument();
    expect(screen.getByText(SOURCE)).toBeInTheDocument();
    expect(screen.queryByTestId('origin-ex-description')).not.toBeInTheDocument();
  });

  it('traduit le rattachement en anglais et en arabe, flèche tournée vers la ligne', () => {
    const { rerender } = render(<OriginLegalReference roo={position8414} language="en" />);
    expect(screen.getByTestId('origin-applied-to')).toHaveTextContent('Code 8414101000 → Appendice IV');
    expect(screen.getByTestId('origin-applied-to')).toHaveTextContent('the heading rule applies');

    rerender(<OriginLegalReference roo={position8414} language="ar" />);
    expect(screen.getByText('الأساس القانوني والمرجع')).toBeInTheDocument();
    expect(screen.getByTestId('origin-applied-to')).toHaveTextContent('8414101000 ← Appendice IV');
    expect(screen.getByTestId('origin-applied-to')).toHaveTextContent('تُطبَّق قاعدة البند');
  });

  it('ligne « ex » : ne prétend pas que la règle vaut pour toute la position et montre sa désignation', () => {
    render(<OriginLegalReference roo={ligneEx1512} language="fr" />);

    const rattachement = screen.getByTestId('origin-applied-to');
    expect(rattachement).toHaveTextContent('ligne « ex » : elle ne vise que les produits de sa désignation');
    expect(rattachement).not.toHaveTextContent('règle de la position');
    expect(screen.getByTestId('origin-ex-description')).toHaveTextContent(
      'Désignation de la ligne : Ex 15.12: Huiles de tournesol, de carthame'
    );
  });

  it('ne rend rien sans référence', () => {
    const { container } = render(<OriginLegalReference roo={{ hs_code: '99' }} language="fr" />);
    expect(container).toBeEmptyDOMElement();
  });
});

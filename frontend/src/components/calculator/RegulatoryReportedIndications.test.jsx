import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import RegulatoryReportedIndications from './RegulatoryReportedIndications';

const LAYER = {
  reliability: 'UNVERIFIED_SECONDARY',
  disclaimer: 'Indications non vérifiées, à confirmer.',
  items: [
    {
      side: 'import',
      country_iso3: 'SEN',
      country_name: 'Sénégal',
      program: 'Inspection non intrusive (Scanners)',
      providers: ['Cotecna'],
      mission: 'Scanners à rayons X.',
      payer: 'IMPORTER_OR_DECLARANT',
      period: { start: '2017', end: 'en cours' },
      reported_fee_range: 'RUS : 20 000 / 45 000 FCFA',
      traceability: 'Code des Douanes sénégalais.',
      verification_status: 'PARTIAL',
      fee_status: 'FEE_EXISTS_AMOUNT_NOT_AVAILABLE',
    },
  ],
};

describe('RegulatoryReportedIndications', () => {
  it('ne rend rien sans couche reportée', () => {
    const { container } = render(<RegulatoryReportedIndications result={{}} language="fr" />);
    expect(container).toBeEmptyDOMElement();
  });

  it('affiche un badge NON VÉRIFIÉ et l’avertissement', () => {
    render(<RegulatoryReportedIndications result={{ regulatory_reported: LAYER }} language="fr" />);
    // Badge exact (texte seul) + phrase d'avertissement complète.
    expect(screen.getByText('NON VÉRIFIÉ')).toBeInTheDocument();
    expect(screen.getByText(/synthèse secondaire NON VÉRIFIÉE/i)).toBeInTheDocument();
  });

  it('affiche la fourchette reportée étiquetée « à confirmer », jamais un total', () => {
    render(<RegulatoryReportedIndications result={{ regulatory_reported: LAYER }} language="fr" />);
    expect(screen.getByText(/RUS : 20 000 \/ 45 000 FCFA/)).toBeInTheDocument();
    expect(screen.getAllByText(/à confirmer/i).length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText(/Cotecna/)).toBeInTheDocument();
  });
});

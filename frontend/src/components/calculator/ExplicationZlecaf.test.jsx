import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import ExplicationZlecaf from './ExplicationZlecaf';

describe('ExplicationZlecaf', () => {
  it('affiche le niveau, les quatre questions et le lien vers la source', () => {
    render(<ExplicationZlecaf result={{
      origin_country_iso3: 'KEN',
      trade_regime: 'NPF',
      zlecaf_status: 'OFFER_ONLY',
      zlecaf_offer_rate_expression: '2.0%',
      zlecaf_offer_rate_source: { title: 'AfCFTA e-Tariff Book', url: 'https://etariff.au-afcfta.org/' },
    }} />);
    expect(screen.getByTestId('explication-zlecaf-niveau')).toHaveTextContent('Simulation sur offre');
    expect(screen.getByText('Statut de la préférence')).toBeInTheDocument();
    expect(screen.getByText(/Taux prévu par l’offre publiée : 2.0%/)).toBeInTheDocument();
    expect(screen.getByText(/n’est pas appliqué au total/)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Voir la source' }))
      .toHaveAttribute('href', 'https://etariff.au-afcfta.org/');
  });

  it("ne rend rien sans résultat", () => {
    const { container } = render(<ExplicationZlecaf result={null} />);
    expect(container).toBeEmptyDOMElement();
  });
});

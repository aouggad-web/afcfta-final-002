import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

vi.mock('axios', () => {
  const get = vi.fn(() =>
    Promise.resolve({
      data: {
        hs6: '520100',
        country_a: 'KEN',
        country_b: 'NGA',
        country_a_name: 'Kenya',
        country_b_name: 'Nigéria',
        flow_a_to_b: { importer: 'NGA', mfn_rate: 20, zlecaf_rate: 4, preference_margin: 16 },
        flow_b_to_a: { importer: 'KEN', mfn_rate: 10, zlecaf_rate: 2, preference_margin: 8 },
        best_preference_direction: 'a_to_b',
      },
    })
  );
  return { default: { get } };
});

import axios from 'axios';
import BilateralTariffComparator from './BilateralTariffComparator';

beforeEach(() => axios.get.mockClear());

describe('BilateralTariffComparator', () => {
  it('désactive le bouton tant que les entrées sont incomplètes', () => {
    render(<BilateralTariffComparator language="fr" />);
    expect(screen.getByRole('button', { name: /Comparer/i })).toBeDisabled();
  });

  it('refuse deux fois le même pays', async () => {
    render(<BilateralTariffComparator language="fr" />);
    const [selA, selB] = screen.getAllByRole('combobox');
    await userEvent.selectOptions(selA, 'KEN');
    await userEvent.selectOptions(selB, 'KEN');
    await userEvent.type(screen.getByRole('textbox'), '520100');
    expect(screen.getByText(/deux pays différents/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Comparer/i })).toBeDisabled();
  });

  it('appelle l’endpoint bilatéral et affiche les deux directions + la meilleure', async () => {
    render(<BilateralTariffComparator language="fr" />);
    const [selA, selB] = screen.getAllByRole('combobox');
    await userEvent.selectOptions(selA, 'KEN');
    await userEvent.selectOptions(selB, 'NGA');
    await userEvent.type(screen.getByRole('textbox'), '520100');

    await userEvent.click(screen.getByRole('button', { name: /Comparer/i }));

    await waitFor(() =>
      expect(axios.get).toHaveBeenCalledWith('/api/bilateral-tariff/KEN/NGA/520100')
    );

    // Marges des deux directions affichées.
    await waitFor(() => expect(screen.getByText('16 pts')).toBeInTheDocument());
    expect(screen.getByText('8 pts')).toBeInTheDocument();
    // Direction la plus avantageuse (a_to_b) = Kenya → Nigéria.
    expect(screen.getByText(/Kenya → Nigéria/)).toBeInTheDocument();
  });
});

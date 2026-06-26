import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

vi.mock('axios', () => {
  const get = vi.fn(() =>
    Promise.resolve({
      data: {
        country_iso3: 'KEN',
        hs6: '520100',
        trade_value: 1000000,
        npf_rate: 10,
        npf_rate_source: 'auto',
        category: 'A',
        category_label: 'Catégorie A',
        is_ldc: false,
        current_implementation_year: 5,
        current_zlecaf_rate: 2,
        annual_saving_now: 80000,
        full_liberalization_year: 2025,
        total_saving_over_schedule: 1300000,
        projection: [
          { year: 0, calendar_year: 2020, zlecaf_rate: 10, duty_npf: 100000, duty_zlecaf: 100000, annual_saving: 0, cumulative_saving: 0 },
          { year: 5, calendar_year: 2025, zlecaf_rate: 0, duty_npf: 100000, duty_zlecaf: 0, annual_saving: 100000, cumulative_saving: 300000 },
        ],
      },
    })
  );
  return { default: { get } };
});

vi.mock('recharts', () => {
  const Stub = ({ children }) => <div>{children}</div>;
  return {
    ResponsiveContainer: Stub, AreaChart: Stub, Area: Stub,
    XAxis: Stub, YAxis: Stub, CartesianGrid: Stub, Tooltip: Stub,
  };
});

import axios from 'axios';
import ZlecafImpactSimulator from './ZlecafImpactSimulator';

beforeEach(() => axios.get.mockClear());

describe('ZlecafImpactSimulator', () => {
  it('désactive le bouton tant que les entrées sont incomplètes', () => {
    render(<ZlecafImpactSimulator language="fr" />);
    expect(screen.getByRole('button', { name: /Simuler/i })).toBeDisabled();
  });

  it('appelle l’endpoint impact avec les bons paramètres et affiche la projection', async () => {
    render(<ZlecafImpactSimulator language="fr" />);

    // Pays importateur (KEN), produit HS6, valeur.
    await userEvent.selectOptions(screen.getByRole('combobox'), 'KEN');
    const inputs = screen.getAllByRole('textbox');
    await userEvent.type(inputs[0], '520100'); // HS6
    await userEvent.type(inputs[1], '1000000'); // valeur

    const btn = screen.getByRole('button', { name: /Simuler/i });
    expect(btn).toBeEnabled();
    await userEvent.click(btn);

    await waitFor(() => {
      expect(axios.get).toHaveBeenCalledWith(
        '/api/dismantlement/impact/KEN/520100',
        expect.objectContaining({ params: expect.objectContaining({ trade_value: 1000000, language: 'fr' }) })
      );
    });

    // KPI taux NPF + économie cumulée affichés (10% apparaît aussi dans le tableau).
    await waitFor(() => expect(screen.getAllByText('10%').length).toBeGreaterThan(0));
    expect(screen.getAllByText('$1,300,000').length).toBeGreaterThan(0);
    // Lignes du tableau (2 années mockées). 2020 unique au tableau ; 2025 aussi en KPI.
    expect(screen.getByText('2020')).toBeInTheDocument();
    expect(screen.getAllByText('2025').length).toBeGreaterThan(0);
  });

  it('n’envoie pas npf_rate quand le champ override est vide', async () => {
    render(<ZlecafImpactSimulator language="fr" />);
    await userEvent.selectOptions(screen.getByRole('combobox'), 'KEN');
    const inputs = screen.getAllByRole('textbox');
    await userEvent.type(inputs[0], '520100');
    await userEvent.type(inputs[1], '1000000');
    await userEvent.click(screen.getByRole('button', { name: /Simuler/i }));

    await waitFor(() => expect(axios.get).toHaveBeenCalled());
    const params = axios.get.mock.calls[0][1].params;
    expect(params).not.toHaveProperty('npf_rate');
  });
});

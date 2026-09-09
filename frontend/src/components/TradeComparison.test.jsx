import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

// --- Mock axios ---------------------------------------------------------
vi.mock('axios', () => {
  const get = vi.fn((url) => {
    if (url.endsWith('/api/statistics')) {
      return Promise.resolve({
        data: {
          overview: { estimated_combined_gdp: 3_000_000_000_000 },
          trade_evolution: {
            intra_african_trade_2023: 200,
            intra_african_trade_2024: 220,
            growth_rate_2023_2024: 10,
            trend: 'up',
          },
        },
      });
    }
    if (url.endsWith('/trade-performance')) {
      return Promise.resolve({
        data: {
          countries_global: [
            { code: 'ML', country: 'MockLand', exports_2024: 5, imports_2024: 3, trade_balance_2024: 2 },
          ],
        },
      });
    }
    if (url.endsWith('/trade-performance-intra-african')) {
      return Promise.resolve({
        data: {
          countries_intra_african: [
            { code: 'ML', country: 'MockLand', exports_2024: 5, imports_2024: 3, trade_balance_2024: 2, intra_african_percentage: 10 },
          ],
        },
      });
    }
    return Promise.resolve({ data: {} });
  });
  return { default: { get } };
});

// --- Mock recharts (évite ResponsiveContainer/layout en jsdom) ----------
vi.mock('recharts', () => {
  const Stub = ({ children }) => <div>{children}</div>;
  return {
    ResponsiveContainer: Stub,
    LineChart: Stub,
    Line: Stub,
    AreaChart: Stub,
    Area: Stub,
    XAxis: Stub,
    YAxis: Stub,
    CartesianGrid: Stub,
    Tooltip: Stub,
    Legend: Stub,
  };
});

import axios from 'axios';
import TradeComparison from './TradeComparison';

beforeEach(() => {
  axios.get.mockClear();
});

describe('TradeComparison — sélecteur d’année (non-régression)', () => {
  it('rend un sélecteur d’année avec 2024 par défaut et les options 2022-2024', async () => {
    render(<TradeComparison language="fr" />);

    const select = await screen.findByRole('combobox');
    expect(select).toHaveValue('2024');

    const options = within(select).getAllByRole('option').map((o) => o.value);
    expect(options).toEqual(['2024', '2023', '2022']);
  });

  it('charge les données 2024 depuis l’API au montage', async () => {
    render(<TradeComparison language="fr" />);
    await screen.findByRole('combobox');

    await waitFor(() => {
      expect(axios.get).toHaveBeenCalledWith(expect.stringContaining('/api/statistics'));
      expect(axios.get).toHaveBeenCalledWith(expect.stringContaining('/trade-performance'));
    });
    // La donnée 2024 (mockée) doit apparaître dans les tableaux
    expect(screen.getAllByText('MockLand').length).toBeGreaterThan(0);
  });

  it('bascule vers les données historiques quand on change l’année', async () => {
    render(<TradeComparison language="fr" />);
    const select = await screen.findByRole('combobox');
    expect(screen.getAllByText('MockLand').length).toBeGreaterThan(0);

    await userEvent.selectOptions(select, '2023');

    // Le setter doit mettre à jour la valeur affichée…
    expect(select).toHaveValue('2023');
    // …et déclencher l’affichage des données historiques codées (2023)
    await waitFor(() => {
      expect(screen.getAllByText('Afrique du Sud').length).toBeGreaterThan(0);
    });
    // L’ancienne donnée 2024 ne doit plus être affichée
    expect(screen.queryByText('MockLand')).toBeNull();
  });
});

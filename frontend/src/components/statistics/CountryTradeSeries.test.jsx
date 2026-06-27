import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

vi.mock('axios', () => {
  const get = vi.fn((url) => {
    const iso3 = String(url ?? '').match(/country\/([A-Z]{3})\//)?.[1];
    if (iso3 === 'ESH') {
      return Promise.resolve({
        data: { country_iso3: 'ESH', years: [2018], chart_rows: [], has_data: false, source: 'OEC / BACI' },
      });
    }
    return Promise.resolve({
      data: {
        country_iso3: iso3,
        country_name: iso3,
        years: [2022, 2023, 2024],
        chart_rows: [
          { year: 2022, exports: 60e9, imports: 50e9, balance: 10e9 },
          { year: 2023, exports: 70e9, imports: 55e9, balance: 15e9 },
          { year: 2024, exports: 80e9, imports: 60e9, balance: 20e9 },
        ],
        has_data: true,
        source: 'OEC / BACI (HS Rev. 2017)',
      },
    });
  });
  return { default: { get } };
});

vi.mock('recharts', () => {
  const Stub = ({ children }) => <div>{children}</div>;
  return {
    ResponsiveContainer: Stub, LineChart: Stub, Line: Stub,
    XAxis: Stub, YAxis: Stub, CartesianGrid: Stub, Tooltip: Stub, Legend: Stub,
  };
});

import axios from 'axios';
import CountryTradeSeries from './CountryTradeSeries';

beforeEach(() => axios.get.mockClear());

describe('CountryTradeSeries', () => {
  it('charge la série du pays par défaut au montage', async () => {
    render(<CountryTradeSeries language="fr" defaultCountry="NGA" />);
    await waitFor(() =>
      expect(axios.get).toHaveBeenCalledWith('/api/oec/country/NGA/trade-series')
    );
    // La source OEC apparaît une fois la série chargée.
    await waitFor(() => expect(screen.getByText(/OEC \/ BACI/)).toBeInTheDocument());
  });

  it('recharge la série quand on change de pays', async () => {
    render(<CountryTradeSeries language="fr" defaultCountry="NGA" />);
    await waitFor(() => expect(axios.get).toHaveBeenCalledWith('/api/oec/country/NGA/trade-series'));

    await userEvent.selectOptions(screen.getByRole('combobox'), 'KEN');
    await waitFor(() =>
      expect(axios.get).toHaveBeenCalledWith('/api/oec/country/KEN/trade-series')
    );
  });

  it('affiche un message quand le pays n’a pas de données OEC', async () => {
    render(<CountryTradeSeries language="fr" defaultCountry="ESH" />);
    await waitFor(() =>
      expect(screen.getByText(/Aucune donnée commerciale OEC/i)).toBeInTheDocument()
    );
  });
});

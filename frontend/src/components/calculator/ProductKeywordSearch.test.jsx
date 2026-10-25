/**
 * Recherche par mot-clé : elle interroge le tarif du pays de destination au
 * socle, et ne montre que le droit de douane — le total est celui du calcul.
 */
import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import axios from 'axios';

import ProductKeywordSearch from './ProductKeywordSearch';

vi.mock('axios');

const LIGNE = {
  code: '24021090',
  hs6: '240210',
  digits: 8,
  description_fr: 'Other',
  description_en: 'Other',
  intitule_sh4: 'Cigars, cheroots, cigarillos and cigarettes',
  dd_rate: null,
  dd_expression: '45 %, min. 1 500 R/kg',
};

describe('ProductKeywordSearch', () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it('cherche dans le tarif du pays de destination, lu au socle', async () => {
    axios.get.mockResolvedValue({ data: { results: [LIGNE], total: 13 } });
    const onSelect = vi.fn();
    render(<ProductKeywordSearch destinationCountry="ZA" onSelect={onSelect} />);

    await userEvent.type(screen.getByRole('textbox'), 'cigarettes');

    expect(await screen.findByText('1 / 13', { exact: false })).toBeInTheDocument();
    expect(axios.get).toHaveBeenCalledWith(
      expect.stringMatching(/\/api\/consultation\/ZAF\/recherche$/),
      { params: { q: 'cigarettes', limit: 25, langue: 'fr' } },
    );
    expect(screen.getByText('2402 — Cigars, cheroots, cigarillos and cigarettes')).toBeInTheDocument();
    expect(screen.getByText('DD 45 %, min. 1 500 R/kg')).toBeInTheDocument();
    expect(screen.queryByText(/TVA|Total/)).not.toBeInTheDocument();

    await userEvent.click(screen.getByText('24021090'));
    expect(onSelect).toHaveBeenCalledWith('24021090', 'Other', LIGNE);
  });

  it("en anglais, cherche dans le tarif en anglais", async () => {
    axios.get.mockResolvedValue({ data: { results: [LIGNE], total: 1 } });
    render(<ProductKeywordSearch destinationCountry="KE" language="en" onSelect={vi.fn()} />);

    await userEvent.type(screen.getByRole('textbox'), 'coffee');

    await waitFor(() => expect(axios.get).toHaveBeenCalledWith(
      expect.stringMatching(/\/api\/consultation\/KEN\/recherche$/),
      { params: { q: 'coffee', limit: 25, langue: 'en' } },
    ));
  });

  it("sans pays de destination, ne cherche pas et le dit", async () => {
    render(<ProductKeywordSearch destinationCountry="" onSelect={vi.fn()} />);

    await userEvent.type(screen.getByRole('textbox'), 'café');

    expect(await screen.findByText('Choisissez d’abord le pays de destination')).toBeInTheDocument();
    await waitFor(() => expect(axios.get).not.toHaveBeenCalled());
  });
});

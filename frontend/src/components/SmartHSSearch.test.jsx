/**
 * Recherche du calculateur : les positions nationales du tarif de destination,
 * lues au socle ; la sélection transmet la position et charge sa règle d'origine.
 */
import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import axios from 'axios';

import SmartHSSearch from './SmartHSSearch';

vi.mock('axios');

const LIGNE = {
  code: '0902100010',
  hs6: '090210',
  digits: 10,
  description_fr: 'Thé vert (non fermenté) — en emballages immédiats',
  description_en: 'Green tea',
  intitule_sh4: 'Tea, whether or not flavoured',
  dd_rate: 32.5,
  dd_expression: null,
};

describe('SmartHSSearch', () => {
  beforeEach(() => {
    vi.resetAllMocks();
    axios.get.mockImplementation((url) => Promise.resolve(
      url.includes('/consultation/')
        ? { data: { results: [LIGNE], total: 1 } }
        : { data: { regle: 'WO' } },
    ));
  });

  it('cherche au socle du pays de destination et transmet la position choisie', async () => {
    const onChange = vi.fn();
    const onSubPositionSelect = vi.fn();
    const onRuleOfOriginLoad = vi.fn();
    render(
      <SmartHSSearch
        value=""
        onChange={onChange}
        destinationCountry="MA"
        onSubPositionSelect={onSubPositionSelect}
        onRuleOfOriginLoad={onRuleOfOriginLoad}
      />,
    );

    await userEvent.type(screen.getByTestId('hs-search-input'), 'thé vert');

    expect(await screen.findByText('0902100010')).toBeInTheDocument();
    expect(axios.get).toHaveBeenCalledWith(
      expect.stringMatching(/\/api\/consultation\/MAR\/recherche$/),
      { params: { q: 'thé vert', limit: 25, langue: 'fr' } },
    );
    expect(screen.getByText('DD: 32.5%')).toBeInTheDocument();
    expect(screen.getByText('0902 — Tea, whether or not flavoured')).toBeInTheDocument();

    await userEvent.click(screen.getByText('0902100010'));
    expect(onChange).toHaveBeenCalledWith('0902100010');
    expect(onSubPositionSelect).toHaveBeenCalledWith('0902100010', LIGNE.description_fr, null);
    await waitFor(() => expect(onRuleOfOriginLoad).toHaveBeenCalledWith({ regle: 'WO' }));
  });

  it("sans pays de destination, n'interroge rien et le dit", async () => {
    render(<SmartHSSearch value="" onChange={vi.fn()} destinationCountry="" />);

    await userEvent.type(screen.getByTestId('hs-search-input'), 'café');

    expect(await screen.findByText('Choisissez d’abord le pays de destination')).toBeInTheDocument();
    expect(axios.get).not.toHaveBeenCalled();
  });
});

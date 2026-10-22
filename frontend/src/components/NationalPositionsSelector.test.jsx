import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import axios from 'axios';

import NationalPositionsSelector from './NationalPositionsSelector';

vi.mock('axios');

describe('NationalPositionsSelector', () => {
  it('signale au calculateur combien de positions il sert, pour quel pays et quel SH6', async () => {
    axios.get.mockResolvedValue({
      data: {
        sub_positions: [
          { code: '0201101100', digits: 10, description_fr: 'De veaux' },
          { code: '0201109000', digits: 10, description_fr: "D'autres bovins" },
        ],
      },
    });
    const onPositionsLoaded = vi.fn();
    render(<NationalPositionsSelector countryCode="DZA" hs6Code="020110" onPositionsLoaded={onPositionsLoaded} />);

    expect(await screen.findByText('0201101100')).toBeInTheDocument();
    expect(axios.get).toHaveBeenCalledWith(expect.stringContaining('/consultation/DZA/sous-positions/020110'));
    expect(onPositionsLoaded).toHaveBeenCalledWith({ countryCode: 'DZA', hs6: '020110', total: 2 });
  });

  it('une liste indisponible ne bloque pas le calcul : elle compte zéro position', async () => {
    axios.get.mockRejectedValue({ response: { status: 503 } });
    const onPositionsLoaded = vi.fn();
    render(<NationalPositionsSelector countryCode="XXX" hs6Code="020110" onPositionsLoaded={onPositionsLoaded} />);

    expect(await screen.findByText('Erreur lors du chargement des positions')).toBeInTheDocument();
    expect(onPositionsLoaded).toHaveBeenCalledWith({ countryCode: 'XXX', hs6: '020110', total: 0 });
  });
});

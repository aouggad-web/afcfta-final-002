/**
 * Onglet Flux stratégiques — rendu des flux et erreur montrée.
 *
 * Ce module vient de perdre ses 34 libellés en dur au profit d'i18n, et ses
 * trois composants internes recevaient jusque-là le dictionnaire par une prop
 * nommée `t`. Le risque de cette migration n'est pas de casser le build — il
 * est qu'un composant rende `opportunities.strategicFlows.quelqueChose` à la
 * place d'un libellé. Ces tests s'exécutent avec la VRAIE instance i18n :
 * une clé manquante apparaîtrait donc en clair dans le DOM et ferait échouer
 * l'assertion de libellé.
 *
 * Le second test tient l'autre bout : une erreur de l'API doit être MONTRÉE.
 * Un écran de flux vide se lit comme « ce pays n'a pas d'opportunité », ce qui
 * est un tout autre message que « la requête a échoué ».
 */
import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import axios from 'axios';

import StrategicFlows from './StrategicFlows';

vi.mock('axios');

const FLOWS = {
  country: 'Kenya',
  summary: { total: 1 },
  flows: [
    {
      hs_code: '0902',
      product: 'Thé',
      signal: 'strong',
      is_emerging: false,
      potential_usd: 125_000_000,
      from: 'KEN',
      discovery_tier: 'tier1',
      strategic_rationale: 'Transformation locale possible',
      transformation: { input_target: 1000, output_target: 800 },
      advantage: { afcfta_tariff_edge: {}, rules_of_origin: {} },
      markets: [{ iso3: 'EGY', name: 'Égypte', value_usd: 40_000_000 }],
      capacity_evidence: {},
    },
  ],
};

beforeEach(() => {
  vi.clearAllMocks();
});

const mockOk = () =>
  axios.get.mockImplementation((url) => {
    if (url.includes('/substitution/countries')) {
      return Promise.resolve({ data: { countries: [{ iso3: 'KEN', name: 'Kenya' }] } });
    }
    if (url.includes('/strategic/flows/')) return Promise.resolve({ data: FLOWS });
    return Promise.resolve({ data: {} });
  });

describe('StrategicFlows', () => {
  it('affiche les flux du pays reçu en entrée', async () => {
    mockOk();
    render(<StrategicFlows language="fr" initialCountry={{ iso3: 'KEN' }} />);
    expect(await screen.findByTestId('strategic-flow-card')).toBeInTheDocument();
    expect(screen.getByText('0902')).toBeInTheDocument();
  });

  it('ne laisse aucune clé i18n brute à l’écran', async () => {
    mockOk();
    const { container } = render(<StrategicFlows language="fr" initialCountry={{ iso3: 'KEN' }} />);
    await screen.findByTestId('strategic-flow-card');
    // Une clé non traduite se rend telle quelle : « opportunities.x.y ».
    expect(container.textContent).not.toMatch(/opportunities\.[a-zA-Z]+\./);
  });

  it('montre l’erreur de l’API plutôt qu’une liste vide', async () => {
    axios.get.mockImplementation((url) => {
      if (url.includes('/substitution/countries')) {
        return Promise.resolve({ data: { countries: [] } });
      }
      return Promise.reject({ response: { data: { detail: 'Service indisponible' } } });
    });
    render(<StrategicFlows language="fr" initialCountry={{ iso3: 'KEN' }} />);
    expect(await screen.findByText('Service indisponible')).toBeInTheDocument();
    await waitFor(() =>
      expect(screen.queryByTestId('strategic-flow-card')).not.toBeInTheDocument());
  });
});

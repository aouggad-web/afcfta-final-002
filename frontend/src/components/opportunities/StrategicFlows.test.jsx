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

  it('cite le texte de la ligne quand la règle est propre à la ligne (15.11)', async () => {
    const texte = 'Fabrication dans laquelle la valeur de toutes les matières non originaires '
      + 'utilisées ne doit pas excéder 60% du prix départ usine du produit pendant 3 ans, '
      + 'après quoi la fabrication dans laquelle les matières utilisées doivent être '
      + "entièrement obtenues doit faire l'objet d'un examen objectif";
    const roo = {
      rule_name: "Règle propre à cette ligne de l'Appendice IV",
      rule_type: 'VA60',
      matches_text: false,
      rule_text_fr: texte,
    };
    const flow = { ...FLOWS.flows[0], hs_code: '151110', advantage: { afcfta_tariff_edge: {}, rules_of_origin: roo } };
    axios.get.mockImplementation((url) => {
      if (url.includes('/substitution/countries')) {
        return Promise.resolve({ data: { countries: [{ iso3: 'KEN', name: 'Kenya' }] } });
      }
      if (url.includes('/strategic/flows/')) return Promise.resolve({ data: { ...FLOWS, flows: [flow] } });
      return Promise.resolve({ data: {} });
    });
    render(<StrategicFlows language="fr" initialCountry={{ iso3: 'KEN' }} />);
    expect(await screen.findByText("Règle propre à cette ligne de l'Appendice IV")).toBeInTheDocument();
    const cite = screen.getByTestId('roo-rule-text');
    expect(cite).toHaveTextContent(texte);
    expect(cite).toHaveAttribute('lang', 'fr');
  });

  it('ne répète pas le texte quand le nom du critère suffit', async () => {
    const roo = { rule_name: 'Changement de Position Tarifaire', rule_type: 'CTH', matches_text: true, rule_text_fr: 'x' };
    const flow = { ...FLOWS.flows[0], advantage: { afcfta_tariff_edge: {}, rules_of_origin: roo } };
    axios.get.mockImplementation((url) => {
      if (url.includes('/substitution/countries')) {
        return Promise.resolve({ data: { countries: [{ iso3: 'KEN', name: 'Kenya' }] } });
      }
      if (url.includes('/strategic/flows/')) return Promise.resolve({ data: { ...FLOWS, flows: [flow] } });
      return Promise.resolve({ data: {} });
    });
    render(<StrategicFlows language="fr" initialCountry={{ iso3: 'KEN' }} />);
    expect(await screen.findByText('Changement de Position Tarifaire')).toBeInTheDocument();
    expect(screen.queryByTestId('roo-rule-text')).not.toBeInTheDocument();
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

  it('annonce l’abonnement requis au lieu de planter sur le refus du serveur', async () => {
    // Module Opportunités réservé aux abonnements payants (audit E1) : le
    // `detail` du refus est un objet, que React ne peut pas afficher tel quel.
    const refus = {
      response: {
        status: 403,
        data: { detail: { error: 'upgrade_required', tier: 'anonymous', message: 'Réservé' } },
      },
    };
    axios.get.mockImplementation(() => Promise.reject(refus));
    render(<StrategicFlows language="fr" initialCountry={{ iso3: 'KEN' }} />);
    const avis = await screen.findAllByTestId('subscription-notice');
    expect(avis[0]).toHaveTextContent('réservé aux abonnements payants');
    expect(avis[0].querySelector('a')).toHaveAttribute('href', '/pricing.html');
  });
});

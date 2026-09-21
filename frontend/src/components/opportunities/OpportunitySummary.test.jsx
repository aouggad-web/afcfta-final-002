/**
 * Onglet Vue d'ensemble — les chiffres servis, et le « — » quand il n'y en a pas.
 *
 * Le contrat de données de la plateforme tient dans le deuxième test : quand
 * le backend n'a pas de chiffre sourcé pour le commerce intra-africain, il
 * renvoie `null`, et l'écran doit afficher « — ». Un composant de synthèse est
 * l'endroit le plus tentant pour glisser une valeur de repli qui « fait
 * sérieux » — et le plus dangereux, parce qu'un chiffre rond sur une carte de
 * résumé est repris tel quel sans qu'on remonte à sa source.
 */
import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import axios from 'axios';

import OpportunitySummary from './OpportunitySummary';

vi.mock('axios');

const aiSummary = (overview) => ({
  overview,
  top_trading_countries: [{ name: 'Afrique du Sud', trade_volume_billion: 120.4, iso3: 'ZAF' }],
  top_sectors: [{ name: 'Minerais', hs_chapter: '26' }],
  data_freshness: null,
});

const mockSummary = (overview) =>
  axios.get.mockImplementation((url) => {
    if (url.includes('/ai/summary')) return Promise.resolve({ data: aiSummary(overview) });
    return Promise.resolve({ data: null });
  });

beforeEach(() => {
  vi.clearAllMocks();
});

describe('OpportunitySummary', () => {
  it('affiche la synthèse servie par le backend', async () => {
    mockSummary({
      total_opportunities_identified: 5387,
      total_african_trade_billion_usd: 1650,
      intra_african_trade_billion_usd: 186,
      afcfta_countries: 54,
    });
    render(<OpportunitySummary language="fr" />);
    expect(await screen.findByTestId('opportunity-summary')).toBeInTheDocument();
    expect(screen.getByText('5,387')).toBeInTheDocument();
  });

  it('affiche « — » quand le backend n’a pas de chiffre sourcé, jamais un repli', async () => {
    mockSummary({
      total_opportunities_identified: 5387,
      total_african_trade_billion_usd: 1650,
      intra_african_trade_billion_usd: null,
      afcfta_countries: 54,
    });
    render(<OpportunitySummary language="fr" />);
    await screen.findByTestId('opportunity-summary');
    expect(screen.getAllByText('—').length).toBeGreaterThan(0);
    // 186 Md$ est l'ordre de grandeur souvent cité : s'il réapparaissait ici
    // alors que la source ne l'a pas donné, ce serait une valeur fabriquée.
    expect(screen.queryByText(/186/)).not.toBeInTheDocument();
  });

  it('DÉFAUT CONNU : quand tout échoue, l’écran affiche des chiffres inventés', async () => {
    // Ce test ne bénit pas ce comportement, il le RETIENT. Chaque appel de ce
    // composant porte son propre `.catch`, si bien que l'état d'erreur est
    // inatteignable : la branche de repli sert alors des valeurs écrites en
    // dur — 5 387 opportunités, 186 Md$ de commerce intra-africain, « +12,3 % »
    // de croissance, et un tableau de produits entièrement inventé — sans que
    // rien à l'écran n'indique que la donnée manque.
    //
    // C'est une infraction directe au contrat « zéro fabrication », sur
    // l'écran d'accueil du module. La correction (afficher « — » et dire
    // l'échec) change ce que voit l'utilisateur : elle est proposée au plan
    // et attend un arbitrage. Le jour où elle sera faite, CE TEST DOIT
    // ÉCHOUER — c'est le signal qu'il est temps de le réécrire.
    axios.get.mockRejectedValue(new Error('réseau'));
    render(<OpportunitySummary language="fr" />);
    await screen.findByTestId('opportunity-summary');
    expect(screen.getByText('5,387')).toBeInTheDocument();
    expect(screen.queryByText(/Erreur lors du chargement/i)).not.toBeInTheDocument();
  });
});

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

  it('annonce les valeurs de référence, datées, au lieu de les substituer en silence', async () => {
    // Les chiffres de repli sont CONSERVÉS — c'est une décision assumée : la
    // propriétaire de la plateforme s'engage à provisionner l'API, de sorte
    // que ce chemin ne serve pratiquement jamais.
    //
    // Ce qui est verrouillé ici, c'est qu'ils ne se substituent plus en
    // silence. Auparavant les deux branches rendaient le MÊME écran, la seule
    // différence étant un badge vert qui apparaissait en cas de succès — et
    // l'absence d'un badge ne se remarque pas. Un écran s'intercale désormais.
    //
    // La date affichée est celle de la dernière RÉVISION de ces valeurs dans
    // le code, pas un millésime de la donnée : rien dans le dépôt n'atteste
    // l'année qu'elles décrivent, et l'inventer serait exactement la
    // fabrication que ce bandeau sert à éviter.
    axios.get.mockRejectedValue(new Error('réseau'));
    render(<OpportunitySummary language="fr" />);

    const bandeau = await screen.findByTestId('summary-reference-banner');
    expect(bandeau).toHaveTextContent(/Valeurs de référence/i);
    expect(bandeau).toHaveTextContent(/9 septembre 2026/);
    // Les chiffres restent servis : le bandeau les qualifie, il ne les cache pas.
    expect(screen.getByText('5,387')).toBeInTheDocument();
  });

  it('ne montre aucun bandeau quand le service répond', async () => {
    mockSummary({
      total_opportunities_identified: 5387,
      total_african_trade_billion_usd: 1650,
      intra_african_trade_billion_usd: 186,
      afcfta_countries: 54,
    });
    render(<OpportunitySummary language="fr" />);
    await screen.findByTestId('opportunity-summary');
    expect(screen.queryByTestId('summary-reference-banner')).not.toBeInTheDocument();
  });
});

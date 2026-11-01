import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import AntidumpingSaisie from './AntidumpingSaisie';
import { antidumpingSaisieProposee, buildCalculRequestBody, paysExpeditionRequete } from './unifiedCalculator';

describe('AntidumpingSaisie', () => {
  it('remonte le producteur et le pays d’expédition en majuscules', async () => {
    const onProducteurChange = vi.fn();
    const onExpeditionChange = vi.fn();
    render(<AntidumpingSaisie onProducteurChange={onProducteurChange} onExpeditionChange={onExpeditionChange} />);
    await userEvent.type(screen.getByTestId('antidumping-producteur'), 'N');
    expect(onProducteurChange).toHaveBeenCalledWith('N');
    await userEvent.type(screen.getByTestId('antidumping-expedition'), 't');
    expect(onExpeditionChange).toHaveBeenCalledWith('T');
  });

  it('ne demande pas le pays d’expédition quand la question SACU le pose déjà', () => {
    render(<AntidumpingSaisie avecExpedition={false} />);
    expect(screen.queryByTestId('antidumping-expedition')).toBeNull();
  });
});

describe('antidumpingSaisieProposee', () => {
  it('seulement pour un antidumping en vigueur', () => {
    expect(antidumpingSaisieProposee(null)).toBe(false);
    expect(antidumpingSaisieProposee([{ type: 'sauvegarde', statut: 'APPLIQUEE' }])).toBe(false);
    expect(antidumpingSaisieProposee([{ type: 'antidumping', statut: 'HORS_PERIODE' }])).toBe(false);
    expect(antidumpingSaisieProposee([{ type: 'antidumping', statut: 'PRODUCTEUR_NON_FOURNI' }])).toBe(true);
    expect(antidumpingSaisieProposee([{ type: 'antidumping', statut: 'EXPEDITION_NON_FOURNIE' }])).toBe(true);
  });
});

describe('producteur transmis à POST /calcul', () => {
  const base = { destinationISO3: 'ZAF', originISO3: 'JPN', hsCode: '72081000', cifValue: 1000 };
  it("n'envoie le producteur que s'il est déclaré", () => {
    expect(buildCalculRequestBody(base).producteur).toBeUndefined();
    expect(buildCalculRequestBody({ ...base, producteur: '  ' }).producteur).toBeUndefined();
    expect(buildCalculRequestBody({ ...base, producteur: ' Nippon Steel ' }).producteur).toBe('Nippon Steel');
  });

});

describe('paysExpeditionRequete', () => {
  it('un pays précis remplace « AUTRE » ou une réponse SACU inconnue', () => {
    expect(paysExpeditionRequete('ZAF', 'BWA', 'no', 'TWN')).toBe('TWN');
    expect(paysExpeditionRequete('ZAF', 'BWA', 'unknown', 'TWN')).toBe('TWN');
    expect(paysExpeditionRequete('ZAF', 'KEN', 'unknown', 'TWN')).toBe('TWN');
  });

  it('la réponse SACU reste seule sans pays précis, et prime quand elle est positive', () => {
    expect(paysExpeditionRequete('ZAF', 'BWA', 'no', '')).toBe('AUTRE');
    expect(paysExpeditionRequete('ZAF', 'BWA', 'no', 'TW')).toBe('AUTRE');
    expect(paysExpeditionRequete('ZAF', 'BWA', 'yes', 'TWN')).toBe('BWA');
    expect(paysExpeditionRequete('ZAF', 'KEN', 'unknown', undefined)).toBeUndefined();
  });

  it("écarte l'origine même après une réponse négative", () => {
    expect(paysExpeditionRequete('ZAF', 'BWA', 'no', 'BWA')).toBe('AUTRE');
  });
});

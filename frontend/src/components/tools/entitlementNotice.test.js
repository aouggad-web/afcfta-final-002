import { describe, expect, it } from 'vitest';

import { entitlementNoticeText, entitlementRefusal } from './entitlementNotice';

// Charge utile réellement renvoyée par entitlement_guard._forbidden().
const upgradeRequired = {
  response: {
    status: 403,
    data: {
      detail: {
        error: 'upgrade_required',
        tier: 'free',
        module: 'tools',
        message: "Ce module n'est pas inclus dans la formule 'free'. Passez à une formule supérieure pour y accéder.",
      },
    },
  },
};

describe('entitlementRefusal', () => {
  it('reconnaît le refus d’abonnement du module Outils', () => {
    expect(entitlementRefusal(upgradeRequired)).toEqual({
      kind: 'upgrade_required',
      tier: 'free',
      message: upgradeRequired.response.data.detail.message,
    });
  });

  it('reconnaît un 403 sans charge utile structurée', () => {
    expect(entitlementRefusal({ response: { status: 403, data: {} } }))
      .toEqual({ kind: 'upgrade_required', tier: null, message: null });
  });

  it('reconnaît un dépassement de quota (formule plafonnée)', () => {
    const refusal = entitlementRefusal({
      response: { status: 429, data: { detail: { error: 'quota_exceeded', tier: 'starter' } } },
    });
    expect(refusal).toEqual({ kind: 'quota_exceeded', tier: 'starter', message: null });
  });

  it('ne masque pas une vraie panne', () => {
    expect(entitlementRefusal({ response: { status: 500, data: {} } })).toBeNull();
    expect(entitlementRefusal({ response: { status: 404, data: {} } })).toBeNull();
    expect(entitlementRefusal({ response: { status: 401, data: {} } })).toBeNull();
    // Erreur réseau : pas de réponse HTTP du tout.
    expect(entitlementRefusal({ message: 'Network Error' })).toBeNull();
    expect(entitlementRefusal(undefined)).toBeNull();
  });
});

describe('entitlementNoticeText', () => {
  it('préfère le message du serveur, qui nomme la formule courante', () => {
    expect(entitlementNoticeText(entitlementRefusal(upgradeRequired), 'fr'))
      .toContain("formule 'free'");
  });

  it('retombe sur un libellé local quand le serveur n’en fournit pas', () => {
    const refusal = { kind: 'upgrade_required', tier: null, message: null };
    expect(entitlementNoticeText(refusal, 'fr')).toContain('formules payantes');
    expect(entitlementNoticeText(refusal, 'en')).toContain('paid plans');
  });

  it('distingue le quota atteint du module non inclus', () => {
    const refusal = { kind: 'quota_exceeded', tier: 'starter', message: null };
    expect(entitlementNoticeText(refusal, 'fr')).toContain('Quota');
  });

  it('ne dit rien en l’absence de refus', () => {
    expect(entitlementNoticeText(null, 'fr')).toBeNull();
  });
});

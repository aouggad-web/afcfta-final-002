import { describe, expect, it } from 'vitest';

import {
  anonymousCalculationNoticeText,
  entitlementNoticeText,
  entitlementRefusal,
  PRICING_URL,
  reportsNoticeText,
} from './entitlementNotice';

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

describe('entitlementNoticeText en arabe', () => {
  it('traduit le refus du serveur en gardant le nom de la formule', () => {
    const text = entitlementNoticeText(entitlementRefusal(upgradeRequired), 'ar');
    expect(text).toContain("'free'");
    expect(text).not.toContain('Ce module');
    expect(text).toMatch(/[؀-ۿ]/);
  });

  it('traduit le dépassement de quota', () => {
    const text = entitlementNoticeText({ kind: 'quota_exceeded', tier: 'starter', message: 'Quota de la formule ...' }, 'ar');
    expect(text).toContain("'starter'");
    expect(text).toContain('حصة');
  });

  it('retombe sur le libellé local arabe sans formule connue', () => {
    const text = entitlementNoticeText({ kind: 'upgrade_required', tier: null, message: "Ce module n'est pas inclus…" }, 'ar');
    expect(text).toContain('للباقات المدفوعة');
  });
});

// Refus des routes /api/reports/* et du calculateur (audit E1).
const anonymousReports = {
  response: {
    status: 403,
    data: { detail: { error: 'upgrade_required', tier: 'anonymous', module: 'reports', message: 'Ce module est réservé aux abonnements payants.' } },
  },
};
const anonymousCalculations = {
  response: {
    status: 429,
    data: { detail: { error: 'quota_exceeded', tier: 'anonymous', module: 'calculator', quota: 10, quota_period: 'day', message: 'Limite de 10 calculs par jour sans abonnement atteinte.' } },
  },
};

describe('reportsNoticeText', () => {
  it('dit, dans la langue de l’interface, que le module est réservé aux abonnements payants', () => {
    expect(reportsNoticeText(anonymousReports, 'fr')).toContain('réservé aux abonnements payants');
    expect(reportsNoticeText(anonymousReports, 'en')).toContain('reserved for paid subscriptions');
    expect(reportsNoticeText(anonymousReports, 'ar')).toContain('وحدة الفرص');
    // Un abonné free reçoit le même avis.
    expect(reportsNoticeText(upgradeRequired, 'en')).toContain('reserved for paid subscriptions');
  });

  it('distingue le quota de rapports atteint d’une formule payante', () => {
    const quota = { response: { status: 429, data: { detail: { error: 'quota_exceeded', tier: 'starter' } } } };
    expect(reportsNoticeText(quota, 'fr')).toContain('Quota de rapports');
  });

  it('laisse les vraies pannes à leur message générique', () => {
    expect(reportsNoticeText({ response: { status: 500, data: {} } }, 'fr')).toBeNull();
    expect(reportsNoticeText({ message: 'Network Error' }, 'fr')).toBeNull();
  });

  it('renvoie vers la page des formules', () => {
    expect(PRICING_URL).toBe('/pricing.html');
  });
});

describe('anonymousCalculationNoticeText', () => {
  it('invite à souscrire, dans la langue de l’interface, avec le quota du serveur', () => {
    expect(anonymousCalculationNoticeText(anonymousCalculations, 'fr'))
      .toBe('Limite de 10 calculs par jour sans abonnement atteinte. Souscrivez un abonnement pour continuer.');
    expect(anonymousCalculationNoticeText(anonymousCalculations, 'en')).toContain('Subscribe to continue');
    expect(anonymousCalculationNoticeText(anonymousCalculations, 'ar')).toContain('اشترك');
  });

  it('ne concerne ni le quota d’un abonné ni une autre erreur', () => {
    const abonne = { response: { status: 429, data: { detail: { error: 'quota_exceeded', tier: 'free', quota: 10 } } } };
    expect(anonymousCalculationNoticeText(abonne, 'fr')).toBeNull();
    expect(anonymousCalculationNoticeText(anonymousReports, 'fr')).toBeNull();
    expect(anonymousCalculationNoticeText({ response: { status: 422, data: {} } }, 'fr')).toBeNull();
  });
});

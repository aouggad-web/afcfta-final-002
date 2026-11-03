import React from 'react';

import { pick } from '../../i18n/lang';
import { PRICING_URL } from './entitlementNotice';

/**
 * Refus d'abonnement montré à l'utilisateur (audit E1) : le texte de
 * `entitlementNotice.js` et un lien vers la page des formules.
 */
export default function SubscriptionNotice({ text, language = 'fr' }) {
  return (
    <span data-testid="subscription-notice">
      {text}{' '}
      <a href={PRICING_URL} style={{ textDecoration: 'underline', fontWeight: 600 }}>
        {pick(language, 'Voir les formules', 'See the plans', 'عرض الباقات')}
      </a>
    </span>
  );
}

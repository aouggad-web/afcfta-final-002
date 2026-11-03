/**
 * Lecture des refus d'abonnement renvoyés par la couche d'entitlements.
 *
 * Le module Outils (téléchargements tarifaires, monitoring de la collecte)
 * est réservé aux formules payantes : `routes/__init__.py` monte le routeur
 * `tariff-data` derrière `require_module_enabled("tools")`, et
 * `entitlements.py` place `"tools"` à `_DENIED` sur la formule gratuite. Un
 * visiteur non abonné reçoit donc un 403 `upgrade_required` — une réponse
 * NORMALE, pas une panne.
 *
 * Les écrans affichaient ce refus comme une erreur technique (« Erreur de
 * chargement », « Request failed with status code 403 »), ce qui se lisait
 * comme une régression du produit. On le distingue ici pour annoncer la
 * condition d'accès. Rien n'est débloqué côté client : le contrôle reste
 * entièrement côté serveur.
 */

import { pick } from '../../i18n/lang';

/** Charge utile d'un refus d'entitlement, ou `null` pour toute autre erreur. */
export function entitlementRefusal(error) {
  const response = error?.response;
  if (!response) return null;

  const detail = response.data?.detail;
  const reason = typeof detail === 'object' && detail !== null ? detail.error : null;

  if (response.status === 403 && (reason === 'upgrade_required' || reason == null)) {
    return { kind: 'upgrade_required', tier: detail?.tier ?? null, message: detail?.message ?? null };
  }
  if (response.status === 429 && reason === 'quota_exceeded') {
    return { kind: 'quota_exceeded', tier: detail?.tier ?? null, message: detail?.message ?? null };
  }
  return null;
}

/**
 * Message à afficher pour un refus. On préfère celui du serveur (il nomme la
 * formule courante) et on retombe sur un libellé local sinon.
 */
export function entitlementNoticeText(refusal, language = 'fr') {
  if (!refusal) return null;
  if (refusal.message) return refusal.message;

  if (refusal.kind === 'quota_exceeded') {
    return pick(language, "Quota de téléchargements atteint pour votre formule. Il se renouvelle à la prochaine période.", 'Download quota reached for your plan. It renews at the next period.', 'تم بلوغ حصة التنزيلات المخصّصة لباقتك. تتجدّد في الفترة القادمة.');
  }
  return pick(language, "Les données tarifaires de ce module sont réservées aux formules payantes. Passez à une formule supérieure pour y accéder.", 'This module’s tariff data is reserved for paid plans. Upgrade your plan to access it.', 'البيانات التعريفية في هذه الوحدة مخصّصة للباقات المدفوعة. قم بالترقية إلى باقة أعلى للوصول إليها.');
}

/** Page des formules, vers laquelle renvoient les refus d'abonnement. */
export const PRICING_URL = '/pricing.html';

/**
 * Refus du module Opportunités (`/api/reports/*`), réservé aux abonnements
 * payants (audit E1). Libellé local, dans la langue de l'interface : le
 * message du serveur n'existe qu'en français. `null` pour toute autre erreur.
 */
export function reportsNoticeText(error, language = 'fr') {
  const refusal = entitlementRefusal(error);
  if (!refusal) return null;
  if (refusal.kind === 'quota_exceeded') {
    return pick(language, "Quota de rapports de votre formule atteint pour aujourd'hui. Passez à une formule supérieure pour continuer.", 'Your plan’s report quota for today is reached. Upgrade your plan to continue.', 'تم بلوغ حصة التقارير اليومية لباقتك. قم بالترقية إلى باقة أعلى للمتابعة.');
  }
  return pick(language, 'Le module Opportunités est réservé aux abonnements payants. Souscrivez un abonnement pour y accéder.', 'The Opportunities module is reserved for paid subscriptions. Subscribe to access it.', 'وحدة الفرص مخصّصة للاشتراكات المدفوعة. اشترك للوصول إليها.');
}

/**
 * Calculs sans abonnement épuisés : 429 `quota_exceeded` de tier
 * « anonymous » (audit E1). Libellé local qui invite à souscrire ; `null`
 * pour toute autre erreur, y compris le quota d'un abonné.
 */
export function anonymousCalculationNoticeText(error, language = 'fr') {
  const refusal = entitlementRefusal(error);
  if (refusal?.kind !== 'quota_exceeded' || refusal.tier !== 'anonymous') return null;
  const quota = error.response.data.detail.quota;
  return pick(language, `Limite de ${quota} calculs par jour sans abonnement atteinte. Souscrivez un abonnement pour continuer.`, `Limit of ${quota} calculations per day without a subscription reached. Subscribe to continue.`, `تم بلوغ حدّ ${quota} عمليات حساب يوميًا دون اشتراك. اشترك للمتابعة.`);
}

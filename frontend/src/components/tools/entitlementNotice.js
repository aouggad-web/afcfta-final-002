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

  const isFr = language === 'fr';
  if (refusal.kind === 'quota_exceeded') {
    return isFr
      ? "Quota de téléchargements atteint pour votre formule. Il se renouvelle à la prochaine période."
      : 'Download quota reached for your plan. It renews at the next period.';
  }
  return isFr
    ? "Les données tarifaires de ce module sont réservées aux formules payantes. Passez à une formule supérieure pour y accéder."
    : 'This module’s tariff data is reserved for paid plans. Upgrade your plan to access it.';
}

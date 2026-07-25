# Ouganda — collecte (accises vérifiées ; TVA taux standard non vérifiable)

Consultation : 2026-07-25 (Africa/Algiers).

**Correction de collecte.** Une première passe sur cette branche avait enregistré `data/uganda/vat_measures.json` avec un statut `PENDING_OFFICIAL_CONSOLIDATION`, un SHA-256 `pending_collection`, et une référence légale fictive (« Value Added Tax Act 1997, Act No. 106 of 1997 »). L'Ouganda n'a pas de « VAT Act 1997 » — la loi en vigueur est la **Value Added Tax Act, Chapitre 349**, adoptée en 1996 (entrée en vigueur le 1er juillet 1996). Ce cycle remplace ces données par une collecte vérifiée sur texte primaire, et ajoute les accises.

## Ce qui a été vérifié sur texte primaire

**Accises** — Excise Duty Act, Cap. 336 (consolidée au 31 décembre 2023, la version la plus récente disponible) :
- Imposition : Section 3(1), renvoyant au barème du Schedule 2.
- 5 lignes représentatives transcrites (cigarettes soft cap locales/importées, bière de malt, spiritueux à base de matières premières importées, boissons non alcoolisées hors jus), avec référence exacte au Schedule 2.

**TVA — mécanisme, pas le taux** — Value Added Tax Act, Cap. 349 :
- Taux zéro sur les exportations : Section 24(4) et Third Schedule, clause 1(a).

## Ce qui n'a PAS été vérifié — et pourquoi

**Le taux standard de la TVA n'est PAS enregistré.** L'article 24(3) de la loi renvoie le taux à « the rate of tax shall be as specified in section 78(2) », et l'article 78(2) délègue la fixation du taux à un arrêté ministériel (« statutory order »), soumis à confirmation parlementaire. Le pourcentage lui-même n'apparaît donc **nulle part dans le texte de loi obtenu** — ni dans la copie `media.ulii.org` (consolidation au 31 décembre 2000), ni dans le miroir Laws.Africa republié par `tradebarriers.org` (même consolidation de base). La page `ulii.org/akn/ug/act/statute/1996/8/eng@2023-12-31` — qui indique dans les résultats de recherche couvrir les amendements jusqu'à 2023 — est protégée par un challenge Cloudflare qui bloque l'accès automatisé et WebFetch (HTTP 403 « Just a moment... »).

L'Uganda Revenue Authority (URA) rapporte publiquement un taux de 18% sur son site, mais sans citer l'arrêté ministériel précis (numéro, date). Conformément à la règle de sincérité (précédent Gabon, PR #311) : un taux répété par l'autorité fiscale elle-même mais sans lecture directe de l'instrument légal qui le fixe n'est pas enregistré comme vérifié — `VAT-RATE-STANDARD` est absent de `vat_measures.json`.

**Schedule 2 non exhaustif** : couvre bien plus de catégories (vins, autres spiritueux, carburants, mobile money, immatriculation de véhicules, sucre…) que les 5 lignes transcrites ce cycle.

## Ce qui reste à collecter

- L'arrêté ministériel (statutory order) fixant le taux TVA actuel, avec numéro et date.
- Consolidation post-2023-12-31 de la VAT Act (contourner ou re-tenter le challenge Cloudflare de ulii.org).
- Finance Act 2026, Customs Tariff Guide URA : URLs localisées lors d'une passe antérieure, non re-vérifiées ce cycle.

## État de l'enregistrement

Juridiction UGA : **non** enregistrée dans `SUPPORTED_JURISDICTIONS` — taux standard TVA non vérifié, accises non exhaustives, pas de Finance Act, pas de TEC. ZLECAf : **pas** d'offre nationale encore enregistrée dans `NATIONAL_OFFER_REGISTRY`.

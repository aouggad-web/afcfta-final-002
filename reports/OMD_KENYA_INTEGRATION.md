# Intégration OMD — overrides EAC/Kenya

**État au 24 juillet 2026 — intégration fonctionnelle, classement et couverture juridique encore partiels.**

## Intégration Git

- Branche : `feat/kenya-overrides-omd-integration`.
- Sauvegarde préalable Kenya/EAC : `6cd4c255`.
- Commit OMD source : `9fdb130ea790f15070db5f5d28e4ce34b6dcea37`.
- Cherry-pick local ciblé : `f9f8cc1f`.
- Conflits : aucun.
- Aucun `pull`, `reset --hard`, force push ou suppression de modification locale.
- Les fichiers locaux ambigus sont restés hors index Git.

L’audit des 398 commits séparant l’ancien HEAD du commit OMD n’a révélé que
des changements indépendants pour cette fonctionnalité. Le commit OMD était
autonome dans l’architecture déjà présente ; aucune chaîne additionnelle de
cherry-picks n’a été nécessaire.

## Source canonique et provenance

La seule source de données est `backend/data/omd_hs_index.json`, chargée par
`backend/services/omd_hs_index_service.py`. Aucun second corpus et aucune copie
du JSON n’ont été créés.

| Métadonnée | Valeur |
|---|---|
| Version SH | HS2022 |
| Édition | 7 |
| Entrées | 6 344 |
| SHA-256 | `c84ea861a183b0c25a16ae343f7f4c3e04fac439822ca62930e09355175f2c87` |
| Date d’acquisition | inconnue (`null`) |
| URL source | inconnue (`null`) |
| Licence | `TO_BE_VERIFIED` |
| Redistribution | interdite tant que non vérifiée |

La route `GET /api/hs-codes/product-index` conserve son contrat de recherche,
ajoute les métadonnées de provenance et n’expose pas d’export du corpus.

## Adaptateur et product mapping

`backend/services/wco_index_adapter.py` fournit
`search_wco_index(query, hs_version="HS2022", language=None, limit=20)`. Il
délègue au service existant et retourne uniquement des correspondances et des
candidats explicitement présents dans l’index, avec niveau et score textuel.
Une position SH4 n’est jamais développée artificiellement en SH6.

`engine.product_mapping.WCOIndexCandidateMapper` reçoit l’interface par
injection. Il peut renseigner `hs4_candidates`, `hs6_candidates`,
`index_terms_used`, `wco_index_matches` et `confidence_score`, mais laisse
toujours `selected_hs6` vide et `requires_human_review` à vrai pour ses
propositions.

Les six descriptions `END_USE_MEASURE` des gazettes restent sans candidat en
production : l’index n’est pas interrogé sur une catégorie générique comme
« various inputs ». Une liste détaillée issue d’une autorisation peut produire
des candidats, mais jamais un classement automatique.

| Indicateur d’intégration OMD | Nombre |
|---|---:|
| Descriptions END_USE extraites des gazettes | 6 |
| Candidats ajoutés sans liste détaillée autorisée | 0 |
| SH6 validés automatiquement par l’OMD | 0 |
| Cas END_USE conservés en revue humaine | 6 |

La file Kenya complète contient par ailleurs 776 mappings juridiques déjà
validés ou en revue : 412 `DIRECT_HS`, 362 `LEGAL_DESCRIPTION` et 2
`MAPPED_HS`; 364 enregistrements demandent une revue humaine. Ils n’ont pas été
refondus par cette intégration.

## Remissions conditionnelles et calculateur

Les statuts `ELIGIBLE_VERIFIED`, `NOT_ELIGIBLE`, `ELIGIBILITY_UNKNOWN` et
`AUTHORIZATION_REQUIRED` sont portés par le contexte d’override.

- `NOT_ELIGIBLE` conserve le CET normal.
- Une éligibilité inconnue ou une autorisation incomplète n’applique pas la
  remission et impose `VERIFIED_PARTIAL`.
- `ELIGIBLE_VERIFIED` exige une référence, une période couvrant la date du
  calcul et la ligne tarifaire exacte dans la liste autorisée.
- Une autorisation expirée ou un code absent n’applique pas la remission.
- Les conditions d’origine et de quantité restent vérifiées séparément.

Le calculateur pose la question demandée. Une réponse « Oui » ouvre les champs
référence, période, lignes tarifaires exactes et marchandises détaillées. La
trace affiche le CET de base, le taux applicable, l’override, le total vérifié,
le statut d’éligibilité et l’avertissement de résultat partiel.

## Couverture des gazettes

Le registre contient quatre fiches : trois gazettes officielles téléchargées
et hachées, plus une fiche globale `SOURCE_PENDING`. Les extractions actuelles
représentent 26 lignes tarifaires et 17 mesures structurées (13 remissions et
4 stays). Cette couverture reste déclarée partielle.

Les blocages juridiques principaux sont : corpus exhaustif des gazettes EAC et
corrigenda, EACCMA 2025 complet, stays/modifications CET ponctuels, listes de
bénéficiaires et allocations, autorisations détaillées, exemptions et
dérogations nationales Kenya, ainsi que les RGI et notes légales nécessaires
au classement. Ces lacunes empêchent `VERIFIED_COMPLETE` à l’échelle du tarif.

## Validations

| Suite | Résultat |
|---|---:|
| Backend OMD, adaptateur et route calcul Kenya | 17 réussis |
| Mappings et overrides juridiques | 29 réussis |
| Composants React OMD et autorisation | 6 réussis |
| Total ciblé | 52 réussis, 0 échec |
| Build Vite de production | réussi |

Le build signale seulement un bundle supérieur au seuil indicatif de 500 kB.
Les tests Python émettent des avertissements de dépendances existants
(dépréciation Pydantic, LibreSSL et types SWIG), sans échec fonctionnel.

## Fichiers propres à l’intégration

- Métadonnées et services :
  `backend/data/omd_hs_index.metadata.json`,
  `backend/services/wco_index_adapter.py`,
  `backend/services/kenya_legal_calculation_service.py`,
  `backend/services/omd_hs_index_service.py`.
- Routes : `backend/routes/hs_codes.py`,
  `backend/routes/authentic_tariffs.py`.
- Moteur : `engine/product_mapping.py`, `engine/legal_override_engine.py`,
  `engine/kenya_customs_calculation.py`, `engine/schemas/legal_override.py`.
- Interface : `frontend/src/components/calculator/CalculatorTab.jsx`,
  `frontend/src/components/calculator/KenyaRemissionAuthorization.jsx`.
- Tests : `backend/tests/test_wco_index_adapter.py`,
  `backend/tests/test_kenya_authentic_route.py`,
  `engine/tests/test_product_mapping.py`,
  `engine/tests/test_kenya_legal_overrides.py`,
  `frontend/src/components/calculator/KenyaRemissionAuthorization.test.jsx`.
- Rapports : `reports/OMD_INDEX_TRACE.md`, ce rapport.

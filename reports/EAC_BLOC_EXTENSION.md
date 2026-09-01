# Extension EAC hors Kenya — Tanzanie, Ouganda, Rwanda, Burundi

**État au 25 juillet 2026 — extraction partielle, aucune couverture complète.**

## Source

`data/sources/eac/official/EAC_Vol_AT_1_No_16_2026-06-30.pdf` (déjà archivée et hachée
lors de la collecte Kenya, SHA-256 `555b8fdd7cc817ae5f729762913c5f8205e503a28170bad86a8a0f66e4c93907`,
vérifié à nouveau lors de cette extraction). Legal Notice EAC/160/2026,
« Table I: Approved Measures on Import Duty Rates in the EAC CET » — 325 lignes,
couvrant l'ensemble des États partenaires de l'EAC (Kenya, Tanzanie, Ouganda,
Rwanda, Burundi, RDC, Soudan du Sud), pas seulement le Kenya.

Aucun nouveau téléchargement n'a été nécessaire : le PDF était déjà présent et
haché dans le dépôt pour la collecte Kenya (PR #304/#307), mais son extraction
n'avait porté que sur les 15 lignes concernant le Kenya. Le texte intégral,
identique pour toutes les juridictions, était donc disponible pour extraction
immédiate — c'est le lot de données le moins coûteux disponible pour étendre la
couche de vérification au-delà du Kenya.

## Couverture de cette extraction

| Juridiction | Mesures extraites | Lignes Table I couvertes |
|---|---:|---|
| Tanzanie (TZA) | 6 | 3, 4, 5, 6, 7, 8 |
| Ouganda (UGA) | 2 | 8, 11 |
| Rwanda (RWA) | 3 | 3, 9, 10 |
| Burundi (BDI) | 1 | 320 |
| **Total nouveau** | **12** | sur 325 lignes de la Table I |

Critère de sélection : lignes disposant d'un ou plusieurs codes SH explicites,
non ambiguës à la lecture (décision, produit et pays clairement identifiables
sans interprétation). Les lignes 1 et 2 (franchise procédurale liée à un cadre
opérationnel spécial avec le gouvernement, sans code SH) ont été délibérément
exclues : elles ne sont pas des dérogations tarifaires par produit et sortent
du périmètre du moteur.

## Lacunes assumées

- **~296 lignes restantes de la Table I** (lignes 12-319, 321-325) ne sont pas
  extraites. La majorité concerne le Kenya (déjà partiellement couvert par
  ailleurs) ou nécessite une lecture plus attentive de décisions à
  sous-clauses multiples (a)/(b)/(c) par pays.
- **Table II** (« Approved Measures … for the Republic of Uganda ») et
  **Table III** (« The Republic of Kenya to stay … ») du même gazette ne sont
  pas extraites.
- **EAC Gazette Vol. AT 1 No. 19** (2025-06-30) et **No. 26** (2025-08-14),
  également archivées, n'ont pas été relues pour du contenu non-Kenya dans le
  cadre de cette extraction — seule la gazette la plus récente (No. 16,
  priorité `CURRENT_CRITICAL`) a été traitée.
- Plusieurs mesures (électrique Rwanda, gants chirurgicaux Ouganda, fil
  machine Burundi) ne précisent pas le taux CET de base dans le texte du
  gazette lui-même (formulation « stay the application of the EAC CET rate »
  sans pourcentage) : `base_rate` est laissé `null` plutôt que déduit d'une
  autre source, avec une note explicite dans `condition_text`.
- Aucune donnée fiscale nationale (TVA, accises, prélèvements) n'est ajoutée
  par cette extraction : elle porte exclusivement sur les dérogations au CET
  commun EAC. La collecte des couches fiscales nationales (TVA/accises/
  formalités) pour ces pays reste à faire, suivant la méthode Kenya
  (sources officielles datées, archivées et hachées).

## Vérifications effectuées

- Les 12 nouvelles mesures se chargent sans erreur contre le schéma
  `LegalOverrideMeasure` (pydantic).
- Isolation par juridiction vérifiée : une mesure `jurisdiction: "TZA"`
  n'affecte jamais un calcul `KEN` sur le même code SH, et réciproquement
  (`engine/tests/test_eac_bloc_legal_overrides.py`).
- Mesure conditionnelle (franchise carte à puce tanzanienne réservée à
  l'Autorité nationale d'identification) : ne s'applique pas sans le fait
  de bénéficiaire, conformément à la discipline déjà en vigueur pour les
  remises conditionnelles kényanes.
- Taux mixte (tissu de coton, Tanzanie — % ou USD/mètre) : le taux plancher
  en pourcentage est appliqué par le résolveur, la formule complète reste
  disponible sur la mesure (`rate_unit`) sans conversion silencieuse.
- Non-régression : les 17 mesures Kenya existantes et les 37 tests
  Kenya/WCO passent à l'identique après extension.

13 nouveaux tests (`engine/tests/test_eac_bloc_legal_overrides.py`).

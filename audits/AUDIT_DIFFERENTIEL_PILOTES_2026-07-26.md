# Livrable A — Audit différentiel, 6 pays pilotes ZLECAf

**Commit HEAD audité :** `1be67b6da14e0a03c731ab3d82b23b4180107bb6` (`main`, "Merge pull request #314")
**Date de l'audit :** 2026-07-26
**Arbre de travail :** propre (`git status --porcelain` vide au moment de l'audit)
**Méthode :** lecture seule. Aucune donnée, aucun taux, aucun fichier n'a été modifié pendant cette phase.
**Portée :** Algérie (DZA), Tunisie (TUN), Maroc (MAR), Égypte (EGY), Afrique du Sud (ZAF), Kenya (KEN).

---

## 1. Constat transversal préalable — pourquoi les chiffres "de référence" ne se retrouvent pas partout

Pour chaque pays pilote, **au moins trois générations de fichiers coexistent** dans le dépôt :

1. `engine/output/{ISO3}_summary.json` — **systématiquement obsolète et faux** sur les 6 pays. Généré le 2026-03-01/06, il ne correspond à aucun chiffre de référence connu (ex. DZA : 5831 lignes au lieu de 17061 ; ZAF : 16568 enregistrements au lieu de 8589). Il dérive d'un gabarit synthétique appliqué mécaniquement à plusieurs pays (confirmé pour MAR : codes HS6 identiques à ceux du Cameroun). **Ne doit plus jamais être utilisé comme source de vérité ni comme référence de comparaison.**
2. `backend/data/crawled/QUARANTINE_SYNTHETIC/{ISO3}_tariffs.json` — jeux de données synthétiques **déjà détectés et mis en quarantaine** par un mécanisme existant (confirmé pour TUN, MAR, ZAF). Bon signe de discipline antérieure, mais preuve que la contamination synthétique a été réelle en production à un moment donné.
3. Le fichier réellement chargé par le backend au runtime — variable selon le pays et la route (voir tableau §2).

**Aucun de ces trois niveaux n'est nommé ou documenté de façon à distinguer clairement "canonique publié" de "brouillon périmé" ou "rejeté".** C'est une dette de gouvernance des données à traiter avant toute nouvelle collecte.

---

## 2. Comparaison chiffres de référence vs fichier réellement servi

| Pays | Fichier réellement chargé au runtime | Lignes / SH6 (référence) | Vérifié exact ? | Provenance déclarée |
|---|---|---|---|---|
| **DZA** | `backend/data/crawled/DZA_tariffs.json` | 17061 sub_positions (SH6 non revérifié séparément) | Partiel — total lignes confirmé, DD présents/manquants **non recalculés** | **conformepro.dz** — agrégateur commercial, PAS le portail douane.gov.dz directement |
| **TUN** | `backend/data/tariffs/TUN_tariffs.json` (= `backend/data/TUN_tariffs.json`, copie identique) | 17512 / 5611 | Oui, exact | douane.gov.tn/tarifweb2025 — **officiel** |
| **MAR** | `backend/data/MAR_tariffs.json` (= `backend/data/tariffs/MAR_tariffs.json`) | 13114 / 5610 ; 12972 DD présents / 142 manquants | Oui, exact (recalcul programmatique) | douane.gov.ma/adil (ADII) — **officiel** |
| **EGY** | `backend/data/EGY_tariffs.json` (= `backend/data/tariffs/EGY_tariffs.json`) | 8746 / 5541 | Oui, exact | customs.gov.eg — **officiel** |
| **ZAF** | `backend/data/ZAF_tariffs.json` | 8589 / 5619 | Oui, exact | sars.gov.za, Schedule 1 Part 1 — **officiel** |
| **KEN** | `backend/data/KEN_tariffs.json` (DD/CET) + `data/kenya/*.json` (TVA/accises/exonérations, PR #307) | 5984 / 5604 ; 5893 DD présents / 91 manquants | Oui, exact (recalcul programmatique) | DD : chaîne texte "EAC CET 2022", **aucun SHA-256** — TVA/accises : archivés et hachés (`data/sources/kenya/official/`) |

**Point critique DZA :** contrairement aux 5 autres pays pilotes, la source déclarée du fichier de production n'est pas le portail douanier officiel algérien mais un agrégateur commercial (conformepro.dz). Selon la hiérarchie des sources du prompt maître (§5), ceci correspond au mieux à un niveau 3 ("piste de recherche"), pas à un niveau 1. **DZA ne peut pas être qualifié de source primaire en l'état.**

---

## 3. Données manquantes par pays

| Pays | Lacune documentée |
|---|---|
| DZA | Aucune preuve documentaire structurée (pas de `sha256`, `source_id`, `effective_from`) sur le fichier de production `crawled/DZA_tariffs.json` — seule une URL par ligne (`source_url` conformepro.dz) est présente. Le module `zlecaf_schedule_dza.py` (démantèlement par liste A/B/C) référence la circulaire DGD n°482/DGD/SP/D.042/24 mais **sans fichier source archivé ni SHA-256** (dette déjà identifiée dans une session antérieure, toujours ouverte). |
| TUN | Aucune offre tarifaire ZLECAf nationale. Pas de `sha256` sur le fichier de production (le champ `reliability: "A"` est une auto-déclaration, non adossée à un hash vérifiable). |
| MAR | Idem TUN : aucune offre ZLECAf nationale, pas de SHA-256 sur `MAR_tariffs.json`. |
| EGY | Idem : aucune offre ZLECAf nationale, pas de SHA-256. Le taux préférentiel ZLECAf provient de notes tarifaires internes en arabe (préfixe `ر`) intégrées au crawl, non d'un texte juridique archivé séparément. |
| ZAF | Aucun calendrier de démantèlement par produit (confirmé explicitement dans le code même : `zlecaf_schedule_zaf.py` ne fournit qu'un statut d'éligibilité). Les 4328 lignes "simulables" appliquent le taux ZLECAf déjà présent sur la ligne HS6 dès que le partenaire figure dans une liste statique `ACTIVE_PARTNERS_ZAF` (14 pays, codée en dur, sourcée seulement par une newsletter dtic/SARS de mars 2026 — pas un texte réglementaire officiel). Aucun SHA-256. |
| KEN | Le droit de douane (DD/CET) — 5984 lignes, y compris les 5893 "présentes" — n'a **aucune** preuve documentaire structurée, malgré le statut de juridiction "gold standard" du dépôt. Seules TVA/accises/exonérations sont vérifiées au niveau attendu par le prompt maître. `zlecaf_rate: 0.0` **uniforme** sur les 5604 lignes SH6 — valeur constante, non variable, sans article de loi ni date d'effet : c'est le pattern explicitement interdit en §4 du prompt maître ("transformer une donnée absente en 0 %"). |

---

## 4. Incohérences détectées entre fichiers / backend / frontend

1. **Bug fonctionnel confirmé pour ZAF** — `backend/services/authentic_tariff_service.py::load_crawled_position_index()` attend les clés `"sub_positions"` / `"hs_code"`, mais `backend/data/crawled/ZAF_tariffs.json` utilise `"positions"` / `"code_raw"` / `"code_clean"`. **L'index par sous-position est silencieusement vide pour l'Afrique du Sud** — le calcul retombe sur le fichier agrégé HS6 sans qu'aucune erreur ne soit levée. Aucun signal utilisateur ni log d'échec identifié à ce stade.
2. **Copies dupliquées byte-identiques** de la même donnée canonique pour TUN, MAR, EGY (`backend/data/{ISO3}_tariffs.json` et `backend/data/tariffs/{ISO3}_tariffs.json`), maintenues par deux services de chargement différents (`tariff_data_service.py` lit `backend/data/tariffs/`, `authentic_tariff_service.py` lit `backend/data/`). Risque de désynchronisation à la prochaine mise à jour d'un seul des deux emplacements.
3. **Au moins 7 routes/moteurs de calcul concurrents** confirmés dans `backend/routes/` : `calculator.py`, `enhanced_calculator.py`, `authentic_tariffs.py`, `postgres_tariffs.py`, `regional_calculator.py`, `tariffs.py`, `tariffs_calculation.py`. Le frontend (`CalculatorTab.jsx`) appelle effectivement plusieurs endpoints différents selon la branche runtime : `/tariff-data/`, `/authentic-tariffs/`, `/postgres-tariffs/`, `/calculate-tariff`, `/tariffs/sub-positions/`, `/hs6-tariffs/`. Ceci confirme directement le problème que le §15 du prompt maître demande de résoudre par un moteur canonique unique.
4. **Le registre `NATIONAL_OFFER_REGISTRY`** (`backend/etl/afcfta_national_offers.py`) ne référence que `DZA`. Pourtant ZAF et KEN appliquent tous deux des taux étiquetés "ZLECAf" par des chemins de code parallèles qui ne passent pas par ce registre (raccourci de partenaire actif pour ZAF, valeur constante 0.0 pour KEN). **Le garde-fou d'honnêteté existe mais n'est pas le seul chemin capable de produire un résultat étiqueté ZLECAf** — c'est une brèche systémique par rapport à la logique cumulative exigée en §12 du prompt maître (signature ≠ ratification ≠ mise en œuvre ≠ réciprocité ≠ éligibilité produit ≠ origine acquise).
5. Deux crawlers concurrents existent pour l'Égypte (`engine/scripts/crawl_egy_egyptariffs.py`, officiel, utilisé ; `backend/crawlers/countries/egypt_tariffs_scraper.py`, agrégateur egyptariffs.com, non utilisé en production) — mort-vivant à nettoyer ou documenter comme désactivé.
6. Version SH non tracée de façon fiable : les convertisseurs (`engine/converters/{tun,mar,egy}_converter.py`) codent en dur `hs_version="HS2022"` sans validation contre une métadonnée de version présente dans la source brute.

---

## 5. Sources officielles déjà archivées (avec preuve SHA-256 vérifiable)

**Seul le Kenya dispose d'archives conformes au §6 du prompt maître**, et uniquement pour sa couche TVA/accises/exonérations :
- `data/sources/kenya/official/eac-cet-2022-updated-june-2025.pdf` — SHA-256 vérifié contre `inventory.csv`.
- Ensemble de textes archivés référencés dans `data/kenya/legal_sources.json` (14 occurrences de `sha256`), chaque enregistrement TVA/accise portant `source_id`, `legal_reference`, `effective_from/to`, `verification_status`.

**Aucun autre pays pilote (DZA, TUN, MAR, EGY, ZAF) ne dispose d'une seule archive primaire hachée SHA-256** couvrant son tarif douanier de production actuel. Les statuts `"data_status": "VERIFIED"` / `"reliability": "A"` présents dans plusieurs fichiers (TUN, MAR) sont des **auto-déclarations du pipeline de crawl**, non adossées à un fichier archivé et un checksum vérifiable au sens strict du prompt maître — elles ne doivent donc pas être présentées telles quelles comme grade `A` sans réserve.

---

## 6. Sources encore nécessaires (priorité immédiate)

Par pays, dans l'ordre où elles bloquent le calcul complet :

| Pays | Source prioritaire à archiver |
|---|---|
| DZA | Texte réglementaire douanier officiel (Journal Officiel / douane.gov.dz) remplaçant ou confirmant conformepro.dz comme source de production ; circulaire DGD 482/2024 (démantèlement ZLECAf) — archivage + SHA-256. |
| TUN | Confirmation/archivage haché du tarif douane.gov.tn déjà identifié comme source (le portail est déjà correct, il manque l'archive probante). |
| MAR | Idem pour douane.gov.ma/adil. |
| EGY | Idem pour customs.gov.eg. |
| ZAF | Corriger d'abord le bug d'indexation (§4.1) avant toute nouvelle collecte ; puis rechercher un calendrier de démantèlement ZLECAf par produit (SARS/dtic) remplaçant la liste statique `ACTIVE_PARTNERS_ZAF` non sourcée juridiquement. |
| KEN | Texte réglementaire du CET EAC 2022 avec portée DD ligne par ligne (au-delà du texte déjà archivé qui couvre la structure générale) ; toute offre ZLECAf nationale kényane réelle, si elle existe, pour remplacer le `zlecaf_rate: 0.0` uniforme actuel. |

---

## 7. Lignes actuellement calculables sans nouvelle collecte

Au sens strict du prompt maître (taux avec source identifiable + date d'effet, zéro estimation) :

- **KEN** : 0 ligne DD/CET pleinement conforme (aucune n'a de SHA-256/source_id) ; TVA/accises/exonérations conformes pour leur périmètre propre (hors DD).
- **DZA, TUN, MAR, EGY, ZAF** : 0 ligne conforme au niveau `DOCUMENTED`/grade `A` tel que défini strictement au §7 — toutes reposent sur une auto-déclaration de pipeline, pas sur une archive SHA-256 vérifiable à ce stade de l'audit.

**Aucun pays pilote n'atteint aujourd'hui les critères de publication du §17** ("100 % des taux utilisés ont une source identifiable [...] zéro taux estimé [...] zéro préférence sans preuve de mise en œuvre"). C'est le point de départ réel, pas une régression : le dépôt contient des données plausibles et globalement correctes en ordre de grandeur, mais la couche de preuve documentaire au niveau exigé par ce prompt maître reste à construire pour les 6 pays, y compris Kenya sur son volet DD.

---

## 8. Obstacles à la jonction ZLECAf (transversal)

1. Le registre central des offres nationales (`NATIONAL_OFFER_REGISTRY`) est contournable par des chemins de code par pays (ZAF, KEN) — à corriger avant toute activation supplémentaire, sinon toute nouvelle "offre nationale" ajoutée au registre coexistera avec des chemins parallèles non gatés.
2. Aucun des 6 pays pilotes n'a de preuve de réciprocité structurée et sourcée (seule une liste de partenaires actifs codée en dur existe pour DZA et ZAF, sans texte juridique archivé pour la version ZAF).
3. Aucune règle d'origine spécifique par produit n'a été localisée dans cet audit (recherche non exhaustive à ce stade — à approfondir en Phase 2).
4. La distinction "offre nationale officielle" vs "canevas générique SH2" (niveau 1 vs niveau 2, cf. plan antérieur du dépôt) n'existe dans le code que pour DZA (`zlecaf_schedule_dza.py`) et partiellement ZAF (statut d'éligibilité seul, pas de calendrier) — absente pour TUN/MAR/EGY/KEN.

---

## 9. Plan d'intégration séquencé proposé

Cette séquence n'implique aucune modification de taux avant validation explicite à chaque étape.

1. **Assainissement (aucune collecte nouvelle)** — marquer ou supprimer `engine/output/{ISO3}_summary.json` (6 fichiers obsolètes confirmés) ; corriger le bug d'indexation ZAF (§4.1) ; documenter explicitement quel fichier est "canonique" par pays pour éviter la coexistence root/`tariffs/` non synchronisée.
2. **Kenya — combler la dette DD** : appliquer au droit de douane EAC/CET la même discipline que la couche TVA/accises déjà conforme (archive + SHA-256 + `source_id` + `effective_from`), puisque c'est la juridiction la plus proche de la conformité complète.
3. **DZA — requalifier la source de production** : rechercher et archiver une source primaire (Journal Officiel / douane.gov.dz) pour remplacer ou corroborer conformepro.dz ; combler la dette SHA-256 de la circulaire DGD 482/2024 déjà identifiée.
4. **TUN / MAR / EGY** — les portails sources sont déjà corrects (officiels) ; la tâche restante est l'archivage probant (téléchargement, SHA-256, `inventory.csv`) plutôt qu'une nouvelle recherche de source.
5. **ZAF** — après correction du bug d'indexation, rechercher un calendrier ZLECAf par produit sourcé juridiquement pour remplacer le raccourci `ACTIVE_PARTNERS_ZAF`.
6. **Moteur canonique (§15 du prompt maître)** — chantier séparé et plus lourd, à ne pas mener en parallèle de la collecte de données par pays (cohérent avec le principe déjà appliqué dans ce dépôt lors des lots UEMOA/EAC/CEMAC précédents : la collecte de données précède la généralisation du moteur).

---

## 10. Statut de recommandation

Tous les pays pilotes restent, à l'issue de cet audit, en statut **`INFORMATIVE_PARTIAL`** au sens du prompt maître. Aucun changement de statut n'est proposé sans preuve nouvelle. Ce document est un audit, pas une collecte : aucune source n'a été téléchargée ni archivée à ce stade.

**En attente de validation avant de poursuivre pays par pays**, conformément à l'instruction finale du prompt maître (§20).

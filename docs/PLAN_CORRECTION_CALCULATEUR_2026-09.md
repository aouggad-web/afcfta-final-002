# Plan de réalisation — corrections du calculateur (54 pays)

**Entrée :** audit du 13 septembre 2026 sur `main@3a16a35`.
**Objet :** transformer les constats de l'audit en travaux ordonnés, mesurables et testables.

## 1. Ce que vaut l'audit

### Constats revérifiés indépendamment sur le dépôt

| Constat de l'audit | Vérification | Résultat |
|---|---|---|
| EGY `0207110000` : 30 % au crawl, 19,5 % au moteur prioritaire | lecture directe des deux fichiers | **Confirmé.** `backend/data/EGY_tariffs.json` porte `dd: 19.5` sur la sous-position et `dd_rate: 19.5` sur le parent HS6 ; `backend/data/crawled/EGY_tariffs.json` porte `taxes.ID.rate = 30.0`. Le moteur prioritaire lit le DD du canonique et ne superpose du crawl que certaines taxes |
| `source_hash` vide sur les sceaux | lecture du sceau EGY | **Confirmé.** `_integrity_seal.source_hash = null`, `content_hash` présent |
| Couche normalisée potentiellement périmée | `start.sh:28-33` | **Confirmé et aggravé.** `crawled_normalized/` est absent du clone (0 fichier, non versionné, ~2 Go) et n'est régénéré que si le dossier est vide. Aucune comparaison d'empreinte |
| Intégrité non imposée au chargement | recherche de `verify_crawled_file` dans les services | **Confirmé.** Aucun chargeur ne l'appelle ; seul `normalize_crawled.py` recopie le sceau |
| Deux circuits concurrents côté interface | `CalculatorTab.jsx:415` puis `:665` | **Confirmé.** `try` GET `/authentic-tariffs/calculate/...`, `catch` silencieux, puis POST `/calculate-tariff` |
| `null` converti en 0 | `authentic_tariff_service.py` | **Confirmé.** ~20 occurrences de `or 0`, dont `dd_rate`/`vat_rate` aux lignes 1639 et 1696 |

L'audit est fiable : ses affirmations sont reproductibles sur les données versionnées, et il distingue correctement ce qui est démontré de ce qui reste indéterminé. Ses réserves de portée (pas d'accès à PostgreSQL de production, pas de revalidation juridique) sont justes et doivent être reprises telles quelles.

### Ce que je corrige dans sa lecture

1. **La hiérarchie des causes est inversée.** L'audit présente « deux moteurs » et « deux jeux de fichiers » comme deux défauts de même rang. Le générateur de bugs est la **résolution de données** : deux sources (`data/ISO_tariffs.json` canonique, `data/crawled/ISO_tariffs.json`) sans règle de préséance explicite, plus une troisième dérivée (`crawled_normalized/`). Les deux moteurs ne créent pas les écarts, ils les rendent visibles. Conséquence de plan : on unifie la résolution **avant** les moteurs, pas l'inverse.

2. **`P0-1` tel qu'écrit est un big-bang.** « Définir un fournisseur de données et un moteur de calcul communs aux deux API » comme premier travail, c'est réécrire 2 247 + 1 137 lignes sans filet de mesure. Il faut d'abord un **harnais différentiel** qui chiffre l'écart entre les deux chemins sur les 54 pays ; il sert ensuite de critère d'acceptation à chaque étape et de garde anti-régression.

3. **Trois travaux manquent au §5 de l'audit.**
   - *Politique d'indisponibilité.* L'audit exige « aucun DD absent transformé en 0 » sans dire ce que l'interface affiche à la place. C'est une décision produit à trancher avant le code (`UNAVAILABLE` explicite, calcul partiel, ou refus de la ligne).
   - *Repli silencieux de l'interface.* Le `catch` de `CalculatorTab.jsx:415` masque les pannes du chemin prioritaire. Tant qu'il existe, aucune convergence backend n'est observable côté utilisateur.
   - *Corpus de référence figé.* Sans jeu de cas attendus versionné, « mêmes montants sur les deux chemins » n'est pas vérifiable en intégration continue.

4. **Une contrainte physique à respecter.** `P1-2` (« comparaison de hash au chargement ») appliquée naïvement à ~2 Go coûterait des dizaines de secondes au démarrage. La vérification doit porter sur un **manifeste** (empreintes des sources + empreinte de la dérivation) et sur une vérification paresseuse par fichier au premier accès, mise en cache.

5. **À sortir du périmètre logiciel.** L'exhaustivité juridique des 54 pays (`P1-4`, revalidation des taux auprès des administrations) est un programme de collecte de données, pas un chantier de code. Il doit avancer en parallèle, avec son propre calendrier, sinon il bloquera indéfiniment les corrections de calcul qui, elles, sont livrables en semaines.

## 2. Principe directeur

Un taux servi doit être **traçable jusqu'à un fichier, une version et une empreinte**, ou déclaré indisponible. Aucune valeur ne doit être fabriquée par défaut — ni un 0, ni un taux de chapitre, ni une base légale attribuée par groupe régional.

## 3. Phases

### Phase 0 — Mesurer avant de corriger (aucun changement de comportement)

| # | Travail | Livrable | Acceptation |
|---|---|---|---|
| 0.1 | Harnais différentiel des deux chemins | `scripts/diff_engines.py` : pour un échantillon déterministe de codes × 54 pays, appelle le service prioritaire et la fonction du POST, PostgreSQL désactivé, CIF fixe | Produit un rapport JSON classant chaque code en `IDENTIQUE`, `ECART_TAUX`, `ECART_MONTANT`, `ABSENT_D_UN_CHEMIN`, `EXCEPTION` |
| 0.2 | Corpus de référence figé | `backend/tests/fixtures/calculator_golden.json` : les 10 cas du §2 de l'audit (EGY 0207110000, TUN 90031100003, DZA 2201101100 et 1001110000, ETH 01013000000, GHA 7612901000 et 270900, MUS 010129, ZAF 020830, SOM 01012100) + valeur source attendue et provenance | Un test échoue tant que le cas n'est pas corrigé ; le fichier cite le fichier et la clé d'où vient la valeur attendue |
| 0.3 | Décision produit sur l'indisponibilité | note d'une page annexée à ce plan | Trois états arrêtés et nommés : `DOCUMENTE`, `INDISPONIBLE`, `NON_APPLICABLE_DOCUMENTE` ; comportement d'affichage défini pour chacun |

> Sans 0.1 et 0.2, les phases suivantes ne sont pas vérifiables. C'est le préalable, pas une formalité.

### Phase 1 — Résolution de données unique (cause racine)

| # | Travail | Fichiers | Acceptation |
|---|---|---|---|
| 1.1 | Service de résolution de ligne unique | nouveau `backend/services/tariff_resolution_service.py` | Une seule fonction `resolve_line(iso3, code)` retourne un objet portant : ligne retenue, **niveau** (national / HS6 parent / chapitre), **source** (`postgres` / `crawled` / `canonical`), fichier, version, empreinte, et la liste des champs indisponibles |
| 1.2 | Préséance explicite et documentée | idem + `tariff_provider_service.py` | Ordre unique et testé : PostgreSQL → crawl (le plus récent) → canonique. Le DD du crawl **prime** sur le DD canonique quand les deux existent (cas EGY) ; aucune remontée au parent HS6 sans marquage explicite du niveau |
| 1.3 | Codes nationaux sans parent canonique | idem | Les 111 DZA, 113 TUN, 72 EGY, 4 233 ETH sont résolus depuis le crawl seul. Plus aucun « ligne introuvable » pour un code présent dans une source servable |
| 1.4 | Préservation des enfants nationaux Ghana | `scripts/normalize_crawled.py` | Les 6 129 codes nationaux GHA restent adressables après normalisation ; `7612901000` ne renvoie plus 422 |
| 1.5 | Branchement Somalie | `tariff_resolution_service.py` | `SOM 01012100` donne le même DD sur les deux chemins, depuis le canonique, sans repli `etl_fallback` de chapitre |

### Phase 2 — Arithmétique, assiettes et taxes

| # | Travail | Fichiers | Acceptation |
|---|---|---|---|
| 2.1 | Suppression des `or 0` porteurs de sens | `authentic_tariff_service.py` (l. 1639, 1696, 1697, 799, 887, 1169 et suivantes) | Un champ absent devient `INDISPONIBLE`, jamais 0. Aucune exception `NoneType`. `DZA 1001110000` et `ZAF 020830` retournent une indisponibilité motivée |
| 2.2 | Droits spécifiques et mixtes | `tax_computation.py`, `authentic_tariff_service.py` | Un droit non exprimable en pourcentage est conservé sous forme d'expression + unité ; le montant n'est calculé que si quantité et devise sont fournies, sinon montant indisponible et paramètre requis signalé. Couvre les 181 lignes SACU et les 1 655 lignes TUN à taxe spécifique |
| 2.3 | Assiettes réelles | `tax_computation.py` | TUN RPD calculée sur « somme des droits et taxes », pas sur CIF ; DSV liquidée sur quantité (`0,1 dinar`/QCS) ou déclarée indisponible. Plus de renommage RPD → TCL |
| 2.4 | Déduplication des taxes | `normalize_crawled.py`, `calculator.py` (`_is_vat_tax`) | `GHA 270900` ne présente plus deux TVA de 15 % ; la déduplication porte sur la nature du prélèvement, pas sur le seul code `DD` |
| 2.5 | Cohérence interne de la réponse | `authentic_tariff_service.py` | `rates.dd_rate_pct` et le détail ne peuvent plus diverger (cas TUN `73090090109` : 0 % annoncé, 30 % calculé). Test de cohérence systématique sur le corpus |
| 2.6 | Réconciliation des indicateurs globaux | `calculator.py:257`, registre pays | Un `vat_status = NOT_AVAILABLE` global ne neutralise plus une TVA prouvée par la ligne (`TUN 90031100003`). L'indicateur global n'est plus qu'un défaut, la ligne fait foi |

### Phase 3 — Convergence des chemins

| # | Travail | Fichiers | Acceptation |
|---|---|---|---|
| 3.1 | POST délégué au moteur unique | `backend/routes/calculator.py` | Le POST consomme la résolution de la phase 1 et le calcul de la phase 2 ; les dictionnaires ETL de chapitre ne servent plus qu'en dernier recours explicitement étiqueté |
| 3.2 | Périmètre ZLECAf homogène | `calculator.py`, `authentic_tariffs.py` | Origine hors ZLECAf : même décision sur les deux chemins (le flux monde → Afrique n'est plus accepté d'un côté et rejeté de l'autre) |
| 3.3 | Fin du repli silencieux de l'interface | `frontend/src/components/calculator/CalculatorTab.jsx:402-690` | Un seul appel ; une erreur du chemin serveur est affichée, pas masquée. La réponse expose la source, le fichier et la version réellement utilisés |
| 3.4 | Verrou anti-divergence | intégration continue | `scripts/diff_engines.py` en CI : tout `ECART_TAUX`, `ECART_MONTANT` ou `EXCEPTION` nouveau fait échouer la construction |

### Phase 4 — Traçabilité opérante

| # | Travail | Fichiers | Acceptation |
|---|---|---|---|
| 4.1 | Manifeste des jeux réellement actifs | nouveau `backend/data/active_datasets_manifest.json` | Pour chaque pays : fichier servi, version, SHA-256, source, version SH, date de collecte — retrouvables depuis une réponse de calcul |
| 4.2 | Intégrité imposée à l'exécution, sans coût de démarrage | `backend/crawlers/integrity.py`, chargeurs | Vérification paresseuse au premier accès par fichier, résultat mis en cache ; une empreinte non concordante refuse la donnée au lieu de la servir |
| 4.3 | Fraîcheur de la couche normalisée | `start.sh:28-33`, `Dockerfile` | La régénération est déclenchée par une divergence d'empreinte des crawls, pas seulement par un dossier vide. Un normalisé périmé est refusé, pas servi |
| 4.4 | `source_hash` renseigné | crawlers, sceaux | Le sceau relie le fichier au document source téléchargé, pour les pays où l'archive existe ; sinon le champ reste nul et le niveau de preuve est déclaré tel quel |
| 4.5 | Provenance juridique corrigée | `normalize_crawled.py` (table des groupes régionaux) | GIN, GMB, LBR, SLE, CPV ne portent plus de base légale UEMOA. Aucune référence n'est attachée sans vérification d'applicabilité |
| 4.6 | Marqueurs d'inférence conservés jusqu'au résultat | `normalize_crawled.py`, réponses | `classification_source = estimation_ia` reste visible dans la taxe structurée, pas seulement dans `raw_data`. Une estimation n'est jamais présentée comme source authentifiée |
| 4.7 | Identification fidèle du format | `authentic_tariff_service.py` | Plus de `data_format = enhanced_v2` sur des fichiers canoniques v4 |

### Phase 5 — Couverture et exhaustivité (piste parallèle, calendrier propre)

| # | Travail | Acceptation |
|---|---|---|
| 5.1 | Énumérations nationales de référence, sur le modèle tunisien | Pour chaque pays prioritaire, un fichier d'énumération officielle daté permettant de chiffrer le déficit — aujourd'hui indéterminé hors TUN |
| 5.2 | Compteurs de couverture à quatre états | `DOCUMENTE`, `PARTIEL`, `INDISPONIBLE`, `NON_APPLICABLE_DOCUMENTE` par position, pour droits, taxes et formalités. Plus de « 100 % » déduit de listes non vides (cas MAR) |
| 5.3 | Formalités au niveau national | Les formalités ne sont plus lues au seul parent HS6 ; sens import/export, autorité, document, base légale et conditions conservés |
| 5.4 | Audit du déploiement | Commit du pod, empreintes des jeux, dates et compteurs PostgreSQL comparés au manifeste 4.1 |
| 5.5 | Remplacement progressif des jeux `W` (moyennes WITS) et `Ø` | 14 pays en moyenne NPF SH6 et 2 pays vides (DJI, ERI) sont étiquetés comme non-nomenclature nationale dans l'interface tant qu'aucune source nationale n'existe |

## 4. Ordonnancement et dépendances

```
Phase 0 (mesure)  ──►  Phase 1 (résolution)  ──►  Phase 2 (calcul)  ──►  Phase 3 (convergence)
                                │                        │
                                └────────► Phase 4 (traçabilité) ◄──────┘
Phase 5 (données) : parallèle, indépendante du code
```

- Les phases 0 à 3 sont séquentielles : chacune s'appuie sur le critère d'acceptation de la précédente.
- La phase 4 peut démarrer dès la fin de 1.1 (le manifeste a besoin du résolveur pour savoir ce qui est servi).
- La phase 5 ne bloque aucune livraison logicielle ; elle conditionne seulement les affirmations d'exhaustivité.

## 5. Règles de livraison

1. **Une phase = une série de commits révisables**, avec le corpus de la phase 0 vert à chaque étape.
2. **Aucune donnée tarifaire n'est modifiée pour faire passer un test.** Les corrections portent sur le code de résolution et de calcul ; une donnée fausse se corrige par recollecte, tracée séparément.
3. **Aucun taux fabriqué.** Si une correction rend une ligne non calculable, elle devient explicitement indisponible — c'est un progrès, pas une régression.
4. **Les colonnes du calculateur sont conservées**, conformément à l'audit ; seules les valeurs et les statuts deviennent fiables.
5. **Aucune affirmation d'authenticité juridique** n'est ajoutée à l'interface sans preuve ligne par ligne.

## 6. Risques

| Risque | Portée | Atténuation |
|---|---|---|
| La correction des `or 0` fait apparaître massivement des indisponibilités | Interface, perception de régression | Chiffrer le volume dès la phase 0 avec le harnais ; trancher l'affichage en 0.3 avant de coder |
| La préséance crawl > canonique dégrade un pays où le canonique est meilleur | Pays à crawl régional ou WITS | La préséance est par pays et par champ, pilotée par le manifeste 4.1, pas codée en dur |
| La convergence des moteurs casse des usages existants du POST | Clients de l'API | Phase 3 derrière un indicateur d'activation, avec le rapport différentiel comme preuve d'équivalence avant bascule |
| L'exhaustivité (phase 5) est confondue avec la correction (phases 1-3) | Communication | Les deux pistes ont des livrables et des calendriers distincts ; aucune ne se réclame de l'autre |

## 7. Ce que ce plan ne prétend pas faire

- Il ne certifie aucun pays juridiquement exhaustif. L'audit non plus, et c'est sa conclusion la plus importante.
- Il ne statue pas sur le contenu de PostgreSQL en production, hors de portée du dépôt (travail 5.4).
- Il ne remplace pas la recollecte officielle des taux ; il garantit que le taux collecté est celui qui est servi, calculé sur la bonne assiette, et identifiable.

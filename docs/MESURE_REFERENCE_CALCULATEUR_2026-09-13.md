# Mesure de référence des deux chemins de calcul — 13 septembre 2026

Résultat du harnais différentiel `scripts/diff_engines.py` (travail 0.1 du plan
de correction). Cette mesure est l'état **avant** correction : elle sert de
point de comparaison à chaque phase suivante.

## Conditions

- 320 positions : 40 codes tirés par pays sur DZA, EGY, ETH, GHA, MUS, SOM, TUN,
  ZAF. Tirage déterministe (graine fixe) : deux exécutions sur le même commit
  portent sur les mêmes codes.
- CIF 1 000, origine SEN, langue française.
- PostgreSQL neutralisé, conversion monétaire neutralisée, appels OEC et Banque
  mondiale neutralisés.
- Couche normalisée générée pour les sept pays porteurs d'un crawl ; la Somalie
  n'en a pas, ce que le rapport signale au lieu de le compter comme un défaut.

## Résultat d'ensemble

**318 divergences sur 320 positions.** Deux positions égyptiennes seulement
donnent le même résultat sur les deux chemins.

| Verdict | Cas | Lecture |
|---|---:|---|
| `ECART_MONTANT` | 174 | Même droit, montants de taxes différents : assiettes ou taxes divergentes |
| `ECART_TAUX` | 50 | Le droit de douane lui-même diffère |
| `ABSENT_POST` | 40 | Position servie par le chemin prioritaire, introuvable sur le POST |
| `ABSENT_PRIORITAIRE` | 33 | Position servie par le POST, introuvable sur le chemin prioritaire |
| `ECART_QUALIFICATION` | 20 | Montants identiques, mais l'un qualifie d'authentique ce que l'autre donne pour indicatif |
| `EXCEPTION_PRIORITAIRE` | 1 | Le chemin prioritaire lève une exception |
| `IDENTIQUE` | 2 | Concordance complète |

## Par pays : chaque défaut est systématique, aucun n'est anecdotique

| Pays | Cas | Répartition | Mécanisme dominant |
|---|---:|---|---|
| Ghana | 40 | `ABSENT_POST` 40 | La normalisation agrège les codes nationaux au parent SH6 : **aucun** enfant national testé n'est adressable sur le POST |
| Tunisie | 40 | `ECART_MONTANT` 40 | Le POST rend une TVA nulle sur toutes les positions testées, malgré les taux publiés par le crawl |
| Afrique du Sud | 40 | `ECART_MONTANT` 40 | Même figure : TVA calculée par le chemin prioritaire, absente du POST |
| Algérie | 40 | `ECART_MONTANT` 39, `EXCEPTION_PRIORITAIRE` 1 | Assiettes divergentes sur les autres taxes (61,54 contre 50,00) et sur la TVA (247,00 contre 256,50) |
| Somalie | 40 | `ECART_TAUX` 40 | Le POST applique un tarif de chapitre (`etl_fallback`) sur **toutes** les positions, au lieu du canonique |
| Égypte | 40 | `ECART_MONTANT` 29, `ECART_TAUX` 9, `IDENTIQUE` 2 | Droit canonique périmé contre droit du crawl ; assiette de TVA divergente |
| Éthiopie | 40 | `ABSENT_PRIORITAIRE` 26, `ECART_MONTANT` 13, `ECART_TAUX` 1 | Positions nationales sans parent SH6 au canonique : introuvables sur le chemin prioritaire |
| Maurice | 40 | `ECART_QUALIFICATION` 20, `ECART_MONTANT` 13, `ABSENT_PRIORITAIRE` 7 | Moyenne NPF WITS présentée comme tarif authentique par le chemin prioritaire |

## Trois familles de causes, et ce qu'elles confirment du plan

1. **Résolution de la ligne (73 cas d'absence).** Le Ghana perd ses enfants
   nationaux à la normalisation ; l'Éthiopie perd ses positions sans parent
   canonique. Les deux chemins ne travaillent pas sur le même ensemble de
   positions. C'est la cause racine que la phase 1 traite, et la mesure confirme
   qu'elle doit passer avant l'unification des moteurs.

2. **Assiettes et taxes (174 cas d'écart de montant).** La divergence porte sur
   la TVA dans 173 des 174 cas. Deux erreurs opposées y coexistent : le chemin
   prioritaire **fabrique** une TVA là où la source n'en porte pas — cas
   sud-africain, où le crawl SARS Schedule 1 ne contient pas la TVA — et le POST
   **supprime** une TVA publiée — cas tunisien, où un indicateur pays global
   neutralise les taux de la ligne. Aucune des deux valeurs n'est démontrée :
   c'est précisément la situation que la note de décision
   `docs/DECISION_INDISPONIBILITE_CALCULATEUR.md` propose de traiter en
   `INDISPONIBLE` plutôt qu'en chiffre.

3. **Qualification de la source (20 cas).** Les montants concordent, la nature de
   la donnée non. Une moyenne NPF WITS de 2022 servie sous le libellé
   `authentic_tariff` est un défaut de traçabilité même quand le chiffre est le
   même de part et d'autre.

## Trois défauts relevés en établissant la mesure

- **Unités contradictoires entre les deux contrats d'API.** Le chemin prioritaire
  publie le droit en pourcentage (`rates.dd_rate_pct` = 19.5), le POST en
  fraction (`normal_tariff_rate` = 0.195, `calculator.py:332`). Le harnais
  convertit pour pouvoir comparer ; l'incohérence reste à corriger en phase 3.
- **Le POST sait déjà dire « indisponible », le chemin prioritaire non.** Le POST
  expose `duty_status=UNAVAILABLE` sur les positions sans droit exploitable, là
  où le chemin prioritaire rend 0 ou lève une exception. La sémantique existe
  donc déjà d'un côté : la phase 2 l'étend, elle ne l'invente pas.
- **La suite de tests dépend silencieusement de la couche non versionnée.**
  `backend/tests/test_calculator_zlecaf_fail_closed.py` échoue trois fois sur une
  couche normalisée partielle (404 `COUNTRY_NOT_RECRAWLED` pour MOZ) et repasse à
  26/26 dès que le pays attendu est normalisé. Un clone neuf ne peut donc pas
  distinguer une régression d'un dossier incomplet. À traiter avec le travail 4.3
  (fraîcheur et refus d'une couche périmée) : un test doit être skippé sur donnée
  absente, pas échouer.

## Reproduire

```bash
# Couche normalisée pour les pays à comparer (non versionnée, ~2 Go au complet)
python3 scripts/normalize_crawled.py --country EGY

# Mesure
PYTHONPATH=.:backend python3 scripts/diff_engines.py \
    --countries DZA,EGY,ETH,GHA,MUS,SOM,TUN,ZAF --per-country 40 \
    --out /tmp/baseline.json

# Les dix cas de l'audit
PYTHONPATH=.:backend python3 scripts/diff_engines.py \
    --cases backend/tests/fixtures/calculator_golden.json
```

## Limites

Cette mesure compare deux chemins entre eux ; elle ne dit pas lequel a raison en
droit. Quand les deux divergent, la source citée dans
`backend/tests/fixtures/calculator_golden.json` tranche par rapport au **fichier
versionné le plus récent**, ce qui n'est pas une revalidation juridique auprès de
l'administration concernée. L'échantillon de 40 codes par pays établit qu'un
défaut est systématique, pas son volume exact sur la nomenclature entière.

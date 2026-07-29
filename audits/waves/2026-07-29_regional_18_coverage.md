# Vague régionale 18 pays — couverture tarifaire et documentaire

Date de référence : 2026-07-29
Périmètre : EAC (7), SACU (5), CEMAC (6)

## Résultat

La vague expose désormais dans les deux chemins du calculateur un bloc
`country_enrichment` homogène pour 18 pays :

- tarif commun et profondeur nationale réellement disponibles ;
- statut de la TVA, des autres taxes et de l'ordre de calcul ;
- statut distinct des préférences ZLECAf ;
- mesures réglementaires et documents exigibles uniquement lorsqu'une source
  locale les rattache au pays ;
- sources, dates, empreintes et statuts de vérification disponibles ;
- anomalies connues, sans correction silencieuse.

Cette évolution augmente la **couverture API**. Elle ne prétend pas avoir
collecté de nouveaux taux nationaux pour les pays encore dépourvus de sources.

## Couverture tarifaire contrôlée

| Bloc | Pays | Lignes par pays | Profondeur constatée | Source déclarée |
|---|---:|---:|---|---|
| EAC | 7 | 5 984 | 8 chiffres | EAC CET 2022 |
| SACU | 5 | 8 589 | 6/8 chiffres | SARS Schedule 1 Part 1 |
| CEMAC | 6 | 5 239 | 8 chiffres | TEC CEMAC |

Les tarifs communs ne servent jamais de preuve pour une taxe intérieure
nationale. Les extensions 10/12 chiffres restent `NOT_AVAILABLE` lorsqu'elles
ne sont pas collectées.

## Statuts fiscaux et réglementaires

| Couche | DOCUMENTED | PARTIAL | UNVERIFIED | NOT_AVAILABLE |
|---|---:|---:|---:|---:|
| TVA | 8 | 3 | 7 | 0 |
| Autres taxes | 2 | 8 | 1 | 7 |
| Ordre de calcul | 2 | 10 | 0 | 6 |
| Préférence ZLECAf | 0 | 1 | 0 | 17 |
| Mesures réglementaires | 0 | 2 | 0 | 16 |
| Documents exigibles | 1 | 1 | 0 | 16 |

`PARTIAL` ne signifie pas « taux estimé ». Il indique qu'une partie du cadre
est traçable mais que la couverture n'est pas suffisante pour qualifier la
couche de complète.

## Documents exigibles

- **Kenya — DOCUMENTED** : certificat d'origine de la section 44A et paquet
  documentaire de dédouanement KRA, avec source, étape et portée.
- **RDC — PARTIAL** : documents rattachés aux mesures SEGUCE, OCC/CBCA et
  OGEFREM/FERI. L'autorité responsable est distinguée de l'émetteur, laissé à
  `null` lorsqu'il n'est pas prouvé.
- **16 autres pays — NOT_AVAILABLE** : aucune liste générique n'est dupliquée
  par ligne SH ou copiée d'un pays voisin.

Les prescriptions nationales, opérationnelles ou liées au mode de transport
restent au niveau pays/mesure. Elles ne deviennent une exigence SH que si une
liste de codes explicite existe dans la source.

## Anomalies prioritaires conservées

- SSD : TVA runtime décrite comme estimée.
- TCD : conflit temporel entre runtime et archive fiscale antérieure.
- GNQ : réutilisation de libellés/bases camerounais.
- UGA : texte fixant le taux standard non archivé.
- GAB : source primaire du taux standard à compléter.
- BDI : taux runtime sans archive fiscale nationale.
- BWA, LSO, NAM, SWZ : tarif SACU disponible, fiscalité nationale non sourcée.
- CAF : prélèvements nationaux non documentés.
- COD : profil complet d'ordre de calcul encore partiel.

Aucun de ces conflits n'est arbitré par une valeur par défaut.

## Contrat d'affichage

> Données réglementaires et tarifaires fournies à titre informatif, non
> opposables à l'administration douanière. Une donnée absente ou non traçable
> reste `NOT_AVAILABLE` et n'est jamais remplacée par une valeur simulée.

## Vérification

- couverture exacte : 18/18 pays ;
- contrôle intégral des fichiers tarifaires des 18 pays et de leurs comptages ;
- chemins de sources enregistrés : tous existants ;
- taux numérique ajouté au registre : 0 ;
- documents génériques affectés aux 16 pays sans source : 0 ;
- tests ciblés : 30 réussis ;
- `black`, `isort`, `flake8` et `git diff --check` : conformes.

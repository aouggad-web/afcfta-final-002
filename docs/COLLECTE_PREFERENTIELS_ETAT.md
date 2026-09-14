# État de la collecte préférentielle et fiscale — 13 septembre 2026

Produit par `scripts/tax_coverage_inventory.py` sur les 53 fichiers de
`backend/data/crawled/`. Codes de taxes canonicalisés par la fonction du dépôt
(`services.authentic_tariff_service._canonical_tax_code`) et non par une
heuristique de l'inventaire — condition pour que l'inventaire et le calculateur
parlent de la même chose.

## Le constat qui commande la suite

**La donnée préférentielle est déjà collectée pour 16 pays, et le calculateur ne
l'exploite pas.** Avant de financer une campagne de collecte, il faut exploiter
ce qui est en place : 42 020 taux ZLECAf sud-africains et la table tunisienne par
pays partenaire dorment dans le dépôt pendant que le calculateur déclare le taux
ZLECAf indisponible.

## Ce qui est déjà collecté

### Colonnes préférentielles dans la collection de taxes

| Régime | Occurrences | Dont taux numérique | Pays |
|---|---:|---:|---|
| **AfCFTA / ZLECAf** | 42 925 | **42 020** | BWA, LSO, NAM, SWZ, ZAF |
| SADC | 42 940 | 42 905 | idem |
| EU / UK | 42 940 | 42 825 | idem |
| MERCOSUR | 42 940 | 42 065 | idem |
| EFTA | 42 940 | 42 610 | idem |
| COMESA (`D2R`) | 1 939 | 1 939 | ETH |

Le Schedule 1 sud-africain porte donc une colonne ZLECAf renseignée sur la
quasi-totalité de ses lignes — 4 654 en franchise (« free »), le reste échelonné
de 2 % à 45 %. Les 905 restantes sont des droits spécifiques, non convertibles en
pourcentage.

### Régimes préférentiels portés hors de la collection de taxes

Invisibles d'un recensement qui ne lirait que `taxes` :

| Champ | Pays | Contenu |
|---|---|---|
| `preferences` | **TUN** | **Taux par pays partenaire et par accord** — le plus riche du dépôt : zones `ZLECAf`, `ZALE` (GAFTA), `ACCORD_UE`, `ACCORD_AELE`, `ACCORD_BILATERAL`, accord d'Agadir. Sur 17 542 positions |
| `fiscal_advantages` | BDI, COD, KEN, RWA, SSD, TZA, UGA | Franchise intra-EAC 0 % sous certificat d'origine. 41 888 positions |
| `advantages` | DZA, ETH | Exonérations en texte libre (GZALE, convention algéro-jordanienne) et colonne COMESA |

## Ce qui reste à collecter

| Cible | Pays | Régimes attendus | Volume potentiel |
|---|---|---|---|
| Portail ADIL | **MAR** | UE, États-Unis, Turquie, Agadir, Ligue arabe | 13 114 positions |
| Portail douanier | **EGY** | UE, Agadir, COMESA, GAFTA | 8 818 positions |
| Régimes régionaux | 15 pays CEDEAO | Franchise intra-communautaire | règle régionale, pas par ligne |
| Régimes régionaux | 6 pays CEMAC | Franchise intra-communautaire | idem |
| Tarif national complet | AGO, LBY, MOZ, STP + 9 autres pays WITS | tout | 13 pays sans nomenclature nationale |

## Déficits fiscaux hors préférentiel

Environ 80 codes de taxes distincts sont recensés — la richesse fiscale réelle
des 54 systèmes : `RS` 72 658, `PCS` 67 419, `PCC` 55 161, `PUA` 54 271,
`TCI` 31 434, `PCAES` 18 387, `PRCT` et `TCS` 17 226 chacun, `EXC` 6 005,
`IAT` 6 279, `OHADA` 5 239, `CIA` 5 239, et les redevances de chambre égyptiennes
libellées en arabe.

Deux manques structurels subsistent :

- **TVA absente de la source** pour 10 pays : les 5 SACU (le Schedule 1 ne
  contient pas la TVA, par construction), GHA, et AGO, LBY, MOZ, STP. Pour les
  six premiers, un taux national figure au fichier canonique ; pour les quatre
  derniers, nulle part.
- **Assiette non portée** par la plupart des sources : le taux est là, la base de
  calcul ne l'est pas. Ce n'est pas un déficit de collecte en soi — le dépôt
  fournit des profils de cascade par pays — mais l'écart entre les deux doit être
  tracé.

## Limites de cet inventaire

Un code de taxe restant, non canonicalisé, agrège **6 086 entrées**.

Ce chiffre en remplace un autre, et la correction vaut d'être dite. Cette
section annonçait d'abord 117 197 entrées, attribuées aux pays CEDEAO qui
porteraient leurs taxes « sans champ `code` ». C'était faux : ces pays portent
bien un code, sous la clé `tax_code`, et l'inventaire ne lisait que `code`. Le
défaut était dans l'outil de mesure, pas dans la donnée, et 95 % du chiffre
publié n'existait pas. Voir `scripts/tax_coverage_inventory.py`.

La même correction a rétabli 442 961 assiettes que l'inventaire déclarait
absentes : la déduplication gardait la collection compacte `taxes`, un
dictionnaire de taux nus, au lieu de `taxes_detail` qui porte `base: "CIF"`.

Les 6 086 entrées restantes sont à trier avant de conclure quoi que ce soit sur
les pays concernés — mais elles ne justifient plus de traiter la CEDEAO comme un
chantier de collecte prioritaire.

L'inventaire décrit ce que les fichiers portent. **Une taxe absente n'est pas
réputée non due** : on ne peut pas déduire d'un fichier ce qu'une administration
lève. L'écart entre le fichier et le prélèvement réel est précisément ce que la
collecte doit établir, et il reste indéterminé hors Tunisie.

## Reproduire

```bash
PYTHONPATH=.:backend python3 scripts/tax_coverage_inventory.py --out inventaire.json
PYTHONPATH=.:backend python3 scripts/tax_coverage_inventory.py --countries TUN,ZAF --detail
```

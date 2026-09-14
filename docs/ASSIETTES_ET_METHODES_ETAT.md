# Assiettes et méthodes de calcul — état des lieux

**Constat bloquant : le dépôt détient deux descriptions de l'assiette, elles ne
s'accordent pas, et le moteur n'en lit qu'une.**

Ce document consigne ce que mesure `scripts/inventory_tax_bases.py`, dont le
rapport est versionné dans `reports/ASSIETTES_ET_METHODES.json`.

## Pourquoi l'assiette n'est pas un détail

Une taxe n'est pas un taux : c'est un taux **et** une assiette. Servir 18 % de
TVA sans savoir si l'assiette est `CIF`, `CIF + DD` ou `CIF + DD + RS + PCS`,
c'est fabriquer un montant — exactement ce que la doctrine de ce dépôt interdit.

Et ce qui compte n'est pas de quelle administration relève le prélèvement. Droit
de douane, droits connexes, taxes à effet équivalent, taxes intérieures et
accises perçues à l'occasion du dédouanement : tout ce que l'opérateur paie au
passage en douane entre dans le coût, pourvu que la source le publie et que la
provenance soit tracée.

## Les deux sources de vérité

| | Où | Qui la lit |
|---|---|---|
| **Assiette publiée** | champ `base` des fichiers `backend/data/crawled/*_tariffs.json` | personne |
| **Table codée** | `COUNTRY_TAX_PROFILES` dans `authentic_tariff_service.py`, 37 pays | `compute_tax_cascade()`, seule |

Le moteur applique la table. Là où elle diverge de la source, le montant servi
est faux.

## Ce que les sources publient réellement

Seize expressions d'assiette distinctes. Pour la TVA, le CIF seul est
l'exception :

| Assiette de la TVA publiée par la source | Pays |
|---|---|
| `CIF + DD + RS + PCS` | 11 — CEDEAO / UEMOA |
| `CIF + DD + TCI` | 6 — CEMAC |
| `CIF + Duty` | 5 — EAC |
| `CIF + Duty + Fees` | Kenya |
| `CIF + Duty + Levies` | Ouganda |
| `VAL.DOU(D)+R(DT) GR.0` | Tunisie |
| `CIF` seul | Côte d'Ivoire |

## Les quinze désaccords

```
BEN BFA CPV GMB GNB LBR MLI NER SEN SLE TGO   TVA   source CIF+DD+RS+PCS   table CIF+DD
KEN                                           TVA   source CIF+DD+Fees     table CIF+DD
UGA                                           TVA   source CIF+DD+Levies   table CIF+DD
TUN                                           TVA   source VAL.DOU+R(DT)   table CIF+DD
CIV                                           TVA   source CIF             table CIF+DD
```

**L'erreur va dans les deux sens**, ce qui exclut toute correction par
coefficient. Sur une opération à 10 000 de CIF :

| | Écart | En part du CIF |
|---|---:|---:|
| Bénin — TVA sous-évaluée (la table omet RS et PCS) | 36,00 | 0,36 % |
| Côte d'Ivoire — TVA sur-évaluée (la table ajoute un DD absent de la source) | 360,00 | 3,60 % |

**14 pays n'ont aucun profil codé** et tombent sur le défaut du moteur — « TVA
sur CIF + DD » — qui est faux pour toute la CEDEAO.

## Les assiettes qui ne sont pas des valeurs

Treize couples pays/taxe portent une assiette non valorielle. Les fondre dans la
cascade produirait des montants faux :

- **quantitatives** — `PN (KG)`, `QCS`, `PN(KG)/100 EXCES` : onze taxes
  tunisiennes, assises sur un poids ou une quantité, pas sur une valeur ;
- **plafonnées** — `CIF (plafond 15 000 XAF)` : la redevance informatique
  camerounaise et équato-guinéenne.

## État de la connaissance, sur 247 couples pays/taxe

| Statut | Couples |
|---|---:|
| `lue_dans_la_source` | 158 |
| `table_codee_seule` | 34 |
| `non_documentee` | 55 |

`non_documentee` dit que le dépôt ignore l'assiette, **pas** qu'elle n'existe
pas : beaucoup d'administrations ne répètent pas dans leur nomenclature une
convention qu'elles publient ailleurs.

## Ce qui reste à trancher

Aucun des quinze désaccords n'est résolu ici, et le rapport n'en tranche aucun.
Deux lectures restent ouvertes, à départager **pays par pays** :

1. la table codée est périmée et la source fait foi — la cohérence par bloc
   régional plaide fortement en ce sens ;
2. certaines entrées de la table encodent une règle réelle que le champ `base`
   du crawl résume mal — auquel cas c'est le crawl qu'il faut creuser.

Le cas ivoirien est le plus suspect : `CIF` seul pour la TVA serait une anomalie
en UEMOA, où ses onze voisins publient tous `CIF + DD + RS + PCS`. Cela ressemble
davantage à une donnée incomplète côté collecte qu'à une règle nationale
distincte, et doit être vérifié sur source primaire avant toute correction.

## Conséquence sur la politique d'indisponibilité

`docs/DECISION_INDISPONIBILITE_CALCULATEUR.md` proposait de servir le taux de TVA
national quand le tarif est muet. **Cette proposition est suspendue jusqu'à
résolution du présent constat** : un taux sans son assiette ne produit pas un
montant, et servir un taux national sur une assiette supposée reviendrait à
fabriquer un chiffre.

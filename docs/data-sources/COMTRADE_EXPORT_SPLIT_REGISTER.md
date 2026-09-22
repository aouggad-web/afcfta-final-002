# Exportations domestiques / réexportations — registre de source

Date de consultation : 2026-09-22. Donnée machine-readable :
`backend/etl/comtrade_export_split.py` (GÉNÉRÉ — ne pas éditer à la main).
Générateur : `backend/scripts/build_comtrade_export_split.py`.

## Source

| ID | Titre | Éditeur | Accès | Statut |
|---|---|---|---|---|
| `UN-COMTRADE-PREVIEW-DXRX` | UN Comtrade, flux `X` / `DX` / `RX`, partenaire Monde, tous produits | Nations Unies (UNSD) | Endpoint **public**, sans clé | COLLECTED |

URL : `https://comtradeapi.un.org/public/v1/preview/C/A/HS`
Référentiel des déclarants : `https://comtradeapi.un.org/files/v1/app/reference/Reporters.json`

Contraintes de l'endpoint public, constatées : **une seule période par appel**
(un appel multi-années répond `Maximum number of periods for preview is 1`) et
une **limite de débit** qui répond `429`. Le générateur espace ses appels et
réessaie.

## Pourquoi ce module existe — et ce qu'il corrige

`services/national_official_stats.py` affirmait qu'« aucune source
internationale ne publie cette ventilation ». **C'est faux.** L'affirmation
justifiait à elle seule la collecte manuelle office par office, qui a donné un
pays sur cinq. La source internationale en donne huit d'un coup, sans clé.

L'erreur n'était pas une paresse de recherche : les codes `DX` / `RX`
n'existent que pour les déclarants qui les soumettent, et rien dans la
documentation générale de Comtrade ne les met en avant. Mais elle était
vérifiable, et elle ne l'avait pas été.

## La règle d'admission : réconcilier, pas seulement exister

Un pays n'entre que si **`DX + RX` retombe sur `X`** à la tolérance d'arrondi
près (un millionième du total, plancher 1 USD).

Ce contrôle n'est pas cosmétique. Neuf pays africains publient les trois flux
sans qu'ils se recomposent :

| Pays | Écart entre `X` et `DX + RX` |
|---|---|
| Namibie | 136 595 731 % du total |
| Zambie | 13 140 549 % |
| Bénin | 140 205 % |
| Angola | 864 % (la somme vaut 8,6 fois le total) |
| Afrique du Sud | 99,6 % |
| Madagascar | 72,3 % |
| Burkina Faso | 78,4 % |
| Maurice | 43,9 % |
| Botswana | 5,4 % |

Ce ne sont pas des arrondis : ce sont des couvertures différentes selon le
flux. Les servir ferait passer une incohérence pour une mesure.

C'est la même règle qui a fait rejeter le Tableau 83 du bulletin togolais
(voir `TGO_STATS_REGISTER.md`) : une décomposition qui ne retombe pas sur son
total n'est pas une décomposition.

## Ce que ce module ne fait pas

- **Il ne complète aucun flux.** Un pays qui ne publie que `X` reste dehors ;
  on n'en déduit pas `DX = X` au motif que ses réexportations seraient
  « probablement faibles ».
- **Il ne convertit pas.** Valeurs en USD telles que publiées par l'ONU.
- **Il ne descend pas au produit ni au client.** Les chiffres portent sur le
  total des marchandises, partenaire Monde.
- **Il ne remplace pas la collecte nationale.** Maurice en est la preuve : son
  office publie la ventilation jusqu'au produit, et Comtrade ne réconcilie pas
  pour elle. Les deux couches sont **complémentaires** — l'ONU couvre plus de
  pays, l'office national descend plus bas. Un test le verrouille
  (`test_this_layer_does_not_replace_the_national_offices`).

## Deux constats que la collecte manuelle n'avait pas donnés

**Le Togo y figure**, avec une ventilation qui réconcilie — alors que son
bulletin INSEED ne le permettait pas. L'avertissement posé dans
`TGO_STATS_REGISTER.md` reste exact sur ce qu'il affirme, mais sa portée était
trop large : la ventilation n'était pas publiable **par l'INSEED**, pas
« pas publiable ».

**La Gambie est à 83,3 % de réexportations.** Quatre cinquièmes de ses
exportations enregistrées ne sont pas d'origine gambienne. C'est le pays où
confondre les deux flux coûte le plus cher au regard des règles d'origine
ZLECAf — et il ne figurait dans aucune liste de cibles.

## Vérifier

```bash
# Régénérer (lent : l'endpoint public limite le débit)
python3 backend/scripts/build_comtrade_export_split.py --dry-run

# Contrôler un pays à la main
curl -s "https://comtradeapi.un.org/public/v1/preview/C/A/HS?reporterCode=404&period=2023&flowCode=DX&cmdCode=TOTAL&partnerCode=0"
curl -s "https://comtradeapi.un.org/public/v1/preview/C/A/HS?reporterCode=404&period=2023&flowCode=RX&cmdCode=TOTAL&partnerCode=0"
curl -s "https://comtradeapi.un.org/public/v1/preview/C/A/HS?reporterCode=404&period=2023&flowCode=X&cmdCode=TOTAL&partnerCode=0"
# Kenya 2023 : 6 433 134 310,035 + 724 975 022,737 = 7 158 109 332,772 ≈ X
```

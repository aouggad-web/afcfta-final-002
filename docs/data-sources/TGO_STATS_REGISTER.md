# Togo — registre des sources statistiques nationales

Date de consultation : 2026-09-21. Donnée machine-readable :
`data/national_stats/TGO.json`.

Même discipline que `MUS_STATS_REGISTER.md` : un éditeur nommé, une
publication datée, une URL, et l'empreinte du fichier servi.

## Sources

| ID | Titre | Éditeur | Année des données | Statut | SHA-256 du fichier servi |
|---|---|---|---|---|---|
| `TGO-INSEED-CIM-2025T4` | Bulletin trimestriel des statistiques du commerce international des marchandises — 4e trimestre 2025 | INSEED Togo | 2025 | COLLECTED | `e4f2e9e924bab49ab4f74ab1c9b011c7407ddfce401bbadd4bf64968eaf7fd34` |

URL : https://inseed.tg/download/7638/ — page de rubrique :
https://inseed.tg/echanges-exterieurs/ (série trimestrielle depuis 2016).

## Ce que cette source apporte — et pourquoi ce n'est PAS une ventilation

Le Togo entrait dans le lot « pays à zones franches actives » pour la même
raison que Maurice : séparer exportations domestiques et réexportations. La
source montre que, pour le Togo, **cette séparation n'est pas publiable**.

**1. La définition est explicite, et elle joue contre nous.** Note
méthodologique, p. xii :

> Les statistiques sont publiées selon deux flux : l'exportation (exportation
> totale) et l'importation. L'exportation regroupe l'exportation simple et la
> réexportation. L'exportation simple est l'expédition des marchandises
> nationales (ou nationalisées par la mise à la consommation). La
> réexportation est l'expédition de biens d'origine étrangère ayant été
> auparavant enregistrés comme des importations.

Le total publié — 258 434,7 millions de FCFA au 2025T4 (Tableau 1) —
**contient** donc les réexportations.

**2. La ventilation n'existe qu'au régime douanier, jamais au produit.** Les
89 tableaux du bulletin portent sur l'exportation *totale*. Le seul endroit où
les deux flux se distinguent est le Tableau 83, « Valeur des échanges selon le
régime douanier » : régimes `1xxx` pour l'exportation définitive, `3xxx` pour
la réexportation. Aucun tableau ne croise le régime avec le produit (SH, CTCI)
ni avec le pays client. Les dix premiers produits exportés et les dix premiers
clients (Tableaux 3 et 5) sont des totaux, tous flux confondus.

**3. Le Tableau 83 ne se réconcilie pas avec le total publié.** Au 2025T4, les
régimes d'exportation `1xxx` totalisent 194 184,3 et les régimes de
réexportation `3xxx` 117 305,8, soit 311 490,1 millions de FCFA — contre
258 434,7 publiés, un écart de 53 055,4. Une recherche exhaustive sur les
sous-ensembles des régimes `3xxx` ne trouve **aucune** combinaison reproduisant
le total publié sur les cinq trimestres du tableau. La règle de composition du
total n'est donc pas celle que suggèrent les libellés.

Conclusion : reconstituer un « export domestique togolais » serait une
agrégation maison, contredite par la source elle-même. Elle n'est pas faite.

## Ce qui est servi à la place

- `export_flow_caveat` — l'avertissement daté, le total publié, et la
  définition citée. C'est un fait sourcé, pas un chiffre inventé : il empêche
  de lire un chiffre d'export togolais (y compris ceux d'OEC et de Comtrade,
  qui héritent de la même définition) comme de la production domestique.
- `free_zone_regimes` — quatre lignes du Tableau 83 reprises **verbatim**,
  colonne 2025T4. Elles disent l'essentiel sur l'origine : la zone franche
  industrielle reçoit 100 527,6 et expédie 84 248,9 millions de FCFA. Une zone
  qui importe plus qu'elle n'exporte en valeur transforme des intrants
  étrangers ; ses sorties n'établissent pas à elles seules l'origine
  togolaise au sens ZLECAf.

## Pays examinés et écartés dans le même lot

| Pays | Source visée | Issue | Motif |
|---|---|---|---|
| Maroc (MAR) | Office des Changes | ÉCARTÉ — fond | Les séries publiées (commerce extérieur, balance des paiements, IDE) ne portent pas de ventilation domestique/réexportation. L'analogue marocain est l'admission temporaire, un concept douanier différent : le plaquer sur ce schéma serait une fabrication par analogie. |
| Kenya (KEN) | KNBS | ÉCARTÉ — accès | `www.knbs.or.ke` échoue au handshake TLS depuis ce bac à sable (`unknown CA`), y compris avec le bundle CA du proxy. Ce n'est pas un refus de politique. **À revalider sur un runner** : le KNBS Economic Survey publie bien « Domestic Exports » et « Re-exports », c'est le meilleur candidat restant. |
| Égypte (EGY) | CAPMAS | ÉCARTÉ — accès | La page de statistiques du commerce extérieur renvoie 1 421 octets (coquille JavaScript) ; aucun fichier statique trouvé. |
| Djibouti (DJI) | INSTAD | ÉCARTÉ — accès | Page d'accueil de 4 309 octets (coquille) et tunnel interrompu en cours d'échange. |

Ces quatre pays ne reçoivent **aucun** fichier : un bloc vide serait pire
qu'un bloc absent.

## Règles de preuve

- Les valeurs sont reprises **telles que publiées**, en millions de FCFA
  (`FCFA M`). Aucune conversion en USD, aucun total recomposé.
- Les chiffres de `TGO.json` sont vérifiés caractère par caractère contre le
  texte du PDF (code de régime, libellé, valeur de la colonne 2025T4).
- Un pays portant `export_flow_caveat` ne peut pas porter simultanément
  `top_reexport_markets` : l'un des deux serait faux. Le test
  `test_a_caveat_and_a_published_split_are_mutually_exclusive` le tient.

## Vérifier

```bash
sha256sum data/national_stats/TGO.json
python3 -c "
import sys; sys.path.insert(0, 'backend')
from services import national_official_stats as nos
print(nos.list_covered_countries())
print('\n'.join(nos.grounding_lines('TGO')))"
```

Contrôle de la non-réconciliation du Tableau 83 (nécessite le PDF) :

```bash
curl -sSL -o /tmp/tgo.pdf https://inseed.tg/download/7638/
sha256sum /tmp/tgo.pdf   # e4f2e9e9...fd34
# Tableau 83, pages 120-121 ; Tableau 1, page 13.
```

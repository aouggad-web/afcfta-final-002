# Maurice — registre des sources statistiques nationales

Date de consultation : 2026-09-21. Donnée machine-readable :
`data/national_stats/MUS.json`.

Ce registre suit la même discipline que les registres de sources juridiques du
dépôt (`KEN_SOURCE_REGISTER.md` et suivants) : un éditeur nommé, une
publication datée, une URL, et l'empreinte du fichier servi.

## Sources

| ID | Titre | Éditeur | Année des données | Statut | SHA-256 du fichier servi |
|---|---|---|---|---|---|
| `MUS-EDB-NL-202407` | Newsletter juillet 2024 — Industry Overview | EDB Mauritius (Economic Development Board) | 2023 | COLLECTED | `40a7c561898dc3a919d4c259047250ad66245043456d35710e8ba5a5308e147d` |

URL : https://edbmauritius.org/newsletter2024/july/overview.html

## Ce que cette source apporte, et que les sources internationales n'ont pas

La séparation entre **exportations domestiques** et **réexportations**.

Maurice réexporte massivement depuis ses zones franches. Une marchandise
réexportée **n'acquiert pas l'origine mauricienne** au sens de la ZLECAf :
seule la production ou la transformation domestique peut y prétendre. Confondre
les deux flux ferait recommander un débouché préférentiel auquel la marchandise
n'a pas droit.

Ni OEC, ni UN Comtrade, ni FAOSTAT ne publient cette ventilation. C'est la
raison d'être de cette couche.

## Règles de preuve

- Les valeurs sont reprises **telles que publiées**, dans la monnaie de
  publication — ici en millions de roupies mauriciennes (`MUR Mn`). Aucune
  conversion en USD n'est faite à cette couche : une conversion suppose un taux
  et une date, que la source ne fournit pas.
- Le champ `value` est un nombre dans l'unité déclarée par `source.unit`. Il
  n'est comparable ni entre pays ni à un montant en USD sans conversion
  explicite.
- Un bloc dépourvu d'éditeur, de publication, d'URL, d'année de données ou de
  devise est **refusé au chargement** plutôt que servi à moitié
  (`_REQUIRED_SOURCE_FIELDS`). Un chiffre invérifiable vaut moins qu'un chiffre
  absent : il inspire confiance sans la mériter.
- Les parts (`share_pct`) sont celles publiées par l'éditeur, non recalculées.

## Portée

Ce bloc alimente deux consommateurs :

- `GET /api/countries/{iso3}/official-stats` — restitution directe ;
- l'ancrage factuel du module Opportunités
  (`claude_trade_service._country_opportunity_grounding`), où il pose
  explicitement que les réexportations ne confèrent pas l'origine.

## Vérifier

```bash
sha256sum data/national_stats/MUS.json
python3 -c "
import sys; sys.path.insert(0, 'backend')
from services import national_official_stats as nos
print(nos.list_covered_countries())
print('\n'.join(nos.grounding_lines('MUS')))"
```

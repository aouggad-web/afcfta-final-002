# Données synthétiques — NE PAS INGÉRER

Les fichiers *_tariffs.json déplacés dans ce dossier ont été générés le 2026-03-06
entre 03:53 et 03:55 (2 minutes pour 46 pays = script automatique, pas crawl réel).

## Caractéristiques des données synthétiques détectées

- Exactement 5 831 lignes HS6 par pays
- Codes HS6 identiques au TEC CEMAC (CMR_tariffs.json) pour TOUS les pays
- Seuls les taux de taxes varient (appliqués mécaniquement depuis une source inconnue)
- Ce sont des templates CEMAC avec taux nationaux appliqués — pas des tarifs nationaux réels

## Pays concernés (46)

AGO BDI BEN BFA BWA CIV COD COM CPV DJI ERI ETH GHA GIN GMB GNB KEN LBR LBY LSO
MAR MDG MLI MOZ MRT MUS MWI NAM NER NGA RWA SDN SEN SLE SOM SSD STP SWZ SYC TGO
TUN TZA UGA ZAF ZMB ZWE

## Sources réelles disponibles à utiliser à la place

- CEDEAO (15 membres) : CSV officiel TEC CEDEAO → CedeaoTecAdapter
- EAC (8 membres) : CSV EAC CET → EacCetAdapter (engine/sources/eac_cet_2022.csv)
- SACU (5 membres ZAF NAM BWA SWZ LSO) : PDF SARS → SarsAdapter
- ETH MUS : portails officiels → eth_tariff_adapter / mus_tariff_adapter
- MAR TUN : portails officiels (réseau requis)
- Autres (AGO MOZ MDG DJI ERI SDN...) : PAS de source réelle disponible → ne pas ingérer

## Règle absolue

Un pays sans source officielle traçable n'est pas intégré.
Mieux vaut « données absentes » que « données fausses ».

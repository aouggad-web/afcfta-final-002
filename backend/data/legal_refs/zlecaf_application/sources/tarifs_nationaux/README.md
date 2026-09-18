# Tarifs douaniers nationaux — sources primaires (famille D)

Collecte des tarifs douaniers nationaux **détaillés** (nomenclature nationale
+ taux, droits et accises), publiés par la douane ou l'autorité de recettes de
chaque pays. Objectif : remplacer la donnée WITS/UNCTAD-TRAINS (moyenne SH6) par
le tarif national réel, position par position.

## Règle d'archivage

Les PDF pèsent de 3,6 à 17 Mo : ils ne sont **pas versionnés** dans le dépôt.
Leur **empreinte SHA-256** est consignée dans `MANIFESTE.json` (URL exacte,
institution, année, taille, pages, structure), pour re-téléchargement et
vérification — doctrine « PDF non archivé, empreinte consignée ».

## État de la collecte

| Pays | Année | Pages | Source |
|---|---|---|---|
| MRT | 2021 | 396 | douanes.mr |
| MDG | 2026 | 292 | douanes.gov.mg |
| MOZ | 2026 | 11 (compact) | at.gov.mz (+ XLSX officiel) |
| ZMB | 2026 | 682 | zra.org.zm |
| ZWE | 2025 | 1162 | zimra.co.zw (Cloudflare → archive.org) |
| MUS | 2026 | 807 | mra.mu |
| MWI | 2023-24 | 642 | mra.mw |

À collecter encore : **AGO, COM, SYC, STP, LBY, SDN** (recherche en cours ;
tous formats — PDF, Excel, HTML — sources primaires uniquement, cabinets
Deloitte/PwC en second plan pour localiser le texte officiel).

Voir `MANIFESTE.json` pour les URL exactes et les SHA-256.
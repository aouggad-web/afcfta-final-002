"""
tariff_crawl — pipeline de collecte tarifaire authentique pour les 54 pays ZLECAf.

Principe directeur : **uniquement des données authentiques, avec source**.
Aucune estimation, aucune valeur générée. Quand aucune source authentique n'est
disponible, on l'indique honnêtement plutôt que de fabriquer une valeur.

Ce package est volontairement **autonome** : il ne dépend ni de MongoDB (`motor`)
ni du package `crawlers/` (dont l'`__init__` importe `motor`). Il peut donc tourner
sur n'importe quelle machine disposant d'un accès réseau + secrets, ainsi qu'en
mode `--dry-run` sans réseau (cartographie de couverture).

Modules :
- manifest : source authentique déclarée pour chaque pays (portail national / TEC
  régional / OMC-WITS), dérivée du registre des 54 pays.
- canonical : schéma de sortie canonique + validateur d'authenticité (rejette le
  vide et l'estimé).
- coverage : classe l'état réel des fichiers data/crawled et produit un rapport.
"""

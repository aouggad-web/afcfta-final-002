# P0 calculateur — premier lot

## Problème et correction

Le calcul prioritaire pouvait afficher un droit de sous-position collectée et
calculer avec le taux agrégé d'une ancienne ligne. Les formats liste, dictionnaire
et `taxes_import` sont maintenant traités avec la même priorité. Une position
nationale exacte peut aussi être utilisée lorsqu'elle manque dans le fichier
canonique d'un pays déjà pris en charge. La priorité PostgreSQL est conservée.

Cas de régression : EGY 0207110000 (DD 30 %), TUN 90031100003 (10 %),
TUN 73090090109 (30 %) et DZA 2201101100 (30 %). Ces valeurs sont celles des
fichiers du dépôt ; cette correction ne constitue pas une authentification juridique.

Les taux absents et expressions spécifiques ou composites ne deviennent plus des
zéros ou pourcentages arbitraires. Le calcul complet renvoie
`CALCULATION_UNAVAILABLE`. Les mesures explicitement présentes dans le détail de
la même ligne restent utilisables. L'interface affiche le refus, efface l'ancien
résultat et ne tente le moteur de repli qu'en cas de réponse 404.

Le normaliseur Ghana conserve les 6 129 positions nationales, leurs droits propres
(y compris zéro), et une seule mesure TVA par position. Il conserve les données
brutes de la position et de son parent sans modifier les fichiers collectés.

## Vérification

- Régressions backend : sélection des sources, positions nationales, taux absents,
  calcul algérien, priorité PostgreSQL, préférences ZLECAf, conversion et route Kenya.
- Tests frontend du répertoire `src/components/calculator` et compilation Vite.
- `python scripts/normalize_crawled.py --country GHA` : 6 129 positions, zéro
  anomalie signalée par la vérification du normaliseur.
- Analyse statique Python des erreurs bloquantes et `git diff --check`.

Les tests locaux utilisent un service de change sans accès réseau ; les tests
de conversion injectent leurs propres taux. Ils ne valident pas PostgreSQL en
production. `npm ci` échoue sur le verrouillage existant (dépendances optionnelles
absentes) ; validation locale avec `npm install --package-lock=false --ignore-scripts`.
Le verrouillage n'a pas été modifié dans ce lot.

## Mise en service

Après revue et intégration, régénérer le fichier dérivé Ghana avec
`python scripts/normalize_crawled.py --country GHA`, puis redémarrer les services
qui mettent les données en cache. Le démarrage existant ne régénère pas toujours
un fichier normalisé déjà présent. Aucune mise en production n'est effectuée par
cette PR.

## P0 restant à traiter

- Aligner entièrement les moteurs GET et POST, notamment leurs politiques de TVA.
- Corriger et tester les assiettes propres aux taxes (dont RPD en Tunisie) et les
  mesures spécifiques dépendant d'une quantité ou d'une unité.
- Résoudre les autres écarts de couverture et de données identifiés dans l'audit.

L'authentification pays par pays, l'exhaustivité légale, les formalités et le
contrôle opérationnel de traçabilité ne sont pas certifiés par ce premier lot.

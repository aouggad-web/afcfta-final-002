# Plan de travail — volet Production

## Objectif
Corriger et professionnaliser le volet Production, avec une priorité immédiate sur le sélecteur de pays et l'harmonisation visuelle des sous-volets Macro, Agriculture, Manufacturing et Mining.

## Diagnostic
- Le sélecteur pays casse la charte dark.
- Le dropdown blanc donne l'impression d'un composant importé.
- La section grandes économies prend trop de place.
- Les sous-volets Production ne sont pas encore totalement homogènes.

## Périmètre
- `frontend/src/components/production/EnhancedCountrySelector.jsx`
- `frontend/src/components/production/ProductionMacro.jsx`
- `frontend/src/components/production/ProductionAgriculture.jsx`
- `frontend/src/components/production/ProductionManufacturing.jsx`
- `frontend/src/components/production/ProductionMining.jsx`

## Plan de travail

### Phase 1 — Sélecteur pays
- passer le trigger en style dark natif
- passer le dropdown en surface dark premium
- réduire la hauteur perçue du panneau
- compacter la zone grandes économies
- harmoniser les états hover / selected / active
- vérifier le portail, le scroll et la fermeture

### Phase 2 — ProductionMacro
- harmoniser le header du sous-volet
- mieux intégrer la zone filtre + sélecteur
- homogénéiser les cartes de graphiques
- améliorer la lisibilité des titres et détails

### Phase 3 — Propagation
- appliquer le même standard à Agriculture
- appliquer le même standard à Manufacturing
- appliquer le même standard à Mining
- uniformiser la structure écran : header, filtres, graphiques, détails

### Phase 4 — QA
- desktop
- responsive
- recherche pays
- clear sélection
- dropdown au-dessus des graphiques
- cohérence visuelle entre les 4 sous-volets

## Critères d'acceptation
- plus aucun panneau blanc hors charte
- sélecteur pays cohérent avec le thème dark
- hiérarchie visuelle plus claire
- expérience homogène sur tous les sous-volets Production

## Ordre d'exécution
1. `EnhancedCountrySelector.jsx`
2. `ProductionMacro.jsx`
3. `ProductionAgriculture.jsx`
4. `ProductionManufacturing.jsx`
5. `ProductionMining.jsx`
6. QA finale

## Suite recommandée
Après Production, enchaîner sur :
1. Statistics
2. Dashboard / News
3. Banking
4. Rules of Origin
5. Opportunities / Country Profiles

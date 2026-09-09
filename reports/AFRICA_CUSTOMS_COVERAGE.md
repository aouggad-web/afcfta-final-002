# Couverture douanière Afrique — modèle régional/national

État au 2026-07-24. Ce tableau décrit la disponibilité et la qualité des
sources ; il ne constitue pas un tarif et ne crée aucun taux.

- Pays couverts : **54** / 54.
- Fichiers tarifaires locaux présents : **54**, tous classés
  `AVAILABLE_UNVERIFIED` jusqu’à validation juridique.
- Pays rattachés à un territoire douanier daté dans le modèle Wave 1 :
  **10**.
- SH6 complets juridiquement calculables dans cette vague : **0**.
- Confiance globale initiale : **0 %** ; un résultat peut être
  `VERIFIED_PARTIAL` lorsqu’une ligne et une source précise sont établies.

## Lecture par pays

Les 54 fiches détaillées sont dans
`data/coverage/africa_country_coverage.json`. Les champs obligatoires sont
séparés : tarif de base, version SH et année, union douanière, taxes nationales,
gazettes, préférence ZLECAf, réciprocité, origine, formalités, SH6 complets ou
partiels et prochaine action. `SOURCE_PENDING` signifie qu’aucun taux ne doit
être émis.

## État régional

- EAC : Kenya, Ouganda, Tanzanie, Rwanda et Burundi disposent d’une adhésion
  datée dans le modèle Wave 1 ; la couverture des gazettes EAC reste partielle.
- SACU : les cinq membres disposent d’une référence CET datée ; la fiscalité
  nationale reste distincte.
- CEMAC/UEMOA : priorités de collecte, sans extrapolation de taux dans ce
  registre.
- COMESA/SADC : affiliations présentes uniquement lorsqu’elles sont marquées
  vérifiables ; les affiliations en attente ne sélectionnent pas un CET.

## Prochaines actions prioritaires

1. Acquérir les gazettes EAC et les listes de remissions/stays applicables au
   Kenya, puis relier les codes HS6 sans recopier la gazette par pays.
2. Valider les dates d’adhésion et les tarifs SACU/EAC pour chaque membre.
3. Acquérir les TEC CEMAC/UEMOA/ECOWAS/COMESA/SADC et leurs exceptions.
4. Collecter séparément VAT, excises, prélèvements, formalités et exemptions
   nationaux.
5. Documenter préférence ZLECAf, réciprocité et règles d’origine pour chaque
   couple importateur/exportateur.

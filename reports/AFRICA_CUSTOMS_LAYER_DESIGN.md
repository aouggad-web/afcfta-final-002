# Couche douanière commune régionale + couche nationale

État : modèle générique ajouté, collecte multipays encore progressive. Les
fichiers de tarifs existants n’ont pas été réécrits et aucun taux nouveau n’est
présenté comme vérifié.

## Schéma proposé

`engine/schemas/customs_territory.py` porte les entités suivantes :

- `CustomsTerritory` et `TerritoryMembership` (adhésions datées, statut de mise en œuvre et source) ;
- `RegionalTariff` et `NationalTariff` (tarif commun puis code national) ;
- `RegionalLegalOverride` et `NationalLegalOverride` (portée, bénéficiaire, origine, usage, autorisation et dates) ;
- `PreferentialRegime`, `ReciprocityStatus` et `OriginRule` ;
- `NationalTax` et `AdministrativeFormality` ;
- `HsConcordance` (HS6 OMD → HS6 cible → code national, version, confiance et dates) ;
- `CountryCoveragePeriod` pour la couverture par pays et période.

Une gazette régionale est référencée une seule fois dans
`data/eac/legal_overrides.json`; les pays applicables sont une portée de la
mesure ou une relation d’adhésion datée. Aucune copie par État n’est créée.

## Moteur

`engine/import_charges.py` expose :

```text
calculate_import_charges(
    importing_country, exporting_country, hs6, national_code=None,
    customs_value=None, calculation_date=None, importer_profile=None,
    intended_use=None, authorizations=None
)
```

Les fournisseurs injectés séparent :

1. territoire douanier effectif à la date ;
2. tarif régional ou tarif national ;
3. overrides régionaux ;
4. overrides nationaux ;
5. préférence, réciprocité et origine ;
6. taxes nationales et formalités.

Une priorité de territoire non résolue, une date manquante, une condition
inconnue ou une source absente donne `VERIFIED_PARTIAL` (ou
`CONFLICT_REVIEW` en cas de conflit), jamais un choix silencieux.

`engine/kenya_customs_calculation.py` reste la façade de compatibilité mais
adapte désormais ses tables Kenya au moteur partagé. Les clés historiques
(`vat`, `excise`, `idf`, `rdl`) sont conservées dans la réponse.

## Composants Kenya encore codés en dur

- `KenyaFiscalStore` charge les tables VAT/excise/levies Kenya : c’est la
  couche nationale injectée, pas une logique de calcul régionale ;
- le service backend charge `data/eac/legal_overrides.json` et le registre EAC ;
- `engine/adapters/eac_cet_adapter.py` conserve un mode historique où VAT/IDF/RDL
  sont ajoutés aux lignes EAC ; le chemin générique les traite séparément ;
- le resolver conserve les valeurs par défaut `KEN`/`EAC` uniquement pour la
  compatibilité des appels historiques ; les nouveaux appels doivent fournir
  le pays et la liste de blocs ;
- la route `/authentic-tariffs/calculate` garde le champ Kenya historique.

Aucune valeur Kenya n’est propagée automatiquement à un autre pays.

## Migration sans régression

- conserver les adaptateurs canoniques et leurs sources validées ;
- introduire progressivement des fournisseurs régionaux communs et des
  fournisseurs fiscaux ISO3 ;
- enregistrer chaque adhésion avec `valid_from`/`valid_to` et ne jamais
  extrapoler l’état actuel vers une date historique ;
- faire passer les nouveaux calculs par `calculate_import_charges` ;
- garder la façade Kenya et les alias de réponse jusqu’à migration des clients ;
- ne modifier un taux existant qu’avec une source juridique plus récente et
  hachée.

## Priorités de collecte

1. Kenya/EAC (gazettes, stays, remissions et EACCMA 2025) ;
2. autres membres EAC et SACU, car la base régionale peut être mutualisée ;
3. CEMAC et UEMOA/TEC, puis ECOWAS, COMESA et SADC ;
4. tarifs nationaux hors union douanière (Algérie, Maroc, Tunisie, Égypte, etc.) ;
5. formalités, réciprocité, origines et préférences ZLECAf pays par pays.

## Risques de doublons entre unions

- un pays peut appartenir à une union douanière et à une zone de libre-échange ;
- une union douanière doit gagner uniquement si elle est active à la date et
  si sa priorité tarifaire est unique ;
- une adhésion `PENDING_VERIFICATION` ne sélectionne aucun tarif ;
- une gazette commune ne doit pas être copiée dans les fichiers nationaux ;
- un code national (8/10/12 chiffres) ne peut être transféré à un autre pays
  sans `HsConcordance` datée et une source du pays cible.

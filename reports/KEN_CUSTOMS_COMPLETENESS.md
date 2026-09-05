# Kenya customs legal-overlay completeness

**État au 24 juillet 2026 — corpus incomplet, calcul complet non autorisé.**

## Lacunes constatées avant modification

L’inspection a montré que le modèle canonique v4 représentait les taux et leur séquence, mais pas leur période d’effet ni les conditions d’une dérogation. `engine/calculation.py` appliquait les mesures par ordre numérique sans comparer date, origine, bénéficiaire, usage ou quantité. L’adaptateur EAC chargeait un CET de base sans registre de gazettes, sans stays/remissions datés et sans détection de conflit. Les fichiers Kenya validés étaient séparés du calcul historique. Aucun mécanisme d’overlay juridique, aucun statut `CONFLICT_REVIEW` et aucune trace consolidée CET → override → taxes nationales n’existaient.

Lors de l’inspection initiale, le HEAD local ne contenait que la table
`commodities`, les index HS6 générés et `search_tariff_lines`. L’index
alphabétique OMD retrouvé ensuite dans le commit `9fdb130e` est désormais
intégré comme source unique de candidats, sans corpus parallèle. Les notes de
section, chapitre et sous-position restent absentes, et le contenu PostgreSQL
runtime n’était pas accessible pendant la collecte.

## Couche ajoutée

- Schéma daté et conditionnel pour les huit types de mesure demandés.
- Résolution par date, code/listes SH, territoire, origine, bénéficiaire, usage et quantité.
- Priorité juridique par étapes, sans application d’une mesure conditionnelle lorsque les faits manquent.
- Conflits de taux au même niveau renvoyés en `CONFLICT_REVIEW`.
- `VERIFIED_PARTIAL` irréversible tant que la couverture des gazettes reste incomplète.
- Trace du CET de base, de l’override, des droits, de la VAT, des excises, de l’IDF, du RDL et des autres prélèvements établis.
- File produit–SH séparée : un index hit n’est jamais l’unique base juridique et un mapping inférieur à 90, multiple, incompatible de version ou en revue ne peut pas être appliqué.

## Gazettes intégrées

| Gazette | Statut | Période couverte par les lignes | Extraction Kenya |
|---|---|---:|---:|
| EAC Vol. AT 1 No. 19, 30-06-2025 | PDF officiel archivé et haché | 01-07-2025 – 30-06-2026 | partielle, priorité Kenya |
| EAC Vol. AT 1 No. 26, 14-08-2025 | PDF officiel archivé et haché | corrigenda 2025 | revue, aucune ligne Kenya ajoutée |
| EAC Vol. AT 1 No. 16, 30-06-2026 | PDF officiel archivé et haché | 01-07-2026 – 30-06-2027 | partielle, priorité Kenya |

Le registre contient les URL officielles, chemins d’archive, statuts d’accès/extraction/validation, empreintes SHA-256 et nombres de lignes extraites. Il ne déclare jamais la couverture complète.

## Mesures et codes couverts

- 17 overlays structurés, 24 codes tarifaires directs distincts sur l’historique chargé.
- 12 overlays en vigueur au 24-07-2026, couvrant 15 codes directs distincts.
- Stays 2025 expirés : 6309.00.10; 8701.21.90, 8701.22.90, 8701.23.90, 8701.24.90, 8701.29.90; 8716.31.90, 8716.39.90 et 8716.40.90.
- Remissions 2026 conditionnelles : 1001.99.10/90; 8308.10.00; 8308.20.00; 3402.90.00; 3210.00.10; 3208.90.10; 3209.90.90; 8425.11.00; 8425.19.00; 8431.39.00; 4408.90.00; 4411.12.00; 7608.20.00; 3909.50.00.
- Le stay 6309.00.10 utilise un taux mixte « 35 % ou USD 0,20/kg, le plus élevé » : aucun taux ad valorem simplifié n’est appliqué sans poids et calcul de la branche spécifique.

## Descriptions sans code SH

Six descriptions Kenya ont été extraites séparément, trois dans chaque gazette annuelle : inputs pour appareils de télécommunication intelligents, matières premières pour aliments pour animaux, et composants de salles propres pharmaceutiques.

| Indicateur | Nombre |
|---|---:|
| Descriptions extraites | 6 |
| Correspondances exactes d’index | 0 |
| SH6 validés | 0 |
| Candidats multiples enregistrés | 0 |
| Cas dépendant de l’usage (`END_USE_MEASURE`) | 6 |
| Cas à revoir | 6 |
| Mappings intégrés automatiquement au moteur | 0 |

Ces expressions désignent des ensembles de marchandises par destination et bénéficiaire. Leur affecter un seul SH6 ferait perdre des qualificatifs essentiels. La file de revue conserve matière, fonction, usage, secteur, bénéficiaire, destination, termes de recherche, conditions, score et actions `VALIDATE`, `REJECT`, `SELECT_OTHER_HS6`.

## Couverture calculable

Le tarif Kenya existant annonce 5 984 positions. Au 24-07-2026 :

- **calculable complètement : 0 %** — aucune position ne peut recevoir `VERIFIED_COMPLETE` puisque le registre des gazettes est incomplet ;
- **calculable partiellement : 100 % au niveau moteur** si une ligne CET datée est fournie, car le moteur conserve le résultat établi et signale la lacune des gazettes ;
- **couverture directe des overlays actuels : 15 / 5 984, soit 0,25 %** ; ce ratio mesure les codes d’overrides extraits, pas la complétude juridique du tarif.

## Sources et mesures encore bloquantes, par priorité

1. Corpus exhaustif des gazettes EAC applicables au Kenya entre la date du CET cible et le 24-07-2026, y compris tous corrigenda.
2. Extraction complète des Legal Notices EAC/161/2026 à EAC/171/2026, en particulier les annexes Kenya de vêtements/textiles.
3. Gazette et texte complet de l’amendement EACCMA 2025 entré en vigueur le 26-09-2025 (`SOURCE_PENDING`).
4. Stays ponctuels et modifications CET publiés hors des deux numéros annuels intégrés.
5. Listes de bénéficiaires, allocations quantitatives et autorisations administratives des duty remission schemes.
6. Dérogations et exemptions nationales Kenya, ainsi que leurs instruments d’exécution, non encore reliées aux codes SH.
7. Preuve de licence/provenance OMD et notes légales nécessaires à la validation SH6 ; l’index runtime est intégré, mais ne classe pas les six descriptions génériques.

Tant que ces lacunes subsistent, le total retourné ne doit pas être utilisé pour une déclaration en douane.

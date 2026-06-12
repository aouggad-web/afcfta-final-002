# Sources tarifaires — fichiers bruts

Ce répertoire accueille les fichiers sources officiels (Excel/CSV/PDF) utilisés
par les adaptateurs de `engine/adapters/`. **Les fichiers bruts ne sont pas
versionnés** (voir `.gitignore`) — seul ce README, qui trace leur origine,
l'est.

## Convention

Pour chaque fichier déposé ici, ajouter une entrée au tableau ci-dessous avec
l'URL d'origine, la date de téléchargement et le hash SHA256
(`sha256sum <fichier>`), afin que toute personne puisse re-télécharger et
vérifier la même version.

| Fichier | Source | URL | Téléchargé le | SHA256 |
|---------|--------|-----|---------------|--------|
| `civ_tec_cedeao_enrichi_27032026.md` | Douanes CIV — TEC CEDEAO 2022 enrichi des droits et taxes nationaux (SYDAM WORLD, MAJ 27/03/2026) | https://www.douanes.ci/info/tec | 2026-06-12 | `0ccc5e078c84b56d551ee604f424a317ef9ad1b2515f06faaa1f92eb5dc05b8a` |

## TEC CEDEAO — préparation du fichier

1. Télécharger le TEC officiel depuis le portail TEC des douanes ivoiriennes
   (https://www.douanes.ci/info/tec — 6 381 lignes SH10, droits + taxes
   nationales) ou auprès d'une autre source officielle :
   - ECOTIS — Commission CEDEAO : https://ecotis.projects.ecowas.int
   - DGD Sénégal : https://www.douanes.sn/ndn723/
   - DGD Bénin : https://douanes.gouv.bj/tarif-exterieur-commun-tec-cedeao-2022/
2. Exporter la feuille principale en CSV (UTF-8, délimiteur `;` ou `,`).
   Colonnes minimales attendues par `cedeao_tec_adapter.py` :
   - **Code** (`Code_SH` / `HS Code` / `NTS`) — 8 ou 10 chiffres, points tolérés
   - **Désignation** (`Designation` / `Description`)
   - **Catégorie** (`Categorie` / `Category`) — bande 0-4, **ou** une colonne
     de taux (`DD` / `Duty Rate`)
   - *(optionnel)* **Unité** (`Unite` / `SU`)
3. Lancer l'adaptateur :
   ```bash
   python engine/adapters/cedeao_tec_adapter.py \
       engine/sources/cedeao_tec_2022.csv \
       engine/output \
       --version-date 2022-01-01
   ```
   → écrit un `{ISO3}_canonical.jsonl` PARTIAL/B pour chacun des 15 membres.
4. Regénérer le registre de statut :
   ```bash
   python engine/scripts/mark_synthetic.py
   cp engine/output/DATA_STATUS.json frontend/public/data/
   ```

## Échantillon de validation

`engine/tests/fixtures/cedeao_tec_sample.csv` est un échantillon synthétique
de 6 lignes couvrant les 5 bandes du TEC — utilisé par
`engine/tests/test_cedeao_tec_adapter.py`. Ce n'est **pas** le TEC réel.

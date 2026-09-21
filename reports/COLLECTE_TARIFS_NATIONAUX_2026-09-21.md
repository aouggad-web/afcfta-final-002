# Collecte des tarifs nationaux — Comores, Madagascar, Soudan, São Tomé-et-Príncipe

_État au 2026-09-21 (rév. 2, après revue). Doctrine : aucun taux inventé, moyenné
ou repris d'un voisin ; une source introuvable est déclarée, jamais remplacée._

## Madagascar — LIVRÉ

| Élément | Valeur |
|---|---|
| Fichier runtime | `backend/data/crawled/MDG_tariffs.json` (scellé) |
| Source | Tarif des douanes, édition 2026 (basé sur le SH 2022), MAJ LFR 2026 |
| URL | https://www.douanes.gov.mg/srcs/uploads/2026/07/TARIF-DES-DOUANES-2026-MAJ-LFR.pdf |
| SHA-256 du PDF | `9f26e514d5bbbb69e3c45082b49694bb39378c983a975568a46490c02b326e5f` |
| SHA-256 du JSON | `fad20f649681ae5a7be2abaac4a9fac73d2cf3264a96e6e7c86837d86650eec7` |
| Positions | **6 544** sous-positions nationales à 8 chiffres (92 chapitres) |
| Colonnes | `DD`, `TVA` (par position), colonne préférentielle `DD APEi` (APE intérimaire, UE) |
| Parseur | `scripts/parse_tarif_mdg_2026.py` (en-têtes de colonnes + accumulation des lignes repliées) |
| Positions écartées | **343**, toutes énumérées dans `non_collected` (motif + page) et résumées dans `non_collected_summary` |

TVA publiées : 20 % (6 259), exonéré (283), réduits **5 %** (`10063010`, riz RL1/RL2)
et **10 %** (`73110000`, récipients à gaz) — vérifiés sur le PDF, ce sont des taux
publiés, pas des cellules mal lues. Aucune TVA `null`.

Écarté et déclaré (jamais deviné) : sous-tables à schéma non univoque —
colonnes `TPP`/`TVP` à droits **spécifiques** en Ariary/litre ou Ariary/kg-net
(notes (1*)/(2*)), colonnes `DS`, et lignes au DD illisible. 343 positions au
total (chapitres 24-27, 29, 48, 69, 71, 75, 81, 84, 87).

**Assiettes établies sur texte primaire** (fiches + extraits archivés + SHA-256) :

| Prélèvement | Article | Assiette | Extrait archivé (SHA-256) |
|---|---|---|---|
| Droit de douane | Code des douanes (Loi n° 2006-023 après LFI 2026), **art. 23 §1 et §4 c)** | `CIF` | `MDG_assiette_droit_de_douane.texte-extrait.txt` → `9677eecd…d0c928` |
| TVA import | CGI éd. 2025, **art. 06.01.11** | `CIF+TOUS_SAUF_TVA` | `MDG_assiette_TVA.texte-extrait.txt` → `b4ca5a48…220848f` |
| Accises, sortie, navigation, autres droits, redevance informatique | Code des douanes **Titre IX (art. 257-265)** + art. 2-3, 9, 16 | ad valorem (valeur) ou spécifique (quantité/tonnage) ; redevance = forfait | `MDG_titre_IX_taxes_diverses.texte-extrait.txt` → `5d038ed5…7b5c3a` ; `MDG_droits_et_taxes_base_art2_3_9_16.texte-extrait.txt` → `8c8cced2…ff1935` |

Fiches : `backend/data/legal_refs/zlecaf_application/MDG_assiette_droit_de_douane_2026-09-21.json`,
`MDG_assiette_TVA_2026-09-21.json`, `MDG_cascade_droits_et_taxes_2026-09-21.json`.

Socle : `build_socle.py MDG` → **6 544 positions, 13 088 droits, état COMPLET,
0 taux et 0 assiette indisponibles**. Registres alignés :
`source_registry_v2.json` (® `artifact_url` = null, l'artefact n'étant pas le PDF),
`data/madagascar/legal_sources.json`, `backend/socle/MANIFESTE.json`,
`backend/socle/assiettes_pays.json` (origine `texte_primaire`),
`ASSIETTE_TVA_ETABLIE["MDG"]` (chemin de reconstruction),
`normalize_wits_dict` (préserve `preferential_rates`).

### Correctifs issus de la revue

- **TVA `null` (5 positions)** : c'étaient des **erreurs de lecture**, pas des
  cellules vides. Une désignation repliée repousse la TVA sur la ligne suivante ;
  le parseur finalisait trop tôt. Corrigé : `4010.31–34` → TVA 20 %,
  `8423.81` → TVA 20 %.
- **Chapitres perdus** : un en-tête non strictement `UQN DD TVA APEi` désactivait
  toute la table. On accepte désormais `UQN DD TVA` (APEi optionnel) ; le
  chapitre 50 et la sous-table 27.12 sont récupérés. Les schémas réellement non
  univoques (`TPP`/`TVP`/`DS`) restent écartés mais sont **énumérés**.
- **Déclaration** : `non_collected` + `non_collected_summary` remplacent le
  décompte erroné « 4 positions ».
- **Reconstruction** : `ASSIETTE_TVA_ETABLIE["MDG"]` empêche `build_socle` de
  retomber sur `CIF+DD` si `assiettes_pays.json` était régénéré.
- **Normaleur** : `normalize_wits_dict` ne jette plus `preferential_rates`
  (6 483 positions APEi exposées, contre 0).
- **`artifact_url`** : ne pointe plus le PDF (le champ attend une copie du JSON).

## Comores — NON PUBLIÉ (preuve négative)

Le portail officiel `douane.gov.km` publie une page « Taxes douanières » qui
**renvoie à la consultation des services de l'administration** et n'expose aucun
taux : « Pour connaître les taux exacts et les conditions d'application,
veuillez contacter nos services ». Assiettes déjà sur texte primaire : DD = `CIF`
(Code des douanes, art. 36 et 40.1 e) ; TVA = `CIF+TOUS_SAUF_TVA` (CGI éd. 2023,
art. 140 4°).

## Soudan — NON DISPONIBLE (preuve négative)

Le portail officiel `web.customs.gov.sd` publie une page « التعريفة الجمركية »
dont le lien de téléchargement du livre complet
(`/wp-content/uploads/2013/01/At-Tryft-Arba-Kamlh.pdf`) répond **HTTP 404**. Le
pays reste servi comme base statistique ; aucune assiette n'est établie.

## São Tomé-et-Príncipe — PÉRIMÉ (preuve négative)

La pauta en vigueur est le **Decreto-lei n.° 14/2023 de 30 de Novembro** (HS
2022), **non publiée** : `aga.st` est une application JavaScript sans document
téléchargeable, `financas.gov.st` renvoie 403. Une copie **non datée** circule
sur un portail tiers (SHA-256 `2f2dc1df…`) : non retenue comme tarif courant.
La TVA est correctement sourcée (Lei 13/2019, art. 15.º).

## Contrôles

- `scripts/verifier_fiche.py --toutes` : 0 anomalie.
- `test_verifier_fiche.py`, `test_zlecaf_legal_sources.py`,
  `test_dataset_hash_stores_agree.py`, `test_national_tax_completion.py` :
  **157 passés, 74 ignorés**.
- `normalize_crawled.py --country MDG` + `build_socle.py MDG` : reconstruits.
- Calculateur : `npf.etat = COMPLET` sur `01012100`, `10063010`, `40103100`,
  `84238100`, `73110000`.

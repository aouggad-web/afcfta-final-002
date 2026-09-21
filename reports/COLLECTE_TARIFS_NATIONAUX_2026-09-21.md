# Collecte des tarifs nationaux — Comores, Madagascar, Soudan, São Tomé-et-Príncipe

_État au 2026-09-21. Doctrine : aucun taux inventé, moyenné ou repris d'un
voisin ; une source introuvable est déclarée, jamais remplacée._

## Madagascar — LIVRÉ

| Élément | Valeur |
|---|---|
| Fichier runtime | `backend/data/crawled/MDG_tariffs.json` (scellé) |
| Source | Tarif des douanes, édition 2026 (basé sur le SH 2022), MAJ LFR 2026 |
| URL | https://www.douanes.gov.mg/srcs/uploads/2026/07/TARIF-DES-DOUANES-2026-MAJ-LFR.pdf |
| SHA-256 du PDF | `9f26e514d5bbbb69e3c45082b49694bb39378c983a975568a46490c02b326e5f` |
| SHA-256 du JSON | `f63c40e969ffa8e6349d12b28a7f371c7fb5e7684216b99fa8a4a45f7047e78a` |
| Positions | **6 527** sous-positions nationales à 8 chiffres (90 chapitres) |
| Colonnes | `DD`, `TVA` (par position), colonne préférentielle `DD APEi` (APE intérimaire, UE) |
| Parseur | `scripts/parse_tarif_mdg_2026.py` (lecture par en-têtes de colonnes) |
| Positions écartées | 4, déclarées dans `non_collected` (schéma de colonnes non univoque — p. 63, 89, 141) |
| Écarté par conception | sous-tables pétrolières (colonnes TPP/TVP à droits **spécifiques** en Ariary/litre ou Ariary/kg-net, notes (1*)/(2*)) et sous-tables à colonne `DS` : schéma non univoque, non deviné |

**Assiettes établies sur texte primaire** (fiches + extraits archivés + SHA-256) :

| Prélèvement | Article | Assiette | Extrait archivé (SHA-256) |
|---|---|---|---|
| Droit de douane | Code des douanes (Loi n° 2006-023 après LFI 2026), **art. 23 §1 et §4 c)** | `CIF` | `MDG_assiette_droit_de_douane.texte-extrait.txt` → `9677eecd…d0c928` |
| TVA import | CGI éd. 2025, **art. 06.01.11** | `CIF+TOUS_SAUF_TVA` | `MDG_assiette_TVA.texte-extrait.txt` → `b4ca5a48…220848f` |
| Accises, sortie, navigation, autres droits, redevance informatique | Code des douanes **Titre IX (art. 257-265)** + art. 2-3, 9, 16 | ad valorem (valeur) ou spécifique (quantité/tonnage) ; redevance = forfait | `MDG_titre_IX_taxes_diverses.texte-extrait.txt` → `5d038ed5…7b5c3a` ; `MDG_droits_et_taxes_base_art2_3_9_16.texte-extrait.txt` → `8c8cced2…ff1935` |

Fiches : `backend/data/legal_refs/zlecaf_application/MDG_assiette_droit_de_douane_2026-09-21.json`,
`MDG_assiette_TVA_2026-09-21.json`, `MDG_cascade_droits_et_taxes_2026-09-21.json`
(les trois passent `scripts/verifier_fiche.py`).

Socle : `build_socle.py MDG` → 6 527 positions, 13 054 droits, **0 assiette
indisponible**, 5 taux indisponibles (TVA laissée vide par le tarif sur
5 positions, déclarée). Registres alignés : `source_registry_v2.json`,
`data/madagascar/legal_sources.json`, `backend/socle/MANIFESTE.json`,
`backend/socle/assiettes_pays.json` (origine `texte_primaire`).

## Comores — NON PUBLIÉ (preuve négative)

Le portail officiel `douane.gov.km` publie une page « Taxes douanières » qui
**renvoie à la consultation des services de l'administration** et n'expose aucun
taux : « Pour connaître les taux exacts et les conditions d'application,
veuillez contacter nos services ». Aucune grille nationale complète n'est donc
publiée en ligne (elle l'était déjà signalée). Les assiettes, elles, tiennent
sur texte primaire : DD = `CIF` (Code des douanes, art. 36 et 40.1 e) ; TVA =
`CIF+TOUS_SAUF_TVA` (CGI éd. 2023, art. 140 4°) — fiches existantes.

**Reste** : obtenir la grille auprès de la DGD comorienne (contact
`dsallaoui@douane.gov.km`) ou une copie datée du tarif.

## Soudan — NON DISPONIBLE (preuve négative)

Le portail officiel `web.customs.gov.sd` publie une page « التعريفة الجمركية »
dont le lien de téléchargement du livre complet
(`/wp-content/uploads/2013/01/At-Tryft-Arba-Kamlh.pdf`) répond **HTTP 404**.
Les pages par section existent mais renvoient des listes sans la table des
droits. Aucune assiette (droit de douane ni taxe intérieure) n'est établie sur
texte primaire accessible ; le pays reste servi comme base statistique.

**Reste** : copie datée du tarif auprès de la Sudan Customs Force, et texte
primaire de la Sales Tax / VAT. Contexte de conflit depuis 2023 : fiabilité à
marquer.

## São Tomé-et-Príncipe — PÉRIMÉ (preuve négative)

La pauta en vigueur est le **Decreto-lei n.° 14/2023 de 30 de Novembro** (HS
2022). Elle **n'est pas publiée** : le site officiel `aga.st` est une
application JavaScript sans document téléchargeable, et `financas.gov.st`
renvoie 403. Seule une copie **non datée** circule sur un portail tiers
(`portaldocomercio.leadershipbt.com`, PDF de 457 pages, SHA-256
`2f2dc1df458c3cccee4b9f4155a1fe54ffd96c5880742ef74034f2a4170bc4b3`) : elle
n'est pas retenue comme tarif national courant, faute de date et d'autorité.
La TVA est, elle, correctement sourcée (Lei 13/2019, art. 15.º).

**Reste** : obtenir la pauta 14/2023 auprès de l'Autorité générale aduaneira, et
le texte douanier primaire fixant l'assiette du droit (`origine_assiette`
encore `profil_code` dans le socle).

## Contrôles

- `scripts/verifier_fiche.py --toutes` : 0 anomalie (33 fiches établissant une valeur).
- `test_verifier_fiche.py`, `test_zlecaf_legal_sources.py`,
  `test_dataset_hash_stores_agree.py`, `test_national_tax_completion.py` :
  157 passés, 74 ignorés.
- `normalize_crawled.py --country MDG` + `build_socle.py MDG` : reconstruits.

# Tunisie — collecte de provenance (calculateur douanier pilote)

Consultation : 2026-07-26.

Chantier de consolidation du calculateur douanier ZLECAf (audit
`audits/AUDIT_DIFFERENTIEL_PILOTES_2026-07-26.md`). La Tunisie fait partie des
6 pays pilotes. `backend/data/tariffs/TUN_tariffs.json` (17512 lignes, source
déclarée `douane.gov.tn/tarifweb2025`) reste la donnée de production, mais ce
portail est **inaccessible en connexion sécurisée** depuis cet environnement
(certificat TLS invalide côté serveur, pas un problème de proxy — voir
`inventory.csv`). Aucun contournement de la vérification TLS n'a été tenté.

## Ce qui a été archivé

- **Loi de Finances 2026** (Loi n°17 de l'année 2025, 12 décembre 2025) :
  téléchargée directement depuis `finances.gov.tn` (portail HTTPS valide,
  domaine distinct de `douane.gov.tn`). 101 pages, texte en arabe. SHA-256
  consigné dans `inventory.csv`.

## Ce qui n'est PAS couvert

- Le barème douanier ligne à ligne (Tarif des douanes tunisien, hébergé sur
  `douane.gov.tn/tarifweb2025`) : **non archivé**, portail inaccessible en
  HTTPS sécurisé. `backend/data/tariffs/TUN_tariffs.json` reste la seule
  source disponible pour les 17512 lignes, sans preuve archivée
  fraîche vérifiable dans cette itération.
- Aucune extraction de taux individuel n'a été faite depuis la Loi de
  Finances 2026 archivée — le document est une preuve de contexte légal
  daté, pas encore une source de taux exploitée ligne par ligne.

## Résultat des tests d'accès

| Source | Résultat |
|---|---|
| `https://www.finances.gov.tn` | HTTP 301 → `https://www.finances.gov.tn/fr`, HTTP 200 |
| `https://www.finances.gov.tn/sites/default/files/2026-01/115725.pdf` | HTTP 200, PDF valide (101 pages) |
| `https://www.douane.gov.tn` | Échec TLS : `unable to get local issuer certificate` (certificat serveur invalide, confirmé par diagnostic `curl -v` — le tunnel proxy s'établit, c'est le certificat présenté par douane.gov.tn qui est rejeté) |
| `https://www.iort.gov.tn` (Journal Officiel) | Connexion réinitialisée (`Recv failure: Connection reset by peer`) |
| `https://www.legislation.tn` | Idem |

## État de l'enregistrement

Aucun changement de comportement du calculateur : cette collecte documente
la provenance, elle n'active ni ne modifie aucune donnée tarifaire servie
par l'API.

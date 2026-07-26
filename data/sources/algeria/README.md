# Algérie — collecte de provenance (calculateur douanier pilote)

Consultation : 2026-07-26.

Chantier de consolidation du calculateur douanier ZLECAf (audit
`audits/AUDIT_DIFFERENTIEL_PILOTES_2026-07-26.md`). L'Algérie fait partie
des 6 pays pilotes.

## Source de données de production

`backend/data/crawled/DZA_tariffs.json` (17061 lignes, source
`conformepro.dz`) reste la donnée de production. L'audit initial avait classé
cette source comme agrégateur commercial (niveau 3 de la hiérarchie des
sources du prompt maître). **Le porteur du produit a explicitement confirmé
accepter cette source comme légitime** — aucune action supplémentaire n'est
requise sur ce point.

## Tentative d'archivage complémentaire (dette ZLECAf niveau 2)

Une dette documentaire distincte, déjà identifiée avant cet audit, restait
ouverte : `backend/services/zlecaf_schedule_dza.py` applique les règles de
démantèlement ZLECAf d'une circulaire nommée en commentaire de code
(« Circulaire DGD n°482/DGD/SP/D.042/24 du 22/10/2024 ») **sans qu'aucun
fichier source ne soit archivé ni haché**.

Résultat de cette itération : **circulaire non trouvée, non archivée.**

- Le portail officiel `douane.gov.dz` est inaccessible : certificat TLS
  invalide côté serveur (même diagnostic que pour `douane.gov.tn`, confirmé
  par `curl -v` — le proxy établit le tunnel, c'est le certificat présenté
  par le serveur cible qui est rejeté). Aucun contournement tenté.
- Les circulaires administratives internes de ce type (instructions de la
  Direction Générale des Douanes aux services, par opposition aux lois et
  décrets publiés au Journal Officiel) ne sont généralement pas publiées
  sur des portails publics indexables.

Voir `inventory.csv` pour le détail complet.

## Ce qui manque pour compléter cette collecte

Un accès fonctionnel à `douane.gov.dz` (ou une republication officielle
alternative de la circulaire 482/2024) serait nécessaire pour combler cette
dette documentaire. Le code applique déjà les règles de cette circulaire
sans preuve archivée — c'est un écart de traçabilité qui reste ouvert,
distinct du choix déjà validé sur la source des données tarifaires elles-mêmes.

## État de l'enregistrement

Aucun changement de comportement du calculateur : aucune donnée tarifaire
ni règle de démantèlement modifiée dans cette itération.

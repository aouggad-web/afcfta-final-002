# Maroc — collecte de provenance (calculateur douanier pilote)

Consultation : 2026-07-26.

Chantier de consolidation du calculateur douanier ZLECAf (audit
`audits/AUDIT_DIFFERENTIEL_PILOTES_2026-07-26.md`). Le Maroc fait partie des
6 pays pilotes. `backend/data/MAR_tariffs.json` (13114 lignes, source
déclarée `douane.gov.ma/adil`, ADII) reste la donnée de production.

## Résultat de cette itération

**Aucun document primaire n'a été archivé.** Le domaine officiel
(`douane.gov.ma`, Administration des Douanes et Impôts Indirects) est bien
réel et accessible (HTTP 200, portail Liferay institutionnel légitime), ce
qui confirme la provenance déjà déclarée dans `MAR_tariffs.json`. Mais
aucun document PDF statique n'a pu être extrait :

- Le portail **ADIL** (`douane.gov.ma/adil/`) est une application
  frameset héritée (HTML 4.01 Frameset, ASP) : son contenu réel (recherche
  tarifaire) est chargé dans des sous-frames dynamiques, non accessible
  par une simple requête HTTP. Il rejette aussi les requêtes automatisées
  sans en-tête User-Agent navigateur.
- La page « bases législatives et réglementaires » du portail principal
  charge son contenu documentaire via des portlets Liferay
  (`journal_content`, iframes AJAX) — aucun lien PDF statique dans le
  HTML servi.

Voir `inventory.csv` pour le détail des tentatives et diagnostics exacts.

## Ce qui manque pour compléter cette collecte

Un accès avec exécution JavaScript (navigateur réel) serait nécessaire
pour identifier et télécharger le Code des Douanes et Impôts Indirects
et/ou les circulaires tarifaires publiées sur ce portail. Aucun
contournement de cette limite technique n'a été tenté.

## État de l'enregistrement

Aucun changement de comportement du calculateur : cette collecte documente
une tentative de provenance, sans succès d'archivage. Aucune donnée
tarifaire modifiée.

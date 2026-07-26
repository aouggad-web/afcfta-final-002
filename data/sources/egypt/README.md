# Égypte — collecte de provenance (calculateur douanier pilote)

Consultation : 2026-07-26.

Chantier de consolidation du calculateur douanier ZLECAf (audit
`audits/AUDIT_DIFFERENTIEL_PILOTES_2026-07-26.md`). L'Égypte fait partie des
6 pays pilotes. `backend/data/EGY_tariffs.json` (8746 lignes, source
déclarée `customs.gov.eg`) reste la donnée de production.

## Résultat de cette itération

**Aucun document primaire nouveau n'a été archivé.** Le domaine officiel
(`customs.gov.eg`, Egyptian Customs Authority) est bien réel et accessible
(HTTP 200, portail institutionnel ASP.NET MVC légitime avec une véritable
section « Legislations »), ce qui confirme la provenance déjà déclarée
dans `EGY_tariffs.json`. Mais aucun document PDF statique n'a pu être
extrait :

- La section `/Legislations/InternationalTrade` charge sa liste de
  documents via un mécanisme AJAX non identifié dans cette itération —
  aucun lien PDF statique dans le HTML initial servi.
- Le service `/Services/Tarif` est un système de requête en direct
  paginé par chapitre (`?page=N&chapterId=1`), pas un document unique
  archivable — c'est la même nature de source que celle déjà utilisée
  par le crawler existant du dépôt (`engine/scripts/crawl_egy_egyptariffs.py`).

Voir `inventory.csv` pour le détail des tentatives et diagnostics exacts.

## Ce qui manque pour compléter cette collecte

Identifier l'endpoint AJAX exact utilisé par la section Legislations, ou
un accès avec exécution JavaScript (navigateur réel), serait nécessaire
pour localiser et télécharger le texte de loi douanière égyptienne
consolidé. Aucun contournement de cette limite technique n'a été tenté.

## État de l'enregistrement

Aucun changement de comportement du calculateur : cette collecte documente
une tentative de provenance, sans succès d'archivage de nouveau document.
Aucune donnée tarifaire modifiée.

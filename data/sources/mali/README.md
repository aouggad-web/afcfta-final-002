# Mali — collecte (TVA vérifiée)

Consultation : 2026-07-25 (Africa/Algiers).

**Correction de collecte.** Une passe antérieure avait enregistré `data/mali/vat_measures.json` avec un statut `PENDING_OFFICIAL_CONSOLIDATION`, un `sha256` `pending_collection`, aucun fichier archivé, et une référence légale générique non vérifiée (« Code Général des Impôts, enacted 1999-06-01 ; UEMOA harmonization rate »), avec une URL fictive (`armp.mali.org/documents/legislation`, domaine qui ne semble pas correspondre à l'ARMP du Mali). Ce cycle remplace ces données par une collecte vérifiée sur texte primaire.

## Ce qui a été vérifié sur texte primaire

Portail officiel de la Direction Générale des Impôts (`dgi.gouv.ml/CGI/`), téléchargé directement (source primaire gouvernementale) :
- **Article 229** (Loi n°11-078) : « Les taux de la TVA sont fixés ainsi qu'il suit : 5% pour les produits visés au point D de la sous-section 1 [...] ; 18% pour les autres produits et les services non exonérés. »

## Ce qui n'a PAS été vérifié — et pourquoi

- La date d'entrée en vigueur exacte de la Loi n°11-078 n'est pas indiquée sur la page consultée ; `effective_from` a été fixé à la date de collecte plutôt qu'à une date législative non confirmée.
- La liste précise des produits visés au « point D » (taux réduit 5%) n'a pas été transcrite ce cycle.
- Loi de Finances 2026 et Tariff Guide douanier : URLs localisées lors d'une passe antérieure, non re-téléchargées ni re-vérifiées ce cycle.
- Accises, prélèvements spéciaux : non abordés dans ce cycle.

## État de l'enregistrement

Juridiction MLI : **non** enregistrée dans `SUPPORTED_JURISDICTIONS` — TVA seule, pas d'accises, pas de Loi de Finances. ZLECAf : **pas** d'offre nationale encore enregistrée dans `NATIONAL_OFFER_REGISTRY`.

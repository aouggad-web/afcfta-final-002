# Sénégal — collecte (TVA vérifiée)

Consultation : 2026-07-25 (Africa/Algiers).

**Correction de collecte.** Une passe antérieure (bulk, plusieurs pays UEMOA) avait enregistré `data/senegal/vat_measures.json` avec un statut `PENDING_OFFICIAL_CONSOLIDATION`, un `sha256` `pending_collection`, aucun fichier archivé, et une référence légale générique non vérifiée (« Code Général des Impôts, enacted 2012-01-01 ; UEMOA harmonization rate »), avec une URL fictive (`armp.sn/textes-legaux/code-general-impots`). Ce cycle remplace ces données par une collecte vérifiée sur texte primaire.

## Ce qui a été vérifié sur texte primaire

Code Général des Impôts (édition juillet 2019, à jour au 27 mars 2019), republication de 387 pages portant la numérotation d'articles et les citations de lois modificatives en texte :
- **Taux standard 18%** — Article 369 (Loi n°2015-06 du 23 mars 2015).
- **Taux réduit 10%** pour l'hébergement touristique agréé — Article 369 (même loi).
- **Exportations** — droit à déduction équivalent au taux zéro — Article 380(a) (Loi n°2018-10 du 30 mars 2018).

Le portail officiel de la DGID (`dgid.sn`) était injoignable depuis cet environnement au moment de la collecte (erreur de certificat TLS) ; le texte utilisé est une republication vérifiée article par article, pas le portail gouvernemental lui-même.

## Ce qui n'a PAS été vérifié — et pourquoi

- Amendements postérieurs à mars 2019 non couverts par cette édition.
- Loi de Finances 2026 et Tariff Guide douanier : URLs localisées lors d'une passe antérieure, non re-téléchargées ni re-vérifiées ce cycle.
- Accises, prélèvements spéciaux : non abordés dans ce cycle.

## État de l'enregistrement

Juridiction SEN : **non** enregistrée dans `SUPPORTED_JURISDICTIONS` — TVA seule, pas d'accises, pas de Loi de Finances. ZLECAf : **pas** d'offre nationale encore enregistrée dans `NATIONAL_OFFER_REGISTRY`.

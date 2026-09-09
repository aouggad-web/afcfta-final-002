# Côte d'Ivoire — collecte (TVA vérifiée via Loi de Finances 2026)

Consultation : 2026-07-25 (Africa/Algiers).

**Correction de collecte.** Une passe antérieure avait enregistré `data/cote-d-ivoire/vat_measures.json` avec un statut `PENDING_OFFICIAL_CONSOLIDATION`, un `sha256` `pending_collection`, aucun fichier archivé, et une affirmation non vérifiée que le Code Général des Impôts couvrait aussi les accises et prélèvements — rien de tout cela n'avait été lu sur texte primaire. Ce cycle remplace ces données par une collecte vérifiée sur texte primaire, limitée à la TVA.

## Ce qui a été vérifié sur texte primaire

Annexe fiscale à la loi de Finances n°2025-987 du 19 décembre 2025 (gestion 2026), téléchargée directement depuis le portail de la Direction Générale du Budget et des Finances (`dgbf.ci`, source primaire gouvernementale) :
- **Article 6** (« Mesures de rationalisation des exonérations fiscales ») cite explicitement « le taux de droit commun de TVA de 18% », en l'appliquant à des opérations dont l'exonération est supprimée (fibres de jute/sisal, aliments pour bétail et leurs intrants, intrants pour engrais — articles 355-17, 355-27, 355-28, 355-30 du CGI).

Le PDF complet fait 10,5 Mo (au-dessus du seuil de 5 Mo pour archivage direct) : seul l'extrait opérationnel (Article 6, ~3 pages) a été archivé en texte ; le SHA-256 du PDF complet est conservé dans `inventory.csv` pour vérification indépendante, sans être commité au dépôt.

## Ce qui n'a PAS été vérifié — et pourquoi

**L'article de base du CGI qui fixe le taux (rapporté par des sources tierces comme l'Article 359) n'a PAS été lu directement.** Seule sa confirmation via cette annexe fiscale 2026 — qui modifie des articles en aval (355-x) tout en désignant explicitement le taux de 18% comme taux de droit commun — a été vérifiée. `effective_from` reflète donc la date de cette loi de finances, pas la date d'entrée en vigueur originelle du CGI.

- Accises, prélèvements spéciaux (PCS, PCC, RS, TSI) : **non vérifiés** — l'affirmation précédente qu'ils étaient « couverts par le Code Général des Impôts » n'était pas fondée sur une lecture de texte.
- Guide d'administration fiscale DGI (procédures, formalités) : URL localisée, non téléchargée ni re-vérifiée ce cycle.

## Lot réglementaire (2026-07-29) — formalités et contrôles à l'importation

Ce cycle ajoute `data/cote-d-ivoire/regulatory_measures.json` : quatre mesures réglementaires obligatoires à l'importation, distinctes des taux fiscaux (GUCE, RFCV, BSC, VOC/PVoC).

**Statuts canoniques de vérification** appliqués à ce lot (aucune archive n'a pu être produite ce cycle) :
- `PARTIAL` : source officielle identifiable (portail gouvernemental / parastatal, référence de décret) mais **non archivée** sur texte primaire ;
- `UNVERIFIED` : information recoupée uniquement par des sources secondaires (aucune mesure de ce lot n'est en `UNVERIFIED` — un portail officiel a été identifié pour chacune) ;
- `pending_primary_archive: true` : drapeau maintenu tant que l'extrait primaire daté n'est pas téléchargé et haché.

**Pourquoi aucune archive.** Les portails officiels (`guce.gouv.ci`, `douanes.ci`, `oic.ci`, `commerce.gouv.ci`, `presidence.ci`) renvoient **HTTP 403 Forbidden** sur récupération automatique (WebFetch). Aucun contournement n'a été tenté. Les références de décrets ont été identifiées par recoupement de sources officielles, sans lecture directe du texte primaire — d'où `PARTIAL` et non `VERIFIED_PRIMARY_TEXT`.

**Frais / tarifs.** Tous les champs `fees` sont laissés à `null` (`fees_status: NOT_AVAILABLE`). **Aucun montant issu de source secondaire n'est renseigné** : conformément au principe fail-closed, aucun frais n'entre dans le calculateur tant qu'une source officielle actuelle ne le confirme pas.

**Webb Fontaine — fiche d'acteur.** Rattaché à la mesure GUCE-CI (`CIV-GUCE-SINGLE-WINDOW`) via `mandated_actors[]`, classé `TECHNICAL_OPERATOR` (rôle historique d'exploitant technique de la plateforme jusqu'au rachat par l'État en 2023, décret n°2023-168) : statut juridique, autorité mandante, mission, base du mandat, durée, frais autorisés (`null`) et document délivré documentés. Un rôle actif post-2023 n'est pas confirmé sur texte primaire.

| Mesure | Autorité | Statut |
|---|---|---|
| GUCE-CI (guichet unique) | GUCE-CI (société d'État) | PARTIAL |
| RFCV (classification/valeur) | Direction Générale des Douanes | PARTIAL |
| BSC (suivi des cargaisons) | Office Ivoirien des Chargeurs | PARTIAL |
| VOC/PVoC (conformité) | Ministère du Commerce et de l'Industrie | PARTIAL |

## État de l'enregistrement

Juridiction CIV : **non** enregistrée dans `SUPPORTED_JURISDICTIONS` — TVA seule (et via un texte d'application, pas l'article de base du CGI), pas d'accises, pas de prélèvements ; les mesures réglementaires ci-dessus sont documentaires (aucun taux/frais exploitable). ZLECAf : **pas** d'offre nationale encore enregistrée dans `NATIONAL_OFFER_REGISTRY`.

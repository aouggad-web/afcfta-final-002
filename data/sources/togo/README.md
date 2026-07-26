# Togo — collecte vérifiée (UEMOA)

Consultation : 2026-07-26. Corrige une collecte initiale fabriquée (statut `PENDING_OFFICIAL_CONSOLIDATION`, `sha256: pending_collection`, domaine inexistant `impots.tgo`).

## Ce qui a été vérifié sur texte primaire

- **TVA taux standard 18%** — Code Général des Impôts, Article 323, cité verbatim dans « Le Cahier Fiscal 2017 » (OTR, Office Togolais des Recettes) : « Le taux de la taxe sur la valeur ajoutée est un taux de 18% applicable à toutes les activités et à tous [les produits], à l'exception de ceux exonérés en vertu de l'article 311. » PDF officiel téléchargé depuis `otr.tg`, 16 pages, texte extractible.
- Ce document confirme aussi un **taux réduit ponctuel de 10%** sur les tissus kaki/imprimés neufs et des **exonérations temporaires** (matériels d'énergies renouvelables, terminaux mobiles), mais uniquement pour l'exercice fiscal 2017 (1er janvier–31 décembre 2017) — mesures expirées, non extraites comme enregistrements permanents.

## Ce qui n'a PAS été collecté

- **Texte consolidé complet du CGI, édition 2018** (168 pages) : localisé sur `otr.tg`, mais c'est un **PDF scanné sans couche de texte** (produit par un scanner Canon iR-ADV) — extraction automatique impossible, aucun outil OCR disponible dans cet environnement (`pytesseract` non installé). L'Article 323 a néanmoins été confirmé via le Cahier Fiscal 2017 ci-dessus.
- **Finance Law 2026** : non localisée dans ce cycle.

## État de l'enregistrement

**Non** enregistrée dans `SUPPORTED_JURISDICTIONS`. **Pas** d'offre ZLECAf dans `NATIONAL_OFFER_REGISTRY`.

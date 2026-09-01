# Copie DZA périmée (16 juin 2026) — remplacée par le fichier racine (29 août 2026)

**Date de retrait** : 2026-09-01 — Audit `audits/AUDIT_CALCULATEUR_DONNEES_TARIFAIRES_2026-09-01.md`, action P0-2.

## Contexte

Deux copies du fichier tarifaire Algérie coexistaient et étaient servies par des
chemins différents :

| Copie | Chemin | Générée le | Statut | Servie par |
|---|---|---|---|---|
| Racine (source de vérité) | `backend/data/DZA_tariffs.json` | 2026-08-29 | CRAWLED_AUTHENTIC (rebuild crawl conformepro.dz/DGD, commit 8b6bd5d6) | `authentic_tariff_service` → routes `/authentic-tariffs/*` |
| **Périmée (ce fichier)** | `backend/data/tariffs/DZA_tariffs.json` | 2026-06-16 | VERIFIED (ETL) | `tariff_data_service` → fallback `/calculate-tariff` |

La comparaison a montré **5 141 conflits réels de taux DD sur les sous-positions
10 chiffres** (ex. `2930100000` : 5 % dans la copie juin vs 15 % dans le crawl
août) et 1 631 conflits au niveau HS6 — deux taux différents servis selon la
route appelée.

## Décision

La copie périmée est retirée du service. Le fichier racine (crawl authentique le
plus récent) est **la source unique de vérité DZA**. Les écarts de réconciliation
canonique↔crawl (16 922 positions, voir `data/coverage/DZA_tariff_reconciliation.json`)
restent à arbitrer contre la source officielle DGD — ils sont documentés, jamais
servis en double.

## Ré-activation

Aucune ré-activation : ce fichier ne doit pas revenir au service. En cas de
re-crawl DZA futur, régénérer `backend/data/DZA_tariffs.json` puis supprimer
l'ancienne version (git history conserve l'historique complet).

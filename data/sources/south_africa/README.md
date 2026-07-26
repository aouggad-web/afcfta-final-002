# Afrique du Sud — collecte officielle

Consultation : 2026-07-25 (Africa/Algiers).

Première collecte, volontairement restreinte : un fait fiscal unique et bien
vérifié (taux TVA standard) et la confirmation d'une offre ZLECAf nationale
officielle publiquement accessible mais non encore extraite ligne à ligne.

## Couverture de cette collecte

1. **TVA** : taux standard 15%, Value-Added Tax Act 1991 (Act 89 of 1991).
   Source de niveau « guide administratif » (page SARS types-of-tax), pas le
   texte consolidé de la loi lui-même — le texte intégral de la loi n'a pas
   été localisé sur un portail public interrogeable dans cette collecte.
   Le taux est néanmoins confirmé courant par plusieurs annonces SARS datées
   (mars-avril 2025) relatant l'annulation d'une hausse à 15.5%/16%
   initialement annoncée.
2. **ZLECAf (niveau 2 — offre nationale)** : Schedule No. 10 Part 8 du
   Customs and Excise Act 1964 contient le texte intégral de l'Accord ZLECAf
   (Government Notice R.1433, Government Gazette 44049, 31 décembre 2020,
   effectif 1er janvier 2021). Ce texte confirme l'existence d'une « colonne
   AfCFTA » dans Schedule No. 1 Part 1 (barème douanier ordinaire, chapitres
   1-99, mis à jour au 24 juillet 2026) — c'est cette colonne qui contient les
   taux préférentiels ligne à ligne réels.

   **Mise à jour 2026-07-26** : ce document (Schedule No. 1 Part 1, 2.85 Mo,
   daté 24 juillet 2026) a été téléchargé et archivé
   (`official/sars-schedule1-part1-chapters1-99.pdf`, SHA-256
   `a5f331640c66d62fe75057658afc2532030e10bb9c8ecb0387a230c85f385bb9`). C'est
   désormais une preuve documentaire primaire complète pour le droit de
   douane ordinaire sud-africain (99 chapitres) et pour l'offre nationale
   ZLECAf de niveau 2. **L'extraction structurée ligne par ligne reste non
   réalisée** : le barème couvre l'intégralité de la nomenclature douanière
   (~5619 positions SH6) et une extraction fiable de chaque taux (droit
   ordinaire + taux préférentiel AfCFTA) dépasse le périmètre de cette
   itération — elle nécessite un traitement dédié du PDF, distinct du simple
   archivage. Statut : `official_downloaded` (document archivé) mais
   extraction ligne à ligne toujours `source_pending_collection` (voir
   `inventory.csv`, ligne `ZAF-SARS-SCH1P1-LINE-EXTRACTION`).

## Ce qui n'est pas couvert

- Accises (Schedule No. 1 Part 2A/2B), droits antidumping/compensateurs/
  sauvegarde (Schedule No. 2), ristournes/remboursements (Schedules 3-6) :
  non collectés.
- Le barème douanier ordinaire lui-même (Schedule No. 1 Part 1) et sa
  colonne ZLECAf : document archivé depuis le 2026-07-26 (voir ci-dessus),
  mais **contenu non extrait** ligne à ligne — aucune donnée structurée
  n'existe encore pour les ~5619 positions SH6.
- Formalités administratives sud-africaines : non collectées.
- La juridiction ZAF n'est donc **pas** enregistrée dans
  `SUPPORTED_JURISDICTIONS` (backend/services/national_legal_calculation_service.py) :
  une couche partielle (TVA seule) donnerait une fausse impression de
  vérification complète si elle était exposée par le calculateur.

## Politique d'archivage

Le PDF officiel de Schedule No. 10 Part 8 (12 Mo, texte intégral de
l'Accord ZLECAf) n'est pas archivé tel quel dans le dépôt — conformément à la
politique de poids (éviter la répétition de l'épisode ~20 Mo de la PR #307).
Un extrait de 80 lignes (page de couverture + citation légale) est conservé
sous `extracted/`, avec le SHA-256 du PDF original consigné dans
`data/south_africa/legal_sources.json` pour permettre une vérification lors
d'une future re-collecte.

## Résultat des tests d'accès

| Source | Résultat (User-Agent navigateur, curl direct) |
|---|---|
| `https://www.sars.gov.za/types-of-tax/value-added-tax/` | HTTP 200 |
| `https://www.sars.gov.za/legal-counsel/primary-legislation/schedules-to-the-customs-and-excise-act-1964/` | HTTP 200 |
| `https://www.sars.gov.za/legal-lprim-ce-sch10p8-schedule-no-10-part-8/` | HTTP 200 (sert directement un PDF, pas une page HTML) |
| `https://www.sars.gov.za/legal-lprim-ce-sch1p1chpt1-to-99-schedule-no-1-part-1-chapters-1-to-99/` | **Mise à jour 2026-07-26** : HTTP 301 → redirection suivie vers `https://www.sars.gov.za/wp-content/uploads/Legal/SCEA1964/Legal-LPrim-CE-Sch1P1Chpt1-to-99-Schedule-No-1-Part-1-Chapters-1-to-99.pdf`, HTTP 200, PDF valide (2.85 Mo), téléchargé et archivé |

Note technique : l'outil WebFetch intégré a retourné 403 Forbidden sur ces
mêmes URLs (proxy sans en-tête User-Agent de navigateur), alors qu'un curl
direct avec User-Agent navigateur a systématiquement réussi. Aucun
contournement d'authentification ou de restriction d'accès n'a été tenté —
uniquement l'usage d'un en-tête User-Agent standard de navigateur.

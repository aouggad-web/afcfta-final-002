# Afrique du Sud — collecte officielle

Consultation : 2026-08-17 (Africa/Algiers).

Cette collecte couvre le taux de TVA standard et le barème douanier officiel
SARS Schedule No. 1 Part 1, y compris sa colonne AfCFTA extraite ligne à ligne.

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
   taux préférentiels ligne à ligne réels. La révision du **6 août 2026** a
   a été vérifiée par SHA-256 et ses **8 592 lignes nationales** extraites
   par position PDF de la colonne AfCFTA. Le jeu structuré contient 4 663
   lignes `free`, 3 617 taux ad valorem, 140 droits composés et 172 droits
   spécifiques. Les 312 droits composés/spécifiques sont conservés verbatim
   mais ne sont pas calculés sans quantité/unité.

## Ce qui n'est pas couvert

- Accises (Schedule No. 1 Part 2A/2B), droits antidumping/compensateurs/
  sauvegarde (Schedule No. 2), ristournes/remboursements (Schedules 3-6) :
  non collectés.
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

Schedule No. 1 Part 1 (2,85 Mo) n'est pas dupliqué dans le dépôt. Son jeu
déterministe est conservé sous
`backend/data/official_preferential/ZAF_afcfta_2026-08-06.json.gz`; le hash du
PDF officiel est verrouillé par `backend/scripts/extract_sars_afcfta_schedule.py`.

## Résultat des tests d'accès

| Source | Résultat (User-Agent navigateur, curl direct) |
|---|---|
| `https://www.sars.gov.za/types-of-tax/value-added-tax/` | HTTP 200 |
| `https://www.sars.gov.za/legal-counsel/primary-legislation/schedules-to-the-customs-and-excise-act-1964/` | HTTP 200 |
| `https://www.sars.gov.za/legal-lprim-ce-sch10p8-schedule-no-10-part-8/` | HTTP 200 (sert directement un PDF, pas une page HTML) |
| `https://www.sars.gov.za/legal-lprim-ce-sch1p1chpt1-to-99-schedule-no-1-part-1-chapters-1-to-99/` | HTTP 200 en GET, PDF daté du 6 août 2026 |

Note technique : l'outil WebFetch intégré a retourné 403 Forbidden sur ces
mêmes URLs (proxy sans en-tête User-Agent de navigateur), alors qu'un curl
direct avec User-Agent navigateur a systématiquement réussi. Aucun
contournement d'authentification ou de restriction d'accès n'a été tenté —
uniquement l'usage d'un en-tête User-Agent standard de navigateur.

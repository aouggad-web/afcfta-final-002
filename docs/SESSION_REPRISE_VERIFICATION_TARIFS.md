# SESSION REPRISE — Vérification pays par pays des tarifs (doctrine zéro-fabrication)

LIRE D'ABORD : `MISSION_TARIFS_AFRICAINS.md`, `audits/ETAT_DONNEES_TARIFAIRES_REGLEMENTAIRES_2026-09-05.md`, puis ce fichier.

## État acquis (poussé sur GitHub, CI verte)
- 10 juridictions nationales actives : KEN, DZA, EGY (sur main) + 7 en PRs **#450–#456**
  (ZAF, CMR, GHA, MUS, RWA, TZA, TUN) — branche `feat/jurisdiction-{iso3}` par pays.
- Auto-découverte : `data/{slug}/jurisdiction_config.json` active une juridiction sans toucher le code.
- Builder : `backend/scripts/build_jurisdiction_files.py <ISO3> <slug>`
- Audit de profondeur : `backend/scripts/audit_jurisdictions_depth.py` (0 orpheline, 0 F.A.P numérique, SHA-256 OK)
- Tests : `backend/tests/test_jurisdictions_priority9.py` (14/14, skip par branche),
  `test_dza_legal_layer.py`, `test_egy_legal_layer.py`
- Le test paramétré sur 7 pays SKIPPÉ si la juridiction n'est pas sur la branche
  (1 PR par pays — cf. règle de reprise).

## ✅ RWA — FAIT (exhaustivité vérifiée contre le PDF officiel, PR #454)
- PDF EAC CET 2022 téléchargé (kra.go.ke), SHA-256 : `4c5acc8b…a53b49` (560 pages).
- Exhaustivité prouvée : 5 954 codes uniques 8 chiffres = Schedule 1 (5 954) ∪ Schedule 2 (49 SI).
- Corrections (`backend/scripts/fix_rwa_cet_completeness.py`, reproductible) :
  - 49 doublons Schedule 1/Schedule 2 arbités selon la règle SI du texte officiel
    (Introduction p. 9 : le taux applicable est celui du Schedule 2) ;
  - 4 taux ad valorem omis ajoutés : 53021000=0%, 58110000=25%, 92099200=10%, 92099400=10% ;
  - 25 droits composés (6309 « 35% or USD 0.40/kg », acier 72xx « 25% or $200/MT »)
    structurés `MAX_AD_VALOREM_SPECIFIC` — AUCUN montant fabriqué (exige la quantité) ;
  - 19 codes fusionnés-absents récupérés (2404 nicotine, 2903, 3808 pesticides,
    3923 capsules, 4105 cuir — taux vérifiés page par page pp. 96/131/188-189/210-211/221) ;
  - 0 doublon, 0 CET manquant, 0 ligne sans DD après correction (crawled + canonique).
- Documentation : `data/rwanda/rwa_gazette_register.json` (verification_nationale),
  `data/rwanda/calculation_method.json` (cascade complète : CIF → DD → Excise →
  IDL 1,5% → AUL 0,2% → QIF 0,2% → TVA 18% → env-plastic 0,2% ; WHT marqué UNVERIFIED ;
  sources = texte du tarif officiel + PwC Rwanda 2026-02-18).
- Sources ajoutées (demande utilisateur) : tralac.org (resources + AfCFTA),
    au.int + au-afcfta.org (UA/ZLECAf), PwC Rwanda (cascade).
  - ⚠️ Total « 7 341 lignes EAC CET » signalé mais NON CONFIRMÉ (TRALAC/UA) —
    marqué UNVERIFIED dans le registre ; référence = PDF officiel (5 954+49=6 003).
  - Tests : `backend/tests/test_rwa_cet_completeness.py` (13 tests).

## Reste à vérifier — pays par pays (dans cet ordre)
2. **TZA** : EAC CET 2022 8 chiffres — refaire la même vérification (doublons SI,
   CET manquants, codes fusionnés-absents) ; un seul contrôle KRA couvre RWA+TZA.
   Recouper avec la piste « 7 341 lignes » (TRALAC/UA) avant de conclure. Mettre à jour registre + tests.
3. **TUN** : 48 sous-positions DD non publiées — re-crawl `douane.gov.tn/tarifweb2025`
   (endpoint identifié re-crawlable ; voir reports/TUN_TARIFF_DOCUMENTATION.md).
   ⚠️ codes à 11 caractères (01012100015) : 10 chiffres + digit additionnel à documenter.
4. **MUS** : 1 309 lignes sans TVA — listes d'exonération MRA (mra.mu) ; documenter comme
   vat_exemptions explicites par position.
5. **ZAF, CMR, GHA** : re-crawl incrémental « à la DZA » (fichiers de progression par position,
   cf. backend/data/crawled/DZA_progress_*.json comme modèle) pour prouver l'exhaustivité.
   ⚠️ CMR à 8 chiffres seulement (5 239 SP) : le tarif national CEMAC descend à 10 chiffres
   — vérifier une troncature du crawl.
6. Après chaque pays : mettre à jour le registre (`verification_nationale`), relancer
   `audit_jurisdictions_depth.py` + tests, committer sur la branche du pays, NE PAS merger
   (relecture humaine avant merge).

## Environnement
- Python : `backend/.venv311` (recréable : pyenv 3.11.10 + `pip install -r requirements.txt pytest black`)
- PyMuPDF installé (extraction PDF DZA/UGA/EAC).
- CI : lint = flake8 seul (black/isort global RETIRÉS — ne pas les remettre).
- Emergent : `BRANCH=main bash sync_emergent.sh` dans le shell Emergent.

## Règles non négociables
Pas de mock/hallucination/extrapolation ; chaque taux lié à sa position nationale + source ;
NOT_AVAILABLE jamais comblé ; invariant numérique F.A.P ; CI verte avant push.
Méthode de calcul : d'abord extraire du texte du tarif officiel lui-même (introduction,
notes, colonne taux), corroborer ensuite par sources non gouvernementales permises
(thèses universitaires, guides de formation logistique, résumés fiscaux Big-4).

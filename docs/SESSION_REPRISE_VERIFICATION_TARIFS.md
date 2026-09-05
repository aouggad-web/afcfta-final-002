# SESSION REPRISE — Vérification pays par pays des tarifs (doctrine zéro-fabrication)

LIRE D'ABORD : `MISSION_TARIFS_AFRICAINS.md`, `audits/ETAT_DONNEES_TARIFAIRES_REGLEMENTAIRES_2026-09-05.md`, puis ce fichier.

## État acquis (poussé sur GitHub main, CI verte)
- 10 juridictions nationales actives : KEN, DZA, EGY (sur main) + 7 en PRs **#450–#456**
  (ZAF, CMR, GHA, MUS, RWA, TZA, TUN) — branche `feat/jurisdiction-{iso3}` par pays.
- Auto-découverte : `data/{slug}/jurisdiction_config.json` active une juridiction sans toucher le code.
- Builder : `backend/scripts/build_jurisdiction_files.py <ISO3> <slug>`
- Audit de profondeur : `backend/scripts/audit_jurisdictions_depth.py` (0 orpheline, 0 F.A.P numérique, SHA-256 OK)
- Tests : `backend/tests/test_jurisdictions_priority9.py` (14/14), `test_dza_legal_layer.py`, `test_egy_legal_layer.py`

## Travail restant — pays par pays (dans cet ordre)
1. **RWA + TZA** : vérifier les 26 positions sans CET (exonérations EAC) contre la gazette EAC/KRA
   (kra.go.ke — un seul contrôle couvre les deux pays). Mettre à jour les registres + tests.
2. **TUN** : 48 sous-positions DD non publiées — re-crawl `douane.gov.tn/tarifweb2025`
   (endpoint identifié re-crawlable ; voir reports/TUN_TARIFF_DOCUMENTATION.md).
3. **MUS** : 1 309 lignes sans TVA — listes d'exonération MRA (mra.mu) ; documenter comme
   vat_exemptions explicites par position.
4. **ZAF, CMR, GHA** : re-crawl incrémental « à la DZA » (fichiers de progression par position,
   cf. backend/data/crawled/DZA_progress_*.json comme modèle) pour prouver l'exhaustivité.
5. Après chaque pays : mettre à jour le registre (`verification_nationale`), relancer
   `audit_jurisdictions_depth.py` + tests, committer sur la branche du pays.

## Environnement
- Python : `backend/.venv311` (recréable : pyenv 3.11.10 + `pip install -r requirements.txt pytest black`)
- PyMuPDF installé (extraction PDF DZA/UGA).
- CI : lint = flake8 seul (black/isort global RETIRÉS — ne pas les remettre).
- Emergent : `BRANCH=main bash sync_emergent.sh` dans le shell Emergent.

## Règles non négociables
Pas de mock/hallucination/extrapolation ; chaque taux lié à sa position nationale + source ;
NOT_AVAILABLE jamais comblé ; invariant numérique F.A.P ; CI verte avant push.

# État des données tarifaires et réglementaires + plan d'amélioration

**Date : 05/09/2026** · Périmètre : module tarifs & réglementaire, 54 pays UA ·
Doctrine de référence : « Pas de mock, pas d'hallucination, pas d'extrapolation » (`MISSION_TARIFS_AFRICAINS.md`)

---

## 1. Vue d'ensemble

Trajectoire documentée : 894 783 lignes SYNTHETIC (juin 2026) → quarantaine des 46 fichiers template
(`crawled/QUARANTINE_SYNTHETIC/`) → gate doctrine `backend/services/tariff_doctrine.py` + archivage des
14 fichiers `enhanced_v2` (01/09/2026, 23 tests verts). Règle en vigueur : NOT_AVAILABLE jamais comblé,
préférence exécutée uniquement si réciprocité prouvée (modèle circulaire DGD 482/2024).

| Catégorie | Pays | Nature | Fiabilité |
|---|---|---|---|
| 🟢 Authentique national (8–11 chiffres) | 6 | Crawl officiel : DZA (17 115 SH10), TUN (17 512 SH11), EGY (8 746), MAR (13 114), MUS (6 073), ETH (2 038 partiel) | Vérifiée ligne à ligne (TUN 6/6, DZA 4/4, EGY 5/5 — `verify_government_sources.py`) |
| 🔵 TEC régional officiel | 34 | CEDEAO 15 (5 387 l.), CEMAC 6 (4 801), EAC 7 (5 604), SACU 5 (5 619) — TEC réel + taxes nationales différenciées | Tarif douanier commun valable ; pas de nomenclature nationale propre |
| 🟡 Dérivé WITS/TRAINS | 12 | AGO, COM, LBY, MDG, MOZ, MRT, MWI, SDN, STP, SYC, ZMB, ZWE — MFN appliqué SH6 (2022) + TVA nationale sourcée | Moyenne MFN ≠ tarif national publié (plafond PARTIAL/C) |
| 🔴 Absents | 2 | DJI, ERI — 0 ligne, placeholders PENDING | Aucune source publique |

Volume total : ~211 844 lignes HS6 canoniques (`backend/data/*_tariffs.json`, 40 pays) + ~64 125 lignes
dérivées (`crawled/`) + ~50 600 lignes d'offres ZLECAf gelées (`official_preferential/`).

## 2. État tarifaire — par pays

### Maghreb + Égypte
- **DZA** 🟢 : 17 115 SH10, 5 505 lignes avec avantages ; TVA 19/9, PRCT 2 %, TCS, DAPS (335 taux) ;
  296 DD + 460 TVA non publiés ; ZLECAf ligne à ligne (circulaire DGD 482/2024 : liste B = 1 163 codes,
  C = 456) — **seul pays exécutable en préférentiel**.
- **TUN** 🟢 : 17 512 SH11, assiettes verbatim (46 codes de taxes), FODEC ; re-crawl des taux live
  re-publiés recommandé et non exécuté.
- **EGY** 🟢 : 8 746 lignes simulables ; 8 803 descriptions/taux DD manquants dans le crawl ;
  ZLECAf lignes A/B ; GOEIC (loi 118/1975, décrets 991/2015…).
- **MAR** ⚠️ : source UNVERIFIED, adil injoignable, simulables = 0, exclu des préférences actives
  (contradiction tralac ↔ douane.gov.ma).

### Afrique australe
- **ZAF/SACU** (BWA, LSO, NAM, SWZ) 🔵 : SARS Schedule 1 officiel (5 619 l.) + annexes ITAC
  (anti-dumping 401, rebates 1 091, accises 288) ; 4 260 lignes « revue requise » ; AfCFTA Schedule
  ZAF 8 592 lignes OFFER_ONLY ; Part 2 countervailing non publiée.
- **ZWE, ZMB, MWI, MOZ, MDG, AGO, COM, MRT, SDN, STP, SYC, LBY** 🟡 : WITS/TRAINS MFN SH6 + TVA
  nationale sourcée (`classification_source: "loi"` ou `"estimation_ia"` tracée).

### Afrique de l'Est
- **EAC** (BDI, COD, KEN, RWA, SSD, TZA, UGA) 🔵 : CET 2022 (KRA) ; gazettes post-CET juin 2025 non
  intégrées ; EACCMA 2025 SOURCE_PENDING (PDF 403) ; SOM VAT = 0.
- **ETH** 🟢 partiel : 2 038 lignes seulement, SUR 10 %, TVA 15 % ; ZLECAf Reg. 574/2025.
- **MUS** 🟢 : MRA Tariff HS2022 (6 073 l.) — écart documenté : le crawl réel est sourcé WITS, le
  canonique revendique MRA.

### Afrique de l'Ouest / Centrale
- **CEDEAO 15** 🔵 : TEC + parafiscaux riches (RS 1 %, PCS 1 %, PCC 0,5 %, PUA 0,2 %, TVA 10–19 %) ;
  NGA : IAT, EXC, Form M (CBN), CISS 1 %, SONCAP.
- **CEMAC 6** 🔵 : TCI 1 %, RI 0,45 %, CAC (CMR), TVA 15–19,25 % ; ECTN/BSC par conseil des chargeurs.

### Préférences ZLECAf
- Exécutable : DZA uniquement.
- Gelées OFFER_ONLY (~50 600 lignes) : CEMAC, EAC, ECOWAS, EGY (×2), ETH, TUN (×2), ZAF, ZMB.
- 44 autres pays : canevas SH2 indicatif (`afcfta_schedule.py`), non officiel ligne à ligne.

## 3. État réglementaire — par pays

| Niveau | Pays | Contenu |
|---|---|---|
| Spécifique sourcé par ligne | DZA (2 915 l.), MAR (4 485), TUN (2 018), EGY (4 833) | Codes officiels nationaux (DGD, GUCE 675–705, ADII, ق/غ) |
| Pilot fail-closed PARTIAL | KEN (le plus riche : 19 formulaires verbatim, exemptions, levées), NGA, CIV, CMR, COD, GHA | 17 mesures, 12 acteurs mandatés, 11 frais vérifiés |
| Mixte (frais vérifiés) | TZA, UGA, ZWE, GAB, COG | Frais PVoC/ECTN 0,25–0,5 % uniquement |
| Générique habillé | ~37 pays | 9 gabarits de documents identiques + nom d'autorité réel (54 pays configurés) ; « DAU/SAD » par défaut ; aucun seuil/délai/coût national |
| Rien de sourcé | 48/54 (registre maître NOT_AVAILABLE, as_of 2026-08-08) | Délais NOT_AVAILABLE partout ; aucune base BNT/NTM |

Règles d'origine ZLECAf : authentiques (Appendice IV, Annexe 2, COM-12 déc. 2023, e-Tariff Book UA) —
96 chapitres (91 AGREED, 3 PARTIAL, 2 YTB), 245 SH4, 50 SH6, 14 types de règles, YTB fail-closed ;
profondeur SH6 ≈ 1 %. RO des unions douanières régionales (UEMOA, CEDEAO, SADC, COMESA) : absentes.

Anomalies connues et assumées : `afcfta_rules_of_origin.py` (2 154 l.) DEPRECATED et drifté ;
scores NTB de 30 zones franches (`afcfta_compliance.json`) estimés non sourcés ;
`data/research/private_customs_missions_*.json` = SECONDARY_AI_SYNTHESIS, non opposable.

---

## 4. Plan d'amélioration de l'exactitude — sans mock, sans hallucination, sans extrapolation

### Phase 0 — Gouvernance (semaine 1, prérequis)
1. Manifeste de dataset actif unique : `data/registry/active_datasets.json`
   (pays → fichier actif → SHA-256 → URL source → date d'effet → version SH).
2. Re-vérification crypto au chargement : recalcul SHA-256 au boot, refus de servir si divergence (fail-closed) — P1 audit 01/09.
3. Métadonnées obligatoires par ligne : `source_url`, `date_effect`, `hs_version`, `provenance_tier` — condition d'entrée en service.
4. Unifier les 3 moteurs de calcul ; rendre le gate doctrine bloquant en CI (supprimer `continue-on-error`).

### Phase 1 — Compléter les 6 pays authentiques (semaines 2–6, ROI immédiat)
5. DZA : publier les 296 DD + 460 TVA manquantes (Tarif d'usage DGD 2020 / JORADP) ; arbitrage conflits par lecture du JO uniquement.
6. TUN : exécuter le re-crawl des taux live re-publiés.
7. EGY : récupérer les 8 803 descriptions/taux manquants (publiés par le portail).
8. MAR : re-crawl adil à la réouverture ; UNVERIFIED → VERIFIED ; réévaluer l'exclusion des préférences.
9. ZAF : compléter Schedule 1 (4 260 lignes) + Part 2 + liste TVA zéro-rated SARS.
10. MUS : crawler le vrai MRA Tariff pour remplacer la provenance WITS.

### Phase 2 — Passer les 34 pays TEC au national (mois 2–6)
11. EAC : gazettes nationales post-CET (dérogations, amendements) + EACCMA 2025 (accès alternatif : publications KRA, parlement.go.ke).
12. CEDEAO : obtenir le CSV officiel attendu par `cedeao_tec_adapter` (douanes.ci/commission) ; garder la variance nationale TVA/accises.
13. CEMAC : règlement CEMAC + BEAC puis relevés nationaux (modèle CMR/CNCC).
14. Longue traîne (12 pays WITS) : contact douanes nationales une par une (vague 3 du DATA_COLLECTION_PLAN). À défaut, conserver WITS assumé `provenance_tier: WTO_MFN_HS6` signalé au frontend.
15. DJI : ASYCUDA World (douane.gouv.dj) si disponible ; ERI : aucune source publique → rester NOT_AVAILABLE affiché.

### Phase 3 — Réglementaire (mois 3–9, en parallèle)
16. Généraliser le pilot fail-closed (méthode CIV/KEN/NGA) : 1 pays/semaine ; priorité aux partenaires ZLECAf actifs (ZAF, CMR, EGY, GHA, KEN, MUS, RWA, TZA, TUN).
17. Structurer les formalités : champs `authority_code`, `legal_basis`, `fee`, `delay` distincts ; attacher au SH8–10, pas au SH6.
18. Exécuter et persistier `enrich_all_africa_formalities.py` (script existant, jamais appliqué).
19. Activer les 8 offres ZLECAf gelées pays par pays : OFFER_ONLY → exécutable uniquement sur instrument douanier national daté (décret/arrêté). Jamais par interpolation du canevas SH2.
20. BNT/NTM : intégrer UNCTAD TRAINS NTM (classification MAST), étiqueté source secondaire — l'« angle mort majeur » (F13) reste entier.
21. RO ZLECAf : compléter SH6 au fil des COM successifs ; supprimer `afcfta_rules_of_origin.py` deprecated.

### Règles transverses (non négociables)
- Aucune valeur générée : pas de défaut 18 %, pas de fallback `return 10.0` (`north_africa_tariffs.py`), pas de `COMOROS = MADAGASCAR.copy()`.
- WITS/WTO/ITC = contre-vérification uniquement, jamais présentés comme tarif national.
- Ce qui n'est pas trouvable = NOT_AVAILABLE affiché — c'est une fonctionnalité, pas une dette.
- Process type d chaque amélioration : source officielle téléchargée → SHA-256 → parseur → conflits arbitrés par le texte légal → tests de non-régression → PARTIAL → VERIFIED après recoupement indépendant.

---

*Sources internes : DATA_COLLECTION_PLAN.md (12/06), AUDIT_APPROFONDI.md (26/06), audits/AUDIT_ET_PLAN_TECHNIQUE_AFCFTA_FINAL_002.md (13/07), reports/AFRICA_CUSTOMS_COVERAGE.md (24/07), reports/{DZA,TUN,EGY,MAR,ZAF}_TARIFF_DOCUMENTATION*.md (29–30/08), audits/AUDIT_CALCULATEUR_DONNEES_TARIFAIRES_2026-09-01.md, MISSION_TARIFS_AFRICAINS.md, data/coverage/africa_country_coverage.json, data/regulatory-compliance/country_registry.json.*

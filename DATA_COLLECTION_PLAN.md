# Plan de collecte des données tarifaires — 54 pays africains
> Version 1.0 — 2026-06-12  
> État courant : **894 783 lignes SYNTHETIC** sur 54 pays (schéma v4, audit 2026-06)  
> Objectif : atteindre ≥ 80 % PARTIAL ou VERIFIED d'ici fin 2026

---

## 1. Architecture des tarifs douaniers africains

### 1.1 Nomenclature harmonisée (SH)

La structure est universelle et empilée :

```
SH2  (98 chapitres)      ← commun à tous les pays
SH4  (~1 244 positions)  ← commun à tous les pays
SH6  (~5 831 sous-positions) ← commun à tous les pays  [couche actuelle SYNTHETIC]
SH8  (8 chiffres) ← spécification régionale (TEC) ou nationale
SH10 (10 chiffres) ← subdivision nationale (DZA, NGA, ZAF…)
SH12 (12 chiffres) ← statistique/fiscal (rare, quelques pays)
```

Conséquence : **une seule collecte du TEC régional débloque tous les pays membres** pour la couche SH8. Les subdivisions nationales SH10/12 restent à collecter pays par pays.

### 1.2 Contenu d'une position tarifaire complète

| Couche | Contenu | Source |
|--------|---------|--------|
| **Nomenclature** | code national, libellé, unité | TEC ou tarif national |
| **Droits et taxes** | taux DD, TVA, taxes parafiscales, méthode de calcul (CIF/FOB/cascade) | Code des douanes + loi de finances |
| **Mesures administratives** | licences, certificats, quotas, interdictions | Textes réglementaires sectoriels |
| **Avantages tarifaires** | taux ZLECAf, COMESA, CEDEAO, APE… + conditions d'origine | Listes de concessions UA/CE |
| **Provenance** | data_status, fiabilité, source, millésime | Audit interne (schéma v4) |

### 1.3 Méthode de calcul — point critique

Le coût final à l'importation n'est **pas** la somme des taux bruts. Il faut la séquence d'application exacte car certaines taxes se calculent sur une assiette incluant les taxes précédentes (mécanisme dit « en cascade »).

**Exemple validé — Algérie (DZA) :**
```
Base de calcul initiale = Valeur CIF

1. DD  (seq 10) : taux × CIF
2. DAPS (seq 15) : taux × CIF
3. TCS  (seq 20) : taux × CIF
4. PRCT (seq 30) : taux × CIF
5. TVA  (seq 90) : taux × (CIF + DD + DAPS + TCS + PRCT)  ← assiette cumulée

Taux effectif ≠ somme des taux nominaux
```

Chaque adaptateur doit implémenter cette logique nationale (`basis_includes[]` dans le schéma v4).

---

## 2. Cartographie des 54 pays par régime tarifaire

### Groupe A — Tarifs extérieurs communs régionaux (TEC/CET)
*Une collecte = N pays débloqués*

#### A1. TEC CEDEAO — 15 pays
| ISO3 | Pays | Part commerce intra-Af. | Particularités nationales |
|------|------|------------------------|--------------------------|
| NGA | Nigeria | ★★★★★ (26 %) | NASENI levy, SURCHARGE 7 %, ETLS |
| GHA | Ghana | ★★★★ | GETFund 2.5 %, NHIL 2.5 %, COVID levy 1 % |
| CIV | Côte d'Ivoire | ★★★ | Taxe spéciale sur les importations (TSI) |
| SEN | Sénégal | ★★★ | — |
| MLI | Mali | ★★ | enclavé, fret terrestre |
| BFA | Burkina Faso | ★★ | enclavé |
| GIN | Guinée | ★★ | taxe spéciale mines |
| BEN | Bénin | ★★ | port de Cotonou, transit |
| TGO | Togo | ★★ | port de Lomé, réexport |
| NER | Niger | ★ | enclavé |
| SLE | Sierra Leone | ★ | — |
| LBR | Liberia | ★ | — |
| GNB | Guinée-Bissau | ★ | — |
| GMB | Gambie | ★ | — |
| CPV | Cap-Vert | ★ | île, tarif propre malgré CEDEAO |

**Source principale** : Commission CEDEAO — Tarif Extérieur Commun (TEC)  
Format : Excel/PDF, nomenclature SH2017 à 8 chiffres  
URL : https://www.ecowas.int/trade/ → "Common External Tariff"  
Fiabilité cible : **PARTIAL/B** (Commission officielle mais pas douanes nationales)  
À compléter par : grilles taxes nationales NGA, GHA, CIV (lois de finances)

#### A2. TEC CEMAC — 6 pays
| ISO3 | Pays | Part commerce intra-Af. | Particularités |
|------|------|------------------------|----------------|
| CMR | Cameroun | ★★★ | surtaxe OHADA, TIC boissons/tabac |
| GAB | Gabon | ★★ | taxe pétrolière |
| TCD | Tchad | ★ | enclavé |
| CAF | Centrafrique | ★ | enclavé, post-conflit |
| COG | Congo | ★ | — |
| GNQ | Guinée équatoriale | ★ | — |

**Source principale** : Commission CEMAC (DERCA)  
Format : Excel, nomenclature SH à 8 chiffres  
URL : http://www.cemac.int / BEAC  
Fiabilité cible : **PARTIAL/B**  
À compléter par : taxes spécifiques CMR (code général des impôts)

#### A3. CET EAC — 8 pays
| ISO3 | Pays | Part commerce intra-Af. | Particularités |
|------|------|------------------------|----------------|
| KEN | Kenya | ★★★★ | excise duty, IDF 3.5 %, RDL 2 % |
| TZA | Tanzanie | ★★★ | excise, SDL, Railway Development Levy |
| UGA | Ouganda | ★★ | excise, infrastructure levy |
| RWA | Rwanda | ★★ | CRF 1.5 %, clean fuel levy |
| BDI | Burundi | ★ | — |
| COD | RD Congo | ★★ | adhésion 2022, harmonisation en cours |
| SSD | Soudan du Sud | ★ | post-conflit, données lacunaires |
| SOM | Somalie | ★ | adhésion 2023, données très lacunaires |

**Source principale** : Secrétariat EAC + Kenya Revenue Authority (KRA)  
Format : Excel (KRA publie un tariff schedule détaillé)  
URL : https://www.kra.go.ke/individual/important-information/rates/tariff  
Fiabilité cible : **PARTIAL/B** → **VERIFIED/A** pour KEN (KRA officiel)  
Note : COD et SOM appliquent le CET EAC partiellement, vérification nécessaire

#### A4. SACU — 5 pays
| ISO3 | Pays | Part commerce intra-Af. | Particularités |
|------|------|------------------------|----------------|
| ZAF | Afrique du Sud | ★★★★★ (22 %) | tarif le plus complet d'Afrique |
| NAM | Namibie | ★★ | additionnel sur véhicules |
| BWA | Botswana | ★★ | — |
| SWZ | Eswatini | ★ | — |
| LSO | Lesotho | ★ | enclavé |

**Source principale** : SARS — South African Revenue Service  
Format : tariff book en ligne (scrappable) + Excel téléchargeable  
URL : https://tariffbook.customs.gov.za/  
Fiabilité cible : **VERIFIED/A** (SARS = source officielle de référence)  
Note : ZAF est la source la plus fiable d'Afrique — SH10 + toutes taxes

---

### Groupe B — Tarifs nationaux individuels (20 pays)

| ISO3 | Pays | Priorité | Source principale identifiée | Disponibilité | Fiabilité cible |
|------|------|----------|------------------------------|---------------|-----------------|
| **DZA** | Algérie | ★★★★★ | conformepro.dz ✅ (fait) / DGD | PARTIAL/B ✅ | → VERIFIED/A |
| **EGY** | Égypte | ★★★★★ | Egyptian Customs Authority (ega.gov.eg) | Excel/XML | VERIFIED/A |
| **MAR** | Maroc | ★★★★ | ADII — tarif.douane.gov.ma | Portail scrappable | VERIFIED/A |
| **TUN** | Tunisie | ★★★ | Douane tunisienne (douane.gov.tn) | Excel/CSV | VERIFIED/A |
| **ETH** | Éthiopie | ★★★ | Ethiopian Customs Commission | PDF → parsing | PARTIAL/B |
| **AGO** | Angola | ★★★ | AGT — pauta.agt.minfin.gov.ao | Portail | PARTIAL/B |
| **MUS** | Maurice | ★★★ | Mauritius Revenue Authority (mra.mu) | Excel | VERIFIED/A |
| **ZMB** | Zambie | ★★ | Zambia Revenue Authority (zra.org.zm) | PDF | PARTIAL/B |
| **ZWE** | Zimbabwe | ★★ | ZIMRA (zimra.co.zw) | PDF | PARTIAL/B |
| **MOZ** | Mozambique | ★★ | AT Moçambique | PDF | PARTIAL/B |
| **MWI** | Malawi | ★★ | MRA Malawi (mra.mw) | PDF/Excel | PARTIAL/B |
| **MDG** | Madagascar | ★★ | Douanes Madagascar | PDF | PARTIAL/B |
| **SDN** | Soudan | ★ | Sudan Customs | disponibilité limitée | PARTIAL/C |
| **LBY** | Libye | ★ | Libyan Customs | très limitée | PARTIAL/C |
| **MRT** | Mauritanie | ★ | DGD Mauritanie | PDF | PARTIAL/B |
| **DJI** | Djibouti | ★ | Douanes Djibouti | limité | PARTIAL/C |
| **SYC** | Seychelles | ★ | Seychelles Revenue Commission | Excel | PARTIAL/B |
| **COM** | Comores | ★ | DGDCI Comores | très limité | PARTIAL/C |
| **STP** | São Tomé | ★ | Alfândega STP | très limité | PARTIAL/C |
| **ERI** | Érythrée | ★ | Customs Commission | quasi-inexistant | SYNTHETIC → C |

---

### Groupe C — Sources internationales (filet de sécurité tous pays)

Ces sources ne remplacent pas les tarifs nationaux mais permettent d'atteindre **PARTIAL/C** pour les pays difficiles.

| Source | Couverture | Chiffres SH | Taxes | Formalités | URL |
|--------|-----------|------------|-------|-----------|-----|
| **ITC MacMap** | 54/54 | SH6/8 | droits uniquement | non | macmap.org |
| **UNCTAD TRAINS / WITS** | 50/54 | SH6/8 | droits + para-tarifaires | non | wits.worldbank.org |
| **WTO Tariff Download** | 45/54 | SH6 | MFN + consolidés | non | tariffdata.wto.org |
| **TRALAC** | 54/54 | SH6 | droits ZLECAf | non | tralac.org |
| **UA — Listes de concessions ZLECAf** | 54/54 (progressif) | SH6 | taux préférentiels | non | au.int/en/trade |

---

## 3. Plan de mise en œuvre par vagues

### Vague 1 — Fondations (T3 2026) — 35 pays débloqués

**Objectif** : couvrir ≥ 80 % du commerce intra-africain avec des données PARTIAL/B minimum.

| Tâche | Pays | Lignes | Adaptateur | Délai estimé |
|-------|------|--------|-----------|-------------|
| TEC CEDEAO v1 | 15 pays | ~87 K | `cedeao_tec_adapter.py` | 2 semaines |
| CET EAC v1 (KRA) | KEN + 7 pays | ~65 K | `eac_cet_adapter.py` | 2 semaines |
| SACU/SARS | 5 pays | ~40 K | `sacu_sars_adapter.py` | 3 semaines |
| EGY natl. | EGY | ~16 K | `egy_customs_adapter.py` | 1 semaine |
| MAR natl. | MAR | ~16 K | `mar_adii_adapter.py` | 2 semaines |

**Résultat attendu** : 35 pays × ~16 K lignes = ~562 K lignes → PARTIAL/B  
DZA déjà en PARTIAL/B (✅)

### Vague 2 — Consolidation (T4 2026) — +12 pays

| Tâche | Pays | Adaptateur |
|-------|------|-----------|
| TEC CEMAC | CMR, GAB, TCD, CAF, COG, GNQ | `cemac_tec_adapter.py` |
| TUN, ETH | TUN, ETH | adaptateurs nationaux |
| ZAF SARS approfondi (SH10 + toutes taxes) | ZAF | upgrade `sacu_sars_adapter.py` |
| MUS, ZMB | MUS, ZMB | adaptateurs nationaux |
| NGA taxes spécifiques | NGA | `nga_taxes_adapter.py` |

### Vague 3 — Longue traîne (2027) — +17 pays restants

| Approche | Pays |
|---------|------|
| Sources nationales progressives | AGO, MOZ, MWI, MDG, ZWE |
| MacMap/TRAINS + validation manuelle | SDN, LBY, DJI, MRT, SYC, COM, STP |
| Cas particuliers (données très lacunaires) | ERI, SSD, SOM |

---

## 4. Spécifications techniques des adaptateurs

### 4.1 Interface commune (hérite de `BaseAdapter`)

```python
class CedeaoTecAdapter(BaseAdapter):
    SOURCE_NAME   = "TEC CEDEAO 2017 — Commission CEDEAO"
    SOURCE_URL    = "https://www.ecowas.int/trade/cet/"
    DATA_STATUS   = "PARTIAL"   # Commission officielle ≠ douanes nationales
    RELIABILITY   = "B"
    SCHEMA_VERSION = "4.0"
    COUNTRIES     = ["BEN","BFA","CPV","CIV","GMB","GHA",
                     "GIN","GNB","LBR","MLI","NER","NGA",
                     "SEN","SLE","TGO"]

    def parse_row(self, row: dict) -> CanonicalRecord:
        """Retourne un CanonicalRecord avec provenance PARTIAL/B."""
        ...

    def national_surcharges(self, iso3: str, hs8: str) -> list[Measure]:
        """Taxes nationales en sus du TEC (NGA, GHA, CIV…)."""
        ...
```

### 4.2 Règles de non-écrasement (idempotence)

```
SYNTHETIC  → peut être remplacé par PARTIAL ou VERIFIED
PARTIAL    → peut être remplacé par VERIFIED uniquement
VERIFIED   → jamais écrasé (sauf version_date plus récente)
```

### 4.3 Structure minimale d'une ligne migrée (PARTIAL/B)

```jsonc
{
  "commodity": { "national_code": "01011010", "hs6": "010110", "digits": 8, ... },
  "measures": [
    {
      "code": "D.D", "rate_pct": 20.0,
      "basis": "CIF", "sequence": 10
    }
  ],
  "provenance": {
    "data_status": "PARTIAL",
    "reliability": "B",
    "source_name": "TEC CEDEAO 2017 — Commission CEDEAO",
    "source_url": "https://www.ecowas.int/...",
    "version_date": "2017-01-01",
    "retrieved_at": "2026-07-01"
  },
  "schema_version": "4.0"
}
```

---

## 5. Ce que les sources ne fournissent pas — collecte complémentaire

Les tarifs régionaux et internationaux couvrent les **droits de douane**. Les éléments suivants nécessitent une collecte séparée :

| Élément | Problème | Solution |
|---------|---------|----------|
| **Taxes intérieures à l'import** (TVA, parafiscal, excise) | Non dans les TEC — dans les lois de finances nationales | Web scraping + veille législative par pays |
| **Méthode de calcul en cascade** | Spécifique à chaque pays | Code des douanes national (jurisprudence + circulaires) |
| **Formalités et documents** | Absents des sources tarifaires | Guichet unique national (quand disponible) ou GATT Art. VIII |
| **Listes de concessions ZLECAf** | Publiées au compte-gouttes par l'UA | Suivi trimestriel ua.int + notifications Secrétariat |
| **Annexe 1 — Catégories A/B/C** | Par pays, calendrier de démantèlement | À intégrer dans `fiscal_advantages[]` + champ `zlecaf_phase` |

---

## 6. Indicateurs de qualité cibles

| Indicateur | Aujourd'hui | Vague 1 | Vague 2 | Fin 2027 |
|-----------|-------------|---------|---------|---------|
| Pays VERIFIED/A | 0 / 54 | 1-2 / 54 | 5-8 / 54 | 15+ / 54 |
| Pays PARTIAL/B | 1 / 54 (DZA) | 34 / 54 | 46 / 54 | 50+ / 54 |
| Pays SYNTHETIC/D | 53 / 54 | 19 / 54 | 8 / 54 | < 4 / 54 |
| Lignes vérifiées | 0 | ~562 K | ~800 K | ~850 K+ |
| Couverture taxes en cascade | 1 pays (DZA) | 5-8 pays | 15+ pays | 30+ pays |
| Listes concessions ZLECAf | 0 | 10 pays | 25 pays | 40+ pays |

---

## 7. Fichiers et adaptateurs à créer

```
engine/
├── adapters/
│   ├── cedeao_tec_adapter.py ✅     # Vague 1 — TEC 15 pays (code prêt, en attente du CSV officiel)
│   ├── eac_cet_adapter.py           # Vague 1 — CET 8 pays (base KRA)
│   ├── sacu_sars_adapter.py         # Vague 1 — SACU 5 pays
│   ├── egy_customs_adapter.py       # Vague 1 — Égypte
│   ├── mar_adii_adapter.py          # Vague 1 — Maroc
│   ├── cemac_tec_adapter.py         # Vague 2 — TEC CEMAC
│   ├── tun_douane_adapter.py        # Vague 2 — Tunisie
│   ├── eth_customs_adapter.py       # Vague 2 — Éthiopie
│   ├── nga_taxes_adapter.py         # Vague 2 — taxes NGA spécifiques
│   └── macmap_fallback_adapter.py   # Vague 3 — filet ITC MacMap
├── scripts/
│   ├── mark_synthetic.py ✅         # marquage SYNTHETIC (fait)
│   ├── run_migration_wave.py        # runner par vague avec rapport
│   └── validate_adapter_output.py  # contrôles qualité post-migration
├── sources/
│   ├── cedeao_tec_2022.csv          # fichier source (non versionné — .gitignore)
│   ├── eac_cet_2022.xlsx
│   └── README_sources.md ✅        # SHA256 + URL de chaque fichier source
└── tests/
    ├── test_dza_conformepro_adapter.py ✅
    ├── test_calculation_dza.py ✅
    ├── test_cedeao_tec_adapter.py ✅
    └── test_sacu_sars_adapter.py    # à créer
```

---

## 8. Priorisation — décision immédiate

Le premier adaptateur à coder est **`cedeao_tec_adapter.py`** car :
1. Débloque 15 pays (27 % du total) en une seule collecte
2. NGA + GHA + CIV représentent ~40 % du commerce intra-africain
3. Le TEC CEDEAO est public et en Excel — pas de scraping nécessaire
4. La structure est proche de ce qui est déjà dans DZA (même nomenclature SH)

Ordre suggéré ensuite : `sacu_sars_adapter.py` → `eac_cet_adapter.py` → `mar_adii_adapter.py` → `egy_customs_adapter.py`

---

*Ce document est mis à jour à chaque vague d'ingestion. Pour le statut en temps réel, voir `engine/output/DATA_STATUS.json`.*

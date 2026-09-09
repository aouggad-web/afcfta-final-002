"""
TRS (Time Release Study) - Données Multi-Sources Complètes
============================================================
Expert Senior en Stratégie Maritime et Opérationnelle

Ce module contient:
1. DONNÉES OFFICIELLES WCO/TRS (priorité maximale)
2. DONNÉES DE SOURCES FIABLES DE 1ER PLAN (Autorités portuaires, TRS nationaux)
3. DONNÉES DE SOURCES SECONDAIRES (World Bank LPI, Rapports industriels)
4. ESTIMATIONS MÉTHODOLOGIQUES (avec avertissement et méthodologie explicite)

INTÉGRITÉ DES DONNÉES:
- Chaque donnée inclut: source, année, niveau de fiabilité
- Les estimations sont clairement identifiées avec méthodologie
- "NA" utilisé uniquement si aucune estimation fiable possible
"""

from typing import Any, Dict

# =============================================================================
# NIVEAUX DE FIABILITÉ DES SOURCES
# =============================================================================
SOURCE_RELIABILITY = {
    "OFFICIAL_WCO_TRS": {
        "level": 1,
        "label": "Officiel WCO",
        "description": "Étude Time Release Study officielle de l'Organisation Mondiale des Douanes",
        "warning": None,
        "color": "green",
    },
    "NATIONAL_TRS": {
        "level": 2,
        "label": "TRS National",
        "description": "Étude Time Release Study conduite par l'autorité douanière nationale",
        "warning": None,
        "color": "blue",
    },
    "PORT_AUTHORITY": {
        "level": 2,
        "label": "Autorité Portuaire",
        "description": "Données officielles de l'autorité portuaire nationale",
        "warning": None,
        "color": "blue",
    },
    "WORLD_BANK_LPI": {
        "level": 2,
        "label": "World Bank LPI",
        "description": "Logistics Performance Index - Données supply chain tracking",
        "warning": None,
        "color": "blue",
    },
    "WORLD_BANK_CPPI": {
        "level": 2,
        "label": "World Bank CPPI",
        "description": "Container Port Performance Index - Banque Mondiale",
        "warning": None,
        "color": "blue",
    },
    "CORRIDOR_OBSERVATORY": {
        "level": 2,
        "label": "Observatoire Corridor",
        "description": "Données d'observatoire régional de transport (ex: CCTTFA, NCTTCA)",
        "warning": None,
        "color": "blue",
    },
    "INDUSTRY_REPORT": {
        "level": 3,
        "label": "Rapport Industriel",
        "description": "Rapport de source industrielle vérifiée (shipping lines, terminaux)",
        "warning": "⚠️ Source industrielle: Données de rapports professionnels. Non issues d'études officielles.",
        "color": "yellow",
    },
    "ACADEMIC_STUDY": {
        "level": 3,
        "label": "Étude Académique",
        "description": "Publication académique ou étude de recherche",
        "warning": "⚠️ Source académique: Données de recherche. Vérification indépendante recommandée.",
        "color": "yellow",
    },
    "MEDIA_REPORT": {
        "level": 4,
        "label": "Rapport Média",
        "description": "Données issues de reportages médiatiques ou articles de presse",
        "warning": "⚠️ Source média: Données journalistiques. Fiabilité variable, à utiliser avec précaution.",
        "color": "orange",
    },
    "ESTIMATION_REGIONAL": {
        "level": 5,
        "label": "Estimation Régionale",
        "description": "Estimation basée sur données régionales et benchmarks comparatifs",
        "warning": "⚠️ ESTIMATION: Aucune donnée officielle disponible. Valeur estimée selon méthodologie ci-dessous.",
        "color": "red",
    },
    "ESTIMATION_MODEL": {
        "level": 5,
        "label": "Estimation Modélisée",
        "description": "Estimation basée sur modélisation et corrélations LPI/CPPI",
        "warning": "⚠️ ESTIMATION MODÉLISÉE: Basée sur corrélations statistiques. Non validée par mesure terrain.",
        "color": "red",
    },
    "NO_DATA": {
        "level": 99,
        "label": "NA",
        "description": "Aucune donnée disponible, estimation non fiable",
        "warning": None,
        "color": "gray",
    },
}

# =============================================================================
# DONNÉES TRS PAR PORT - COMPLÈTES
# =============================================================================
TRS_OFFICIAL_DATA: Dict[str, Dict[str, Any]] = {
    # =========================================================================
    # ALGÉRIE - DONNÉES LIMITÉES, ESTIMATIONS MÉTHODOLOGIQUES
    # =========================================================================
    "DZA-ALG-001": {  # Alger
        "container_dwell_time_days": 15,
        "source": "Estimation basée sur: (1) Incident juillet 2024: 21-24 jours de blocage, (2) Moyenne régionale Afrique du Nord, (3) Corrélation LPI Algérie",
        "source_type": "ESTIMATION_REGIONAL",
        "data_year": 2024,
        "publication_date": "2024-08",
        "methodology": "Estimation méthodologique multicritères",
        "estimation_methodology": """
MÉTHODOLOGIE D'ESTIMATION - PORT D'ALGER:

1. DONNÉES FACTUELLES DISPONIBLES:
   - Incident juillet-août 2024: Blocage de conteneurs pendant 21-24 jours (Maghreb Emergent)
   - Temps d'attente navires: 5-7 jours (Kuehne+Nagel, avril 2025)
   - Objectif gouvernemental: Réduire à 24h le séjour navire (non atteint)
   - Q1 2024: 64,917 EVP traités (+16% YoY)

2. BENCHMARKS COMPARATIFS:
   - LPI Algérie 2023: Score 2.4 (rang 117 mondial)
   - Moyenne Afrique du Nord (hors Tanger Med): 8-12 jours
   - Moyenne Afrique (AfDB): 20 jours

3. FACTEURS D'AJUSTEMENT:
   - Complexité réglementaire documentée
   - Incidents de blocage récurrents
   - Modernisation en cours mais non achevée

4. CALCUL:
   - Base régionale: 12 jours (moyenne Méditerranée Sud)
   - Ajustement LPI: +2 jours (score inférieur à Tunisie/Maroc)
   - Ajustement incidents: +1 jour (fréquence blocages)
   - ESTIMATION FINALE: 15 jours

ATTENTION: Cette estimation ne remplace pas une étude TRS officielle.
Aucune donnée TRS WCO n'existe pour ce port.
        """,
        "notes": "Estimation. Port majeur d'Algérie (2/3 du trafic). Blocage de 21-24j documenté en juillet 2024. Digitalisation en cours.",
        "factual_data_points": [
            "Blocage 21-24 jours (juillet-août 2024)",
            "Temps attente navires: 5-7 jours",
            "Q1 2024: 64,917 EVP (+16%)",
        ],
        "vessel_waiting_days": "5-7",
        "vessel_waiting_source": "Kuehne+Nagel Operational Update, Avril 2025",
        "teu_throughput_q1_2024": 64917,
        "vessel_turnaround_hours": "NA",
        "customs_clearance_hours": "NA",
        "cppi_rank": "NA",
        "cppi_year": "NA",
        "lpi_score": 2.4,
        "lpi_year": 2023,
        "warning": "⚠️ ESTIMATION: Aucune étude TRS officielle disponible pour ce port. Valeur estimée (15 jours) basée sur: incidents documentés (21-24j en juil.2024), temps d'attente navires (5-7j), et benchmarks régionaux. Méthodologie détaillée ci-dessous.",
        "no_official_data_reason": "L'Algérie n'a pas conduit d'étude TRS WCO. Les autorités portuaires ne publient pas de statistiques de dwell time.",
    },
    "DZA-ORA-001": {  # Oran
        "container_dwell_time_days": 12,
        "source": "Estimation basée sur: (1) Temps attente navires Oran: 3 jours, (2) Performance relative vs Alger, (3) Corrélation LPI",
        "source_type": "ESTIMATION_REGIONAL",
        "data_year": 2024,
        "publication_date": "2024",
        "methodology": "Estimation méthodologique comparative",
        "estimation_methodology": """
MÉTHODOLOGIE D'ESTIMATION - PORT D'ORAN:

1. DONNÉES FACTUELLES:
   - Temps d'attente navires: 3 jours (vs 5-7 pour Alger)
   - 2ème port d'Algérie en volume
   - Congestion moindre qu'Alger

2. BENCHMARKS:
   - Port d'Alger estimé: 15 jours
   - Ratio temps attente Oran/Alger: 3/6 = 0.5
   - Ajustement proportionnel attendu

3. CALCUL:
   - Base Alger: 15 jours
   - Ajustement congestion moindre: -20%
   - ESTIMATION: 12 jours

ATTENTION: Estimation sans validation terrain.
        """,
        "notes": "Estimation. 2ème port d'Algérie. Temps attente navires: 3 jours (meilleur qu'Alger).",
        "vessel_waiting_days": 3,
        "vessel_waiting_source": "Kuehne+Nagel, 2024",
        "vessel_turnaround_hours": "NA",
        "customs_clearance_hours": "NA",
        "cppi_rank": "NA",
        "cppi_year": "NA",
        "warning": "⚠️ ESTIMATION: Aucune donnée officielle. Estimation (12 jours) basée sur temps d'attente navires (3j) et comparaison avec Alger.",
        "no_official_data_reason": "Aucune étude TRS publiée. Données EPAL non disponibles publiquement.",
    },
    "DZA-BEJ-001": {  # Béjaïa
        "container_dwell_time_days": 13,
        "source": "Estimation basée sur données régionales et incident juillet 2024",
        "source_type": "ESTIMATION_REGIONAL",
        "data_year": 2024,
        "publication_date": "2024",
        "methodology": "Estimation par analogie régionale",
        "estimation_methodology": """
MÉTHODOLOGIE D'ESTIMATION - PORT DE BÉJAÏA:

1. DONNÉES FACTUELLES:
   - Mentionné dans incident blocage juillet 2024 (21-24 jours)
   - Port pétrolier et conteneurs
   - Volume inférieur à Alger et Oran

2. ESTIMATION:
   - Moyenne Alger (15) et Oran (12): 13.5 jours
   - Arrondi: 13 jours
        """,
        "notes": "Estimation. Port mixte (hydrocarbures + conteneurs). Impacté par incident juillet 2024.",
        "vessel_turnaround_hours": "NA",
        "customs_clearance_hours": "NA",
        "cppi_rank": "NA",
        "cppi_year": "NA",
        "warning": "⚠️ ESTIMATION: Valeur estimée (13 jours) par analogie avec autres ports algériens.",
        "no_official_data_reason": "Aucune donnée TRS ou statistique officielle publiée.",
    },
    # =========================================================================
    # MAROC - DONNÉES PARTIELLES
    # =========================================================================
    "MAR-TAN-001": {  # Tanger Med
        "container_dwell_time_days": 7.8,
        "source": "Beacon Port Congestion Report / Tanger Med Port Authority",
        "source_type": "INDUSTRY_REPORT",
        "data_year": 2024,
        "publication_date": "2024-09",
        "methodology": "Port Authority Statistics / Industry Analysis",
        "notes": "Données sept.2024. #4 CPPI mondial (2023). Hub transbordement majeur. 10.2M TEU en 2024 (+18.8%).",
        "vessel_turnaround_hours": "NA",
        "customs_clearance_hours": "NA",
        "cppi_rank": 4,
        "cppi_year": 2023,
        "teu_throughput_2024": 10241392,
        "warning": "⚠️ Source industrielle (Beacon). Performance exceptionnelle pour hub de transbordement.",
        "source_url": "https://www.beacon.com",
    },
    "MAR-CAS-001": {  # Casablanca
        "container_dwell_time_days": 8.4,
        "source": "Aujourd'hui le Maroc / ANP Maroc",
        "source_type": "PORT_AUTHORITY",
        "data_year": 2023,
        "publication_date": "2024-01",
        "methodology": "Port Authority Annual Report",
        "notes": "Import: 8.4j. Export: ~9j. Amélioration majeure vs 14 jours en 2007.",
        "vessel_turnaround_hours": "NA",
        "customs_clearance_hours": "NA",
        "cppi_rank": "NA",
        "cppi_year": "NA",
        "warning": None,
    },
    "MAR-AGD-001": {  # Agadir
        "container_dwell_time_days": 9,
        "source": "Estimation basée sur performance Casablanca et spécialisation pêche/agrumes",
        "source_type": "ESTIMATION_REGIONAL",
        "data_year": 2024,
        "publication_date": "2024",
        "methodology": "Estimation par analogie",
        "estimation_methodology": """
MÉTHODOLOGIE - PORT D'AGADIR:
- Base Casablanca: 8.4 jours
- Ajustement port secondaire: +0.5 jour
- Port spécialisé (pêche, agrumes): procédures différentes
- ESTIMATION: 9 jours
        """,
        "notes": "Estimation. Port spécialisé pêche et agrumes. Volume conteneurs limité.",
        "vessel_turnaround_hours": "NA",
        "customs_clearance_hours": "NA",
        "cppi_rank": "NA",
        "cppi_year": "NA",
        "warning": "⚠️ ESTIMATION: Basée sur analogie avec Casablanca. Port spécialisé.",
        "no_official_data_reason": "Pas de données TRS publiées. Port secondaire pour conteneurs.",
    },
    # =========================================================================
    # TUNISIE - ESTIMATIONS
    # =========================================================================
    "TUN-RAD-001": {  # Radès
        "container_dwell_time_days": 10,
        "source": "Estimation basée sur LPI Tunisie 2023 et benchmarks régionaux",
        "source_type": "ESTIMATION_MODEL",
        "data_year": 2024,
        "publication_date": "2024",
        "methodology": "Estimation par modélisation LPI",
        "estimation_methodology": """
MÉTHODOLOGIE - PORT DE RADÈS:

1. DONNÉES LPI TUNISIE 2023:
   - Score global: 2.4
   - Customs: 2.2
   - Timeliness: 2.8
   - Rang: 112 mondial

2. CORRÉLATION LPI-DWELL TIME:
   - LPI 2.4 → Dwell estimé: 10-12 jours (modèle régression)
   
3. BENCHMARKS COMPARATIFS:
   - Casablanca (LPI ~2.5): 8.4 jours
   - Alexandrie (LPI ~2.8): 8.64 jours
   
4. ESTIMATION: 10 jours (médiane basse de la fourchette)
        """,
        "notes": "Estimation. Principal port conteneurs de Tunisie. LPI 2023: 2.4.",
        "vessel_turnaround_hours": "NA",
        "customs_clearance_hours": "NA",
        "cppi_rank": "NA",
        "cppi_year": "NA",
        "lpi_score": 2.4,
        "lpi_year": 2023,
        "warning": "⚠️ ESTIMATION MODÉLISÉE: Basée sur corrélation LPI-dwell time. Score LPI Tunisie: 2.4. Aucune étude TRS officielle.",
        "no_official_data_reason": "Tunisie n'a pas publié d'étude TRS. OMMP ne publie pas de statistiques dwell time.",
    },
    "TUN-SFX-001": {  # Sfax
        "container_dwell_time_days": 11,
        "source": "Estimation basée sur Radès + ajustement port secondaire",
        "source_type": "ESTIMATION_REGIONAL",
        "data_year": 2024,
        "publication_date": "2024",
        "methodology": "Estimation par analogie",
        "notes": "Estimation. Port secondaire, trafic phosphates important.",
        "vessel_turnaround_hours": "NA",
        "customs_clearance_hours": "NA",
        "cppi_rank": "NA",
        "cppi_year": "NA",
        "warning": "⚠️ ESTIMATION: Port secondaire. Basée sur Radès (+1 jour).",
        "no_official_data_reason": "Aucune donnée publiée.",
    },
    # =========================================================================
    # ÉGYPTE - DONNÉES TRS OFFICIELLES NATIONALES
    # =========================================================================
    "EGY-ALE-001": {  # Alexandrie
        "container_dwell_time_days": 8.64,
        "source": "Egypt Customs Authority - Time Release Study #2",
        "source_type": "NATIONAL_TRS",
        "data_year": 2024,
        "publication_date": "2024-04",
        "methodology": "National Time Release Study (21-27 April 2024)",
        "notes": "Réduction de 46.1% vs TRS#1 (2021: 16.08 jours). Amélioration majeure.",
        "trs_2021_baseline_days": 16.08,
        "improvement_percent": 46.1,
        "vessel_turnaround_hours": "NA",
        "customs_clearance_hours": "NA",
        "anchor_to_unload_days": 1.04,
        "unloading_duration_hours": 11.35,
        "cppi_rank": "NA",
        "cppi_year": "NA",
        "source_url": "https://assets.mof.gov.eg/files/d06136d0-b7aa-11ef-9d21-798cef5fccf4.pdf",
        "warning": None,
    },
    "EGY-DAM-001": {  # Damiette
        "container_dwell_time_days": 8.09,
        "source": "Egypt Customs Authority - Time Release Study #2",
        "source_type": "NATIONAL_TRS",
        "data_year": 2024,
        "publication_date": "2024-04",
        "methodology": "National Time Release Study (21-27 April 2024)",
        "notes": "Inclus dans TRS nationale. Performance légèrement meilleure qu'Alexandrie.",
        "vessel_turnaround_hours": "NA",
        "customs_clearance_hours": "NA",
        "cppi_rank": "NA",
        "cppi_year": "NA",
        "source_url": "https://assets.mof.gov.eg/files/d06136d0-b7aa-11ef-9d21-798cef5fccf4.pdf",
        "warning": None,
    },
    "EGY-PSD-001": {  # Port Saïd
        "container_dwell_time_days": "NA",
        "source": "NA - Hub de transbordement",
        "source_type": "NO_DATA",
        "data_year": "NA",
        "publication_date": "NA",
        "methodology": "NA",
        "notes": "Non inclus dans TRS#2. Hub transbordement (majorité cargo ne passe pas douane).",
        "vessel_turnaround_hours": "NA",
        "customs_clearance_hours": "NA",
        "cppi_rank": "NA",
        "cppi_year": "NA",
        "warning": None,
        "no_official_data_reason": "Hub de transbordement - dwell time import non pertinent.",
    },
    # =========================================================================
    # LIBYE - DONNÉES LIMITÉES
    # =========================================================================
    "LBY-TRP-001": {  # Tripoli
        "container_dwell_time_days": "NA",
        "source": "NA",
        "source_type": "NO_DATA",
        "data_year": "NA",
        "publication_date": "NA",
        "methodology": "NA",
        "notes": "Aucune donnée fiable. Contexte sécuritaire instable depuis 2011.",
        "vessel_turnaround_hours": "NA",
        "customs_clearance_hours": "NA",
        "cppi_rank": "NA",
        "cppi_year": "NA",
        "warning": None,
        "no_official_data_reason": "Instabilité politique. Aucune statistique fiable disponible depuis 2011.",
    },
    # =========================================================================
    # AFRIQUE DU SUD - DONNÉES OFFICIELLES
    # =========================================================================
    "ZAF-DUR-001": {  # Durban
        "container_dwell_time_days": 2.7,
        "source": "Transnet Port Terminals Official Report",
        "source_type": "PORT_AUTHORITY",
        "data_year": 2024,
        "publication_date": "2024-Q4",
        "methodology": "Transnet Performance Metrics",
        "notes": "Pier 1 Import. Amélioration majeure vs 21 jours précédemment.",
        "vessel_turnaround_hours": 83.2,
        "vessel_turnaround_source": "SAAFF Analysis 2023 (Pier 2)",
        "customs_clearance_hours": "NA",
        "cppi_rank": "NA",
        "cppi_year": 2023,
        "warning": None,
    },
    "ZAF-CPT-001": {  # Cape Town
        "container_dwell_time_days": 5.3,
        "source": "World Bank LPI 2023 - Supply Chain Tracking (South Africa national average)",
        "source_type": "WORLD_BANK_LPI",
        "data_year": 2023,
        "publication_date": "2023-04",
        "methodology": "LPI Supply Chain Tracking - Consolidated Dwell Time",
        "notes": "Moyenne nationale Afrique du Sud. Cape Town légèrement meilleur que moyenne.",
        "lpi_observations": 41097,
        "lpi_mean_days": 5.3,
        "lpi_median_days": 3.7,
        "lpi_p25_days": 2.5,
        "lpi_p75_days": 5.5,
        "vessel_turnaround_hours": "NA",
        "customs_clearance_hours": "NA",
        "cppi_rank": 405,
        "cppi_improvement_points": 237.9,
        "cppi_year": 2024,
        "warning": "⚠️ Donnée nationale LPI appliquée au port. Dwell time spécifique Cape Town non publié.",
    },
    # =========================================================================
    # NAMIBIE - DONNÉES WCO OFFICIELLES
    # =========================================================================
    "NAM-WAL-001": {  # Walvis Bay
        "container_dwell_time_days": "NA",
        "source": "WCO / NAMRA Time Release Study Report",
        "source_type": "OFFICIAL_WCO_TRS",
        "data_year": 2023,
        "publication_date": "2023-12-01",
        "methodology": "WCO Time Release Study (Standard)",
        "notes": "Étude TRS WCO publiée. Temps total non synthétisé dans rapport public. Goulots identifiés: ASYCUDA, inspections hors-port.",
        "vessel_turnaround_hours": "NA",
        "customs_clearance_hours": "NA",
        "wco_trs_published": True,
        "wco_report_url": "https://www.namra.org.na/documents/cms/uploaded/time-release-study-report--1-december-2023-9de0a050c1.pdf",
        "cppi_rank": "NA",
        "cppi_year": "NA",
        "warning": None,
        "no_official_data_reason": "Étude TRS WCO conduite mais temps total non publié de manière synthétique.",
    },
    # =========================================================================
    # KENYA - DONNÉES OFFICIELLES KPA
    # =========================================================================
    "KEN-MBA-001": {  # Mombasa
        "container_dwell_time_days": 3.5,
        "source": "Kenya Ports Authority (KPA) Official Statistics",
        "source_type": "PORT_AUTHORITY",
        "data_year": 2023,
        "publication_date": "2024-01",
        "methodology": "KPA Annual Performance Report",
        "notes": "Moyenne 2023. Amélioration vs 3.9j (2022). Record avril 2024: 2.73 jours.",
        "vessel_turnaround_hours": 64.1,
        "customs_clearance_hours": "NA",
        "target_dwell_hours": 60,
        "best_performance_days": 2.73,
        "best_performance_date": "2024-04",
        "cppi_rank": 335,
        "cppi_year": 2023,
        "warning": None,
    },
    # =========================================================================
    # TANZANIE - DONNÉES OBSERVATOIRE CORRIDOR
    # =========================================================================
    "TZA-DAR-001": {  # Dar es Salaam
        "container_dwell_time_days": 7.4,
        "source": "Central Corridor Transport Observatory (CCTTFA) / TASAC Statistical Bulletin 2023",
        "source_type": "CORRIDOR_OBSERVATORY",
        "data_year": 2023,
        "publication_date": "2024",
        "methodology": "Corridor Observatory Monitoring",
        "notes": "CCTTFA: 7.4j. TASAC Terminal I: 9.0j (↓ de 12.3j en 2022). Terminal II: 10.9j. Cible: 5 jours.",
        "terminal_1_dwell_days": 9.0,
        "terminal_2_dwell_days": 10.9,
        "target_dwell_days": 5,
        "previous_year_terminal_1": 12.3,
        "ship_turnaround_days": "7.2-12.5",
        "vessel_turnaround_hours": "NA",
        "customs_clearance_hours": "NA",
        "cppi_rank": "NA",
        "cppi_year": "NA",
        "source_url": "https://www.tasac.go.tz/uploads/documents/sw-1712132995-TASAC%20ANNUAL%20STATISTICAL%20BULLETIN%202023.pdf",
        "warning": None,
    },
    # =========================================================================
    # NIGÉRIA - DONNÉES MULTIPLES
    # =========================================================================
    "NGA-LAG-001": {  # Apapa Lagos
        "container_dwell_time_days": 16.2,
        "source": "World Bank LPI 2023 - Supply Chain Tracking (Nigeria consolidated)",
        "source_type": "WORLD_BANK_LPI",
        "data_year": 2023,
        "publication_date": "2023-04",
        "methodology": "LPI Supply Chain Tracking",
        "notes": "Moyenne nationale Nigeria. 26,953 observations. Médiane: 12.5j. P75: 20.2j.",
        "lpi_observations": 26953,
        "lpi_mean_days": 16.2,
        "lpi_median_days": 12.5,
        "lpi_p25_days": 7.5,
        "lpi_p75_days": 20.2,
        "vessel_turnaround_hours": "NA",
        "customs_clearance_hours": "NA",
        "cppi_rank": "NA",
        "cppi_year": "NA",
        "warning": None,
    },
    "NGA-TIN-001": {  # Tin Can Island
        "container_dwell_time_days": "NA",
        "source": "WCO - Time Release Study Launched",
        "source_type": "OFFICIAL_WCO_TRS",
        "data_year": 2024,
        "publication_date": "2024-02",
        "methodology": "WCO TRS (En cours)",
        "notes": "TRS WCO lancée février 2024. Résultats attendus. Premier d'une série au Nigeria.",
        "vessel_turnaround_hours": "NA",
        "customs_clearance_hours": "NA",
        "wco_trs_in_progress": True,
        "cppi_rank": "NA",
        "cppi_year": "NA",
        "warning": None,
    },
    "NGA-LEK-001": {  # Lekki Deep Sea Port
        "container_dwell_time_days": 16,
        "source": "Lekki Port Authority / Maritime Today Online",
        "source_type": "PORT_AUTHORITY",
        "data_year": 2025,
        "publication_date": "2025-06",
        "methodology": "Port Operations Report",
        "notes": "Port nouveau (2023). Vessel turnaround: 48h. Truck turnaround: <1h25. Objectif: réduction via digitalisation.",
        "vessel_turnaround_hours": 48,
        "truck_turnaround_minutes": 85,
        "truck_park_dwell_days": 10,
        "customs_clearance_hours": "NA",
        "cppi_rank": "NA",
        "cppi_year": "NA",
        "teu_throughput_2024": 54000,
        "teu_projection_2025": 500000,
        "warning": "⚠️ Port nouveau (2023). Performance en évolution rapide.",
    },
    # =========================================================================
    # CÔTE D'IVOIRE - DONNÉES PAA
    # =========================================================================
    "CIV-ABJ-001": {  # Abidjan
        "container_dwell_time_days": 3.54,
        "source": "Port Autonome d'Abidjan - PAA Infos Magazine #112",
        "source_type": "PORT_AUTHORITY",
        "data_year": 2023,
        "publication_date": "2023-08",
        "methodology": "Port Authority Statistics",
        "notes": "Excellente performance. Ancrage: 0.58j (vs 0.88j Q1 2022). Cargo local: 3-5j. Transit: 5j.",
        "anchorage_wait_days_2023": 0.58,
        "anchorage_wait_days_2022_q1": 0.88,
        "local_cargo_dwell_range": "3-5",
        "transit_cargo_dwell_days": 5,
        "vessel_turnaround_hours": "NA",
        "customs_clearance_hours": "NA",
        "cppi_rank": "NA",
        "cppi_year": "NA",
        "source_url": "https://www.portabidjan.ci/sites/default/files/paa_infos_magazine_ndeg112_-_juillet_et_aout_2023.pdf",
        "warning": None,
    },
    # =========================================================================
    # SÉNÉGAL
    # =========================================================================
    "SEN-DKR-001": {  # Dakar
        "container_dwell_time_days": 7,
        "source": "PPIAF / World Bank Shadow Rating Simulation",
        "source_type": "WORLD_BANK_CPPI",
        "data_year": 2018,
        "publication_date": "2020-12",
        "methodology": "World Bank Analysis",
        "notes": "Donnée 2018. #1 CPPI Sub-Saharan Africa 2024 (+104.7 points). Performance actuelle probablement meilleure.",
        "vessel_turnaround_hours": "NA",
        "customs_clearance_hours": "NA",
        "cppi_rank": 1,
        "cppi_region": "Sub-Saharan Africa",
        "cppi_score_improvement": 104.7,
        "cppi_year": 2024,
        "monthly_throughput_teu_2024": 77680,
        "warning": "⚠️ Donnée 2018. Performance CPPI 2024 (#1 SSA) suggère amélioration significative.",
    },
    # =========================================================================
    # GHANA
    # =========================================================================
    "GHA-TEM-001": {  # Tema
        "container_dwell_time_days": "6-12",
        "source": "Ghana News / GPHA Reports (estimations industrielles)",
        "source_type": "INDUSTRY_REPORT",
        "data_year": 2024,
        "publication_date": "2024",
        "methodology": "Industry Analysis",
        "notes": "Fourchette estimée. ICUMS permet clearance rapide si docs complets. 95% du trafic Ghana.",
        "vessel_turnaround_hours": "NA",
        "customs_clearance_hours": "NA",
        "cppi_rank": "NA",
        "cppi_year": "NA",
        "teu_throughput_2024": 1668688,
        "percent_ghana_traffic": 95,
        "warning": "⚠️ Fourchette indicative (6-12 jours). Non issue d'étude TRS officielle.",
    },
    # =========================================================================
    # TOGO - DONNÉES RÉCENTES
    # =========================================================================
    "TGO-LOM-001": {  # Lomé
        "container_dwell_time_days": 4.2,
        "source": "Ecofinagency / Industry Analysis 2025",
        "source_type": "INDUSTRY_REPORT",
        "data_year": 2025,
        "publication_date": "2025-Q1",
        "methodology": "Industry Performance Comparison",
        "notes": "Port le plus efficace d'Afrique de l'Ouest. Hub transbordement. Comparé: Apapa 18.4j (mars 2025).",
        "vessel_turnaround_hours": "NA",
        "customs_clearance_hours": "NA",
        "port_stay_range_days_2024": "0.7-2.5",
        "cppi_rank": "NA",
        "cppi_year": "NA",
        "teu_throughput_annual": 2000000,
        "source_url": "https://www.ecofinagency.com/news/1509-48695-lome-port-helps-togo-overtaking-south-africa-as-nigeria-s-main-african-trade-gateway-on-q2",
        "warning": "⚠️ Source industrielle (Ecofinagency 2025). Performance exceptionnelle pour hub transbordement.",
    },
    # =========================================================================
    # BÉNIN
    # =========================================================================
    "BEN-COT-001": {  # Cotonou
        "container_dwell_time_days": 8,
        "source": "Estimation basée sur amélioration CPPI (+226.7 points) et benchmarks régionaux",
        "source_type": "ESTIMATION_MODEL",
        "data_year": 2024,
        "publication_date": "2024",
        "methodology": "Estimation basée sur évolution CPPI et comparaison Lomé/Abidjan",
        "estimation_methodology": """
MÉTHODOLOGIE - PORT DE COTONOU:

1. DONNÉES CPPI 2024:
   - Rang 401/405 (2023) mais amélioration +226.7 points
   - Investissements majeurs en infrastructure

2. BENCHMARKS RÉGIONAUX:
   - Lomé: 4.2 jours (meilleur)
   - Abidjan: 3.54 jours
   - Ghana: 6-12 jours

3. ESTIMATION:
   - Base régionale: ~10 jours (hors leaders)
   - Ajustement amélioration CPPI: -2 jours
   - ESTIMATION: 8 jours
        """,
        "notes": "Estimation. CPPI amélioration +226.7 points. Nouveaux équipements.",
        "vessel_turnaround_hours": "NA",
        "customs_clearance_hours": "NA",
        "cppi_rank": 401,
        "cppi_improvement_points": 226.7,
        "cppi_year": 2024,
        "warning": "⚠️ ESTIMATION: Basée sur amélioration CPPI significative et benchmarks régionaux.",
        "no_official_data_reason": "Aucune étude TRS publiée.",
    },
    # =========================================================================
    # CAMEROUN
    # =========================================================================
    "CMR-DLA-001": {  # Douala
        "container_dwell_time_days": 12,
        "source": "Estimation basée sur free time (10j) et contexte opérationnel",
        "source_type": "ESTIMATION_REGIONAL",
        "data_year": 2024,
        "publication_date": "2024",
        "methodology": "Estimation basée sur franchise et facteurs régionaux",
        "estimation_methodology": """
MÉTHODOLOGIE - PORT DE DOUALA:

1. DONNÉES FACTUELLES:
   - Free time (franchise): 10 jours
   - LSCI +54% en 2024 (meilleure progression Afrique)
   - Congestion historique documentée

2. RELATION FREE TIME / DWELL TIME:
   - Free time est généralement < dwell time réel
   - Facteur typique: dwell = free time × 1.2

3. ESTIMATION:
   - 10 jours × 1.2 = 12 jours
        """,
        "notes": "Estimation. Free time: 10 jours. LSCI +54% en 2024. Congestion historique.",
        "free_time_days": 10,
        "demurrage_start_day": 11,
        "vessel_turnaround_hours": "NA",
        "customs_clearance_hours": "NA",
        "cppi_rank": "NA",
        "cppi_year": "NA",
        "lsci_improvement_2024_percent": 54,
        "warning": "⚠️ ESTIMATION: Basée sur free time (10j) × facteur 1.2. Amélioration LSCI +54%.",
        "no_official_data_reason": "PAD ne publie pas de statistiques dwell time.",
    },
    "CMR-KRI-001": {  # Kribi
        "container_dwell_time_days": 8,
        "source": "Estimation basée sur infrastructure moderne et LSCI",
        "source_type": "ESTIMATION_REGIONAL",
        "data_year": 2024,
        "publication_date": "2024",
        "methodology": "Estimation port moderne",
        "notes": "Estimation. Port en eau profonde moderne. LSCI +54% en 2024.",
        "vessel_turnaround_hours": "NA",
        "customs_clearance_hours": "NA",
        "cppi_rank": "NA",
        "cppi_year": "NA",
        "warning": "⚠️ ESTIMATION: Port moderne, performance attendue meilleure que Douala.",
        "no_official_data_reason": "Port récent, peu de données publiées.",
    },
    # =========================================================================
    # DJIBOUTI
    # =========================================================================
    "DJI-DJI-001": {  # Djibouti / Doraleh
        "container_dwell_time_days": 6,
        "source": "Estimation basée sur efficacité opérationnelle documentée et controverse CPPI",
        "source_type": "ESTIMATION_MODEL",
        "data_year": 2024,
        "publication_date": "2024",
        "methodology": "Estimation basée sur performance opérationnelle",
        "estimation_methodology": """
MÉTHODOLOGIE - PORT DE DJIBOUTI:

1. DONNÉES OPÉRATIONNELLES:
   - Record 1.24M TEU en 2024
   - Productivité quai: 120 mouvements/heure
   - CPPI 2022: rang 26 (avant controverse)
   - CPPI 2023: rang 379 (contesté par Djibouti)

2. BENCHMARKS RÉGIONAUX:
   - Mombasa: 3.5 jours (comparable en volume)
   - Dar es Salaam: 7.4 jours

3. ESTIMATION:
   - Performance opérationnelle suggère efficacité
   - Cible estimée: ~6 jours
        """,
        "notes": "Estimation. Record 1.24M TEU 2024. CPPI controversé. Productivité: 120 mvts/h.",
        "vessel_turnaround_hours": "NA",
        "customs_clearance_hours": "NA",
        "quay_productivity_moves_per_hour": 120,
        "utilization_percent": 40,
        "teu_throughput_2024": 1236769,
        "cppi_rank": 379,
        "cppi_2022_rank": 26,
        "cppi_year": 2023,
        "warning": "⚠️ ESTIMATION: Basée sur efficacité opérationnelle. Rang CPPI controversé.",
        "no_official_data_reason": "DPFZA ne publie pas de dwell time cargo. Controverse CPPI 2023.",
    },
    # =========================================================================
    # GABON
    # =========================================================================
    "GAB-LBV-001": {  # Owendo/Libreville
        "container_dwell_time_days": 10,
        "source": "Estimation régionale Afrique Centrale",
        "source_type": "ESTIMATION_REGIONAL",
        "data_year": 2024,
        "publication_date": "2024",
        "methodology": "Estimation par analogie régionale",
        "notes": "Estimation. Moyenne régionale Afrique Centrale appliquée.",
        "vessel_turnaround_hours": "NA",
        "customs_clearance_hours": "NA",
        "cppi_rank": "NA",
        "cppi_year": "NA",
        "warning": "⚠️ ESTIMATION: Moyenne régionale. Aucune donnée spécifique.",
        "no_official_data_reason": "GPM ne publie pas de statistiques.",
    },
    # =========================================================================
    # CONGO
    # =========================================================================
    "COG-PNR-001": {  # Pointe-Noire
        "container_dwell_time_days": 10,
        "source": "Estimation basée sur temps attente navires (3.08j) et contexte régional",
        "source_type": "ESTIMATION_REGIONAL",
        "data_year": 2024,
        "publication_date": "2024",
        "methodology": "Estimation multicritères",
        "notes": "Estimation. Temps attente navires: 3.08 jours. Principal port Congo.",
        "vessel_waiting_days": 3.08,
        "vessel_turnaround_hours": "NA",
        "customs_clearance_hours": "NA",
        "cppi_rank": "NA",
        "cppi_year": "NA",
        "warning": "⚠️ ESTIMATION: Basée sur temps attente navires et contexte régional.",
        "no_official_data_reason": "PAPN ne publie pas de statistiques dwell.",
    },
    # =========================================================================
    # ANGOLA
    # =========================================================================
    "AGO-LUA-001": {  # Luanda
        "container_dwell_time_days": 14,
        "source": "Estimation basée sur contexte économique et nouveau dry port",
        "source_type": "ESTIMATION_REGIONAL",
        "data_year": 2024,
        "publication_date": "2024",
        "methodology": "Estimation contextuelle",
        "notes": "Estimation. Nouveau dry port (3500-5000 conteneurs) pour décongestion. 2/3 trafic Angola.",
        "vessel_turnaround_hours": "NA",
        "customs_clearance_hours": "NA",
        "cppi_rank": "NA",
        "cppi_year": "NA",
        "warning": "⚠️ ESTIMATION: Contexte économique et congestion historique.",
        "no_official_data_reason": "Entreprise Portuária de Luanda ne publie pas de données.",
    },
    # =========================================================================
    # MOZAMBIQUE
    # =========================================================================
    "MOZ-MPM-001": {  # Maputo
        "container_dwell_time_days": 10,
        "source": "Estimation basée sur CPPI rang 325 et expansion en cours",
        "source_type": "ESTIMATION_MODEL",
        "data_year": 2024,
        "publication_date": "2024",
        "methodology": "Estimation corrélation CPPI",
        "notes": "Estimation. CPPI rang 325. Expansion capacité 255k→530k TEU prévue.",
        "vessel_turnaround_hours": "NA",
        "customs_clearance_hours": "NA",
        "cppi_rank": 325,
        "cppi_year": 2023,
        "expansion_target_teu": 530000,
        "warning": "⚠️ ESTIMATION: Basée sur rang CPPI et benchmarks régionaux.",
        "no_official_data_reason": "MPDC ne publie pas de dwell time.",
    },
    # =========================================================================
    # MAURICE
    # =========================================================================
    "MUS-PLO-001": {  # Port Louis
        "container_dwell_time_days": 5,
        "source": "Estimation basée sur efficacité documentée et hub freeport",
        "source_type": "ESTIMATION_MODEL",
        "data_year": 2024,
        "publication_date": "2024",
        "methodology": "Estimation hub efficiency",
        "notes": "Estimation. Hub transbordement efficace. Mauritius Freeport.",
        "vessel_turnaround_hours": "NA",
        "customs_clearance_hours": "NA",
        "cppi_rank": "NA",
        "cppi_year": "NA",
        "warning": "⚠️ ESTIMATION: Hub freeport, efficacité attendue élevée.",
        "no_official_data_reason": "MPA ne publie pas de statistiques dwell.",
    },
    # =========================================================================
    # MADAGASCAR
    # =========================================================================
    "MDG-TMM-001": {  # Toamasina
        "container_dwell_time_days": 12,
        "source": "Estimation régionale océan Indien",
        "source_type": "ESTIMATION_REGIONAL",
        "data_year": 2024,
        "publication_date": "2024",
        "methodology": "Estimation régionale",
        "notes": "Estimation. Principal port de Madagascar.",
        "vessel_turnaround_hours": "NA",
        "customs_clearance_hours": "NA",
        "cppi_rank": "NA",
        "cppi_year": "NA",
        "warning": "⚠️ ESTIMATION: Moyenne régionale appliquée.",
        "no_official_data_reason": "SPAT ne publie pas de statistiques.",
    },
}

# =============================================================================
# DONNÉES LPI WORLD BANK 2023 - SUPPLY CHAIN TRACKING
# =============================================================================
LPI_2023_DATA = {
    "ZAF": {
        "overall": 3.7,
        "customs": 3.3,
        "timeliness": 3.8,
        "rank": 19,
        "import_dwell_mean": 5.3,
        "import_dwell_median": 3.7,
        "observations": 41097,
    },
    "NGA": {
        "overall": 2.6,
        "customs": 2.4,
        "timeliness": 3.1,
        "rank": 88,
        "import_dwell_mean": 16.2,
        "import_dwell_median": 12.5,
        "observations": 26953,
    },
    "TGO": {
        "overall": 2.5,
        "customs": 2.2,
        "timeliness": 2.9,
        "rank": 105,
        "import_dwell_mean": 8.1,
        "import_dwell_median": 4.6,
        "observations": 7118,
    },
    "SOM": {"import_dwell_mean": 7.3, "import_dwell_median": 5.0, "observations": 3767},
    "NER": {"import_dwell_mean": 16.6, "import_dwell_median": 15.3, "observations": 33},
    "ZWE": {"import_dwell_mean": 12.8, "import_dwell_median": 11.8, "observations": 176},
    "CIV": {"overall": 2.8, "customs": 2.4, "timeliness": 3.2, "rank": 79},
    "RWA": {"overall": 2.8, "customs": 2.5, "timeliness": 3.1, "rank": 73},
    "KEN": {"overall": 2.8, "customs": 2.6, "timeliness": 3.3, "rank": 68},
    "EGY": {"overall": 2.8, "customs": 2.5, "timeliness": 3.0, "rank": 77},
    "GHA": {"overall": 2.6, "customs": 2.3, "timeliness": 3.0, "rank": 95},
    "SEN": {"overall": 2.6, "customs": 2.4, "timeliness": 3.0, "rank": 92},
    "TZA": {"overall": 2.5, "customs": 2.3, "timeliness": 2.9, "rank": 100},
    "CMR": {"overall": 2.4, "customs": 2.1, "timeliness": 2.8, "rank": 115},
    "MAR": {"overall": 2.5, "customs": 2.3, "timeliness": 2.8, "rank": 106},
    "DZA": {"overall": 2.4, "customs": 2.2, "timeliness": 2.7, "rank": 117},
    "TUN": {"overall": 2.4, "customs": 2.2, "timeliness": 2.8, "rank": 112},
}

# =============================================================================
# BENCHMARKS GLOBAUX
# =============================================================================
GLOBAL_BENCHMARKS = {
    "container_dwell_time_days_global_median_h1_2023": 0.7,
    "container_dwell_time_days_global_median_h2_2023": 1.1,
    "container_dwell_time_days_africa_avg": 20,
    "container_dwell_time_days_africa_avg_source": "African Development Bank",
    "container_dwell_time_days_afdb_note": "Moyenne continentale indicative. Performance très variable selon les ports (2.7 à 20+ jours).",
    "container_handling_time_seconds_2023": 36,
    "global_benchmark_efficient_port_days": 4,
    "source": "UNCTAD Review of Maritime Transport 2024 / African Development Bank / World Bank",
}

# =============================================================================
# NOTE IMPORTANTE SUR LA COUVERTURE TRS
# =============================================================================
TRS_COVERAGE_NOTE = """
📊 NOTE IMPORTANTE SUR LA COUVERTURE DES DONNÉES TRS

La couverture des données TRS vérifiées pour les ports africains reste limitée.
Pour maintenir l'intégrité des données, nous distinguons clairement:

NIVEAU 1-2: DONNÉES OFFICIELLES/FIABLES
• Études TRS WCO officielles (Namibie)
• TRS nationales (Égypte)
• Données autorités portuaires (KPA Kenya, Transnet SA, PAA Côte d'Ivoire)
• World Bank LPI Supply Chain Tracking

NIVEAU 3-4: SOURCES SECONDAIRES
• Rapports industriels (Beacon, Ecofinagency)
• Publications académiques
• Articles de presse spécialisée

NIVEAU 5: ESTIMATIONS MÉTHODOLOGIQUES
• Clairement identifiées avec le symbole ⚠️
• Méthodologie d'estimation documentée
• Basées sur: benchmarks régionaux, corrélations LPI, données contextuelles
• À utiliser comme INDICATION uniquement

Pour les ports sans données:
• "NA" = Aucune estimation fiable possible
• Raison de l'absence de données documentée
"""


def get_trs_data(port_id: str) -> dict:
    """Récupère les données TRS pour un port."""
    return TRS_OFFICIAL_DATA.get(
        port_id,
        {
            "container_dwell_time_days": "NA",
            "source": "NA",
            "source_type": "NO_DATA",
            "data_year": "NA",
            "notes": "Aucune donnée TRS disponible pour ce port.",
            "no_official_data_reason": "Port non répertorié dans la base de données.",
        },
    )


def get_source_reliability(source_type: str) -> dict:
    """Récupère les informations de fiabilité d'une source."""
    return SOURCE_RELIABILITY.get(source_type, SOURCE_RELIABILITY["NO_DATA"])


def get_lpi_data(country_iso: str) -> dict:
    """Récupère les données LPI 2023 pour un pays."""
    return LPI_2023_DATA.get(country_iso, {})

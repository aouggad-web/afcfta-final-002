
import json
from pathlib import Path

# Charger les données existantes
json_path = '/app/projets_structurants_afrique.json'
try:
    with open(json_path, 'r', encoding='utf-8') as f:
        existing_projects = json.load(f)
except FileNotFoundError:
    existing_projects = {}

# NOUVEAUX PROJETS (Extrait des recherches)
NEW_PROJECTS = {
    # AFRIQUE DE L'EST
    "KEN": [
        {
            "titre": "LAPSSET Corridor (Lamu-Garissa)",
            "secteur": "Transport & Logistique",
            "statut": "En construction (Phase 1)",
            "budget": "2.5 Mrd USD (Est.)",
            "echeance": "2025 (Route Lamu-Garissa)",
            "description": "Corridor de transport majeur reliant le nouveau port de Lamu à l'Éthiopie et au Soudan du Sud via Garissa. Inclut routes, pipeline et aéroports.",
            "impact": "Désenclavement du Nord Kenya. Nouvelle porte d'entrée pour l'Afrique de l'Est.",
            "partenaires": "LAPSSET Authority, China Communications Construction",
            "source": "Gouvernement Kenyan / AfDB 2025"
        },
        {
            "titre": "SGR Phase 2B (Naivasha-Kisumu-Malaba)",
            "secteur": "Transport Ferroviaire",
            "statut": "Lancement Travaux 2025",
            "budget": "Est. 3.5 Mrd USD",
            "echeance": "2027-2028",
            "description": "Extension de la ligne ferroviaire Standard Gauge Railway (SGR) vers la frontière ougandaise pour compléter le corridor Nord.",
            "impact": "Connexion ferroviaire directe Mombasa-Kampala-Kigali. Réduction drastique des coûts logistiques régionaux.",
            "partenaires": "Kenya Railways, Financement Chinois (Potentiel)",
            "source": "Kenya Railways Corp"
        }
    ],
    "TZA": [
        {
            "titre": "SGR Dar es Salaam-Mwanza-Kigali",
            "secteur": "Transport Ferroviaire",
            "statut": "En construction (Phases 3-6)",
            "budget": "7.6 Mrd USD",
            "echeance": "2026 (Phases principales)",
            "description": "Ligne ferroviaire électrique à écartement standard reliant le port de Dar es Salaam aux Grands Lacs (Rwanda, Burundi, RDC).",
            "impact": "Corridor central modernisé. Accès direct à l'océan pour les pays enclavés.",
            "partenaires": "TRC, Yapi Merkezi, Mota-Engil",
            "source": "Tanzania Railways Corporation"
        },
        {
            "titre": "Projet Gazier LNG Lindi",
            "secteur": "Énergie",
            "statut": "Négociations finales / FID",
            "budget": "30-40 Mrd USD",
            "echeance": "2028-2030",
            "description": "Construction d'un terminal de liquéfaction de gaz naturel à Lindi pour exploiter les immenses réserves offshore.",
            "impact": "Transformation économique de la Tanzanie. Devises majeures via exportations GNL.",
            "partenaires": "Equinor, Shell, ExxonMobil",
            "source": "Tanzania Petroleum Development Corp"
        }
    ],
    "ETH": [
        {
            "titre": "Grand Ethiopian Renaissance Dam (GERD)",
            "secteur": "Énergie",
            "statut": "Opérationnel (Remplissage final)",
            "budget": "4.8 Mrd USD",
            "echeance": "2025 (Pleine capacité)",
            "description": "Plus grand barrage hydroélectrique d'Afrique (6.4 GW) sur le Nil Bleu.",
            "impact": "Indépendance énergétique. Exportation d'électricité vers Kenya, Djibouti, Soudan.",
            "partenaires": "EPP (Ethiopian Electric Power)",
            "source": "Gouvernement Éthiopien"
        }
    ],
    
    # AFRIQUE AUSTRALE
    "ZAF": [
        {
            "titre": "Boegoebaai Green Hydrogen Port",
            "secteur": "Énergie & Portuaire",
            "statut": "Planification avancée",
            "budget": "Est. 10 Mrd USD",
            "echeance": "2028-2030",
            "description": "Nouveau port en eau profonde et zone économique spéciale dédiés à la production et l'exportation d'hydrogène vert.",
            "impact": "Hub mondial de l'hydrogène vert. Réindustrialisation du Northern Cape.",
            "partenaires": "Sasol, Transnet",
            "source": "Infrastructure South Africa"
        },
        {
            "titre": "Extension Corridor Conteneurs Durban-Gauteng",
            "secteur": "Logistique",
            "statut": "En modernisation",
            "budget": "Est. 5 Mrd USD",
            "echeance": "2027",
            "description": "Modernisation de l'axe logistique vital reliant le port de Durban au cœur industriel de Johannesburg (Rail & Route).",
            "impact": "Décongestion du port de Durban. Compétitivité accrue de l'Afrique du Sud.",
            "partenaires": "Transnet",
            "source": "Transnet"
        }
    ],
    "AGO": [
        {
            "titre": "Raffinerie de Lobito",
            "secteur": "Énergie",
            "statut": "En construction",
            "budget": "6 Mrd USD",
            "echeance": "2026",
            "description": "Construction d'une raffinerie d'une capacité de 200,000 barils/jour.",
            "impact": "Auto-suffisance en produits raffinés. Exportation régionale vers la Zambie et la RDC.",
            "partenaires": "Sonangol",
            "source": "Ministère des Ressources Minérales"
        },
        {
            "titre": "Corridor Ferroviaire de Lobito",
            "secteur": "Transport",
            "statut": "Opérationnel / Extension vers Zambie",
            "budget": "555 M USD (Financement US)",
            "echeance": "En cours",
            "description": "Réhabilitation et extension du chemin de fer de Benguela pour relier le port de Lobito aux mines de RDC et Zambie.",
            "impact": "Route d'exportation la plus rapide pour le cuivre/cobalt de la Copperbelt. Soutien stratégique US/UE.",
            "partenaires": "Lobito Atlantic Railway, DFC (USA)",
            "source": "Gouvernement Angolais / USA"
        }
    ],
    "MOZ": [
        {
            "titre": "Projet Mozambique LNG (Cabo Delgado)",
            "secteur": "Énergie",
            "statut": "Reprise progressive (Post-Force Majeure)",
            "budget": "20 Mrd USD",
            "echeance": "2027-2028",
            "description": "Développement des champs gaziers offshore et usine de liquéfaction à Afungi.",
            "impact": "Transformation du Mozambique en acteur gazier mondial majeur.",
            "partenaires": "TotalEnergies",
            "source": "TotalEnergies / INP"
        }
    ],
    
    # AFRIQUE DE L'OUEST & CENTRALE
    "CIV": [
        {
            "titre": "Métro d'Abidjan (Ligne 1)",
            "secteur": "Transport Urbain",
            "statut": "En construction",
            "budget": "1.5 Mrd EUR",
            "echeance": "2025-2026",
            "description": "Train urbain de 37km traversant Abidjan du Nord au Sud, reliant l'aéroport.",
            "impact": "Transport de 500,000 passagers/jour. Révolution de la mobilité à Abidjan.",
            "partenaires": "Bouygues, Keolis, Alstom",
            "source": "Gouvernement Ivoirien"
        },
        {
            "titre": "Extension Port d'Abidjan (Terminal TC2)",
            "secteur": "Logistique Maritime",
            "statut": "Opérationnel / Phase 2",
            "budget": "900 M USD",
            "echeance": "2025 (Optimisation)",
            "description": "Second terminal à conteneurs capable d'accueillir des navires de 14,000 EVP.",
            "impact": "Consolidation d'Abidjan comme hub portuaire leader en Afrique de l'Ouest.",
            "partenaires": "Port Autonome d'Abidjan, Bolloré (MSC)",
            "source": "PAA"
        }
    ],
    "CMR": [
        {
            "titre": "Extension Port en Eau Profonde de Kribi (Phase 2)",
            "secteur": "Logistique Maritime",
            "statut": "En construction",
            "budget": "794 M USD",
            "echeance": "2025-2026",
            "description": "Extension des terminaux et zones logistiques pour augmenter la capacité de traitement.",
            "impact": "Hub de transbordement régional. Débouché pour le fer de Mbalam et le Tchad/RCA.",
            "partenaires": "CHEC (Chine), Port Autonome de Kribi",
            "source": "PAK"
        },
        {
            "titre": "Barrage de Nachtigal",
            "secteur": "Énergie",
            "statut": "Mise en service partielle",
            "budget": "1.2 Mrd EUR",
            "echeance": "2025 (Pleine puissance)",
            "description": "Barrage hydroélectrique de 420 MW sur la Sanaga.",
            "impact": "Augmentation de 30% de la capacité électrique du pays. Exportation vers le Tchad.",
            "partenaires": "EDF, SFI",
            "source": "NHPC"
        }
    ],
    "TUN": [
        {
            "titre": "Interconnexion Électrique ELMED (Tunisie-Italie)",
            "secteur": "Énergie",
            "statut": "Approuvé / Financement bouclé",
            "budget": "850 M EUR",
            "echeance": "2028",
            "description": "Câble sous-marin de 200km reliant le réseau électrique tunisien à l'Europe (Sicile).",
            "impact": "Pont énergétique Afrique-Europe. Exportation d'énergies renouvelables solaires.",
            "partenaires": "STEG, Terna, UE",
            "source": "Ministère de l'Industrie"
        }
    ]
}

# Fusionner les dictionnaires (Mise à jour ou Ajout)
existing_projects.update(NEW_PROJECTS)

# Sauvegarder
with open(json_path, 'w', encoding='utf-8') as f:
    json.dump(existing_projects, f, indent=2, ensure_ascii=False)

print(f"✅ Ajouté/Mis à jour les projets pour {len(NEW_PROJECTS)} nouveaux pays.")
print("Pays couverts maintenant:", list(existing_projects.keys()))


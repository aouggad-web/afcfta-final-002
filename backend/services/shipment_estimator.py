"""
Estimation d'expédition : de la valeur FOB au nombre et au type de conteneurs.

PROBLÈME RÉSOLU : le coût rendu (landed cost) des scénarios Opportunités
n'ajoutait que le fret d'UN SEUL conteneur 20′ (TEU), quelle que soit la
valeur FOB saisie — une opération de 2 M$ était facturée comme un unique
conteneur. Ce module estime le POIDS de la marchandise à partir de sa valeur
FOB (ratio valeur/poids par produit), en déduit le NOMBRE et le TYPE de
conteneurs nécessaires, pour que le coût de fret soit multiplié en
conséquence.

DISCIPLINE « zéro fabrication » : le poids est une ESTIMATION, jamais une
donnée réelle. Le ratio valeur/poids (USD/kg) est un ordre de grandeur typique
par chapitre SH — la valeur unitaire réelle varie fortement selon la qualité,
la marque, le conditionnement. Chaque sortie porte `is_estimate: True`, le
ratio utilisé, sa base, et reste ENTIÈREMENT remplaçable : si l'appelant
fournit un poids réel (`weight_kg_override`), l'estimation est ignorée.

Base du ratio USD/kg : ordres de grandeur des valeurs unitaires du commerce
international (UN Comtrade / BACI, moyennes par grande catégorie de produits) —
matières premières lourdes et bon marché en bas de l'échelle (minerais,
céréales, combustibles ~0,1–1 USD/kg), produits manufacturés au milieu
(textile, machines ~5–40 USD/kg), électronique / pharma / précieux en haut
(50 – >1000 USD/kg). Ce sont des repères de dimensionnement logistique, pas
des prix.
"""

from __future__ import annotations

import math
from typing import Dict, Optional

# Capacités utiles (charge maximale) des conteneurs — identiques à celles du
# comparateur multimodal (multimodal_freight_service : TEU 21 600 kg, FEU
# 26 400 kg). Redéclarées ici pour éviter une dépendance circulaire.
TEU_CAPACITY_KG = 21_600  # conteneur 20 pieds
FEU_CAPACITY_KG = 26_400  # conteneur 40 pieds

# Ratio valeur/poids (USD par kg) par chapitre SH (2 chiffres). Ordres de
# grandeur documentés (valeurs unitaires typiques du commerce mondial) — voir
# docstring. Un chapitre absent retombe sur _DEFAULT_USD_PER_KG.
_USD_PER_KG_BY_CHAPTER: Dict[str, float] = {
    # Animaux vivants & produits animaux (01–05)
    "01": 3.0,
    "02": 4.0,
    "03": 4.5,
    "04": 3.0,
    "05": 2.0,
    # Produits végétaux (06–14) — majorité de vrac agricole bon marché
    "06": 3.0,
    "07": 1.0,
    "08": 1.5,
    "09": 4.0,
    "10": 0.4,
    "11": 0.8,
    "12": 1.2,
    "13": 5.0,
    "14": 1.5,
    # Graisses & huiles (15)
    "15": 1.3,
    # Aliments préparés, boissons, tabac (16–24)
    "16": 5.0,
    "17": 0.8,
    "18": 3.5,
    "19": 2.5,
    "20": 2.0,
    "21": 4.0,
    "22": 2.0,
    "23": 0.5,
    "24": 12.0,
    # Produits minéraux (25–27) — très lourds, très bon marché
    "25": 0.3,
    "26": 0.2,
    "27": 0.6,
    # Chimie & industries connexes (28–38)
    "28": 2.0,
    "29": 6.0,
    "30": 60.0,
    "31": 0.5,
    "32": 4.0,
    "33": 20.0,
    "34": 3.0,
    "35": 3.0,
    "36": 6.0,
    "37": 15.0,
    "38": 3.5,
    # Plastiques & caoutchouc (39–40)
    "39": 3.0,
    "40": 3.5,
    # Cuirs, fourrures (41–43)
    "41": 4.0,
    "42": 25.0,
    "43": 40.0,
    # Bois, liège, vannerie (44–46)
    "44": 0.8,
    "45": 3.0,
    "46": 4.0,
    # Papier & pâte (47–49)
    "47": 0.7,
    "48": 1.5,
    "49": 5.0,
    # Textiles (50–63)
    "50": 30.0,
    "51": 12.0,
    "52": 5.0,
    "53": 3.0,
    "54": 6.0,
    "55": 5.0,
    "56": 5.0,
    "57": 8.0,
    "58": 12.0,
    "59": 8.0,
    "60": 10.0,
    "61": 18.0,
    "62": 18.0,
    "63": 8.0,
    # Chaussures, coiffures, etc. (64–67)
    "64": 15.0,
    "65": 15.0,
    "66": 10.0,
    "67": 12.0,
    # Pierres, plâtre, céramique, verre (68–70)
    "68": 1.5,
    "69": 2.0,
    "70": 3.0,
    # Perles, pierres & métaux précieux (71) — extrêmement cher au kg
    "71": 2000.0,
    # Métaux communs & ouvrages (72–83)
    "72": 0.9,
    "73": 2.5,
    "74": 8.0,
    "75": 15.0,
    "76": 4.0,
    "78": 2.5,
    "79": 3.0,
    "80": 25.0,
    "81": 30.0,
    "82": 12.0,
    "83": 6.0,
    # Machines & matériel électrique (84–85)
    "84": 15.0,
    "85": 40.0,
    # Matériel de transport (86–89)
    "86": 12.0,
    "87": 15.0,
    "88": 400.0,
    "89": 8.0,
    # Instruments de précision, optique, horlogerie (90–92)
    "90": 80.0,
    "91": 150.0,
    "92": 30.0,
    # Armes (93)
    "93": 50.0,
    # Meubles, jouets, ouvrages divers (94–96)
    "94": 6.0,
    "95": 12.0,
    "96": 15.0,
    # Objets d'art & antiquités (97)
    "97": 500.0,
}

# Défaut prudent (produit manufacturé « moyen ») quand le chapitre est inconnu.
_DEFAULT_USD_PER_KG = 8.0

# En-deçà, on considère qu'un seul 20′ suffit ; au-delà on bascule en 40′
# (plus économique pour les gros volumes). Seuil = capacité d'un TEU.
_TEU_MAX_KG = TEU_CAPACITY_KG


def usd_per_kg_for_hs(hs_code: str) -> Dict:
    """Ratio valeur/poids (USD/kg) estimé pour un code SH, avec sa base."""
    chapter = (hs_code or "").strip().replace(".", "").replace(" ", "")[:2]
    rate = _USD_PER_KG_BY_CHAPTER.get(chapter)
    if rate is not None:
        return {
            "usd_per_kg": rate,
            "hs_chapter": chapter,
            "source": "Valeur unitaire typique du commerce mondial par chapitre SH "
            "(ordre de grandeur UN Comtrade / BACI) — estimation de dimensionnement.",
            "is_estimate": True,
        }
    return {
        "usd_per_kg": _DEFAULT_USD_PER_KG,
        "hs_chapter": chapter or None,
        "source": "Chapitre SH inconnu — ratio manufacturé moyen par défaut "
        f"({_DEFAULT_USD_PER_KG} USD/kg). Estimation de dimensionnement.",
        "is_estimate": True,
    }


def plan_containers(weight_kg: float) -> Dict:
    """Choisit le type de conteneur et le nombre nécessaire pour un poids donné."""
    weight_kg = max(float(weight_kg or 0), 0.0)
    if weight_kg <= 0:
        return {
            "container_type": "teu",
            "container_capacity_kg": TEU_CAPACITY_KG,
            "containers_needed": 0,
            "note": "Poids nul ou indéterminé.",
        }
    if weight_kg <= _TEU_MAX_KG:
        container_type, capacity = "teu", TEU_CAPACITY_KG
    else:
        container_type, capacity = "feu", FEU_CAPACITY_KG
    n = max(1, math.ceil(weight_kg / capacity))
    label = "20 pieds" if container_type == "teu" else "40 pieds"
    return {
        "container_type": container_type,
        "container_capacity_kg": capacity,
        "containers_needed": n,
        "note": f"{n} conteneur(s) {label} pour {round(weight_kg):,} kg estimés "
        f"(capacité {capacity:,} kg/conteneur).".replace(",", " "),
    }


def estimate_shipment(
    goods_value_usd: Optional[float],
    hs_code: str,
    weight_kg_override: Optional[float] = None,
) -> Dict:
    """
    Estime le poids et le plan de conteneurs d'une expédition à partir de sa
    valeur FOB et de son code SH.

    Si ``weight_kg_override`` est fourni (poids réel connu), il est utilisé tel
    quel et le ratio valeur/poids est ignoré (``weight_source: "fourni"``).

    Retourne un dict prêt à afficher : poids (estimé ou fourni), ratio utilisé,
    type et nombre de conteneurs, et les drapeaux de traçabilité. Renvoie
    ``available: False`` si ni le poids ni la valeur ne sont exploitables.
    """
    if weight_kg_override and weight_kg_override > 0:
        plan = plan_containers(weight_kg_override)
        return {
            "available": True,
            "weight_kg": round(float(weight_kg_override), 1),
            "weight_source": "fourni",
            "is_estimate": False,
            "value_to_weight": None,
            **plan,
        }

    if not goods_value_usd or goods_value_usd <= 0:
        return {
            "available": False,
            "note": "Ni poids réel ni valeur FOB exploitable — dimensionnement "
            "conteneur impossible.",
        }

    ratio = usd_per_kg_for_hs(hs_code)
    weight_kg = float(goods_value_usd) / ratio["usd_per_kg"]
    plan = plan_containers(weight_kg)
    return {
        "available": True,
        "weight_kg": round(weight_kg, 1),
        "weight_source": "estimé",
        "is_estimate": True,
        "value_to_weight": ratio,
        "goods_value_usd": float(goods_value_usd),
        **plan,
    }

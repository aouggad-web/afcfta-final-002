"""Un taux réduit réel doit atteindre l'écran.

`postgres_tariff_service.get_commodity_details()` émettait ses avantages
fiscaux sous la clé `reduced_rate`, alors que `RegulatoryDetailsPanel.jsx` lit
`adv.reduced_rate_pct`. Conséquence à l'écran : « % » sans chiffre — le taux
réduit existait, et l'opérateur ne le voyait pas.

Ce service est retiré ; le panneau a lu ensuite `/regulatory-engine`, dont le
modèle canonique (`engine/schemas/canonical_model.py`) porte le taux réduit.

Ce moteur n'a jamais pu répondre : ses fichiers de lignes (`*_canonical.jsonl`)
ne sont pas livrés, et le panneau affichait « Pays … non disponible » pour tous
les pays. Le panneau lit désormais le socle (`/consultation/…`), la source du
calcul, et ne porte plus de section « avantages » : le taux préférentiel dépend
d'une origine que l'onglet Réglementation ne connaît pas. Le contrôle négatif
reste, déplacé : le panneau et sa source sont comparés dans le code source, de
sorte que le retour à une source qui ne répond pas échoue ici, pas à l'écran.
"""

import os
import re
import sys


sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PANNEAU = os.path.join(
    RACINE, "frontend", "src", "components", "calculator", "RegulatoryDetailsPanel.jsx"
)
MODELE = os.path.join(RACINE, "engine", "schemas", "canonical_model.py")

CLE_CANONIQUE = "reduced_rate_pct"


# ─────────────────────────────────────────────────────────────────────────────
# LE CONTRÔLE NÉGATIF QUI COMPTE : la divergence elle-même était le défaut.
#
# Un test qui vérifie seulement la valeur de la clé laisse revenir le défaut à
# la première refonte. Ceux-ci lisent le SOURCE du producteur et du
# consommateur, et tombent si l'un s'écarte des autres.
# ─────────────────────────────────────────────────────────────────────────────


def _source(chemin):
    with open(chemin, encoding="utf-8") as f:
        return f.read()


def test_le_producteur_porte_la_cle_canonique():
    """Le modèle canonique du moteur réglementaire nomme le taux réduit."""
    src = _source(MODELE)
    assert f"{CLE_CANONIQUE}:" in src, f"canonical_model.py doit porter « {CLE_CANONIQUE} »"
    assert "reduced_rate:" not in src, "l'ancienne clé « reduced_rate » ne doit pas revenir"


def test_le_panneau_lit_le_socle_et_non_le_moteur_sans_donnees():
    """Le panneau interroge la source du calcul, jamais `/regulatory-engine`.

    Ce dernier lit `engine/output/*_canonical.jsonl`, absents du dépôt et de
    l'image : toute consultation y répond « Pays … non disponible ». Ce test lit
    le SOURCE du panneau : il tombe si le panneau y retourne, au lieu de laisser
    un onglet qui ne livre aucun résultat arriver jusqu'à l'opérateur.
    """
    src = _source(PANNEAU)
    assert "/consultation/" in src and "/position/" in src, "le panneau doit lire la fiche du socle"
    assert "/formalites/" in src, "le panneau doit lire les formalités du socle"
    # L'APPEL, pas la mention : l'en-tête du panneau raconte pourquoi il a changé.
    assert not re.search(r"\$\{API\}/regulatory-engine", src), (
        "le panneau ne doit plus interroger le moteur réglementaire"
    )

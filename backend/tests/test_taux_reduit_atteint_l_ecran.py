"""Un taux réduit réel doit atteindre l'écran.

`postgres_tariff_service.get_commodity_details()` émettait ses avantages
fiscaux sous la clé `reduced_rate`, alors que `RegulatoryDetailsPanel.jsx` lit
`adv.reduced_rate_pct`. Conséquence à l'écran : « % » sans chiffre — le taux
réduit existait, et l'opérateur ne le voyait pas.

Ce service est retiré ; le panneau lit désormais `/regulatory-engine`, dont le
modèle canonique (`engine/schemas/canonical_model.py`) porte le taux réduit.
Le contrôle négatif reste : le producteur et le consommateur sont comparés dans
le code source, de sorte qu'aucun ne peut diverger de l'autre en silence.
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


def test_le_panneau_lit_la_cle_que_le_backend_emet():
    """Et le consommateur doit lire ce même nom.

    Ce test lie les trois fichiers : si quelqu'un renomme la clé côté backend
    sans toucher au panneau — ou l'inverse — il tombe, au lieu de laisser un
    taux réel disparaître de l'écran sans bruit.
    """
    src = _source(PANNEAU)
    lectures = set(re.findall(r"adv\.(reduced_rate\w*)", src))
    assert lectures, "le panneau doit lire un taux réduit"
    assert lectures == {CLE_CANONIQUE}, (
        f"le panneau lit {sorted(lectures)} alors que le backend émet "
        f"« {CLE_CANONIQUE} »"
    )

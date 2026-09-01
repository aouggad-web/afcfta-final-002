"""Utilitaires partagés pour parser les tableaux d'énumération TUN
(douane.gov.tn/tarifwebnew/getresultat.php).

Les libellés retournés par la source peuvent contenir des « < » littéraux
(ex. « <= 1000 cm3 »). On capture donc la cellule de façon non gloutonne
jusqu'à </td> puis on décape les balises et on désencode les entités HTML.
"""

from __future__ import annotations

import html as htmllib
import os
import re

CELL_RE = re.compile(r"submit_frm_resultat\('', '', '(\d+)'\); return false;\">(.*?)</td>", re.S)
_TAG_RE = re.compile(r"<[^>]+>")


def _clean(s: str) -> str:
    return htmllib.unescape(_TAG_RE.sub("", s)).strip()


def parse_enumeration(text: str) -> dict[str, str]:
    """Retourne {code: libellé} depuis un HTML de la page de résultats.

    Chaque ligne du tableau contient deux cellules cliquables : le code
    (répété) puis le libellé. Une réponse dont la parité est cassée est
    considérée invalide et retourne {}.
    """
    cells = CELL_RE.findall(text)
    if not cells or len(cells) % 2 != 0:
        return {}
    out: dict[str, str] = {}
    for i in range(0, len(cells), 2):
        code, raw_code = cells[i]
        if raw_code.strip() != code:
            return {}
        label_cell = cells[i + 1][1] if i + 1 < len(cells) else ""
        if not label_cell:
            return {}
        out.setdefault(code, _clean(label_cell))
    return out


def verify_tls_default() -> bool:
    """TLS ACTIVÉ par défaut. Exporter TUN_INSECURE_TLS=1 pour désactiver
    ponctuellement dans un environnement dont la chaîne TLS de douane.gov.tn
    est problématique — cela expose alors aux MITM."""
    return os.environ.get("TUN_INSECURE_TLS", "").strip() not in ("1", "true", "yes")

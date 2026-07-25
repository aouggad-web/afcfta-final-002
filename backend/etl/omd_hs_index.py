"""
ETL — Index alphabétique OMD (Système Harmonisé, 7e éd. 2022) -> JSON recherchable.

Transforme les deux index alphabétiques de l'OMD (Vol. 1 A-L, Vol. 2 M-Z), fournis
en Markdown, en un index structuré ``produit -> code(s) SH`` exploitable par un
moteur de recherche « nom de marchandise -> SH6 » destiné aux utilisateurs sans
connaissance douanière.

Structure source (lignes de tableau ``|colonne 1|colonne 2|``) :
  * ``|**ABACA**|5305.21-5305.29|``         -> terme + plage SH6
  * ``|**ABAISSE-LANGUE**en bois|4421.90|`` -> terme + qualificatif + SH6
  * ``|**ABATS**||`` puis ``|comestibles|02|`` -> parent + enfants (qualificatifs)
  * ``|**ABRICOTS**voir "**FRUITS**"||``     -> renvoi vers un autre terme
  * ``|...|1515.40-1516-<br>1520|``          -> plusieurs codes (retour ligne <br>)
  * codes : SH2 (``02``), SH4 (``1601``), SH6 (``5305.21``), plages (``A-B``).

Sortie : ``backend/data/omd_hs_index.json`` ::

    {
      "source": "OMD — Index alphabétique du Système Harmonisé (7e éd. 2022)",
      "entries": [
        {"label": "ABACA", "term": "ABACA", "qualifier": null,
         "codes_display": "5305.21 – 5305.29", "hs_codes": ["530521", "530529"],
         "is_range": true, "see_also": null},
        ...
      ]
    }

Aucune fabrication : on n'expanse jamais une plage en codes intermédiaires (qui
pourraient ne pas exister), on ne conserve que les bornes normalisées + la chaîne
brute pour l'affichage. Les renvois « voir X » sont conservés tels quels.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, List, Optional

_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
_VOL1 = _DATA_DIR / "omd_index_vol1.md"
_VOL2 = _DATA_DIR / "omd_index_vol2.md"
_OUT = _DATA_DIR / "omd_hs_index.json"

# Lignes de bruit (en-têtes/pieds de page, marqueurs de lettre, numéros de page).
_NOISE = re.compile(
    r"SYSTEME HARMONISE|INDEX ALPHABETIQUE|SEPTIEME EDITION|<mark>|^\s*$|^\s*\.\s*$"
)
# Séparateur de tableau markdown ``|---|---|``.
_SEP = re.compile(r"^\|[\s:|-]+\|$")

# Un code SH tel qu'écrit dans l'index : 2, 4 chiffres, ou 4.2 (SH6 pointé).
_CODE_TOKEN = re.compile(r"\d{2}(?:\d{2})?(?:\.\d{2})?")


def _clean_markup(text: str) -> str:
    """Retire le gras markdown et normalise les espaces (garde les apostrophes)."""
    text = text.replace("<br>", " ")
    text = text.replace("**", "")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _normalize_code(token: str) -> str:
    """``5305.21`` -> ``530521`` ; ``1601`` -> ``1601`` ; ``02`` -> ``02``."""
    return token.replace(".", "")


def _redot(code: str) -> str:
    """Réaffiche un code normalisé lisiblement : ``530521`` -> ``5305.21``."""
    return f"{code[:4]}.{code[4:]}" if len(code) == 6 else code


def _extract_codes(col2_raw: str) -> Dict:
    """
    Extrait de la 2e colonne : la liste des codes SH normalisés (bornes de plage
    incluses, sans expansion), un affichage propre reconstruit, et si c'est une
    plage (exactement deux codes reliés par un tiret).
    """
    cleaned = _clean_markup(col2_raw)
    tokens = _CODE_TOKEN.findall(cleaned)
    hs_codes: List[str] = []
    for tok in tokens:
        norm = _normalize_code(tok)
        if norm not in hs_codes:  # la source double parfois les codes (mise en page)
            hs_codes.append(norm)

    # Plage stricte : deux codes seulement, séparés par un tiret (ex. 5305.21-5305.29).
    # Une énumération (>2 codes, ex. 1511-1516-1520) n'est PAS une plage.
    is_range = len(hs_codes) == 2 and bool(re.search(r"\d\s*-\s*\d", cleaned))
    if is_range:
        display = f"{_redot(hs_codes[0])} – {_redot(hs_codes[1])}"
    else:
        display = ", ".join(_redot(c) for c in hs_codes)
    return {"codes_display": display, "hs_codes": hs_codes, "is_range": is_range}


def _split_term_qualifier(col1_clean: str) -> Dict:
    """
    Sépare un libellé de 1re colonne en (terme, qualificatif, renvoi).

    - ``ABAISSE-LANGUE en bois`` (terme en gras suivi d'un qualificatif) : le
      découpage bold/normal a déjà été perdu par _clean_markup, on se rabat donc
      sur le repérage du renvoi « voir » ; la distinction terme/qualificatif fine
      est gérée en amont par le suivi parent/enfant.
    - ``ABRICOTS voir "FRUITS"`` -> terme ABRICOTS, renvoi FRUITS.
    """
    see_match = re.search(r'voir\s*"?([^"]+?)"?\s*$', col1_clean, re.IGNORECASE)
    see_also: Optional[str] = None
    if see_match:
        see_also = see_match.group(1).strip(' "')
        col1_clean = col1_clean[: see_match.start()].strip()
    return {"text": col1_clean, "see_also": see_also}


def _is_bold_header(col1_raw: str) -> bool:
    """Vrai si la 1re colonne commence par un terme en gras (nouveau parent)."""
    return col1_raw.lstrip().startswith("**")


def parse_file(path: Path) -> List[Dict]:
    """Parse un volume d'index en liste d'entrées structurées."""
    entries: List[Dict] = []
    current_parent: Optional[str] = None

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or _NOISE.search(line) or _SEP.match(line):
            continue
        if not line.startswith("|"):
            # Ligne hors tableau : numéro de page, lettre de section -> ignore.
            continue

        cols = [c for c in line.split("|")[1:-1]]
        if len(cols) < 2:
            continue
        col1_raw, col2_raw = cols[0], cols[1]
        col1_clean = _clean_markup(col1_raw)
        if not col1_clean:
            continue

        is_header = _is_bold_header(col1_raw)
        tq = _split_term_qualifier(col1_clean)
        codes = _extract_codes(col2_raw)

        # Terme parent en gras -> (re)définit le contexte pour les enfants suivants.
        if is_header:
            # Le terme en gras est le préfixe ; un éventuel qualificatif collé
            # (ex. « ABAISSE-LANGUE en bois ») est conservé dans le libellé complet.
            first_bold = re.match(r"\*\*(.+?)\*\*", col1_raw)
            current_parent = _clean_markup(first_bold.group(1)) if first_bold else tq["text"]
            term = current_parent
            qualifier = tq["text"][len(term) :].strip() or None
        else:
            # Ligne enfant : qualificatif sous le dernier parent en gras.
            term = current_parent or tq["text"]
            qualifier = tq["text"] if current_parent else None

        label = term if not qualifier else f"{term} — {qualifier}"

        # On ne retient une entrée que si elle porte au moins un code OU un renvoi.
        if not codes["hs_codes"] and not tq["see_also"]:
            continue

        entries.append(
            {
                "label": label,
                "term": term,
                "qualifier": qualifier,
                "codes_display": codes["codes_display"] or None,
                "hs_codes": codes["hs_codes"],
                "is_range": codes["is_range"],
                "see_also": tq["see_also"],
            }
        )

    return entries


def build() -> Dict:
    """Construit l'index complet (Vol. 1 + Vol. 2) et l'écrit en JSON."""
    entries: List[Dict] = []
    for vol in (_VOL1, _VOL2):
        if vol.exists():
            entries.extend(parse_file(vol))

    payload = {
        "source": "OMD — Index alphabétique du Système Harmonisé (7e éd. 2022)",
        "entry_count": len(entries),
        "entries": entries,
    }
    _OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    return payload


if __name__ == "__main__":
    result = build()
    print(f"Entrées écrites : {result['entry_count']} -> {_OUT}")

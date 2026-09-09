"""Exact selection for calculation; browsing may still accept shorter HS prefixes."""

import re


class NationalPositionRequired(ValueError):
    def __init__(self, code, hs_code, candidates):
        message = (
            "Sélectionnez une sous-position nationale précise avant de calculer."
            if code == "NATIONAL_POSITION_SELECTION_REQUIRED"
            else "Position nationale introuvable : aucun tarif voisin ne sera appliqué."
        )
        self.detail = {
            "code": code,
            "message": message,
            "hs_code": hs_code,
            "candidate_count": len(candidates),
            "candidates": sorted(candidates)[:200],
        }
        super().__init__(message)


def normalize_calculation_code(hs_code):
    code = str(hs_code).replace(".", "").replace(" ", "")
    if not re.fullmatch(r"[0-9]{6,12}", code):
        raise NationalPositionRequired("NATIONAL_POSITION_NOT_FOUND", code, [])
    return code


def select_calculation_position(hs_code, positions):
    """Return an existing exact line or an unambiguous child, never a sibling.

    None for an HS6 with no national enumeration: the caller retains its
    existing documented HS6 availability/status policy. A claimed national
    code, however, must exist in the enumerated positions.
    """
    code = normalize_calculation_code(hs_code)
    indexed = {}
    for position in positions:
        raw = position.get("code_raw") or position.get("code") or position.get("national_code")
        normalized = str(raw or "").replace(".", "").replace(" ", "")
        if re.fullmatch(r"[0-9]{6,12}", normalized) and normalized.startswith(code[:6]):
            indexed.setdefault(normalized, position)
    national = {key: value for key, value in indexed.items() if len(key) > 6}
    if len(code) > 6:
        if code not in indexed:
            raise NationalPositionRequired("NATIONAL_POSITION_NOT_FOUND", code, national)
        return indexed[code]
    if len(national) > 1:
        raise NationalPositionRequired("NATIONAL_POSITION_SELECTION_REQUIRED", code, national)
    if national:
        return next(iter(national.values()))
    return indexed.get(code)

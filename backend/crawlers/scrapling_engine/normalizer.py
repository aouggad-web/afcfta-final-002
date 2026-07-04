"""
Normalisation vers le contrat v2 (docs/PLAN_SCRAPLING_CRAWLERS.md §4).

Discipline zéro-perte : le texte brut (`raw` / `condition_raw`) est TOUJOURS
conservé ; le parsing structuré (document/autorité, régime) est un enrichissement
best-effort, jamais une condition de rétention de la donnée.

Gère les deux formes rencontrées dans le crawlé DZA existant :
  - formalities : liste de chaînes OU de dicts ;
  - advantages  : liste de chaînes OU de dicts {"tax","rate","condition_fr"}.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Dict, List, Optional, Union

# ── Référentiel des régimes (extensible par pays) — "pas uniquement les ALE" ──
REGIME_KEYWORDS: List[tuple] = [
    # (code, kind, mots-clés — comparés sans accents ni casse)
    ("ZLECAF", "ALE", ("zlecaf", "afcfta", "zone de libre-echange continentale")),
    ("ZALE", "ALE", ("zale", "zone arabe", "gafta", "grande zone arabe")),
    ("UE_ASSOC", "ALE", ("union europeenne", "accord d'association", "ue-", " ue ")),
    ("CONV_JOR", "convention_bilaterale", ("algero-jordanien",)),
    ("CONV_TUN", "convention_bilaterale", ("algero-tunisien",)),
    ("CONV_BILATERALE", "convention_bilaterale", ("convention",)),
    ("HYDROCARB", "regime_economique", ("hydrocarbure", "activites petroliere")),
    (
        "ANDI_INVEST",
        "regime_economique",
        ("andi", "aapi", "investissement", "attestation d'emploi"),
    ),
    ("FRANCHISE", "regime_economique", ("franchise",)),
]

# Autorités connues (motifs → libellé complet) — enrichi au fil des pays.
AUTHORITY_PATTERNS: List[tuple] = [
    (r"m\.\s*agriculture|ministere de l'agriculture", "Ministère de l'Agriculture"),
    (r"m\.\s*sante|ministere de la sante", "Ministère de la Santé"),
    (r"m\.\s*energie|ministere de l'energie", "Ministère de l'Énergie"),
    (r"m\.\s*commerce|ministere du commerce", "Ministère du Commerce"),
    (r"m\.\s*defense|ministere de la defense", "Ministère de la Défense"),
    (r"m\.\s*interieur|ministere de l'interieur", "Ministère de l'Intérieur"),
    (r"banque d'algerie|banque centrale", "Banque centrale"),
    (r"douane", "Administration des douanes"),
]


def _fold(text: str) -> str:
    """Minuscule sans accents, espaces normalisés — pour la comparaison."""
    text = unicodedata.normalize("NFD", text or "")
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    return re.sub(r"\s+", " ", text.lower()).strip()


def detect_regime(condition: str) -> Dict:
    """Rattache une condition d'avantage à un régime du référentiel.
    Régime non reconnu -> AUTRE (le texte brut reste la vérité)."""
    folded = _fold(condition)
    for code, kind, keywords in REGIME_KEYWORDS:
        if any(k in folded for k in keywords):
            return {"code": code, "kind": kind}
    return {"code": "AUTRE", "kind": "non_classe"}


def _extract_requires(condition: str) -> Optional[str]:
    """Pièce exigée si identifiable (certificat d'origine, attestation, visa…)."""
    folded = _fold(condition)
    for pattern, label in [
        (r"certificat d'origine", "Certificat d'origine"),
        (r"attestation d'emploi", "Attestation d'emploi"),
        (r"programme previsionnel", "Programme prévisionnel visé"),
        (r"autorisation", "Autorisation préalable"),
        (r"visa", "Visa"),
    ]:
        if re.search(pattern, folded):
            return label
    return None


def parse_advantage(item: Union[str, Dict]) -> Dict:
    """Chaîne ou dict {"tax","rate","condition_fr"} -> avantage v2."""
    if isinstance(item, dict):
        condition = item.get("condition_fr") or item.get("condition") or item.get("raw") or ""
        tax = item.get("tax")
        rate = item.get("rate")
    else:
        condition, tax, rate = str(item), None, None
    regime = detect_regime(condition)
    out = {
        "regime": regime["code"],
        "regime_kind": regime["kind"],
        "condition_raw": condition,
    }
    if tax is not None:
        out["tax"] = tax
    if rate is not None:
        out["rate"] = rate
    requires = _extract_requires(condition)
    if requires:
        out["requires"] = requires
    return out


def parse_formality(item: Union[str, Dict]) -> Dict:
    """Chaîne ou dict -> formalité v2 {document, issuing_authority?, raw}.
    Motifs : « libellé (autorité) » et « … délivré(e) par le ministère de X »."""
    raw = item if isinstance(item, str) else (item.get("raw") or item.get("name") or str(item))
    document = raw
    authority = None

    # Motif « libellé (autorité) »
    m = re.match(r"^(.*?)\s*\(([^)]+)\)\s*$", raw)
    if m:
        document, authority_hint = m.group(1).strip(), m.group(2)
    else:
        # Motif « délivré(e)/visé(e) par … »
        m2 = re.search(r"(?:delivree?|visee?|par)\s+(?:par\s+)?(le|la|l')\s*(.+)$", _fold(raw))
        authority_hint = m2.group(2) if m2 else ""

    folded_hint = _fold(authority_hint) if authority_hint else _fold(raw)
    for pattern, label in AUTHORITY_PATTERNS:
        if re.search(pattern, folded_hint):
            authority = label
            break

    out = {"document": document.strip().rstrip("."), "raw": raw}
    if authority:
        out["issuing_authority"] = authority
    return out


def normalize_position(position: Dict) -> Dict:
    """Position brute (v1 ou crawl neuf) -> position v2. Champs inconnus conservés."""
    out = dict(position)
    out["formalities"] = [parse_formality(f) for f in (position.get("formalities") or [])]
    out["advantages"] = [parse_advantage(a) for a in (position.get("advantages") or [])]
    return out


def build_regimes_registry(sub_positions: List[Dict]) -> List[Dict]:
    """Référentiel des régimes réellement observés dans les positions."""
    seen: Dict[str, Dict] = {}
    names = {code: (code, kind) for code, kind, _ in REGIME_KEYWORDS}
    for pos in sub_positions:
        for adv in pos.get("advantages") or []:
            code = adv.get("regime", "AUTRE")
            if code not in seen:
                kind = adv.get("regime_kind") or names.get(code, (code, "non_classe"))[1]
                seen[code] = {"code": code, "kind": kind, "occurrences": 0}
            seen[code]["occurrences"] += 1
    return sorted(seen.values(), key=lambda r: -r["occurrences"])


def assemble_output(
    country: str,
    country_name: str,
    source: str,
    sub_positions: List[Dict],
    calculation_rules: Optional[Dict] = None,
    extracted_at: Optional[str] = None,
) -> Dict:
    """Assemble le fichier final au contrat v2 (consommé tel quel par le
    Calculateur via load_crawled_position_index)."""
    normalized = [normalize_position(p) for p in sub_positions]
    chapters = {p.get("chapter") for p in normalized if p.get("chapter")}
    sections = {p.get("section") for p in normalized if p.get("section")}
    return {
        "country": country.upper(),
        "country_name": country_name,
        "source": source,
        "extracted_at": extracted_at,
        "source_quality": "crawled_authentic",
        "stats": {
            "sections": len(sections),
            "chapters": len(chapters),
            "sub_positions": len(normalized),
            "errors": 0,
        },
        "calculation_rules": calculation_rules or {},
        "regimes_registry": build_regimes_registry(normalized),
        "sub_positions": normalized,
    }

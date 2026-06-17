"""
Moteur de calcul des droits et taxes — ventilation NPF vs ZLECAf.

Point clé : la BASE d'imposition (assiette) et la MÉTHODE diffèrent selon le pays.
Les données douanières authentiques portent, pour chaque taxe, sa base déclarée
(ex. CIF, « CIF + DD + RS + PCS », « CIF + DD + TCI », « CIF+Duty+Fees »…). Ce
moteur calcule CHAQUE taxe sur SA base déclarée plutôt que d'appliquer une
cascade uniforme, et produit la ventilation complète sous les deux régimes :

- NPF (régime normal) : taux et bases tels que déclarés.
- ZLECAf : seul le DROIT DE DOUANE est réduit/éliminé (taux préférentiel) ; les
  taxes internes (TVA) et les prélèvements gardent leur taux. Les montants des
  taxes dont la base inclut le droit de douane (ex. TVA = CIF + DD + …) baissent
  mécaniquement sous ZLECAf, ce que le moteur reflète automatiquement.

Module pur (aucune dépendance réseau/Mongo), donc entièrement testable.
"""
from __future__ import annotations

import re
from typing import List, Dict, Any, Optional, Set

# Codes/intitulés identifiant le droit de douane (le seul droit réduit par ZLECAf).
DD_CODES = {"DD", "DI", "ID", "DDDROIT", "GENERAL", "DDDROIT"}
DD_NAME_HINTS = (
    "import duty", "customs duty", "droit de douane", "droit d'importation",
    "cet import duty", "general customs",
)
# Codes/intitulés identifiant la TVA (impôt intérieur, inchangé par ZLECAf).
VAT_CODES = {"TVA", "VAT", "TVA/APTAXE"}
VAT_NAME_HINTS = ("tva", "vat", "valeur ajout", "value added")

# Jetons de base qui désignent la valeur en douane (graine = valeur CIF).
_CIF_TOKENS = ("CIF", "FOB", "VALEUR", "VAL.DOU", "VALEUR DOUANE", "ASSIETTE")


def classify(line: Dict[str, Any]) -> str:
    """Classe une ligne de taxe : 'dd' | 'tva' | 'autre'."""
    code = str(line.get("code", "")).upper().strip()
    name = str(line.get("name", "")).lower()
    if code in DD_CODES or any(h in name for h in DD_NAME_HINTS):
        return "dd"
    if code in VAT_CODES or any(h in name for h in VAT_NAME_HINTS):
        return "tva"
    return "autre"


def _strip_cap(base: str) -> str:
    """Retire les annotations entre parenthèses (ex. « (plafond 15 000 XAF) »)."""
    return re.sub(r"\(.*?\)", "", base or "").strip()


def _base_components(base_expr: Optional[str], category: str,
                     dd_code: str, other_codes: List[str]) -> Set[str]:
    """Résout l'expression de base en un ensemble de codes contribuant à l'assiette.

    Retourne les codes (hors CIF) à additionner à la valeur. Un ensemble vide
    signifie « base = CIF seule ». Si la base est absente/variable, applique la
    méthode NATIONALE par défaut :
      - droit de douane et autres taxes  -> CIF
      - TVA -> CIF + droit de douane + toutes les autres taxes
    """
    expr = _strip_cap(base_expr or "")
    if not expr or expr.lower() == "variable":
        if category == "tva":
            return {dd_code, *other_codes}
        return set()

    comps: Set[str] = set()
    for raw in expr.split("+"):
        tok = raw.strip().upper()
        if not tok:
            continue
        if any(tok.startswith(c) for c in _CIF_TOKENS):
            continue  # graine = valeur, pas un composant additionnel
        if tok in ("DUTY", "DD", "DI", "ID"):
            comps.add(dd_code)
        elif tok in ("FEES", "LEVIES", "AUTRES", "OTHERS"):
            comps.update(other_codes)
        else:
            comps.add(tok)  # code explicite (RS, PCS, TCI, …)
    return comps


def _resolve_amounts(value: float, lines: List[Dict[str, Any]],
                     dd_code: str, dd_rate_pct: float,
                     caps: Optional[Dict[str, float]] = None) -> Dict[str, float]:
    """Calcule le montant de chaque taxe en respectant les dépendances de base.

    `dd_rate_pct` permet d'imposer le taux du droit de douane (NPF ou ZLECAf) ;
    les bases qui référencent le droit de douane sont recalculées en conséquence.
    Résolution itérative : on calcule d'abord les lignes dont tous les composants
    sont connus, puis les lignes composites (ex. TVA), jusqu'à convergence.

    `caps` (optionnel) : plafond de MONTANT par code de taxe, exprimé dans la même
    devise que `value` (ex. RI CEMAC plafonné à 15 000 XAF converti en USD). Le
    montant calculé est alors écrêté : min(ad valorem, plafond).
    """
    caps = caps or {}
    cats = {l["code"]: classify(l) for l in lines}
    other_codes = [l["code"] for l in lines if cats[l["code"]] == "autre"]
    deps = {
        l["code"]: _base_components(l.get("base"), cats[l["code"]], dd_code, other_codes)
        for l in lines
    }
    rate_of = {}
    for l in lines:
        r = l.get("rate_pct")
        r = float(r) if isinstance(r, (int, float)) else 0.0
        rate_of[l["code"]] = dd_rate_pct if l["code"] == dd_code else r

    amounts: Dict[str, float] = {}
    remaining = [l["code"] for l in lines]
    # Itère tant qu'on peut résoudre de nouvelles lignes.
    progress = True
    while remaining and progress:
        progress = False
        for code in list(remaining):
            if deps[code] - set(amounts.keys()):
                continue  # dépendances pas encore toutes calculées
            base_value = value + sum(amounts[c] for c in deps[code] if c in amounts)
            amt = round(base_value * rate_of[code] / 100.0, 2)
            if code in caps:
                amt = round(min(amt, caps[code]), 2)  # écrêtage au plafond
            amounts[code] = amt
            remaining.remove(code)
            progress = True
    # Cycle/dépendance manquante : repli sur CIF pour les lignes restantes.
    for code in remaining:
        amt = round(value * rate_of[code] / 100.0, 2)
        if code in caps:
            amt = round(min(amt, caps[code]), 2)
        amounts[code] = amt
    return amounts


def _base_value_of(value: float, code: str, lines: List[Dict[str, Any]],
                   amounts: Dict[str, float], dd_code: str) -> float:
    cats = {l["code"]: classify(l) for l in lines}
    other_codes = [l["code"] for l in lines if cats[l["code"]] == "autre"]
    line = next(l for l in lines if l["code"] == code)
    comps = _base_components(line.get("base"), cats[code], dd_code, other_codes)
    return round(value + sum(amounts.get(c, 0.0) for c in comps), 2)


def parse_cap(base_expr: Optional[str]) -> Optional[Dict[str, Any]]:
    """Extrait un plafond de l'expression de base (ex. « CIF (plafond 15 000 XAF) »).

    Retourne {"amount": 15000.0, "currency": "XAF"} ou None si pas de plafond.
    """
    if not base_expr:
        return None
    m = re.search(r"plafond\s*([\d\s.,]+?)\s*([A-Z]{3})", base_expr, re.IGNORECASE)
    if not m:
        return None
    raw = m.group(1).replace(" ", "").replace(" ", "").replace(",", ".")
    try:
        amount = float(raw)
    except ValueError:
        return None
    return {"amount": amount, "currency": m.group(2).upper()}


def compute_dual_breakdown(
    value: float,
    lines: List[Dict[str, Any]],
    npf_dd_rate_pct: float,
    zlecaf_dd_rate_pct: float,
    caps: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """Ventilation complète NPF vs ZLECAf, taxe par taxe, base par base.

    `lines` : [{code, name, rate_pct, base?, source?}] — TOUTES les taxes du
    régime (droit de douane inclus). Les doublons de code sont préfixés pour
    rester distincts.

    `caps` (optionnel) : {code: plafond_montant} dans la devise de `value`
    (ex. RI CEMAC plafonné à 15 000 XAF converti en USD). Écrête le montant.
    """
    # Dé-duplication des codes (certaines sources répètent un code).
    seen: Dict[str, int] = {}
    norm_lines: List[Dict[str, Any]] = []
    for l in lines:
        code = str(l.get("code") or l.get("name") or "TAX").upper().strip() or "TAX"
        seen[code] = seen.get(code, 0) + 1
        if seen[code] > 1:
            code = f"{code}#{seen[code]}"
        norm_lines.append({**l, "code": code})

    dd_code = next((l["code"] for l in norm_lines if classify(l) == "dd"), None)

    npf_amounts = _resolve_amounts(value, norm_lines, dd_code, npf_dd_rate_pct, caps)
    zlc_amounts = _resolve_amounts(value, norm_lines, dd_code, zlecaf_dd_rate_pct, caps)

    breakdown: List[Dict[str, Any]] = []
    tot = {"npf": {"dd": 0.0, "tva": 0.0, "autre": 0.0},
           "zlecaf": {"dd": 0.0, "tva": 0.0, "autre": 0.0}}

    for l in norm_lines:
        code = l["code"]
        cat = classify(l)
        is_dd = (code == dd_code)
        rate = float(l.get("rate_pct") or 0.0)
        entry = {
            "code": code.split("#")[0],
            "name": l.get("name", code),
            "category": {"dd": "droit_douane", "tva": "tva", "autre": "autre_taxe"}[cat],
            "base_expr": l.get("base") or ("CIF + droit + taxes (méthode nationale)" if cat == "tva" else "CIF"),
            "rate_npf_pct": round(npf_dd_rate_pct if is_dd else rate, 4),
            "rate_zlecaf_pct": round(zlecaf_dd_rate_pct if is_dd else rate, 4),
            "base_value_npf": _base_value_of(value, code, norm_lines, npf_amounts, dd_code),
            "base_value_zlecaf": _base_value_of(value, code, norm_lines, zlc_amounts, dd_code),
            "amount_npf": npf_amounts[code],
            "amount_zlecaf": zlc_amounts[code],
            "affected_by_zlecaf": is_dd,
            "source": l.get("source", ""),
        }
        _cap = parse_cap(l.get("base"))
        if _cap:
            entry["cap"] = _cap  # plafond déclaré (montant + devise)
            entry["capped_npf"] = (code in (caps or {})) and npf_amounts[code] >= (caps or {}).get(code, float("inf")) - 0.01
        breakdown.append(entry)
        tot["npf"][cat] += npf_amounts[code]
        tot["zlecaf"][cat] += zlc_amounts[code]

    def _summary(regime: str) -> Dict[str, float]:
        t = tot[regime]
        total_taxes = round(t["dd"] + t["tva"] + t["autre"], 2)
        return {
            "droit_douane": round(t["dd"], 2),
            "autres_taxes": round(t["autre"], 2),
            "tva": round(t["tva"], 2),
            "total_taxes_et_droits": total_taxes,
            "cout_total": round(value + total_taxes, 2),
        }

    npf_sum = _summary("npf")
    zlc_sum = _summary("zlecaf")
    return {
        "value": round(value, 2),
        "breakdown": breakdown,
        "summary": {
            "npf": npf_sum,
            "zlecaf": zlc_sum,
            "economie_droits": round(npf_sum["droit_douane"] - zlc_sum["droit_douane"], 2),
            "economie_totale": round(npf_sum["cout_total"] - zlc_sum["cout_total"], 2),
        },
    }


def localize_breakdown(dual: Dict[str, Any], usd_to_local_rate: float) -> Dict[str, Any]:
    """Ajoute les montants en monnaie locale (1 USD = `usd_to_local_rate` locale).

    Pur et sans état : retourne un nouveau détail enrichi de `amount_npf_local`
    et `amount_zlecaf_local` par taxe, plus un récapitulatif en monnaie locale.
    Les MONTANTS deviennent bi-devises ; les TAUX (en %) restent inchangés.
    """
    r = float(usd_to_local_rate)

    breakdown_local = []
    for b in dual["breakdown"]:
        breakdown_local.append({
            **b,
            "amount_npf_local": round(b["amount_npf"] * r, 2),
            "amount_zlecaf_local": round(b["amount_zlecaf"] * r, 2),
        })

    def _loc(summary: Dict[str, float]) -> Dict[str, float]:
        return {k: round(v * r, 2) for k, v in summary.items()}

    summary = dual["summary"]
    summary_local = {
        "npf": _loc(summary["npf"]),
        "zlecaf": _loc(summary["zlecaf"]),
        "economie_droits": round(summary["economie_droits"] * r, 2),
        "economie_totale": round(summary["economie_totale"] * r, 2),
    }
    return {"breakdown": breakdown_local, "summary_local": summary_local}


# Mappage code de taxe -> clé de référence légale (pour les journaux).
JOURNAL_LEGAL_KEY = {
    "DD": "dd", "DI": "dd", "ID": "dd", "GENERAL": "dd", "DDDROIT": "dd",
    "RS": "rs", "PCS": "pcs", "PCC": "cedeao", "PC": "cedeao", "PUA": "cedeao",
    "TCI": "tci", "RI": "tci",
    "TVA": "vat", "VAT": "vat",
    "DAPS": "daps", "PRCT": "prct", "TCS": "tcs",
}

_CATEGORY_ORDER = {"droit_douane": 0, "autre_taxe": 1, "tva": 2}


def build_journal(value: float, breakdown: List[Dict[str, Any]], regime: str,
                  legal_refs: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Construit le journal de calcul (étapes) pour un régime à partir du détail.

    Cohérent avec compute_dual_breakdown : chaque étape porte la base RÉELLE de
    la taxe (assiette déclarée) et un cumul = valeur + somme des montants. Le
    cumul final égale le coût total du régime.
    """
    amt_k = f"amount_{regime}"
    base_k = f"base_value_{regime}"
    rate_k = f"rate_{regime}_pct"

    ordered = sorted(breakdown, key=lambda b: _CATEGORY_ORDER.get(b["category"], 1))
    journal = [{
        "step": 1, "component": "Valeur CIF", "base": round(value, 2), "rate": "-",
        "amount": round(value, 2), "cumulative": round(value, 2),
        "legal_ref": legal_refs.get("cif", {}).get("ref", "Incoterms 2020 - CIF"),
        "legal_ref_url": legal_refs.get("cif", {}).get("url"),
    }]
    running = value
    step = 2
    for b in ordered:
        running += b[amt_k]
        if b["category"] == "droit_douane" and regime == "zlecaf":
            ref = legal_refs.get("zlecaf", {"ref": "Accord ZLECAf", "url": None})
        else:
            key = JOURNAL_LEGAL_KEY.get(str(b["code"]).upper())
            ref = legal_refs.get(key, {"ref": b.get("source", ""), "url": None})
        journal.append({
            "step": step,
            "component": b["name"],
            "base": b[base_k],
            "rate": f"{b[rate_k]:.1f}%",
            "amount": round(b[amt_k], 2),
            "cumulative": round(running, 2),
            "legal_ref": ref.get("ref", ""),
            "legal_ref_url": ref.get("url"),
        })
        step += 1
    return journal

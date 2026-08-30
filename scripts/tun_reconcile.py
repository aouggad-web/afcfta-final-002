#!/usr/bin/env python3
"""Réconciliation TUN : crawl Tarif Web 2026 (30/08) ↔ crawl tarifweb2025 (juin).
Détecte : changements de taux, nouveaux codes avec taux (ex-113 sans taux),
codes disparus (restructurés), divergences. Zéro arbitrage — tout est documenté.
Sortie : tmp/TUN_reconciliation_2026-08-30.json
"""
import json
import re
import subprocess
import sys
from pathlib import Path

NEW = Path("backend/data/crawled/TUN_rates_2026-08-30.json")
OLD_BRANCH = "1b690934:backend/data/crawled/TUN_tariffs.json"
OLD_TMP = Path("tmp/TUN_tariffs_juin.json")
OUT = Path("reports/TUN_RECONCILIATION_2026-08-30.json")

TAX_MAP = [
    ("DD", re.compile(r"^DD")),
    ("TVA", re.compile(r"^TVA")),
    ("DC", re.compile(r"^D\.?C\b|^DROIT.{0,4}CONSOM", re.I)),
    ("FODEC", re.compile(r"FODEC", re.I)),
    ("RPD", re.compile(r"^RPD")),
    ("DSV", re.compile(r"^D\.?S\.?V")),
]


def tax_code(code, label=""):
    s = f"{code} {label}"
    for name, rx in TAX_MAP:
        if rx.search(code) or rx.search(label):
            return name
    return None


def load_old():
    if not OLD_TMP.exists():
        blob = subprocess.run(
            ["git", "show", OLD_BRANCH], capture_output=True, check=True, cwd="."
        ).stdout
        OLD_TMP.write_bytes(blob)
    return json.loads(OLD_TMP.read_text(encoding="utf-8"))


def old_taxes(sub):
    """{taxe: (raw, num)} depuis le format juin (codes pollués type 'DDDROIT')."""
    out = {}
    for t in sub.get("taxes_import") or []:
        code = t.get("code", "") or ""
        name = t.get("name", "") or ""
        cat = tax_code(code, name)
        if cat and cat not in out:
            out[cat] = (t.get("raw_value", ""), t.get("rate_pct"))
    return out


def new_taxes(rec):
    out = {}
    for t in rec.get("import_taxes") or []:
        cat = tax_code(t.get("code", ""), t.get("label", ""))
        if cat and cat not in out:
            out[cat] = (t.get("value_raw", ""), t.get("value_num"))
    return out


def norm_val(raw):
    """Normalise '5.700 dinars' → (5.7, 'dinars'), '36 %' → (36.0, '%')."""
    if raw is None:
        return None
    m = re.match(r"^\s*(-?[\d\s.,]+)\s*(%|dinars?|dt|D)\s*$", str(raw), re.I)
    if not m:
        return ("raw", str(raw).strip())
    n = m.group(1).replace(" ", "").replace("\xa0", "").rstrip(".")
    try:
        return (float(n), m.group(2).lower())
    except ValueError:
        return ("raw", str(raw).strip())


def values_equal(a, b):
    na, nb = norm_val(a), norm_val(b)
    if na is None and nb is None:
        return True
    if na is None or nb is None:
        return False
    if isinstance(na, tuple) and isinstance(nb, tuple):
        return abs(na[0] - nb[0]) < 1e-9 and na[1] == nb[1]
    return na == nb


def main():
    old = load_old()
    old_subs = {s["hs_code"]: s for s in old["sub_positions"]}
    new_doc = json.loads(NEW.read_text(encoding="utf-8"))
    new_rates = new_doc["rates"]

    changes, only_old, only_new = [], [], []
    same = 0
    new_with_rates = 0

    all_codes = sorted(set(old_subs) | set(new_rates))
    for code in all_codes:
        o, n = old_subs.get(code), new_rates.get(code)
        o_in, n_in = o is not None, n is not None
        if o_in and not n_in:
            only_old.append({"code": code, "raison": "absent du crawl 2026"})
            continue
        if n_in and not o_in:
            r = {"code": code, "statut": "nouveau"}
            if n.get("no_result"):
                r["statut"] = "nouveau_sans_taux"
            else:
                nt = new_taxes(n)
                r["statut"] = "nouveau_avec_taux" if nt else "nouveau_sans_taux"
                if nt:
                    new_with_rates += 1
                    r["taux"] = {k: v[0] for k, v in nt.items()}
            only_new.append(r)
            continue
        if n.get("no_result"):
            only_old.append({"code": code, "raison": "portail 2026: aucune donnée"})
            continue
        ot, nt2 = old_taxes(o), new_taxes(n)
        if not ot and not nt2:
            same += 1
            continue
        diff = {}
        for cat in sorted(set(ot) | set(nt2)):
            ov, nv = ot.get(cat), nt2.get(cat)
            if ov is None:
                diff[cat] = {"old": None, "new": nv[0]}
            elif nv is None:
                diff[cat] = {"old": ov[0], "new": None}
            elif not values_equal(ov[0], nv[0]):
                diff[cat] = {"old": ov[0], "new": nv[0]}
        if diff:
            changes.append({"code": code, "designation": o.get("designation", ""), "changes": diff})
        else:
            same += 1

    doc = {
        "country": "TUN",
        "generated_at": "2026-08-30",
        "sources": {
            "old": "tarifweb2025 (crawl juin 2026) — backend/data/crawled/TUN_tariffs.json @1b690934",
            "new": "douane.gov.tn/tarifwebnew (Tarif Web 2026) — tmp/TUN_rates_2026-08-30.json",
        },
        "stats": {
            "codes_old": len(old_subs),
            "codes_new": len(new_rates),
            "identiques": same,
            "changements_taux": len(changes),
            "uniquement_old": len(only_old),
            "uniquement_new": len(only_new),
            "nouveaux_avec_taux": new_with_rates,
        },
        "changements_taux": changes,
        "uniquement_old": only_old[:500],
        "uniquement_new": only_new[:500],
    }
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
    s = doc["stats"]
    print(f"identiques: {s['identiques']} | changements: {s['changements_taux']} | "
          f"nouveaux avec taux: {s['nouveaux_avec_taux']} | sans données 2026: {s['uniquement_old']} | "
          f"nouveaux (2026 only): {s['uniquement_new']}")
    print(f"→ {OUT}")
    for c in changes[:15]:
        print(f"  {c['code']}: {c['changes']}")


if __name__ == "__main__":
    main()

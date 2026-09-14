#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_egy_tariffs_official.py

Fusionne les EGY_official_progress_*.json (crawl officiel customs.gov.eg
/Services/TrfDetails) en un fichier canonique + rapport de réconciliation
avec l'ancien fichier EGY_tariffs.json.

Règles (aucune extrapolation) :
  - taxes : verbatim arabe + taux numériques lus littéralement dans la chaîne
    publiée (ex. "ضريبة الوارد : 5%" -> 5.0 ; "صفر" -> 0.0). Rien d'autre.
  - instructions : verbatim, avec codes officiels (ر = préférences FTA /
    exonérations, غ = formalités administratives, ق = restrictions).
  - name_fr : uniquement si l'ancien crawl (juin 2026, même source officielle)
    contient le code — champ séparé "name_fr_from_previous_crawl".
"""
from __future__ import annotations

import glob
import hashlib
import json
import os
import re
import shutil
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND_DIR.parent
CRAWLED_DIR = BACKEND_DIR / "data" / "crawled"
REPORTS_DIR = REPO_ROOT / "reports"

RATE_RE = re.compile(r"(\d+(?:[.,]\d+)?)\s*%")

# Code officiel inscrit en préfixe de chaque instruction : « ر6790-... »,
# « غ4046-... », « ق3034-... ».
#
# Il faut le lire là, et non dans le tableau InstructionCodes que renvoie
# l'API. Les deux tableaux de la réponse officielle n'ont ni la même longueur
# ni le même ordre — sur la position 0101210000, l'API rend onze instructions
# pour douze codes, et le tableau des codes contient même un doublon. Les
# apparier par position attribuait donc à chaque texte le code d'une autre
# instruction : 72,6 % des entrées du fichier produit portaient un code faux.
# Le garde-fou d'égalité des longueurs ne protégeait de rien, puisque des
# tailles identiques n'impliquent pas un ordre identique — il se contentait de
# vider les deux listes quand les tailles différaient, perdant au passage des
# préférences réelles.
INSTRUCTION_CODE_RE = re.compile(r"^\s*([رغق]\d+)")


def _instruction_code(text: str) -> str | None:
    """Code officiel d'une instruction, lu dans son propre texte."""
    match = INSTRUCTION_CODE_RE.match(str(text or ""))
    return match.group(1) if match else None


TAX_CODE_MAPPING = {
    "ضريبة الوارد": "ID",
    "ضريبة قيمه مضافه": "VAT",
    "ضريبة الدمغة": "STAMP",
    "رسم دعم": "SUPPORT",
}

# Le schéma a porté deux générations de clés pour les mêmes taxes : « DD » et
# « TVA » d'abord, « ID » et « VAT » depuis. Comparer un document courant à une
# base sans traduire ces clés ne mesure rien — c'est exactement le défaut qui
# faisait annoncer 8 793 différences de taux là où il n'y en avait aucune : la
# base était interrogée sur des clés qu'elle ne portait plus, tout taux non nul
# ressortait donc comme « modifié ». La comparaison se fait sur le code
# canonique, quelle que soit la génération du document comparé.
LEGACY_TAX_CODE_ALIASES = {"DD": "ID", "TVA": "VAT"}


def rates_by_canonical_code(line: dict) -> dict[str, float | None]:
    """Taux par code canonique de taxe, quelle que soit la génération du schéma."""
    out: dict[str, float | None] = {}
    for key, value in (line.get("taxes") or {}).items():
        code = LEGACY_TAX_CODE_ALIASES.get(key, key)
        out[code] = value.get("rate") if isinstance(value, dict) else value
    return out


def norm_code(code: str) -> str:
    return code.replace("/", "").strip()


def parse_taxes_lines(taxes_verbatim: list[str]) -> list[dict]:
    """Parse ordonné des lignes de taxes publiées par la source.

    Structure de la source : une ligne sans ':' est un en-tête de régime
    (accord commercial, ex. « اتفاقيه الشراكه المصريه الاوربيه ») ; les lignes
    « LABEL : valeur » qui suivent s'appliquent sous CE régime. Les lignes qui
    précèdent tout en-tête sont les taux génériques. Rien n'est interprété :
    le texte arabe reste verbatim."""
    out: list[dict] = []
    regime = None
    for raw in taxes_verbatim or []:
        raw = raw.strip()
        if not raw:
            continue
        if ":" not in raw:
            regime = raw
            out.append(
                {
                    "label_ar": raw,
                    "code": None,
                    "raw": "",
                    "rate": None,
                    "rate_parsed": False,
                    "regime_ar": regime,
                    "kind": "regime_header",
                }
            )
            continue
        label = raw.split(":")[0].strip()
        value = raw.split(":", 1)[1].strip()
        code = None
        for ar, cd in TAX_CODE_MAPPING.items():
            if ar in label:
                code = cd
                break
        num = None
        m = RATE_RE.search(value)
        if m:
            num = float(m.group(1).replace(",", "."))
        elif "صفر" in value:
            num = 0.0
        out.append(
            {
                "label_ar": label,
                "code": code,
                "raw": value,
                "rate": num,
                "rate_parsed": num is not None,
                "regime_ar": regime,
                "kind": "tax",
            }
        )
    return out


def build_taxes_dict(taxes_parsed: list[dict]) -> dict:
    """Dict des taux GÉNÉRIQUES uniquement (aucun régime). En cas de libellé
    dupliqué générique (ex. TVA ad valorem + TVA minimum), la 2e/3e occurrence
    est conservée sous un suffixe _2/_3 — aucune donnée n'est écrasée."""
    out: dict = {}
    seen: dict[str, int] = {}
    for e in taxes_parsed:
        if e.get("kind") != "tax" or e.get("regime_ar"):
            continue
        key = e.get("code") or e["label_ar"]
        seen[key] = seen.get(key, 0) + 1
        if seen[key] > 1:
            key = f"{key}_{seen[key]}"
        out[key] = {
            "code": e.get("code"),
            "label_ar": e["label_ar"],
            "raw": e["raw"],
            "rate": e["rate"],
            "rate_parsed": e["rate_parsed"],
        }
    return out


def build_regime_rates(taxes_parsed: list[dict]) -> list[dict]:
    """Taux publiés SOUS un régime (accord) — conservés séparément du taux
    générique (l'ancien parseur les écrasait dans le dict)."""
    return [
        {
            "regime_ar": e["regime_ar"],
            "code": e.get("code"),
            "label_ar": e["label_ar"],
            "raw": e["raw"],
            "rate": e["rate"],
            "rate_parsed": e["rate_parsed"],
        }
        for e in taxes_parsed
        if e.get("kind") == "tax" and e.get("regime_ar")
    ]


def _index(doc: dict) -> dict[str, dict]:
    return {(p.get("hs_code") or "").replace("/", ""): p for p in doc.get("sub_positions") or []}


#: Champ portant le texte verbatim dans chaque entrée de bloc famille.
#: C'est le seul que le constructeur écrit, et une réconciliation qui en
#: chercherait un autre serait aveugle aux trois blocs : elle pourrait alors
#: annoncer zéro texte perdu sans avoir rien mesuré.
FAMILY_TEXT_FIELD = "text_verbatim"


def _family_texts(line: dict, key: str) -> set[str]:
    """Textes portés par UN bloc famille d'une position."""
    return {
        str(entry[FAMILY_TEXT_FIELD])
        for entry in line.get(key) or []
        if isinstance(entry, dict) and entry.get(FAMILY_TEXT_FIELD)
    }


def _raw_texts(line: dict) -> set[str]:
    """Instructions brutes, avant répartition en familles."""
    return {str(t) for t in (line.get("official_instructions") or [])}


#: Champs de provenance et de référence qu'une reconstruction ne doit pas toucher.
REFERENCE_FIELDS = (
    "source",
    "source_url",
    "detail_endpoint",
    "source_quality",
    "code_official",
    "name_fr_from_previous_crawl",
    "date_consulted",
)

#: Blocs dont la reconstruction change volontairement le contenu.
FAMILY_FIELDS = ("formalities", "restrictions", "fta_preferences", "official_instructions")


def reconcile(base: dict, built: dict) -> dict:
    """Bilan avant/après entre la base de comparaison et le document construit.

    La base est le document que la reconstruction remplace. Toute mesure ici
    porte sur les codes canoniques de taxe : interroger une base sur des clés
    qu'elle ne porte plus ne mesure pas une différence de taux, seulement une
    différence de vocabulaire.
    """
    before, after = _index(base), _index(built)
    common = sorted(set(before) & set(after))

    rates_changed = []
    for code in common:
        b, a = rates_by_canonical_code(before[code]), rates_by_canonical_code(after[code])
        for tax in sorted(set(b) | set(a)):
            if b.get(tax) != a.get(tax):
                rates_changed.append(
                    {"code": code, "tax": tax, "before": b.get(tax), "after": a.get(tax)}
                )
                break

    def _null_rates(index: dict) -> int:
        return sum(
            1
            for line in index.values()
            if not any(r is not None for r in rates_by_canonical_code(line).values())
        )

    def _family_totals(index: dict) -> dict[str, int]:
        return {f: sum(len(line.get(f) or []) for line in index.values()) for f in FAMILY_FIELDS}

    lost_raw = sorted(
        {t for code in common for t in _raw_texts(before[code]) - _raw_texts(after[code])}
    )
    # Chaque bloc famille est comparé à lui-même, pas à la réunion des trois :
    # un texte déplacé d'une famille à une autre est un changement voulu de ce
    # correctif, une disparition en est un défaut, et seule la mesure par bloc
    # les distingue.
    familles_textes = {}
    for famille in ("formalities", "restrictions", "fta_preferences"):
        avant = {t for c in common for t in _family_texts(before[c], famille)}
        apres = {t for c in common for t in _family_texts(after[c], famille)}
        sortis = sorted(avant - apres)
        familles_textes[famille] = {
            "distinct_before": len(avant),
            "distinct_after": len(apres),
            "sortis_de_ce_bloc": len(sortis),
            "retrouves_dans_une_autre_famille": sum(
                1
                for t in sortis
                if any(
                    t in {x for c in common for x in _family_texts(after[c], autre)}
                    for autre in ("formalities", "restrictions", "fta_preferences")
                    if autre != famille
                )
            ),
            "sortis_sample": sortis[:10],
        }
    references_changed = [
        code
        for code in common
        if any(before[code].get(f) != after[code].get(f) for f in REFERENCE_FIELDS)
    ]

    return {
        "positions": {
            "before": len(before),
            "after": len(after),
            "added": sorted(set(after) - set(before)),
            "removed": sorted(set(before) - set(after)),
        },
        "rates": {
            "positions_changed": len(rates_changed),
            "sample": rates_changed[:60],
            "positions_without_any_rate_before": _null_rates(before),
            "positions_without_any_rate_after": _null_rates(after),
        },
        "families": {
            "before": _family_totals(before),
            "after": _family_totals(after),
        },
        "instruction_texts": {
            # Les familles sont mesurées séparément des instructions brutes, et
            # séparément entre elles. Les réunir en un seul ensemble rendait le
            # contrôle inopérant : official_instructions contient déjà chaque
            # texte brut des deux côtés, si bien que l'ensemble réuni restait
            # identique même en vidant un bloc famille entier. Vérifié : la
            # suppression de tout un bloc passait inaperçue.
            "raw_instructions": {
                "distinct_before": len({t for c in common for t in _raw_texts(before[c])}),
                "distinct_after": len({t for c in common for t in _raw_texts(after[c])}),
                "lost": len(lost_raw),
                "lost_sample": lost_raw[:20],
            },
            "par_famille": familles_textes,
        },
        "references": {
            "fields_checked": list(REFERENCE_FIELDS),
            "positions_changed": len(references_changed),
            "sample": references_changed[:20],
        },
        "provenance": {
            f: {"before": base.get(f), "after": built.get(f)}
            for f in ("extracted_at", "rebuilt_at")
        },
        # Comparer les valeurs, non leur seule présence : deux méthodes de
        # calcul différentes sont toutes deux « non vides », et ce champ
        # certifie une conservation, pas une existence.
        "calculation_method_preserved": base.get("calculation_method")
        == built.get("calculation_method"),
    }


def comparison_base(path: Path, doc: dict, origin: str, ref: str | None = None) -> dict:
    """Identité vérifiable de la base de comparaison, inscrite dans le rapport.

    ``ref`` doit désigner la base d'une façon qu'un relecteur puisse rejouer —
    une révision git plutôt qu'un chemin temporaire, qui ne prouverait rien
    puisque personne d'autre ne peut l'ouvrir.
    """
    return {
        "origin": origin,
        "ref": ref or str(path),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "extracted_at": doc.get("extracted_at"),
        "rebuilt_at": doc.get("rebuilt_at"),
        "positions": len(doc.get("sub_positions") or []),
        "note": (
            "Le bilan avant/après compare le document construit à CETTE base, "
            "et non au crawl de juin 2026 ni aux fichiers de progression."
        ),
    }


def write_report(
    *,
    base_path: Path,
    base_doc: dict,
    base_origin: str,
    base_ref: str | None,
    built: dict,
    stats: dict,
    chapters_covered: list,
    backup: str | None,
    now: str,
) -> dict:
    """Écrit le rapport de réconciliation, base de comparaison explicitée.

    Le rapport a longtemps publié un compteur `rate_diff_vs_previous` sans dire
    à quoi il comparait. Il annonçait 8 793 différences de taux — un artefact
    entier : la base était interrogée sur les clés `DD`/`TVA` d'une génération
    antérieure du schéma, si bien que toute position portant un taux ressortait
    comme modifiée. Un rapport qui ne nomme pas sa base ne peut pas être
    contredit, donc ne prouve rien ; celui-ci la nomme et l'empreinte.
    """
    report = {
        "date": now,
        "comparison_base": comparison_base(base_path, base_doc, base_origin, base_ref),
        "before_after": reconcile(base_doc, built),
        "stats": stats,
        "chapters_covered": chapters_covered,
    }
    if backup:
        report["backup"] = backup
    REPORTS_DIR.mkdir(exist_ok=True)
    (REPORTS_DIR / "EGY_REBUILD_RECONCILIATION.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return report


def main() -> int:
    now = datetime.now(timezone.utc).isoformat()

    # Le rapport doit pouvoir être refait sans reconstruire le fichier tarifaire.
    # Le réécrire pour corriger un rapport le ferait diverger de ce qui a été
    # scellé, et son sceau d'intégrité certifierait alors un dérivé.
    if "--reconcile-only" in sys.argv:
        base_path = Path(sys.argv[sys.argv.index("--base") + 1])
        base_ref = sys.argv[sys.argv.index("--base-ref") + 1] if "--base-ref" in sys.argv else None
        built_path = CRAWLED_DIR / "EGY_tariffs.json"
        built = json.loads(built_path.read_text(encoding="utf-8"))
        report = write_report(
            base_path=base_path,
            base_doc=json.loads(base_path.read_text(encoding="utf-8")),
            base_origin=(
                "version du fichier antérieure à la reconstruction, relue depuis "
                "l'historique git"
            ),
            base_ref=base_ref,
            built=built,
            stats=dict(built.get("stats") or {}),
            chapters_covered=sorted(built.get("chapters_covered") or []),
            backup=None,
            now=now,
        )
        print(json.dumps(report["before_after"], ensure_ascii=False, indent=1))
        return 0

    files = sorted(glob.glob(str(CRAWLED_DIR / "EGY_official_progress_*.json")))
    if not files:
        print("aucun fichier de progression EGY officiel")
        return 2
    positions = {}
    chapters_covered = set()
    for f in files:
        d = json.loads(Path(f).read_text(encoding="utf-8"))
        chapters_covered.add(d.get("chapter"))
        for row in d.get("data", []):
            code = norm_code(row.get("code", ""))
            if code:
                positions[code] = row
    print(f"{len(files)} chapitres, {len(positions)} positions officielles")

    old_path = CRAWLED_DIR / "EGY_tariffs.json"
    old = json.loads(old_path.read_text(encoding="utf-8"))

    # Date de collecte, à ne jamais confondre avec la date de construction.
    # Une reconstruction ne reconsulte pas la source : dater le document du
    # jour de la reconstruction en ferait une provenance fausse, exactement
    # le défaut que ce dépôt combat ailleurs. On reprend donc la date portée
    # par les fichiers de progression, et à défaut celle du document existant.
    collecte = next(
        (row["extracted_at"] for row in positions.values() if row.get("extracted_at")),
        old.get("extracted_at") or now,
    )
    old_by_code = {
        (p.get("hs_code") or "").replace("/", ""): p for p in old.get("sub_positions", [])
    }

    sub_positions = []
    stats = Counter()
    for code in sorted(positions):
        row = positions[code]
        taxes_verbatim = row.get("taxes_verbatim") or []
        # re-parse depuis le verbatim (source ordonnée faisant foi) ; le dict
        # `taxes` du crawl est un repli si le verbatim est absent
        if taxes_verbatim:
            taxes_parsed = parse_taxes_lines(taxes_verbatim)
            taxes = build_taxes_dict(taxes_parsed)
            regime_rates = build_regime_rates(taxes_parsed)
        else:
            taxes = row.get("taxes") or {}
            regime_rates = []
        if regime_rates:
            stats["with_regime_rates"] += 1
        old_line = old_by_code.get(code)

        dd = taxes.get("ID") or {}
        vat = taxes.get("VAT") or {}

        instructions = row.get("instructions") or []
        codes_instr = row.get("instruction_codes") or []
        # Chaque instruction porte son propre code : on le lit dans le texte
        # plutôt que de l'apparier par position avec InstructionCodes.
        instructions_codees = [(_instruction_code(t), t) for t in instructions]
        formalities = [
            {
                "code_verbatim": c,
                "text_verbatim": t,
                "kind": "administrative_instruction(غ)",
                "source": row.get("source"),
            }
            for c, t in instructions_codees
            if c and c.startswith("غ")
        ]
        fta_preferences = [
            {
                "code_verbatim": c,
                "text_verbatim": t,
                "kind": "customs_instruction(ر)",
                "zlecaf": ("افريقية القارية" in t),
            }
            for c, t in instructions_codees
            if c and c.startswith("ر")
        ]
        restrictions = [
            {
                "code_verbatim": c,
                "text_verbatim": t,
                "kind": "restriction(ق)",
                "source": row.get("source"),
            }
            for c, t in instructions_codees
            if c and c.startswith("ق")
        ]

        line = {
            "hs_code": code,
            "code_official": row.get("number") or row.get("code"),
            "chapter": code[:2],
            "heading": code[:4],
            "desc_ar": row.get("short_desc_ar") or row.get("desc_ar"),
            "name_fr_from_previous_crawl": (old_line or {}).get("name"),
            "name_ar_from_previous_crawl": (old_line or {}).get("name_ar"),
            "taxes": taxes,
            "taxes_regimes": regime_rates,
            "taxes_verbatim_ar": row.get("taxes_verbatim"),
            "official_instructions": instructions,
            "official_instruction_codes": codes_instr,
            "formalities": formalities,
            "restrictions": restrictions,
            "fta_preferences": fta_preferences,
            "zlecaf_instruction": next((t for t in fta_preferences if t["zlecaf"]), None),
            "data_status": row.get("data_status", "OK"),
            "source": "customs.gov.eg — Autorité Égyptienne des Douanes (Services/Tarif + TrfDetails)",
            "source_url": row.get("source_url"),
            "detail_endpoint": row.get("detail_endpoint"),
            "source_quality": "crawled_authentic" if row.get("data_status") == "OK" else "PARTIAL",
            "date_consulted": (row.get("extracted_at") or collecte)[:10],
        }
        if instructions:
            stats["with_instructions"] += 1
        if fta_preferences:
            stats["with_fta_preferences"] += 1
        if formalities:
            stats["with_formalities"] += 1
        if any(f["zlecaf"] for f in fta_preferences):
            stats["with_zlecaf_instruction"] += 1
        if not dd and not vat:
            stats["missing_taxes"] += 1
        stats["total"] += 1
        sub_positions.append(line)

    # positions de l'ancien fichier absentes du crawl officiel
    legacy = []
    for code, old_line in old_by_code.items():
        if code not in positions:
            l = dict(old_line)
            l["source_quality"] = "previous_crawl_unverified_today"
            l["data_status"] = "REVIEW_REQUIRED"
            legacy.append(l)
            stats["legacy_not_in_official_crawl"] += 1

    doc = {
        "country": "EGY",
        "country_name": "Égypte",
        "source": "customs.gov.eg — Autorité Égyptienne des Douanes",
        "source_url": "https://www.customs.gov.eg/Services/Tarif",
        "detail_endpoint": "POST https://www.customs.gov.eg/Services/TrfDetails?trfNumber={code}&trfType=1",
        "source_quality": "crawled_authentic",
        "extracted_at": collecte,
        "rebuilt_at": now,
        "built_by": "backend/scripts/build_egy_tariffs_official.py",
        "policy": (
            "Crawl officiel : taxes et instructions verbatim (arabe), taux lus littéralement "
            "dans les chaînes publiées. Les codes ر = instructions tarifaires/préférences "
            "(ZLECAf groupes أ/ب inclus), غ = formalités administratives, ق = restrictions. "
            "Les libellés français proviennent du crawl précédent (même autorité) et sont "
            "identifiés comme tels."
        ),
        "stats": dict(stats),
        "chapters_covered": sorted(chapters_covered),
        "sub_positions": sub_positions + legacy,
    }

    # La méthode de calcul telle que publiée par la source est un élément de
    # provenance que ce script ne reconstruit pas : la perdre à chaque
    # reconstruction viderait le document d'une information qu'il détenait.
    if old.get("calculation_method"):
        doc["calculation_method"] = old["calculation_method"]

    backup_dir = REPO_ROOT / "data" / "archive" / "crawled_backup"
    backup_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_path = backup_dir / f"EGY_tariffs_{ts}.json"
    shutil.copy2(old_path, backup_path)

    tmp = old_path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, old_path)

    write_report(
        base_path=backup_path,
        base_doc=old,
        base_origin="fichier remplacé par cette exécution, sauvegardé avant écrasement",
        base_ref=str(backup_path.relative_to(REPO_ROOT)),
        built=doc,
        stats=dict(stats),
        chapters_covered=sorted(chapters_covered),
        backup=str(backup_path.relative_to(REPO_ROOT)),
        now=now,
    )
    print(json.dumps(dict(stats), ensure_ascii=False, indent=1))
    print(f"backup: {backup_path.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

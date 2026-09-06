"""Audit de profondeur : exhaustivité des positions nationales + traçabilité + invariants."""
import json, hashlib, re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
NUM = re.compile(r"^\d+(?:[.,]\d+)?$")
SLUGS = {"ZAF":"south_africa","CMR":"cameroon","GHA":"ghana","MUS":"mauritius","RWA":"rwanda","TZA":"tanzania","TUN":"tunisia"}
for cc, slug in SLUGS.items():
    slug_dir = ROOT / "data" / slug
    reg_files = list(slug_dir.glob("*gazette_register.json")) if slug_dir.is_dir() else []
    if not reg_files:
        print(f"{cc}: juridiction absente de cette branche (1 PR par pays) — SKIPPÉ")
        continue
    cp = ROOT / "backend" / "data" / f"{cc}_tariffs.json"
    d = json.loads(cp.read_text(encoding="utf-8"))
    if "tariff_lines" in d:
        lines = d["tariff_lines"]
        pos = {sp["code"] for l in lines for sp in (l.get("sub_positions") or []) if sp.get("code")}
        hs6_sans_sp = sum(1 for l in lines if not (l.get("sub_positions") or []))
        dd_missing = sum(1 for l in lines if not any(
            (t.get("tax") in ("DD","D.D","CET","DDDROIT") or str(t.get("tax","")).startswith("DD"))
            for t in (l.get("taxes_detail") or [])))
        n_lines = len(lines)
    else:
        # mode NATIONAL : le tarif national authentique est la source unique
        sps = d.get("positions") or d.get("sub_positions") or []
        pos = {sp["hs_code"] for sp in sps if sp.get("hs_code")}
        hs6_sans_sp = 0
        dd_missing = sum(1 for sp in sps if not sp.get("consolidation_flag") and not any(
            (t.get("code","").startswith("DD") or t.get("tax_name","").startswith("CET") or t.get("is_cet"))
            for t in (sp.get("taxes_import") or sp.get("taxes_detail") or [])))
        n_lines = len(sps)
    reg = json.loads(reg_files[0].read_text(encoding="utf-8"))
    sha_ok = reg["base_tariff_documentation"]["sha256"] == hashlib.sha256(cp.read_bytes()).hexdigest()
    formalities = (
        [f for l in lines for f in (l.get("administrative_formalities") or [])]
        if "tariff_lines" in d
        else [f for sp in (d.get("positions") or d.get("sub_positions") or [])
              for f in (sp.get("reglementation_import") or [])]
    )
    num_bad = sum(1 for f in formalities
                  if isinstance(f, dict) and (f.get("document_fr") or f.get("description"))
                  and NUM.fullmatch((f.get("document_fr") or f.get("description") or "").strip()))
    ov = json.loads((slug_dir / "legal_overrides.json").read_text(encoding="utf-8"))
    # correspondance SH6 (comme le moteur _hs_match) : une mesure portant un
    # code ch.31xxxx00 est couverte si le SH6 (310100) est publié par la source
    published_hs6 = {l.get("hs6") for l in d.get("tariff_lines", []) if l.get("hs6")} | {c[:6] for c in pos}
    orphan = sum(1 for m in ov["measures"] for c in m["hs_codes"] if c[:6] not in published_hs6)
    print(f"{cc}: SP={len(pos)} | lignes={n_lines} | hs6_sans_SP={hs6_sans_sp} | sha_OK={sha_ok} | FAP_num_bad={num_bad} | mesures_orphelines={orphan} | DD_manquantes={dd_missing}")

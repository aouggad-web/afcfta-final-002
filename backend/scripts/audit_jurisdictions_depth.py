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
    lines = d["tariff_lines"]
    pos = {sp["code"] for l in lines for sp in (l.get("sub_positions") or []) if sp.get("code")}
    hs6_sans_sp = sum(1 for l in lines if not (l.get("sub_positions") or []))
    reg = json.loads(reg_files[0].read_text(encoding="utf-8"))
    sha_ok = reg["base_tariff_documentation"]["sha256"] == hashlib.sha256(cp.read_bytes()).hexdigest()
    num_bad = sum(1 for l in lines for f in (l.get("administrative_formalities") or [])
                  if isinstance(f, dict) and f.get("document_fr") and NUM.fullmatch(f["document_fr"].strip()))
    ov = json.loads((slug_dir / "legal_overrides.json").read_text(encoding="utf-8"))
    orphan = sum(1 for m in ov["measures"] for c in m["hs_codes"] if c not in pos)
    dd_missing = sum(1 for l in lines if not any(t.get("tax") in ("DD","D.D","CET","DDDROIT") for t in (l.get("taxes_detail") or [])))
    print(f"{cc}: SP={len(pos)} | hs6_sans_SP={hs6_sans_sp} | sha_OK={sha_ok} | FAP_num_bad={num_bad} | mesures_orphelines={orphan} | DD_manquantes={dd_missing}")

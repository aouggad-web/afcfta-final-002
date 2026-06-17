"""
Adaptateur de bloc régional — propagation du Tarif Extérieur Commun (TEC/TDC).

Les membres d'une union douanière appliquent le MÊME tarif extérieur commun aux
importations en provenance des pays tiers (droit de douane + prélèvements
communautaires). C'est un fait juridique : le TEC CEDEAO et le TDC CEMAC sont
identiques pour tous les États membres. Seule la TVA est nationale.

Cet adaptateur comble les lacunes : un membre dépourvu de fichier hérite du tarif
commun authentique détenu par un État de référence du même bloc, avec :
  - le droit de douane + les prélèvements communautaires copiés tels quels,
  - la TVA remplacée par le taux NATIONAL du pays cible,
  - une provenance 'regional_cet_official' et une source explicite.

100 % hors réseau : la source (le TEC) existe déjà dans le dépôt via les États
membres déjà crawlés. Un futur crawl national pourra superséder ces fichiers.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

from ..manifest import _load_registry, Provenance
from ..canonical import validate_authenticity

CRAWLED_DIR = Path(__file__).resolve().parents[2] / "data" / "crawled"

VAT_CODES = {"TVA", "VAT"}

# Pays qui appliquent le TEC du bloc MAIS avec des prélèvements nationaux
# spécifiques (au-delà du droit commun) : ils requièrent un crawl national propre
# plutôt qu'une simple propagation du TEC. Ex. Ghana (GETFUND, NHIL).
NATIONAL_ONLY = {"GHA"}

# Référence + instrument officiel par bloc.
BLOC_REFERENCE: Dict[str, Dict[str, str]] = {
    "ECOWAS": {
        "reference": "BEN",
        "instrument": "Tarif Extérieur Commun CEDEAO (TEC)",
        "instrument_url": "https://www.ecowas.int",
        "members": "BEN BFA CIV CPV GHA GIN GMB GNB LBR MLI NER NGA SEN SLE TGO",
    },
    "CEMAC": {
        "reference": "CMR",
        "instrument": "Tarif Douanier Commun CEMAC (TDC)",
        "instrument_url": "https://www.cemac.int",
        "members": "CAF CMR COG GAB GNQ TCD",
    },
}


def _container_key(doc: Dict[str, Any]) -> str:
    for k in ("sub_positions", "positions", "tariff_lines"):
        if k in doc:
            return k
    return "positions"


def _swap_vat(pos: Dict[str, Any], vat_rate: float) -> Dict[str, Any]:
    """Copie une position en remplaçant la TVA par le taux national cible.

    Le droit de douane et les prélèvements communautaires (communs au bloc) sont
    conservés à l'identique ; seule la TVA est nationale.
    """
    p = copy.deepcopy(pos)

    taxes = p.get("taxes")
    if isinstance(taxes, dict):
        for code in list(taxes.keys()):
            if code.upper() in VAT_CODES:
                taxes[code] = vat_rate

    detail = p.get("taxes_detail")
    if isinstance(detail, list):
        for td in detail:
            if str(td.get("tax_code", "")).upper() in VAT_CODES:
                td["rate"] = vat_rate

    return p


def build_regional_file(
    target_iso: str,
    bloc: str,
) -> Tuple[Dict[str, Any], List[str]]:
    """Construit le document tarifaire régional pour un pays cible.

    Retourne (doc, issues_de_validation).
    """
    cfg = BLOC_REFERENCE[bloc]
    ref_iso = cfg["reference"]
    ref_path = CRAWLED_DIR / f"{ref_iso}_tariffs.json"
    if not ref_path.exists():
        raise FileNotFoundError(f"Fichier de référence introuvable : {ref_path}")

    R = _load_registry().AFRICAN_COUNTRIES_REGISTRY
    tcfg = R.get(target_iso.upper())
    if not tcfg:
        raise ValueError(f"Pays inconnu au registre : {target_iso}")
    vat_rate = float(tcfg.get("vat_rate", 0.0))
    country_name = tcfg.get("name_fr") or tcfg.get("name_en") or target_iso

    ref_doc = json.loads(ref_path.read_text(encoding="utf-8"))
    key = _container_key(ref_doc)
    ref_positions = ref_doc.get(key, [])

    positions = [_swap_vat(p, vat_rate) for p in ref_positions]

    source = (
        f"{cfg['instrument']} — appliqué par {country_name} "
        f"(réf. État membre {ref_iso}). TVA = taux national {vat_rate:g}%."
    )
    doc = {
        "country_code": target_iso.upper(),
        "country": target_iso.upper(),
        "country_name": country_name,
        "source": source,
        "source_url": cfg["instrument_url"],
        "source_quality": Provenance.REGIONAL_CET.value,
        "economic_community": bloc,
        "tariff_system": cfg["instrument"],
        "derived_from": ref_iso,
        "note": (
            "Tarif extérieur commun du bloc (droit de douane + prélèvements "
            "communautaires identiques entre États membres). TVA nationale. "
            "Des dérogations nationales temporaires peuvent s'appliquer ; un "
            "crawl national ultérieur peut superséder ce fichier."
        ),
        "total_positions": len(positions),
        "stats": {"sub_positions": len(positions)},
        key: positions,
    }

    ok, issues = validate_authenticity(doc)
    return doc, ([] if ok else issues)


def _positions_count(iso: str) -> int:
    path = CRAWLED_DIR / f"{iso}_tariffs.json"
    if not path.exists():
        return -1
    doc = json.loads(path.read_text(encoding="utf-8"))
    for k in ("sub_positions", "positions", "tariff_lines"):
        if k in doc:
            return len(doc[k])
    return 0


def find_gaps(bloc: str) -> List[str]:
    """Membres du bloc dépourvus de données (fichier absent ou vide).

    Exclut les pays NATIONAL_ONLY, qui nécessitent un crawl national dédié.
    """
    members = BLOC_REFERENCE[bloc]["members"].split()
    return [
        iso for iso in members
        if _positions_count(iso) <= 0 and iso not in NATIONAL_ONLY
    ]


def deferred_national(bloc: str) -> List[str]:
    """Membres du bloc sans données mais réservés à un crawl national."""
    members = BLOC_REFERENCE[bloc]["members"].split()
    return [
        iso for iso in members
        if _positions_count(iso) <= 0 and iso in NATIONAL_ONLY
    ]


def fill_bloc_gaps(bloc: str, dry_run: bool = True) -> List[Dict[str, Any]]:
    """Comble les lacunes d'un bloc. Retourne le rapport par pays.

    dry_run=True : ne fait qu'évaluer (aucune écriture).
    """
    results = []
    for iso in find_gaps(bloc):
        try:
            doc, issues = build_regional_file(iso, bloc)
            if issues:
                results.append({"iso3": iso, "status": "rejected", "detail": "; ".join(issues)})
                continue
            n = doc["stats"]["sub_positions"]
            if not dry_run:
                out = CRAWLED_DIR / f"{iso}_tariffs.json"
                out.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
            results.append({
                "iso3": iso,
                "status": "would_write" if dry_run else "written",
                "detail": f"{n} positions (TEC {bloc}, TVA nationale)",
            })
        except Exception as e:
            results.append({"iso3": iso, "status": "error", "detail": str(e)})
    return results

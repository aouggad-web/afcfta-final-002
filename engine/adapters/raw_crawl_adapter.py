"""
Moteur générique d'ingestion de crawls tarifaires réels — multi-pays
=====================================================================
Objectif : MAXIMISER le nombre de positions tarifaires officielles ingérées,
au niveau de ligne nationale le plus profond (8 / 10 / 11 digits), avec le
MINIMUM d'effort par pays.

Principe
--------
Tous les crawls douaniers nationaux partagent la même forme « plate » :

    {
      "country_code": "ETH",
      "source": "...", "source_url": "...", "crawled_at": "...",
      "positions": [
        {"code": "...", "description_en": "...", "chapter": "..",
         "dd_rate": .., "excise_rate": .., "vat_rate": .., ...}
      ]
    }

Au lieu d'écrire un adaptateur complet par pays, on décrit chaque régime fiscal
national par un **TaxProfile** : une séquence ordonnée de composantes (droit,
accise, TVA, surtaxe, retenue…), chacune indiquant :
  - d'où vient son taux (champ du crawl, ou taux légal fixe),
  - son assiette (CIF, ou CIF + composantes amont),
  - quand l'émettre (toujours, ou seulement si > 0),
  - sa nature canonique (CUSTOMS_DUTY / EXCISE / VAT / LEVY / OTHER_TAX).

Ajouter un pays = ajouter un TaxProfile dans PROFILES (≈ 15 lignes) + déposer
son crawl. Le moteur produit immédiatement des CanonicalTariffLine VERIFIED/A.

Usage CLI
---------
    python engine/adapters/raw_crawl_adapter.py ETH eth_raw.json engine/output/
    python engine/adapters/raw_crawl_adapter.py MUS mus_raw.json engine/output/ --dry-run
    python engine/adapters/raw_crawl_adapter.py --list      # profils disponibles
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from datetime import datetime, date, timezone
from pathlib import Path
from typing import Callable, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from schemas.canonical_model import (
    CanonicalTariffLine, CommodityCode, Measure, Provenance,
    MeasureType, DataStatus, ReliabilityGrade, RateType, DutyBasis,
    SCHEMA_VERSION,
)


# ============================================================================
# Description déclarative d'un régime fiscal national
# ============================================================================

@dataclass
class TaxComponent:
    """Une composante fiscale (droit, taxe, prélèvement) d'un régime national."""
    code: str                       # ex. "D.D", "ER", "SR", "T.V.A", "WHR"
    name_fr: str
    name_en: str
    measure_type: MeasureType
    basis: DutyBasis
    rate_field: Optional[str] = None   # champ du crawl (ex. "dd_rate")
    fixed_rate: Optional[float] = None # taux légal fixe (ex. 10.0 pour surtaxe)
    includes_codes: list[str] = field(default_factory=list)  # pour CIF_PLUS_INCLUDED
    emit_when: str = "always"          # "always" | "positive"
    is_customs_duty: bool = False      # → is_zlecaf_applicable + savings_pct
    legal_reference: Optional[str] = None
    observation: Optional[str] = None

    def resolve_rate(self, pos: dict) -> float:
        if self.fixed_rate is not None:
            return float(self.fixed_rate)
        if self.rate_field:
            return float(pos.get(self.rate_field) or 0)
        return 0.0


def _default_sensitivity(dd: float, excise: float) -> str:
    if dd >= 30 or excise >= 100:
        return "sensible"
    if dd >= 15 or excise >= 30:
        return "élevé"
    return "normal"


@dataclass
class TaxProfile:
    """Profil fiscal national complet."""
    country_iso3: str
    source_name: str
    source_url: str
    source_document: str
    components: list[TaxComponent]
    notes: str = ""
    version_date: Optional[date] = None
    data_status: DataStatus = DataStatus.VERIFIED
    reliability: ReliabilityGrade = ReliabilityGrade.A
    hs_version: str = "HS2022"
    sensitivity_fn: Callable[[float, float], str] = _default_sensitivity


# ============================================================================
# Moteur de conversion
# ============================================================================

def _build_provenance(profile: TaxProfile, crawled_at: str) -> Provenance:
    try:
        retrieved = datetime.fromisoformat(crawled_at.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        retrieved = datetime.now(timezone.utc)
    return Provenance(
        data_status=profile.data_status,
        reliability=profile.reliability,
        source_name=profile.source_name,
        source_url=profile.source_url,
        source_document=profile.source_document,
        version_date=profile.version_date,
        retrieved_at=retrieved,
        notes=profile.notes or None,
    )


def _convert_position(pos: dict, profile: TaxProfile,
                      prov: Provenance) -> CanonicalTariffLine:
    code = str(pos["code"]).strip()
    hs6 = code[:6]
    iso = profile.country_iso3

    measures: list[Measure] = []
    emitted_codes: list[str] = []
    dd_rate = 0.0
    excise_rate = 0.0

    # Séquence FIXE par position dans le profil (idx 0 → 10, idx 1 → 20, …),
    # indépendante des composantes effectivement émises : la séquence d'une
    # taxe reste stable même si une composante amont est absente (ex. accise).
    for idx, comp in enumerate(profile.components):
        rate = comp.resolve_rate(pos)
        if comp.emit_when == "positive" and rate <= 0:
            continue

        # Assiette : ne retenir dans includes que les composantes réellement émises
        basis_includes: list[str] = []
        if comp.basis == DutyBasis.CIF_PLUS_INCLUDED:
            basis_includes = [c for c in comp.includes_codes if c in emitted_codes]

        measures.append(Measure(
            country_iso3=iso,
            national_code=code,
            measure_type=comp.measure_type,
            code=comp.code,
            name_fr=comp.name_fr,
            name_en=comp.name_en,
            rate_pct=rate,
            rate_type=RateType.EXEMPT if rate == 0 else RateType.AD_VALOREM,
            basis=comp.basis,
            basis_includes=basis_includes,
            sequence=(idx + 1) * 10,
            is_zlecaf_applicable=comp.is_customs_duty,
            legal_reference=comp.legal_reference,
            observation=comp.observation or f"{comp.code} — {profile.source_name}",
        ))
        emitted_codes.append(comp.code)

        if comp.is_customs_duty:
            dd_rate = rate
        elif comp.measure_type == MeasureType.EXCISE:
            excise_rate = max(excise_rate, rate)

    total_npf = round(sum(m.rate_pct or 0 for m in measures), 4)
    total_zlecaf = round(total_npf - dd_rate, 4)

    commodity = CommodityCode(
        country_iso3=iso,
        national_code=code,
        hs6=hs6,
        digits=pos.get("digits", len(code)),
        description_fr=pos.get("description_en", ""),
        description_en=pos.get("description_en"),
        chapter=str(pos.get("chapter", code[:2])),
        unit=pos.get("unit"),
        hs_version=profile.hs_version,
        sensitivity=profile.sensitivity_fn(dd_rate, excise_rate),
    )

    return CanonicalTariffLine(
        commodity=commodity,
        measures=measures,
        total_npf_pct=total_npf,
        total_zlecaf_pct=total_zlecaf,
        savings_pct=round(dd_rate, 4),
        last_updated=datetime.now(timezone.utc),
        schema_version=SCHEMA_VERSION,
        provenance=prov,
    )


# ============================================================================
# GARDE-FOUS ANTI-DONNÉES-GÉNÉRIQUES (verrous durs)
# ============================================================================
# Objectif : il doit être IMPOSSIBLE de produire une CanonicalTariffLine
# estampillée VERIFIED/A à partir d'une donnée inventée, générée ou non
# traçable. On préfère REFUSER l'ingestion plutôt que d'émettre du faux.

class ProfileValidationError(ValueError):
    """Profil fiscal mal formé : risque de taux inventés."""


class CrawlValidationError(ValueError):
    """Crawl non conforme : non traçable, synthétique, ou statistiquement suspect."""


# Marqueurs trahissant une origine non officielle
_SYNTHETIC_MARKERS = {
    "synthetic", "generated", "template", "random", "fake", "mock",
    "sample", "dummy", "placeholder", "test",
}


def _validate_profile(profile: TaxProfile) -> None:
    """
    VERROU 1 — Le profil ne peut pas fabriquer de taux par produit.

    - Le droit de douane (qui varie par produit) DOIT provenir d'un champ du
      crawl (rate_field), jamais d'un taux fixe codé en dur.
    - Une composante à taux fixe n'est admise que pour une taxe statutaire
      (TVA/surtaxe/retenue) ET doit porter une référence légale.
    - Toute composante sans source de taux est rejetée.
    """
    cd = [c for c in profile.components if c.is_customs_duty]
    if len(cd) != 1:
        raise ProfileValidationError(
            f"[{profile.country_iso3}] Le profil doit avoir exactement 1 composante "
            f"droit de douane (is_customs_duty=True), trouvé {len(cd)}.")
    duty = cd[0]
    if duty.rate_field is None or duty.fixed_rate is not None:
        raise ProfileValidationError(
            f"[{profile.country_iso3}] Le droit de douane '{duty.code}' doit lire son "
            f"taux dans un champ du crawl (rate_field), jamais via fixed_rate. "
            f"Un droit de douane fixe codé en dur = donnée inventée → interdit.")

    for c in profile.components:
        if c.rate_field is None and c.fixed_rate is None:
            raise ProfileValidationError(
                f"[{profile.country_iso3}] Composante '{c.code}' sans source de taux "
                f"(ni rate_field ni fixed_rate).")
        if c.fixed_rate is not None:
            if c.is_customs_duty:
                raise ProfileValidationError(
                    f"[{profile.country_iso3}] '{c.code}' : un droit de douane ne peut "
                    f"pas être à taux fixe.")
            if not c.legal_reference:
                raise ProfileValidationError(
                    f"[{profile.country_iso3}] Composante à taux fixe '{c.code}' "
                    f"({c.fixed_rate} %) SANS référence légale — un taux statutaire "
                    f"doit citer sa base légale (proclamation, loi de finances…).")


def _validate_crawl(data: dict, profile: TaxProfile) -> list[str]:
    """
    VERROU 2 — Le crawl doit être réel, traçable et statistiquement plausible.

    Refuse :
      - absence de source / source_url ;
      - data_type marqué synthétique/généré/template ;
      - aucune position ;
      - champ de droit de douane absent d'une partie des positions ;
      - une seule bande tarifaire (signature d'un remplissage par template) ;
      - tous les droits à zéro (donnée vide déguisée).
    Retourne la liste des avertissements non bloquants.
    """
    iso = profile.country_iso3
    warnings: list[str] = []

    source = str(data.get("source", "")).strip()
    source_url = str(data.get("source_url", "")).strip()
    if not source:
        raise CrawlValidationError(f"[{iso}] Champ 'source' manquant — origine non traçable.")
    if not source_url:
        raise CrawlValidationError(f"[{iso}] Champ 'source_url' manquant — origine non traçable.")

    data_type = str(data.get("data_type", "")).lower()
    if any(m in data_type for m in _SYNTHETIC_MARKERS):
        raise CrawlValidationError(
            f"[{iso}] data_type='{data_type}' marqué synthétique/généré — "
            f"refus d'ingestion en VERIFIED.")

    positions = data.get("positions", [])
    if not positions:
        raise CrawlValidationError(f"[{iso}] Aucune position dans le crawl.")

    # Le champ du droit de douane doit être présent (pas défaut silencieux à 0)
    duty = next(c for c in profile.components if c.is_customs_duty)
    field_name = duty.rate_field
    missing = sum(1 for p in positions if field_name not in p)
    if missing:
        raise CrawlValidationError(
            f"[{iso}] Champ droit de douane '{field_name}' absent de {missing}/"
            f"{len(positions)} positions — interdit de combler par 0 (ce serait inventer).")

    # Réalisme : un vrai tarif national a TOUJOURS plusieurs bandes
    duty_values = {float(p.get(field_name) or 0) for p in positions}
    if duty_values == {0.0}:
        raise CrawlValidationError(
            f"[{iso}] Tous les droits de douane sont à 0 % — donnée vide ou non extraite.")
    if len(duty_values) < 2:
        raise CrawlValidationError(
            f"[{iso}] Une seule bande de droit ({duty_values}) sur {len(positions)} "
            f"positions — signature typique d'un remplissage par template. Refus.")

    # Avertissements non bloquants
    if len(positions) < 500:
        warnings.append(
            f"[{iso}] Seulement {len(positions)} positions — un tarif national complet "
            f"en compte généralement plusieurs milliers. Vérifier l'exhaustivité du crawl.")

    return warnings


def convert_with_profile(data: dict, profile: TaxProfile,
                         strict: bool = True) -> list[CanonicalTariffLine]:
    """
    Convertit un dict raw_crawl en CanonicalTariffLine selon un profil donné.

    En mode strict (défaut), applique les garde-fous anti-données-génériques :
    lève ProfileValidationError / CrawlValidationError si l'origine n'est pas
    réelle et traçable, AVANT de produire la moindre ligne.
    """
    if strict:
        _validate_profile(profile)
        for w in _validate_crawl(data, profile):
            print(f"  ⚠ {w}")
    prov = _build_provenance(
        profile, data.get("crawled_at", datetime.now(timezone.utc).isoformat()))
    return [_convert_position(p, profile, prov) for p in data.get("positions", [])]


# ============================================================================
# Registre des profils nationaux
# ============================================================================

PROFILES: dict[str, TaxProfile] = {}


def register(profile: TaxProfile) -> TaxProfile:
    PROFILES[profile.country_iso3] = profile
    return profile


# ── ETH — Ethiopian Customs Commission ──────────────────────────────────────
register(TaxProfile(
    country_iso3="ETH",
    source_name="Ethiopian Customs Commission (ECC) — Tariff Schedule",
    source_url="https://customs.erca.gov.et/trade/customs-division/tariff",
    source_document=(
        "Ethiopian Customs Commission — Tariff Schedule officiel (DR/ER/SR/VAT/WHR) "
        "— https://customs.erca.gov.et/trade/customs-division/tariff"
    ),
    notes=(
        "Crawl direct du portail douanier ECC officiel. SR=10%, VAT=15%, WHR=3% "
        "sont des taux légaux fixes. Exonérations spécifiques non modélisées."
    ),
    sensitivity_fn=lambda dd, ex: (
        "sensible" if dd >= 30 else "élevé" if dd >= 20 else "normal"),
    components=[
        TaxComponent("D.D", "Droit de Douane (DD)", "Customs Duty",
                     MeasureType.CUSTOMS_DUTY, DutyBasis.CIF,
                     rate_field="dd_rate", emit_when="always", is_customs_duty=True),
        TaxComponent("ER", "Excise Duty (ER)", "Excise Duty",
                     MeasureType.EXCISE, DutyBasis.CIF,
                     rate_field="excise_rate", emit_when="positive"),
        TaxComponent("SR", "Surtax (SR) — 10 % de (CIF + DD + Excise)", "Surtax",
                     MeasureType.LEVY, DutyBasis.CIF_PLUS_INCLUDED,
                     fixed_rate=10.0, includes_codes=["D.D", "ER"],
                     emit_when="always", legal_reference="Proclamation 312/2002"),
        TaxComponent("T.V.A", "Taxe sur la Valeur Ajoutée (TVA) — 15 %",
                     "Value Added Tax (VAT)",
                     MeasureType.VAT, DutyBasis.CIF_PLUS_INCLUDED,
                     fixed_rate=15.0, includes_codes=["D.D", "ER", "SR"],
                     emit_when="always",
                     legal_reference="Value Added Tax Proclamation 285/2002"),
        TaxComponent("WHR", "Retenue à la source (WHR) — 3 % du CIF",
                     "Withholding Tax at Import",
                     MeasureType.OTHER_TAX, DutyBasis.CIF,
                     fixed_rate=3.0, emit_when="always",
                     legal_reference="Income Tax Proclamation 979/2016"),
    ],
))

# ── MUS — Mauritius Revenue Authority ───────────────────────────────────────
register(TaxProfile(
    country_iso3="MUS",
    source_name="MRA Integrated Tariff Schedule HS2022 (Maurice)",
    source_url="https://www.mra.mu/download/TariffInfo010426.pdf",
    source_document=(
        "Mauritius Revenue Authority — Integrated Tariff Schedule HS2022 "
        "as at 01 April 2026 — https://www.mra.mu/download/TariffInfo010426.pdf"
    ),
    version_date=date(2026, 4, 1),
    notes=(
        "Crawl du PDF officiel MRA Integrated Tariff HS2022 (01/04/2026). "
        "Excise élevé tabac/alcool (jusqu'à 230 %). 1 415 positions exonérées de VAT. "
        "Taxe environnementale (EPL) non incluse."
    ),
    components=[
        TaxComponent("D.D", "Droit de Douane général (NPF)",
                     "General (MFN) Customs Duty",
                     MeasureType.CUSTOMS_DUTY, DutyBasis.CIF,
                     rate_field="dd_rate", emit_when="always", is_customs_duty=True),
        TaxComponent("EXCISE", "Excise Duty", "Excise Duty",
                     MeasureType.EXCISE, DutyBasis.CIF,
                     rate_field="excise_rate", emit_when="positive"),
        TaxComponent("T.V.A", "Taxe sur la Valeur Ajoutée (VAT) — 15 %",
                     "Value Added Tax (VAT)",
                     MeasureType.VAT, DutyBasis.CIF_PLUS_INCLUDED,
                     rate_field="vat_rate", includes_codes=["D.D", "EXCISE"],
                     emit_when="positive",
                     legal_reference="Value Added Tax Act 1998 (as amended)"),
    ],
))


# ============================================================================
# CLI
# ============================================================================

def process_file(country: str, json_path: str | Path, output_dir: str | Path,
                 dry_run: bool = False) -> dict:
    country = country.upper()
    if country not in PROFILES:
        raise KeyError(
            f"Aucun profil fiscal pour {country!r}. "
            f"Profils disponibles : {', '.join(sorted(PROFILES))}. "
            f"Ajoutez un TaxProfile dans PROFILES.")
    profile = PROFILES[country]
    data = json.loads(Path(json_path).read_text(encoding="utf-8"))

    file_country = str(data.get("country_code", country)).upper()
    if file_country != country:
        print(f"  ⚠ country_code du fichier ({file_country}) ≠ profil demandé ({country})")

    records = convert_with_profile(data, profile)
    chapters = {r.commodity.chapter for r in records}
    dd_dist: dict[float, int] = {}
    for r in records:
        dd = next((m.rate_pct for m in r.measures if m.is_zlecaf_applicable), 0) or 0
        dd_dist[dd] = dd_dist.get(dd, 0) + 1

    print(f"  {country} : {len(records):,} positions / {len(chapters)} chapitres / "
          f"{profile.data_status.value}/{profile.reliability.value}")
    print(f"    DD bands : {dict(sorted(dd_dist.items()))}")

    if dry_run:
        print("  (--dry-run) Fichier NON écrit.")
        return {"written": 0, "total": len(records)}

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{country}_canonical.jsonl"
    with out_path.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(r.model_dump_json() + "\n")
    print(f"  → {out_path}")
    return {"written": len(records), "total": len(records), "output": str(out_path)}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("country", nargs="?", help="Code ISO3 (ex. ETH, MUS)")
    ap.add_argument("input", nargs="?", help="Chemin du crawl raw JSON")
    ap.add_argument("output", nargs="?", help="Répertoire de sortie")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--list", action="store_true", help="Lister les profils disponibles")
    args = ap.parse_args()

    if args.list:
        print("Profils fiscaux disponibles :")
        for iso in sorted(PROFILES):
            p = PROFILES[iso]
            print(f"  {iso} — {p.source_name} ({len(p.components)} composantes)")
        return

    if not (args.country and args.input and args.output):
        ap.error("country, input et output sont requis (ou utilisez --list)")
    process_file(args.country, args.input, args.output, dry_run=args.dry_run)


if __name__ == "__main__":
    main()

"""
Adaptateur Algérie — source conformepro.dz (format CSV tarif intégré)
=====================================================================

Premier adaptateur de DONNÉES RÉELLES du plan de refonte (vague 1).

Entrée  : CSV conformepro (délimiteur ';', BOM UTF-8, colonnes du fichier
          DZA_tarif_douanier_echantillon.csv — même format attendu pour
          l'extraction complète des 98 chapitres).
Sortie  : lignes canoniques v4 avec assiette structurée, séquence de calcul,
          formalités réelles (dénomination + autorité émettrice) et
          avantages fiscaux par accord.

Statut de provenance émis : PARTIAL / fiabilité B.
  conformepro.dz est un agrégateur privé du tarif intégré algérien — pas la
  source primaire (DGD / Journal Officiel). Les lignes passeront VERIFIED/A
  après recoupement avec le tarif officiel DGD.

Séquence de calcul algérienne implémentée (Circ. 419 DGD) :
  10  D.D    Droit de Douane                          → sur valeur CAF
  15  DAPS   Droit Additionnel Provisoire de Sauvegarde → sur valeur CAF
  20  T.C.S  Taxe de Contribution de Solidarité        → sur valeur CAF
  30  PRCT   Prélèvement Compensation Transport        → sur valeur CAF
  90  T.V.A  Taxe sur la Valeur Ajoutée → sur CAF + D.D + DAPS + T.C.S + PRCT
"""

import csv
import io
import re
from datetime import datetime, date
from pathlib import Path
from typing import Generator, List, Optional

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from schemas.canonical_model import (
    CommodityCode, Measure, Requirement, FiscalAdvantage,
    CanonicalTariffLine, MeasureType, RequirementType,
    Provenance, DataStatus, ReliabilityGrade, RateType, DutyBasis,
    SCHEMA_VERSION,
)

COUNTRY = "DZA"

# --- Référentiel des autorités émettrices algériennes (extensible) ---
AUTHORITIES = {
    "m. agriculture": ("Ministère de l'Agriculture et du Développement Rural", "MADR"),
    "m. sante": ("Ministère de la Santé", "MS"),
    "m. commerce": ("Ministère du Commerce et de la Promotion des Exportations", "MCPE"),
    "m. energie": ("Ministère de l'Énergie et des Mines", "MEM"),
    "dgd": ("Direction Générale des Douanes", "DGD"),
    "banque d'algerie": ("Banque d'Algérie", "BA"),
}

# --- Inférence du type de formalité depuis sa dénomination ---
REQ_TYPE_RULES = [
    (r"^visa\b", RequirementType.VISA),
    (r"^derogation\b", RequirementType.DEROGATION),
    (r"^autorisation\b", RequirementType.AUTHORIZATION),
    (r"^certificat\b", RequirementType.CERTIFICATE),
    (r"^declaration\b", RequirementType.IMPORT_DECLARATION),
    (r"^licence\b|^license\b", RequirementType.LICENSE),
    (r"^permis\b", RequirementType.PERMIT),
    (r"controle|inspection", RequirementType.INSPECTION),
]


def _f(val: str) -> Optional[float]:
    """Parse un taux ; '' -> None (absent de la source, à distinguer de 0)."""
    val = (val or "").strip().replace(",", ".")
    return float(val) if val else None


def _parse_authority(text: str):
    """Extrait l'autorité entre parenthèses : 'Visa ... (m. agriculture)'."""
    m = re.search(r"\(([^)]+)\)\s*$", text)
    if not m:
        return text.strip(), None, None
    label = text[: m.start()].strip()
    key = m.group(1).strip().lower()
    full, code = AUTHORITIES.get(key, (m.group(1).strip(), None))
    return label, full, code


def _req_type(label: str) -> RequirementType:
    low = label.lower()
    for pattern, rtype in REQ_TYPE_RULES:
        if re.search(pattern, low):
            return rtype
    return RequirementType.AUTHORIZATION


class DZAConformeproAdapter:
    """Parse le CSV conformepro vers le format canonique v4."""

    def __init__(self, source_path: str, version_date: Optional[date] = None):
        self.source_path = Path(source_path)
        self.version_date = version_date
        self.stats = {"lines": 0, "measures": 0, "requirements": 0, "advantages": 0}

    # ------------------------------------------------------------------
    def provenance(self) -> Provenance:
        return Provenance(
            data_status=DataStatus.PARTIAL,
            reliability=ReliabilityGrade.B,
            source_name="conformepro.dz — tarif intégré algérien (agrégateur privé)",
            source_url="https://conformepro.dz",
            source_document=self.source_path.name,
            version_date=self.version_date,
            retrieved_at=datetime.now(),
            notes="Source secondaire fidèle au tarif intégré DGD ; passera "
                  "VERIFIED/A après recoupement avec le tarif officiel "
                  "DGD / Journal Officiel.",
        )

    # ------------------------------------------------------------------
    def transform(self) -> Generator[CanonicalTariffLine, None, None]:
        raw = self.source_path.read_text(encoding="utf-8-sig")
        reader = csv.DictReader(io.StringIO(raw), delimiter=";")
        for row in reader:
            row = {k.strip(): (v or "").strip() for k, v in row.items()}
            code = row.get("Code_SH_10_chiffres", "")
            if not re.fullmatch(r"\d{10}", code):
                continue
            yield self._line(row, code)
            self.stats["lines"] += 1

    # ------------------------------------------------------------------
    def _line(self, row: dict, code: str) -> CanonicalTariffLine:
        commodity = CommodityCode(
            country_iso3=COUNTRY,
            national_code=code,
            hs6=code[:6],
            digits=10,
            description_fr=row.get("Designation_complete") or row.get("Designation", ""),
            description_official_fr=row.get("Designation"),
            chapter=row.get("Chapitre", code[:2]).zfill(2),
            hs_version="HS2022",
        )

        measures = self._measures(code, row)
        requirements = self._requirements(code, row.get("Formalites_particulieres", ""))
        advantages = self._advantages(code, row.get("Avantages_fiscaux", ""))

        total_npf = sum(m.rate_pct or 0 for m in measures)

        line = CanonicalTariffLine(
            commodity=commodity,
            measures=measures,
            requirements=requirements,
            fiscal_advantages=advantages,
            total_npf_pct=round(total_npf, 2),
            source_file=str(self.source_path),
            last_updated=datetime.now(),
            schema_version=SCHEMA_VERSION,
            provenance=self.provenance(),
        )
        self.stats["measures"] += len(measures)
        self.stats["requirements"] += len(requirements)
        self.stats["advantages"] += len(advantages)
        return line

    # ------------------------------------------------------------------
    def _measures(self, code: str, row: dict) -> List[Measure]:
        dd = _f(row.get("Droit_de_Douane_DD_pct"))
        tva = _f(row.get("TVA_pct"))
        tcs = _f(row.get("TCS_pct"))
        prct = _f(row.get("PRCT_pct"))
        daps = _f(row.get("DAPS_pct"))

        measures: List[Measure] = []

        def add(mtype, mcode, name_fr, name_en, rate, seq, *,
                basis=DutyBasis.CIF, includes=None, legal=None,
                zlecaf=False, obs=None):
            measures.append(Measure(
                country_iso3=COUNTRY, national_code=code,
                measure_type=mtype, code=mcode,
                name_fr=name_fr, name_en=name_en,
                rate_pct=rate if rate is not None else 0.0,
                rate_type=RateType.EXEMPT if rate in (None, 0.0) else RateType.AD_VALOREM,
                basis=basis, basis_includes=includes or [],
                sequence=seq, legal_reference=legal,
                is_zlecaf_applicable=zlecaf,
                observation=obs,
            ))

        add(MeasureType.CUSTOMS_DUTY, "D.D", "Droit de Douane", "Customs Duty",
            dd, 10, legal="Art. 16 Code des Douanes", zlecaf=True,
            obs=None if dd is not None else
            "Taux absent de la source — vérifier le tarif DGD (exonération probable)")

        if daps is not None:
            add(MeasureType.SAFEGUARD, "DAPS",
                "Droit Additionnel Provisoire de Sauvegarde",
                "Provisional Additional Safeguard Duty",
                daps, 15, legal="LF 2018 art. 2 / arrêtés DAPS",
                obs="Mesure de sauvegarde — son maintien sous régime "
                    "préférentiel dépend de l'arrêté en vigueur")

        if tcs is not None:
            add(MeasureType.OTHER_TAX, "T.C.S", "Taxe de Contribution de Solidarité",
                "Solidarity Contribution Tax", tcs, 20, legal="Circ. 419 DGD")

        if prct is not None:
            add(MeasureType.LEVY, "PRCT",
                "Prélèvement à la Compensation du Transport",
                "Transport Compensation Levy", prct, 30, legal="Circ. 419 DGD")

        # TVA : assiette = CAF + toutes les mesures en amont présentes
        upstream = [m.code for m in measures]
        add(MeasureType.VAT, "T.V.A", "Taxe sur la Valeur Ajoutée",
            "Value Added Tax", tva, 90,
            basis=DutyBasis.CIF_PLUS_INCLUDED, includes=upstream,
            legal="Code des Taxes sur le Chiffre d'Affaires",
            obs=None if tva is not None else
            "Taux absent de la source — produit possiblement exonéré de TVA, "
            "vérifier le Code des TCA")

        return measures

    # ------------------------------------------------------------------
    def _requirements(self, code: str, raw: str) -> List[Requirement]:
        reqs = []
        for i, part in enumerate(p.strip() for p in raw.split("|") if p.strip()):
            label, authority, auth_code = _parse_authority(part)
            reqs.append(Requirement(
                country_iso3=COUNTRY, national_code=code,
                requirement_type=_req_type(label),
                code=f"DZA-F{i+1:02d}",
                document_fr=label.capitalize() if label.islower() else label,
                is_mandatory=True,
                issuing_authority=authority,
                issuing_authority_code=auth_code,
                applies_to="IMPORT",
            ))
        return reqs

    # ------------------------------------------------------------------
    def _advantages(self, code: str, raw: str) -> List[FiscalAdvantage]:
        advantages = []
        for part in (p.strip() for p in raw.split("|") if p.strip()):
            low = part.lower()
            if "zale" in low:
                advantages.append(FiscalAdvantage(
                    country_iso3=COUNTRY, national_code=code,
                    tax_code="D.D", reduced_rate_pct=0.0,
                    condition_fr="Origine d'un pays membre de la ZALE, "
                                 "certificat d'origine ZALE à l'appui",
                    agreement="ZALE (Grande Zone Arabe de Libre-Échange)",
                    required_document="Certificat d'origine ZALE",
                ))
            elif "algero-jordanienne" in low or "jordan" in low:
                for tax in ("D.D", "DAPS"):
                    advantages.append(FiscalAdvantage(
                        country_iso3=COUNTRY, national_code=code,
                        tax_code=tax, reduced_rate_pct=0.0,
                        condition_fr="Origine jordanienne dans le cadre de la "
                                     "convention algéro-jordanienne",
                        agreement="Convention Algéro-Jordanienne",
                        required_document="Certificat d'origine (convention "
                                          "algéro-jordanienne)",
                    ))
            else:
                advantages.append(FiscalAdvantage(
                    country_iso3=COUNTRY, national_code=code,
                    tax_code="D.D", reduced_rate_pct=0.0,
                    condition_fr=part, agreement=None,
                ))
        return advantages


# ----------------------------------------------------------------------
def run(source: str, output: str, version_date: Optional[str] = None) -> dict:
    """Exécute l'adaptateur et écrit le JSONL canonique."""
    vd = date.fromisoformat(version_date) if version_date else None
    adapter = DZAConformeproAdapter(source, version_date=vd)
    out = Path(output)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        for line in adapter.transform():
            f.write(line.model_dump_json(exclude_none=False) + "\n")
    return adapter.stats


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("source", help="CSV conformepro")
    ap.add_argument("output", help="JSONL canonique de sortie")
    ap.add_argument("--version-date", default=None, help="Millésime du tarif (YYYY-MM-DD)")
    args = ap.parse_args()
    stats = run(args.source, args.output, args.version_date)
    print(f"DZA conformepro -> {args.output}")
    print(f"  lignes: {stats['lines']} | mesures: {stats['measures']} | "
          f"formalités: {stats['requirements']} | avantages: {stats['advantages']}")

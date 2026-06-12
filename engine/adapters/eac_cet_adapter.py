"""
Adaptateur EAC CET — Common External Tariff (8 pays, vague 1)
==============================================================

Une seule collecte du CET publié par le Secrétariat de l'EAC (Gazette,
Annexe 1 au Protocole d'Union Douanière) débloque les États partenaires
pour la couche droits de douane (codes SH8).

Entrée  : CSV produit par ``engine/scripts/eac_cet_md_to_csv.py`` depuis
          le document officiel « EAC CET 2022 Version » (en vigueur au
          1er juillet 2022). Colonnes : Code_SH ; Designation ; Unite ;
          DD ; DD_specifique ; DD_unite_specifique ; Sensible ; Taux_brut.
Sortie  : un JSONL canonique v4 PAR PAYS ({ISO3}_canonical.jsonl).

Statut de provenance émis : PARTIAL / fiabilité B.
  Le CET est un texte communautaire officiel, mais il ne constitue pas le
  tarif intégré national : TVA et prélèvements nationaux restent à
  vérifier pays par pays. Chaque mesure nationale ajoutée ici porte une
  observation explicite « à confirmer ».

Bandes tarifaires du CET 2022 (4 bandes + produits sensibles) :
  0 %   Matières premières, biens d'équipement, intrants essentiels
  10 %  Produits intermédiaires
  25 %  Produits finis
  35 %  Produits finis disponibles dans la région (4e bande, 01/07/2022)
  Schedule 2 : produits sensibles 35-100 %, taux mixtes
  (ex. riz « 75% or $345/MT whichever is higher »)

Séquence de calcul implémentée :
  10  D.D   Droit de douane (CET)                  → sur valeur CAF
  30+ prélèvements nationaux documentés (IDF/RDL…) → voir registre
  90  TVA/VAT                                      → sur CAF + droits amont
"""

import csv
import io
import re
import unicodedata
from datetime import datetime, date
from pathlib import Path
from typing import Dict, Generator, List, Optional

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from schemas.canonical_model import (
    CommodityCode, Measure, FiscalAdvantage,
    CanonicalTariffLine, MeasureType,
    Provenance, DataStatus, ReliabilityGrade, RateType, DutyBasis,
    SCHEMA_VERSION,
)

# ----------------------------------------------------------------------
# Référentiels EAC
# ----------------------------------------------------------------------

COUNTRIES = ["BDI", "COD", "KEN", "RWA", "SSD", "TZA", "UGA", "SOM"]

# Membres en période transitoire d'alignement au CET au millésime 2022
TRANSITION_NOTE = {
    "COD": "RDC : adhésion à l'EAC en juillet 2022 — alignement au CET en "
           "période transitoire, vérifier le tarif national appliqué",
    "SOM": "Somalie : adhésion à l'EAC en mars 2024 — alignement au CET en "
           "période transitoire, vérifier le tarif national appliqué",
}

CET_BANDS = {0.0, 10.0, 25.0, 35.0}

VERIFY_NOTE = ("Taxe nationale hors CET — taux standard documenté, à confirmer "
               "contre la loi de finances en vigueur du pays")

# TVA / taxe générale sur la consommation par pays (taux standard documentés).
# Format : (code, intitulé FR, intitulé EN, taux %).
# SSD et SOM : pas de TVA documentée de manière fiable → aucune mesure émise
# (politique « données réelles uniquement », pas d'extrapolation).
VAT_BY_COUNTRY: Dict[str, tuple] = {
    "BDI": ("T.V.A", "Taxe sur la Valeur Ajoutée", "Value Added Tax", 18.0),
    "COD": ("T.V.A", "Taxe sur la Valeur Ajoutée", "Value Added Tax", 16.0),
    "KEN": ("VAT",   "Taxe sur la Valeur Ajoutée", "Value Added Tax", 16.0),
    "RWA": ("VAT",   "Taxe sur la Valeur Ajoutée", "Value Added Tax", 18.0),
    "TZA": ("VAT",   "Taxe sur la Valeur Ajoutée", "Value Added Tax", 18.0),
    "UGA": ("VAT",   "Taxe sur la Valeur Ajoutée", "Value Added Tax", 18.0),
}

# Prélèvements nationaux documentés (base légale connue), en sus du CET.
EXTRA_NATIONAL: Dict[str, List[dict]] = {
    "KEN": [
        dict(measure_type=MeasureType.LEVY, code="IDF",
             name_fr="Import Declaration Fee",
             name_en="Import Declaration Fee",
             rate_pct=2.5, basis=DutyBasis.CUSTOMS_VALUE, sequence=30,
             legal_reference="Miscellaneous Fees and Levies Act 2016, "
                             "modifié Finance Act 2023",
             observation=VERIFY_NOTE),
        dict(measure_type=MeasureType.LEVY, code="RDL",
             name_fr="Railway Development Levy",
             name_en="Railway Development Levy",
             rate_pct=1.5, basis=DutyBasis.CUSTOMS_VALUE, sequence=31,
             legal_reference="Miscellaneous Fees and Levies Act 2016, "
                             "modifié Finance Act 2023",
             observation=VERIFY_NOTE),
    ],
    "TZA": [
        dict(measure_type=MeasureType.LEVY, code="RDL",
             name_fr="Railway Development Levy",
             name_en="Railway Development Levy",
             rate_pct=1.5, basis=DutyBasis.CIF, sequence=30,
             legal_reference="Railways Act (Tanzanie), levy sur importations "
                             "mises à la consommation",
             observation=VERIFY_NOTE),
    ],
    "UGA": [
        dict(measure_type=MeasureType.LEVY, code="INFRA",
             name_fr="Infrastructure Levy",
             name_en="Infrastructure Levy",
             rate_pct=1.5, basis=DutyBasis.CIF, sequence=30,
             legal_reference="EAC infrastructure levy — loi de finances Ouganda",
             observation=VERIFY_NOTE),
    ],
    "RWA": [
        dict(measure_type=MeasureType.LEVY, code="IDL",
             name_fr="Infrastructure Development Levy",
             name_en="Infrastructure Development Levy",
             rate_pct=1.5, basis=DutyBasis.CIF, sequence=30,
             legal_reference="Law on Infrastructure Development Levy (Rwanda)",
             observation=VERIFY_NOTE),
        dict(measure_type=MeasureType.LEVY, code="AUL",
             name_fr="Prélèvement Union Africaine",
             name_en="African Union Import Levy",
             rate_pct=0.2, basis=DutyBasis.CIF, sequence=31,
             legal_reference="Décision UA Kigali 2016 — mise en œuvre Rwanda",
             observation=VERIFY_NOTE),
    ],
}

# ----------------------------------------------------------------------
# Détection souple des colonnes du CSV source
# ----------------------------------------------------------------------

def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]", "", s.lower())


COLUMN_ALIASES = {
    "code": {"codesh", "code", "hscode", "tariffcode"},
    "description": {"designation", "description", "libelle"},
    "rate": {"dd", "rate", "dutyrate", "taux"},
    "unit": {"unite", "unit", "su"},
    "specific": {"ddspecifique", "specific", "specificamount"},
    "specific_unit": {"dduniteSpecifique".lower(), "specificunit"},
    "sensitive": {"sensible", "sensitive", "si"},
    "raw": {"tauxbrut", "rawrate"},
}


def _detect_columns(fieldnames: List[str]) -> Dict[str, str]:
    mapping = {}
    for field in fieldnames or []:
        n = _norm(field)
        for role, aliases in COLUMN_ALIASES.items():
            if role not in mapping and n in aliases:
                mapping[role] = field
    missing = {"code", "description", "rate"} - set(mapping)
    if missing:
        raise ValueError(
            f"Colonnes introuvables dans le CSV CET: {sorted(missing)} "
            f"(en-têtes vus: {fieldnames})")
    return mapping


# ----------------------------------------------------------------------
# Adaptateur
# ----------------------------------------------------------------------

class EacCetAdapter:
    """Parse l'EAC CET 2022 (CSV) et émet les lignes canoniques v4 par pays."""

    SOURCE_NAME = ("EAC CET 2022 Version — Common External Tariff "
                   "(EAC Gazette, Annexe 1 au Protocole d'Union Douanière)")
    SOURCE_URL = ("https://www.kra.go.ke/images/publications/"
                  "EAC-CET-2022-VERSION-30TH-JUNE-Fn.pdf")

    def __init__(self, source_path: str, version_date: Optional[date] = None,
                 hs_version: str = "HS2022"):
        self.source_path = Path(source_path)
        self.version_date = version_date or date(2022, 7, 1)
        self.hs_version = hs_version
        self.stats = {"source_lines": 0, "skipped": 0, "out_of_band": 0}
        self._rows: Optional[List[dict]] = None

    # ------------------------------------------------------------------
    def provenance(self, country: str) -> Provenance:
        notes = ("Droits de douane issus du CET communautaire officiel "
                 "(4 bandes 0/10/25/35 % + produits sensibles Schedule 2) ; "
                 "taxes intérieures (TVA, prélèvements nationaux) issues des "
                 "taux standards documentés — à recouper avec la loi de "
                 "finances et le tarif intégré national de chaque État.")
        if country in TRANSITION_NOTE:
            notes = TRANSITION_NOTE[country] + " | " + notes
        return Provenance(
            data_status=DataStatus.PARTIAL,
            reliability=ReliabilityGrade.B,
            source_name=self.SOURCE_NAME,
            source_url=self.SOURCE_URL,
            source_document=self.source_path.name,
            version_date=self.version_date,
            retrieved_at=datetime.now(),
            notes=notes,
        )

    # ------------------------------------------------------------------
    def parse_source(self) -> List[dict]:
        if self._rows is not None:
            return self._rows

        raw = self.source_path.read_text(encoding="utf-8-sig")
        reader = csv.DictReader(io.StringIO(raw), delimiter=";")
        cols = _detect_columns(reader.fieldnames)

        def _f(row, key) -> Optional[float]:
            if key not in cols:
                return None
            val = (row.get(cols[key]) or "").replace(",", ".").strip()
            try:
                return float(val) if val else None
            except ValueError:
                return None

        rows = []
        for row in reader:
            code = re.sub(r"[\s.]", "", row.get(cols["code"], "") or "")
            rate = _f(row, "rate")
            if not re.fullmatch(r"\d{8}", code) or rate is None:
                self.stats["skipped"] += 1
                continue
            sensitive = (row.get(cols["sensitive"], "") or "") == "1" \
                if "sensitive" in cols else False
            if rate not in CET_BANDS and not sensitive:
                self.stats["out_of_band"] += 1
            rows.append({
                "code": code,
                "description": row.get(cols["description"], ""),
                "rate": rate,
                "unit": row.get(cols["unit"], "") if "unit" in cols else None,
                "specific": _f(row, "specific"),
                "specific_unit": row.get(cols["specific_unit"], "") or None
                                 if "specific_unit" in cols else None,
                "sensitive": sensitive,
                "raw": row.get(cols["raw"], "") if "raw" in cols else "",
            })
            self.stats["source_lines"] += 1

        self._rows = rows
        return rows

    # ------------------------------------------------------------------
    def transform(self, country_iso3: str) -> Generator[CanonicalTariffLine, None, None]:
        country = country_iso3.upper()
        if country not in COUNTRIES:
            raise ValueError(f"{country} n'est pas membre de l'EAC")
        prov = self.provenance(country)
        for row in self.parse_source():
            yield self._line(country, row, prov)

    # ------------------------------------------------------------------
    def _line(self, country: str, row: dict, prov: Provenance) -> CanonicalTariffLine:
        code = row["code"]
        commodity = CommodityCode(
            country_iso3=country,
            national_code=code,
            hs6=code[:6],
            digits=len(code),
            description_fr=row["description"],
            description_official_fr=row["description"],
            description_en=row["description"],
            chapter=code[:2],
            category="CET-SENSIBLE" if row["sensitive"] else None,
            unit=row["unit"] or None,
            sensitivity="sensible" if row["sensitive"] else "normal",
            hs_version=self.hs_version,
        )

        measures = self._measures(country, row)
        advantages = self._advantages(country, code)
        total_npf = sum(m.rate_pct or 0 for m in measures)

        return CanonicalTariffLine(
            commodity=commodity,
            measures=measures,
            fiscal_advantages=advantages,
            total_npf_pct=round(total_npf, 2),
            source_file=str(self.source_path),
            last_updated=datetime.now(),
            schema_version=SCHEMA_VERSION,
            provenance=prov,
        )

    # ------------------------------------------------------------------
    def _measures(self, country: str, row: dict) -> List[Measure]:
        code, dd_rate = row["code"], row["rate"]
        measures: List[Measure] = []

        def add(**kw):
            defaults = dict(country_iso3=country, national_code=code,
                            rate_type=RateType.AD_VALOREM, basis=DutyBasis.CIF)
            defaults.update(kw)
            if defaults.get("rate_type") == RateType.AD_VALOREM \
                    and defaults.get("rate_pct") in (None, 0.0):
                defaults["rate_type"] = RateType.EXEMPT
            measures.append(Measure(**defaults))

        # 10 — Droit de douane CET (mixte pour certains produits sensibles :
        # « le plus élevé » du taux ad valorem ou du montant spécifique)
        dd_kw = dict(measure_type=MeasureType.CUSTOMS_DUTY, code="D.D",
                     name_fr="Droit de Douane (CET EAC)",
                     name_en="Customs Duty (EAC CET)",
                     rate_pct=dd_rate, sequence=10,
                     is_zlecaf_applicable=True,
                     legal_reference="EAC CET 2022 — Legal Notice, en vigueur "
                                     "au 01/07/2022 (EAC Gazette)")
        if row["specific"] is not None:
            dd_kw.update(rate_type=RateType.ALTERNATIVE,
                         specific_amount=row["specific"],
                         specific_unit=row["specific_unit"],
                         observation=f"Taux alternatif : appliquer le plus élevé "
                                     f"des deux — « {row['raw']} »")
        elif row["sensitive"]:
            dd_kw.update(observation="Produit sensible (Schedule 2 du CET)")
        add(**dd_kw)

        # 30+ — prélèvements nationaux documentés
        for extra in EXTRA_NATIONAL.get(country, []):
            add(**extra)

        # 90 — TVA (uniquement si taux standard documenté pour le pays)
        if country in VAT_BY_COUNTRY:
            vat_code, vat_fr, vat_en, vat_rate = VAT_BY_COUNTRY[country]
            upstream = [m.code for m in measures
                        if m.basis in (DutyBasis.CIF, DutyBasis.CUSTOMS_VALUE,
                                       DutyBasis.CIF_PLUS_INCLUDED)]
            add(measure_type=MeasureType.VAT, code=vat_code,
                name_fr=vat_fr, name_en=vat_en,
                rate_pct=vat_rate, sequence=90,
                basis=DutyBasis.CIF_PLUS_INCLUDED, basis_includes=upstream,
                observation=VERIFY_NOTE +
                " ; assiette = CAF + droits et taxes en amont (hors TVA)")

        return measures

    # ------------------------------------------------------------------
    def _advantages(self, country: str, code: str) -> List[FiscalAdvantage]:
        return [
            FiscalAdvantage(
                country_iso3=country, national_code=code,
                tax_code="D.D", reduced_rate_pct=0.0,
                condition_fr="Origine communautaire EAC — franchise de droits "
                             "au sein de l'Union douanière, certificat "
                             "d'origine EAC à l'appui",
                agreement="EAC",
                required_document="Certificat d'origine EAC",
            ),
            FiscalAdvantage(
                country_iso3=country, national_code=code,
                tax_code="D.D", reduced_rate_pct=0.0,
                condition_fr="Origine d'un État partie ZLECAf — taux et "
                             "calendrier selon la liste de concessions "
                             "tarifaires du pays importateur (catégories "
                             "A/B/C), certificat d'origine ZLECAf à l'appui",
                agreement="ZLECAf",
                required_document="Certificat d'origine ZLECAf",
            ),
        ]

    # ------------------------------------------------------------------
    def get_summary(self, country_iso3: str) -> dict:
        return {
            "country_iso3": country_iso3.upper(),
            "adapter": "eac_cet_adapter",
            "adapter_version": "1.0",
            "source": self.SOURCE_NAME,
            "total_tariff_lines": self.stats["source_lines"],
            "data_status": DataStatus.PARTIAL.value,
            "reliability": ReliabilityGrade.B.value,
            "schema_version": SCHEMA_VERSION,
            "generated_at": datetime.now().isoformat(),
        }


# ----------------------------------------------------------------------
def run(source: str, output_dir: str, countries: Optional[List[str]] = None,
        version_date: Optional[str] = None) -> dict:
    """Exécute l'adaptateur : un JSONL canonique par pays membre."""
    vd = date.fromisoformat(version_date) if version_date else None
    adapter = EacCetAdapter(source, version_date=vd)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    targets = [c.upper() for c in (countries or COUNTRIES)]
    written = {}
    for iso3 in targets:
        out_file = out_dir / f"{iso3}_canonical.jsonl"
        n = 0
        with out_file.open("w", encoding="utf-8") as f:
            for line in adapter.transform(iso3):
                f.write(line.model_dump_json(exclude_none=False) + "\n")
                n += 1
        written[iso3] = n

    return {"countries": written, **adapter.stats}


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("source", help="CSV de l'EAC CET (sortie de eac_cet_md_to_csv.py)")
    ap.add_argument("output_dir", help="Répertoire de sortie des JSONL canoniques")
    ap.add_argument("--countries", nargs="*", default=None,
                    help="Sous-ensemble de pays ISO3 (défaut: les 8 membres)")
    ap.add_argument("--version-date", default=None,
                    help="Millésime du CET (YYYY-MM-DD, défaut 2022-07-01)")
    args = ap.parse_args()
    stats = run(args.source, args.output_dir, args.countries, args.version_date)
    print(f"EAC CET -> {args.output_dir}")
    print(f"  lignes source: {stats['source_lines']} | ignorées: {stats['skipped']} "
          f"| hors bande (non sensibles): {stats['out_of_band']}")
    for iso3, n in stats["countries"].items():
        print(f"  {iso3}: {n} lignes canoniques")

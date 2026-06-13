"""
Adaptateur TEC CEDEAO — Tarif Extérieur Commun (15 pays, vague 1)
==================================================================

Une seule collecte du TEC publié par la Commission de la CEDEAO débloque les
15 États membres pour la couche droits de douane (codes à 8 ou 10 chiffres).

Entrée  : export CSV du TEC (délimiteur ';' ou ',', en-têtes FR ou EN —
          détection automatique des colonnes code / désignation / catégorie /
          taux DD / unité). Le fichier source officiel (Excel) est à déposer
          dans engine/sources/ puis à exporter en CSV — voir
          engine/sources/README_sources.md.
Sortie  : un JSONL canonique v4 PAR PAYS ({ISO3}_canonical.jsonl).

Statut de provenance émis : PARTIAL / fiabilité B.
  Le TEC est un texte communautaire officiel, mais il ne constitue pas le
  tarif intégré national : les taxes intérieures (TVA, prélèvements) et les
  formalités restent à vérifier pays par pays contre la loi de finances et
  le code des douanes nationaux. Chaque mesure nationale ajoutée ici porte
  une observation explicite "à confirmer".

Bandes tarifaires du TEC (5 catégories) :
  0 →  0 %   Biens sociaux essentiels
  1 →  5 %   Biens de première nécessité, matières premières, biens d'équipement
  2 → 10 %   Intrants et produits intermédiaires
  3 → 20 %   Biens de consommation finale
  4 → 35 %   Biens spécifiques pour le développement économique

Séquence de calcul implémentée (harmonisation UEMOA/CEDEAO) :
  10  D.D        Droit de Douane (TEC)                  → sur valeur CAF
  20  R.S        Redevance Statistique (UEMOA, 1 %)     → sur valeur CAF
  25  PC-CEDEAO  Prélèvement Communautaire CEDEAO 0,5 % → sur valeur CAF
  26  PCS-UEMOA  Prélèvement Communautaire de Solidarité → sur valeur CAF
  27  PUA        Prélèvement Union Africaine 0,2 % (UA) → sur valeur CAF
  30+ taxes nationales spécifiques (NGA, GHA…)          → voir registre
  90  TVA/VAT    → sur CAF + droits et taxes en amont (hors TVA)
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
# Référentiels CEDEAO
# ----------------------------------------------------------------------

COUNTRIES = [
    "BEN", "BFA", "CIV", "CPV", "GHA", "GIN", "GMB", "GNB",
    "LBR", "MLI", "NER", "NGA", "SEN", "SLE", "TGO",
]

UEMOA = {"BEN", "BFA", "CIV", "GNB", "MLI", "NER", "SEN", "TGO"}

CET_BANDS = {0: 0.0, 1: 5.0, 2: 10.0, 3: 20.0, 4: 35.0}

VERIFY_NOTE = ("Taxe nationale hors TEC — taux standard usuel, à confirmer "
               "contre la loi de finances en vigueur du pays")

# TVA / taxe générale sur la consommation par pays (taux standard usuels).
# Format : (code, intitulé FR, intitulé EN, taux %)
VAT_BY_COUNTRY: Dict[str, tuple] = {
    "BEN": ("T.V.A", "Taxe sur la Valeur Ajoutée", "Value Added Tax", 18.0),
    "BFA": ("T.V.A", "Taxe sur la Valeur Ajoutée", "Value Added Tax", 18.0),
    "CIV": ("T.V.A", "Taxe sur la Valeur Ajoutée", "Value Added Tax", 18.0),
    "CPV": ("IVA",   "Imposto sobre o Valor Acrescentado", "Value Added Tax", 15.0),
    "GHA": ("VAT",   "Taxe sur la Valeur Ajoutée", "Value Added Tax", 15.0),
    "GIN": ("T.V.A", "Taxe sur la Valeur Ajoutée", "Value Added Tax", 18.0),
    "GMB": ("VAT",   "Taxe sur la Valeur Ajoutée", "Value Added Tax", 15.0),
    "GNB": ("IGV",   "Imposto Geral sobre Vendas", "General Sales Tax", 19.0),
    "LBR": ("GST",   "Taxe sur les Biens et Services", "Goods and Services Tax", 10.0),
    "MLI": ("T.V.A", "Taxe sur la Valeur Ajoutée", "Value Added Tax", 18.0),
    "NER": ("T.V.A", "Taxe sur la Valeur Ajoutée", "Value Added Tax", 19.0),
    "NGA": ("VAT",   "Taxe sur la Valeur Ajoutée", "Value Added Tax", 7.5),
    "SEN": ("T.V.A", "Taxe sur la Valeur Ajoutée", "Value Added Tax", 18.0),
    "SLE": ("GST",   "Taxe sur les Biens et Services", "Goods and Services Tax", 15.0),
    "TGO": ("T.V.A", "Taxe sur la Valeur Ajoutée", "Value Added Tax", 18.0),
}

# Taxes nationales spécifiques documentées, en sus des prélèvements
# communautaires. Chaque entrée : dict prêt pour Measure (sans pays/code SH).
EXTRA_NATIONAL: Dict[str, List[dict]] = {
    "NGA": [
        dict(measure_type=MeasureType.OTHER_TAX, code="CISS",
             name_fr="Comprehensive Import Supervision Scheme",
             name_en="Comprehensive Import Supervision Scheme",
             rate_pct=1.0, basis=DutyBasis.FOB, sequence=30,
             observation=VERIFY_NOTE + " (assiette FOB)"),
    ],
    "GHA": [
        dict(measure_type=MeasureType.LEVY, code="NHIL",
             name_fr="National Health Insurance Levy",
             name_en="National Health Insurance Levy",
             rate_pct=2.5, basis=DutyBasis.CIF_PLUS_INCLUDED,
             basis_includes=["D.D"], sequence=30,
             observation=VERIFY_NOTE),
        dict(measure_type=MeasureType.LEVY, code="GETFund",
             name_fr="Ghana Education Trust Fund Levy",
             name_en="Ghana Education Trust Fund Levy",
             rate_pct=2.5, basis=DutyBasis.CIF_PLUS_INCLUDED,
             basis_includes=["D.D"], sequence=31,
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
    "code": {"code", "codesh", "codesh10", "codesh8", "hscode", "nts",
             "ntscode", "tariffcode", "codetarifaire", "position"},
    "description": {"designation", "designationcomplete", "description",
                    "descriptionofgoods", "libelle", "produit"},
    "category": {"categorie", "category", "cat", "band", "bande"},
    "rate": {"dd", "taux", "tauxdd", "duty", "dutyrate", "importduty",
             "droitdedouane", "ddpct", "rate"},
    "unit": {"unite", "unit", "su", "uniteStatistique".lower(), "us",
             "statisticalunit"},
    # Colonnes optionnelles — CSV enrichi (douanes.ci)
    "tva": {"tva", "vat", "taxevaleurajoutee"},
    "tsb": {"tsb", "taxespecifique", "specifictax"},
    "psv": {"psv"},
}


def _detect_columns(fieldnames: List[str]) -> Dict[str, str]:
    """Associe chaque rôle (code, description…) au nom de colonne du CSV."""
    mapping = {}
    for field in fieldnames or []:
        n = _norm(field)
        for role, aliases in COLUMN_ALIASES.items():
            if role not in mapping and n in aliases:
                mapping[role] = field
    missing = {"code", "description"} - set(mapping)
    if missing:
        raise ValueError(
            f"Colonnes introuvables dans le CSV TEC: {sorted(missing)} "
            f"(en-têtes vus: {fieldnames})")
    if "category" not in mapping and "rate" not in mapping:
        raise ValueError(
            "Le CSV TEC doit contenir une colonne 'Catégorie' (bande 0-4) "
            "ou une colonne de taux DD")
    return mapping


def _sniff_delimiter(sample: str) -> str:
    return ";" if sample.count(";") >= sample.count(",") else ","


# ----------------------------------------------------------------------
# Adaptateur
# ----------------------------------------------------------------------

class CedeaoTecAdapter:
    """Parse le TEC CEDEAO (CSV) et émet les lignes canoniques v4 par pays."""

    SOURCE_NAME = "TEC CEDEAO — Tarif Extérieur Commun (Commission CEDEAO)"
    SOURCE_URL = "https://www.douanes.ci/info/tec"

    def __init__(self, source_path: str, version_date: Optional[date] = None,
                 hs_version: str = "HS2022"):
        self.source_path = Path(source_path)
        self.version_date = version_date
        self.hs_version = hs_version
        self.stats = {"source_lines": 0, "skipped": 0, "band_mismatch": 0}
        self._rows: Optional[List[dict]] = None

    # ------------------------------------------------------------------
    def provenance(self) -> Provenance:
        return Provenance(
            data_status=DataStatus.PARTIAL,
            reliability=ReliabilityGrade.B,
            source_name=self.SOURCE_NAME,
            source_url=self.SOURCE_URL,
            source_document=self.source_path.name,
            version_date=self.version_date,
            retrieved_at=datetime.now(),
            notes="Droits de douane issus du TEC communautaire officiel ; "
                  "taxes intérieures (TVA, prélèvements nationaux) issues des "
                  "taux standards usuels — à recouper avec la loi de finances "
                  "et le tarif intégré national de chaque État membre.",
        )

    # ------------------------------------------------------------------
    def parse_source(self) -> List[dict]:
        """Parse le CSV une seule fois ; retourne les lignes normalisées."""
        if self._rows is not None:
            return self._rows

        raw = self.source_path.read_text(encoding="utf-8-sig")
        delim = _sniff_delimiter(raw.splitlines()[0] if raw else "")
        reader = csv.DictReader(io.StringIO(raw), delimiter=delim)
        cols = _detect_columns(reader.fieldnames)

        rows = []
        for row in reader:
            row = {k: (v or "").strip() for k, v in row.items() if k}
            code = re.sub(r"[\s.]", "", row.get(cols["code"], ""))
            if not re.fullmatch(r"\d{8}|\d{10}", code):
                self.stats["skipped"] += 1
                continue

            category = None
            if "category" in cols:
                m = re.search(r"\d", row.get(cols["category"], ""))
                category = int(m.group()) if m else None

            rate = None
            if "rate" in cols:
                val = row.get(cols["rate"], "").replace(",", ".").rstrip("% ")
                rate = float(val) if val else None

            if rate is None and category is not None:
                rate = CET_BANDS.get(category)
            if rate is None:
                self.stats["skipped"] += 1
                continue
            if category is not None and CET_BANDS.get(category) not in (None, rate):
                self.stats["band_mismatch"] += 1

            def _opt_float(col_key: str) -> Optional[float]:
                if col_key not in cols:
                    return None
                val = row.get(cols[col_key], "").replace(",", ".").rstrip("% ")
                try:
                    return float(val) if val else None
                except ValueError:
                    return None

            rows.append({
                "code": code,
                "description": row.get(cols["description"], ""),
                "category": category,
                "rate": rate,
                "unit": row.get(cols["unit"], "") if "unit" in cols else None,
                "tva_override": _opt_float("tva"),
                "tsb": _opt_float("tsb"),
                "psv": _opt_float("psv"),
            })
            self.stats["source_lines"] += 1

        self._rows = rows
        return rows

    # ------------------------------------------------------------------
    def transform(self, country_iso3: str) -> Generator[CanonicalTariffLine, None, None]:
        country = country_iso3.upper()
        if country not in COUNTRIES:
            raise ValueError(f"{country} n'est pas membre de la CEDEAO")
        prov = self.provenance()
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
            chapter=code[:2],
            category=f"TEC-{row['category']}" if row["category"] is not None else None,
            unit=row["unit"] or None,
            hs_version=self.hs_version,
        )

        measures = self._measures(country, code, row["rate"],
                                  tva_override=row.get("tva_override"),
                                  tsb=row.get("tsb"),
                                  psv=row.get("psv"))
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
    def _measures(self, country: str, code: str, dd_rate: float,
                  tva_override: Optional[float] = None,
                  tsb: Optional[float] = None,
                  psv: Optional[float] = None) -> List[Measure]:
        measures: List[Measure] = []

        def add(**kw):
            defaults = dict(country_iso3=country, national_code=code,
                            rate_type=RateType.AD_VALOREM, basis=DutyBasis.CIF)
            defaults.update(kw)
            if defaults.get("rate_pct") in (None, 0.0):
                defaults["rate_type"] = RateType.EXEMPT
            measures.append(Measure(**defaults))

        # 10 — Droit de douane TEC
        add(measure_type=MeasureType.CUSTOMS_DUTY, code="D.D",
            name_fr="Droit de Douane (TEC CEDEAO)",
            name_en="Customs Duty (ECOWAS CET)",
            rate_pct=dd_rate, sequence=10,
            is_zlecaf_applicable=True,
            legal_reference="TEC CEDEAO — édition SH 2022")

        # 20 — Redevance statistique (UEMOA harmonisée à 1 %)
        if country in UEMOA:
            add(measure_type=MeasureType.OTHER_TAX, code="R.S",
                name_fr="Redevance Statistique",
                name_en="Statistical Fee",
                rate_pct=1.0, sequence=20,
                legal_reference="Redevance statistique harmonisée UEMOA",
                observation=VERIFY_NOTE)

        # 25 — Prélèvement communautaire CEDEAO (tous membres)
        add(measure_type=MeasureType.LEVY, code="PC-CEDEAO",
            name_fr="Prélèvement Communautaire CEDEAO",
            name_en="ECOWAS Community Levy",
            rate_pct=0.5, sequence=25,
            legal_reference="Protocole A/P1/7/96 CEDEAO",
            observation="Applicable aux importations originaires de pays "
                        "tiers ; exonéré pour les marchandises d'origine "
                        "communautaire (SLEC)")

        # 26 — Prélèvement communautaire de solidarité (UEMOA uniquement)
        if country in UEMOA:
            add(measure_type=MeasureType.LEVY, code="PCS-UEMOA",
                name_fr="Prélèvement Communautaire de Solidarité",
                name_en="UEMOA Community Solidarity Levy",
                rate_pct=0.8, sequence=26,
                legal_reference="Acte additionnel UEMOA (taux porté de "
                                "0,5 % à 0,8 % en 2017)",
                observation=VERIFY_NOTE)

        # 27 — Prélèvement Union Africaine (tous membres, Décision UA Kigali 2016)
        add(measure_type=MeasureType.LEVY, code="PUA",
            name_fr="Prélèvement Union Africaine",
            name_en="African Union Import Levy",
            rate_pct=0.2, sequence=27,
            legal_reference="Décision UA Kigali 2016 — financement de l'UA",
            observation=VERIFY_NOTE)

        # 30+ — droits spécifiques documentés dans le CSV enrichi
        if tsb is not None:
            measures.append(Measure(
                country_iso3=country, national_code=code,
                measure_type=MeasureType.OTHER_TAX, code="TSB",
                name_fr="Taxe Spécifique sur les Boissons",
                name_en="Specific Tax on Beverages",
                rate_type=RateType.SPECIFIC, specific_amount=tsb,
                basis=DutyBasis.CIF, sequence=35,
                observation=VERIFY_NOTE + " (montant FCFA/unité)"))
        if psv is not None:
            measures.append(Measure(
                country_iso3=country, national_code=code,
                measure_type=MeasureType.OTHER_TAX, code="PSV",
                name_fr="Prélèvement Spécifique (viandes/volailles)",
                name_en="Specific Levy on Meat/Poultry",
                rate_type=RateType.SPECIFIC, specific_amount=psv,
                basis=DutyBasis.CIF, sequence=36,
                observation=VERIFY_NOTE + " (montant FCFA/unité)"))

        # 30+ — taxes nationales spécifiques documentées
        for extra in EXTRA_NATIONAL.get(country, []):
            add(**extra)

        # 90 — TVA / taxe générale sur la consommation
        vat_code, vat_fr, vat_en, vat_rate = VAT_BY_COUNTRY[country]
        if tva_override is not None:
            vat_rate = tva_override
        upstream = [m.code for m in measures
                    if m.basis in (DutyBasis.CIF, DutyBasis.CIF_PLUS_INCLUDED)]
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
                condition_fr="Origine communautaire CEDEAO sous le Schéma de "
                             "Libéralisation des Échanges (SLEC), certificat "
                             "d'origine CEDEAO à l'appui",
                agreement="CEDEAO/SLEC",
                required_document="Certificat d'origine CEDEAO",
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
            "adapter": "cedeao_tec_adapter",
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
    adapter = CedeaoTecAdapter(source, version_date=vd)
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
    ap.add_argument("source", help="CSV du TEC CEDEAO (export du fichier officiel)")
    ap.add_argument("output_dir", help="Répertoire de sortie des JSONL canoniques")
    ap.add_argument("--countries", nargs="*", default=None,
                    help="Sous-ensemble de pays ISO3 (défaut: les 15 membres)")
    ap.add_argument("--version-date", default=None,
                    help="Millésime du TEC (YYYY-MM-DD)")
    args = ap.parse_args()
    stats = run(args.source, args.output_dir, args.countries, args.version_date)
    print(f"TEC CEDEAO -> {args.output_dir}")
    print(f"  lignes source: {stats['source_lines']} | ignorées: {stats['skipped']} "
          f"| incohérences bande/taux: {stats['band_mismatch']}")
    for iso3, n in stats["countries"].items():
        print(f"  {iso3}: {n} lignes canoniques")

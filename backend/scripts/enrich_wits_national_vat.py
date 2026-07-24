"""
Enrichissement TVA nationale — les 13 pays sourcés via WITS/TRAINS.

WITS/TRAINS ne publie que le droit de douane MFN au niveau SH6, sans couche
nationale (cf. wits_source.py). Ce script ajoute le taux de TVA (ou taxes
d'importation équivalentes) national standard, sourcé individuellement pour
chaque pays (recherche documentée le 2026-07-05, sources citées ci-dessous).

Limite assumée (pas de fabrication) : c'est le taux STANDARD national, pas une
donnée vérifiée position par position — un futur crawl national ou WITS
préférentiel resterait plus précis. Le champ "note" sur chaque taxe le dit
explicitement.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

CRAWLED_DIR = Path(__file__).parent.parent / "data" / "crawled"

NOTE_STANDARD = (
    "Taux national standard (non vérifié position par position — WITS/TRAINS "
    "ne couvre que le droit de douane MFN SH6)."
)


class NationalTax:
    def __init__(
        self,
        code: str,
        name: str,
        rate: float,
        source: str,
        source_url: str,
        as_of: str,
        reduced_rates: str = "",
    ):
        self.code = code
        self.name = name
        self.rate = rate
        self.source = source
        self.source_url = source_url
        self.as_of = as_of
        # Texte libre, sourcé, décrivant les taux réduits/exonérations connus —
        # PAS une correspondance HS précise (non disponible sans couche
        # nationale) : on documente l'exception plutôt que de deviner à quelles
        # positions SH elle s'applique exactement.
        self.reduced_rates = reduced_rates

    def to_entry(self) -> Dict:
        note = NOTE_STANDARD
        if self.reduced_rates:
            note += f" Taux dérogatoires connus (non appliqués ici, à vérifier par produit) : {self.reduced_rates}"
        return {
            "name": self.name,
            "rate": self.rate,
            "raw": f"{self.rate} %",
            "source": self.source,
            "source_url": self.source_url,
            "as_of": self.as_of,
            "note": note,
        }


# Chaque pays -> liste de taxes nationales à ajouter (hors DD, déjà présent).
# Recherché et sourcé individuellement (voir PR) ; LBY n'a pas de TVA.
NATIONAL_TAXES: Dict[str, List[NationalTax]] = {
    "AGO": [
        NationalTax(
            "IVA",
            "Imposto sobre o Valor Acrescentado (IVA)",
            14.0,
            "PwC Worldwide Tax Summaries — Angola",
            "https://taxsummaries.pwc.com/angola/corporate/other-taxes",
            "2026",
            reduced_rates=(
                "7 % (régime simplifié, CA 10M-350M Kwanzas ; alimentation dès 2026), "
                "5 % (équipement industriel à usage productif), exonéré (CA < 10M Kwanzas)."
            ),
        )
    ],
    "COM": [
        NationalTax(
            "TVA",
            "Taxe sur la Valeur Ajoutée (TVA)",
            10.0,
            "Société Générale International Trade Portal — Comoros Taxation",
            "https://import-export.societegenerale.fr/en/country/comoros/presentation-taxation",
            "2026",
            reduced_rates=(
                "3 % (eau, frais de scolarité privée, transport aérien inter-îles), "
                "5 % (restauration, banque, transport international), "
                "7,5 % (téléphonie mobile), 25 % (casinos)."
            ),
        )
    ],
    "LBY": [
        NationalTax(
            "TSP",
            "Port Services Tax (taxe des services portuaires)",
            4.0,
            "PwC Worldwide Tax Summaries — Libya",
            "https://taxsummaries.pwc.com/libya/corporate/other-taxes",
            "2026",
        ),
        NationalTax(
            "TP",
            "Production Tax (taxe de production)",
            2.0,
            "PwC Worldwide Tax Summaries — Libya",
            "https://taxsummaries.pwc.com/libya/corporate/other-taxes",
            "2026",
        ),
    ],
    "MDG": [
        NationalTax(
            "TVA",
            "Taxe sur la Valeur Ajoutée (TVA)",
            20.0,
            "PwC Worldwide Tax Summaries — Madagascar / Loi n° 2025-021 (Loi de Finances 2026)",
            "https://taxsummaries.pwc.com/madagascar/corporate/other-taxes",
            "2026",
            reduced_rates="10 % (gaz butane), 0 % (exportations).",
        )
    ],
    "MOZ": [
        NationalTax(
            "IVA",
            "Imposto sobre o Valor Acrescentado (IVA)",
            16.0,
            "PwC Worldwide Tax Summaries — Mozambique",
            "https://taxsummaries.pwc.com/mozambique/corporate/other-taxes",
            "2026 (taux en vigueur depuis le 2024-01-01)",
            reduced_rates="5 % (santé privée, éducation — services, hors marchandises importées).",
        )
    ],
    "MRT": [
        NationalTax(
            "TVA",
            "Taxe sur la Valeur Ajoutée (TVA)",
            16.0,
            "Direction Générale des Impôts (Mauritanie)",
            "https://impots.gov.mr/DGI/files/doctrine/Livre2-Titre1-TVA-20191010.pdf",
            "2026 (taux en vigueur depuis 2017)",
        )
    ],
    "MUS": [
        NationalTax(
            "VAT",
            "Value Added Tax (VAT)",
            15.0,
            "Mauritius Revenue Authority / PwC Worldwide Tax Summaries",
            "https://www.mra.mu/26-vat",
            "2026",
        )
    ],
    "MWI": [
        NationalTax(
            "VAT",
            "Value Added Tax (VAT)",
            17.5,
            "Malawi Revenue Authority — Public Notice (New Tax Measures)",
            "https://www.mra.mw",
            "2026-01-01 (relevé de 16.5 % à 17.5 %)",
        )
    ],
    "SDN": [
        NationalTax(
            "VAT",
            "Value Added Tax (VAT)",
            17.0,
            "Trading Economics / CEIC Data (Sudan Sales Tax Rate) — source primaire non "
            "vérifiable (Chambre des impôts indisponible depuis le conflit de 2023)",
            "https://tradingeconomics.com/sudan/sales-tax-rate",
            "2026 (fiabilité moyenne — administration fiscale perturbée)",
        )
    ],
    "STP": [
        NationalTax(
            "IVA",
            "Imposto sobre o Valor Acrescentado (IVA)",
            15.0,
            "Lei n.º 02/2023 de 31 de maio (Código do IVA)",
            "https://www.mirandalawfirm.com/pt/conhecimento-media/publications/alerts/entrada-em-vigor-do-codigo-do-iva-em-stp-2",
            "2026 (en vigueur depuis le 2023-06-01)",
            reduced_rates=(
                "7,5 % (panier de base — riz, farine, pâtes, pain, lait, haricots ; "
                "Annexe I du Code de la TVA), 0 % (exportations)."
            ),
        )
    ],
    "SYC": [
        NationalTax(
            "VAT",
            "Value Added Tax (VAT)",
            15.0,
            "Seychelles Revenue Commission / IMF Country Report No. 25/147",
            "https://src.gov.sc/seychelles-tax-system/",
            "2026",
        )
    ],
    "ZMB": [
        NationalTax(
            "VAT",
            "Value Added Tax (VAT)",
            16.0,
            "Zambia Revenue Authority / PwC Worldwide Tax Summaries",
            "https://www.zra.org.zm/tax-information/",
            "2026",
        )
    ],
    "ZWE": [
        NationalTax(
            "VAT",
            "Value Added Tax (VAT)",
            15.5,
            "ZIMRA Public Notice 07 of 2026",
            "https://www.zimra.co.zw",
            "2026-01-01 (relevé de 15 % à 15.5 %)",
        )
    ],
}


def enrich_country(iso3: str, taxes_to_add: List[NationalTax]) -> Optional[int]:
    path = CRAWLED_DIR / f"{iso3}_tariffs.json"
    if not path.exists():
        print(f"[{iso3}] fichier introuvable : {path}")
        return None

    data = json.loads(path.read_text(encoding="utf-8"))
    positions = data.get("sub_positions", [])
    if not positions:
        print(f"[{iso3}] aucune position — rien à enrichir.")
        return None

    codes_added = [t.code for t in taxes_to_add]
    for pos in positions:
        taxes = pos.setdefault("taxes", {})
        for t in taxes_to_add:
            taxes[t.code] = t.to_entry()

    rules = data.setdefault("calculation_rules", {"order": ["DD"], "bases": {}})
    order = rules.setdefault("order", ["DD"])
    for code in codes_added:
        if code not in order:
            order.append(code)
    rules["source"] = (
        "MFN appliqué SH6 (WITS/TRAINS) + TVA/taxes nationales standard "
        f"({', '.join(codes_added)}) sourcées individuellement — voir taxes[].source "
        "par position. Formalités et avantages fiscaux par position non couverts."
    )

    data["source_quality"] = "crawled_authentic_partial_national"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[{iso3}] {len(positions)} positions enrichies ({', '.join(codes_added)}).")
    return len(positions)


def main():
    total = 0
    for iso3, taxes in NATIONAL_TAXES.items():
        n = enrich_country(iso3, taxes)
        if n:
            total += n
    print(f"\nTotal : {total} positions enrichies sur {len(NATIONAL_TAXES)} pays.")


if __name__ == "__main__":
    main()

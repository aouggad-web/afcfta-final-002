"""
Surcharges de TVA par produit — 13 pays WITS, phase 2 (après enrich_wits_national_vat.py).

Chaque texte de loi TVA national indique soit un PRODUIT (nom ou, plus
rarement, code SH), soit une DESTINATION FINALE (usage industriel,
exportation...) pour justifier un taux dérogatoire. Ce script applique le
taux dérogatoire aux positions SH concernées, UNIQUEMENT quand la
correspondance HS6 est raisonnablement non ambiguë (le code SH6 couvre
essentiellement le produit nommé, pas une catégorie plus large qui
inclurait des articles non visés par la loi).

Deux niveaux de traçabilité, exposés dans "classification_source" :
  - "loi"           : le texte de loi (ou son règlement d'application) cite
                      LUI-MÊME le code/la position SH.
  - "estimation_ia" : la loi ne nomme que le produit ; le code SH est une
                      classification technique que j'ai établie à partir du
                      nom (nomenclature SH standard), PAS une citation légale.

Règles de destination finale (ex. "équipement industriel sous licence",
statut de l'importateur pour les sociétés minières en Mauritanie, statut
diplomatique en Angola) ne sont PAS mappables par code SH — elles dépendent
de qui importe, pas de ce qui est importé. Documentées mais non appliquées.

Catégories trouvées mais volontairement NON appliquées ici (skip) car trop
larges pour une correspondance SH6 fiable : huiles de cuisson (plusieurs
chapitres 15.xx selon l'huile), viandes fraîches/congelées génériques
(éventail de sous-positions 02.01-02.04), volaille "cuisses" (sous-position
plus fine que SH6), gaz domestique/LPG au sens large (chapitre 27.11 couvre
aussi le propane et d'autres usages), bicyclettes (87.12 couvre tous les
vélos, pas seulement ceux ≤4 vitesses), kérosène/carburéacteur (271019 est
un fourre-tout "autres" trop large), engrais/moustiquaires/ARV zambiens
(descriptions trop génériques sans code SH confirmé), listes libyennes
(texte arabe non accessible), Soudan (aucune liste produit trouvée).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

CRAWLED_DIR = Path(__file__).parent.parent / "data" / "crawled"


class ProductOverride:
    def __init__(
        self,
        hs_prefix: str,
        tax_code: str,
        name: str,
        rate: float,
        classification_source: str,  # "loi" | "estimation_ia"
        source: str,
        source_url: str,
        as_of: str,
        product_note: str = "",
    ):
        self.hs_prefix = hs_prefix
        self.tax_code = tax_code
        self.name = name
        self.rate = rate
        self.classification_source = classification_source
        self.source = source
        self.source_url = source_url
        self.as_of = as_of
        self.product_note = product_note

    def to_entry(self) -> Dict:
        note = (
            "Correspondance SH établie par classification technique (nom du "
            "produit cité par la loi, code SH non cité par la loi elle-même)."
            if self.classification_source == "estimation_ia"
            else "Code/position SH cité directement par le texte réglementaire."
        )
        if self.product_note:
            note += f" {self.product_note}"
        return {
            "name": self.name,
            "rate": self.rate,
            "raw": f"{self.rate} %",
            "source": self.source,
            "source_url": self.source_url,
            "as_of": self.as_of,
            "classification_source": self.classification_source,
            "note": note,
        }


# iso3 -> liste de surcharges (préfixe SH6 ou plus court -> taxe remplacée/ajoutée)
PRODUCT_OVERRIDES: Dict[str, List[ProductOverride]] = {
    "AGO": [
        # Anexo I (Código do IVA) — 5 % permanent depuis OGE 2026 (anciennement 7 %,
        # réduit à 5% par la Loi 14/23 dès 2024-01-01). Sous-ensemble non ambigu.
        ProductOverride("1905", "IVA", "Imposto sobre o Valor Acrescentado (IVA) — pão", 5.0,
                         "estimation_ia", "Anexo I Código do IVA / minfin.gov.ao",
                         "https://www.minfin.gov.ao/sala-de-imprensa/noticias/noticia/nova-taxa-do-iva-em-5-para-os-bens-alimentares-de-amplo-consumo-e-cesta-basica-entra-em-vigor-a-1-de-janeiro-de-2024",
                         "2026 (permanent depuis OGE 2026)", "Nom légal : \"pão\" (pain)."),
        ProductOverride("0407", "IVA", "IVA — ovos", 5.0, "estimation_ia",
                         "Anexo I Código do IVA / minfin.gov.ao",
                         "https://www.minfin.gov.ao/sala-de-imprensa/noticias/noticia/nova-taxa-do-iva-em-5-para-os-bens-alimentares-de-amplo-consumo-e-cesta-basica-entra-em-vigor-a-1-de-janeiro-de-2024",
                         "2026", "Nom légal : \"ovos\" (œufs)."),
        ProductOverride("0713", "IVA", "IVA — feijão", 5.0, "estimation_ia",
                         "Anexo I Código do IVA / minfin.gov.ao",
                         "https://www.minfin.gov.ao/sala-de-imprensa/noticias/noticia/nova-taxa-do-iva-em-5-para-os-bens-alimentares-de-amplo-consumo-e-cesta-basica-entra-em-vigor-a-1-de-janeiro-de-2024",
                         "2026", "Nom légal : \"feijão\" (haricots)."),
        ProductOverride("0701", "IVA", "IVA — batata", 5.0, "estimation_ia",
                         "Anexo I Código do IVA / minfin.gov.ao",
                         "https://www.minfin.gov.ao/sala-de-imprensa/noticias/noticia/nova-taxa-do-iva-em-5-para-os-bens-alimentares-de-amplo-consumo-e-cesta-basica-entra-em-vigor-a-1-de-janeiro-de-2024",
                         "2026", "Nom légal : \"batata\" (pomme de terre)."),
        ProductOverride("1101", "IVA", "IVA — farinha de trigo", 5.0, "estimation_ia",
                         "Anexo I Código do IVA / minfin.gov.ao",
                         "https://www.minfin.gov.ao/sala-de-imprensa/noticias/noticia/nova-taxa-do-iva-em-5-para-os-bens-alimentares-de-amplo-consumo-e-cesta-basica-entra-em-vigor-a-1-de-janeiro-de-2024",
                         "2026", "Nom légal : \"farinha de trigo\" (farine de blé)."),
        ProductOverride("1102", "IVA", "IVA — farinha de milho", 5.0, "estimation_ia",
                         "Anexo I Código do IVA / minfin.gov.ao",
                         "https://www.minfin.gov.ao/sala-de-imprensa/noticias/noticia/nova-taxa-do-iva-em-5-para-os-bens-alimentares-de-amplo-consumo-e-cesta-basica-entra-em-vigor-a-1-de-janeiro-de-2024",
                         "2026", "Nom légal : \"farinha de milho\" (farine de maïs)."),
        ProductOverride("2201", "IVA", "IVA — água mineral/de mesa", 5.0, "estimation_ia",
                         "Anexo I Código do IVA / minfin.gov.ao",
                         "https://www.minfin.gov.ao/sala-de-imprensa/noticias/noticia/nova-taxa-do-iva-em-5-para-os-bens-alimentares-de-amplo-consumo-e-cesta-basica-entra-em-vigor-a-1-de-janeiro-de-2024",
                         "2026", "Nom légal : \"água mineral e de mesa\"."),
        ProductOverride("3401", "IVA", "IVA — sabão", 5.0, "estimation_ia",
                         "Anexo I Código do IVA / minfin.gov.ao",
                         "https://www.minfin.gov.ao/sala-de-imprensa/noticias/noticia/nova-taxa-do-iva-em-5-para-os-bens-alimentares-de-amplo-consumo-e-cesta-basica-entra-em-vigor-a-1-de-janeiro-de-2024",
                         "2026", "Nom légal : \"sabão\" (savon)."),
        ProductOverride("0402", "IVA", "IVA — leite condensado/em pó", 5.0, "estimation_ia",
                         "Anexo I Código do IVA / minfin.gov.ao",
                         "https://www.minfin.gov.ao/sala-de-imprensa/noticias/noticia/nova-taxa-do-iva-em-5-para-os-bens-alimentares-de-amplo-consumo-e-cesta-basica-entra-em-vigor-a-1-de-janeiro-de-2024",
                         "2026", "Nom légal : \"leite condensado e em pó\"."),
    ],
    "MOZ": [
        # Art. 9(13)/12(a) CIVA — cesta básica EXONEREE (0%), pas seulement reduite.
        ProductOverride("1005", "IVA", "IVA — milho (exonéré, cesta básica)", 0.0, "estimation_ia",
                         "Art. 9(13)/12(a) Código do IVA (Lei 22/2022)",
                         "https://taxsummaries.pwc.com/mozambique/corporate/other-taxes",
                         "2026", "Nom légal : \"milho\" (maïs)."),
        ProductOverride("1006", "IVA", "IVA — arroz (exonéré, cesta básica)", 0.0, "estimation_ia",
                         "Art. 9(13)/12(a) Código do IVA (Lei 22/2022)",
                         "https://taxsummaries.pwc.com/mozambique/corporate/other-taxes",
                         "2026", "Nom légal : \"arroz\" (riz)."),
        ProductOverride("1001", "IVA", "IVA — trigo (exonéré, cesta básica)", 0.0, "estimation_ia",
                         "Art. 9(13)/12(a) Código do IVA (Lei 22/2022)",
                         "https://taxsummaries.pwc.com/mozambique/corporate/other-taxes",
                         "2026", "Nom légal : \"trigo\" (blé)."),
        ProductOverride("1101", "IVA", "IVA — farinha de trigo (exonéré)", 0.0, "estimation_ia",
                         "Art. 9(13)/12(a) Código do IVA (Lei 22/2022)",
                         "https://taxsummaries.pwc.com/mozambique/corporate/other-taxes",
                         "2026", "Nom légal : \"farinha de trigo\"."),
        ProductOverride("1905", "IVA", "IVA — pão (exonéré)", 0.0, "estimation_ia",
                         "Art. 9(13)/12(a) Código do IVA (Lei 22/2022)",
                         "https://taxsummaries.pwc.com/mozambique/corporate/other-taxes",
                         "2026", "Nom légal : \"pão\"."),
        ProductOverride("2501", "IVA", "IVA — sal iodado (exonéré)", 0.0, "estimation_ia",
                         "Art. 9(13)/12(a) Código do IVA (Lei 22/2022)",
                         "https://taxsummaries.pwc.com/mozambique/corporate/other-taxes",
                         "2026", "Nom légal : \"sal iodado\"."),
        ProductOverride("0702", "IVA", "IVA — tomate (exonéré)", 0.0, "estimation_ia",
                         "Art. 9(13)/12(a) Código do IVA (Lei 22/2022)",
                         "https://taxsummaries.pwc.com/mozambique/corporate/other-taxes",
                         "2026", "Nom légal : \"tomate fresco ou refrigerado\"."),
        ProductOverride("0701", "IVA", "IVA — batata (exonéré)", 0.0, "estimation_ia",
                         "Art. 9(13)/12(a) Código do IVA (Lei 22/2022)",
                         "https://taxsummaries.pwc.com/mozambique/corporate/other-taxes",
                         "2026", "Nom légal : \"batata\"."),
        ProductOverride("0703", "IVA", "IVA — cebola (exonéré)", 0.0, "estimation_ia",
                         "Art. 9(13)/12(a) Código do IVA (Lei 22/2022)",
                         "https://taxsummaries.pwc.com/mozambique/corporate/other-taxes",
                         "2026", "Nom légal : \"cebola\"."),
        ProductOverride("401410", "IVA", "IVA — preservativos (exonéré)", 0.0, "estimation_ia",
                         "Art. 9(13)/12(a) Código do IVA (Lei 22/2022)",
                         "https://taxsummaries.pwc.com/mozambique/corporate/other-taxes",
                         "2026", "Nom légal : \"preservativos\"."),
        ProductOverride("380891", "IVA", "IVA — insecticidas (exonéré)", 0.0, "estimation_ia",
                         "Art. 9(13)/12(a) Código do IVA (Lei 22/2022)",
                         "https://taxsummaries.pwc.com/mozambique/corporate/other-taxes",
                         "2026", "Nom légal : \"insecticidas\"."),
    ],
    "STP": [
        ProductOverride("1006", "IVA", "IVA — arroz (Anexo I, panier de base)", 7.5, "estimation_ia",
                         "Lei n.º 02/2023 de 31 de maio, Anexo I",
                         "https://www.mirandalawfirm.com/pt/conhecimento-media/publications/alerts/entrada-em-vigor-do-codigo-do-iva-em-stp-2",
                         "2026", "Nom légal : \"arroz\"."),
        ProductOverride("1102", "IVA", "IVA — farinha de milho (Anexo I)", 7.5, "estimation_ia",
                         "Lei n.º 02/2023 de 31 de maio, Anexo I",
                         "https://www.mirandalawfirm.com/pt/conhecimento-media/publications/alerts/entrada-em-vigor-do-codigo-do-iva-em-stp-2",
                         "2026", "Nom légal : \"farinha de milho\" (farine de MAÏS, pas de blé)."),
        ProductOverride("1902", "IVA", "IVA — massas alimentícias (Anexo I)", 7.5, "estimation_ia",
                         "Lei n.º 02/2023 de 31 de maio, Anexo I",
                         "https://www.mirandalawfirm.com/pt/conhecimento-media/publications/alerts/entrada-em-vigor-do-codigo-do-iva-em-stp-2",
                         "2026", "Nom légal : \"massas alimentícias\" (pâtes)."),
        ProductOverride("1905", "IVA", "IVA — pão (Anexo I)", 7.5, "estimation_ia",
                         "Lei n.º 02/2023 de 31 de maio, Anexo I",
                         "https://www.mirandalawfirm.com/pt/conhecimento-media/publications/alerts/entrada-em-vigor-do-codigo-do-iva-em-stp-2",
                         "2026", "Nom légal : \"pão\"."),
        ProductOverride("0401", "IVA", "IVA — leite (Anexo I)", 7.5, "estimation_ia",
                         "Lei n.º 02/2023 de 31 de maio, Anexo I",
                         "https://www.mirandalawfirm.com/pt/conhecimento-media/publications/alerts/entrada-em-vigor-do-codigo-do-iva-em-stp-2",
                         "2026", "Nom légal : \"leite\"."),
        ProductOverride("0713", "IVA", "IVA — feijão (Anexo I)", 7.5, "estimation_ia",
                         "Lei n.º 02/2023 de 31 de maio, Anexo I",
                         "https://www.mirandalawfirm.com/pt/conhecimento-media/publications/alerts/entrada-em-vigor-do-codigo-do-iva-em-stp-2",
                         "2026", "Nom légal : \"feijão\"."),
    ],
    "MDG": [
        # HS 2711.13 = "butanes, liquéfiés" : position SH6 mondiale standard pour le
        # butane — correspondance quasi-certaine même si le texte de loi malgache ne
        # cite lui-même que le taux (le SH 7311.00.00 trouvé concerne le RÉCIPIENT
        # en acier, pas le gaz). Taux relevé 5%->10% par la Loi de Finances 2025
        # (et non 2026 comme initialement supposé).
        ProductOverride("271113", "TVA", "TVA — gaz butane", 10.0, "estimation_ia",
                         "Loi de Finances 2025 (LOI n° 2024-025) — gaz butane",
                         "https://www.mef.gov.mg/assets/vendor/ckeditor/plugins/kcfinder/upload/files/lfi_2025/Ampliation%20LOI%20n%C2%B0%202024-025LF2025_VF_PRMLG--12-18.pdf",
                         "2025 (en vigueur depuis, confirmé toujours actif en 2026)",
                         "Recherche interrompue avant confirmation finale : la Loi de "
                         "Finances 2026 mentionnerait une \"détaxation du riz\" (HS 1006) "
                         "non appliquée ici faute de confirmation dans le texte primaire."),
    ],
    "ZWE": [
        # S.I. 15/2024 (VAT (General)(Amendment) Regulations 2024) — la loi ELLE-MÊME
        # cite les positions douanières (Customs and Excise Act [Chapter 23:02]).
        ProductOverride("8701", "VAT", "VAT — agricultural tractors (exempt)", 0.0, "loi",
                         "Zimbabwe VAT Act [Chapter 23:12], Second Schedule + S.I. 15 of 2024",
                         "https://www.dlapiperafrica.com",
                         "2024 (S.I. 15/2024, toujours en vigueur 2026)",
                         "Exclut les semi-tracteurs routiers selon le texte réglementaire."),
        ProductOverride("8432", "VAT", "VAT — tillers / soil-preparation machinery (exempt)", 0.0, "loi",
                         "Zimbabwe VAT Act [Chapter 23:12], Second Schedule + S.I. 15 of 2024",
                         "https://www.dlapiperafrica.com",
                         "2024 (S.I. 15/2024, toujours en vigueur 2026)", ""),
    ],
    "MUS": [
        # VAT Act — First Schedule (exonéré) : cite directement les codes SH.
        ProductOverride("9018", "VAT", "VAT — medical/surgical/dental instruments (exempt)", 0.0, "loi",
                         "Mauritius VAT Act, First Schedule",
                         "https://www.mra.mu/26-vat",
                         "2026", "Liste First Schedule non exhaustive — d'autres sous-positions "
                         "(tissus, cuirs, soie, cocopeat) existent mais ne sont pas reprises ici."),
    ],
    "MWI": [
        # VAT Act (Cap 42:02) — la loi dit "classifié conformément au SH" mais les
        # codes numériques précis n'ont pas été retrouvés ; correspondance technique.
        ProductOverride("0409", "VAT", "VAT — natural honey (exempt)", 0.0, "estimation_ia",
                         "Malawi VAT Act (Cap 42:02), First Schedule",
                         "https://malawilii.org/akn/mw/act/2005/7",
                         "2026", "Nom légal : \"natural honey\"."),
        ProductOverride("0407", "VAT", "VAT — birds' eggs (exempt)", 0.0, "estimation_ia",
                         "Malawi VAT Act (Cap 42:02), First Schedule",
                         "https://malawilii.org/akn/mw/act/2005/7",
                         "2026", "Nom légal : \"birds' eggs\"."),
        ProductOverride("4901", "VAT", "VAT — printed books (exempt)", 0.0, "estimation_ia",
                         "Malawi VAT Act (Cap 42:02), First Schedule",
                         "https://malawilii.org/akn/mw/act/2005/7",
                         "2026", "Nom légal : \"printed matter — books\"."),
    ],
    "SYC": [
        ProductOverride("1006", "VAT", "VAT — rice (exempt import)", 0.0, "estimation_ia",
                         "Seychelles VAT Act 2010, First Schedule Part I",
                         "https://seylii.org",
                         "2026", "Nom légal : \"rice\"."),
        ProductOverride("071340", "VAT", "VAT — lentils (exempt import)", 0.0, "estimation_ia",
                         "Seychelles VAT Act 2010, First Schedule Part I",
                         "https://seylii.org",
                         "2026", "Nom légal : \"lentils\"."),
    ],
    "MRT": [
        # "Produits pétroliers" 20% (vs 16% standard) — la loi nomme une catégorie
        # qui correspond en pratique à l'intégralité du chapitre SH 27.
        ProductOverride("27", "TVA", "TVA — produits pétroliers (chap. 27)", 20.0, "estimation_ia",
                         "Code Général des Impôts (Mauritanie), doctrine TVA DGI",
                         "https://impots.gov.mr/DGI/files/doctrine/Livre2-Titre1-TVA-20191010.pdf",
                         "2026", "Catégorie légale : \"produits pétroliers\" — chapitre SH 27 entier."),
    ],
    # LBY, COM, SDN, ZMB : aucune correspondance SH suffisamment fiable trouvée —
    # aucune surcharge appliquée (cf. docstring). Les taxes nationales de base
    # (enrich_wits_national_vat.py) restent la seule couche disponible pour eux.
}


def apply_overrides(iso3: str, overrides: List[ProductOverride]) -> int:
    path = CRAWLED_DIR / f"{iso3}_tariffs.json"
    if not path.exists():
        print(f"[{iso3}] fichier introuvable.")
        return 0

    data = json.loads(path.read_text(encoding="utf-8"))
    positions = data.get("sub_positions", [])
    if not positions:
        print(f"[{iso3}] aucune position.")
        return 0

    touched = 0
    for pos in positions:
        code = pos.get("hs_code", "")
        for ov in overrides:
            if code.startswith(ov.hs_prefix):
                taxes = pos.setdefault("taxes", {})
                taxes[ov.tax_code] = ov.to_entry()
                touched += 1

    rules = data.setdefault("calculation_rules", {"order": ["DD"], "bases": {}})
    suffix = (
        " Surcharges par produit ajoutées pour des positions spécifiques "
        "(voir taxes[].classification_source par position : 'loi' = code SH "
        "cité par le texte réglementaire, 'estimation_ia' = classification "
        "technique du produit nommé par la loi)."
    )
    if suffix not in rules.get("source", ""):
        rules["source"] = rules.get("source", "") + suffix

    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[{iso3}] {touched} position(s) avec surcharge produit appliquée.")
    return touched


def main():
    total = 0
    for iso3, overrides in PRODUCT_OVERRIDES.items():
        total += apply_overrides(iso3, overrides)
    print(f"\nTotal : {total} surcharges position par position appliquées.")


if __name__ == "__main__":
    main()

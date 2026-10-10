"""Convertit la sortie de scripts/extraire_tec_civ.py en artefact canonique
backend/data/crawled/CIV_tariffs.json (positions, taxes_detail, légende), puis
le scelle (backend/crawlers/integrity) ; l'empreinte du fichier est à reporter
dans backend/data/source_registry_v2.json.

    python3 scripts/extraire_tec_civ.py <tarif.pdf> <tec.json>
    python3 scripts/convertir_tec_civ.py <tec.json> <tarif.pdf>
"""
import datetime
import hashlib
import json
import os
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RACINE, "backend"))
from crawlers.integrity import seal_crawled_file  # noqa: E402

SORTIE = os.path.join(RACINE, "backend", "data", "crawled", "CIV_tariffs.json")
NOMS = {
    "DD": ("Droit de Douane", "ad_valorem", "CIF"),
    "RST": ("Redevance Statistique", "ad_valorem", "CIF"),
    "PCC": ("Prélèvement Communautaire CEDEAO", "ad_valorem", "CIF"),
    "PCS": ("Prélèvement Communautaire de Solidarité (UEMOA)", "ad_valorem", "CIF"),
    "PUA": ("Prélèvement de l'Union Africaine", "ad_valorem", "CIF"),
    "TVA": ("Taxe sur la Valeur Ajoutée", "ad_valorem", "CIF"),
    "TSB": ("Taxe Spéciale sur les Boissons (CGI art. 418)", "ad_valorem", "CIF"),
    "TAB": ("Taxe Spéciale sur les Tabacs (CGI art. 418)", "ad_valorem", "CIF"),
    "TCB": ("Taxe Spéciale sur les Parfums et Cosmétiques (CGI art. 418)", "ad_valorem", "CIF"),
    "TSM": ("Taxe Spéciale sur les Marbres (CGI art. 418)", "ad_valorem", "CIF"),
    "DUS": ("Droit Unique de Sortie (export)", "ad_valorem", "variable"),
    "TMP": ("Taxe Spéciale sur certains produits en plastique, métal, verre et carton (FCFA/kg)", "specific", "variable"),
    "TCI": ("Taxe Conjoncturelle à l'Importation", "ad_valorem", "variable"),
    "PSV": ("Prélèvement Spécial de Viabilité", "specific", "variable"),
}
CODE = {"RST": "RS", "TSB": "TSB_PT"}

tec = json.load(open(sys.argv[1], encoding="utf-8"))
pdf_sha = hashlib.sha256(open(sys.argv[2], "rb").read()).hexdigest()
positions = []
for code, valeurs in tec.items():
    detail = []
    for k, taux in valeurs.items():
        if k.startswith("_"):
            continue
        nom, type_taux, base = NOMS.get(
            k, (f"Taxe nationale de code SYDAM « {k} » (nature et assiette non établies)", "ad_valorem", "variable")
        )
        detail.append({"tax_code": CODE.get(k, k), "tax_name": nom, "rate": taux, "rate_type": type_taux, "base": base})
    positions.append({
        "code": f"{code[:4]}.{code[4:6]}.{code[6:8]}.{code[8:]}", "code_clean": code, "code_length": 10,
        "designation": valeurs["_libelle"], "chapter": code[:2], "hs2": code[:2], "hs4": code[:4], "hs6": code[:6],
        "unit": "QA", "taxes": {d["tax_code"]: d["rate"] for d in detail}, "taxes_detail": detail,
        "source": "douanes.ci", "data_type": "national",
    })
artefact = {
    "country": "CIV", "country_name": "Côte d'Ivoire", "source": "douanes.ci", "source_url": "https://www.douanes.ci",
    "method": "pdf_officiel", "hs_level": "national_sub_positions",
    "nomenclature": "TEC CEDEAO 2022 (SH 2022), version SYDAM World, taxation nationale",
    "data_type": "national", "currency": "XOF (FCFA)",
    "extracted_at": datetime.datetime.now(datetime.timezone.utc).isoformat(), "total_positions": len(positions),
    "source_document": {
        "titre": "TEC CEDEAO 2022 version SYDAM World — libellé révisé, enrichi de la taxation nationale (mise à jour : 27/03/2026)",
        "pages": 566, "sha256": pdf_sha,
        "depot": "PR #620, data/cote-d-ivoire/docs_officiels/TEC-CEDEAO-ENRICHI-TAXATION-NATIONALE-27-03-2026.pdf",
        "lecture": "texte du PDF, valeurs rattachées aux colonnes par leur position horizontale et aux positions par le quadrillage du tableau (scripts/extraire_tec_civ.py)",
    },
    "tax_legend": {
        "DD": "Droit de douane (TEC CEDEAO)", "TVA": "Taxe sur la valeur ajoutée (0, 9 ou 18 %)",
        "RS": "Redevance statistique (colonne RST, 1 %)", "PCC": "Prélèvement communautaire CEDEAO (0,5 %)",
        "PCS": "Prélèvement communautaire de solidarité UEMOA (0,8 %)", "PUA": "Prélèvement de l'Union africaine (0,2 %)",
        "TSB_PT": "Taxe spéciale sur les boissons (colonne TSB, CGI art. 418)",
        "TAB": "Taxe spéciale sur les tabacs (CGI art. 418, 57 %)",
        "TCB": "Taxe spéciale sur les parfums et cosmétiques (CGI art. 418)",
        "TSM": "Taxe spéciale sur les marbres (CGI art. 418)", "DUS": "Droit unique de sortie (export)",
        "TMP": "Taxe spéciale sur certains produits en plastique, métal, verre et carton (FCFA/kg, circulaire DGD n° 2389)",
        "TCI": "Taxe conjoncturelle à l'importation (selon un prix de déclenchement)",
        "PSV": "Prélèvement spécial de viabilité (FCFA/kg)",
        "autres": "TUB, TUF, TUE, PSS, TAI, TBG, TCT, TFS, TPQ, TSS : codes du tarif sans légende dans le document ; nature et assiette non établies",
    },
    "notes": [
        "Tarif officiel de la Direction générale des douanes (douanes.ci), mise à jour du 27 mars 2026, remplaçant la collecte du portail GUCE du 19 février 2026.",
        "Une case vide du tarif est une taxe non due ; la TVA vide sur 61 positions est lue comme non renseignée.",
    ],
    "positions": positions,
}
json.dump(artefact, open(SORTIE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(len(positions), seal_crawled_file(SORTIE, "https://www.douanes.ci").file_hash)

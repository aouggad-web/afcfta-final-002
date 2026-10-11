"""Convertit la sortie de scripts/extraire_tec_gin.py en artefact canonique
backend/data/crawled/GIN_tariffs.json, puis le scelle (backend/crawlers/integrity) ;
l'empreinte du fichier est à reporter dans backend/data/source_registry_v2.json.

Colonnes d'entrée du tarif (arrêté du 31/03/2017, art. 9) : DD, RTL, AC
(accises, servie sous le code DA), TVA, PC (prélèvement communautaire de la
CEDEAO, code PCC) et CA (centime additionnel). Une accise « ex » est omise ; une
accise de plus de 100 (produits pétroliers) est un montant spécifique, servi
sans taux. La colonne DFE (sortie) n'entre pas dans un calcul d'importation.

    python3 scripts/extraire_tec_gin.py <tarif.pdf> <tec.json>
    python3 scripts/convertir_tec_gin.py <tec.json> <tarif.pdf>
"""
import datetime
import hashlib
import json
import os
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RACINE, "backend"))
from crawlers.integrity import seal_crawled_file  # noqa: E402

SORTIE = os.path.join(RACINE, "backend", "data", "crawled", "GIN_tariffs.json")
COLONNES = [
    ("DD", "DD", "Droit de Douane (TEC CEDEAO)", "CIF"),
    ("RTL", "RTL", "Redevance de Traitement et de Liquidation", "CIF"),
    ("PC", "PCC", "Prélèvement Communautaire CEDEAO", "CIF"),
    ("CA", "CA", "Centime Additionnel", "CIF"),
    ("AC", "DA", "Droit d'accises (colonne AC du tarif)", "variable"),
    ("TVA", "TVA", "Taxe sur la Valeur Ajoutée", None),
]

tec = json.load(open(sys.argv[1], encoding="utf-8"))
pdf_sha = hashlib.sha256(open(sys.argv[2], "rb").read()).hexdigest()
precedent = {}
if os.path.exists(SORTIE):
    precedent = {p["code_clean"]: p.get("designation") for p in json.load(open(SORTIE, encoding="utf-8"))["positions"]}
positions = []
for code, valeurs in sorted(tec.items()):
    detail = []
    for col, canon, nom, base in COLONNES:
        taux = valeurs.get(col)
        if col == "AC" and not taux:
            continue
        if col == "AC" and taux > 100:
            taux = None
            nom += " — montant spécifique, unité non lue"
        detail.append({"tax_code": canon, "tax_name": nom, "rate": taux, "rate_type": "ad_valorem", "base": base})
    positions.append({
        "code": f"{code[:4]}.{code[4:6]}.{code[6:8]}.{code[8:]}", "code_clean": code, "code_length": 10,
        "designation": precedent.get(code) or valeurs.get("_libelle", ""), "chapter": code[:2], "hs2": code[:2],
        "hs4": code[:4], "hs6": code[:6], "unit": "QA",
        "taxes": {d["tax_code"]: d["rate"] for d in detail}, "taxes_detail": detail,
        "source": "dgd.gov.gn", "data_type": "national",
    })
artefact = {
    "country": "GIN", "country_name": "Guinée", "source": "dgd.gov.gn", "source_url": "https://dgd.gov.gn/",
    "method": "pdf_officiel", "hs_level": "national_sub_positions",
    "nomenclature": "TEC CEDEAO (SH 2022), tarif de la DGD de Guinée",
    "data_type": "national", "currency": "GNF (Franc Guinéen)",
    "extracted_at": datetime.datetime.now(datetime.timezone.utc).isoformat(), "total_positions": len(positions),
    "source_document": {
        "titre": "Tarif extérieur commun de la CEDEAO, SH 2022, DGD de Guinée (colonnes DD, RTL, AC, TVA, PC, CA, DFE), 18/01/2022",
        "pages": 414, "sha256": pdf_sha,
        "depot": "PR #620, data/guinee/docs_officiels/TEC-SH2022-GUINEE.pdf",
        "lecture": "texte du PDF, valeurs rattachées aux colonnes de l'en-tête et à la cellule de la position (scripts/extraire_tec_gin.py)",
    },
    "notes": [
        "Tarif de la DGD (SH 2022) remplaçant la collecte du 19 février 2026 (SH 2017, sans RTL, accises ni centime additionnel).",
        "« ex » au tarif : taxe non due (TVA à 0 %, accise omise).",
        "15 positions dont les valeurs n'ont pas été lues (cellule coupée par un saut de page) : taux non renseignés.",
    ],
    "positions": positions,
}
json.dump(artefact, open(SORTIE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(len(positions), seal_crawled_file(SORTIE, "https://dgd.gov.gn/").file_hash)

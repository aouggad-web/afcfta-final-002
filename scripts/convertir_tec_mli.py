"""Convertit la sortie de scripts/extraire_tec_mli.py en artefact canonique
backend/data/crawled/MLI_tariffs.json (positions, taxes_detail, légende), puis
le scelle (backend/crawlers/integrity) ; l'empreinte du fichier est à reporter
dans backend/data/source_registry_v2.json.

La colonne PC du tarif de 2023 est le prélèvement communautaire de la CEDEAO,
que le Mali a quittée le 29 janvier 2025 ; il est servi sous le code PC-AES,
prélèvement confédéral de l'AES au même taux (décision du 28 mars 2025).

    python3 scripts/extraire_tec_mli.py <tarif.pdf> <tec.json>
    python3 scripts/convertir_tec_mli.py <tec.json> <tarif.pdf>
"""
import datetime
import hashlib
import json
import os
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RACINE, "backend"))
from crawlers.integrity import seal_crawled_file  # noqa: E402

SORTIE = os.path.join(RACINE, "backend", "data", "crawled", "MLI_tariffs.json")
NOMS = {
    "DD": ("DD", "Droit de Douane (TEC CEDEAO)", "CIF"),
    "RS": ("RS", "Redevance Statistique", "CIF"),
    "PC": ("PC-AES", "Prélèvement Confédéral AES (colonne PC du tarif)", "CIF"),
    "PCS": ("PCS", "Prélèvement Communautaire de Solidarité (UEMOA)", "CIF"),
    "ISCP": ("ISCP", "Impôt Spécial sur Certains Produits", "variable"),
    "TVA": ("TVA", "Taxe sur la Valeur Ajoutée", "variable"),
    "TAI": ("TAI", "Taxe d'Ajustement à l'Importation", "variable"),
    "TCI": ("TCI", "Taxe Conjoncturelle à l'Importation", "variable"),
    "TCP": ("TCP", "Taxe Complémentaire de Protection", "variable"),
}

tec = json.load(open(sys.argv[1], encoding="utf-8"))
pdf_sha = hashlib.sha256(open(sys.argv[2], "rb").read()).hexdigest()
positions = []
for code, valeurs in sorted(tec.items()):
    detail = []
    for k, taux in valeurs.items():
        if k.startswith("_") or k not in NOMS:
            continue
        canon, nom, base = NOMS[k]
        detail.append({"tax_code": canon, "tax_name": nom, "rate": taux, "rate_type": "ad_valorem", "base": base})
    if not detail:
        continue
    if "TVA" not in valeurs:
        # Case de TVA vide : taux non renseigné, pas TVA non due.
        canon, nom, base = NOMS["TVA"]
        detail.append({"tax_code": canon, "tax_name": nom, "rate": None, "rate_type": "ad_valorem", "base": base})
    positions.append({
        "code": f"{code[:4]}.{code[4:6]}.{code[6:8]}.{code[8:]}", "code_clean": code, "code_length": 10,
        "designation": valeurs.get("_libelle", ""), "chapter": code[:2], "hs2": code[:2], "hs4": code[:4], "hs6": code[:6], "unit": "QA",
        "taxes": {d["tax_code"]: d["rate"] for d in detail}, "taxes_detail": detail,
        "source": "douanes.gouv.ml", "data_type": "national",
    })
artefact = {
    "country": "MLI", "country_name": "Mali", "source": "douanes.gouv.ml", "source_url": "https://douanes.gouv.ml/",
    "method": "pdf_officiel", "hs_level": "national_sub_positions",
    "nomenclature": "TEC CEDEAO (SH 2022), édition du Mali, structure fiscale nationale",
    "data_type": "national", "currency": "XOF (FCFA)",
    "extracted_at": datetime.datetime.now(datetime.timezone.utc).isoformat(), "total_positions": len(positions),
    "source_document": {
        "titre": "Le Tarif extérieur commun de la CEDEAO — édition du Mali (colonnes DD, RS, PC, PCS, ISCP, TVA, TAI, TCI, TCP, AUTRES), 28/12/2023",
        "pages": 448, "sha256": pdf_sha,
        "depot": "PR #620, data/mali/docs_officiels/TEC-CEDEAO-SH2023-MALI.pdf",
        "lecture": "texte du PDF, valeurs rattachées aux colonnes par leur position horizontale et aux positions par la ligne du code (scripts/extraire_tec_mli.py)",
    },
    "notes": [
        "Tarif du Mali (SH 2022) remplaçant la collecte du 19 février 2026 (SH 2017).",
        "Une case vide est une taxe non due ; la TVA vide sur 12 positions est lue comme non renseignée.",
        "Colonne PC (CEDEAO, 0,5 %) servie sous le code PC-AES depuis la sortie du Mali de la CEDEAO.",
    ],
    "positions": positions,
}
json.dump(artefact, open(SORTIE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(len(positions), seal_crawled_file(SORTIE, "https://douanes.gouv.ml/").file_hash)

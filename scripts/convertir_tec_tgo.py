"""Convertit la sortie de scripts/extraire_tec_tgo.py en artefact canonique
backend/data/crawled/TGO_tariffs.json, puis le scelle (backend/crawlers/integrity) ;
l'empreinte du fichier est à reporter dans backend/data/source_registry_v2.json.

Le tarif de l'OTR ne porte que D.D. et R.S. ; les prélèvements du tableau
officiel des taux de l'OTR (PCS 0,8 %, PC 0,5 %, PUA 0,2 %, prélèvement
national de solidarité 0,5 %) et la TVA (18 %) sont ajoutés à chaque position
(fiche TGO_prelevements_TVA_2026-10-12.json). Le libellé est celui de la
collecte précédente quand la position y figure, sinon celui lu dans le tarif.

    python3 scripts/extraire_tec_tgo.py <tarif.pdf> <tec.json>
    python3 scripts/convertir_tec_tgo.py <tec.json> <tarif.pdf>
"""
import datetime
import hashlib
import json
import os
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RACINE, "backend"))
from crawlers.integrity import seal_crawled_file  # noqa: E402

SORTIE = os.path.join(RACINE, "backend", "data", "crawled", "TGO_tariffs.json")
AJOUTS = [
    ("PCS", "Prélèvement Communautaire de Solidarité (UEMOA)", 0.8, "CIF"),
    ("PCC", "Prélèvement Communautaire CEDEAO", 0.5, "CIF"),
    ("PUA", "Prélèvement Union Africaine", 0.2, "CIF"),
    ("PNS", "Prélèvement National de Solidarité", 0.5, "CIF"),
    # Assiette laissée vide : la table des assiettes établies y place celle de la
    # directive n° 02/98/CM/UEMOA (valeur en douane + droits et taxes d'entrée).
    ("TVA", "Taxe sur la Valeur Ajoutée", 18.0, None),
]

tec = json.load(open(sys.argv[1], encoding="utf-8"))
pdf_sha = hashlib.sha256(open(sys.argv[2], "rb").read()).hexdigest()
precedent = {}
if os.path.exists(SORTIE):
    precedent = {p["code_clean"]: p.get("designation") for p in json.load(open(SORTIE, encoding="utf-8"))["positions"]}
positions = []
for code, valeurs in sorted(tec.items()):
    detail = [
        {"tax_code": "DD", "tax_name": "Droit de Douane (TEC CEDEAO)", "rate": valeurs.get("DD"),
         "rate_type": "ad_valorem", "base": "CIF"},
        {"tax_code": "RS", "tax_name": "Redevance Statistique", "rate": valeurs.get("RS"),
         "rate_type": "ad_valorem", "base": "CIF"},
    ] + [{"tax_code": c, "tax_name": n, "rate": t, "rate_type": "ad_valorem", "base": b} for c, n, t, b in AJOUTS]
    positions.append({
        "code": f"{code[:4]}.{code[4:6]}.{code[6:8]}.{code[8:]}", "code_clean": code, "code_length": 10,
        "designation": precedent.get(code) or valeurs.get("_libelle", ""), "chapter": code[:2], "hs2": code[:2],
        "hs4": code[:4], "hs6": code[:6], "unit": "QA",
        "taxes": {d["tax_code"]: d["rate"] for d in detail}, "taxes_detail": detail,
        "source": "otr.tg", "data_type": "national",
    })
artefact = {
    "country": "TGO", "country_name": "Togo", "source": "otr.tg", "source_url": "https://www.otr.tg/",
    "method": "pdf_officiel", "hs_level": "national_sub_positions",
    "nomenclature": "TEC CEDEAO (SH 2022), tarif officiel de l'OTR",
    "data_type": "national", "currency": "XOF (FCFA)",
    "extracted_at": datetime.datetime.now(datetime.timezone.utc).isoformat(), "total_positions": len(positions),
    "source_document": {
        "titre": "Tarif extérieur commun de la CEDEAO actualisé au 10/11/2025 (OTR du Togo, colonnes D.D. et R.S.)",
        "pages": 478, "sha256": pdf_sha,
        "depot": "PR #620, data/togo/docs_officiels/TEC-CEDEAO-ACTUALISE-NOV2025.pdf",
        "lecture": "texte du PDF dans l'ordre des cellules : code, libellé, unité, D.D., R.S. (scripts/extraire_tec_tgo.py)",
    },
    "notes": [
        "Tarif officiel de l'OTR (SH 2022) remplaçant la collecte du 19 février 2026 (SH 2017, PCS à 1 %, sans PNS).",
        "PCS, PC, PUA, PNS et TVA ajoutés à taux uniforme (tableau officiel des taux de l'OTR ; fiche TGO_prelevements_TVA_2026-10-12.json).",
        "0304.82.00.00 : aucune valeur imprimée au tarif, D.D. et R.S. non renseignés.",
    ],
    "positions": positions,
}
json.dump(artefact, open(SORTIE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(len(positions), seal_crawled_file(SORTIE, "https://www.otr.tg/").file_hash)

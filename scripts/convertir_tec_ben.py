"""Convertit la sortie de scripts/extraire_tec_ben.py en artefact canonique
backend/data/crawled/BEN_tariffs.json, puis le scelle (backend/crawlers/integrity) ;
l'empreinte du fichier est à reporter dans backend/data/source_registry_v2.json.

Le tarif de la DGDDI ne porte que D.D. et R.S. ; les prélèvements
communautaires (PCS 0,8 %, PC 0,5 %, prélèvement de solidarité de l'UA 0,2 %),
la redevance d'aménagement urbain (0,5 %) et la TVA (18 %) sont ajoutés à chaque position (fiche
BEN_prelevements_TVA_2026-10-11.json). Le libellé est celui de la collecte
précédente quand la position y figure : l'export Excel centre le libellé des
cellules sur plusieurs lignes, que l'extraction tronque.

    python3 scripts/extraire_tec_ben.py <tarif.pdf> <tec.json>
    python3 scripts/convertir_tec_ben.py <tec.json> <tarif.pdf>
"""
import datetime
import hashlib
import json
import os
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RACINE, "backend"))
from crawlers.integrity import seal_crawled_file  # noqa: E402

SORTIE = os.path.join(RACINE, "backend", "data", "crawled", "BEN_tariffs.json")
AJOUTS = [
    ("PCS", "Prélèvement Communautaire de Solidarité (UEMOA)", 0.8, "CIF"),
    ("PCC", "Prélèvement Communautaire CEDEAO", 0.5, "CIF"),
    ("PUA", "Prélèvement de solidarité (Union africaine)", 0.2, "CIF"),
    ("RAU", "Redevance d'Aménagement Urbain", 0.5, "CIF"),
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
        "source": "douanes.gouv.bj", "data_type": "national",
    })
artefact = {
    "country": "BEN", "country_name": "Bénin", "source": "douanes.gouv.bj", "source_url": "https://douanes.gouv.bj/tarif-douane/",
    "method": "pdf_officiel", "hs_level": "national_sub_positions",
    "nomenclature": "TEC CEDEAO (SH 2022), tarif officiel de la DGDDI",
    "data_type": "national", "currency": "XOF (FCFA)",
    "extracted_at": datetime.datetime.now(datetime.timezone.utc).isoformat(), "total_positions": len(positions),
    "source_document": {
        "titre": "TARIF EXTERIEUR COMMUN TEC-CEDEAO SH2022 (DGDDI du Bénin, colonnes D.D. et R.S.), 07/11/2024",
        "pages": 392, "sha256": pdf_sha,
        "depot": "PR #620, data/benin/docs_officiels/TEC-CEDEAO-SH2022-TARIF-BENIN.pdf",
        "lecture": "texte du PDF, valeurs rattachées aux colonnes de l'en-tête de la page 1 et à la cellule de la position (scripts/extraire_tec_ben.py)",
    },
    "notes": [
        "Tarif officiel de la DGDDI (SH 2022) remplaçant la collecte du 19 février 2026 (SH 2017).",
        "PCS, PC, prélèvement de solidarité, RAU et TVA ajoutés à taux uniforme (fiche BEN_prelevements_TVA_2026-10-11.json).",
        "R.S. non lue sur 3 positions (bas de page) : taux non renseigné.",
    ],
    "positions": positions,
}
json.dump(artefact, open(SORTIE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(len(positions), seal_crawled_file(SORTIE, "https://douanes.gouv.bj/tarif-douane/").file_hash)

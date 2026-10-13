"""Convertit la sortie de scripts/extraire_pauta_cpv.py en artefact canonique
backend/data/crawled/CPV_tariffs.json, puis le scelle (backend/crawlers/integrity) ;
l'empreinte du fichier est à reporter dans backend/data/source_registry_v2.json.

Lignes servies par position (fiche CPV_pauta_IVA_ICE_2026-10-12.json) :

- DI de la Pauta (Lei 51/X/2025, annexe III de la Lei 69/X/2025) sur la valeur
  en douane ;
- TC, taxa comunitária CEDEAO 0,5 %, servie sous le code PCC : les originaires
  de la CEDEAO en sont exclus comme ailleurs ;
- ICE ad valorem sur la valeur en douane + DI + TC, et la taxe spécifique du
  tabac ou de l'alcool où elle existe (Código do ICE, art. 13 : tous impôts et
  taxes sauf l'ICE lui-même) ;
- ICE spécifique en CVE par unité des véhicules de l'annexe II de la Lei 69/X/2025 ;
- taxe spécifique de 180$00 par paquet de cigarettes (Lei 69/X/2025, art. 90) ;
- taxe spécifique en CVE par litre sur les boissons alcooliques (art. 91), dont
  le barème n'est pas dans les textes déposés : ligne sans montant, total déclaré
  incomplet ;
- IVA 15 % ou 0 (« Is ») sur la valeur en douane + tous les droits et taxes
  sauf l'IVA (Regulamento do IVA, art. 16).

Véhicules électriques (8703.80, 8711.60) : exonérés de DI, d'ICE et d'IVA
(Lei 69/X/2025, art. 54, n.º 1).

    python3 scripts/extraire_pauta_cpv.py <pauta2022.pdf> <lei51.pdf> <oe2026.pdf> <pauta.json>
    python3 scripts/convertir_tec_cpv.py <pauta.json> <pauta2022.pdf> <lei51.pdf> <oe2026.pdf>
"""
import datetime
import hashlib
import json
import os
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RACINE, "backend"))
from crawlers.integrity import seal_crawled_file  # noqa: E402

SORTIE = os.path.join(RACINE, "backend", "data", "crawled", "CPV_tariffs.json")
URL = "https://www.mf.gov.cv/"
ELECTRIQUES = ("870380", "871160")
ALCOOLS = ("2203", "2204", "2205", "2206", "2208")
CIGARETTES = "2402200000"

pauta = json.load(open(sys.argv[1], encoding="utf-8"))
empreintes = [hashlib.sha256(open(chemin, "rb").read()).hexdigest() for chemin in sys.argv[2:5]]
positions = []
for code, v in sorted(pauta.items()):
    di, ice, iva = v["DI"], v["ICE"], v["IVA"]
    electrique = code.startswith(ELECTRIQUES)
    if electrique:
        di, ice, iva = 0.0, None, 0.0
    detail = [
        {"tax_code": "DD", "tax_name": "Direitos de Importação (DI)", "rate": di, "rate_type": "ad_valorem",
         "base": "CIF"},
        {"tax_code": "PCC", "tax_name": "Taxa Comunitária CEDEAO (TC)", "rate": v["TC"], "rate_type": "ad_valorem",
         "base": "CIF"},
    ]
    # Les taxes spécifiques du tabac et de l'alcool entrent dans l'assiette de
    # l'ICE (Código do ICE, art. 13, n.º 3, a) : tous impôts et taxes sauf l'ICE).
    speciales = []
    if code == CIGARETTES:
        speciales.append({"tax_code": "TET", "tax_name": "Taxa específica sobre o tabaco (Lei 69/X/2025, art. 90.º)",
                          "rate": None, "specific_value": "180 CVE/maço"})
    if code.startswith(ALCOOLS):
        speciales.append({"tax_code": "TEA",
                          "tax_name": "Taxa específica sobre o álcool (Lei 69/X/2025, art. 91.º) — montant par litre non publié",
                          "rate": None})
    detail += speciales
    if ice:
        detail.append({"tax_code": "ICE", "tax_name": "Imposto sobre Consumos Especiais (ad valorem)", "rate": ice,
                       "rate_type": "ad_valorem", "base": "+".join(["CIF+DD+PCC"] + [t["tax_code"] for t in speciales])})
    if v.get("ICE_CVE_U") and not electrique:
        detail.append({"tax_code": "ICES", "tax_name": "ICE específico (Lei 69/X/2025, anexo II)", "rate": None,
                       "specific_value": f"{v['ICE_CVE_U']:.0f} CVE/u"})
    detail.append({"tax_code": "TVA", "tax_name": "Imposto sobre o Valor Acrescentado (IVA)", "rate": iva,
                   "rate_type": "ad_valorem", "base": "CIF+TOUS_SAUF_TVA"})
    positions.append({
        "code": f"{code[:4]}.{code[4:6]}.{code[6:8]}.{code[8:]}", "code_clean": code, "code_length": 10,
        "designation": v["_libelle"], "chapter": code[:2], "hs2": code[:2], "hs4": code[:4], "hs6": code[:6],
        "unit": "QA", "taxes": {d["tax_code"]: d["rate"] for d in detail}, "taxes_detail": detail,
        "source": "Pauta Aduaneira de Cabo Verde", "data_type": "national", "_texte": v["_origine"],
    })
artefact = {
    "country": "CPV", "country_name": "Cap-Vert", "source": "Pauta Aduaneira de Cabo Verde", "source_url": URL,
    "method": "pdf_officiel", "hs_level": "national_sub_positions",
    "nomenclature": "Pauta Aduaneira (SH 2022 par la Lei n.º 51/X/2025)",
    "data_type": "national", "currency": "CVE",
    "extracted_at": datetime.datetime.now(datetime.timezone.utc).isoformat(), "total_positions": len(positions),
    "source_document": {
        "titre": "Pauta Aduaneira 2022 ; Lei n.º 51/X/2025 (B.O. I série n.º 30, 17/04/2025) ; "
                 "Lei n.º 69/X/2025, OE 2026 (B.O. I série n.º 133, supl. 1, 31/12/2025), anexos II e III",
        "sha256": dict(zip(["pauta_2022", "lei_51_X_2025", "lei_69_X_2025"], empreintes)),
        "depot": "data/cpv/reference/",
        "lecture": "colonnes lues par position horizontale des mots (scripts/extraire_pauta_cpv.py)",
    },
    "notes": [
        "Remplace la transposition du TEC depuis le Bénin : le Cap-Vert applique sa propre Pauta (DI nationaux "
        "jusqu'à 55 %), sans redevance statistique ; l'adoption du TEC y est progressive (Lei 69/X/2025, art. 94).",
        "TC 0,5 % servie sous le code PCC (taxa comunitária CEDEAO).",
        "Taxe spécifique sur les produits doces (art. 92) et taxe carbone (art. 95, Lei 45/X/2024) : "
        "barème et champ absents des textes déposés, non servis.",
    ],
    "positions": positions,
}
json.dump(artefact, open(SORTIE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(len(positions), seal_crawled_file(SORTIE, URL).file_hash)

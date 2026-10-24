"""Remises de droits des Legal Notices EAC/162 à EAC/173/2026 (EAC Gazette
Vol. AT 1 No. 16 du 30/06/2026, p. 82-119), une mesure par code et par État,
pour data/eac/legal_overrides.json.

Ce sont les listes d'intrants par État partenaire et par filière (mobilier,
vêtements et textiles, chaussures, intrants industriels), complément de la
Table A de l'EAC/161/2026. Les tableaux sont lus dans le PDF déposé
(data/sources/eac/official/EAC_Vol_AT_1_No_16_2026-06-30.pdf) : une ligne
(S/N) porte un ou plusieurs codes, une désignation et, selon la notice, un
taux par code, un taux unique pour toute la liste ou une décision rédigée
(EAC/163 : États et taux dans le texte). Un code à 4 chiffres (« 41.07 »,
« 5801 ») vaut pour toute la position.

    python3 scripts/extraire_remises_eac_162_173_2026.py <sortie.json>
"""
import json
import os
import re
import sys

import pymupdf

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDF = os.path.join(REPO, "data", "sources", "eac", "official", "EAC_Vol_AT_1_No_16_2026-06-30.pdf")
URL = ("https://www.eac.int/documents?controller=download&file=a3c7fa5a-b765-48ed-befa-b6b65bf5b3cc"
       "&name=EAC+Vol.+AT+1+NO.+16+JUNE+2026.pdf.pdf&task=download.file")
SHA = "555b8fdd7cc817ae5f729762913c5f8205e503a28170bad86a8a0f66e4c93907"
PAGES = range(82, 120)

U, R, T, B, K = "UGA", "RWA", "TZA", "BDI", "KEN"
NOMS = {"Uganda": U, "Rwanda": R, "Tanzania": T, "Burundi": B, "Kenya": K}

#: notice : (titre, États, taux unique de la liste ou None)
NOTICES = {
    "162": ("Approved Duty Remission on Raw Materials and Inputs for the Manufacture of Goods for the Republic of Uganda", [U], None),
    "163": ("Approved Duty Remission on Raw Materials and Inputs for the Manufacture of Furniture for the Republic of Rwanda and the Republic of Uganda", None, None),
    "164": ("Approved Duty Remission on Raw Materials and Inputs for the Manufacture of Garments and Other Made Up Textile Products for the Republic of Burundi, Republic of Rwanda, United Republic of Tanzania and the Republic of Uganda", [B, R, T, U], None),
    "165": ("Approved Duty Remission on Raw Materials and Inputs for the Manufacture of Garments and Other Made Up Textile Products for the Republic of Rwanda", [R], 0),
    "166": ("Approved Duty Remission on Raw Materials and Inputs for the Manufacture of Garments and Other Made Up Textile Products for the Republic of Uganda", [U], None),
    "167": ("Approved Duty Remission on Raw Materials and Inputs for the Manufacture of Garments and Other Made Up Textile Products for the United Republic of Tanzania", [T], None),
    "168": ("Approved Duty Remission on Raw Materials and Inputs for the Manufacture of Garments and Other Made Up Textile Products for the Republic of Kenya", [K], None),
    "169": ("Approved Duty Remission on Raw Materials and Inputs for the Manufacture of Footwear (Shoes) for the Republic of Rwanda", [R], 0),
    "170": ("Approved Duty Remission on Raw Materials and Inputs for the Manufacture of Footwear (Shoes) for the Republic of Uganda", [U], None),
    "171": ("Approved Duty Remission on Raw Materials and Inputs for the Manufacture of Footwear (Shoes) for the United Republic of Tanzania", [T], None),
    "172": ("Approved Duty Remission on Raw Materials and Inputs for the Manufacture of Goods for the Republic of Burundi", [B], None),
    "173": ("Approved Duty Remission on Raw Materials and Inputs for the Manufacture of Goods for the Republic of Rwanda", [R], 0),
}

#: Numéros de ligne fautifs dans la gazette, gardés tels quels dans la référence.
SIC = {("172", "2296"): "S/N 296", ("172", "141", "4823.20.00"): "S/N 142"}

#: Codes publiés absents du TEC 2022 servi (subdivisés depuis) : portés sur les
#: lignes nationales qui les remplacent, sauf celles dont le droit servi est déjà
#: inférieur au taux de remise (la remise y relèverait le droit).
SUBDIVISES = {
    ("167", "4821.10.00"): ["48211010", "48211090"],
    ("170", "6406.10.00"): ["64061010", "64061090"],
    ("172", "2106.90.90"): ["21069099"],
    ("172", "4804.19.00"): ["48041910", "48041990"],
    ("172", "4811.59.00"): ["48115910", "48115990"],
    ("172", "4821.10.00"): ["48211090"],
    ("173", "2106.90.90"): ["21069091", "21069092", "21069099"],
}

#: Lignes non intégrées, et pourquoi.
ECARTEES = {
    ("172", "2106.90.20"): "remise à 10 % sur une ligne au TEC de 0 % : elle relèverait le droit",
    ("172", "7217.10.00"): "remise à 10 % sur une ligne que l'EAC/160/2026 porte à 0 % au Burundi : elle relèverait le droit",
    ("172", "3402.19.00"): "code du SH 2017, sans ligne unique au SH 2022 (3402.3x et 3402.4x)",
    ("173", "1701.99.20"): "« Other sugar for industrial use » : aucune ligne du TEC 2022 servi ne porte ce code, le rattachement serait une supposition",
}


def lignes():
    """(notice, S/N, codes, désignation, taux ou décision, titre du tableau), dans l'ordre du PDF."""
    doc = pymupdf.open(PDF)
    notice, sortie = None, []
    for pno in PAGES:
        page = doc[pno - 1]
        debuts = [(b[1], re.search(r"EAC/(\d+)/2026", b[4]).group(1))
                  for b in page.get_text("blocks") if re.search(r"Legal Notice No\. EAC/\d+/2026", b[4])]
        for table in page.find_tables().tables:
            courante = notice
            for y, n in debuts:
                if y < table.bbox[1]:
                    courante = n
            for r in table.extract():
                r = [" ".join((c or "").split()) for c in r]
                if r[0].startswith(("REPUBLIC", "UNITED")):
                    titre = r[0]
                    continue
                if r[0].replace(" ", "") == "S/N":
                    continue
                taux = r[3] if len(r) > 3 else ""
                if re.fullmatch(r"\d+\.?", r[0]):
                    sortie.append([courante, r[0].rstrip("."), r[1].split(), r[2], taux, titre])
                elif r[0] == "" and sortie and sortie[-1][0] == courante:
                    sortie[-1][2] += r[1].split()
                    sortie[-1][3] = " ".join(filter(None, (sortie[-1][3], r[2])))
                    sortie[-1][4] = " ".join(filter(None, (sortie[-1][4], taux)))
                else:
                    raise ValueError(f"ligne non rattachée, p. {pno} : {r}")
        for _, n in debuts:
            notice = n
    return [ligne for ligne in sortie if ligne[0] in NOTICES]


def mesures_162_173():
    mesures = []
    for notice, sn, codes, desc, taux, titre in lignes():
        _, etats, unique = NOTICES[notice]
        condition = titre
        if notice == "163":
            # « Granted Uganda and Rwanda a duty remission on inputs for manufacture of furniture at 10% for one year »
            etats = [NOMS[e] for e in re.findall(r"Uganda|Rwanda", taux.split(" a duty")[0])]
            condition, taux = taux, re.search(r"at (\d+)%", taux).group(1) + "%"
        if unique is not None:
            par_code = [unique] * len(codes)
        else:
            par_code = [float(t) for t in re.findall(r"(\d+(?:\.\d+)?)%", taux)]
            if len(par_code) == 1:
                par_code *= len(codes)
        if len(par_code) != len(codes) or not etats:
            raise ValueError(f"EAC/{notice} S/N {sn} : {codes} {taux!r}")
        for publie, t in zip(codes, par_code):
            if (notice, publie) in ECARTEES:
                continue
            ref = SIC.get((notice, sn)) or SIC.get((notice, sn, publie))
            ref = f"S/N {sn}" + (f" [sic, {ref}]" if ref else "")
            remplacants = SUBDIVISES.get((notice, publie))
            for code, etat in [(c, e) for c in remplacants or [publie.replace(".", "")] for e in etats]:
                mesures.append({
                    "measure_id": f"EAC-{notice}-2026-REMISSION-{code}-{etat}-S{sn}",
                    "jurisdiction": etat,
                    "measure_type": "DUTY_REMISSION",
                    "legal_title": NOTICES[notice][0],
                    "gazette_number": f"EAC Gazette Vol. AT 1 No. 16; Legal Notice EAC/{notice}/2026",
                    "gazette_date": "2026-06-30",
                    "legal_reference": f"Legal Notice EAC/{notice}/2026, {ref}",
                    "publication_url": URL,
                    "source_hash": SHA,
                    "effective_from": "2026-07-01",
                    "effective_to": "2027-06-30",
                    "hs_code_from": code,
                    "hs_code_to": code,
                    "hs_version": "HS2022",
                    "product_description": desc + (
                        f" ({publie} publié, subdivisé au TEC 2022 : ligne {code})" if remplacants else ""),
                    "base_rate": None,
                    "override_rate": float(t),
                    "rate_unit": "%",
                    "beneficiary": "MANUFACTURER",
                    "origin_scope": "ALL",
                    "import_purpose": None,
                    "quantity_limit": None,
                    "condition_text": condition,
                    "verification_status": "VERIFIED_OFFICIAL_EXTRACT",
                    "requires_human_review": False,
                })
    return mesures


if __name__ == "__main__":
    resultat = mesures_162_173()
    with open(sys.argv[1], "w", encoding="utf-8") as f:
        json.dump(resultat, f, ensure_ascii=False, indent=2)
    print(len(resultat), "mesures")

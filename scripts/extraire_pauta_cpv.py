"""Lit la Pauta Aduaneira du Cap-Vert et ses deux modifications, et en tire, par
position nationale à dix chiffres, le libellé, le droit d'importation (DI), la
taxa comunitária CEDEAO (TC), l'ICE ad valorem, l'IVA et la taxe spécifique
d'ICE par véhicule.

Chaîne appliquée, dans cet ordre :

1. Pauta Aduaneira 2022 (SH 2017), 239 pages, colonnes DI, TC, ICE, IVA lues
   par position horizontale ; « Is » en colonne IVA = isento (0), ICE vide =
   pas d'ICE.
2. Lei n.º 51/X/2025 (B.O. I série n.º 30, 17/04/2025), annexe : SH 2022.
   Chaque ligne « XXXX.XX.XX nn » porte U.C., Cl., DI, ICE, IVA ; une ligne
   « Suprimida » retire la position, les autres la créent ou la remplacent.
   « L » en colonne DI vaut 0 (les lignes « aeronaves civis » supprimées y
   portent « L » là où la Pauta 2022 imprime 0). La TC n'y figure pas : elle
   reste celle de la Pauta, 0,5 % sur toutes les positions.
3. Lei n.º 69/X/2025 (OE 2026) : annexe III (art. 94, adoption progressive du
   TEC) remplace le DI des positions listées ; annexe II (art. 89) fixe l'ICE
   spécifique en CVE par unité des véhicules neufs et d'occasion de 4 ans au plus.

    python3 scripts/extraire_pauta_cpv.py <pauta2022.pdf> <lei51.pdf> <oe2026.pdf> <sortie.json>
"""
import json
import re
import sys

import pymupdf

CODE10 = re.compile(r"^\d{10}$")


def taux(texte):
    texte = texte.strip()
    if texte in ("", None):
        return None
    if texte.upper() in ("IS", "L"):
        return 0.0
    return float(texte.replace(",", "."))


def pauta_2022(chemin):
    sortie = {}
    for page in pymupdf.open(chemin):
        mots = page.get_text("words")
        codes = sorted((m for m in mots if CODE10.match(m[4]) and m[0] < 100), key=lambda m: m[1])
        for k, c in enumerate(codes):
            ligne = sorted((m for m in mots if abs(m[1] - c[1]) < 3), key=lambda m: m[0])
            col = {k: " ".join(m[4] for m in ligne if lo <= m[0] < hi) for k, (lo, hi) in {
                "DI": (520, 575), "TC": (575, 620), "ICE": (620, 670), "IVA": (670, 760)}.items()}
            # Le libellé peut déborder sur les lignes suivantes, jusqu'au code suivant.
            fin = codes[k + 1][1] - 3 if k + 1 < len(codes) else c[1] + 40
            libelle = " ".join(m[4] for m in sorted(
                (m for m in mots if 120 < m[0] < 520 and c[1] - 3 < m[1] < fin), key=lambda m: (round(m[1]), m[0])))
            sortie[c[4]] = {
                "_libelle": libelle, "DI": taux(col["DI"]), "TC": taux(col["TC"]),
                "ICE": taux(col["ICE"]), "IVA": taux(col["IVA"]), "_origine": ["Pauta 2022"],
            }
    return sortie


INTERTITRES = {"Subposição", "Subposições", "Posição", "Nova", "Inserir", "Subdividir", "CAPITULO", "CAPÍTULO", "Nota"}


def lei_51(chemin):
    lignes = []
    for page in pymupdf.open(chemin):
        mots = page.get_text("words")
        codes = [m for m in mots if re.fullmatch(r"\d{4}\.\d{2}\.\d{2}", m[4]) and m[0] < 60]
        rangs = sorted((m for m in mots if re.fullmatch(r"\d{2}", m[4]) and 100 < m[0] < 120), key=lambda m: m[1])
        for k, z in enumerate(rangs):
            c = min(codes, key=lambda c: abs(c[1] - z[1]), default=None)
            if c is None or abs(c[1] - z[1]) > 10:
                continue
            ligne = sorted((m for m in mots if abs(m[1] - z[1]) < 3), key=lambda m: m[0])
            col = {k: " ".join(m[4] for m in ligne if lo <= m[0] < hi) for k, (lo, hi) in {
                "DI": (447, 475), "ICE": (475, 505), "IVA": (505, 535)}.items()}
            libelle = " ".join(m[4] for m in ligne if 130 < m[0] < 380)
            if not libelle:
                # Libellé imprimé sous la ligne des taux (1901.90.10 à .99,
                # 2008.93, 9705.29) : lu jusqu'à la ligne suivante ou au
                # prochain intertitre de l'annexe.
                fin = rangs[k + 1][1] - 3 if k + 1 < len(rangs) else z[1] + 120
                suite = []
                for y in sorted({round(m[1]) for m in mots if z[1] + 3 < m[1] < fin and 130 < m[0] < 380}):
                    mots_ligne = sorted((m for m in mots if abs(m[1] - y) < 2 and 130 < m[0] < 380), key=lambda m: m[0])
                    # Un tiret ouvre l'intertitre du groupe suivant (« -- Outros »).
                    if mots_ligne[0][4] in INTERTITRES or (suite and mots_ligne[0][4].startswith("-")):
                        break
                    suite += [m[4] for m in mots_ligne]
                libelle = " ".join(suite)
            lignes.append({
                "code": c[4].replace(".", "") + z[4], "supprimee": "suprimid" in libelle.lower(),
                "_libelle": libelle.lstrip("- "), "DI": taux(col["DI"]), "ICE": taux(col["ICE"]),
                "IVA": taux(col["IVA"]),
            })
    return lignes


def annexe_oe(document, premiere_page):
    """Annexes II et III de l'OE 2026 : code, libellé, U.C., valeur."""
    lignes = []
    for n in range(premiere_page, len(document)):
        texte = document[n].get_text()
        if n > premiere_page and (texte.lstrip().startswith("Anexo") or not re.search(r"^\d{10}", texte, re.M)):
            break
        lignes += [ligne.strip() for ligne in texte.split("\n") if ligne.strip()]
    debuts = [i for i, ligne in enumerate(lignes) if re.match(r"^\d{10}\b", ligne)]
    sortie = {}
    for k, i in enumerate(debuts):
        segment = lignes[i:debuts[k + 1] if k + 1 < len(debuts) else len(lignes)]
        valeurs = [s for s in segment[1:] if re.fullmatch(r"\d{1,3}(?: \d{3})*", s)]
        if valeurs:
            sortie[segment[0][:10]] = float(valeurs[0].replace(" ", ""))
    return sortie


def page_de(document, titre):
    return next(n for n, page in enumerate(document) if page.get_text().lstrip().split("\n")[0].strip() == titre)


pauta = pauta_2022(sys.argv[1])
suppressions = creations = 0
for ligne in lei_51(sys.argv[2]):
    code = ligne.pop("code")
    if ligne.pop("supprimee"):
        suppressions += pauta.pop(code, None) is not None
        continue
    ancien = pauta.get(code, {})
    creations += not ancien
    pauta[code] = {**ligne, "TC": 0.5, "_origine": ancien.get("_origine", []) + ["Lei 51/X/2025"]}

oe = pymupdf.open(sys.argv[3])
di_oe = annexe_oe(oe, page_de(oe, "Anexo III"))
ice_vehicules = annexe_oe(oe, page_de(oe, "Anexo II"))
absents = []
for code, di in di_oe.items():
    if code not in pauta:
        absents.append(code)
        continue
    pauta[code]["DI"] = di
    pauta[code]["_origine"].append("OE 2026, anexo III")
for code, montant in ice_vehicules.items():
    if code not in pauta:
        absents.append(code)
        continue
    if montant:
        pauta[code]["ICE_CVE_U"] = montant
        pauta[code]["_origine"].append("OE 2026, anexo II")

sans_libelle = [code for code, v in pauta.items() if not v["_libelle"].strip()]
assert not sans_libelle, f"positions sans libellé : {sans_libelle}"
json.dump(pauta, open(sys.argv[4], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(len(pauta), "positions ;", suppressions, "supprimées et", creations, "créées par la Lei 51 ;",
      len(di_oe), "DI de l'annexe III ;", sum(1 for v in ice_vehicules.values() if v), "ICE spécifiques ;",
      "absents de la Pauta :", absents)

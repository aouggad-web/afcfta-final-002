"""Lit le tarif douanier officiel de la Somalie (ministère des Finances,
« Somali Customs Tariff 2022 », Mogadiscio, mai 2022, 323 pages) et en fait
l'artefact canonique backend/data/crawled/SOM_tariffs.json, scellé (backend/crawlers/integrity) ;
l'empreinte du fichier est à reporter dans backend/data/source_registry_v2.json.

Le texte est lu par `pdftotext -layout` (poppler). Chaque position à huit
chiffres (« 0101 21 00 ») porte, en fin de ligne ou sur l'une des trois lignes
suivantes quand le libellé est long, l'unité statistique et le droit
d'importation de la colonne 4 (« 25 % »). Le droit est un droit ad valorem sur
la valeur en douane (fiche SOM_assiette_DD_2026-09-17.json).

Sans taux : « – » (porc, boissons alcoolisées, soies de porc : 41 positions),
« TBD % » (4 positions du 12.09) et « (y) » (03.02.39) — le tarif n'en publie
pas ; le droit est porté sans taux.

Le libellé est celui de la ligne, précédé de l'intitulé de la position à
quatre chiffres et des intitulés de groupe (« – Other fresh eggs ») dont il
dépend : « – – Other » seul ne dit rien.

    python3 scripts/convertir_tarif_som.py <Somali_Customs_Tariff_Final.pdf>
"""
import datetime
import hashlib
import json
import os
import re
import subprocess
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RACINE, "backend"))
from crawlers.integrity import seal_crawled_file  # noqa: E402

SORTIE = os.path.join(RACINE, "backend", "data", "crawled", "SOM_tariffs.json")
URL = "https://mof.gov.so/sites/default/files/Publications/Somali_Customs_Tariff_Final.pdf"
PAGE = "https://mof.gov.so/publications/somali-customs-tariff-2022"

CODE = re.compile(r"^\s*(\d{4} \d{2} \d{2})\s+(.*)$")
POSITION = re.compile(r"^\s*(\d{4})\s{3,}(\S.*)$")
GROUPE = re.compile(r"^\s+((?:–\s*)+)(\S.*)$")
TAUX = re.compile(r"\s{2,}(\d+(?:[.,]\d+)?\s*%|–|-|TBD\s*%|\(y\))\s*$")
COLONNES = re.compile(r"\s{3,}\S.*$")
TIRETS = re.compile(r"^((?:–\s*)*)(.*)$")


def _texte(ligne):
    """Le libellé seul : sans l'unité ni le taux portés à droite."""
    return COLONNES.sub("", ligne.strip()).strip()


def _joindre(morceaux):
    """Les lignes d'un libellé replié, sans espace après une coupure « plant- »."""
    texte = ""
    for morceau in filter(None, morceaux):
        texte += morceau if not texte or texte.endswith("-") else " " + morceau
    return texte


def _niveau(libelle):
    tirets, reste = TIRETS.match(libelle).groups()
    return tirets.count("–"), reste.strip()


def lire(lignes):
    # Dès l'intitulé de la position 01.01 : ses lignes (« – Horses ») en dépendent.
    debut = next(i for i, ligne in enumerate(lignes) if re.match(r"^0101\s{3,}\S", ligne))
    positions, intitule, groupes = {}, "", {}
    i = debut
    while i < len(lignes):
        ligne = lignes[i]
        m = CODE.match(ligne)
        if not m:
            p = POSITION.match(ligne)
            g = GROUPE.match(ligne)
            if p or (g and not TAUX.search(ligne)):
                suite = [_texte((p or g).group(2))]
                while i + 1 < len(lignes) and re.match(r"^\s{6,}[^\s–]", lignes[i + 1]) \
                        and not CODE.match(lignes[i + 1]) and not TAUX.search(lignes[i + 1]):
                    i += 1
                    suite.append(_texte(lignes[i]))
                if p:
                    intitule, groupes = _joindre(suite), {}
                else:
                    niveau = g.group(1).count("–")
                    groupes = {n: t for n, t in groupes.items() if n < niveau}
                    groupes[niveau] = _joindre(suite)
            i += 1
            continue
        code = m.group(1).replace(" ", "")
        taux = TAUX.search(ligne)
        libelle = [_texte(m.group(2))]
        j = i + 1
        while j < len(lignes) and j <= i + 3 and lignes[j].strip() and not CODE.match(lignes[j]) \
                and not POSITION.match(lignes[j]) and not GROUPE.match(lignes[j]):
            if not taux:
                taux = TAUX.search(lignes[j])
            # Une ligne qui ne porte que l'unité et le taux (colonnes 3 et 4) n'a pas de libellé.
            texte = "" if len(lignes[j]) - len(lignes[j].lstrip()) > 40 else _texte(lignes[j])
            if texte:
                libelle.append(texte)
            j += 1
        if not taux:
            raise SystemExit(f"{code} : droit introuvable")
        brut = taux.group(1).replace(" ", "")
        niveau, propre = _niveau(_joindre(libelle))
        chaine = [groupes[n] for n in sorted(groupes) if n < niveau] if niveau else []
        designation = " — ".join(t for t in [intitule if niveau else "", *chaine, propre] if t)
        positions[code] = {
            "designation": designation,
            "taux": float(brut.rstrip("%").replace(",", ".")) if brut[0].isdigit() else None,
            "brut": brut,
        }
        i = j
    return positions


def main(pdf):
    texte = subprocess.run(["pdftotext", "-layout", pdf, "-"], check=True, capture_output=True, text=True).stdout
    lues = lire(texte.split("\n"))
    pdf_sha = hashlib.sha256(open(pdf, "rb").read()).hexdigest()
    positions = []
    for code, v in sorted(lues.items()):
        detail = [{"tax_code": "DD", "tax_name": "Droit de douane (tarif douanier somalien 2022)", "rate": v["taux"],
                   "rate_type": "ad_valorem", "base": "CIF"}]
        if v["taux"] is None:
            detail[0]["observation"] = f"Colonne 4 du tarif : « {v['brut']} » — aucun taux publié."
        positions.append({
            "code": f"{code[:4]}.{code[4:6]}.{code[6:]}", "code_clean": code, "code_length": 8,
            "designation": v["designation"], "chapter": code[:2], "hs2": code[:2], "hs4": code[:4],
            "hs6": code[:6], "taxes": {"DD": v["taux"]}, "taxes_detail": detail,
            "source": "mof.gov.so", "data_type": "national",
        })
    artefact = {
        "country": "SOM", "country_name": "Somalie", "source": "mof.gov.so", "source_url": PAGE,
        "method": "pdf_officiel", "hs_level": "national_sub_positions",
        "nomenclature": "Somali Customs Tariff 2022 (SH 2017), ministère des Finances",
        "data_type": "national", "currency": "USD",
        "extracted_at": datetime.datetime.now(datetime.timezone.utc).isoformat(), "total_positions": len(positions),
        "source_document": {
            "titre": "Federal Government of Somalia, Ministry of Finance — Somali Customs Tariff 2022, Mogadishu May 2022",
            "url": URL, "pages": 323, "sha256": pdf_sha,
            "lecture": "pdftotext -layout ; colonne 4 (Import duty rates) lue en fin de ligne de la position ou sur les "
                       "trois lignes suivantes (scripts/convertir_tarif_som.py)",
        },
        "notes": [
            "Tarif national de la Somalie à la place du TEC de l'EAC 2022, que la Somalie n'applique pas.",
            "Droit ad valorem sur la valeur en douane ; pas de taux publié sur 46 positions (« – », « TBD % », « (y) »).",
            "Taxe sur les ventes à l'importation non portée : aucun texte publiant son taux (fiche SOM_taux_TVA_2026-09-18.json).",
        ],
        "positions": positions,
    }
    with open(SORTIE, "w", encoding="utf-8") as f:
        json.dump(artefact, f, ensure_ascii=False, indent=2)
    print(len(positions), seal_crawled_file(SORTIE, PAGE).file_hash)


if __name__ == "__main__":
    main(sys.argv[1])

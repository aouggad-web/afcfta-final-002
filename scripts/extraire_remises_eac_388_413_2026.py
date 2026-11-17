"""Remises de droits des Legal Notices EAC/388 à EAC/413/2026 (EAC Gazette Vol. AT 1
No. 31 du 12/11/2026), pour data/eac/legal_overrides.json.

Ce sont des remises accordées au Kenya à des fabricants (ou meuniers, assembleurs)
NOMMÉS, pour des quantités et des produits finis fixés : une ligne du tableau (S/N)
porte une société et un ou plusieurs codes, avec la quantité allouée et le produit fini.
La remise ne vaut donc que pour ces sociétés et ces quantités : le moteur
(engine/legal_override_engine.py) ne l'applique qu'avec une autorisation datée qui nomme
la ligne exacte ; sans elle, le droit du TEC reste dû et la note dit à quelles
conditions la remise s'appliquerait. Aucune de ces mesures n'écrase le tarif de base ni
la préférence ZLECAf du couloir.

Les tableaux sont lus dans le PDF déposé
(data/sources/eac/official/EAC_Vol_AT_1_No_31_2026-11-12.pdf) avec pymupdf.find_tables.
Le script contrôle sa lecture contre le texte des pages : la suite des codes SH de chaque
notice, la société et la quantité de chaque ligne doivent y figurer.

Dates : « for twelve (12) months » ne dit pas à partir de quand ; la date de la gazette
(12/11/2026) est retenue comme début, le plus tardif des débuts possibles, donc la
remise n'est jamais tenue pour effective avant sa publication. « Up to 30th June, 2027 » se
lit comme une échéance.

Lignes non intégrées (écartées, avec leur motif) : celles dont le code est absent du TEC
servi pour le Kenya (le rattachement serait une supposition) et celles dont le droit servi
est déjà inférieur ou égal au taux de la remise (elle ne l'abaisserait pas, ou le
relèverait) ; ce contrôle lit backend/socle/KEN.json (python3 scripts/build_socle.py KEN).

    python3 scripts/extraire_remises_eac_388_413_2026.py <lignes.json> <mesures.json> <ecartees.json>
    python3 scripts/extraire_remises_eac_388_413_2026.py --integrer
        (met à jour data/eac/legal_overrides.json et data/eac/eac_gazette_register.json, sans doublon)
"""
import json
import os
import re
import sys
from datetime import date, timedelta

import pymupdf

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDF = os.path.join(REPO, "data", "sources", "eac", "official", "EAC_Vol_AT_1_No_31_2026-11-12.pdf")
SOCLE_KEN = os.path.join(REPO, "backend", "socle", "KEN.json")
URL = ("https://www.eac.int/documents?Itemid=297&controller=download&file=00c004d5-31e4-4b6d-9dd0-01268535905f"
       "&name=EAC+Vol.+AT+1+NO.+31+NOVEMBER+2026.pdf.pdf&task=download.file")
SHA = "794d16f3e5716c299ac9f99a5ccb257b3dab5eb915fc89990473aa1bf47d5850"
DATE_GAZETTE = date(2026, 11, 12)
DATE_VERIFICATION = "2026-11-17"
ECHEANCE_FIN_JUIN = date(2027, 6, 30)
PAGES = range(4, 38)
NOTICES = range(388, 414)

CODE = re.compile(r"\d{4}\.\d{2}\.\d{2}")
TAUX = {"zero": 0.0, "ten": 10.0}
BENEFICIAIRES = {"MANUFACTURER": "fabricant", "MILLER": "meunier", "ASSEMBLER": "assembleur"}


def nettoyer(texte):
    """Texte d'une cellule : césures « \xad » recollées, espaces réduits."""
    return " ".join(re.sub("\xad\\s*", "", texte or "").split())


def quantite(brut, unite=None):
    """« 2, 200 » vaut 2200 ; « 18.2 » vaut 18.2 ; « 1, 500 UNITS » vaut 1500 quand la colonne
    d'unité dit UNITS ; rien ne se devine."""
    brut = nettoyer(brut)
    if unite and brut.endswith(" " + unite):
        brut = brut[: -len(unite) - 1]
    if not re.fullmatch(r"\d+(?:, ?\d{3})*(?:\.\d+)?", brut):
        return None
    return float(brut.replace(", ", "").replace(",", ""))


def beneficiaire(titre):
    titre = titre.upper()
    if "MILLERS" in titre:
        return "MILLER"
    if "ASSEMBLERS" in titre or "ASSEMBLY" in titre:
        return "ASSEMBLER"
    return "MANUFACTURER"


def lire():
    """(notices, lignes) lus dans le PDF : notices {n: titre, taux, échéance, condition} et
    lignes [{notice, rang, sn, société, code, désignation, quantité, unité, produit fini}]."""
    doc = pymupdf.open(PDF)
    textes = {}
    notices, lignes = {}, []
    courante, etat = None, {}
    for pno in PAGES:
        page = doc[pno - 1]
        debuts = [(b[1], int(re.search(r"EAC\s*/\s*(\d+)\s*/\s*2026", b[4]).group(1)))
                  for b in page.get_text("blocks") if re.search(r"Legal Notice No\. EAC\s*/\s*\d+\s*/\s*2026", b[4])]
        for _, n in debuts:
            notices.setdefault(n, {})
        textes.setdefault(debuts[0][1] if debuts else courante, []).append(page.get_text())
        for table in page.find_tables().tables:
            n = courante
            for y, no in debuts:
                if y < table.bbox[1]:
                    n = no
            rows = [[nettoyer(c) for c in r] for r in table.extract()]
            entete = rows[0]
            if not entete[0].replace(" ", "") == "S/N":
                raise ValueError(f"p. {pno} : tableau sans en-tête S/N : {entete}")
            avec_unite = len(entete) == 7
            # Un tableau se poursuit sur la page suivante : la société et le produit fini en cours
            # restent ceux de la notice jusqu'au prochain S/N.
            societe, produit = etat.get(n, (None, None))
            for r in rows[1:]:
                sn, soc, code, desc = r[0], r[1], r[2], r[3]
                if not CODE.fullmatch(code):
                    raise ValueError(f"p. {pno}, EAC/{n} : ligne sans code SH lisible : {r}")
                if sn:
                    societe, produit = soc, None
                elif soc:
                    # Le nom d'une société peut se poursuivre sur la ligne de code suivante
                    # (« Black Petals » puis « Limited ») : le tableau le coupe par ligne.
                    societe = f"{societe} {soc}"
                if r[-1]:
                    produit = r[-1]
                unite = r[5] if avec_unite else ("MT" if "Metric Tons" in entete[4] else entete[4])
                lignes.append({
                    "notice": n, "sn": sn or lignes[-1]["sn"], "societe": societe, "code": code,
                    "designation": desc, "quantite": quantite(r[4], unite), "quantite_brute": r[4],
                    "unite": unite,
                    "produit_fini": produit,
                })
            etat[n] = (societe, produit)
        for _, n in debuts:
            courante = n
    # Une société dont le nom se poursuit sur la ligne de code suivante garde son nom entier
    # sur toutes ses lignes (le dernier état d'un S/N est le nom complet).
    noms = {(ligne["notice"], ligne["sn"]): ligne["societe"] for ligne in lignes}
    for ligne in lignes:
        ligne["societe"] = noms[(ligne["notice"], ligne["sn"])]
    return notices, lignes, textes


def metadonnees(doc, notices):
    """Titre, taux, échéance et condition de chaque notice, lus dans son texte."""
    toutes = "\n".join(p.get_text() for p in doc)
    morceaux = re.split(r"(?=Legal Notice No\. EAC\s*/\s*\d+\s*/\s*2026)", toutes)
    for morceau in morceaux:
        m = re.match(r"Legal Notice No\. EAC\s*/\s*(\d+)\s*/\s*2026", morceau)
        if not m or int(m.group(1)) not in NOTICES:
            continue
        n = int(m.group(1))
        plat = nettoyer(morceau)
        titre = re.search(r"APPROVED DUTY REMISSION .*? FOR KENYA", plat).group(0)
        taux = re.search(r"duty rate of (zero|ten) percent \((\d+)%\)", plat, re.I)
        if not taux or TAUX[taux.group(1).lower()] != float(taux.group(2)):
            raise ValueError(f"EAC/{n} : taux illisible")
        douze = re.search(r"(?:for|to be imported for) twelve(?: \(12\))? months", plat, re.I)
        fin_juin = re.search(r"up to 30th June, 2027", plat, re.I)
        if bool(douze) == bool(fin_juin):
            raise ValueError(f"EAC/{n} : durée ambiguë")
        condition = re.search(r"Condition of remission of import duty (.*?) (?:RT\. HON\.|$)", plat)
        notices[n] = {
            "titre": titre, "taux": float(taux.group(2)),
            "echeance": "12 mois" if douze else "30 juin 2027",
            "condition": condition.group(1) if condition else None,
        }
    return notices


def controler(lignes, notices, doc):
    """La lecture doit retrouver, notice par notice, les codes, sociétés et quantités du texte."""
    toutes = "\n".join(p.get_text() for p in doc)
    toutes_plat = " ".join(re.sub("\xad\\s*", "", toutes).split())
    morceaux = re.split(r"(?=Legal Notice No\. EAC\s*/\s*\d+\s*/\s*2026)", toutes)
    attendus = {}
    for morceau in morceaux:
        m = re.match(r"Legal Notice No\. EAC\s*/\s*(\d+)\s*/\s*2026", morceau)
        if m and int(m.group(1)) in NOTICES:
            attendus[int(m.group(1))] = CODE.findall(morceau)
    assert sorted(attendus) == list(NOTICES), sorted(attendus)
    for n in NOTICES:
        lus = [ligne["code"] for ligne in lignes if ligne["notice"] == n]
        assert lus == attendus[n], f"EAC/{n} : codes lus {lus} ≠ codes du texte {attendus[n]}"
    for ligne in lignes:
        assert ligne["quantite"] is not None or not ligne["quantite_brute"], ligne
        assert ligne["societe"] and ligne["produit_fini"], ligne
        # Chaque mot de la société figure dans le texte (un nom coupé sur deux lignes du
        # tableau n'est pas contigu dans le texte de la page).
        assert all(mot in toutes_plat for mot in ligne["societe"].split()), ligne
    return len(lignes)


def ecarter_ou_retenir(lignes):
    """(retenues, écartées avec motif) selon le TEC servi pour le Kenya."""
    with open(SOCLE_KEN, encoding="utf-8") as f:
        positions = json.load(f)["positions"]
    retenues, ecartees = [], []
    for ligne in lignes:
        code = ligne["code"].replace(".", "")
        position = positions.get(code)
        if position is None:
            ecartees.append(dict(ligne, motif="code absent du TEC servi pour le Kenya : le rattachement à une ligne serait une supposition"))
            continue
        dd = next((d for d in position.get("droits") or [] if d.get("code") == "DD"), None)
        servi = dd.get("taux") if dd else None
        if servi is None:
            ecartees.append(dict(ligne, motif="droit servi sans taux ad valorem : la remise ne se compare pas"))
        elif servi <= ligne["taux"]:
            ecartees.append(dict(ligne, motif=f"droit servi de {servi:g} % : la remise à {ligne['taux']:g} % ne l'abaisserait pas"))
        else:
            retenues.append(dict(ligne, droit_servi=servi))
    return retenues, ecartees


def mesures(retenues, notices):
    sortie = []
    rang = {}
    for ligne in retenues:
        n = ligne["notice"]
        notice = notices[n]
        rang[n] = rang.get(n, 0) + 1
        code = ligne["code"].replace(".", "")
        fin = ECHEANCE_FIN_JUIN if notice["echeance"] == "30 juin 2027" else DATE_GAZETTE.replace(year=2027) - timedelta(days=1)
        benef = beneficiaire(notice["titre"])
        quantite_texte = (
            f"{ligne['quantite']:g} {ligne['unite']}" if ligne["quantite"] is not None else "non indiquée")
        condition = (
            f"{BENEFICIAIRES[benef].capitalize()} kényan nommé par la gazette : {ligne['societe']} ; produit fini : "
            f"{ligne['produit_fini']} ; quantité allouée : {quantite_texte} (S/N {ligne['sn']}). "
            f"Remise de {notice['taux']:g} % valable {'douze mois' if notice['echeance'] == '12 mois' else 'jusqu’au 30 juin 2027'}"
            + (" à compter d'une date que l'avis ne fixe pas (la date de la gazette est retenue)." if notice["echeance"] == "12 mois" else ".")
        )
        if notice["condition"]:
            condition += " Condition de la notice : " + notice["condition"]
        sortie.append({
            "measure_id": f"EAC-{n}-2026-REMISSION-{code}-KEN-S{ligne['sn']}-{rang[n]}",
            "jurisdiction": "KEN",
            "measure_type": "DUTY_REMISSION",
            "legal_title": notice["titre"],
            "gazette_number": f"EAC Gazette Vol. AT 1 No. 31; Legal Notice EAC/{n}/2026",
            "gazette_date": DATE_GAZETTE.isoformat(),
            "legal_reference": f"Legal Notice EAC/{n}/2026",
            "publication_url": URL,
            "source_hash": SHA,
            "effective_from": DATE_GAZETTE.isoformat(),
            "effective_to": fin.isoformat(),
            "hs_code_from": code,
            "hs_code_to": code,
            "hs_version": "HS2022",
            "product_description": ligne["designation"],
            "base_rate": None,
            "override_rate": notice["taux"],
            "rate_unit": "%",
            "beneficiary": benef,
            "origin_scope": "ALL",
            "import_purpose": None,
            "quantity_limit": None,
            "named_beneficiary": ligne["societe"],
            "allocated_quantity": ligne["quantite"],
            "allocated_quantity_unit": ligne["unite"],
            "finished_product": ligne["produit_fini"],
            "condition_text": condition,
            "verification_status": "VERIFIED_OFFICIAL_EXTRACT",
            "requires_human_review": False,
        })
    return sortie


GAZETTE = "Vol. AT 1 No. 31"
MESURES_JSON = os.path.join(REPO, "data", "eac", "legal_overrides.json")
REGISTRE_JSON = os.path.join(REPO, "data", "eac", "eac_gazette_register.json")
PHRASE_PORTEE = (
    " Legal Notices EAC/388 à EAC/413/2026 (EAC Gazette Vol. AT 1 No. 31 du 12/11/2026 : remises accordées au "
    "Kenya à des fabricants, meuniers et assembleurs NOMMÉS, pour des quantités et des produits finis fixés) : "
    "{n} mesures, une par société et par code, au Kenya seul ; {e} lignes écartées (code absent du TEC servi, "
    "ou droit servi déjà inférieur ou égal à la remise)."
)


def integrer(resultat, ecartees, n_lignes):
    """Met à jour le fichier des mesures et le registre des gazettes, sans doublon."""
    with open(MESURES_JSON, encoding="utf-8") as f:
        donnees = json.load(f)
    donnees["measures"] = [m for m in donnees["measures"] if GAZETTE not in (m.get("gazette_number") or "")]
    donnees["measures"] += resultat
    donnees["as_of"] = DATE_VERIFICATION
    donnees["scope_note"] = donnees["scope_note"].split(" Legal Notices EAC/388")[0] + PHRASE_PORTEE.format(
        n=len(resultat), e=len(ecartees))
    with open(MESURES_JSON, "w", encoding="utf-8") as f:
        json.dump(donnees, f, ensure_ascii=False, indent=2)
        f.write("\n")
    with open(REGISTRE_JSON, encoding="utf-8") as f:
        registre = json.load(f)
    registre["gazettes"] = [g for g in registre["gazettes"] if g["reference"] != "EAC Gazette Vol. AT 1 No. 31"]
    registre["gazettes"].append({
        "reference": "EAC Gazette Vol. AT 1 No. 31",
        "date": DATE_GAZETTE.isoformat(),
        "territory": "Kenya",
        "measure_types": ["DUTY_REMISSION"],
        "official_url": URL,
        "official_mirror_url": None,
        "archive_path": "data/sources/eac/official/EAC_Vol_AT_1_No_31_2026-11-12.pdf",
        "sha256": SHA,
        "access_status": "DOWNLOADED_OFFICIAL",
        "extraction_status": "COMPLETE_KEN_REMISSIONS",
        "extraction_note": (
            f"Legal Notices EAC/388 à EAC/413/2026 : {n_lignes} lignes de tableau lues (société, code SH, quantité "
            f"allouée, produit fini), {len(resultat)} mesures intégrées, {len(ecartees)} lignes écartées avec leur "
            "motif. Lecture par scripts/extraire_remises_eac_388_413_2026.py, recoupée avec deux extractions "
            "indépendantes : aucune divergence sur les codes, quantités, unités et produits finis."
        ),
        "validation_status": "OFFICIAL_HASHED",
        "tariff_lines_extracted": len(resultat),
        "priority": "CURRENT_CRITICAL",
    })
    registre["as_of"] = DATE_VERIFICATION
    texte = json.dumps(registre, ensure_ascii=False, indent=2)
    # Le registre écrit ses listes de chaînes sur une ligne : on garde sa mise en forme.
    texte = re.sub(r'\[\s+("[^"\]]*"(?:,\s+"[^"\]]*")*)\s+\]',
                   lambda m: "[" + ", ".join(re.findall(r'"[^"]*"', m.group(1))) + "]", texte)
    with open(REGISTRE_JSON, "w", encoding="utf-8") as f:
        f.write(texte + "\n")


def calculer():
    doc = pymupdf.open(PDF)
    notices, lignes, _ = lire()
    notices = metadonnees(doc, notices)
    n = controler(lignes, notices, doc)
    retenues, ecartees = ecarter_ou_retenir([dict(ligne, taux=notices[ligne["notice"]]["taux"]) for ligne in lignes])
    return notices, lignes, n, mesures(retenues, notices), ecartees


if __name__ == "__main__":
    notices, lignes, n, resultat, ecartees = calculer()
    if sys.argv[1:] == ["--integrer"]:
        integrer(resultat, ecartees, n)
    else:
        for chemin, contenu in zip(sys.argv[1:4], (lignes, resultat, ecartees)):
            with open(chemin, "w", encoding="utf-8") as f:
                json.dump(contenu, f, ensure_ascii=False, indent=2)
    print(f"{n} lignes lues dans {len(notices)} notices ; {len(resultat)} mesures ; {len(ecartees)} lignes écartées")

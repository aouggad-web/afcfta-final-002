#!/usr/bin/env python3
"""Relevé des fiches officielles du tarif douanier algérien (douane.gov.dz).

Source unique des taux ad valorem, des taxes spécifiques et des formalités de
l'Algérie : la fiche « sous-position » de l'e-service de la DGD. Trois étapes,
reprenables, dont les pages brutes restent dans ``--cache`` (hors dépôt) :

  listes   racine → sections → chapitres → rangées : liste officielle des codes ;
  fiches   fiche de chaque code de la liste ;
  fichier  data/dza/releve_dgd.json — tableaux tels que publiés, une position
           par ligne. Le tableau « Avantages fiscaux » n'est pas repris : il ne
           publie ni condition ni accord, et n'est pas servi.

puis une quatrième, sans réseau, qui lit le relevé et le crawl en place :

  verser   backend/data/crawled/DZA_tariffs.json prend du relevé les taxes ad
           valorem, les formalités, la désignation et l'URL de chaque fiche ;
           les codes absents du tarif DGD en sortent. Le « ? » qui tient la
           place d'un caractère perdu à la mise en ligne est corrigé à la main,
           ligne par ligne, d'après data/dza/designations_corrigees.json. Le
           crawl est rescellé (le sceau est horodaté : relancer l'étape change
           le fichier, même à relevé égal) et son empreinte reportée au
           registre ; suit ``python scripts/build_socle.py DZA``.

Une page anti-robot du pare-feu (≈ 2,5 Ko, renvoyée en HTTP 200) n'est jamais
comptée comme lue : elle est relue après une pause croissante. TLS vérifié de
bout en bout ; le serveur DGD n'envoie pas son certificat intermédiaire
(Sectigo DV R36), fourni par data/dza/sectigo_dv_r36.crt.

Usage : python scripts/releve_dgd_dza.py {listes|fiches|fichier} --cache DOSSIER
        python scripts/releve_dgd_dza.py verser
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import gzip
import hashlib
import html
import json
import re
import ssl
import sys
import time
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
SORTIE = RACINE / "data" / "dza" / "releve_dgd.json"
INTERMEDIAIRE = RACINE / "data" / "dza" / "sectigo_dv_r36.crt"
BASE = "https://www.douane.gov.dz/spip.php"
UA = {"User-Agent": "Mozilla/5.0 (releve tarifaire, lecture seule)"}
CRAWL = RACINE / "backend" / "data" / "crawled" / "DZA_tariffs.json"
REGISTRE = RACINE / "backend" / "data" / "source_registry_v2.json"
CORRECTIONS = RACINE / "data" / "dza" / "designations_corrigees.json"
TABLEAUX = {
    "Taxes Ad-Valorem": "taxes",
    "Taxes spécifiques annexes": "taxes_specifiques",
    "Formalités Administratives Particulières": "formalites",
}


def page_anti_robot(raw: bytes) -> bool:
    return len(raw) < 6000 and (b"eval(function(p,a,c,k,e,d)" in raw or b"cookiesession" in raw)


def contexte_tls(cafile: str | None) -> ssl.SSLContext:
    ctx = ssl.create_default_context(cafile=cafile)
    ctx.load_verify_locations(cafile=str(INTERMEDIAIRE))
    return ctx


def lire(url: str, chemin: Path, ctx: ssl.SSLContext) -> dict:
    """Page relue et gardée en cache, ou l'erreur après sept essais."""
    erreur = None
    for essai in range(7):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=90, context=ctx) as r:
                raw, statut = r.read(), r.status
            if statut == 200 and not page_anti_robot(raw):
                chemin.parent.mkdir(parents=True, exist_ok=True)
                with gzip.open(chemin, "wb") as f:
                    f.write(raw)
                time.sleep(0.4)
                return {"url": url, "releve_le": datetime.now(timezone.utc).isoformat(timespec="seconds")}
            erreur = f"HTTP {statut}" + (", page anti-robot" if page_anti_robot(raw) else "")
        except Exception as exc:  # noqa: BLE001 — l'erreur est rapportée, pas avalée
            if isinstance(getattr(exc, "reason", exc), ssl.SSLCertVerificationError):
                raise  # un certificat refusé ne se répare pas en réessayant
            erreur = f"{type(exc).__name__}: {exc}"
        if essai < 6:  # pas d'attente après le dernier essai
            time.sleep(20 * (essai + 1))
    return {"url": url, "erreur": erreur}


def _liens(raw: bytes, motif: str) -> list:
    return sorted(set(re.findall(motif, raw.decode("utf-8", "replace"))))


class Liste(HTMLParser):
    """Page rangée (page=position) : une ligne par sous-position, data-href → code."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.lignes, self._ligne, self._cellule = [], None, None

    def handle_starttag(self, t, a):
        a = dict(a)
        if t == "tr":
            self._ligne = {"href": a.get("data-href"), "cellules": []}
        elif t == "td" and self._ligne is not None:
            self._cellule = ""

    def handle_endtag(self, t):
        if t == "td" and self._cellule is not None:
            self._ligne["cellules"].append(" ".join(self._cellule.split()))
            self._cellule = None
        elif t == "tr" and self._ligne is not None:
            if self._ligne["cellules"]:
                self.lignes.append(self._ligne)
            self._ligne = None

    def handle_data(self, x):
        if self._cellule is not None:
            self._cellule += x


def codes_de_la_rangee(raw: bytes) -> list:
    p = Liste()
    p.feed(raw.decode("utf-8", "replace"))
    out = []
    for ligne in p.lignes:
        m = re.search(r"sous_position=(\d+)", ligne["href"] or "")
        if m:
            out.append([m[1], ligne["cellules"][-1]])
    return out


class Fiche(HTMLParser):
    """Fiche sous-position : badge du code, désignation, tableaux (titre, lignes)."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tables = []; self._tab = None; self._row = None; self._cell = None
        self.badge = None; self._in_badge = False
        self.champs = {}; self._strong = None; self._label = None; self._champ_buf = None
        self._in_dd_sp = False; self._desig_div = False; self.designation = None; self._div_depth = 0
        self.cle = None; self._in_cle = False
    # -- tables
    def handle_starttag(self, t, a):
        a = dict(a); cls = a.get("class") or ""
        if t == "table" and cls == "table":
            self._tab = []
        elif self._tab is not None and t == "tr":
            self._flush_row(); self._row = []
        elif self._tab is not None and t in ("td", "th") and self._row is not None:
            self._cell = []
        elif self._cell is not None:
            self._cell.append(" ")
        if t == "span" and "badge" in cls.split() and "bgnd-success" in cls.split():
            self._in_badge = True; self._buf_badge = []
        if t == "span" and cls == "text-success":
            self._in_cle = True
        if t == "strong":
            self._strong = []
        if t == "div" and self._label == "Désignation du Produit" and self.designation is None:
            self._desig_div = True; self._div_depth = 1; self._buf_desig = []
        elif t == "div" and self._desig_div:
            self._div_depth += 1
        elif t == "br" and self._desig_div:
            self._buf_desig.append("\n")
        if t == "p" and self._label not in (None, "Désignation du Produit"):
            self._end_champ()
    def _flush_row(self):
        if self._row is not None and self._tab is not None:
            if self._cell is not None:
                self._row.append(" ".join("".join(self._cell).split())); self._cell = None
            if self._row: self._tab.append(self._row)
        self._row = None
    def _end_champ(self):
        if self._label and self._champ_buf is not None:
            self.champs[self._label] = " ".join("".join(self._champ_buf).split())
        self._label = None; self._champ_buf = None
    def handle_endtag(self, t):
        if self._tab is not None and t in ("td", "th") and self._cell is not None and self._row is not None:
            self._row.append(" ".join("".join(self._cell).split())); self._cell = None
        elif self._tab is not None and t == "tr":
            self._flush_row()
        elif t == "table" and self._tab is not None:
            self._flush_row()
            rows = self._tab; self._tab = None
            if rows: self.tables.append((rows[0][0], rows[1:]))
        elif self._cell is not None:
            self._cell.append(" ")
        if t == "span" and self._in_badge:
            self._in_badge = False
            if self.badge is None: self.badge = "".join(self._buf_badge).strip()
        if t == "span" and self._in_cle:
            self._in_cle = False
        if t == "strong" and self._strong is not None:
            lab = "".join(self._strong).replace(":", "").strip(); self._strong = None
            if self._label and self._label != "Désignation du Produit": self._end_champ()
            self._label = lab; self._champ_buf = []
        if t == "div" and self._desig_div:
            self._div_depth -= 1
            if self._div_depth == 0:
                self._desig_div = False
                self.designation = "\n".join(" ".join(l.split()) for l in "".join(self._buf_desig).split("\n")).strip()
                self._label = None
        if t in ("p", "dd") and self._label and self._label != "Désignation du Produit":
            self._end_champ()
    def handle_data(self, d):
        if self._cell is not None: self._cell.append(d)
        if self._in_badge: self._buf_badge.append(d)
        if self._in_cle and self.cle is None and d.strip(): self.cle = d.strip()
        if self._strong is not None: self._strong.append(d)
        elif self._desig_div: self._buf_desig.append(d)
        elif self._champ_buf is not None: self._champ_buf.append(d)



def lire_fiche(raw: bytes) -> dict:
    p = Fiche()
    p.feed(raw.decode("utf-8", "replace"))
    p.close()
    p._end_champ()
    return {"badge": p.badge or None, "designation": p.designation, "tableaux": p.tables}


def _index(chemin: Path) -> dict:
    index = {}
    if chemin.exists():
        for ligne in chemin.read_text(encoding="utf-8").splitlines():
            e = json.loads(ligne)
            if "erreur" not in e:
                index[e["cle"]] = e
    return index


def _ecrire_index(chemin: Path, e: dict) -> None:
    with chemin.open("a", encoding="utf-8") as f:
        f.write(json.dumps(e, ensure_ascii=False) + "\n")


def etape_listes(cache: Path, ctx: ssl.SSLContext) -> None:
    idx_path = cache / "index_listes.jsonl"
    deja = _index(idx_path)

    def page(cle, url, nom):
        if cle in deja:
            return deja[cle]
        e = lire(url, cache / "listes" / f"{nom}.html.gz", ctx)
        e["cle"] = cle
        if "erreur" not in e:
            _ecrire_index(idx_path, e)
        return e

    racine = page("racine", f"{BASE}?page=tarif_douanier", "racine")
    sections = _liens(gzip.open(cache / "listes" / "racine.html.gz").read(), r"page=chapitre&amp;section=(\w+)")
    chapitres = []
    for s in sections:
        page(f"section_{s}", f"{BASE}?page=chapitre&section={s}", f"section_{s}")
        raw = gzip.open(cache / "listes" / f"section_{s}.html.gz").read()
        chapitres += [(s, c) for c in _liens(raw, rf"page=range&amp;section={s}&amp;chapitre=(\d\d)")]
    rangees = []
    for s, c in chapitres:
        page(f"chapitre_{c}", f"{BASE}?page=range&section={s}&chapitre={c}", f"chapitre_{c}")
        raw = gzip.open(cache / "listes" / f"chapitre_{c}.html.gz").read()
        rangees += [(s, c, r) for r in _liens(raw, rf"page=position&amp;section=\w+&amp;chapitre={c}&amp;range=(\d\d)")]
    with cf.ThreadPoolExecutor(max_workers=3) as ex:
        lues = list(ex.map(lambda x: page(f"rangee_{x[1]}{x[2]}",
                                          f"{BASE}?page=position&section={x[0]}&chapitre={x[1]}&range={x[2]}",
                                          f"rangee_{x[1]}{x[2]}"), rangees))
    print(f"racine {racine.get('releve_le')} ; {len(sections)} sections, {len(chapitres)} chapitres, {len(rangees)} rangées")
    # Une rangée non lue retirerait ses codes de la liste officielle sans
    # qu'aucune fiche ne manque : l'étape échoue, et se relance.
    echecs = [e["url"] for e in lues if "erreur" in e]
    if echecs:
        raise SystemExit(f"{len(echecs)} rangées non lues, relancer « listes » :\n" + "\n".join(echecs))


LIBELLE = re.compile(r"<dt>(Section|Chapitre|Rangée) (\w+)<sep> :</sep></dt><dd[^>]*>(?:<a [^>]*>)?(.*?)(?:</a>)?</dd>", re.S)


def libelles_officiels(cache: Path) -> dict:
    """Libellés publiés des sections, chapitres et rangées, d'après les pages rangée."""
    out = {"sections": {}, "chapitres": {}, "rangees": {}}
    for cle in sorted(_index(cache / "index_listes.jsonl")):
        if cle.startswith("rangee_"):
            raw = gzip.open(cache / "listes" / f"{cle}.html.gz").read().decode("utf-8", "replace")
            v = {niveau: (n, html.unescape(re.sub(r"\s+", " ", texte)).strip())
                 for niveau, n, texte in LIBELLE.findall(raw)}
            out["sections"][v["Section"][0]] = v["Section"][1]
            out["chapitres"][v["Chapitre"][0]] = v["Chapitre"][1]
            out["rangees"][v["Chapitre"][0] + v["Rangée"][0]] = v["Rangée"][1]
    return out


def liste_officielle(cache: Path) -> dict:
    """{code: (section, rangée, désignation de liste)} d'après les pages rangée."""
    idx = _index(cache / "index_listes.jsonl")
    codes = {}
    for cle, e in idx.items():
        if cle.startswith("rangee_"):
            section = re.search(r"section=(\w+)", e["url"])[1]
            raw = gzip.open(cache / "listes" / f"{cle}.html.gz").read()
            for code, designation in codes_de_la_rangee(raw):
                codes[code] = (section, cle[len("rangee_"):], designation)
    return codes


def etape_fiches(cache: Path, ctx: ssl.SSLContext) -> None:
    idx_path = cache / "index_fiches.jsonl"
    deja = _index(idx_path)
    codes = liste_officielle(cache)
    a_lire = [c for c in sorted(codes) if c not in deja]
    print(f"{len(codes)} codes officiels, {len(a_lire)} fiches à lire")

    def fiche(code):
        section = codes[code][0]
        url = (f"{BASE}?page=sous_position&section={section}&chapitre={code[:2]}&range={code[2:4]}"
               f"&position={code[4:10]}&sous_position={code}")
        e = lire(url, cache / "fiches" / f"{code}.html.gz", ctx)
        e["cle"] = code
        if "erreur" not in e:
            _ecrire_index(idx_path, e)
        else:
            print("ÉCHEC", code, e["erreur"], flush=True)

    with cf.ThreadPoolExecutor(max_workers=3) as ex:
        list(ex.map(fiche, a_lire))


def etape_fichier(cache: Path, crawl: Path) -> None:
    codes = liste_officielle(cache)
    idx = _index(cache / "index_fiches.jsonl")
    positions, manquantes = {}, []
    for code in sorted(codes):
        e = idx.get(code)
        if not e:
            manquantes.append(code)
            continue
        f = lire_fiche(gzip.open(cache / "fiches" / f"{code}.html.gz").read())
        if f["badge"] != code:
            manquantes.append(code)
            continue
        tableaux = {titre: lignes for titre, lignes in f["tableaux"]}
        positions[code] = {"url": e["url"], "releve_le": e["releve_le"], "designation": f["designation"],
                           **{cle: tableaux.get(titre, [])[1:] for titre, cle in TABLEAUX.items()}}
    connus = {x["hs_code"] for x in json.loads(crawl.read_text(encoding="utf-8"))["sub_positions"]}
    dates = sorted(p["releve_le"] for p in positions.values())
    entete = {
        "source": "douane.gov.dz — Tarif douanier (e-service DGD), fiche sous-position",
        "source_root_url": f"{BASE}?page=tarif_douanier",
        "releve_du": dates[0] if dates else None,
        "releve_au": dates[-1] if dates else None,
        "collecteur": "scripts/releve_dgd_dza.py",
        "colonnes": {"taxes": ["Taxe", "Taux (%)", "Observation"],
                     "taxes_specifiques": ["Taxe", "Quotité/Unité", "Unité", "Unité de mesure", "Observation"],
                     "formalites": ["Code", "Document"]},
        "tableau_non_repris": "Avantages fiscaux — taxe et taux sans condition ni accord nommé, non servis",
        "codes_officiels": len(codes),
        "positions_relues": len(positions),
        "positions_non_relues": manquantes,
        "absents_du_tarif_dgd": sorted(connus - set(codes)),
        "libelles": libelles_officiels(cache),
    }
    lignes = [f"  {json.dumps(k, ensure_ascii=False)}: {json.dumps(v, ensure_ascii=False)}" for k, v in entete.items()]
    corps = [f"    {json.dumps(c)}: {json.dumps(p, ensure_ascii=False, separators=(',', ':'))}" for c, p in positions.items()]
    SORTIE.write_text("{\n" + ",\n".join(lignes) + ',\n  "positions": {\n' + ",\n".join(corps) + "\n  }\n}\n",
                      encoding="utf-8")
    print(f"{SORTIE.relative_to(RACINE)} : {len(positions)} positions, {len(manquantes)} non relues,"
          f" {len(entete['absents_du_tarif_dgd'])} absentes du tarif DGD")


def etape_verser(crawl: Path) -> None:
    sys.path.insert(0, str(RACINE / "backend"))
    from crawlers.integrity import seal_crawled_file

    r = json.loads(SORTIE.read_text(encoding="utf-8"))
    if r["positions_non_relues"]:
        raise SystemExit("relevé incomplet : rien n'est versé")
    corrections = json.loads(CORRECTIONS.read_text(encoding="utf-8"))

    def libelle(texte):
        return corrections["libelles"].get(texte, texte)

    c = json.loads(crawl.read_text(encoding="utf-8"))
    anciennes = {p["hs_code"]: p for p in c["sub_positions"]}
    positions = []
    for code, f in sorted(r["positions"].items()):
        p = anciennes.get(code) or {
            "raw_code": f"{code[:2]}.{code[2:4]}.{code[4:]}", "hs_code": code,
            "heading": f"{code[:2]}.{code[2:4]}", "chapter": code[:2],
            "section": re.search(r"section=(\w+)", f["url"])[1],
        }
        # La désignation servie est celle de la fiche. Le « ? » y tient la place
        # d'un caractère perdu à la mise en ligne : chaque ligne, et chaque
        # Observation, est servie corrigée à la main (décision du 04/10/2026).
        p["name"] = "\n".join(corrections["lignes"].get(ligne, ligne) for ligne in f["designation"].split("\n"))
        # Le libellé de la rangée (position à 4 chiffres) et du chapitre, tels
        # que la DGD les publie : la fiche commence sous la rangée. Ils
        # remplacent la désignation hiérarchique de conformepro.
        p["heading_label"] = libelle(r["libelles"]["rangees"][code[:4]])
        p["chapter_label"] = libelle(r["libelles"]["chapitres"][code[:2]])
        taxes = {}
        for sigle, taux, observation in f["taxes"]:
            cle = sigle.replace(".", "")
            if not re.fullmatch(r"[A-Z]+", cle) or cle in taxes:
                raise SystemExit(f"{code} : sigle {sigle!r} illisible ou en double, rien n'est versé")
            taxes[cle] = {"label_published": sigle, "rate": float(taux)}
            if observation:
                taxes[cle]["note"] = corrections["observations"].get(observation, observation)
        if "?" in p["name"] + p["heading_label"] + p["chapter_label"] + "".join(t.get("note", "") for t in taxes.values()):
            raise SystemExit(f"{code} : « ? » non corrigé, à reprendre dans {CORRECTIONS.name} ; rien n'est versé")
        p["taxes"] = taxes
        p["formalities"] = [{"code": k, "text_verbatim": document} for k, document in f["formalites"]]
        for cle in ("specific_taxes", "advantages", "tax_advantages", "source_gaps", "source_url",
                    "source_root_url", "date_consulted", "description", "designation_full", "display_code"):
            p.pop(cle, None)
        p["source"], p["crawled_at"] = f["url"], f["releve_le"]
        positions.append(p)

    retires = ("source_root_url", "source_provenance", "stats", "progress_stats", "policy", "_integrity_seal")
    entete = {k: v for k, v in c.items() if k not in retires and k != "sub_positions"}
    entete.update(source="douane.gov.dz — Tarif douanier (e-service DGD)", source_url=r["source_root_url"],
                  extracted_at=r["releve_au"], built_by="scripts/releve_dgd_dza.py verser")
    crawl.write_text(json.dumps({**entete, "sub_positions": positions}, ensure_ascii=False, indent=1) + "\n",
                     encoding="utf-8")
    seal_crawled_file(str(crawl), source_url=r["source_root_url"])

    lignes = Counter(k for p in positions for k in p["taxes"])
    registre = json.loads(REGISTRE.read_text(encoding="utf-8"))
    dza = registre["countries"]["DZA"]
    dza.pop("coverage_gaps", None)
    dza.update(
        organism="Direction Générale des Douanes (DGD), e-service Tarif douanier",
        url=r["source_root_url"], retrieved_at=r["releve_au"][:10], positions_count=len(positions),
        sha256=hashlib.sha256(crawl.read_bytes()).hexdigest(),
        taxes=sorted(lignes, key=lambda k: (-lignes[k], k)),
        formalities=f"{sum(1 for p in positions if p['formalities'])} positions avec formalités "
                    f"({len({x['code'] for p in positions for x in p['formalities']})} codes F.A.P)",
        legal_refs=f"{sum(1 for p in positions if p.get('legal_refs'))} positions avec legal_refs "
                   "(Code Douanes + Tarif D'Usage)",
    )
    REGISTRE.write_text(json.dumps(registre, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{crawl.relative_to(RACINE)} : {len(positions)} positions,"
          f" +{len(set(r['positions']) - set(anciennes))} −{len(set(anciennes) - set(r['positions']))}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("etape", choices=["listes", "fiches", "fichier", "verser"])
    ap.add_argument("--cache", type=Path, help="dossier des pages brutes (hors dépôt)")
    ap.add_argument("--cafile", help="magasin de certificats racines (défaut : celui du système)")
    ap.add_argument("--crawl", type=Path, default=CRAWL)
    a = ap.parse_args()
    if a.etape == "verser":
        etape_verser(a.crawl)
    elif a.cache is None:
        ap.error("--cache est requis pour listes, fiches et fichier")
    elif a.etape == "fichier":
        etape_fichier(a.cache, a.crawl)
    else:
        (etape_listes if a.etape == "listes" else etape_fiches)(a.cache, contexte_tls(a.cafile))


if __name__ == "__main__":
    main()

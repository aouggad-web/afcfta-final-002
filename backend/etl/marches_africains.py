"""Marchés africains pour le tableau de bord de direction (décision du 08/11/2026).

- Cours des matières premières : Pink Sheet de la Banque mondiale (CC BY 4.0),
  moyennes mensuelles en dollars US, publiées début de mois. Le classeur est
  remplacé sur place chaque mois (son dossier change une fois par an) : on
  relit son adresse sur la page de la Banque mondiale, puis on le redemande
  avec If-Modified-Since, et il n'est relu que s'il a changé.
- Indices boursiers, points à l'ouverture et à la clôture de la dernière séance,
  lus sur les sites officiels des bourses : Alger (SGBV, DZAIR INDEX), Abidjan
  (BRVM Composite), Lagos (NGX All-Share) et Nairobi (NSE 20). Pour un indice,
  l'ouverture est la clôture de la séance précédente. NGX ne publie que la
  dernière valeur : les clôtures sont gardées par date de séance (voir
  suivre_ngx) et, faute de la clôture de la veille, l'ouverture reste vide.

Une source en panne n'efface pas la dernière valeur lue : elle est rendue avec
`a_jour: False`, et elle est redemandée cinq minutes plus tard.
"""

import asyncio
import io
import json
import logging
import re
import time
from datetime import date, datetime, timedelta, timezone
from typing import Dict, Optional, Tuple

import aiohttp

logger = logging.getLogger(__name__)

PAGE_BANQUE_MONDIALE = "https://www.worldbank.org/en/research/commodity-markets"
_LIEN_PINK_SHEET = re.compile(
    r"https://thedocs\.worldbank\.org/[^\"'\s<>]*CMO-Historical-Data-Monthly\.xlsx"
)

# (clé, colonne du Pink Sheet, famille). Les libellés (trois langues) et les
# unités affichées sont côté interface.
PRODUITS = [
    ("brent", "Crude oil, Brent", "hydrocarbures"),
    ("gaz_europe", "Natural gas, Europe", "hydrocarbures"),
    ("gnl_japon", "Liquefied natural gas, Japan", "hydrocarbures"),
    ("charbon_afs", "Coal, South African", "hydrocarbures"),
    ("or", "Gold", "minerais"),
    ("cuivre", "Copper", "minerais"),
    ("minerai_fer", "Iron ore, cfr spot", "minerais"),
    ("aluminium", "Aluminum", "minerais"),
    ("platine", "Platinum", "minerais"),
    ("zinc", "Zinc", "minerais"),
    ("cacao", "Cocoa", "agriculture"),
    ("cafe_robusta", "Coffee, Robusta", "agriculture"),
    ("coton", "Cotton, A Index", "agriculture"),
    ("the", "Tea, Mombasa", "agriculture"),
    ("huile_palme", "Palm oil", "agriculture"),
    ("arachide", "Groundnuts", "agriculture"),
    ("phosphate", "Phosphate rock", "engrais"),
    ("uree", "Urea", "engrais"),
    ("dap", "DAP", "engrais"),
]
MOIS_SERIE = 13  # le mois publié et les 12 précédents (courbe sur un an)

SOURCES_INDICES = {
    "dzair": "https://www.sgbv.dz/",
    "brvm_c": "https://www.brvm.org/fr",
    "ngx_asi": "https://doclib.ngxgroup.com/REST/api/mrkstat/mrksnapshot",
    "nse20": "https://www.nse.co.ke/",
}
# Ordre d'affichage ; place et pays sont côté interface.
INDICES = ["dzair", "brvm_c", "ngx_asi", "nse20"]

DUREE_COURS_S = 12 * 3600
DUREE_INDICES_S = 30 * 60
NOUVEL_ESSAI_S = 5 * 60  # après un échec, la source est redemandée plus tôt
DELAIS = {"cours": DUREE_COURS_S, **{c: DUREE_INDICES_S for c in INDICES}}

# Bourse de Lagos : séance de 10 h à 14 h 30, heure du Nigeria (UTC+1 toute
# l'année, sans heure d'été).
LAGOS = timezone(timedelta(hours=1))
OUVERTURE_NGX = (10, 0)
FERMETURE_NGX = (14, 30)
# Jours fériés fixes du Nigeria (mois, jour) ; Vendredi saint et lundi de Pâques
# sont calculés. Les fêtes musulmanes, annoncées au dernier moment, sont
# reconnues à l'instantané lui-même (voir suivre_ngx).
FERIES_FIXES_NGX = {(1, 1), (5, 1), (6, 12), (10, 1), (12, 25), (12, 26)}
JOURS_GARDES_NGX = 15
_ENTETES = {"User-Agent": "Mozilla/5.0 (compatible; AfCFTA-Trade-Intelligence/1.0)"}
_DELAI = aiohttp.ClientTimeout(total=20)


def _nombre(texte: str) -> float:
    """« 20 420,74 », « 4,187.52 » ou « 0,10 » → float."""
    t = re.sub(r"[\s  ]", "", texte)
    if "," in t and "." in t:
        t = t.replace(",", "")  # 4,187.52 : virgule des milliers
    else:
        t = t.replace(",", ".")
    return float(t)


# ── Cours des matières premières ────────────────────────────────────────────


def lien_pink_sheet(html: str) -> Optional[str]:
    trouve = _LIEN_PINK_SHEET.search(html or "")
    return trouve.group(0) if trouve else None


def _colonne(nom) -> str:
    return re.sub(r"[\s*]+", " ", str(nom or "")).strip().lower()


def lire_pink_sheet(contenu: bytes) -> Dict:
    """Feuille « Monthly Prices » → mois publié et série de chaque produit."""
    import openpyxl

    classeur = openpyxl.load_workbook(io.BytesIO(contenu), read_only=True, data_only=True)
    lignes = list(classeur["Monthly Prices"].iter_rows(values_only=True))
    classeur.close()

    entete = next(i for i, l in enumerate(lignes[:12]) if any(_colonne(c) == "gold" for c in l))
    colonnes = {_colonne(c): j for j, c in enumerate(lignes[entete])}
    mois = [l for l in lignes[entete + 1 :] if re.fullmatch(r"\d{4}M\d{2}", str(l[0] or ""))]
    recents = mois[-MOIS_SERIE:]

    def valeur(v):
        return round(float(v), 4) if isinstance(v, (int, float)) else None

    produits = {}
    for cle, colonne, famille in PRODUITS:
        j = colonnes.get(_colonne(colonne))
        if j is None:
            logger.warning("Pink Sheet : colonne absente %s", colonne)
            continue
        serie = [valeur(l[j]) for l in recents]
        if serie and serie[-1] is not None:
            produits[cle] = {"famille": famille, "serie": serie}

    dernier = str(recents[-1][0])
    return {
        "mois": f"{dernier[:4]}-{dernier[5:]}",
        "mois_serie": [f"{str(l[0])[:4]}-{str(l[0])[5:]}" for l in recents],
        "produits": produits,
    }


# ── Indices boursiers ───────────────────────────────────────────────────────


def lire_sgbv(html: str) -> Dict:
    """Page d'accueil de la SGBV : série complète du DZAIR INDEX (horodatages en ms)."""
    bloc = re.search(r"name\s*:\s*'Dzair Indice'\s*,\s*data\s*:\s*\[((?:\s*\[[^\]]*\]\s*,?)+)\s*\]", html)
    points = re.findall(r"\[(\d{12,14}),\s*([\d.]+)\]", bloc.group(1) if bloc else "")
    if len(points) < 2:
        raise ValueError("DZAIR INDEX introuvable")
    (_, veille), (horodatage, cloture) = points[-2], points[-1]
    jour = datetime.fromtimestamp(int(horodatage) / 1000, tz=timezone.utc).date()
    return {"ouverture": float(veille), "cloture": float(cloture), "date": jour.isoformat()}


def lire_brvm(html: str) -> Dict:
    """Page d'accueil de la BRVM : BRVM Composite, clôture et variation du jour."""
    ligne = re.search(
        r"<td>\s*BRVM-C\s*</td>\s*<td[^>]*>\s*([\d\s.,]+?)\s*</td>\s*<td[^>]*>\s*(-?[\d\s.,]+?)\s*%",
        html,
    )
    if not ligne:
        raise ValueError("BRVM Composite introuvable")
    cloture, variation = _nombre(ligne.group(1)), _nombre(ligne.group(2))
    return {"ouverture": round(cloture / (1 + variation / 100), 2), "cloture": cloture, "date": None}


def lire_nse(html: str) -> Dict:
    """Page d'accueil de la NSE : NSE 20, valeur et variation en points."""
    apres = re.search(r"<h3>\s*NSE 20\s*</h3>(.{0,1500})", html, re.S)
    nombres = re.findall(r"-?[\d,]+\.\d+", re.sub(r"<[^>]+>", " ", apres.group(1)) if apres else "")
    if len(nombres) < 2:
        raise ValueError("NSE 20 introuvable")
    cloture, variation = _nombre(nombres[0]), _nombre(nombres[1])
    return {"ouverture": round(cloture - variation, 2), "cloture": cloture, "date": None}


def lire_ngx(texte: str) -> Dict:
    """Instantané officiel de NGX : All-Share Index (sans la veille, voir suivre_ngx).
    L'empreinte (transactions, volume, valeur échangés dans la séance) dit si
    une nouvelle séance a eu lieu depuis la précédente."""
    donnees = json.loads(texte)
    asi = donnees.get("ASI")
    if not asi:
        raise ValueError("NGX ASI introuvable")
    empreinte = [donnees.get(k) for k in ("DEALS", "VOLUME", "VALUE")]
    return {"ouverture": None, "cloture": float(asi), "date": None, "empreinte": empreinte}


def _paques(annee: int) -> date:
    """Dimanche de Pâques (calendrier grégorien, méthode de Meeus)."""
    a, b, c = annee % 19, annee // 100, annee % 100
    d, e = b // 4, b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = c // 4, c % 4
    l_ = (32 + 2 * e + 2 * i - h - k) % 7
    m_ = (a + 11 * h + 22 * l_) // 451
    mois = (h + l_ - 7 * m_ + 114) // 31
    jour = (h + l_ - 7 * m_ + 114) % 31 + 1
    return date(annee, mois, jour)


def ferie_ngx(jour: date) -> bool:
    if (jour.month, jour.day) in FERIES_FIXES_NGX:
        return True
    paques = _paques(jour.year)
    return jour in (paques - timedelta(days=2), paques + timedelta(days=1))


def _jour_ouvre_precedent(jour: date, sans_seance=()) -> date:
    jour -= timedelta(days=1)
    while jour.weekday() >= 5 or ferie_ngx(jour) or jour.isoformat() in sans_seance:
        jour -= timedelta(days=1)
    return jour


def seance_ngx(maintenant: datetime) -> Tuple[date, bool]:
    """Séance que montre l'instantané NGX lu à `maintenant`, et si sa valeur est
    déjà la clôture (séance terminée) ou encore un cours de séance."""
    t = maintenant.astimezone(LAGOS)
    if t.weekday() < 5 and not ferie_ngx(t.date()) and (t.hour, t.minute) >= OUVERTURE_NGX:
        return t.date(), (t.hour, t.minute) >= FERMETURE_NGX
    # Avant l'ouverture, le week-end ou un jour férié : la dernière séance est close.
    return _jour_ouvre_precedent(t.date()), True


def suivre_ngx(lu: Dict, memoire: Optional[Dict], maintenant: Optional[datetime] = None) -> Tuple[Dict, Dict]:
    """NGX ne donne que la dernière valeur, sans date ni veille. On garde les
    clôtures par date de séance (lectures faites après la fermeture, ou avant
    l'ouverture suivante) ; l'ouverture est la clôture du jour de séance
    précédent. Si cette clôture n'a pas été lue (personne n'a consulté le
    tableau ce jour-là, serveur arrêté), l'ouverture reste vide plutôt que fausse.

    Un jour ouvré où l'activité (empreinte) n'a pas bougé depuis la séance
    précédente n'est pas une séance (férié annoncé tard, séance pas encore
    commencée) : on montre la séance précédente, et, une fois la journée finie,
    ce jour est noté « sans séance » pour le calcul de la veille."""
    seance, close = seance_ngx(maintenant or datetime.now(timezone.utc))
    memoire = memoire or {}
    clotures = dict(memoire.get("clotures") or {})
    empreintes = dict(memoire.get("empreintes") or {})
    sans_seance = set(memoire.get("sans_seance") or [])
    empreinte = lu.get("empreinte")
    precedente = max((j for j in clotures if j < seance.isoformat()), default=None)
    if precedente and empreinte and empreintes.get(precedente) == empreinte:
        if close:
            sans_seance.add(seance.isoformat())
        seance = date.fromisoformat(precedente)
    elif close:
        clotures[seance.isoformat()] = lu["cloture"]
        if empreinte:
            empreintes[seance.isoformat()] = empreinte
    gardes = sorted(clotures)[-JOURS_GARDES_NGX:]
    memoire = {
        "clotures": {j: clotures[j] for j in gardes},
        "empreintes": {j: empreintes[j] for j in gardes if j in empreintes},
        "sans_seance": sorted(j for j in sans_seance if gardes and j >= gardes[0]),
    }
    ouverture = clotures.get(_jour_ouvre_precedent(seance, sans_seance).isoformat())
    lu = {k: v for k, v in lu.items() if k != "empreinte"}
    return {**lu, "ouverture": ouverture, "date": seance.isoformat()}, memoire


LECTEURS = {"dzair": lire_sgbv, "brvm_c": lire_brvm, "ngx_asi": lire_ngx, "nse20": lire_nse}


# ── Collecte et cache ───────────────────────────────────────────────────────


class Marches:
    """Cache en mémoire ; la base (facultative) garde la mémoire NGX et les
    dernières valeurs entre deux redémarrages."""

    def __init__(self):
        self.cours: Optional[Dict] = None
        self.indices: Dict[str, Dict] = {}
        self.memoire_ngx: Optional[Dict] = None
        self.lus_a: Dict[str, float] = {}  # source → heure de la dernière lecture
        self._etat_charge = False
        self._prochain_essai_base = 0.0
        self._verrou = asyncio.Lock()

    async def _texte(self, session, url) -> str:
        async with session.get(url, headers=_ENTETES, timeout=_DELAI) as r:
            r.raise_for_status()
            return await r.text()

    async def _rafraichir_cours(self, session):
        lien = lien_pink_sheet(await self._texte(session, PAGE_BANQUE_MONDIALE))
        if not lien:
            raise ValueError("lien du Pink Sheet introuvable")
        entetes = dict(_ENTETES)
        if self.cours and self.cours.get("lien") == lien and self.cours.get("modifie_le"):
            entetes["If-Modified-Since"] = self.cours["modifie_le"]
        async with session.get(lien, headers=entetes, timeout=_DELAI) as r:
            if r.status == 304:
                return  # classeur inchangé depuis la dernière lecture
            r.raise_for_status()
            contenu = await r.read()
            modifie_le = r.headers.get("Last-Modified")
        self.cours = {**lire_pink_sheet(contenu), "lien": lien, "modifie_le": modifie_le}

    async def _rafraichir_indice(self, session, cle):
        lu = LECTEURS[cle](await self._texte(session, SOURCES_INDICES[cle]))
        if cle == "ngx_asi":
            lu, self.memoire_ngx = suivre_ngx(lu, self.memoire_ngx)
        variation = (
            round((lu["cloture"] - lu["ouverture"]) / lu["ouverture"] * 100, 2)
            if lu.get("ouverture")
            else None
        )
        self.indices[cle] = {**lu, "variation_pct": variation, "a_jour": True,
                             "lu_le": datetime.now(timezone.utc).isoformat(timespec="seconds")}

    async def _charger(self, db):
        if db is None or self._etat_charge or time.time() < self._prochain_essai_base:
            return
        try:
            doc = await db.marches_africains.find_one({"_id": "etat"}) or {}
        except Exception as e:
            # Base indisponible : réessayée dans NOUVEL_ESSAI_S, pas à chaque appel
            # (chaque essai attend le délai de sélection du serveur Mongo).
            logger.warning("Marchés : lecture de l'état impossible (%s)", type(e).__name__)
            self._prochain_essai_base = time.time() + NOUVEL_ESSAI_S
            return
        # Mémoire NGX : celle de la base complétée par celle lue depuis (plus récente).
        base, vive = doc.get("memoire_ngx") or {}, self.memoire_ngx or {}
        self.memoire_ngx = {
            "clotures": {**(base.get("clotures") or {}), **(vive.get("clotures") or {})},
            "empreintes": {**(base.get("empreintes") or {}), **(vive.get("empreintes") or {})},
            "sans_seance": sorted(set(base.get("sans_seance") or []) | set(vive.get("sans_seance") or [])),
        }
        self.indices = {**doc.get("indices", {}), **self.indices}
        if self.cours is None and doc.get("cours"):
            self.cours = doc["cours"]
        self._etat_charge = True

    async def _enregistrer(self, db):
        # Pas d'écriture tant que l'état n'a pas été relu : elle écraserait la
        # mémoire NGX et les cours gardés en base.
        if db is None or not self._etat_charge:
            return
        try:
            await db.marches_africains.replace_one(
                {"_id": "etat"},
                {"_id": "etat", "memoire_ngx": self.memoire_ngx, "indices": self.indices, "cours": self.cours},
                upsert=True,
            )
        except Exception as e:
            logger.warning("Marchés : enregistrement impossible (%s)", type(e).__name__)

    async def apercu(self, db=None, session_http=None) -> Dict:
        async with self._verrou:
            await self._charger(db)
            maintenant = time.time()
            taches = [c for c in DELAIS if maintenant - self.lus_a.get(c, 0.0) > DELAIS[c]]
            if taches:
                session = session_http or aiohttp.ClientSession()
                try:
                    resultats = await asyncio.gather(
                        *[
                            self._rafraichir_cours(session) if c == "cours" else self._rafraichir_indice(session, c)
                            for c in taches
                        ],
                        return_exceptions=True,
                    )
                finally:
                    if session_http is None:
                        await session.close()
                for c, r in zip(taches, resultats):
                    if isinstance(r, Exception):
                        logger.warning("Marchés : %s indisponible (%s)", c, r)
                        if c in self.indices:
                            self.indices[c]["a_jour"] = False
                        # Redemandée dans NOUVEL_ESSAI_S, et non au bout du délai complet.
                        self.lus_a[c] = maintenant - DELAIS[c] + NOUVEL_ESSAI_S
                    else:
                        self.lus_a[c] = maintenant
                await self._enregistrer(db)

            internes = ("lien", "modifie_le")
            cours = {k: v for k, v in (self.cours or {}).items() if k not in internes} or None
            return {
                "cours": cours,
                "indices": [{"cle": c, **self.indices[c]} for c in INDICES if c in self.indices],
                "sources": {
                    "cours": "Banque mondiale, Pink Sheet (CC BY 4.0)",
                    "indices": "SGBV (Alger), BRVM (Abidjan), NGX (Lagos), NSE (Nairobi)",
                },
            }


MARCHES = Marches()

"""Tableau de bord de direction : cours de la Banque mondiale et indices des
bourses africaines (08/11/2026). Extraits réels des pages officielles."""

import asyncio
import io
from datetime import datetime, timedelta, timezone

import openpyxl
import pytest

from etl import marches_africains as m

SGBV = """<script>series : [{ type: 'line',
    name : 'Dzair Indice',
    data : [[1793836800000,3809.446],[1794096000000,3812.105]] ,
    dataGrouping: { enabled:false }}]</script>"""

BRVM = """<tr><td>BRVM-C</td><td class="text-right">520,74</td><td class="text-right">0,10% <span class="icone-seance good"></span></td><td></td> </tr>
<tr><td>BRVM-30</td><td class="text-right">251,79</td><td class="text-right">0,07% </td></tr>"""

BRVM_BAISSE = BRVM.replace("520,74", "1 020,50").replace("0,10%", "-2,00%")

NSE = """<div class="stat_figures"><p>239.72<span class="stat_percent negg">-1.89</span></p></div>
<div class="stat_head"><h3>NSE 20</h3></div>
<div class="stat_figures"><p>4,187.52<span class="stat_percent" style="color:#4BAC43">19.55</span></p></div>
<div class="stat_head"><h3>NSE 25</h3></div>
<div class="stat_figures"><p>6,733.75<span class="stat_percent negg">-28.50</span></p></div>"""

NGX = '{"$id":"1","ASI":248877.22,"DEALS":32666.00,"CAP":161593642364255.53}'

PAGE_BM = (
    '<a href="https://thedocs.worldbank.org/en/doc/74e8be41ceb20fa0da750cda2f6b9e4e-0050012026/'
    'related/CMO-Historical-Data-Monthly.xlsx">Monthly prices</a>'
)


def _pink_sheet(mois=("2025M10", "2026M09", "2026M10")) -> bytes:
    """Classeur au format du Pink Sheet : titre, en-têtes, unités, puis un mois par ligne."""
    classeur = openpyxl.Workbook()
    feuille = classeur.active
    feuille.title = "Monthly Prices"
    feuille.append(["World Bank Commodity Price Data (The Pink Sheet)"])
    feuille.append(["Updated on November 03, 2026"])
    feuille.append([])
    feuille.append([None, "Crude oil, Brent", "Coal, South African **", "Gold", "Urea ", "Cocoa"])
    feuille.append([None, "($/bbl)", "($/mt)", "($/troy oz)", "($/mt)", "($/kg)"])
    valeurs = {"2025M10": [64.7, 91.6, 4058, 394.4, 5.95], "2026M09": [116.8, 98.2, 4319, 407.5, 5.92],
               "2026M10": [125, 100, 4105, 420, "…"], "2026M11": [118, 99, 4150, 415, 5.6]}
    for cle in mois:
        feuille.append([cle, *valeurs[cle]])
    tampon = io.BytesIO()
    classeur.save(tampon)
    return tampon.getvalue()


def test_lien_du_pink_sheet_relu_sur_la_page_de_la_banque_mondiale():
    assert m.lien_pink_sheet(PAGE_BM).endswith("-0050012026/related/CMO-Historical-Data-Monthly.xlsx")
    assert m.lien_pink_sheet("<html>rien</html>") is None


def test_pink_sheet_mois_publie_et_series():
    cours = m.lire_pink_sheet(_pink_sheet())
    assert cours["mois"] == "2026-10"
    assert cours["mois_serie"] == ["2025-10", "2026-09", "2026-10"]
    assert cours["produits"]["brent"] == {"famille": "hydrocarbures", "serie": [64.7, 116.8, 125]}
    # En-têtes à astérisques ou espace final retrouvés.
    assert cours["produits"]["charbon_afs"]["serie"][-1] == 100
    assert cours["produits"]["uree"]["famille"] == "engrais"
    # Mois non publié (« … ») : le produit n'est pas affiché avec un faux cours.
    assert "cacao" not in cours["produits"]


def test_dzair_index_ouverture_cloture_et_date_de_seance():
    assert m.lire_sgbv(SGBV) == {"ouverture": 3809.446, "cloture": 3812.105, "date": "2026-11-08"}


def test_brvm_ouverture_deduite_de_la_variation():
    assert m.lire_brvm(BRVM) == {"ouverture": 520.22, "cloture": 520.74, "date": None}
    assert m.lire_brvm(BRVM_BAISSE)["ouverture"] == 1041.33


def test_nse20_variation_en_points():
    assert m.lire_nse(NSE) == {"ouverture": 4167.97, "cloture": 4187.52, "date": None}


LAGOS = timezone(timedelta(hours=1))


def _a_lagos(jour, heure, minute=0):
    return datetime(2026, 11, jour, heure, minute, tzinfo=LAGOS)


def _ngx(valeur):
    return {**m.lire_ngx(NGX), "cloture": valeur}


def test_ngx_seance_selon_l_heure_de_lagos():
    # 09/11/2026 est un lundi.
    assert m.seance_ngx(_a_lagos(9, 11)) == (datetime(2026, 11, 9).date(), False)  # en séance
    assert m.seance_ngx(_a_lagos(9, 15)) == (datetime(2026, 11, 9).date(), True)  # séance close
    assert m.seance_ngx(_a_lagos(9, 8)) == (datetime(2026, 11, 6).date(), True)  # avant l'ouverture : vendredi
    assert m.seance_ngx(_a_lagos(8, 12)) == (datetime(2026, 11, 6).date(), True)  # dimanche : vendredi


def test_ngx_ouverture_egale_la_cloture_de_la_veille():
    lu, memoire = m.suivre_ngx(m.lire_ngx(NGX), None, _a_lagos(9, 16))
    assert lu["ouverture"] is None and lu["cloture"] == 248877.22 and lu["date"] == "2026-11-09"
    # Le lendemain, en séance : les cours bougent, l'ouverture reste la clôture de lundi.
    for heure, valeur in ((10, 249100.0), (11, 249500.0), (14, 250000.0)):
        lu, memoire = m.suivre_ngx(_ngx(valeur), memoire, _a_lagos(10, heure))
        assert lu["ouverture"] == 248877.22 and lu["cloture"] == valeur and lu["date"] == "2026-11-10"
    # Lu le mercredi avant l'ouverture : clôture de mardi, ouverture = clôture de lundi.
    lu, memoire = m.suivre_ngx(_ngx(250200.0), memoire, _a_lagos(11, 9))
    assert (lu["ouverture"], lu["cloture"], lu["date"]) == (248877.22, 250200.0, "2026-11-10")


def test_ngx_sans_la_cloture_de_la_veille_l_ouverture_reste_vide():
    _, memoire = m.suivre_ngx(_ngx(100000.0), None, _a_lagos(9, 16))  # lundi
    # Mardi jamais lu ; mercredi : la clôture de lundi n'est pas celle de la veille.
    lu, memoire = m.suivre_ngx(_ngx(99000.0), memoire, _a_lagos(11, 16))
    assert lu["ouverture"] is None
    # Lu seulement pendant la séance de jeudi : pas une clôture.
    lu, memoire = m.suivre_ngx(_ngx(99500.0), memoire, _a_lagos(12, 11))
    assert lu["ouverture"] == 99000.0
    lu, _ = m.suivre_ngx(_ngx(98000.0), memoire, _a_lagos(13, 16))  # vendredi
    assert lu["ouverture"] is None


@pytest.mark.parametrize("lecteur", [m.lire_sgbv, m.lire_brvm, m.lire_nse])
def test_page_modifiee_signalee(lecteur):
    with pytest.raises(ValueError):
        lecteur("<html>page refaite</html>")


class _Reponse:
    def __init__(self, corps, statut=200, entetes=None):
        self._corps, self.status = corps, statut
        self.headers = entetes or {}

    def raise_for_status(self):
        if self.status >= 400:
            raise RuntimeError(f"HTTP {self.status}")

    async def text(self):
        return self._corps

    async def read(self):
        return self._corps

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False


class _Session:
    """Sert les extraits réels ; le Pink Sheet porte une date de modification et
    répond 304 à If-Modified-Since quand il n'a pas changé."""

    MODIFIE = "Tue, 03 Nov 2026 19:30:42 GMT"

    def __init__(self, pannes=(), pink_sheet=None, modifie=MODIFIE):
        self.pannes = set(pannes)
        self.lues = []
        self.entetes = []
        self.modifie = modifie
        self.corps = {
            m.PAGE_BANQUE_MONDIALE: PAGE_BM,
            m.lien_pink_sheet(PAGE_BM): pink_sheet or _pink_sheet(),
            m.SOURCES_INDICES["dzair"]: SGBV,
            m.SOURCES_INDICES["brvm_c"]: BRVM,
            m.SOURCES_INDICES["ngx_asi"]: NGX,
            m.SOURCES_INDICES["nse20"]: NSE,
        }

    def get(self, url, headers=None, **kwargs):
        self.lues.append(url)
        self.entetes.append(dict(headers or {}))
        if url in self.pannes:
            return _Reponse("", 503)
        if url == m.lien_pink_sheet(PAGE_BM):
            if (headers or {}).get("If-Modified-Since") == self.modifie:
                return _Reponse(b"", 304)
            return _Reponse(self.corps[url], entetes={"Last-Modified": self.modifie})
        return _Reponse(self.corps[url])


def test_apercu_complet_puis_cache():
    marches = m.Marches()
    session = _Session()
    apercu = asyncio.run(marches.apercu(session_http=session))
    assert apercu["cours"]["mois"] == "2026-10"
    assert "lien" not in apercu["cours"] and "modifie_le" not in apercu["cours"]
    assert [i["cle"] for i in apercu["indices"]] == ["dzair", "brvm_c", "ngx_asi", "nse20"]
    dzair = apercu["indices"][0]
    assert dzair["variation_pct"] == 0.07 and dzair["a_jour"] is True
    assert apercu["indices"][2]["variation_pct"] is None  # NGX : première lecture

    # Deuxième appel dans les délais : aucune requête.
    lues = len(session.lues)
    asyncio.run(marches.apercu(session_http=session))
    assert len(session.lues) == lues


def test_source_en_panne_garde_la_derniere_valeur():
    marches = m.Marches()
    asyncio.run(marches.apercu(session_http=_Session()))
    marches.lus_a.clear()  # délais écoulés
    apercu = asyncio.run(marches.apercu(session_http=_Session(pannes={m.SOURCES_INDICES["brvm_c"]})))
    brvm = next(i for i in apercu["indices"] if i["cle"] == "brvm_c")
    assert brvm["cloture"] == 520.74 and brvm["a_jour"] is False


def test_pink_sheet_inchange_non_relu_nouvelle_edition_relue_a_la_meme_adresse():
    marches = m.Marches()
    asyncio.run(marches.apercu(session_http=_Session()))
    # Classeur inchangé : redemandé avec If-Modified-Since, 304, cours gardés.
    marches.lus_a.clear()
    session = _Session()
    apercu = asyncio.run(marches.apercu(session_http=session))
    i = session.lues.index(m.lien_pink_sheet(PAGE_BM))
    assert session.entetes[i]["If-Modified-Since"] == _Session.MODIFIE
    assert apercu["cours"]["mois"] == "2026-10"
    # Édition de novembre publiée à la même adresse : relue.
    marches.lus_a.clear()
    session = _Session(pink_sheet=_pink_sheet(mois=("2025M10", "2026M09", "2026M10", "2026M11")),
                       modifie="Thu, 03 Dec 2026 19:00:00 GMT")
    apercu = asyncio.run(marches.apercu(session_http=session))
    assert apercu["cours"]["mois"] == "2026-11"


def test_echec_redemande_cinq_minutes_plus_tard_et_non_douze_heures():
    marches = m.Marches()
    lien = m.lien_pink_sheet(PAGE_BM)
    apercu = asyncio.run(marches.apercu(session_http=_Session(pannes={m.PAGE_BANQUE_MONDIALE})))
    assert apercu["cours"] is None
    attente = marches.lus_a["cours"] + m.DELAIS["cours"] - __import__("time").time()
    assert 0 < attente <= m.NOUVEL_ESSAI_S
    assert marches.lus_a["dzair"] + m.DELAIS["dzair"] - __import__("time").time() > m.NOUVEL_ESSAI_S
    marches.lus_a["cours"] -= m.NOUVEL_ESSAI_S
    session = _Session()
    apercu = asyncio.run(marches.apercu(session_http=session))
    assert lien in session.lues and apercu["cours"]["mois"] == "2026-10"


class _BaseEnPanne:
    """Collection Mongo dont la lecture échoue une fois, puis répond."""

    def __init__(self):
        self.appels = 0
        self.ecrit = []

    async def find_one(self, filtre):
        self.appels += 1
        if self.appels == 1:
            raise RuntimeError("Mongo indisponible")
        return {"_id": "etat", "memoire_ngx": {"clotures": {"2026-11-06": 247000.0}}, "indices": {}, "cours": None}

    async def replace_one(self, filtre, doc, upsert=False):
        self.ecrit.append(doc)


def test_lecture_mongo_ratee_reessayee_sans_ecraser_l_etat_garde():
    base = _BaseEnPanne()
    db = type("Db", (), {"marches_africains": base})()
    marches = m.Marches()
    asyncio.run(marches.apercu(db=db, session_http=_Session()))
    assert base.ecrit == []  # rien d'écrit tant que l'état n'a pas été relu
    marches.lus_a.clear()
    asyncio.run(marches.apercu(db=db, session_http=_Session()))
    assert base.appels == 2 and base.ecrit
    assert "2026-11-06" in base.ecrit[-1]["memoire_ngx"]["clotures"]

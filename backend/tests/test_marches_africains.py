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

EIA = """<tr>
 <td class='B6'>&nbsp;&nbsp;2026 Oct-26 to Oct-30</td>
 <td class='B3'>128.12</td>
 <td class='B3'>123.10</td>
 <td class='B3'>119.20</td>
 <td class='B3'>115.28</td>
 <td class='B3'>120.15</td>
 </tr>
 <tr>
 <td class='B6'>&nbsp;&nbsp;2026 Nov- 2 to Nov- 6</td>
 <td class='B3'>107.39</td>
 <td class='B3'>107.03</td>
 <td class='B3'></td>
 <td class='B3'></td>
 <td class='B3'></td>
 </tr>"""

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
    # Chaque valeur a sa propre empreinte d'activité (transactions, volume, valeur).
    return {**m.lire_ngx(NGX), "cloture": valeur, "empreinte": [valeur, 1, 1]}


def test_ngx_empreinte_d_activite_lue_et_retiree_de_la_reponse():
    lu = m.lire_ngx(NGX)
    assert lu["empreinte"] == [32666.00, None, None]
    sortie, _ = m.suivre_ngx(lu, None, _a_lagos(9, 16))
    assert "empreinte" not in sortie


def test_ngx_seance_selon_l_heure_de_lagos():
    # 09/11/2026 est un lundi.
    assert m.seance_ngx(_a_lagos(9, 11)) == (datetime(2026, 11, 9).date(), False)  # en séance
    assert m.seance_ngx(_a_lagos(9, 15)) == (datetime(2026, 11, 9).date(), True)  # séance close
    assert m.seance_ngx(_a_lagos(9, 8)) == (datetime(2026, 11, 6).date(), True)  # avant l'ouverture : vendredi
    assert m.seance_ngx(_a_lagos(8, 12)) == (datetime(2026, 11, 6).date(), True)  # dimanche : vendredi


def test_ngx_ouverture_egale_la_cloture_de_la_veille():
    lu, memoire = m.suivre_ngx(_ngx(248877.22), None, _a_lagos(9, 16))
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
            m.PAGE_BRENT_EIA: EIA,
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
    marches._prochain_essai_base = 0  # délai avant un nouvel essai de la base écoulé
    asyncio.run(marches.apercu(db=db, session_http=_Session()))
    assert base.appels == 2 and base.ecrit
    assert "2026-11-06" in base.ecrit[-1]["memoire_ngx"]["clotures"]


def _a_lagos_le(mois, jour, heure):
    return datetime(2026, mois, jour, heure, 0, tzinfo=LAGOS)


def test_ngx_jour_ferie_fixe_non_compte_comme_seance():
    _, memoire = m.suivre_ngx(_ngx(104000.0), None, _a_lagos_le(9, 29, 16))  # mardi
    _, memoire = m.suivre_ngx(_ngx(105000.0), memoire, _a_lagos_le(9, 30, 16))  # mercredi
    # Jeudi 01/10/2026, fête de l'indépendance : pas de séance, on montre celle de mercredi.
    assert m.seance_ngx(_a_lagos_le(10, 1, 11)) == (datetime(2026, 9, 30).date(), True)
    lu, memoire = m.suivre_ngx(_ngx(105000.0), memoire, _a_lagos_le(10, 1, 11))
    assert (lu["date"], lu["ouverture"], lu["cloture"]) == ("2026-09-30", 104000.0, 105000.0)
    # Vendredi 02/10 en séance : la séance précédente est celle de mercredi.
    lu, _ = m.suivre_ngx(_ngx(106000.0), memoire, _a_lagos_le(10, 2, 11))
    assert (lu["date"], lu["ouverture"]) == ("2026-10-02", 105000.0)
    # Pâques 2026 (5 avril) : Vendredi saint et lundi de Pâques chômés.
    assert m.ferie_ngx(datetime(2026, 4, 3).date()) and m.ferie_ngx(datetime(2026, 4, 6).date())
    assert not m.ferie_ngx(datetime(2026, 4, 7).date())


def test_ngx_ferie_annonce_tard_reconnu_a_l_activite_inchangee():
    _, memoire = m.suivre_ngx(_ngx(99000.0), None, _a_lagos(10, 16))  # mardi
    _, memoire = m.suivre_ngx(_ngx(100000.0), memoire, _a_lagos(11, 16))  # mercredi
    # Jeudi 12/11 chômé (fête annoncée tard) : l'activité n'a pas bougé depuis mercredi.
    lu, memoire = m.suivre_ngx(_ngx(100000.0), memoire, _a_lagos(12, 11))
    assert (lu["date"], lu["ouverture"], lu["cloture"]) == ("2026-11-11", 99000.0, 100000.0)
    lu, memoire = m.suivre_ngx(_ngx(100000.0), memoire, _a_lagos(12, 16))
    assert lu["date"] == "2026-11-11" and memoire["sans_seance"] == ["2026-11-12"]
    # Vendredi : la séance précédente est celle de mercredi.
    lu, _ = m.suivre_ngx(_ngx(101000.0), memoire, _a_lagos(13, 11))
    assert (lu["date"], lu["ouverture"]) == ("2026-11-13", 100000.0)


def test_lecture_mongo_ratee_la_memoire_recente_n_est_pas_ecrasee(monkeypatch):
    base = _BaseEnPanne()
    db = type("Db", (), {"marches_africains": base})()
    marches = m.Marches()
    # Base en panne le vendredi soir : la clôture du 13 n'existe qu'en mémoire.
    _, marches.memoire_ngx = m.suivre_ngx(_ngx(100000.0), None, _a_lagos(13, 16))
    asyncio.run(marches._charger(db))
    assert not marches._etat_charge
    # Lundi : la base répond (elle ne connaît que le 06/11) ; les deux mémoires sont réunies.
    marches._prochain_essai_base = 0
    asyncio.run(marches._charger(db))
    assert set(marches.memoire_ngx["clotures"]) == {"2026-11-06", "2026-11-13"}
    lu, _ = m.suivre_ngx(_ngx(101000.0), marches.memoire_ngx, _a_lagos(16, 11))
    assert lu["ouverture"] == 100000.0


def test_base_injoignable_pas_de_nouvel_essai_a_chaque_appel():
    class _Toujours(_BaseEnPanne):
        async def find_one(self, filtre):
            self.appels += 1
            raise RuntimeError("Mongo injoignable")

    base = _Toujours()
    db = type("Db", (), {"marches_africains": base})()
    marches = m.Marches()
    for _ in range(3):
        asyncio.run(marches.apercu(db=db, session_http=_Session()))
    assert base.appels == 1 and base.ecrit == []


def test_brent_dernier_prix_quotidien_eia():
    assert m.lire_brent_eia(EIA) == {"prix": 107.03, "date": "2026-11-03"}
    # Semaine à cheval sur deux années : la date suit le calendrier.
    fin_annee = EIA.replace("2026 Nov- 2 to Nov- 6", "2026 Dec-29 to Jan- 2").replace(
        "<td class='B3'></td>\n <td class='B3'></td>\n <td class='B3'></td>",
        "<td class='B3'>101.5</td>\n <td class='B3'></td>\n <td class='B3'>99.9</td>")
    assert m.lire_brent_eia(fin_annee) == {"prix": 99.9, "date": "2027-01-02"}
    with pytest.raises(ValueError):
        m.lire_brent_eia("<html>page refaite</html>")


def test_apercu_rend_le_dernier_brent():
    apercu = asyncio.run(m.Marches().apercu(session_http=_Session()))
    assert apercu["brent_jour"] == {"prix": 107.03, "date": "2026-11-03", "source": "EIA"}


# ── Audit D7 (16/11/2026) : la collecte ne bloque plus les visiteurs ────────


class _ReponseLente(_Reponse):
    def __init__(self, corps, delai):
        super().__init__(corps)
        self._delai = delai

    async def text(self):
        await asyncio.sleep(self._delai)
        return self._corps


class _SessionLente(_Session):
    """Une bourse qui met longtemps à répondre."""

    def __init__(self, lente, delai):
        super().__init__()
        self.lente, self.delai = lente, delai

    def get(self, url, headers=None, **kwargs):
        if url == self.lente:
            self.lues.append(url)
            return _ReponseLente(self.corps[url], self.delai)
        return super().get(url, headers=headers, **kwargs)


def test_une_source_lente_ne_fait_pas_attendre_le_visiteur(monkeypatch):
    monkeypatch.setattr(m, "_ATTENTE_COLLECTE_S", 0.05)
    marches = m.Marches()
    session = _SessionLente(m.SOURCES_INDICES["brvm_c"], delai=0.5)

    async def scenario():
        debut = asyncio.get_running_loop().time()
        premier, second = await asyncio.gather(
            marches.apercu(session_http=session), marches.apercu(session_http=session)
        )
        duree = asyncio.get_running_loop().time() - debut
        await marches._collecte  # la collecte, elle, va au bout
        return premier, second, duree

    premier, second, duree = asyncio.run(scenario())

    assert duree < 0.4
    # Une seule collecte pour les deux visiteurs simultanés.
    assert session.lues.count(m.SOURCES_INDICES["brvm_c"]) == 1
    assert "brvm_c" in marches.indices and marches.lus_a["brvm_c"] > 0


def test_le_classeur_est_lu_hors_de_la_boucle(monkeypatch):
    dans_la_boucle = []
    lire = m.lire_pink_sheet

    def lire_observe(contenu):
        try:
            asyncio.get_running_loop()
            dans_la_boucle.append(True)
        except RuntimeError:
            dans_la_boucle.append(False)
        return lire(contenu)

    monkeypatch.setattr(m, "lire_pink_sheet", lire_observe)

    apercu = asyncio.run(m.Marches().apercu(session_http=_Session()))

    assert dans_la_boucle == [False] and apercu["cours"]["mois"] == "2026-10"


def test_reponse_annoncee_trop_volumineuse_non_lue():
    class _SessionLourde(_Session):
        def get(self, url, headers=None, **kwargs):
            reponse = super().get(url, headers=headers, **kwargs)
            if url == m.SOURCES_INDICES["dzair"]:
                reponse.headers = {"Content-Length": "999999999999"}  # près de 1 To annoncé
            return reponse

    marches = m.Marches()
    apercu = asyncio.run(marches.apercu(session_http=_SessionLourde()))

    assert "dzair" not in [i["cle"] for i in apercu["indices"]]
    assert "brvm_c" in [i["cle"] for i in apercu["indices"]]

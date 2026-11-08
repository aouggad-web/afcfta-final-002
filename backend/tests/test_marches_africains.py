"""Tableau de bord de direction : cours de la Banque mondiale et indices des
bourses africaines (08/11/2026). Extraits réels des pages officielles."""

import asyncio
import io

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
               "2026M10": [125, 100, 4105, 420, "…"]}
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


def test_ngx_ouverture_tenue_par_la_memoire():
    lu = m.lire_ngx(NGX)
    premier, memoire = m.suivre_ngx(lu, None)
    assert premier["ouverture"] is None and premier["cloture"] == 248877.22
    # Même valeur (pas de nouvelle séance) : rien ne bouge.
    meme, memoire = m.suivre_ngx(lu, memoire)
    assert meme["ouverture"] is None
    # Nouvelle séance : l'ancienne clôture devient l'ouverture.
    suivant, memoire = m.suivre_ngx({**lu, "cloture": 250000.0}, memoire)
    assert suivant["ouverture"] == 248877.22 and suivant["cloture"] == 250000.0


@pytest.mark.parametrize("lecteur", [m.lire_sgbv, m.lire_brvm, m.lire_nse])
def test_page_modifiee_signalee(lecteur):
    with pytest.raises(ValueError):
        lecteur("<html>page refaite</html>")


class _Reponse:
    def __init__(self, corps, statut=200):
        self._corps, self.status = corps, statut

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
    def __init__(self, pannes=()):
        self.pannes = set(pannes)
        self.lues = []
        self.corps = {
            m.PAGE_BANQUE_MONDIALE: PAGE_BM,
            m.lien_pink_sheet(PAGE_BM): _pink_sheet(),
            m.SOURCES_INDICES["dzair"]: SGBV,
            m.SOURCES_INDICES["brvm_c"]: BRVM,
            m.SOURCES_INDICES["ngx_asi"]: NGX,
            m.SOURCES_INDICES["nse20"]: NSE,
        }

    def get(self, url, **kwargs):
        self.lues.append(url)
        return _Reponse("", 503) if url in self.pannes else _Reponse(self.corps[url])


def test_apercu_complet_puis_cache():
    marches = m.Marches()
    session = _Session()
    apercu = asyncio.run(marches.apercu(session_http=session))
    assert apercu["cours"]["mois"] == "2026-10" and "lien" not in apercu["cours"]
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
    marches.indices_lus_a = 0  # délai écoulé
    apercu = asyncio.run(marches.apercu(session_http=_Session(pannes={m.SOURCES_INDICES["brvm_c"]})))
    brvm = next(i for i in apercu["indices"] if i["cle"] == "brvm_c")
    assert brvm["cloture"] == 520.74 and brvm["a_jour"] is False


def test_meme_edition_du_pink_sheet_non_retelechargee():
    marches = m.Marches()
    asyncio.run(marches.apercu(session_http=_Session()))
    marches.cours_lu_a = marches.indices_lus_a = 0
    session = _Session()
    asyncio.run(marches.apercu(session_http=session))
    assert m.lien_pink_sheet(PAGE_BM) not in session.lues

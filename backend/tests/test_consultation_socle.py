"""Consultation du tarif par le socle : les sous-positions proposées à l'écran
sont celles que POST /calcul sait liquider, et les formalités sont celles que
la source publie pour la position."""

import importlib
import importlib.util
import os
import re
import sys

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from services import socle
from services.designation import texte_designation

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

pytestmark = pytest.mark.skipif(
    not all(os.path.exists(os.path.join(socle.SOCLE_DIR, f"{iso}.json")) for iso in ("TUN", "EGY", "DZA", "MAR", "KEN", "ZAF")),
    reason="socle absent : python3 scripts/build_socle.py",
)


def _module(nom):
    spec = importlib.util.spec_from_file_location(f"routes_{nom}_test", os.path.join(BACKEND, "routes", f"{nom}.py"))
    module = importlib.util.module_from_spec(spec)
    sys.modules[f"routes_{nom}_test"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def client():
    # Sans la garde d'accès, posée à l'inclusion dans routes/__init__.py : ces
    # tests lisent le tarif, pas le contrôle d'accès (test_acces_par_formule.py).
    app = FastAPI()
    consultation = _module("consultation")
    app.include_router(consultation.router)
    app.include_router(consultation.router_reglementation)
    app.include_router(_module("calcul").router)
    return TestClient(app)


def test_sous_positions_lues_au_socle(client):
    reponse = client.get("/consultation/TUN/sous-positions/870323")
    assert reponse.status_code == 200
    corps = reponse.json()
    assert corps["source"] == "socle"
    assert corps["total"] == len(corps["sub_positions"]) > 1
    premiere = corps["sub_positions"][0]
    assert premiere["code"].startswith("870323") and premiere["digits"] == 10
    assert "cle_controle" in premiere
    assert isinstance(premiere["description_fr"], str) and premiere["description_fr"]


def test_le_droit_de_douane_est_celui_du_socle(client):
    ligne = client.get("/consultation/EGY/sous-positions/220830").json()["sub_positions"][0]
    assert ligne["code"] == "2208300000" and ligne["dd_rate"] == 3000.0


def test_memes_positions_que_le_calcul_en_reclame(client):
    """Un SH6 à plusieurs positions : la liste servie est exactement celle que
    POST /calcul nomme dans son refus POSITION_NATIONALE_REQUISE."""
    refus = client.post("/calcul", json={"destination": "TUN", "code_sh": "870323", "valeur_cif": 1000})
    assert refus.status_code == 422
    attendues = [p["code"] for p in refus.json()["detail"]["positions"]]
    servies = [p["code"] for p in client.get("/consultation/TUN/sous-positions/870323").json()["sub_positions"]]
    assert servies == attendues


def test_pays_hors_socle_et_code_invalide(client):
    assert client.get("/consultation/XXX/sous-positions/010121").status_code == 503
    assert client.get("/consultation/EGY/sous-positions/12").status_code == 422


def _formalites(client, iso, code):
    reponse = client.get(f"/consultation/{iso}/formalites/{code}")
    assert reponse.status_code == 200
    return reponse.json()


def test_algerie_la_fiche_dgd_de_la_position(client):
    corps = _formalites(client, "DZA", "0101.21.11.00")
    assert corps["statut"] == "DOCUMENTEES" and corps["reserve"] is None
    assert [f["code"] for f in corps["formalities"]] == ["160", "180"]
    # Source exhaustive : une fiche sans tableau est un constat, pas une lacune.
    corps = _formalites(client, "DZA", "1520002000")
    assert corps["statut"] == "AUCUNE_FORMALITE_PARTICULIERE" and corps["formalities"] == []


def test_egypte_l_arabe_officiel_et_la_traduction_signalee(client):
    formalite = _formalites(client, "EGY", "0101210000")["formalities"][0]
    assert formalite["texte"].startswith(formalite["code"])
    assert formalite["traduction_non_officielle"] is True
    assert formalite["document_fr"] != formalite["texte"]


def test_maroc_le_constat_n_est_que_celui_de_la_source(client):
    """« Aucun document à présenter » est publié par l'ADIL pour la position ;
    une position sans mention reste « non établies »."""
    assert _formalites(client, "MAR", "2201100090")["statut"] == "AUCUNE_FORMALITE_PARTICULIERE"
    corps = _formalites(client, "MAR", "0201100011")
    assert corps["statut"] == "NON_ETABLIES" and "absence d'obligation" in corps["reserve"]


def test_sans_source_et_position_introuvable(client):
    assert _formalites(client, "KEN", "01012900")["statut"] == "NON_ETABLIES"
    corps = _formalites(client, "MAR", "9999999999")
    assert corps["statut"] == "POSITION_INTROUVABLE" and corps["reserve"]


def _recherche(client, iso3, q, **params):
    reponse = client.get(f"/consultation/{iso3}/recherche", params={"q": q, **params})
    assert reponse.status_code == 200
    return reponse.json()


def test_recherche_par_code_lue_au_socle(client):
    corps = _recherche(client, "TUN", "0902.10")
    assert corps["source"] == "socle"
    codes = [r["code"] for r in corps["results"]]
    assert codes == sorted(codes) and codes and all(c.startswith("090210") for c in codes)
    assert set(codes) <= set(socle.charger("TUN")["positions"])


def test_recherche_par_mots_sans_accents_ni_casse(client):
    assert _recherche(client, "KEN", "café")["results"] == _recherche(client, "KEN", "CAFE")["results"]
    corps = _recherche(client, "MAR", "thé vert")
    assert corps["total"] >= 1 and all(r["code"].startswith("0902") for r in corps["results"])


def test_recherche_un_mot_commence_un_mot_de_la_designation(client):
    """« vert » ne trouve pas « invertebrates », ni « thé » l'article anglais."""
    assert all(r["code"].startswith("0902") for r in _recherche(client, "MAR", "thé vert")["results"])
    the = _recherche(client, "MAR", "thé", limit=100)
    assert the["total"] < 200 and any(r["code"].startswith("0902") for r in the["results"])
    assert _recherche(client, "TUN", "..")["total"] == 0


def test_recherche_un_code_mele_aux_mots_borne_le_code(client):
    corps = _recherche(client, "MAR", "87.03 voiture")
    assert corps["total"] >= 1 and all(r["code"].startswith("8703") for r in corps["results"])


def test_recherche_textes_prepares_une_fois_par_chargement(client):
    module = sys.modules["routes_consultation_test"]
    positions = socle.charger("KEN")["positions"]
    _recherche(client, "KEN", "coffee", langue="en")
    assert module._textes["KEN"][0] is positions
    premier = module._textes["KEN"][2]
    _recherche(client, "KEN", "tea", langue="en")
    assert module._textes["KEN"][2] is premier
    assert module._textes["KEN"][1] == "en"  # KEN publie en anglais


def test_recherche_l_intitule_sh4_situe_une_ligne_sans_designation_propre(client):
    """« Other » sous 2402 : trouvée par « cigarettes », située par l'intitulé SH4."""
    corps = _recherche(client, "ZAF", "cigarettes", limit=2, langue="en")
    assert corps["total"] > len(corps["results"]) == 2
    ligne = corps["results"][0]
    assert ligne["hs6"] == ligne["code"][:6] and ligne["digits"] == len(ligne["code"])
    assert "cigarettes" in ligne["intitule_sh4"].lower()


def test_recherche_ne_sert_que_le_droit_de_douane(client):
    """Ni total ni TVA : le montant des droits et taxes est celui de POST /calcul."""
    ligne = _recherche(client, "KEN", "coffee", langue="en")["results"][0]
    assert set(ligne) == {
        "code", "hs6", "digits", "description_fr", "description_en", "intitule_sh4", "dd_rate", "dd_expression"
    }


def test_recherche_pays_invalide_ou_hors_socle(client):
    assert client.get("/consultation/zz/recherche", params={"q": "cafe"}).status_code == 422
    assert client.get("/consultation/XXX/recherche", params={"q": "cafe"}).status_code == 503
    assert client.get("/consultation/KEN/recherche", params={"q": "a"}).status_code == 422


def test_recherche_les_mots_entiers_d_abord_puis_par_code(client):
    """« thé » : le thé (0902) avant « théophylline » (2939), bien que 2939
    vienne après 0902 et 0302 avant ; dans chaque groupe, l'ordre du code."""
    codes = [r["code"] for r in _recherche(client, "MAR", "thé", limit=100)["results"]]
    the = [c for c in codes if c.startswith("0902")]
    assert codes[: len(the)] == the == sorted(the)
    assert codes.index(next(c for c in codes if c.startswith("2939"))) > len(the)
    reste = codes[len(the):]
    assert any(c < the[0] for c in reste)  # un début de mot classé plus bas que son code


def test_recherche_dans_la_langue_de_l_interface(client):
    """Français : le tarif en français ; anglais : le tarif en anglais."""
    assert _recherche(client, "DZA", "lait")["total"] > 0
    assert _recherche(client, "DZA", "lait", langue="en")["total"] == 0
    assert _recherche(client, "DZA", "milk", langue="en")["total"] > 0  # libellés SH6 anglais
    assert _recherche(client, "KEN", "coffee", langue="en")["total"] > 0
    assert _recherche(client, "KEN", "coffee")["total"] == 0
    assert _recherche(client, "KEN", "café")["total"] > 0  # libellés SH6 français
    corps = _recherche(client, "MAR", "tea", langue="en")
    assert corps["langue"] == "en" and corps["results"][0]["code"].startswith("0902")
    assert client.get("/consultation/KEN/recherche", params={"q": "tea", "langue": "de"}).status_code == 422


def test_recherche_q_bornee_a_2000_caracteres(client):
    """Constat E2 : au-delà de 2 000 caractères, la requête est refusée."""
    q = ("huile " * 334)[:2000]
    assert client.get("/consultation/TUN/recherche", params={"q": q}).status_code == 200
    assert client.get("/consultation/TUN/recherche", params={"q": q + "x"}).status_code == 422
    assert client.get("/consultation/TUN/recherche", params={"q": "1" * 2001}).status_code == 422


def test_recherche_la_plus_longue_designation_collee_est_acceptee(client):
    """Coller une désignation nationale reste possible : au Maroc, certaines
    dépassent 1 000 caractères."""
    positions = socle.charger("MAR")["positions"].values()
    plus_longue = max((texte_designation(p.get("designation"), "fr") or "" for p in positions), key=len)
    assert 1000 < len(plus_longue) <= 2000
    assert client.get("/consultation/MAR/recherche", params={"q": plus_longue}).status_code == 200


def test_recherche_un_mot_repete_ne_compte_qu_une_fois(client, monkeypatch):
    """Constat E2 : « de de de … » ne prépare qu'un couple de motifs, et
    trouve ce que trouve « de »."""
    attendu = _recherche(client, "TUN", "de")
    motifs = []

    class _ReCompte:
        def __getattr__(self, nom):
            return getattr(re, nom)

        def compile(self, motif, *args):
            motifs.append(motif)
            return re.compile(motif, *args)

    monkeypatch.setattr(sys.modules["routes_consultation_test"], "re", _ReCompte())
    corps = _recherche(client, "TUN", ("de " * 100).strip())
    assert len(motifs) == 2
    assert corps["total"] == attendu["total"] and corps["results"] == attendu["results"]


@pytest.mark.parametrize(
    "module",
    [
        "services.authentic_tariff_service",
        "services.tariff_provider_service",
        "services.postgres_tariff_service",
        "services.national_legal_calculation_service",
        "services.export_tariff_service",
        "engine.national_customs_calculation",
        "routes.authentic_tariffs",
        "routes.postgres_tariffs",
        "routes.hs6_database",
        "routes.search",
        "search.hs_code_search",
    ],
)
def test_l_ancien_service_est_retire(module):
    """Une seule recherche (celle-ci), une seule consultation, un seul calcul
    (POST /calcul) : l'ancien service et ses routes ne reviennent pas."""
    assert importlib.util.find_spec(module) is None


def test_l_ancienne_table_de_profils_est_retiree():
    from services import tax_profile_data

    assert not hasattr(tax_profile_data, "COUNTRY_TAX_PROFILES")


def test_un_droit_compose_se_lit_en_entier(client):
    """« 10% or 55c/kg less 90% » (ZAF 1901.90.10) : 10 % n'est qu'une
    composante. L'écran n'affiche le taux que s'il est le droit entier ; ici,
    l'expression."""
    lignes = client.get("/consultation/ZAF/sous-positions/190190").json()["sub_positions"]
    ligne = next(l for l in lignes if l["code"] == "19019010")
    assert ligne["dd_rate"] is None
    assert ligne["dd_expression"] == "10% or 55c/kg less 90%"


# ── Fiche de la position : droits, taxes et restrictions, lus au socle ───────
# Le panneau « Réglementation » du calculateur lisait un moteur dont les
# fichiers de lignes ne sont pas livrés : il répondait « Pays DZA non
# disponible » pour tous les pays. Il lit désormais le socle, comme le calcul.


def test_fiche_les_droits_de_la_position_tels_que_le_socle_les_porte(client):
    corps = client.get("/consultation/DZA/position/0201101100").json()
    assert corps["success"] is True and corps["source"] == "socle"
    assert corps["code"] == "0201101100" and corps["niveau"] == "national" and corps["hs6"] == "020110"
    assert "veaux" in corps["description_fr"]
    taux = {d["code"]: d["taux"] for d in corps["droits"]}
    assert taux["DD"] == 5.0 and taux["TCS"] == 3.0
    # Chaque ligne dit sur quoi elle porte et d'où elle vient.
    dd = next(d for d in corps["droits"] if d["code"] == "DD")
    assert dd["assiette"] == "CIF" and dd["source"] and dd["famille"] == "droit"


def test_fiche_les_droits_sont_ceux_que_le_calcul_liquide(client):
    """Une seule source : les taux de la fiche sont ceux des lignes de POST /calcul."""
    fiche = client.get("/consultation/DZA/position/0201101100").json()["droits"]
    calcul = client.post(
        "/calcul", json={"destination": "DZA", "code_sh": "0201101100", "valeur_cif": 1000}
    ).json()["npf"]["lignes"]
    assert {d["code"]: d["taux"] for d in fiche} == {l["code"]: l["taux_pct"] for l in calcul}


def test_fiche_un_droit_compose_se_lit_en_entier(client):
    """Même règle que les sous-positions : 10 % n'est qu'une composante."""
    fiche = client.get("/consultation/ZAF/position/19019010").json()
    dd = next(d for d in fiche["droits"] if d["code"] == "DD")
    assert dd["taux"] is None
    assert dd["expression"] == "10% or 55c/kg less 90%"


def test_fiche_un_taux_absent_reste_null_et_jamais_zero(client):
    """EGY 0206.80.00 : la source ne publie aucun taux de DD. « null » se lit
    « à compléter » ; 0 se lirait « exonéré »."""
    fiche = client.get("/consultation/EGY/position/0206800000").json()
    dd = next(d for d in fiche["droits"] if d["code"] == "DD")
    assert dd["taux"] is None and dd["expression"] is None


def test_fiche_dit_quand_la_source_ne_publie_pas_la_tva(client):
    """Une liste sans TVA ne doit pas se lire « aucune TVA » : la couverture
    nomme la famille que la source ne publie pas (ZAF : le crawl SARS n'en
    porte aucune)."""
    couverture = client.get("/consultation/ZAF/position/19019010").json()["couverture"]
    assert couverture["tva"] is False and "TVA" in couverture["motif"]
    assert client.get("/consultation/DZA/position/0201101100").json()["couverture"]["tva"] is True


def _requiert_socle(*pays):
    """Saute le test si l'un de ces pays n'est pas construit (le module ne garde
    que six pays) : un socle partiel ne doit pas faire échouer ce qu'il ne sert pas."""
    return pytest.mark.skipif(
        not all(os.path.exists(os.path.join(socle.SOCLE_DIR, f"{iso}.json")) for iso in pays),
        reason=f"socle absent : {' '.join(pays)}",
    )


def test_fiche_les_restrictions_sont_servies_telles_que_publiees(client):
    corps = client.get("/consultation/EGY/position/0101210000").json()
    assert len(corps["restrictions"]) == 1
    restriction = corps["restrictions"][0]
    assert restriction["texte"].startswith("ق3034") and restriction["source"]
    assert client.get("/consultation/DZA/position/0201101100").json()["restrictions"] == []


@_requiert_socle("LBY")
def test_fiche_une_interdiction_d_importation_se_lit(client):
    """La Libye écrit ses restrictions sous une autre forme que l'Égypte
    (type / verbatim / libelle_fr / portee). Lue sous une seule forme, la
    seconde donnait une carte vide : une position interdite se présentait comme
    une position aux taux incomplets."""
    corps = client.get("/consultation/LBY/position/01031000").json()
    assert corps["restrictions"] == [
        {
            "type": "IMPORTATION_INTERDITE",
            "libelle": "Importation interdite",
            "texte": "ممنوع استيراده",
            "portee": "NPF et Ligue arabe",
            "source": corps["restrictions"][0]["source"],
        }
    ]
    assert corps["restrictions"][0]["source"].startswith("customs.gov.ly")


@_requiert_socle("LBY")
def test_fiche_toutes_les_restrictions_ont_la_meme_forme_et_un_texte(client):
    """Toutes les interdictions libyennes et un échantillon des restrictions
    égyptiennes : mêmes clés, et un texte à afficher — une restriction sans
    texte serait invisible. Les positions viennent du socle, pas d'une liste, et
    le nombre de restrictions vues est celui du socle : un balayage qui ne verrait
    rien (route qui n'en sert plus) passerait sinon pour réussi."""
    cles = {"type", "libelle", "texte", "portee", "source"}
    attendues = vues = 0
    for iso3, limite in (("LBY", None), ("EGY", 60)):
        positions = socle.charger(iso3)["positions"]
        avec = [c for c, p in positions.items() if p.get("restrictions")]
        for code in avec if limite is None else avec[:limite]:
            attendues += len(positions[code]["restrictions"])
            for restriction in client.get(f"/consultation/{iso3}/position/{code}").json()["restrictions"]:
                vues += 1
                assert set(restriction) == cles and restriction["texte"], (iso3, code, restriction)
    assert vues == attendues > 0


@_requiert_socle("LBY")
def test_fiche_la_designation_arabe_est_servie(client):
    """LBY : le « verbatim » français et anglais est le code lui-même ; la
    désignation existe en arabe, et elle se sert."""
    corps = client.get("/consultation/LBY/position/01031000").json()
    assert re.search(r"[\u0600-\u06FF]", corps["description_ar"])


def test_fiche_un_code_national_inexistant_sert_la_ligne_sh6_sous_son_vrai_code(client):
    """ZAF publie des lignes SH6 : un code national qui n'existe pas retombe sur
    la ligne du SH6, et le dit — « code » est celui de la ligne servie, pas le
    code saisi, que le tarif ne publie pas."""
    corps = client.get("/consultation/ZAF/position/0101210000").json()
    assert corps["niveau"] == "hs6" and corps["code"] == "010121" and corps["hs6"] == "010121"


def test_fiche_une_position_nationale_garde_son_code(client):
    corps = client.get("/consultation/DZA/position/0201101100").json()
    assert corps["niveau"] == "national" and corps["code"] == "0201101100"
    # TUN : la clé de contrôle saisie avec la position ne change pas la position.
    tunisie = client.get("/consultation/TUN/position/01012100015").json()
    assert tunisie["niveau"] == "national" and tunisie["code"] == "0101210001"


@_requiert_socle("COM")
def test_fiche_une_moyenne_statistique_n_est_pas_un_taux_publie(client):
    """Comores, Soudan, Sao Tomé : le « droit de douane » est une moyenne WITS/
    UNCTAD-TRAINS au SH6, pas le tarif national. Le calcul le déclare INDICATIF ;
    la fiche le marque, avec le même prédicat."""
    droits = {d["code"]: d for d in client.get("/consultation/COM/position/010121").json()["droits"]}
    assert droits["DD"]["base_statistique"] is True
    national = client.get("/consultation/DZA/position/0201101100").json()["droits"]
    assert not any(d["base_statistique"] for d in national)


@_requiert_socle("STP")
def test_fiche_un_droit_national_d_un_pays_a_moyennes_n_est_pas_marque(client):
    """Sao Tomé : 140 positions portent un droit national (Lei n.º 04/2023) sous
    un libellé « WITS/TRAINS ». C'est la source qui décide, pas le libellé."""
    positions = socle.charger("STP")["positions"]
    code = next(
        (
            c
            for c, p in positions.items()
            if any(
                d.get("code") == "DD" and "Lei" in (d.get("source") or "") and "WITS" not in (d.get("source") or "")
                for d in p["droits"]
            )
        ),
        None,
    )
    if code is None:
        pytest.skip("aucun droit national à Sao Tomé dans ce socle")
    droits = {d["code"]: d for d in client.get(f"/consultation/STP/position/{code}").json()["droits"]}
    assert droits["DD"]["base_statistique"] is False


def test_fiche_les_usages_qui_substituent_un_regime_sont_nommes(client):
    """EGY 3401.19.00.10 : pour l'usage domestique, une taxe de Table de 5 %
    remplace la TVA de 14 %. Les lignes servies sont celles du régime courant ;
    la fiche nomme l'usage qui en change."""
    corps = client.get("/consultation/EGY/position/3401190010").json()
    assert [u["code"] for u in corps["usages"]] == ["USAGE_DOMESTIQUE"]
    assert corps["usages"][0]["libelle"] and corps["usages"][0]["texte"]
    assert client.get("/consultation/DZA/position/0201101100").json()["usages"] == []


def test_fiche_un_sh6_a_plusieurs_positions_demande_le_choix(client):
    """Même réponse que POST /calcul : le choix revient à l'opérateur."""
    refus = client.get("/consultation/TUN/position/870323")
    assert refus.status_code == 422
    detail = refus.json()["detail"]
    assert detail["code"] == "POSITION_NATIONALE_REQUISE"
    attendues = client.post("/calcul", json={"destination": "TUN", "code_sh": "870323", "valeur_cif": 1000})
    assert [p["code"] for p in detail["positions"]] == [p["code"] for p in attendues.json()["detail"]["positions"]]


def test_fiche_position_absente_code_invalide_et_pays_hors_socle(client):
    absente = client.get("/consultation/DZA/position/9999999999")
    assert absente.status_code == 404
    assert absente.json()["detail"].startswith("DZA/9999999999 : position absente du socle")
    assert client.get("/consultation/DZA/position/abc").status_code == 422
    assert client.get("/consultation/XXX/position/020110").status_code == 503


def test_fiche_porte_les_champs_de_la_position_du_socle(client):
    """Chapitre, unité, désignation anglaise, assiette et note de chaque ligne :
    ce que le socle porte, ni plus ni moins. Les valeurs viennent du socle, pas
    d'un tarif figé qu'un nouveau crawl ferait changer."""
    for iso3, code in (("DZA", "0201101100"), ("ZAF", "19019010"), ("EGY", "0101210000")):
        position, _ = socle.position(iso3, code)
        corps = client.get(f"/consultation/{iso3}/position/{code}").json()
        assert corps["chapitre"] == position["chapitre"] and corps["hs6"] == position["hs6"]
        assert corps["unite"] == position.get("unite")
        assert corps["description_en"] == texte_designation(position.get("designation"), "en")
        assert [d["note"] for d in corps["droits"]] == [d.get("note") for d in position["droits"]]
        assert [d["assiette"] for d in corps["droits"]] == [d.get("assiette") for d in position["droits"]]


def test_fiche_une_mesure_de_defense_commerciale_n_est_pas_un_taux_manquant(client):
    """ZAF : un droit antidumping ou de sauvegarde n'a pas de taux unique, il
    dépend de l'origine, du producteur ou du produit. Servi sans taux ni drapeau,
    il se lisait « la source ne publie pas de taux » : un manque, là où il y a une
    mesure conditionnelle. La position vient du socle (ces mesures ont un terme)."""
    positions = socle.charger("ZAF")["positions"]
    code, ligne = next(
        ((c, d) for c, p in positions.items() for d in p["droits"] if d.get("defense_commerciale")),
        (None, None),
    )
    if code is None:
        pytest.skip("aucune mesure de défense commerciale à ce jour dans le socle ZAF")
    droits = client.get(f"/consultation/ZAF/position/{code}").json()["droits"]
    assert next(d for d in droits if d["code"] == ligne["code"])["conditionnel"] is True
    assert not any(d["conditionnel"] for d in client.get("/consultation/DZA/position/0201101100").json()["droits"])

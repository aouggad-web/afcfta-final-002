"""Un taux réduit réel doit atteindre l'écran.

`postgres_tariff_service.get_commodity_details()` émettait ses avantages
fiscaux sous la clé `reduced_rate`, alors que `RegulatoryDetailsPanel.jsx` lit
`adv.reduced_rate_pct` — et que `authentic_tariff_service.py` émet bien
`reduced_rate_pct`. Un seul des deux producteurs était donc lu.

Conséquence à l'écran : `{adv.reduced_rate_pct}%` avec une valeur absente rend
« % » sans chiffre. Le taux réduit existait en base, il était acquis, et
l'opérateur ne le voyait pas. C'est un G2 — le produit cache du vrai.

Le nom canonique est `reduced_rate_pct` : c'est celui que
`test_regulatory_engine.py` verrouille déjà, celui de l'autre producteur, et
celui du panneau. Le service PostgreSQL était l'exception.

Le contrôle négatif de ce lot est le plus utile : il compare les DEUX
producteurs et le consommateur dans le code source, de sorte qu'aucun ne peut
re-divorcer des autres en silence — c'est la divergence elle-même qui était le
défaut, pas la valeur d'une clé.
"""

import os
import re
import sqlite3
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.postgres_tariff_service import PostgresTariffService  # noqa: E402

RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PANNEAU = os.path.join(
    RACINE, "frontend", "src", "components", "calculator", "RegulatoryDetailsPanel.jsx"
)
SERVICE_PG = os.path.join(RACINE, "backend", "services", "postgres_tariff_service.py")
SERVICE_AUTH = os.path.join(RACINE, "backend", "services", "authentic_tariff_service.py")

CLE_CANONIQUE = "reduced_rate_pct"


@pytest.fixture
def provider():
    """Les mêmes fixtures relationnelles isolées que le reste du dossier.

    Lignes sentinelles `ZZZ` : jamais de la donnée tarifaire d'application.
    """
    db = sqlite3.connect(":memory:")
    db.row_factory = sqlite3.Row
    db.executescript(
        """
        CREATE TABLE commodities (id INTEGER, country_iso3 TEXT, national_code TEXT,
          hs6 TEXT, digits INTEGER, description_fr TEXT, description_en TEXT,
          chapter TEXT, category TEXT, unit TEXT, sensitivity TEXT,
          total_npf_pct REAL, total_zlecaf_pct REAL, savings_pct REAL);
        CREATE TABLE measures (commodity_id INTEGER, measure_type TEXT, code TEXT,
          name_fr TEXT, name_en TEXT, rate_pct REAL, is_zlecaf_applicable INTEGER,
          zlecaf_rate_pct REAL, observation TEXT);
        CREATE TABLE requirements (commodity_id INTEGER, requirement_type TEXT,
          code TEXT, document_fr TEXT, document_en TEXT, is_mandatory INTEGER,
          issuing_authority TEXT);
        CREATE TABLE fiscal_advantages (commodity_id INTEGER, tax_code TEXT,
          reduced_rate_pct REAL, condition_fr TEXT, condition_en TEXT);
        INSERT INTO commodities VALUES
          (1,'ZZZ','00000001','000000',8,'A','A','00','cat','u','none',99,88,11);
        INSERT INTO fiscal_advantages VALUES
          (1,'DD',2.5,'Condition de test','Test condition'),
          (1,'TVA',0.0,'Exonération de test','Test exemption');
    """
    )
    service = PostgresTariffService.__new__(PostgresTariffService)
    service._execute_query = lambda query, params=None: [
        dict(row) for row in db.execute(query, params or {}).fetchall()
    ]
    yield service, db
    db.close()


def _avantages(service):
    details = service.get_commodity_details("ZZZ", "00000001")
    assert details is not None, "la position sentinelle doit se résoudre"
    return {a["tax_code"]: a for a in details["fiscal_advantages"]}


def test_le_taux_reduit_est_emis_sous_le_nom_que_l_ecran_lit(provider):
    """Le cœur du correctif."""
    service, _ = provider
    par_taxe = _avantages(service)
    assert par_taxe["DD"][CLE_CANONIQUE] == 2.5
    assert par_taxe["TVA"][CLE_CANONIQUE] == 0.0


def test_l_ancien_nom_ne_subsiste_pas_en_double(provider):
    """Émettre les deux clés « pour ne rien casser » serait pire.

    Deux noms pour la même valeur, et le prochain qui passe ne sait plus lequel
    fait foi ; l'un des deux finit par dériver, et on est revenu au défaut.
    """
    service, _ = provider
    for avantage in _avantages(service).values():
        assert "reduced_rate" not in avantage, (
            "l'ancienne clé ne doit pas cohabiter avec la nouvelle : "
            "un seul nom fait foi"
        )


def test_un_taux_reduit_a_zero_reste_servi(provider):
    """Contrôle négatif : 0 % est une exonération, pas une absence.

    Une exonération totale est l'avantage fiscal le plus intéressant pour
    l'opérateur. La traiter comme une valeur manquante — parce qu'elle est
    « fausse » au sens booléen — la ferait disparaître de l'écran.
    """
    service, _ = provider
    tva = _avantages(service)["TVA"]
    assert tva[CLE_CANONIQUE] == 0.0
    assert tva[CLE_CANONIQUE] is not None


# ─────────────────────────────────────────────────────────────────────────────
# LE CONTRÔLE NÉGATIF QUI COMPTE : la divergence elle-même était le défaut.
#
# Un test qui vérifie seulement la valeur de la clé laisse revenir le défaut à
# la première refonte. Ceux-ci lisent le SOURCE des deux producteurs et du
# consommateur, et tombent si l'un s'écarte des autres.
# ─────────────────────────────────────────────────────────────────────────────


def _source(chemin):
    with open(chemin, encoding="utf-8") as f:
        return f.read()


def test_les_deux_producteurs_emettent_la_meme_cle():
    """`postgres_tariff_service` et `authentic_tariff_service` doivent s'accorder."""
    for chemin in (SERVICE_PG, SERVICE_AUTH):
        src = _source(chemin)
        assert f'"{CLE_CANONIQUE}":' in src, (
            f"{os.path.basename(chemin)} doit émettre « {CLE_CANONIQUE} »"
        )
        # L'ancien nom ne doit plus apparaître comme clé émise. Il reste permis
        # comme nom de COLONNE SQL (`SELECT tax_code, reduced_rate_pct, …`),
        # que ce test ne touche pas.
        assert '"reduced_rate":' not in src, (
            f"{os.path.basename(chemin)} émet encore l'ancienne clé "
            "« reduced_rate » — c'est la divergence qui rendait le taux invisible"
        )


def test_le_panneau_lit_la_cle_que_le_backend_emet():
    """Et le consommateur doit lire ce même nom.

    Ce test lie les trois fichiers : si quelqu'un renomme la clé côté backend
    sans toucher au panneau — ou l'inverse — il tombe, au lieu de laisser un
    taux réel disparaître de l'écran sans bruit.
    """
    src = _source(PANNEAU)
    lectures = set(re.findall(r"adv\.(reduced_rate\w*)", src))
    assert lectures, "le panneau doit lire un taux réduit"
    assert lectures == {CLE_CANONIQUE}, (
        f"le panneau lit {sorted(lectures)} alors que le backend émet "
        f"« {CLE_CANONIQUE} »"
    )

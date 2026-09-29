import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'commun'))

import oec  # noqa: E402
import sources  # noqa: E402


def test_hs_id_prefixe_de_section():
    assert oec.hs_id('33') == '633'
    assert oec.hs_id('3304') == '63304'
    assert oec.hs_id('300490') == '6300490'
    assert oec.hs_id('0101') == '10101'
    assert oec.hs_id('3901') == '73901'


def test_sources_payantes_sans_cle_non_configurees(monkeypatch):
    monkeypatch.delenv('OEC_API_TOKEN', raising=False)
    assert sources.par_cle('oec_pro').statut() == 'non configurée'
    monkeypatch.setenv('OEC_API_TOKEN', 'x')
    assert sources.par_cle('oec_pro').statut() == 'disponible'


def test_registre_sans_doublon_et_sans_secret():
    cles = [s.cle for s in sources.SOURCES]
    assert len(cles) == len(set(cles))
    assert all(s.env == '' or s.env.isupper() for s in sources.SOURCES)


class _Marches:
    """Flux fictifs (USD/an) : imp/exp par pays et flux bilatéraux, même interface que verif_cibles.Marches."""

    def __init__(self, imp, exp, bil=None):
        self._i, self._e, self._b = imp, exp, bil or {}

    def imp(self, p):
        return self._i.get(p, {})

    def exp(self, p):
        return self._e.get(p, {})

    def bil(self, o, d):
        return self._b.get((o, d), {})


def test_verdict_marche_trop_petit_rejete_malgre_la_marge():
    import verif_cibles as vc  # noqa: E402
    m = _Marches({'MAR': {'080510': 1.4e6}}, {'MAR': {'080510': 51e6}, 'EGY': {'080510': 900e6}})
    v, motifs, ind = vc.verdict('EGY', 'MAR', '080510', 40, 0, m)
    assert v == 'REJETÉE' and ind['marge'] == 40 and 'marché trop petit' in motifs[0]


def test_verdict_creneau_si_destination_exportatrice_nette():
    import verif_cibles as vc  # noqa: E402
    m = _Marches({'EGY': {'080410': 17e6}}, {'EGY': {'080410': 101e6}, 'DZA': {'080410': 150e6}})
    assert vc.verdict('DZA', 'EGY', '080410', 1, 0, m)[0] == 'CRÉNEAU'


def test_verdict_retenu_avec_reexportation_et_preference_partielle():
    import verif_cibles as vc  # noqa: E402
    m = _Marches({'DZA': {'040690': 105e6}, 'EGY': {'040690': 60e6}}, {'EGY': {'040690': 76e6}})
    v, motifs, ind = vc.verdict('EGY', 'DZA', '040690', 30, 26.67, m, (1, 9))
    assert v == 'RETENUE'
    assert any(x.startswith('réexportation') for x in motifs) and any('1 ligne(s) nationale(s) sur 9' in x for x in motifs)
    assert abs(vc.score(ind) - 76e6 * 3.33 / 100) < 1


def test_verdict_sans_marge_rejete():
    import verif_cibles as vc  # noqa: E402
    m = _Marches({'MAR': {'080410': 241e6}}, {'DZA': {'080410': 150e6}})
    assert vc.verdict('DZA', 'MAR', '080410', 40, 40, m)[1][0] == 'aucune marge servie en 2026'

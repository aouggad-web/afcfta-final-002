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

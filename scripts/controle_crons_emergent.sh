#!/usr/bin/env bash
# Contrôle des crons du pod Emergent (audit de sécurité : C3, point 17).
#
# Lecture seule. Appelé par sync_emergent.sh (étape 1bis) et, toutes les
# heures, par le backend (backend/surveillance_crons.py).
#
# Codes retour : 0 rien à signaler ; 1 anomalie, compromission possible du
# pod ; 2 contrôle incomplet (fichier illisible, manifeste absent).
#
# Emplacements réglables, pour les tests : EMERGENT_DIR (/app/.emergent),
# CRON_D (/etc/cron.d), CRON_SPOOL (/var/spool/cron/crontabs) et MANIFESTE
# (scripts/crons_emergent_sha256.txt). Les chemins écrits DANS les lignes de cron
# (/app/.emergent/cron/…, /app/backend/.env) restent ceux du pod.

EMERGENT_DIR="${EMERGENT_DIR:-/app/.emergent}"
CRON_D="${CRON_D:-/etc/cron.d}"
CRON_SPOOL="${CRON_SPOOL:-/var/spool/cron/crontabs}"
MANIFESTE="${MANIFESTE:-$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" >/dev/null && pwd)/crons_emergent_sha256.txt}"

# Persistance (audit de sécurité, C3) : webhook_crond.sh — script de la
# plateforme, non modifié ici — recopie à chaque démarrage du pod
# .emergent/cron/webhook-crons (gitignoré, donc jamais supprimé par git clean)
# dans /etc/cron.d et lance cron en root : une ligne plantée une fois survit
# aux synchronisations. On SIGNALE toute ligne hors de la grammaire d'Emergent :
# en-tête et ligne watch_crons relevés dans des rendus réels (historique git,
# commits 92d07699 et f5a14932) ; ligne dispatch_webhook déduite des variables
# lues par dispatch_webhook.sh. L'expression étant stricte, tout chaînage
# (; | & $ ` % ( ) …) est hors grammaire.
_check_emergent_crons() (
  # Sous-shell sans -e/-u : ce contrôle informe, il n'interrompt jamais le
  # déploiement. Code retour 1 en cas d'anomalie, 2 si le contrôle est
  # incomplet, rappelés en fin de sync_emergent.sh.
  set +eu
  export LC_ALL=C  # plages [A-Za-z] au sens octet, quelle que soit la locale du pod
  local env_ok='^(SHELL=/bin/sh|PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin|JOB_ID=[0-9a-f-]{36}|WEBHOOK_ENV_FILE=/app/backend/\.env|CRON_API_URL=https://[a-z0-9.-]+\.emergentagent\.com)$'
  # Séparateurs : espaces et tabulations seulement (un CR n'est pas un rendu Emergent).
  local b=$'[ \t]' f n line why b64 url host dup suspects=0
  local s="$b+" val='[A-Za-z0-9_.,:/+=@-]*' incomplet=0 nom attendu chemin
  local url_re='^https?://([A-Za-z0-9.-]+)(:[0-9]*)?([/?#].*)?$'
  # Affectation lue par sh : en début de mot (pas « CRON_NAME=xENDPOINT_URL_B64=… »).
  local ep_re="(^|${b})ENDPOINT_URL_B64=([^[:space:]]+)"
  local job_ok="^(@(hourly|daily|weekly|monthly|yearly|annually|midnight)|[0-9A-Za-z*/,-]+(${s}[0-9A-Za-z*/,-]+){4})${s}root"
  job_ok+="(${s}(CRON_API_URL=https://[a-z0-9.-]+\\.emergentagent\\.com|WEBHOOK_ENV_FILE=/app/backend/\\.env|(CRON_NAME|METHOD|ENDPOINT_URL_B64|JOB_ID|AT_DATE|END_DATE)=${val}))*"
  job_ok+="(${s}/bin/sh)?${s}/app/\\.emergent/cron/(dispatch_webhook|watch_crons)\\.sh"
  job_ok+="(${s}>>?${b}*(/var/log/webhook-cron\\.log|/dev/null)(${s}2>&1)?)?${b}*\$"
  # Anomalie hors d'une ligne de cron : comptée et affichée de la même façon.
  _signaler() {
    suspects=$((suspects + 1))
    printf '  ⚠ %s\n' "$(printf '%s' "$1" | tr -d '\000-\037\177' | cut -c1-220)"
  }
  # read de bash efface sans rien dire un octet NUL, que cron garde (il coupe
  # la commande à cet endroit) : un fichier qui en contient n'est pas lu.
  _octets_sains() { [ "$(tr -d '\011\012\040-\176' < "$1" | wc -c)" -eq 0 ]; }
  local masque='s/([A-Za-z_][A-Za-z0-9_]*)=[^[:space:]]*/\1=***/g; s/[A-Za-z0-9+_-]{20,}=*/***/g'
  for f in "$EMERGENT_DIR/cron/webhook-crons" "$CRON_D/webhook-crons"; do
    [ -f "$f" ] || { echo "  · $f : absent"; continue; }
    [ -r "$f" ] || { echo "  · $f : illisible, contrôle incomplet"; incomplet=1; continue; }
    _octets_sains "$f" || { _signaler "$f : octet de contrôle ou non ASCII"; continue; }
    n=0
    while IFS= read -r line || [ -n "$line" ]; do
      n=$((n + 1))
      [[ $line =~ ^[[:space:]]*(#.*)?$ || $line =~ $env_ok ]] && continue
      why=""
      if ! [[ $line =~ $job_ok ]]; then
        # Ligne brute affichée valeurs masquées (VAR=… et longues suites).
        why="hors forme Emergent : $(printf '%s' "$line" \
          | sed -E 's/([A-Za-z_][A-Za-z0-9_]*)=[^[:space:]]*/\1=***/g; s/[A-Za-z0-9+_-]{20,}=*/***/g')"
      else
        # Variable répétée : le contrôle lirait la première valeur, sh garde la dernière.
        dup="$(printf '%s\n' "$line" | grep -oE "(^|${b})[A-Z_][A-Z0-9_]*=" | tr -d $' \t' | sort | uniq -d | tr '\n' ' ')"
        if [ -n "$dup" ]; then
          why="variable répétée sur la ligne : $dup"
        elif [[ $line =~ $ep_re ]]; then
          # Hôte réellement contacté par curl, lu sur la valeur décodée ENTIÈRE
          # (jamais un préfixe) : l'autorité doit être un nom d'hôte nu (port
          # facultatif) — « https://x.emergentagent.com@tiers/ » ou un « \ »
          # viseraient le tiers et partent donc en « illisible ». Base64
          # invalide, octet hors ASCII imprimable (NUL, saut de ligne…) ou
          # valeur démesurée : « illisible » aussi.
          b64="${BASH_REMATCH[2]}" host=""
          if url="$(printf '%s' "$b64" | base64 -d 2>/dev/null)" \
            && [ "$(printf '%s' "$b64" | base64 -d 2>/dev/null | tr -d '\041-\176' | wc -c)" -eq 0 ] \
            && [ "${#url}" -le 2048 ] && [[ $url =~ $url_re ]]; then
            host="$(printf '%s' "${BASH_REMATCH[1]}" | tr '[:upper:]' '[:lower:]')"
            host="${host%.}"  # nom absolu « x.emergentagent.com. » : même hôte
          fi
          [[ $host =~ (^|\.)emergentagent\.com$ ]] \
            || why="dispatch vers un hôte hors emergentagent.com : ${host:-illisible}"
        fi
        # watch_crons.sh ne rend une ligne dispatch_webhook qu'à partir de
        # .emergent/crons.yml : sans ce fichier, aucune n'a lieu d'exister.
        if [ -z "$why" ] && [[ $line =~ dispatch_webhook\.sh ]] && [ ! -f "$EMERGENT_DIR/crons.yml" ]; then
          why="tâche dispatch_webhook alors que l'application ne déclare aucun cron (.emergent/crons.yml absent)"
        fi
        # Un crons.yml est lui-même vérifié par le manifeste, plus bas.
      fi
      [ -n "$why" ] || continue
      suspects=$((suspects + 1))
      printf '  ⚠ %s:%d : %s\n' "$f" "$n" "$(printf '%s' "$why" | tr -d '\000-\037\177' | cut -c1-220)"
    done < "$f"
  done
  if [ -f "$EMERGENT_DIR/cron/webhook-crons" ] && [ -f "$CRON_D/webhook-crons" ] \
    && ! cmp -s "$EMERGENT_DIR/cron/webhook-crons" "$CRON_D/webhook-crons"; then
    _signaler "$CRON_D/webhook-crons diffère de la copie persistante d'Emergent."
  fi
  # Sur le pod seulement (point 17 de l'audit) : le reste de /etc/cron.d, les
  # crontabs d'utilisateur et l'empreinte des scripts de la plateforme. Relevé
  # sur le pod le 06/11/2026 : .placeholder et e2scrub_all (Debian), plus
  # webhook-crons ; spool vide ; scripts identiques au dépôt.
  if [ -d "$EMERGENT_DIR/cron" ]; then
    local e2_ok='^(30 3 \* \* 0 root test -e /run/systemd/system \|\| SERVICE_MODE=1 /usr/lib/(aarch64|x86_64)-linux-gnu/e2fsprogs/e2scrub_all_cron|10 3 \* \* \* root test -e /run/systemd/system \|\| SERVICE_MODE=1 /(usr/)?sbin/e2scrub_all -A -r)$'
    for f in "$CRON_D"/* "$CRON_D"/.[!.]* "$CRON_D"/..?*; do
      [ -e "$f" ] || [ -L "$f" ] || continue
      nom="${f##*/}"
      case "$nom" in
        webhook-crons) ;;
        .placeholder | e2scrub_all)
          if [ ! -f "$f" ] || [ -L "$f" ] || [ ! -r "$f" ]; then
            _signaler "$f : n'est plus un fichier ordinaire lisible"
            continue
          fi
          _octets_sains "$f" || { _signaler "$f : octet de contrôle ou non ASCII"; continue; }
          n=0
          while IFS= read -r line || [ -n "$line" ]; do
            n=$((n + 1))
            [[ $line =~ ^[[:space:]]*(#.*)?$ ]] && continue
            [ "$nom" = e2scrub_all ] && [[ $line =~ $e2_ok ]] && continue
            _signaler "$f:$n : ligne hors forme Debian : $(printf '%s' "$line" | sed -E "$masque")"
          done < "$f"
          ;;
        *) _signaler "fichier inattendu dans $CRON_D : $nom" ;;
      esac
    done
    if [ -d "$CRON_SPOOL" ]; then
      if [ -r "$CRON_SPOOL" ] && [ -x "$CRON_SPOOL" ]; then
        for f in "$CRON_SPOOL"/* "$CRON_SPOOL"/.[!.]* "$CRON_SPOOL"/..?*; do
          [ -e "$f" ] || [ -L "$f" ] || continue
          _signaler "crontab d'utilisateur dans $CRON_SPOOL : ${f##*/}"
        done
      else
        echo "  · $CRON_SPOOL : illisible, contrôle incomplet"
        incomplet=1
      fi
    fi
    # Empreintes des scripts de la plateforme, versionnées dans le dépôt :
    # un script modifié sur le pod (persistance root) est signalé.
    local verifiees=0 crons_yml_au_manifeste=0
    if [ -r "$MANIFESTE" ]; then
      while read -r attendu chemin || [ -n "$attendu" ]; do
        [ -n "$attendu" ] || continue
        verifiees=$((verifiees + 1))
        [ "$chemin" = .emergent/crons.yml ] && crons_yml_au_manifeste=1
        f="$EMERGENT_DIR/${chemin#.emergent/}"
        if [ ! -f "$f" ] || [ ! -r "$f" ]; then
          _signaler "script de la plateforme absent ou illisible : $chemin"
        elif [ "$(sha256sum "$f" | cut -d' ' -f1)" != "$attendu" ]; then
          _signaler "script de la plateforme modifié : $chemin (empreinte différente du manifeste)"
        fi
      done < "$MANIFESTE"
      if [ "$verifiees" -eq 0 ]; then
        echo "  · $MANIFESTE : aucune empreinte, scripts non vérifiés"
        incomplet=1
      fi
    else
      echo "  · $MANIFESTE : absent, empreintes non vérifiées"
      incomplet=1
    fi
    # L'application ne déclare aucun cron : un crons.yml apparu sur le pod
    # ferait rendre des tâches dispatch_webhook par watch_crons.sh. S'il
    # devient légitime, son empreinte s'ajoute au manifeste.
    if [ -e "$EMERGENT_DIR/crons.yml" ] && [ "$crons_yml_au_manifeste" -eq 0 ]; then
      _signaler ".emergent/crons.yml présent alors que l'application ne déclare aucun cron"
    fi
  fi
  if [ "$suspects" -gt 0 ]; then
    echo "  ⚠ $suspects anomalie(s) : compromission possible du pod. Ne pas se contenter"
    echo "     de re-synchroniser : demander au support Emergent de reconstruire le pod ET son volume."
    return 1
  fi
  if [ "$incomplet" -eq 1 ]; then
    echo "  · Contrôle incomplet : voir les lignes « · » ci-dessus."
    return 2
  fi
  echo "  ✓ Aucune entrée cron hors forme Emergent."
)

_check_emergent_crons

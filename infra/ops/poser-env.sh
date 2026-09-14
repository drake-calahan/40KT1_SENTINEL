#!/usr/bin/env bash
# Pose /opt/sentinel/.env sur les deux nœuds — 40KT1_SENTINEL, mise en service.
#
# - La clé d'enrôlement est générée ICI, en mémoire, et n'est JAMAIS affichée.
#   C'est un secret PARTAGÉ : la même valeur sur le serveur et sur l'agent.
# - Le fichier transite par un fichier temporaire 0600 dans le HOME de calahan,
#   puis sudo l'installe en 0600 root:root et le temporaire est détruit.
# - sudo demande le mot de passe de CHAQUE nœud, l'un après l'autre.
# - Relancer ne régénère rien si un .env existe déjà : on refuse d'écraser.
set -euo pipefail
umask 077
DOMAINE="tail29e268.ts.net"
SERVEUR="patator-standby.${DOMAINE}"

CLE="$(openssl rand -base64 48 | tr -d '\n')"
[ "${#CLE}" -ge 60 ] || { echo "génération de clé suspecte — arrêt"; exit 1; }

poser() {  # $1=nom inventaire  $2=rôle
  local noeud="$1" role="$2" hote="$1.${DOMAINE}"
  echo "══ ${noeud} (${role})"
  ssh -o BatchMode=yes "calahan@${hote}" 'test ! -e ~/.sentinel-env.tmp' \
    || { echo "  un temporaire traîne sur ${noeud} — arrêt"; exit 1; }
  # 1. Écriture du temporaire, sans sudo, par l'entrée standard (jamais en argument).
  printf '%s\n' \
    "SENTINEL_NODE_NAME=${noeud}" \
    "SENTINEL_NODE_ROLE=${role}" \
    "SENTINEL_SERVER_HOST=${SERVEUR}" \
    "SENTINEL_SERVER_ENROLL_PORT=1515" \
    "SENTINEL_SERVER_EVENT_PORT=1514" \
    "SENTINEL_ENROLL_KEY=${CLE}" \
    "SENTINEL_RESPONSE_ENABLED=false" \
    "SENTINEL_RESPONSE_DRY_RUN=true" \
  | ssh -o BatchMode=yes "calahan@${hote}" 'umask 077; cat > ~/.sentinel-env.tmp'
  # 2. Installation par sudo — terminal interactif pour le mot de passe du nœud.
  ssh -t "calahan@${hote}" '
    set -e
    if sudo test -e /opt/sentinel/.env; then
      echo "  /opt/sentinel/.env EXISTE DÉJÀ — non écrasé"; shred -u ~/.sentinel-env.tmp; exit 3
    fi
    sudo install -d -m 0755 -o root -g root /opt/sentinel
    sudo install -m 0600 -o root -g root ~/.sentinel-env.tmp /opt/sentinel/.env
    shred -u ~/.sentinel-env.tmp
    printf "  clé présente : %s · hôte serveur : %s · droits : %s\n" \
      "$(sudo grep -c "^SENTINEL_ENROLL_KEY=.\+" /opt/sentinel/.env)" \
      "$(sudo grep -c "^SENTINEL_SERVER_HOST=.\+" /opt/sentinel/.env)" \
      "$(sudo stat -c "%a %U:%G" /opt/sentinel/.env)"
  '
}

poser patator-standby secondary
poser patator-tower primary
unset CLE
echo "Fait. La clé n'a été affichée nulle part ; elle se relit sur le serveur par"
echo "« sudo grep SENTINEL_ENROLL_KEY /opt/sentinel/.env » si un ré-enrôlement l'exige."

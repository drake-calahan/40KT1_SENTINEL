#!/usr/bin/env bash
# Garde « rien n'est armé » : refuse les lignes ajoutées qui arment un dispositif.
# Contrôle textuel sur le diff — pas une analyse sémantique Ansible.
# Brief : .agent/briefs/P00.8-garde-ci-armement.md
set -euo pipefail

usage() {
  echo "Usage: $0 <ref-de-base>" >&2
  echo "Exemple : $0 origin/main" >&2
}

if [[ $# -ne 1 ]]; then
  usage
  exit 2
fi

BASE_REF="$1"

if ! git rev-parse --verify "${BASE_REF}^{commit}" >/dev/null 2>&1; then
  echo "Impossible de calculer le diff : base introuvable (« ${BASE_REF} »)." >&2
  echo "Un contrôle qui n'a pas pu regarder ne rend jamais vert." >&2
  exit 2
fi

# Motifs refusés (espaces optionnels autour du séparateur).
PATTERN='sentinel_[a-z_]*_enabled[[:space:]]*:[[:space:]]*true|SENTINEL_[A-Z_]*_ENABLED[[:space:]]*=[[:space:]]*true|sentinel_response_dry_run[[:space:]]*:[[:space:]]*false|SENTINEL_RESPONSE_DRY_RUN[[:space:]]*=[[:space:]]*false'

# Chemins exclus : un runbook doit pouvoir montrer la commande d'armement.
is_excluded() {
  local path="$1"
  [[ "${path}" == docs/* ]] && return 0
  [[ "${path}" == .agent/* ]] && return 0
  [[ "${path}" == *.md ]] && return 0
  [[ "${path}" == .github/scripts/garde-armement.sh ]] && return 0
  [[ "${path}" == .github/workflows/armement-guard.yml ]] && return 0
  return 1
}

DIFF_OUT=""
if ! DIFF_OUT="$(git diff --unified=0 --find-renames "${BASE_REF}...HEAD" 2>&1)"; then
  echo "Impossible de calculer le diff contre « ${BASE_REF} »." >&2
  echo "${DIFF_OUT}" >&2
  echo "Un contrôle qui n'a pas pu regarder ne rend jamais vert." >&2
  exit 2
fi

found=0
current_file=""
new_line=0

while IFS= read -r line || [[ -n "${line}" ]]; do
  if [[ "${line}" =~ ^\+\+\+\ (b/)?(.*)$ ]]; then
    current_file="${BASH_REMATCH[2]}"
    if [[ "${current_file}" == "/dev/null" ]]; then
      current_file=""
    fi
    new_line=0
    continue
  fi

  if [[ "${line}" =~ ^@@\ -[0-9]+(,[0-9]+)?\ \+([0-9]+)(,[0-9]+)?\ @@ ]]; then
    new_line="${BASH_REMATCH[2]}"
    continue
  fi

  # Ligne ajoutée (pas l'en-tête +++).
  if [[ "${line}" == +* && "${line}" != +++* ]]; then
    if [[ -n "${current_file}" ]] && ! is_excluded "${current_file}"; then
      content="${line:1}"
      if echo "${content}" | grep -E -q "${PATTERN}"; then
        echo "Armement détecté dans ${current_file}:${new_line}" >&2
        echo "  ${content}" >&2
        found=1
      fi
    fi
    ((new_line++)) || true
  fi
done <<< "${DIFF_OUT}"

if [[ "${found}" -eq 1 ]]; then
  echo "" >&2
  echo "Armer est un geste d'exploitation, décrit par un runbook et joué par un humain" >&2
  echo "(.agent/RULES.md § 1). Si ce lot doit livrer du code d'armement, la valeur" >&2
  echo "reste \`false\` dans le dépôt et le runbook porte le geste." >&2
  exit 1
fi

exit 0

# Rôle `sentinel_agent` — agent sur les nœuds Linux

> **Lot `P01.1`** · agent `cursor` · Écrit sur le gabarit [`../GABARIT.md`](../GABARIT.md).

## En une phrase

Il **pose** l'agent Wazuh sur un nœud Linux, l'enrôle auprès du serveur central
par clé, rend sa configuration — et **ne le démarre pas**.

## Ce que « désarmé » veut dire ici

`sentinel_agent_enabled` vaut `false`, et cette valeur ne change pas dans le dépôt.

| | `false` (défaut) | `true` (geste de runbook) |
|---|---|---|
| Dépôt, paquet épinglé | posé | posé |
| `ossec.conf`, enrôlement | rendu / effectué | rendu / effectué |
| Unité `wazuh-agent.service` | **installée, arrêtée, désactivée** | activée et démarrée |

Comme le serveur, le rôle pose `/usr/sbin/policy-rc.d` avant l'installation du
paquet pour empêcher un démarrage par effet de bord.

## Prérequis sur la machine

1. **Épingle et clé de dépôt** — portées par le rôle serveur
   (`sentinel_server_wazuh_version`, `sentinel_server_repo_key_*` dans
   `roles/sentinel_server/defaults/main.yml`). Le playbook `02_agent.yml` les
   charge avant le rôle ; **aucune seconde copie** dans ce rôle. Version
   courante après `P01.10` : `4.14.7` ; empreinte confirmée en `A2`.

2. **Poser le `.env`** — `{{ sentinel_install_dir }}/.env`, mode `0600`, avec au
   minimum :
   - `SENTINEL_ENROLL_KEY` — clé d'enrôlement (générée, jamais dans le dépôt)
   - `SENTINEL_SERVER_HOST` — nom MagicDNS du serveur central sur le tailnet

Le rôle **échoue clairement** si l'une des deux manque.

## Surveillance d'intégrité

La liste des chemins surveillés en temps réel vient de
`sentinel_fim_realtime_paths` dans `group_vars/all/main.yml`. Le rôle la
transforme en blocs `<directories>` ; il ne la recopie pas dans `defaults/`.
`sentinel_fim_nodiff_paths` alimente les `<nodiff>` : le contenu de ces
fichiers (notamment le `.env` de HQ) ne doit pas voyager dans le diff d'alerte.

## Désinstallation

```bash
ansible-playbook playbooks/02_agent.yml -e '{"sentinel_agent_desinstaller": true}'
```

Retire le paquet, l'épinglage agent et désactive l'unité. **Conserve l'état**
(`/var/ossec` : clés, journaux locaux).

Pour détruire l'état en plus :

```bash
ansible-playbook playbooks/02_agent.yml \
  -e '{"sentinel_agent_desinstaller": true, "sentinel_agent_purger_etat": true}'
```

## Vérifications

```bash
cd infra/ansible && ansible-lint playbooks/02_agent.yml
```

```bash
cd infra/ansible && ansible-playbook playbooks/02_agent.yml --check --diff
```

⚠️ **Aucun `apply` sans ordre PO** (`RULES` § 2).

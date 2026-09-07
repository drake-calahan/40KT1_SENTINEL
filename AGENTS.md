# AGENTS.md — Contrat commun multi-outil (40KT1_SENTINEL)

Point d'entrée **uniforme** pour **Claude Code** et **Cursor**. Ce sont les deux
seuls acteurs agents de ce dépôt : contrairement à `40KT1_HQ`, il n'y a ici ni
Codex, ni Antigravity, **ni serveur MCP de coordination**. La coordination est
manuelle et repose sur une règle simple — *une tâche suivie à la fois, une
branche par tâche*.

Les détails vivent dans `.agent/` ; ce fichier ne les duplique pas.

## Au démarrage de toute session

1. Lire [`.agent/RULES.md`](.agent/RULES.md) (non négociable).
2. Lire le prompt dédié : [`.agent/prompts/claude.md`](.agent/prompts/claude.md) ou
   [`.agent/prompts/cursor.md`](.agent/prompts/cursor.md).
3. Lire [`.agent/ACTIVE.md`](.agent/ACTIVE.md) — **index actif** (phase courante,
   décisions en attente, ce qui est armé et ce qui ne l'est pas).
4. Lire uniquement le **Focus** / la tâche ouverte dans
   [`.agent/TASKS.md`](.agent/TASKS.md).
5. Consulter [`.agent/DISCOVERY.md`](.agent/DISCOVERY.md) **par pertinence** à la
   tâche, pas en entier.

Photo programme : [`.agent/DASHBOARD.md`](.agent/DASHBOARD.md) ·
hub docs : [`docs/README.md`](docs/README.md).

### Actif vs archivé (ne pas confondre)

| Couche | Où | Lecture session |
|--------|-----|-----------------|
| **Actif** | `ACTIVE.md`, Focus `TASKS`, `docs/plans/`, runbooks | Obligatoire |
| **Consigné** | ADR Suspendu / Sans objet, stubs de phases fermées | Sur besoin |
| **Archivé** | `.agent/archive/`, `docs/archive/` | **Jamais** au démarrage |

**Ne pas supprimer** un doc : `git mv` vers l'archive + stub.

## Identités & branches

| Outil | Identité | Préfixe de branche |
|-------|----------|--------------------|
| Claude Code | `claude` | `claude/<tâche>` |
| Cursor | `cursor` | `cursor/<tâche>` |

Une tâche suivie à la fois. Base = `origin/main` frais. **Jamais push direct sur `main`.**

## Coordination sans hub

Il n'y a pas de mécanisme de verrous. Ce qui le remplace :

- **`TASKS.md` porte l'état réel**, committé. `[~]` mentionne l'agent et la date.
- **Un agent ne prend jamais une tâche déjà `[~]`** par l'autre sans que le PO
  l'ait redistribuée explicitement.
- **Les branches ne se croisent pas** : chacun sur son préfixe, PR vers `main`.
- En cas de doute sur qui tient quoi : demander au PO. Ne pas deviner.

## Garde-fous PO

- Pas de push sur `main`.
- Ne pas toucher secrets / `.env` / configuration de production.
- Ne pas supprimer de documentation sans demande explicite du PO.
- **Aucun `ansible-playbook` sans `--check --diff` d'abord, et aucun `apply` sur
  une machine réelle sans ordre PO explicite.** Cette règle porte plus lourd ici
  que dans HQ : les cibles sont les deux nœuds de production.
- **Ne jamais armer une réponse automatique** dans un commit. Armer est un geste
  d'exploitation, décrit par un runbook, joué par un humain.

## Livraison

Branche dédiée → commit → validations → PR vers `main`. Cocher `TASKS.md`
seulement après preuves vertes.

## Cursor

Playbook : [`.cursor/PLAYBOOK.md`](.cursor/PLAYBOOK.md). Rôles : skills dans
`.cursor/skills/`. Règles : `.cursor/rules/`. Workers : `.cursor/agents/`.

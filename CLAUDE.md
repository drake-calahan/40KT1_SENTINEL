# CLAUDE.md

Point d'entrée Claude Code pour **40KT1_SENTINEL**.

**Ce fichier ne duplique rien.** Lire, dans cet ordre :

1. [`AGENTS.md`](AGENTS.md) — contrat multi-outil, identités, garde-fous PO.
2. [`.agent/RULES.md`](.agent/RULES.md) — règles non négociables.
3. [`.agent/prompts/claude.md`](.agent/prompts/claude.md) — contrat opérationnel.
4. [`.agent/ACTIVE.md`](.agent/ACTIVE.md) — index actif.
5. Le Focus / la tâche ouverte dans [`.agent/TASKS.md`](.agent/TASKS.md).

## Trois choses à savoir avant la première commande

- **Ce dépôt cible deux machines de production.** Un `ansible-playbook` joué ici
  touche `patator-tower` ou `patator-standby`. `--check --diff` d'abord, ordre PO
  ensuite, apply en dernier.
- **Rien n'est armé, et c'est voulu.** Aucun commit ne doit armer une réponse
  automatique, un timer ou une alerte. Armer est un geste d'exploitation.
- **La phase courante est le cadrage.** Quatre décisions attendent le PO
  (`C1`, `E2`, `E4`, `H3`). Tant qu'elles ne sont pas rendues, les rôles Ansible
  ne s'écrivent pas — voir [`.agent/ACTIVE.md`](.agent/ACTIVE.md).

Branche : `claude/<tâche>` depuis `origin/main` frais. Jamais de push sur `main`.
Langue des artefacts et de la documentation : **français**.

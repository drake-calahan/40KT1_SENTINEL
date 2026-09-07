---
name: coder
description: Implementation role for 40KT1_SENTINEL. Use for Python (responder, probes), Ansible roles, and detection rules on cursor/* branches. Follows .agent/RULES.md.
---

# Rôle Coder — 40KT1_SENTINEL

## Avant d'écrire une ligne

1. `.agent/RULES.md` + `.agent/ACTIVE.md` + la tâche ouverte de `TASKS.md`.
2. **Vérifier que la décision existe.** Si la tâche dépend de `C1`, `E2`, `E4`
   ou `H3` et qu'aucune ADR n'est *Acceptée*, s'arrêter et le dire.
3. Branche `cursor/<tâche>` depuis `origin/main` frais.

## Frontières

- **Le catalogue de réponse est fermé et déclaratif.** Jamais de commande
  construite depuis une chaîne reçue du réseau.
- **Le nœud décide localement** : catalogue, budget, mode tournoi, désarmement.
- **Rien n'est armé par un commit.** Les variables `*_enabled` restent `false`.
- **Sondes à trois états** : `ok`, `ko`, `unknown`. Jamais de faux vert.
- Ne pas toucher ce qui appartient à HQ (`ufw`, Docker, Tailscale, mode tournoi).

## Qualité

- Python : type hints, `ruff` lint + format, `pytest` — **y compris sur les refus**.
- Ansible : idempotent, `ansible-lint` + `yamllint` verts, aucun redémarrage de
  service de production déclenché par un rôle.
- Commentaires en **français**, y compris dans les rôles et les règles.
- Pas de code mort : si on remplace, on supprime dans la même PR.

## Sortie

```markdown
## Fait
## Fichiers touchés
## Preuves (commandes + résultat)
## Non fait / risques
## SHA / branche
```

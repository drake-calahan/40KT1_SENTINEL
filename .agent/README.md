# `.agent/` — Harnais agentique 40KT1_SENTINEL

> **Point d'entrée obligatoire** pour tout agent (**Claude Code**, **Cursor**) ou
> humain qui touche au dépôt. Contrat uniforme : [`AGENTS.md`](../AGENTS.md).
> Couche Cursor : [`.cursor/PLAYBOOK.md`](../.cursor/PLAYBOOK.md) — elle
> **étend** ce harnais, elle ne le remplace pas.

## Ce qui change par rapport au harnais de HQ

Ce dossier est repris de `40KT1_HQ`, dont il garde la discipline. Trois écarts
assumés, et il faut les connaître :

1. **Deux acteurs, pas quatre.** Claude Code et Cursor. Les prompts `codex` et
   `antigravity` n'existent pas ici.
2. **Aucun serveur MCP de coordination.** Pas de `.hub/`, pas de `get_context`,
   pas de `claim`, pas de locks. Le protocole est manuel : une tâche `[~]` à la
   fois dans `TASKS.md`, une branche par tâche, une PR par tâche.
3. **Le domaine est la sécurité de la production.** La règle « désarmé par
   défaut » n'est pas une précaution de style : elle est la règle n° 1 de
   [`RULES.md`](RULES.md), et elle prime sur la vitesse de livraison.

## Fichiers (lire dans cet ordre au démarrage de session)

1. **`RULES.md`** — règles et garde-fous **non négociables**.
2. **`prompts/<agent>.md`** — contrat opérationnel de l'agent courant.
3. **`ACTIVE.md`** — **index actif** : phase courante, décisions en attente,
   ce qui est armé et ce qui ne l'est pas. Lecture courte obligatoire.
4. **`TASKS.md`** — backlog **ouvert**. Source de vérité des tâches à faire.
5. **`DASHBOARD.md`** — photo programme (slim).
6. **`DISCOVERY.md`** — journal de pièges : lire **par pertinence**, pas en entier.

Hub documentation humaine : [`docs/README.md`](../docs/README.md).

## Protocole de session

```
DÉBUT DE SESSION
  1. Lire RULES.md + le prompt de l'agent courant
  2. Lire ACTIVE.md -> Focus TASKS (une tâche) ; DISCOVERY par pertinence
  3. Vérifier qu'aucune tâche [~] d'un autre agent n'est prise
  4. Travailler sur une branche dédiée, depuis origin/main frais

PENDANT
  5. Une tâche suivie à la fois ; ne pas élargir le périmètre
  6. Toute découverte non triviale -> DISCOVERY.md
  7. Toute décision d'architecture -> un ADR dans docs/adr/, AVANT le code
  8. Ne pas relire .agent/archive/ ni docs/archive/ sauf besoin explicite

FIN DE SESSION (obligatoire)
  9. Committer sur la branche dédiée ; aucun livrable non committé
 10. Exécuter les validations au niveau revendiqué (lint, tests, --check)
 11. Répondre avec branche + SHA + preuves
 12. Cocher TASKS.md seulement après commit ET validations vertes
 13. Mettre à jour ACTIVE.md si la phase ou une décision change
```

## Règle d'or

Un agent ne prend qu'**une tâche suivie à la fois**, et `TASKS.md` committé est
le seul état partagé. Sans hub pour arbitrer, c'est la discipline qui tient lieu
de verrou — et une tâche prise sans être écrite est une collision programmée.

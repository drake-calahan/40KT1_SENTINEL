# Plans de phase

> **Audience** : PO · agents · contributeurs
> **Statut** : actif (index)
> Vérité d'avancement : [`.agent/ACTIVE.md`](../../.agent/ACTIVE.md)

## Actifs

| Plan | Sujet | État |
|------|--------|------|
| [`P01`](P01-mise-en-service.md) | Mise en service : phases P0 → P4, de l'observation seule à la réponse armée | **P0 en cours** — bloqué par `ADR-003` |
| [`P02`](P02-lancement-implementation.md) | Lancement de l'implémentation : découpage en lots, affectation `claude` / `cursor` / PO, vagues | **actif** — vague 0 bloquée par `P00.6` |

`P01` dit *quoi* et *dans quel ordre* ; `P02` dit *qui*, *en combien de morceaux*,
et *à quelle condition un lot part*. Les deux se lisent ensemble.

## Archivés

_(aucun)_ — l'archive est [`../archive/plans/`](../archive/plans/), et
archiver signifie `git mv` + stub, jamais supprimer.

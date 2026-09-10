# `.agent/briefs/` — Briefs de lot

> **À quoi ça sert** : un brief est la **conception d'un lot**, écrite avant que
> le lot ne parte. Il se lit d'un bout à l'autre, il ne renvoie à aucune décision
> restée ouverte, et il se termine par des critères d'acceptation qu'une commande
> peut vérifier.
>
> Découpage et affectation : [`docs/plans/P02`](../../docs/plans/P02-lancement-implementation.md).
> Backlog : [`TASKS.md`](../TASKS.md). Règles : [`RULES.md`](../RULES.md).

## Pourquoi ces fichiers existent

Ce dépôt n'a **pas de hub de coordination**. Ce qui remplace un hub, c'est un
périmètre écrit avant d'ouvrir la branche. Sans brief, l'agent qui code arbitre —
et un arbitrage pris dans une session ne se retrouve nulle part trois semaines
plus tard.

Un brief n'est donc **pas** un ticket. C'est le contrat du lot : ce qu'il produit,
ce qu'il ne touche pas, et ce qui prouve qu'il est fini.

## Statuts

| Statut | Ce que ça veut dire |
|--------|---------------------|
| **prêt** | Tout est tranché. Le lot peut partir dès que son bloqueur est levé. |
| **en attente** | Un lot amont doit livrer d'abord ; l'en-tête dit lequel et ce qu'il apporte. |
| **esquisse** | Le périmètre est posé, la conception ne l'est pas. **Ne pas coder dessus.** |

Un brief en `esquisse` qui part quand même produit exactement ce que ce dossier
existe pour éviter.

## Comment le PO lance un lot Cursor

1. Vérifier dans [`TASKS.md`](../TASKS.md) qu'aucune tâche `[~]` de `claude` ne
   touche la même zone (zones : `P02` § 6).
2. Nouveau chat Cursor, modèle « thinking », `/orchestrator` ou le skill visé.
3. Coller : *« Lot `P0X.Y`. Lis `.agent/briefs/P0X.Y-….md` en entier, puis
   `.agent/RULES.md` et `.agent/ACTIVE.md`. Ouvre la branche indiquée et livre
   le périmètre du brief, rien de plus. »*
4. À la livraison : lire les **preuves collées**, pas le verdict. Une PR qui
   annonce vert sans sortie de commande est une PR non vérifiée.

## Les briefs

| Lot | Sujet | Pour | Statut |
|-----|-------|------|--------|
| [`P00.2`](P00.2-adr-001-accepte.md) | `ADR-001` → *Accepté* | `cursor` | prêt |
| [`P00.7`](P00.7-nettoyage-post-amorce.md) | Nettoyage post-amorce | `cursor` | prêt |
| [`P00.8`](P00.8-garde-ci-armement.md) | Garde CI « rien n'est armé » | `cursor` | prêt |
| [`P01.7`](P01.7-instrumentation-observation.md) | Journal des faux positifs | `cursor` | prêt |
| [`P01.2`](P01.2-regles-integrite.md) | Règles d'intégrité | `cursor` | prêt |
| [`P01.8`](P01.8-regles-auth-docker.md) | Règles authentification + Docker | `cursor` | en attente (`P01.2`) |
| [`P01.1`](P01.1-role-sentinel-agent.md) | Rôle `sentinel_agent` | `cursor` | en attente (`P01.0`) |
| [`P01.9`](P01.9-rapports-hebdomadaires.md) | Rapports conformité + vulnérabilités | `cursor` | en attente (`P01.1`) |
| [`P02.0`](P02.0-cablage-alerte.md) | Câblage de l'alerte | `cursor` | en attente (`P01.5`) |
| [`P02.1`](P02.1-grille-severite.md) | Grille de sévérité | `cursor` | en attente (`P02.0`) |
| [`P03.2`](P03.2-runbook-mode-a-blanc.md) | Runbook du mode à blanc | `cursor` | prêt |
| [`P03.3`](P03.3-runbook-desarmement.md) | Runbook de désarmement testé | `cursor` | esquisse |

Les lots de `claude` n'ont pas de brief ici : leur conception vit dans l'ADR ou
dans le code qu'ils produisent, et leur intention est écrite dans
[`P02`](../../docs/plans/P02-lancement-implementation.md) § 5.

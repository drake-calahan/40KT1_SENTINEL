# ADR — Architecture Decision Records (40KT1_SENTINEL)

> Index agents : [`.agent/ACTIVE.md`](../../.agent/ACTIVE.md) ·
> hub : [`../README.md`](../README.md).

Les ADR **restent dans ce dossier**. On ne les déplace pas vers l'archive : le
**statut** porte la couche Actif / Consigné.

| Couche | Statuts | Lecture |
|--------|---------|---------|
| **En attente** | Proposé | **Oui** — c'est ce qui bloque le chantier |
| **Actif** | Accepté | Oui si la tâche touche le sujet |
| **Consigné** | Suspendu · Sans objet · Remplacé par ADR-XXX | Sur besoin |

## Numérotation

La numérotation **repart à 001** dans ce dépôt. Une ADR de `40KT1_HQ` est
toujours citée avec son dépôt d'origine (« `ADR-062` de HQ ») — sans quoi
`ADR-002` d'ici et `ADR-002` de là-bas deviennent indiscernables dans six mois.

## Les décisions

| # | Décision | Statut | Bloque |
|---|----------|--------|--------|
| [001](ADR-001-moteur-et-profil-de-deploiement.md) | Moteur de détection et profil de déploiement | **Proposé** | `P1` |
| [002](ADR-002-catalogue-et-budget-de-reponse.md) | Catalogue de réponse, budget, mode tournoi | **Proposé** | `P3` |
| [003](ADR-003-hote-du-serveur-central.md) | Hôte du serveur central | **Proposé** | `P1` |

## ADR de `40KT1_HQ` dont ce dépôt dépend

Elles ne sont pas recopiées ici — elles font autorité chez elles, et une copie
divergerait.

| # (HQ) | Sujet | Ce qu'on en tire |
|---|---|---|
| `ADR-029` | Standby tiède, n'écrit jamais | le standby ne doit pas devenir un second point d'écriture |
| `ADR-030` | Exposition publique par tunnel, un seul connecteur | couper le connecteur est un geste visible, jamais anodin |
| `ADR-054` | Ubuntu Server sur le nœud primaire | `sudo-rs`, `sudo.ws`, mises à jour sans redémarrage |
| `ADR-057` | Cockpit ops contrôleur tailnet | le motif « exception bornée + sortie écrite » |
| `ADR-061` | Relève automatique en lecture seule, mode tournoi | la notion de fenêtre où une réponse coûte cher |
| `ADR-062` | Auto-réparation bornée : catalogue, budget, journal | **le modèle direct** d'`ADR-002` |

## Gabarit

[`_TEMPLATE.md`](_TEMPLATE.md). Une ADR sans **option écartée**, sans
**conséquence négative** et sans **réversibilité** est un compte rendu, pas une
décision.

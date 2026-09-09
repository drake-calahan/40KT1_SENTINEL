# Playbooks

> **Un seul existe : [`00_check.yml`](00_check.yml)**, et il ne change rien.
> Les trois autres s'écrivent sur le gabarit
> ([`../roles/GABARIT.md`](../roles/GABARIT.md)).

## `00_check.yml` — le playbook qui ne change rien

```bash
cd infra/ansible && ansible-playbook playbooks/00_check.yml --check --diff
```

Il répond à une seule question, avant tous les autres : *les machines sont-elles
dans l'état que les rôles présument ?* Il **lit** — élévation de privilège,
chemin de la stack HQ, témoin de mode tournoi, `notify.sh`, présence éventuelle
d'une installation Sentinelle, témoin de désarmement — et rend `ok`, `KO` ou
**`INCONNU`** ligne par ligne.

Trois propriétés à ne pas perdre en le modifiant :

1. Il commence par une **garde de cible** sur `localhost` : un groupe vide fait
   échouer le playbook avant tout contact.
2. `ignore_unreachable: true` sur le play des nœuds — on veut savoir **qui** est
   joignable, ce qui est précisément l'information cherchée.
3. Il **refuse de conclure si aucun hôte n'a été atteint**. Sans ce refus,
   `ignore_unreachable` rendrait `0` avec zéro machine contrôlée.

## Ce qui viendra, et dans quel ordre

| Fichier | Rôle | Débloqué par |
|---|---|---|
| `01_server.yml` | serveur central, profil frugal, écoute `tailscale0` | `P01.6` (fait) |
| `02_agent.yml` | agents sur les nœuds Linux, un nœud à la fois | `01_server.yml` joué |
| `03_responder.yml` | exécuteur local + unités `sentinel-*`, **désarmé** | `ADR-002` acceptée |

## Deux règles qui valent pour tous

**Cibler un groupe, jamais un hôte en dur.** Dans `40KT1_HQ`, cinq playbooks
visaient `primary_win11` en dur ; déplacer l'hôte les aurait rendus muets — sans
erreur, sur zéro hôte. *Un playbook qui ne fait rien et rend `ok` est le pire des
modes de panne.* Et cibler un groupe ne suffit pas : le groupe peut être vide.
D'où la **garde de cible** en tête de playbook — modèle dans `00_check.yml`,
motif dans [`../roles/GABARIT.md`](../roles/GABARIT.md) § 4.3.

**Rendre compte du nombre d'hôtes touchés** dans le bilan de fin de play. C'est
le seul contrôle qui distingue « tout va bien » de « je n'ai regardé personne ».

# Playbooks — à écrire

> **Aucun playbook n'existe encore**, et c'est l'état correct de la phase 0 :
> l'hôte du serveur central n'est pas tranché (`ADR-003`), donc écrire
> `01_server.yml` reviendrait à choisir cet hôte par un commit.

## Ce qui viendra, et dans quel ordre

| Fichier | Rôle | Débloqué par |
|---|---|---|
| `01_server.yml` | serveur central, profil frugal, écoute `tailscale0` | `ADR-003` acceptée |
| `02_agent.yml` | agents sur les nœuds Linux, un nœud à la fois | `01_server.yml` joué |
| `03_responder.yml` | exécuteur local + unités `sentinel-*`, **désarmé** | `ADR-002` acceptée |

## Deux règles qui valent pour tous

**Cibler un groupe, jamais un hôte en dur.** Dans `40KT1_HQ`, cinq playbooks
visaient `primary_win11` en dur ; déplacer l'hôte les aurait rendus muets — sans
erreur, sur zéro hôte. *Un playbook qui ne fait rien et rend `ok` est le pire des
modes de panne.*

**Rendre compte du nombre d'hôtes touchés** dans le bilan de fin de play. C'est
le seul contrôle qui distingue « tout va bien » de « je n'ai regardé personne ».

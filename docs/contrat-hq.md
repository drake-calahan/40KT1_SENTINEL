# Contrat de frontière avec `40KT1_HQ`

> **Statut** : proposition — attend la réponse `H3`.
> **⚠️ Ce document doit exister DES DEUX CÔTÉS.** Une frontière écrite dans un
> seul dépôt n'est pas une frontière : c'est une intention que l'autre dépôt
> ignore. Tant que son jumeau n'existe pas dans `40KT1_HQ`, ce contrat n'engage
> personne. Suivi : `P00.5` dans [`.agent/TASKS.md`](../.agent/TASKS.md).

## Le risque, en une phrase

Deux dépôts qui provisionnent les mêmes machines par Ansible finissent par se
défaire l'un l'autre — et le symptôme est **une règle qui disparaît toute
seule** entre deux `apply`, sans que rien n'ait changé dans le dépôt qui la
porte. C'est un défaut coûteux parce qu'il ne ressemble pas à un conflit : il
ressemble à une panne.

## Le principe

**HQ possède l'infrastructure. Sentinelle s'y greffe.**

Sentinelle **ajoute**, elle ne réécrit jamais. Un objet possédé par HQ n'est
touché par Sentinelle sous aucun prétexte, même pour le « corriger ».

## Le partage, objet par objet

| Objet | Propriétaire | Ce que l'autre a le droit de faire |
|---|---|---|
| Politique `ufw` (`deny incoming`, `tailscale0`, SSH LAN) | **HQ** | Sentinelle ajoute des règles **taguées** dans une chaîne dédiée ; ne change jamais la politique par défaut |
| Docker Engine, sa configuration, la rotation de ses journaux | **HQ** | Sentinelle lit les événements ; ne configure pas |
| Tailscale, l'appartenance au tailnet, les ACL | **HQ** | Sentinelle utilise `tailscale0` comme unique interface d'écoute |
| `unattended-upgrades` et sa liste noire | **HQ** | Sentinelle **signale** un retard de paquet ; ne met rien à jour |
| Unités et timers systemd | chacun les siens | préfixes distincts : `40kt1-*` (HQ) et `sentinel-*` (Sentinelle) |
| `.env` du nœud (stack de production) | **HQ** | Sentinelle a son propre `.env`, dans son propre répertoire |
| Arborescence `/srv/40kt1` et `~/40KT1_HQ` | **HQ** | Sentinelle la surveille en lecture ; n'y écrit pas |
| Mode tournoi (`node-state/tournament-mode`) | **HQ** | Sentinelle **lit** le témoin ; ne le pose ni ne le retire |
| Chemin d'alerte (`scripts/notify.sh`) | **HQ** | Sentinelle l'appelle, avec **ses propres destinataires** (salon et sujet distincts) |
| Blocage d'IP en réponse | **Sentinelle** | chaîne dédiée, avec expiration — jamais dans les règles d'HQ |
| Règles de détection, catalogue de réponse, exécuteur | **Sentinelle** | HQ ne les lit ni ne les modifie |
| Journaux de sécurité | **Sentinelle** | — |

## Trois pièges concrets, à connaître avant d'écrire un rôle

### 1. `ufw` ne couvre pas les ports publiés par Docker

Le démon insère ses propres règles dans la chaîne `DOCKER-USER`, **en amont**
d'`ufw`. Un port publié par un conteneur reste joignable depuis le LAN malgré
`deny incoming`. C'est déjà consigné dans `roles/host_baseline/tasks/40_firewall.yml`
de HQ. **Ne pas relire ces règles en croyant le port fermé**, et ne pas
« corriger » la politique d'HQ pour le fermer : ce serait sortir de la frontière.

### 2. Deux automates ne se posent pas le même verrou

HQ pose et retire le mode tournoi. Sentinelle le lit. Si Sentinelle le posait
« pour se protéger pendant un incident », elle armerait ou désarmerait la relève
automatique de HQ sans le savoir.

### 3. Un rôle Sentinelle ne redémarre aucun service de production

C'est la règle de `host_baseline` dans HQ, et elle vaut ici : un rôle doit
pouvoir être rejoué sur une machine en production **sans rien redémarrer**. Un
changement qui l'exigerait est *signalé dans le bilan du rôle*, joué dans une
fenêtre choisie par un humain.

## Ce qui appartient à HQ et que Sentinelle ne refait pas

| Sujet | Où il vit |
|---|---|
| Durcissement du système | rôle `host_baseline` |
| Supervision de disponibilité | `scripts/watchdog.py`, `node_status.py` |
| Auto-réparation | `scripts/selfheal.py`, `ADR-062` |
| Relève automatique en lecture seule | `scripts/failover.py`, `ADR-061` |
| Sauvegardes et offsite | `scripts/backup.sh`, `mirror-sync.sh` |
| Exposition publique | `cloudflared`, `ADR-030` |

**En cas de doute sur l'appartenance d'un sujet : il va dans HQ, et Sentinelle le
lit.**

## Modification de ce contrat

Par amendement **simultané des deux fichiers**, avec la date. Un contrat modifié
d'un seul côté est pire que pas de contrat : il donne l'illusion d'un accord.

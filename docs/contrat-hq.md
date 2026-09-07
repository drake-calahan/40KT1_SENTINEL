# Contrat de frontière avec `40KT1_HQ`

> **Statut** : **en vigueur côté Sentinelle** depuis le 2026-09-07 (réponse `H3`).
> **⚠️ Son jumeau côté `40KT1_HQ` n'existe pas encore.** Tant qu'il n'est pas
> fusionné là-bas, ce texte n'engage que ce dépôt-ci : une frontière écrite dans
> un seul dépôt n'est pas une frontière, c'est une intention que l'autre dépôt
> ignore.
> Le texte à porter est prêt :
> [`contrat-hq-jumeau.md`](contrat-hq-jumeau.md). Suivi : `P00.5` dans
> [`.agent/TASKS.md`](../.agent/TASKS.md).

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
| **État de la relève** (armée / au repos) | **HQ** | Sentinelle **lit** l'état et **arrête son serveur central** quand la relève s'arme (`ADR-003`, condition 2) ; elle ne l'arme, ne le désarme et ne le retarde jamais |
| Chemin d'alerte (`scripts/notify.sh`) | **HQ** | Sentinelle l'appelle, avec **ses propres destinataires** (salon et sujet distincts) |
| **Chaîne pare-feu de réponse** (blocage d'IP, taguée, à expiration) | **Sentinelle** | chaîne dédiée, jamais dans les règles d'HQ ; HQ ne la vide pas et ne la réordonne pas |
| Règles de détection, catalogue de réponse, exécuteur | **Sentinelle** | HQ ne les lit ni ne les modifie |
| Journaux de sécurité | **Sentinelle** | HQ n'y écrit pas ; ils sont traités comme une donnée sensible des deux côtés |

## Trois pièges concrets, à connaître avant d'écrire un rôle

### 1. `ufw` ne couvre pas les ports publiés par Docker

Le démon insère ses propres règles dans la chaîne `DOCKER-USER`, **en amont**
d'`ufw`. Un port publié par un conteneur reste joignable depuis le LAN malgré
`deny incoming`. C'est déjà consigné dans `roles/host_baseline/tasks/40_firewall.yml`
de HQ. **Ne pas relire ces règles en croyant le port fermé**, et ne pas
« corriger » la politique d'HQ pour le fermer : ce serait sortir de la frontière.

### 2. Deux automates ne se posent pas le même verrou

HQ pose et retire le mode tournoi ; il arme et désarme la relève. Sentinelle
**lit** les deux. Si Sentinelle posait le mode tournoi « pour se protéger pendant
un incident », elle armerait ou désarmerait la relève automatique de HQ sans le
savoir.

La réciproque vaut : HQ n'a pas à retirer une règle de la chaîne de Sentinelle
parce qu'elle « traîne ». Cette chaîne expire toute seule — c'est sa garantie de
réversibilité, et la vider à la main la casse.

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

## Ce que ce contrat coûte à HQ

Trois choses, et elles sont volontairement petites :

1. **Ne pas vider la chaîne pare-feu de Sentinelle** lors d'un `apply` de
   `host_baseline`. C'est le seul objet de Sentinelle qu'un rôle de HQ pourrait
   effacer sans le vouloir.
2. **Ne pas renommer** le témoin de mode tournoi ni le mécanisme qui porte l'état
   de la relève sans amender ce contrat des deux côtés : Sentinelle les lit.
3. **Garder `notify.sh` appelable** avec des destinataires passés par
   l'environnement. Aucun changement de comportement demandé.

Rien d'autre. Sentinelle ne demande à HQ ni configuration, ni exception, ni
ouverture de port.

## Modification de ce contrat

Par amendement **simultané des deux fichiers**, avec la date. Un contrat modifié
d'un seul côté est pire que pas de contrat : il donne l'illusion d'un accord.

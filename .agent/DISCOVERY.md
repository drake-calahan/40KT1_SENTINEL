# DISCOVERY.md — Journal de découvertes 40KT1_SENTINEL

> Faits sur l'existant, pièges, contraintes apprises. Pour ne pas re-découvrir.
> Chaque entrée : date, sujet, fait, implication.
>
> **Lecture agents** : par **pertinence** à la tâche en cours — pas le fichier
> entier. Index actif : [`ACTIVE.md`](ACTIVE.md).

## Le parc, tel qu'il est (relevé du 2026-09-07, source : dépôt `40KT1_HQ`)

### `patator-tower` — nœud primaire

- Ubuntu Server **26.04**, i7-6700K (Skylake, 2015), NVMe 512 Go.
- Stack de production en Docker : `db` (Postgres) · `api` (FastAPI) · `caddy` ·
  `cloudflared` · `scraper`. Sert `hq.40kt1.com`.
- `/srv/40kt1` sur un volume logique dédié (`lv_srv`) — la remise à plat du
  système n'emporte pas l'état.
- **`sudo-rs` est le `sudo` par défaut d'Ubuntu 26.04** et casse l'élévation
  Ansible (« Timeout waiting for privilege escalation prompt »). Le contournement
  de HQ : `ansible_become_exe: /usr/bin/sudo.ws`. **À reprendre tel quel** dans
  tout inventaire visant ce nœud.
- Windows reste **intact** sur le disque 0, inatteignable tant que le contrôleur
  SATA est en AHCI. C'est une surface latente que rien ne surveille.

### `patator-standby` — nœud secondaire

- Linux **Mint**, ASUS 2013, i7 3ᵉ génération, **16 Go**, SSD.
- Miroir restauré chaque nuit. **N'écrit jamais** (ADR-029 de HQ) — c'est ce qui
  garantit qu'aucune divergence ne naît.
- Stack dans `~/40KT1_HQ`, pas dans `/opt`.
- Porte aussi le cockpit ops (exception `P31.7`) et sert de **relais GitHub** aux
  nœuds Linux (héritage `C9`).
- ⚠️ **Défaut réseau récidivant** : perte totale d'IPv4, quatre occurrences
  (28/08, 30/08, 05/09, 06/09). Cause : NetworkManager ne commite pas sa config
  IPv4 ; le témoin fiable n'est pas la route mais `IP4.ADDRESS`. Un
  `nmcli device reapply` **ne suffit pas** — il faut un cycle complet du lien.
  **Implication pour nous** : toute règle qui alerte sur la perte de contact avec
  cet agent doit agréger, jamais répéter.

### Réseau et exposition

- Chemin d'exploitation : **tailnet Tailscale** `tail29e268.ts.net`, MagicDNS.
- `ufw` : `deny incoming` par défaut, `tailscale0` ouvert, SSH depuis
  `192.168.1.0/24` **en secours**.
- ⚠️ **`ufw` ne couvre pas les ports publiés par Docker** : le démon insère ses
  règles dans `DOCKER-USER`, **en amont** d'`ufw`. Un port publié par un
  conteneur reste joignable depuis le LAN malgré `deny incoming`. Consigné dans
  `roles/host_baseline/tasks/40_firewall.yml` de HQ. **Ne pas relire ces règles
  en croyant le port fermé.**
- Exposition publique par **tunnel sortant cloudflared** ; un seul connecteur à
  la fois (ADR-030 de HQ).
- Les deux nœuds sont à **70 km** l'un de l'autre : ni compteur électrique, ni
  box, ni FAI communs. C'est une redondance de domaine de panne réelle, et c'est
  ce qui rend le standby crédible comme hôte du serveur central.

### Postes d'administration

`AEGIS-TOWER` (Windows 11 + Docker Desktop, poste du PO) · `pc-devsecops` ·
`bluefin` (base atomique orientée podman, désalignée de la chaîne
`docker compose` du dépôt).
⚠️ **Aucun n'est allumé en permanence.** C'est la question `B1` du plan `P37` de
HQ, jamais levée — et elle interdit de faire d'un poste le serveur central.

## Pièges de méthode, déjà payés par HQ

### Le faux vert (deux occurrences)

1. **Playbooks visant zéro hôte.** Cinq playbooks ciblaient `primary_win11` en
   dur ; déplacer l'hôte les aurait rendus muets — dont le retour arrière du
   lendemain. Ils auraient rendu `ok` sans rien faire.
   *« Un playbook qui ne fait rien et rend `ok` est le pire des modes de panne. »*
2. **Missions du cockpit rendant vert sans joindre un nœud** — mission `ok` en
   0,6 s, sans contact.

**Implication** : toute sonde écrite ici distingue `ok`, `ko` et **`unknown`**.
Une mesure qui n'a pas pu être prise ne rend jamais `ok`.

### Le self-heal maison

`heal.ps1`, 514 lignes, tournait toutes les 5 minutes sur la tour. Supprimé par
le plan `P30`, avec ce constat : *« l'essentiel de ce qu'il faisait, Docker le
fait mieux et sans code. »*
**Implication** : préférer l'outil sur étagère pour le moteur, n'écrire que la
colle spécifique au projet — et la tester.

### La supervision qui n'alerte personne

Ordre imposé par le runbook `supervision-croisee.md` de HQ : poser les
destinataires, **prouver le câblage** (`notify.sh test-alert`), **et seulement
ensuite** armer.
**Implication** : c'est la règle n° 1 de [`RULES.md`](RULES.md), reprise telle
quelle.

### L'alerte qui se répète finit en sourdine

`watchdog.py` alerte à la **transition** de la liste des échecs, jamais à chaque
cycle. *« Une supervision qui répète la même panne toutes les dix minutes finit
en sourdine, et une sourdine ne se rallume jamais. »*
**Nuance propre à la sécurité** : la répétition porte une information (cent
tentatives valent mieux qu'une). D'où l'agrégation avec compteur plutôt que la
suppression pure — voir `F3`.

### La sauvegarde offsite muette

Retex du 2026-09-04 : l'offsite existait, était configuré, et n'écrivait rien —
sans que personne le sache.
**Implication** : à la mise en service, **prouver** l'écriture des archives, ne
pas la supposer.

## Pièges rencontrés dans ce dépôt

### `Path.exists()` confond « absent » et « je n'ai pas pu regarder »

*2026-09-07, exécuteur de réponse (`P03.0`).* `Path.exists()` avale l'`OSError` et
rend `False` — donc un témoin de désarmement dans un répertoire illisible se lit
comme « pas de désarmement », et un témoin de mode tournoi inaccessible se lit
comme « pas de tournoi ». Les deux erreurs vont dans le sens permissif.

**Implication** : dans `responder/gardes.py`, la présence d'un témoin se lit par
`os.stat` avec trois issues — présent / absent / **indéterminé** — et
l'indéterminé vaut l'état le plus restrictif. C'est le même faux vert que celui
des playbooks à zéro hôte, sous un autre déguisement.

### Un compteur en mémoire n'est pas un budget

*2026-09-07.* Le budget de trois gestes par heure se lit dans le journal, pas
dans une variable : un redémarrage du service remettrait un compteur en mémoire à
zéro, et le budget servirait exactement quand il ne faut pas — après un incident
qui a fait redémarrer la machine.

**Implication** : le journal est la source du compte, et une ligne corrompue rend
le compte `None` (non mesurable) plutôt qu'un total partiel. Un total partiel
desserre la garde sans le dire.

### Le dégel doit être tracé, pas seulement possible

*2026-09-07.* Première version : le gel se levait en retirant le fichier témoin.
Défaut — le geste ne laissait aucune trace, et le compte de l'heure glissante
restait de toute façon au-dessus du plafond : le PO aurait retiré le fichier et
constaté que « ça ne marche pas ».

**Implication** : `python -m responder.degel "motif"` retire le témoin **et**
écrit une entrée `degel` dans le journal ; c'est cette entrée qui remet le
compteur à zéro. Le motif est obligatoire.

## Contraintes de ressources

- Serveur central en profil frugal : **0,7 à 1,2 Go** de RAM. Le profil complet
  (indexeur + console) ajoute **4 à 5 Go** — hors budget sur les 16 Go du
  standby, qui portent déjà le miroir Postgres et doivent garder de la marge
  pour la relève en lecture seule.
- Agent : 60 à 100 Mo. Falco (phase 4, option) : 150 à 250 Mo.

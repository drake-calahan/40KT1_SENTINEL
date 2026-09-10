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
- ⚠️ **`docker events` ne porte pas privileged / mounts / ports.** Relevé en
  revue de `P01.8` (2026-09-10) : le wodle `docker-listener` relaie le flux
  `docker events` ; pour un `create`/`start`, `Actor.Attributes` contient les
  **labels**, plus `image` et `name` — rien d'autre. Pas d'attribut
  `privileged`, pas de liste de montages, pas de mapping de ports ; un
  bind-mount de `/var/run/docker.sock` ne produit pas d'événement `volume`.
  **Implication** : les cas « conteneur `--privileged` », « socket monté » et
  « port sur `0.0.0.0` » (celui que `ufw` ne voit pas) **ne se détectent pas**
  depuis ce flux. Une règle Wazuh sur ces champs serait un faux vert silencieux.
  Il faut une sonde d'inspection (`docker inspect` périodique) ou du FIM/auditd
  sur le `docker-compose.yml` — lot `P01.17`.

### Options de règle Wazuh : `<srcuser>` / `<dstuser>` refusés

*2026-09-10 (revue P01.8 tour 2).* Les balises `<srcuser>` et `<dstuser>`
**ne sont pas** des options de règle : `analysisd` répond
`Invalid option 'srcuser' for rule` et **refuse de charger le fichier entier**
(issues upstream [#19879](https://github.com/wazuh/wazuh/issues/19879),
[#868](https://github.com/wazuh/wazuh-ruleset/issues/868)). `<field name="srcuser">`
échoue aussi (`Field 'srcuser' is static`). Seul `<user>` (alias de `dstuser`)
est documenté côté règle ; pour filtrer le compte qui *élève* un sudo, il faut
un `<regex>` / `<match>` sur le message. `<srcip>` reste une option valide.
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

## Ansible — quatre faux verts, mesurés en écrivant le gabarit (`P01.6`)

### `-e var=false` arme au lieu de désarmer

*2026-09-09.* La forme `ansible-playbook … -e sentinel_agent_enabled=false` passe
la **chaîne** `"false"`, et une chaîne non vide est **vraie** en Jinja. La
commande tapée pour désarmer arme. Le runbook d'armement s'écrira sur ce piège.

**Implication** : tout rôle affirme `... is boolean` en préconditions
(`roles/gabarit/tasks/00_garde.yml`), et la forme correcte est JSON :
`-e '{"sentinel_agent_enabled": true}'`.

### Avec `failed_when: false`, `.failed` ne dit plus rien

*2026-09-09.* Motif tentant pour lire un témoin sans planter :
`stat` + `failed_when: false`, puis tester `resultat.failed`. Il vaut **toujours
faux**, y compris quand le module n'a rien pu lire et n'a donc rien renvoyé. On
conclut alors « fichier absent » sur une mesure qui n'a pas eu lieu — le faux
vert, écrit à la main.

**Implication** : le test porte sur la **présence de la clé** `stat`
(`'stat' not in resultat` → `inconnu`), jamais sur `.failed`. Vérifié sur les
trois cas (témoin présent / absent / module muet).

### `ignore_unreachable: true` rend `0` sur zéro machine

*2026-09-09.* Nécessaire ici — `patator-standby` perd son IPv4 — mais si **tous**
les nœuds sont injoignables, le playbook se termine avec le code `0`. Il n'a rien
contrôlé et le dit vert.

**Implication** : `00_check.yml` se termine par un play `localhost` qui **refuse
de conclure** si l'ensemble atteint est vide, et nomme les nœuds restés
`INCONNU`. Un play qui vise un groupe **vide**, lui, n'exécute aucune tâche : le
seul endroit qui peut le voir est la **garde de cible**, en amont.

### `\'` dans une chaîne Jinja : la tâche ne se charge même pas

*2026-09-09.* Le français est plein d'apostrophes, et l'écrire `d\'ADR-003` dans
une chaîne Jinja **simple-quotée** paraît naturel. Ça ne l'est pas : le moteur de
templating d'Ansible coupe la chaîne à l'apostrophe et rend
`expected token ',', got 'ADR'`. La tâche **ne se charge pas** — ce n'est pas une
erreur d'exécution mais une erreur de chargement, qui peut se présenter comme un
`internal-error: A malformed block was encountered` attribué à un **autre
fichier** que celui qui la porte.

**Ce qui rend le piège coûteux** : `jinja2` seul **accepte** `\'` — donc un
contrôle local qui se contente de compiler les expressions passe au vert. C'est
ce qui est arrivé : 193 expressions compilées localement, 4 fichiers cassés en CI.

**Implication** : écrire les chaînes Jinja en **guillemets doubles** dès qu'elles
contiennent une apostrophe, ce qui est la règle plutôt que l'exception en
français. Le gabarit a été corrigé en premier — il se recopie.

### `ansible-lint` ne s'installe pas sur le poste Windows du PO

*2026-09-09.* Conflit de dépendances irrésoluble (`ansible-core` n'a pas de roue
Windows). Conséquence : **`ansible-lint` ne se joue qu'en CI**, et un lot Ansible
ne peut donc pas être annoncé vert avant que la PR ait tourné.

**Implication** : ne pas cocher un lot Ansible sur des vérifications locales
seules, et le dire dans la PR plutôt que de laisser croire à une vérification
complète. `yamllint`, lui, s'installe et tourne — il attrape la forme, pas la
sémantique Ansible.

### La garde CI d'armement ne voit pas `yes`

*2026-09-09.* Mesuré sur `5ce90c0` : `sentinel_response_enabled: yes`,
`... : True`, `... : on` et `sentinel_response_dry_run: no` ajoutés dans
`infra/ansible/` passent `garde-armement.sh` en **vert**. Le motif ne connaît que
`true` / `false` littéraux, alors que `yes` est l'idiome Ansible courant.

**Implication** : lot `P00.11`. En attendant, le gabarit impose `false` littéral
dans `defaults/` — et la garde CI reste la ceinture, pas les bretelles.

## L'exécuteur — trois pièges relevés en câblant les gestes (`P03.6`)

### `is_private` de Python ne protège pas le tailnet de façon stable

*2026-09-09.* Première version de `bloquer_ip` : refuser les adresses privées
avec `adresse.is_private`. Défaut mesuré — **la plage du tailnet
(`100.64.0.0/10`) n'y est pas classée de la même façon selon la version de
Python**, et `is_private` couvre par ailleurs les plages de documentation
(`203.0.113.0/24`), que rien n'oblige à protéger.

**Implication** : le chemin d'administration du parc dépendait du hasard d'une
mise à jour d'interpréteur. Les plages protégées sont désormais **nommées une par
une**, avec leur motif, dans `PLAGES_PROTEGEES`. Une garde qui protège le chemin
du retour ne se délègue pas à une propriété de bibliothèque.

### Un geste qui échoue ne laissait aucune trace

*2026-09-09.* `P03.0` appelait le geste câblé puis journalisait `execute`. Si le
geste levait, l'exception s'échappait de `traiter()` : **ni geste, ni refus, ni
ligne au journal**. On croyait la menace traitée, et la tentative ne consommait
pas le budget — donc elle se rejouait sans fin.

**Implication** : résultat `echoue`, distinct de `refuse` (refuser, c'est décider
de ne pas agir ; échouer, c'est avoir essayé sans aboutir), et **consommateur de
budget**. Une tentative reste une tentative.

### Le catalogue se contourne en changeant de nom de geste

*2026-09-09.* Arrêter le conteneur `cloudflared` **est** `couper_connecteur` —
classé *alerte* en nominal, *jamais* en tournoi. Rien n'empêchait un ordre
`arreter_conteneur` de cible `cloudflared` de le jouer quand même. Le catalogue
fermé cessait d'être fermé, sans qu'une ligne de `catalogue.py` ait bougé.

**Implication** : chaque geste porte la liste de ce sur quoi il refuse d'agir, et
cette liste se lit comme une **conséquence du catalogue**, pas comme une
préférence. À généraliser : avant de câbler un geste, se demander *quel autre
geste du catalogue celui-ci permettrait de jouer par un autre nom*.

## Contraintes de ressources

- Serveur central en profil frugal : **0,7 à 1,2 Go** de RAM. Le profil complet
  (indexeur + console) ajoute **4 à 5 Go** — hors budget sur les 16 Go du
  standby, qui portent déjà le miroir Postgres et doivent garder de la marge
  pour la relève en lecture seule.
- Agent : 60 à 100 Mo. Falco (phase 4, option) : 150 à 250 Mo.

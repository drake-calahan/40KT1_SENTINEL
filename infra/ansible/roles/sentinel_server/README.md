# Rôle `sentinel_server` — serveur central, profil frugal

> **Lot `P01.0`** · agent `claude` · Décidé par
> [`ADR-001`](../../../../docs/adr/ADR-001-moteur-et-profil-de-deploiement.md)
> (moteur) et
> [`ADR-003`](../../../../docs/adr/ADR-003-hote-du-serveur-central.md) (hôte).
> Écrit sur le gabarit [`../GABARIT.md`](../GABARIT.md).

## En une phrase

Il **pose** le manager Wazuh sur `patator-standby`, à une version épinglée et
gelée, configuré pour n'écouter que sur le tailnet — et **ne le démarre pas**.

## Ce que « désarmé » veut dire ici

`sentinel_server_enabled` vaut `false`, et cette valeur ne change pas dans le
dépôt.

| | `false` (défaut) | `true` (geste de runbook) |
|---|---|---|
| Dépôt de paquets, clé vérifiée | posé | posé |
| Paquet `wazuh-manager`, version épinglée + gelée | installé | installé |
| `ossec.conf`, `api.yaml`, secret d'enrôlement | rendus | rendus |
| Unité `wazuh-manager.service` | **installée, arrêtée, désactivée** | activée et démarrée |
| Écoute réelle vérifiée par `ss -lntp` | — | **oui, et l'armement échoue sinon** |

Le paquet installe une unité systemd, et sur Debian un paquet **démarre** son
service à l'installation. Le rôle pose donc `/usr/sbin/policy-rc.d` avant
l'installation et le retire après : sans cela, « désarmé » ne voudrait rien
dire, le moteur tournerait dès la pose.

## Les trois refus d'armement

`20_armement.yml` refuse de démarrer si :

1. le **témoin de désarmement d'urgence** est posé — ou **illisible**. Un `ok`
   n'est pas un `inconnu` : on n'arme pas sur une mesure qu'on n'a pas pu
   prendre ;
2. le **bornage `cgroup`** n'est pas posé (condition 1 d'`ADR-003`, lot
   `P01.4`). Sur 16 Go partagés avec le miroir Postgres et la relève, armer
   sans plafond rendrait la condition déclarative ;
3. après démarrage, une **socket du moteur écoute hors du tailnet**. C'est ce
   qui rend la condition 3 d'`ADR-003` *vérifiée* et non *annoncée*.

## Ce qui n'est pas dans ce rôle, et où ça vit

| Sujet | Lot |
|---|---|
| Bornage `cgroup` et arrêt pendant la relève (`C3`) | `P01.4` |
| Agents sur les deux nœuds | `P01.1` (`cursor`) |
| Règles de détection | `P01.2`, `P01.8` (`cursor`) |
| Câblage de l'alerte, **preuve d'arrivée d'abord** | `P02.0` |
| Réponse active, catalogue, exécuteur | `P03.x` — **cinq portes** d'`ADR-002` § 6 |
| `ufw`, Docker, Tailscale | **HQ** — Sentinelle ajoute, ne réécrit pas |

Le rôle ne pose **aucune** règle de pare-feu : l'écoute est bornée par la
configuration du moteur, pas par un filtre. C'est délibéré — `ufw` ne couvre pas
les ports publiés par Docker sur ces machines
([`DISCOVERY.md`](../../../../.agent/DISCOVERY.md)), donc s'y fier pour tenir
`C4` serait s'appuyer sur une garde qui a déjà un trou connu.

## Deux choses à faire **avant** le premier `--check`

### 1. Confirmer l'empreinte de la clé du dépôt

`sentinel_server_repo_key_confirmee` vaut `false`, et **le rôle refuse de
s'exécuter tant qu'il vaut `false`**. L'empreinte présente dans `defaults/` a
été recopiée de mémoire, pas relevée sur la source officielle : une empreinte
fausse ne protège de rien, elle donne l'apparence d'un contrôle.

La marche à suivre est écrite au-dessus de la variable dans
[`defaults/main.yml`](defaults/main.yml). Ce dépôt ajoute une source de paquets
tierce à une machine de production : la chaîne d'approvisionnement est la menace
**n° 2** du classement `B1`.

### 2. Poser le `.env` sur la machine

`{{ sentinel_install_dir }}/.env`, mode `0600`, propriétaire `root`, avec
`SENTINEL_ENROLL_KEY` **générée** — jamais recopiée d'ailleurs. Le rôle échoue
clairement si elle manque : un serveur central sans secret d'enrôlement
accepterait des agents sans les authentifier, ou n'en accepterait aucun. Dans
les deux cas, un faux vert.

La valeur ne passe **ni** par le dépôt, **ni** par l'inventaire, **ni** par un
`-e`. Modèle : [`.env.example`](../../../../.env.example).

## La question ouverte — à trancher avant `P01.9`

**Le mineur retenu (`4.7.5`) n'est pas un détail pour `D4`** (inventaire de
vulnérabilités, rapport hebdomadaire — lot `P01.9`, `cursor`).

Wazuh a redessiné son détecteur de vulnérabilités au cours de la série 4.x, et
la version redessinée **stocke ses résultats dans l'indexeur** — que le profil
frugal n'installe pas (`ADR-001`). Selon le mineur choisi, `D4` est donc soit
disponible localement, soit à produire autrement.

**Ce point n'est pas vérifié.** Il est écrit ici parce qu'il se découvre au
mauvais moment sinon : au milieu de `P01.9`, avec le moteur déjà posé sur une
machine de production et la version gelée.

Ce qu'il faut faire, dans cet ordre :

1. **relever** le comportement réel du mineur candidat (documentation de
   l'éditeur, notes de version) — c'est un fait à constater, pas à supposer ;
2. si `D4` exige l'indexeur, **choisir** entre : rester sur un mineur qui s'en
   passe, produire l'inventaire par un autre moyen en lecture seule, ou rouvrir
   `ADR-001` sur le profil. Les trois sont défendables ; aucune ne se décide
   dans un rôle Ansible ;
3. **consigner** le choix — et si le profil bouge, c'est un amendement
   d'`ADR-001`, pas une variable qu'on change.

Tâche ouverte : `P01.10` dans [`TASKS.md`](../../../../.agent/TASKS.md).

## Désinstallation — la réversibilité, jouable

```bash
ansible-playbook playbooks/01_server.yml -e '{"sentinel_server_desinstaller": true}'
```

Retire l'unité, le paquet, le gel, le dépôt, la clé, l'épinglage et le bornage.
**Conserve l'état** (`/var/ossec` : journaux, base des agents).

L'effacer est un **geste séparé** :

```bash
ansible-playbook playbooks/01_server.yml \
  -e '{"sentinel_server_desinstaller": true, "sentinel_server_purger_etat": true}'
```

Retirer le logiciel et détruire les preuves ne sont pas le même geste. Les
journaux de sécurité décrivent l'infrastructure entière — chemins, comptes,
horaires, empreintes (`RULES` § 4).

## Vérifications

```bash
cd infra/ansible && ansible-lint playbooks/01_server.yml
```

```bash
cd infra/ansible && ansible-playbook playbooks/01_server.yml --check --diff
```

⚠️ `patator-standby` perd son IPv4 par intermittence — quatre occurrences en
trois semaines. Un `--check` en échec sur ce nœud n'est pas forcément un défaut
du playbook, et **ne pas conclure vert** sans l'avoir joué pour de bon.

⚠️ **Aucun `apply` sans ordre PO de la session courante** (`RULES` § 2).

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

## Le mineur et `D4` — tranché le 2026-09-09

**Le choix du mineur n'était pas neutre pour `D4`** (inventaire de
vulnérabilités, rapport hebdomadaire — lot `P01.9`). Il est **tranché**.

Le fait, relevé sur la documentation de l'éditeur : la coupure est à **`4.8.0`**
(12 juin 2024). Avant, les résultats de vulnérabilités vivent dans une base
SQLite **locale** du manager et l'API du manager sait les lire. À partir de
`4.8.0`, ils sont poussés vers l'**indexeur** — que le profil frugal n'installe
pas (`ADR-001`) — et les points de sortie `/vulnerability` de l'API du manager
sont **supprimés**.

**Décision du PO (`P01.10`, issue B)** : monter sur la branche courante et
produire `D4` autrement. Le motif est que rester en `4.7.5` aurait posé sur deux
machines de production un composant privilégié figé à ~2 ans de correctifs —
pour ne gagner que la source du rapport le **moins** critique des quatre besoins
de détection. `D1`, `D2` et `D3` sont indifférents au mineur.

La version est donc `4.14.7`, la plus récente servie par le dépôt de l'éditeur
au 2026-09-09.

### Ce qui reste à mesurer, et qui ne peut l'être que sur machine

**Où `D4` prendra sa source en profil frugal sur `4.14.x` n'est pas établi.**
La documentation dit que le module pousse ses résultats vers l'indexeur ; elle
dit aussi que le rapport de détection est envoyé au moteur d'analyse
(`analysisd`), ce qui laisserait des **alertes dans `alerts.json`** même sans
indexeur. Les deux peuvent être vrais, et un fil de la communauté rapporte que
le module refuse de s'initialiser quand aucun indexeur n'est joignable.

**Ce n'est donc pas tranché par la documentation.** La mesure se prend au
premier `--check --diff` puis à la pose, dans cet ordre :

1. le module se charge-t-il sans indexeur, ou refuse-t-il de démarrer ?
2. produit-il des alertes dans `alerts.json` ?
3. si non : `D4` se produit à partir de l'inventaire de paquets du
   `syscollector` (local, lisible) confronté à une source CVE en lecture seule.

**Exigence qui ne dépend d'aucune de ces réponses**, et qui est déjà portée dans
le brief `P01.9` : le rapport doit **distinguer « aucune vulnérabilité » de
« aucune donnée »** et sortir en `unknown` bruyant dans le second cas. Un
rapport vide qui ressemble à « rien à signaler » est le faux vert que ce dépôt
existe pour empêcher.

Relevé complet : [`docs/releves/P01.10`](../../../../docs/releves/P01.10-mineur-du-moteur-et-D4.md).

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

### Ce que le premier `--check` ne prouve pas

Sur un hôte où le moteur n'a jamais été posé, `--check` n'installe rien : donc
`wazuh-manager.service` n'existe pas encore, et la tâche qui garantit
« ni activée ni démarrée » n'a **aucune unité à vérifier**. Le rôle ne s'arrête
pas dessus (`P01.15`) — il l'inscrit au bilan, avec la phrase qui compte :

> Ce `--check` ne prouve donc PAS que le moteur restera à l'arrêt.

C'est à l'`apply` que la garantie se mesure. Et si l'unité manque **après** un
apply réel, le rôle refuse de poursuivre plutôt que de rendre `ok` : une unité
jamais vue ne peut pas avoir été laissée à l'arrêt.

⚠️ **Aucun `apply` sans ordre PO de la session courante** (`RULES` § 2).

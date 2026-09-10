# Mise en service — observation seule

> ✅ **JOUABLE depuis le 2026-09-10** — `ADR-003` est *Acceptée*, les trois
> rôles existent, et les trois playbooks ont été **répétés à blanc de bout en
> bout** sur un hôte vierge (conteneur Debian 12 `systemd`, `--check --diff`
> puis `apply`, aucune machine du parc touchée — `P01.20`). Cette répétition a
> trouvé cinq défauts qui n'apparaissaient qu'à l'exécution ; ils sont corrigés.
>
> **Ce qui reste à faire est un geste d'exploitation, et il appartient au PO.**
> Ce runbook ne s'auto-exécute pas : il se lit, puis il se joue, dans l'ordre.

## Ce qui a été prouvé en répétition, et ce qui ne l'a pas été

Sur un hôte de laboratoire vierge (conteneur Debian 12 `systemd`, `tailscale0`
factice, inventaire de production joué en local — `P01.20`) :

| Geste | Résultat |
|---|---|
| `00_check.yml --check --diff` | ✅ `rc=0` |
| `01_server.yml --check --diff` sur hôte vierge | ✅ `rc=0`, six points signalés non joués |
| `01_server.yml` apply, désarmé | ✅ `rc=0` — unité `inactive` **et** `disabled`, huit fichiers de règles posés, `wazuh-analysisd -t` propre |
| second passage | ✅ plafond **mesuré** : `MemoryMax=1500M`, `CPUQuota=400ms` |
| armement `-e '{"sentinel_server_enabled": true}'` | ✅ `rc=0` — unité `active`, **une seule socket** : `remoted` sur le tailnet |
| `02_agent.yml --check --diff` | ✅ `rc=0` |

**Ce qui n'est PAS prouvé** — et qu'aucun bac à sable ne prouvera :

- l'`apply` réel d'un agent, l'enrôlement compris : il demande deux machines et
  un manager joignable par le tailnet ;
- la durée réelle du premier démarrage du moteur (entre 25 s et plus de 90 s
  selon la charge en répétition ; le drop-in porte `TimeoutStartSec=300`, **à
  confirmer sur la machine**) ;
- tout ce qui dépend du parc : IPv4 du standby, `sudo-rs`, chemins de HQ.

Un bac à sable dit qu'un playbook **peut** aller au bout. Il ne dit rien de la
machine sur laquelle vous allez le jouer.

## Ce que cette procédure met en service

Le serveur central en **profil frugal** et les agents sur les deux nœuds Linux,
en **observation seule** : aucune alerte poussée, aucune réponse. On mesure le
bruit de fond.

## Avant de commencer — cinq vérifications

1. **`ADR-003` est acceptée** et l'hôte du serveur central est nommé. ✅ fait.
   Sans cela, on installe au mauvais endroit et on ré-enrôle tout plus tard.
2. **Le tailnet est sain entre l'hôte central et les deux nœuds.**
   `patator-standby` a un défaut IPv4 récidivant : vérifier `IP4.ADDRESS`, pas
   seulement la route. Voir [`.agent/DISCOVERY.md`](../../.agent/DISCOVERY.md).
   Le rôle refuse de poser si `tailscale0` n'a pas d'adresse — c'est voulu.
3. **Le `.env` de chaque nœud est posé** (`/opt/sentinel/.env`, mode `0600`,
   propriétaire `root`), à partir de `.env.example`, avec
   `SENTINEL_RESPONSE_ENABLED=false` — c'est le défaut, ne pas le changer ici.
   Deux variables sont **bloquantes**, et le contrôle s'arrête sans elles :

   | Variable | Où elle sert | Ce que sa présence évite |
   |---|---|---|
   | `SENTINEL_ENROLL_KEY` | serveur **et** agents | un serveur qui accepte des agents sans les authentifier — ou aucun |
   | `SENTINEL_SERVER_HOST` | agents | une IP publique en dur là où seul le MagicDNS du tailnet a le droit d'être |

   La valeur ne passe **ni** par le dépôt, **ni** par l'inventaire, **ni** par
   un `-e`. Elle est générée sur la machine, jamais recopiée d'ailleurs.
4. **Le poste de commande est prêt** — WSL sur `AEGIS-TOWER`, voir
   [`poste-de-commande.md`](poste-de-commande.md). Ansible ne tourne pas sous
   Windows, et un dépôt lu depuis `/mnt/c` fait ignorer `ansible.cfg`.
5. **L'élévation de privilège fonctionne** sur les deux nœuds. `sudo-rs` casse
   `become` avec un message qui ressemble à un problème de réseau : le
   contournement (`ansible_become_exe: /usr/bin/sudo.ws`) est déjà dans
   l'inventaire, et `00_check.yml` vérifie qu'il tient encore.

### Poser le `.env` — la marche à suivre, commande par commande

> **Le poste de commande est WSL sur `AEGIS-TOWER`** (décision PO du
> 2026-09-10) : sa préparation est dans
> [`poste-de-commande.md`](poste-de-commande.md), à jouer **avant** ceci.

**La clé d'enrôlement est la MÊME des deux côtés.** C'est un secret partagé :
le serveur la pose dans `authd.pass` et l'agent la présente au premier contact.
Deux valeurs différentes ne produisent pas une erreur claire — elles produisent
un agent qui ne s'enrôle pas, sur un serveur qui refuse sans dire pourquoi. On
la génère **une fois**, et on la recopie.

**1. Générer la clé** — sur le poste de commande, une seule fois :

```bash
openssl rand -base64 48
```

Ne la coller ni dans le dépôt, ni dans un ticket, ni dans une conversation.
Elle vit dans un gestionnaire de mots de passe, et dans deux fichiers `.env`.

**2. Sur `patator-standby`** (le serveur central) :

```bash
sudo install -d -m 0755 -o root -g root /opt/sentinel
sudo install -m 0600 -o root -g root /dev/null /opt/sentinel/.env
sudo tee /opt/sentinel/.env >/dev/null <<'ENV'
SENTINEL_NODE_NAME=patator-standby
SENTINEL_NODE_ROLE=secondary
SENTINEL_SERVER_HOST=patator-standby.tail29e268.ts.net
SENTINEL_SERVER_ENROLL_PORT=1515
SENTINEL_SERVER_EVENT_PORT=1514
SENTINEL_ENROLL_KEY=<LA CLÉ GÉNÉRÉE À L'ÉTAPE 1>
SENTINEL_RESPONSE_ENABLED=false
SENTINEL_RESPONSE_DRY_RUN=true
ENV
sudo chmod 0600 /opt/sentinel/.env && sudo ls -l /opt/sentinel/.env
```

**3. Sur `patator-tower`** (le nœud primaire) — même clé, `SERVER_HOST` pointant
vers le **serveur central**, pas vers lui-même :

```bash
sudo install -d -m 0755 -o root -g root /opt/sentinel
sudo install -m 0600 -o root -g root /dev/null /opt/sentinel/.env
sudo tee /opt/sentinel/.env >/dev/null <<'ENV'
SENTINEL_NODE_NAME=patator-tower
SENTINEL_NODE_ROLE=primary
SENTINEL_SERVER_HOST=patator-standby.tail29e268.ts.net
SENTINEL_SERVER_ENROLL_PORT=1515
SENTINEL_SERVER_EVENT_PORT=1514
SENTINEL_ENROLL_KEY=<LA MÊME CLÉ>
SENTINEL_RESPONSE_ENABLED=false
SENTINEL_RESPONSE_DRY_RUN=true
ENV
sudo chmod 0600 /opt/sentinel/.env && sudo ls -l /opt/sentinel/.env
```

**4. Vérifier sans lire la valeur** — ce qui compte est la présence, pas le
contenu :

```bash
sudo grep -c '^SENTINEL_ENROLL_KEY=.\+' /opt/sentinel/.env   # doit rendre 1
sudo grep -c '^SENTINEL_SERVER_HOST=.\+' /opt/sentinel/.env  # doit rendre 1
sudo stat -c '%a %U:%G' /opt/sentinel/.env                   # doit rendre 600 root:root
```

Ce qui n'est **pas** à poser maintenant : `SENTINEL_API_TOKEN` (lot `P01.9`),
le webhook Discord et les URL de push (lot `P02.0`, dont la première exigence
est la preuve d'arrivée sur le téléphone). Un secret posé « pour plus tard »
est un secret exposé sans usage.

⚠️ `SENTINEL_RESPONSE_ENABLED=false` et `SENTINEL_RESPONSE_DRY_RUN=true` sont
les défauts du dépôt et **ne se changent pas ici**. La réponse s'arme par
`ADR-002` § 6, cinq portes, et le geste appartient au PO.

## Étape 0 — le contrôle de terrain, en lecture seule

```bash
ansible-playbook -i inventory/production.yml playbooks/00_check.yml --check --diff
```

Il ne pose rien. Il dit qui répond, si l'élévation marche, où est la stack HQ,
et ce qu'il **n'a pas pu mesurer** — un nœud injoignable ressort `INCONNU`, pas
`ok`. Un `patator-tower` non joint n'est pas un feu vert pour la suite.

## 1. Le serveur central

```bash
ansible-playbook -i inventory/production.yml playbooks/01_server.yml --check --diff
```

Relire le diff **avant** de retirer `--check`. Points à contrôler dans le diff :

- l'écoute est sur `tailscale0` **uniquement** — jamais `0.0.0.0` ;
- le bornage `cgroup` est présent si l'hôte est `patator-standby` ;
- aucun service de production n'est redémarré.

**Lire aussi le bilan, pas seulement le diff.** Sur un hôte vierge, ce premier
`--check` rend `ok` en signalant **six points « SIGNALÉ, NON JOUÉ »** — c'est le
comportement correct, pas un défaut :

| Ce qui est signalé | Pourquoi c'est normal ici |
|---|---|
| unités de l'interlock absentes | `--check` ne les a que simulées |
| plafond `cgroup` non mesuré | rien n'est appliqué en `--check` |
| chemin de l'état de la relève non confirmé | `P01.13`, arbitrage PO en attente |
| installation du moteur non simulée | `apt` ne connaît pas un dépôt qu'il n'a pas encore |
| unité `wazuh-manager` absente | le paquet n'est pas posé |
| règles non posées, chargement non prouvé | `/var/ossec/etc/rules` n'existe pas encore |

Un `--check` **sans** ces signalements sur un hôte vierge voudrait dire que le
contrôle a menti. C'est le sens de la ligne « ce `--check` ne prouve donc PAS
que… » qui accompagne chacun.

Puis, **sur ordre PO explicite**, sans `--check`.

⚠️ **Le premier `apply` laisse deux choses non prouvées, par construction :**
le plafond `cgroup` (le rôle qui le pose passe **avant** celui qui installe le
moteur, donc systemd ne connaît pas encore l'unité à borner) et la version
réellement servie par le dépôt. **Rejouer le playbook une seconde fois** les
mesure toutes les deux — la deuxième passe doit être `changed=0` sur la pose et
verte sur les deux contrôles. Un déploiement se fait en deux passages, et la
seconde n'est pas une reprise : c'est la mesure.

### Ce qu'un `apply` laisse « changed » à chaque passage

Cinq tâches ressortent `changed` même sur une machine déjà conforme, et ce
n'est pas une dérive : le répertoire temporaire de la clé du dépôt (créé, rempli,
retiré) et le fichier `policy-rc.d` (posé le temps de l'installation, retiré
juste après). Les compter comme du bruit est correct ; les voir disparaître
serait le vrai signal d'alarme, puisque c'est la parade qui empêche le paquet de
démarrer son service tout seul.

## 2. La fenêtre d'enrôlement — à ouvrir, puis à refermer

⚠️ **Le démon d'enrôlement est FERMÉ par défaut, et il doit le rester hors mise
en service.** Motif mesuré (`P01.21`) : `wazuh-authd` écoute sur `0.0.0.0`, et
Wazuh n'offre **aucune** option pour le lier à une interface — `<auth>` n'a pas
l'équivalent du `local_ip` de `<remote>`. Ouvert en permanence, le port
d'inscription et le secret qui le protège seraient joignables depuis le LAN, ce
que `C4` interdit. Le contrôle d'écoute de l'armement refuse d'ailleurs cet
état, et il a raison.

L'enrôlement est donc une **fenêtre**, pas un réglage :

```bash
ansible-playbook -i inventory/production.yml playbooks/01_server.yml   -e '{"sentinel_server_enabled": true, "sentinel_server_authd_ouvert": true}'
```

… puis on inscrit les agents (§ 3), **puis on referme** en rejouant la même
commande **sans** `sentinel_server_authd_ouvert`. Tant que la fenêtre est
ouverte, le playbook le signale à chaque passage, et l'armement le refuse.

## 3. Les agents, un nœud à la fois

```bash
ansible-playbook -i inventory/production.yml playbooks/02_agent.yml --limit patator-tower --check --diff
```

**Un nœud à la fois, et le primaire en premier.** Motif : si l'agent perturbe
quoi que ce soit, on veut le découvrir sur la machine qu'on regarde, pas sur les
deux en même temps.

⚠️ **`patator-standby` ne reçoit PAS d'agent**, et ce n'est pas un oubli :
`wazuh-agent` et `wazuh-manager` se déclarent en conflit au niveau du paquet —
`apt` refuse d'installer les deux. Le nœud n'est pas aveugle pour autant : le
manager se surveille lui-même (agent local `000`), avec **les mêmes listes
d'intégrité** que les agents. Le playbook exclut cet hôte de lui-même
(`sentinel_agents_linux:!sentinel_server`) et le rôle refuse de s'y exécuter si
un `--limit` l'y amenait quand même.

## 4. Vérifier que les agents sont vus — et qu'ils mesurent

Deux contrôles, pas un. Le premier dit que l'agent est connecté ; le second dit
qu'il **regarde**. Un agent connecté qui ne remonte rien est un faux vert, et
c'est le mode de panne le plus dangereux d'une supervision.

## 5. Poser la règle anti-rafale — déjà écrite, à vérifier

`patator-standby` perd son IPv4 régulièrement (quatre occurrences en trois
semaines). Sans règle d'agrégation, la première coupure produit une rafale
d'alertes de perte de contact, et la réaction naturelle est de couper le bruit —
donc de perdre le signal.

La règle s'écrit **avant** la mise sous tension : c'est fait
([`rules/agents/10-contact-agent.xml`](../../rules/agents/10-contact-agent.xml),
`P01.3`), et elle est posée sur le manager par le rôle lui-même (`P01.19`).
Après le premier `apply`, vérifier sur la machine que le moteur la voit :

```bash
sudo /var/ossec/bin/wazuh-analysisd -t
sudo ls /var/ossec/etc/rules/sentinel-*.xml
```

Le premier doit sortir sans erreur ; le second doit lister les cinq familles.
Un manager sans ces fichiers tourne et ne détecte **rien** de ce que le dépôt
décrit — sans produire la moindre erreur.

## 6. Laisser tourner, et compter

Période d'observation : **14 jours** par défaut (`D5`), couvrant au moins un
déploiement complet et une sauvegarde offsite.

Tenir un journal des alertes non pertinentes : c'est lui qui produit le critère
de sortie, et il ne se reconstitue pas de mémoire.

> **Sortie de phase** : moins de 3 alertes non pertinentes par semaine, **deux
> semaines de suite**. Chiffré, mesuré, écrit — pas « ça a l'air calme ».

## Ce que cette procédure ne fait pas

Elle n'arme **rien**. Aucune alerte ne part, aucune réponse ne s'exécute.
L'armement est l'objet de [`armement-de-la-reponse.md`](armement-de-la-reponse.md),
et il ne s'ouvre qu'après la sortie de cette phase.

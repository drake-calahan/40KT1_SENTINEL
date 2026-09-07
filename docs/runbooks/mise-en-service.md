# Mise en service — observation seule

> ⚠️ **PAS ENCORE JOUABLE.** Ce runbook décrit une intention, pas un geste
> disponible. Il devient jouable quand
> [`ADR-003`](../adr/ADR-003-hote-du-serveur-central.md) est **acceptée** et que
> les rôles `sentinel_server` et `sentinel_agent` existent (`P01.0`, `P01.1`).
>
> Il est écrit maintenant pour que la discussion porte sur des gestes, pas sur
> des principes — et parce qu'un runbook rédigé après coup ne dit jamais
> pourquoi.

## Ce que cette procédure met en service

Le serveur central en **profil frugal** et les agents sur les deux nœuds Linux,
en **observation seule** : aucune alerte poussée, aucune réponse. On mesure le
bruit de fond.

## Avant de commencer — trois vérifications

1. **`ADR-003` est acceptée** et l'hôte du serveur central est nommé.
   Sans cela, on installe au mauvais endroit et on ré-enrôle tout plus tard.
2. **Le tailnet est sain entre l'hôte central et les deux nœuds.**
   `patator-standby` a un défaut IPv4 récidivant : vérifier `IP4.ADDRESS`, pas
   seulement la route. Voir [`.agent/DISCOVERY.md`](../../.agent/DISCOVERY.md).
3. **Le `.env` de chaque nœud est posé**, à partir de `.env.example`, avec
   `SENTINEL_RESPONSE_ENABLED=false` — c'est le défaut, ne pas le changer ici.

## 1. Le serveur central

```bash
ansible-playbook -i inventory/production.yml playbooks/01_server.yml --check --diff
```

Relire le diff **avant** de retirer `--check`. Points à contrôler dans le diff :

- l'écoute est sur `tailscale0` **uniquement** — jamais `0.0.0.0` ;
- le bornage `cgroup` est présent si l'hôte est `patator-standby` ;
- aucun service de production n'est redémarré.

Puis, **sur ordre PO explicite**, sans `--check`.

## 2. Les agents, un nœud à la fois

```bash
ansible-playbook -i inventory/production.yml playbooks/02_agent.yml --limit patator-tower --check --diff
```

**Un nœud à la fois, et le primaire en premier.** Motif : si l'agent perturbe
quoi que ce soit, on veut le découvrir sur la machine qu'on regarde, pas sur les
deux en même temps.

## 3. Vérifier que les agents sont vus — et qu'ils mesurent

Deux contrôles, pas un. Le premier dit que l'agent est connecté ; le second dit
qu'il **regarde**. Un agent connecté qui ne remonte rien est un faux vert, et
c'est le mode de panne le plus dangereux d'une supervision.

## 4. Poser la règle anti-rafale — maintenant, pas après

`patator-standby` perd son IPv4 régulièrement (quatre occurrences en trois
semaines). Sans règle d'agrégation, la première coupure produit une rafale
d'alertes de perte de contact, et la réaction naturelle est de couper le bruit —
donc de perdre le signal.

La règle s'écrit **avant** la mise sous tension. Voir `P01.3`.

## 5. Laisser tourner, et compter

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

# ADR-003 : Hôte du serveur central

- **Statut** : **Accepté** — décidé le 2026-09-07 (réponses `C1` à `C5`)
- **Date** : rédigée le 2026-09-07 · décidée le 2026-09-07
- **Décideurs** : Thomas (PO) + agent DevSecOps
- **Plan** : [`P01`](../plans/P01-mise-en-service.md) — lot `P01.0` ·
  [`P02`](../plans/P02-lancement-implementation.md) — vague 2
- **Bloque** : plus rien. Cette ADR **débloque** la phase `P1`.
- **Revue obligatoire** : **2027-03-07** (six mois) — voir § « La sortie ».

> **Décision la plus structurante du chantier**, et elle ne se change pas après
> coup sans réinstaller. L'hôte est `patator-standby`, en profil frugal, sous
> quatre conditions vérifiables et avec une sortie datée.

## Contexte

Quatre hôtes possibles, aucun parfait.

| Option | Pour | Contre |
|---|---|---|
| **(a) `patator-standby`** | allumé 24/7 · **à 70 km de la tour** — un attaquant qui prend la tour ne prend pas le serveur de sécurité · ne sert pas le nom public | 16 Go partagés avec le miroir **et** le rôle de relève · défaut réseau récidivant (4 occurrences) · domaine de panne commun entre sécurité et secours |
| **(b) matériel dédié** (mini-PC N100 / 16 Go, ordre de 250 €) | le bon choix d'architecture · aucun domaine de panne partagé · profil complet possible | coût · un hôte de plus à entretenir |
| **(c) `patator-tower`** | puissance disponible | **le serveur surveille la machine sur laquelle il tourne** : un compromis de la tour emporte les preuves |
| **(d) un poste ops** | rien | éliminé : **aucun des trois n'est allumé la nuit** (contrainte `B1` du plan `P37` de HQ) |

L'option (d) n'est pas un choix : c'est une contrainte déjà établie, et elle est
la moitié de la réponse.

## Options envisagées

1. **(c) la tour.** Écartée sur un motif simple et suffisant : un dispositif qui
   surveille son propre hôte ne survit pas au compromis de cet hôte. Les
   journaux qui comptent sont exactement ceux qu'un attaquant efface.
2. **(a) le standby, profil frugal.** **Retenue**, sous les quatre conditions du
   § suivant.
3. **(b) matériel dédié.** Écartée **aujourd'hui** par `C2` — le budget matériel
   est **zéro**. Elle n'est pas abandonnée : elle est la **sortie** de cette ADR.
4. **(e) `bluefin`, poste du labo SecOps.** Retenue **uniquement** comme plan B
   de MVP, en journée. Écartée comme hôte nominal par la même contrainte `B1`
   que (d) : le poste n'est pas allumé la nuit, et un serveur de sécurité qui
   dort la nuit ne surveille pas les heures qui comptent.

## Décision

**Le serveur central vit sur `patator-standby`, en profil frugal.**

C'est exactement la forme qu'a prise l'exception `P31.7` pour le cockpit dans
HQ : une cohabitation transitoire, assumée, **datée**, et dont la sortie est
décrite ici plutôt que renvoyée à plus tard.

### Le plan B, et sa limite

`bluefin` peut porter le serveur central **en journée, pour un MVP** — le temps
de valider une configuration, pas d'exploiter un dispositif. Il ne devient
**hôte de secours 24/7 que dans le pire cas** : le standby indisponible
durablement et aucun matériel dédié. Cette bascule est une **dérogation**, elle
se consigne dans `ACTIVE.md` avec sa date et son motif, et elle rouvre la revue.

`bluefin` n'est **jamais** l'hôte nominal. Sa base atomique orientée `podman` est
désalignée de la chaîne `docker compose` du parc : l'y installer durablement
créerait une seconde manière de faire, dans le dépôt dont le rôle est de dire ce
qui tourne où.

### Les quatre conditions — et comment chacune se vérifie

Une condition qu'on ne peut pas mesurer est un vœu. Chacune porte donc son
contrôle et le lot qui l'implémente.

| # | Condition | Contrôle | Lot |
|---|---|---|---|
| 1 | **Bornage `cgroup` permanent** : 1,5 Go de mémoire (`MemoryMax`) et une part de CPU plafonnée (`CPUQuota`) pour l'ensemble du dispositif | `systemctl show sentinel-*.service -p MemoryMax,CPUQuota` rend les valeurs de `group_vars`, sur la machine | `P01.4` |
| 2 | **Arrêt automatique du serveur central quand la relève s'arme** (`C3`) | l'unité s'arrête sur l'état de relève posé par HQ, et les **agents continuent d'écrire en local** | `P01.4` |
| 3 | **Écoute sur `tailscale0` uniquement** (`C4`) | `ss -lntp` ne montre aucun port du dispositif sur une autre interface — jamais de Funnel, jamais via `cloudflared`, jamais sur le nom public | `P01.0` |
| 4 | **La sortie est écrite** | le § suivant, et la date de revue en tête de cette ADR | — |

Sur la condition 2, un point de frontière qui n'est pas négociable : **Sentinelle
lit l'état de la relève ; elle ne le pose ni ne le retire.** Deux automates qui se
posent le même verrou est un mode de panne connu, et c'est déjà la règle pour le
mode tournoi. Le contrat de frontière porte cette lecture
([`contrat-hq.md`](../contrat-hq.md)).

Une **dérogation exceptionnelle** au bornage est possible à la demande du PO
(`C3`) : elle est temporaire, motivée, et consignée. Elle ne se prend pas dans un
commit.

## La sortie

Trois déclencheurs. Le premier qui survient met fin à la cohabitation.

1. **Un matériel dédié existe.** Le serveur central déménage. Le déménagement ne
   demande pas de retoucher les agents — seulement de les ré-enrôler. Cette ADR
   est amendée avec la date effective.
2. **Le bornage ne tient pas.** Constat mesuré, pas ressenti : pression mémoire
   sur le miroir Postgres, relève dégradée, ou dépassement répété du plafond.
   Le serveur central est **arrêté sur le standby** et replié en MVP de jour sur
   `bluefin`, le temps d'acquérir un matériel dédié.
3. **La revue du 2027-03-07.** Si ni 1 ni 2 ne sont survenus, la cohabitation
   est **reconduite explicitement**, avec sa date, ou cette ADR est amendée.
   Sans cette revue, une exception transitoire devient définitive sans que
   personne ne l'ait décidé — c'est précisément le reproche fait à `P31.7`.

## Chiffrement du stockage (`C5`)

Sur le standby : **hors périmètre de la phase 1**, noté comme **dette**, pas
comme oubli. Le serveur central porte des journaux qui décrivent
l'infrastructure entière — chemins, comptes, horaires, empreintes : un disque
volé est une carte du système.

Sur un matériel dédié : **LUKS à l'installation**, où il ne coûte rien. La sortie
1 emporte donc aussi la levée de cette dette.

## Conséquences

- **Positives** : le serveur de sécurité vit sur une machine allumée en
  permanence, à 70 km de la cible principale, hors du chemin public, sans
  dépense.
- **Négatives / dette** : sécurité et secours partagent un domaine de panne —
  c'est le reproche fait à `P31.7` dans HQ, et il vaut ici aussi. Le défaut
  réseau récidivant du standby rendra les premières semaines bruyantes ; c'est la
  raison d'être de la règle anti-rafale (`P01.3`), écrite **avant** la mise sous
  tension. Le stockage n'est pas chiffré.
- **Réversibilité** : le déménagement vers un matériel dédié ne demande pas de
  retoucher les agents. L'installation elle-même se défait par le rôle Ansible,
  et ne modifie aucun état de production.

## Ce que cette décision n'autorise pas

Installer le profil complet (indexeur + console) sur `patator-standby` · exposer
le serveur central hors du tailnet · faire d'un poste d'administration l'hôte
nominal, `bluefin` compris · laisser passer la revue du 2027-03-07 sans écrire
ce qui a été décidé · poser ou retirer l'état de relève de HQ.

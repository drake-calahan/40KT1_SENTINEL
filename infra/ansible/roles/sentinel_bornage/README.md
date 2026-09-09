# Rôle `sentinel_bornage` — les deux conditions vérifiables d'`ADR-003`

> **Lot `P01.4`** · agent `claude` · Écrit sur le gabarit
> [`../GABARIT.md`](../GABARIT.md).

`ADR-003` accepte que le serveur central cohabite avec le miroir Postgres et la
relève en lecture seule sur les 16 Go de `patator-standby` — **sous quatre
conditions**, dont deux sont du code, et c'est ce rôle :

| # | Condition | Ce que ce rôle en fait |
|---|---|---|
| 1 | Bornage `cgroup` permanent | drop-in systemd posé **et mesuré** |
| 2 | Arrêt du serveur central quand la relève s'arme (`C3`) | interlock posé, **livré désarmé** |

## Deux moitiés, deux régimes — et c'est délibéré

**Le plafond est une contrainte.** Il ne fait rien : il empêche. Le poser n'arme
rien, au contraire — il réduit ce que la machine peut subir. Il est donc posé
**sans garde**, à chaque passage, et `sentinel_server` **refuse de s'armer sans
lui**.

**L'interlock est un automate.** Il arrête un service. C'est un geste, donc il
est livré désarmé comme tout le reste (`RULES` § 1) : unité et timer posés, ni
activés ni démarrés.

Confondre les deux donnerait soit un plafond qu'on oublie d'armer — et la
condition 1 redevient déclarative, ce qu'`ADR-003` refuse explicitement —, soit
un automate armé par un merge.

## Ce rôle ne redémarre rien

systemd applique les limites d'un `cgroup` **à chaud** après `daemon-reload` :
borner le serveur central ne demande pas de l'interrompre. C'est ce qui permet
de rejouer ce rôle sur une machine en production sans rien redémarrer — la
règle de `host_baseline` dans HQ, et elle vaut ici.

`handlers/main.yml` ne contient donc **aucun** handler de redémarrage. S'il en
apparaît un, cette propriété est perdue et la revue doit le refuser.

## « Posé » ne veut pas dire « appliqué »

Un drop-in écrit sans `daemon-reload` est un fichier, pas une limite — et la
différence **ne se voit pas dans un `--diff`**. Le rôle relit donc ce que systemd
applique réellement et **échoue** si `MemoryMax` revient à `infinity` :

```bash
systemctl show wazuh-manager.service -p MemoryHigh -p MemoryMax -p CPUQuotaPerSecUSec
```

C'est ce qui rend la condition 1 *vérifiable* et non *déclarative*. En `--check`,
la mesure n'a pas lieu — et le bilan le dit, plutôt que de laisser un vert
passer pour une preuve.

## L'interlock : trois états, jamais deux

| État lu | Comment | Action |
|---|---|---|
| **armée** | le témoin existe | arrêt du serveur central |
| **au repos** | témoin absent, **dossier lisible** | rien, et en silence |
| **inconnu** | le dossier lui-même est illisible | `sentinel_bornage_interlock_sur_inconnu` |

« Témoin absent » et « je n'ai pas pu regarder » ne sont **pas** le même état.
C'est pour cela que le rôle vérifie le **répertoire** avant d'armer : sans lui,
l'interlock rendrait « inconnu » à chaque passage, et un dispositif qui crie
sans arrêt finit désactivé — le contraire du but.

### Le défaut sur inconnu est `signaler`, et voici pourquoi

1. Agir sur une mesure qu'on n'a pas pu prendre est exactement ce que `RULES`
   § 1 interdit.
2. Le risque que la condition 2 couvre — le moteur qui mange la mémoire du
   standby pendant que la relève sert la production — est **déjà borné par la
   condition 1**, qui est permanente et inconditionnelle. L'interlock est un
   raffinement au-dessus d'un plafond, pas la seule protection.

`arreter` reste un choix défendable. Il se pose dans `defaults/`, il se
consigne, et il n'a pas besoin d'un amendement d'ADR.

### Ce que l'interlock ne fait jamais

- Il n'arme pas la relève, ne la désarme pas, ne la retarde pas. Il **lit**.
  Deux automates qui se posent le même verrou est un mode de panne connu
  ([`contrat-hq.md`](../../../../docs/contrat-hq.md) § 2).
- Il **ne redémarre pas** le serveur central quand la relève retombe.
  Quelqu'un doit d'abord regarder *pourquoi* elle s'est armée. Un automate qui
  redémarre tout seul masque exactement l'incident qu'on veut voir.

## Le prérequis qui bloque l'armement

`hq_failover_state_confirme` vaut **`false`**, et `00_garde.yml` **refuse
d'armer l'interlock** tant qu'il vaut `false`.

Le contrat de frontière nomme l'objet — « l'état de la relève (armée / au
repos) » — mais **pas le fichier qui le porte** : ce mécanisme vit dans
`scripts/failover.py` et `ADR-061`, côté HQ. La valeur présente dans
`group_vars` est une **hypothèse**, calquée sur le témoin de mode tournoi qui
vit dans le même répertoire.

Un automate qui arrête le serveur de sécurité en se fondant sur un chemin deviné
est **pire** que pas d'interlock : il s'arrêterait au hasard, ou jamais, sans
qu'on sache lequel.

Ce chemin se confirme en portant le jumeau du contrat dans HQ (`P00.5`), et se
consigne **des deux côtés**.

## Comment on l'arme

Deux gestes distincts, dans cet ordre, chacun par un humain qui déroule un
runbook :

```bash
# 1. Le plafond est déjà posé par un passage normal du rôle. On le VÉRIFIE :
systemctl show wazuh-manager.service -p MemoryMax
```

```bash
# 2. L'interlock, une fois le chemin de l'état de la relève confirmé :
ansible-playbook playbooks/01_server.yml \
  -e '{"sentinel_bornage_interlock_enabled": true}' --check --diff
```

⚠️ **`--check --diff` d'abord, ordre PO de la session courante ensuite, apply en
dernier** (`RULES` § 2).

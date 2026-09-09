# Gabarit de rôle — le contrat que tout rôle de Sentinelle respecte

> **Lot `P01.6`** · agent `claude` · Ce document et le rôle
> [`gabarit/`](gabarit/) qui l'accompagne passent **avant** le premier vrai rôle.
> Sans eux, le deuxième rôle recopie les choix implicites du premier, et
> personne ne les revoit jamais.

Le squelette à copier est [`gabarit/`](gabarit/) :

```bash
cp -r infra/ansible/roles/gabarit infra/ansible/roles/sentinel_agent
```

Puis on remplace `gabarit` par le nom du rôle partout, et on efface les
commentaires `À REMPLACER`. Ce qui suit explique **pourquoi** chaque pièce est
là — parce qu'un gabarit qu'on ne comprend pas se contourne.

---

## 1. Disposition des fichiers

```
roles/<nom>/
├── README.md            ce que le rôle fait, ce qu'il ne fait pas, comment on le désinstalle
├── defaults/main.yml    tout ce qui se surcharge — dont la garde `*_enabled`
├── vars/main.yml        ce qui ne se surcharge PAS (constantes du rôle)
├── meta/main.yml        `galaxy_info` minimal, dépendances explicites
├── handlers/main.yml    UNIQUEMENT des unités `sentinel-*`, et c'est vérifié
├── templates/           toute configuration est rendue, jamais éditée en place
└── tasks/
    ├── main.yml         orchestration, et rien d'autre
    ├── 00_garde.yml     préconditions — ce qui doit être vrai avant de poser
    ├── 10_pose.yml      la pose des fichiers ; ne démarre rien
    ├── 20_armement.yml  ce qui n'a lieu QUE si la garde est passée à `true`
    └── 90_bilan.yml     le rendu de compte, y compris ce qui n'a pas été fait
```

`tasks/main.yml` **n'exécute aucune tâche métier** : il enchaîne les quatre
fichiers, dans cet ordre, avec leurs `tags`. Un `main.yml` qui fait le travail
finit à trois cents lignes et devient illisible à 3 h du matin.

**Numéroter les fichiers de tâches** (`00_`, `10_`, …) : l'ordre d'exécution est
alors visible dans `ls`, ce qui n'est pas le cas avec `garde.yml`, `pose.yml`,
`armement.yml`.

---

## 2. La garde `*_enabled` — le cœur du gabarit

`RULES` § 1 : *tout est désarmé par défaut ; armer est un geste d'exploitation.*
Le gabarit rend cette règle **structurelle**, pas déclarative.

### Les trois obligations

1. **`defaults/main.yml` porte `<role>_enabled: false`.** Cette valeur ne change
   jamais dans le dépôt. La CI `garde-armement` refuse une PR qui la passe à
   `true` — voir [`.github/scripts/garde-armement.sh`](../../../.github/scripts/garde-armement.sh).
2. **`00_garde.yml` vérifie que c'est un booléen**, et non la chaîne `"false"`
   qui vaut `true` en Jinja. C'est le mode de panne classique d'un `-e` mal
   passé, et il arme silencieusement.
3. **Tout ce qui arme vit dans `20_armement.yml`, et nulle part ailleurs.** Le
   fichier entier est sous `when: <role>_enabled | bool`. Un `when` d'armement
   dispersé dans cinq tâches ne se relit pas.

### Ce que « désarmé » veut dire, précisément

| Élément | `_enabled: false` (le défaut) | `_enabled: true` (geste de runbook) |
|---|---|---|
| Fichiers, configuration, template | **posés** | posés |
| Unité `sentinel-*` | **installée**, ni `enabled` ni `started` | `enabled` **et** `started` |
| Timer `sentinel-*` | **installé**, arrêté | activé |

Poser sans démarrer est le point entier : `--check --diff` montre alors ce que
l'armement fera, avant que quiconque l'arme.

---

## 3. « Aucun redémarrage d'un service de HQ »

HQ possède `ufw`, Docker, Tailscale, `auditd` s'il est à lui, et toutes les
unités `40kt1-*`. Sentinelle **ajoute** ([`contrat-hq.md`](../../../docs/contrat-hq.md)).

La règle : **un rôle de ce dépôt ne redémarre que des unités dont le nom commence
par `sentinel-`.** Elle n'est pas laissée à la vigilance du relecteur.

- Les redémarrages passent **tous** par le handler `redemarrer les unites
  sentinelle` de [`gabarit/handlers/main.yml`](gabarit/handlers/main.yml), qui
  **affirme le préfixe avant d'agir** et échoue s'il ne le trouve pas.
- Aucune tâche de rôle n'appelle `ansible.builtin.systemd_service` avec
  `state: restarted` en direct. Si vous en écrivez une, vous contournez la
  garde, et la revue la refusera.
- Un changement qui **exigerait** de redémarrer un service de HQ ne se joue pas :
  il se **signale** dans `90_bilan.yml` et le rôle s'arrête là. C'est
  `infra/ansible/README.md` § 1, rendu exécutable.

Pourquoi si strict : `patator-tower` sert `hq.40kt1.com`. Un `restart` de
`docker` ou de `caddy` glissé dans un handler coupe le site public pendant
l'installation d'un outil de sécurité, et personne ne fait le lien.

---

## 4. Le bilan de fin de rôle, et le compte des hôtes

Deux bilans, deux portées, deux modes de panne différents.

### 4.1 Bilan **de rôle** — par hôte (`90_bilan.yml`)

Il dit, pour l'hôte courant : le rôle est-il armé ou non, ce qui a été posé, et
surtout **ce qui a été signalé sans être joué**. Un rôle qui se tait sur ce
qu'il a refusé de faire est un rôle qui ment par omission.

### 4.2 Bilan **de play** — le nombre d'hôtes réellement touchés

C'est le contrôle qui distingue « tout va bien » de « je n'ai regardé
personne ». Il compare `ansible_play_hosts_all` (les hôtes visés) à
`ansible_play_hosts` (ceux encore joignables à la fin).

> **Le piège, déjà payé dans HQ** : cinq playbooks visaient un hôte en dur. Le
> déplacer les aurait rendus muets — **sur zéro hôte, en rendant `ok`**.

Et le bilan de play ne suffit pas à l'attraper : **un play qui vise un groupe
vide n'exécute aucune tâche**, donc aucun bilan ne s'affiche. Le seul endroit
qui peut le voir est **en amont**.

### 4.3 La garde de cible — obligatoire en tête de chaque playbook

Tout playbook de ce dépôt commence par un play `localhost` qui **affirme que le
groupe visé n'est pas vide**, avant que le play réel ne s'exécute :

```yaml
- name: Garde de cible — refuser un play qui ne vise personne
  hosts: localhost
  gather_facts: false
  connection: local
  tasks:
    - name: Le groupe visé porte au moins un hôte
      ansible.builtin.assert:
        that: groups['sentinel_agents_linux'] | default([]) | length > 0
        fail_msg: >-
          Le groupe « sentinel_agents_linux » est vide : ce playbook ne toucherait
          AUCUN hôte et rendrait « ok ». C'est le pire mode de panne du parc.
```

Le modèle complet est dans
[`playbooks/00_check.yml`](../playbooks/00_check.yml), qui n'existe que pour ça.

---

## 5. Trois états, jamais deux

`RULES` § 1 : **un `ok` n'est pas un `inconnu`.** Toute vérification écrite dans
un rôle rend `ok`, `ko` **ou** `unknown` — et `unknown` n'est pas `ok`.

En pratique, dans une tâche de contrôle :

- `failed_when` / `changed_when` explicites, **jamais** laissés au défaut ;
- un `stat` qui ne peut pas lire rend `unknown`, pas « fichier absent » ;
- ne **jamais** écrire `when: ... | default(true)` sur un contrôle : le défaut
  transforme l'absence de mesure en mesure réussie.

Le mode tournoi est l'exemple canonique : le fichier témoin
`{{ hq_tournament_mode_file }}` est **présent** (tournoi), **absent** (pas de
tournoi), ou **illisible** (inconnu — et on ne conclut pas).

---

## 6. Idempotence et `--check`

- Le rôle est **rejouable sur une machine en production sans rien redémarrer**.
- Deux `--check` consécutifs montrent **zéro changement** au second.
- Toute tâche de lecture porte `changed_when: false`. Une commande de contrôle
  qui se déclare `changed` rend l'idempotence indémontrable.
- Le rôle fonctionne **en `--check`** : pas de `command` dont le résultat
  conditionne une tâche suivante sans `check_mode: false` assumé et commenté.

---

## 7. Secrets

Un rôle **pose des permissions, jamais des valeurs** (`RULES` § 4).

- Les trois secrets (clé d'enrôlement, jeton d'API, webhook Discord) sont lus
  depuis le `.env` **de la machine**, jamais depuis l'inventaire, jamais depuis
  le dépôt.
- Toute tâche qui les manipule porte **`no_log: true`**.
- Un secret **absent** fait échouer le rôle avec un message actionnable. Il ne le
  fait jamais continuer : un composant installé et non enrôlé est un faux vert.

---

## 8. La liste de relecture d'une PR de rôle

À dérouler avant de demander la revue. Chaque ligne correspond à un § ci-dessus.

- [ ] Disposition conforme ; `tasks/main.yml` n'orchestre que (§ 1).
- [ ] `<role>_enabled: false` dans `defaults/`, garde de type en `00_garde.yml`,
      tout l'armement dans `20_armement.yml` (§ 2).
- [ ] Aucun `state: restarted` en direct ; aucune unité non `sentinel-*` (§ 3).
- [ ] Bilan de rôle **et** bilan de play ; garde de cible en tête de playbook (§ 4).
- [ ] Chaque contrôle distingue `ok` / `ko` / `unknown` (§ 5).
- [ ] Deux `--check` de suite : zéro changement au second (§ 6).
- [ ] `no_log` sur les secrets ; aucune valeur sensible dans le diff (§ 7).
- [ ] `ansible-lint` et `yamllint` verts.
- [ ] Le `README.md` du rôle dit **comment on le désinstalle**.

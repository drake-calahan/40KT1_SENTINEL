# Ansible — Sentinelle

> ⚠️ **Un seul playbook existe : [`playbooks/00_check.yml`](playbooks/00_check.yml),
> qui ne change rien.** Aucun rôle de production n'est écrit. Les cibles de cet
> inventaire sont les **deux machines de production** du parc. Lire
> [`.agent/RULES.md`](../../.agent/RULES.md) § 2 avant toute commande.

## Avant d'écrire un rôle

**Lire [`roles/GABARIT.md`](roles/GABARIT.md)**, et copier
[`roles/gabarit/`](roles/gabarit/). Le gabarit fixe la disposition, la garde
`*_enabled`, la politique « aucun redémarrage d'un service de HQ », le bilan de
fin de rôle et la garde de cible. Il passe **avant** le premier rôle : sinon le
deuxième recopie les choix implicites du premier, et personne ne les revoit.

## La règle, avant tout le reste

```
--check --diff  →  ordre PO de la session courante  →  apply
```

Le hook shell de Cursor **refuse** un `ansible-playbook` sans `--check`.
Ce n'est pas une précaution de style : `patator-tower` sert `hq.40kt1.com`.

## Structure cible

```
infra/ansible/
├── ansible.cfg
├── requirements.yml          collections, source unique (CI + poste d'admin)
├── inventory/
│   ├── production.yml        les deux nœuds + l'hôte central (tranché, ADR-003)
│   └── group_vars/
│       └── all/main.yml      variables partagées, aucun secret
├── playbooks/
│   ├── 00_check.yml          préconditions, LECTURE SEULE          (P01.6) ✔
│   ├── 01_server.yml         serveur central, profil frugal        (P01.0)
│   ├── 02_agent.yml          agents sur les nœuds Linux            (P01.1)
│   └── 03_responder.yml      exécuteur local + unités systemd      (P03.0)
└── roles/
    ├── GABARIT.md            le contrat de tout rôle                (P01.6) ✔
    ├── gabarit/              le squelette à copier                  (P01.6) ✔
    ├── sentinel_server/
    ├── sentinel_agent/
    └── sentinel_responder/
```

## Le seul playbook jouable aujourd'hui

```bash
cd infra/ansible && ansible-playbook playbooks/00_check.yml --check --diff
```

Il **lit** et ne pose rien : c'est le seul du dépôt dont ce soit vrai, et c'est
pourquoi il porte le numéro `00`. Il refuse de conclure si aucun hôte n'a été
atteint — un contrôle qui n'a regardé personne ne rend jamais vert.

## Ce que tout rôle de ce dépôt doit respecter

1. **Idempotence.** Rejouable sur une machine en production **sans redémarrer un
   service**. Un changement qui l'exigerait est *signalé* dans le bilan du rôle,
   pas joué.
2. **Rien n'est armé.** Toute variable `*_enabled` vaut `false` par défaut.
   L'armement est un geste d'exploitation, décrit par un runbook.
3. **Sentinelle ajoute, ne réécrit jamais.** Règles pare-feu dans une chaîne
   dédiée et taguées ; unités préfixées `sentinel-*` ; jamais la politique
   `ufw` d'HQ, jamais Docker, jamais Tailscale.
4. **Aucun secret dans un rôle.** On pose des permissions, pas des valeurs.

## Pièges du parc, déjà payés (voir `.agent/DISCOVERY.md`)

- **`sudo-rs` est le `sudo` par défaut d'Ubuntu 26.04** et casse l'élévation :
  « Timeout waiting for privilege escalation prompt », un message qui ressemble à
  un problème de réseau ou de mot de passe et n'est ni l'un ni l'autre.
  Correctif : `ansible_become_exe: /usr/bin/sudo.ws`, déjà posé dans l'inventaire.
- **Un play qui vise zéro hôte rend `ok` sans rien faire.** Vérifier le nombre
  d'hôtes réellement touchés, pas le code de retour.
- **`patator-standby` perd son IPv4 régulièrement.** Un `--check` qui échoue sur
  ce nœud n'est pas forcément un défaut du playbook.

## Vérifications locales

```bash
yamllint -d "{extends: relaxed, rules: {line-length: disable}}" infra/ansible/
```

```bash
cd infra/ansible && ansible-lint playbooks/*.yml
```

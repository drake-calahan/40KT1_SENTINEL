# Rôle `gabarit` — squelette, pas un rôle de production

> **Ce rôle ne se joue pas. Il se copie.** Aucun playbook du dépôt ne
> l'inclut, et aucun ne doit l'inclure.

Le contrat qu'il matérialise est écrit dans [`../GABARIT.md`](../GABARIT.md).
Ce fichier-ci n'en est que la copie de travail.

## Comment on s'en sert

```bash
cp -r infra/ansible/roles/gabarit infra/ansible/roles/sentinel_agent
grep -rn "gabarit\|À REMPLACER" infra/ansible/roles/sentinel_agent
```

Le `grep` donne la liste exacte de ce qui reste à faire : chaque occurrence de
`gabarit` est un nom à changer, chaque `À REMPLACER` est un emplacement où le
vrai contenu s'écrit. Quand les deux motifs ont disparu, le rôle est complet au
sens du gabarit — pas au sens de sa fonction.

## Ce que le squelette apporte déjà, et qu'il ne faut pas défaire

| Pièce | Ce qu'elle empêche |
|---|---|
| `defaults/main.yml` — `gabarit_enabled: false` | qu'un merge arme un dispositif |
| `tasks/00_garde.yml` — garde de type | qu'un `-e x=false` arme en croyant désarmer |
| `tasks/00_garde.yml` — mode tournoi à trois états | qu'un témoin illisible se lise « pas de tournoi » |
| `tasks/10_pose.yml` — pose sans démarrer | qu'un `--check` ne montre pas ce que l'armement fera |
| `tasks/20_armement.yml` — tout l'armement, à un seul endroit | qu'un armement dispersé devienne illisible |
| `handlers/main.yml` — affirmation du préfixe `sentinel-` | qu'un handler coupe `hq.40kt1.com` |
| `tasks/90_bilan.yml` — les points signalés non joués | qu'un rôle mente par omission |

## Ce que ce rôle ne fait pas, et ne fera jamais

- Il **ne redémarre aucun service de 40KT1_HQ** — ni Docker, ni Tailscale, ni
  `ufw`, ni SSH, ni une unité `40kt1-*`. Le handler le refuse par
  affirmation, pas par convention.
- Il **ne pose ni ne retire** le témoin de mode tournoi : HQ le pose,
  Sentinelle le lit ([`docs/contrat-hq.md`](../../../../docs/contrat-hq.md)).
- Il **n'écrit aucun secret**.

## Désinstallation

Le squelette n'installe rien de réel, donc il n'y a rien à désinstaller.

**En revanche, tout rôle copié depuis lui doit remplir cette section**, et de
façon jouable : les chemins exacts à retirer, l'unité à désactiver, l'état à
conserver ou non. `ADR-001` compte la désinstallation par le rôle parmi les
propriétés qui rendent le choix réversible — une réversibilité qu'aucun rôle ne
sait exécuter n'est qu'une phrase.

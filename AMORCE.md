# AMORCE — poser ce paquet comme dépôt

> Ce fichier est le seul du paquet qui ne fait pas partie du dépôt final.
> **Le supprimer après le premier commit** (`git rm AMORCE.md`).

## Ce que contient le paquet

Un dépôt complet en **phase 0** : harnais agent, couche Cursor, trois ADR au
statut *Proposé*, un plan, trois runbooks, le contrat de frontière avec
`40KT1_HQ`, un squelette Ansible et trois workflows de CI.

**Aucun code exécutable, aucun playbook, aucune valeur de secret.** C'est
délibéré : l'hôte du serveur central n'est pas tranché, et écrire un rôle avant
la décision reviendrait à trancher par un commit.

## 1. Poser le dépôt local

Décompresser l archive dans ton espace de travail : elle contient un dossier
`40KT1_SENTINEL/` complet, fichiers cachés inclus (`.agent/`, `.cursor/`,
`.github/`, `.gitignore`).

```bash
cd <ton-espace-de-travail>/40KT1_SENTINEL && git init -b main
```

```bash
rm AMORCE.md
```

## 2. Vérifier avant de committer

Deux contrôles qui coûtent trente secondes et évitent une reprise d'historique.

```bash
git status --short
```

Aucun fichier `.env` ne doit apparaître — seul `.env.example` est suivi.

```bash
grep -rn "enabled: true" infra/ansible/ .env.example || echo "OK : rien n est arme"
```

## 3. Premier commit

```bash
git add -A && git commit -m "chore(amorce): squelette du depot Sentinelle, phase 0 — TASKS#P00.0"
```

## 4. Créer le dépôt distant — **privé**

```bash
gh repo create drake-calahan/40KT1_SENTINEL --private --source=. --remote=origin --push
```

Vérifier que la visibilité est bien `private` : le dépôt décrit la topologie du
parc, les chemins, les comptes et les horaires. C'est une carte du système.

## 5. Les trois gestes GitHub qui restent

1. **Protection de branche sur `main`** — PR obligatoire, pas de push direct.
   C'est la contrepartie du garde-fou « jamais push sur `main` » qui n'est,
   côté agents, qu'une règle de texte.
2. **Vérifier que les trois workflows tournent** sur la première PR
   (`ansible-ci`, `python-ci`, `secrets-scan`). En phase 0 ils sont verts sans
   rien avoir à faire — c'est attendu, et documenté dans chaque fichier.
3. **Rien d'autre.** Pas de secret à poser : les trois secrets du dispositif
   vivent dans le `.env` des machines, pas dans GitHub.

## 6. Ce qu'il faut faire ensuite, dans l'ordre

| # | Geste | Où |
|---|-------|-----|
| 1 | Répondre au questionnaire | [`docs/cadrage/questionnaire.md`](docs/cadrage/questionnaire.md) |
| 2 | Consigner les réponses, avec leur date | [`.agent/ACTIVE.md`](.agent/ACTIVE.md) § « Réponses au cadrage » |
| 3 | Faire passer les ADR de *Proposé* à *Accepté* | [`docs/adr/`](docs/adr/) |
| 4 | **Créer le jumeau du contrat de frontière côté `40KT1_HQ`** | `P00.5` |
| 5 | Écrire `01_server.yml` | débloqué par `ADR-003` |

Le geste 4 est le plus facile à oublier et le plus coûteux : une frontière
écrite d'un seul côté n'est pas une frontière, c'est une intention que l'autre
dépôt ignore.

## Ce que le paquet ne prétend pas être

Il ne remplace pas les décisions. Les défauts proposés dans le questionnaire
sont des propositions argumentées, pas des choix faits — et quatre d'entre eux
(`C1`, `E2`, `E4`, `H3`) changent la forme du code, pas seulement ses valeurs.

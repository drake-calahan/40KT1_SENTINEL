## Ce que fait cette PR

<!-- Une phrase. Le titre porte le reste. -->

Tâche : `TASKS#P0X.Y`

## Preuves

<!-- Commandes réellement exécutées et leur résultat. Pas « CI verte » : la
     sortie. Ne jamais annoncer vert sur une vérification partielle. -->

- [ ] `ruff check` + `ruff format --check`
- [ ] `pytest` (dont les **refus** de l'exécuteur, s'il est touché)
- [ ] `yamllint` + `ansible-lint`
- [ ] `ansible-playbook … --check --diff` si un rôle est touché

## Garde-fous de ce dépôt

- [ ] **Aucun `*_enabled` passé à `true`** — **vérifié par la CI `garde-armement`**
- [ ] Aucun secret dans le diff (`.env.example` seul est éditable)
- [ ] Sentinelle **ajoute** : rien de ce qui appartient à `40KT1_HQ` n'est
      réécrit (politique `ufw`, Docker, Tailscale, mode tournoi)
- [ ] Unités préfixées `sentinel-*`, règles pare-feu dans la chaîne dédiée
- [ ] Les sondes touchées distinguent `ok` / `ko` / **`unknown`**
- [ ] Une décision d'architecture ? → l'ADR existe **et** précède ce code

## Ce que cette PR n'arme pas

<!-- Si elle livre du code d'armement, dire explicitement quel runbook devra
     être joué, par qui, et ce qui restera désarmé après le merge.
     Code livré n'est pas dispositif armé. -->

# Runbooks — Sentinelle

> ⚠️ **Deux le sont désormais** — `poste-de-commande.md` et
> `mise-en-service.md`, depuis le 2026-09-10 : les rôles existent et la chaîne
> complète a été répétée à blanc sur un hôte vierge (`P01.20`). **Rien n'est
> installé sur le parc pour autant** : jouable veut dire « la procédure tient »,
> pas « c'est fait ». Les autres restent fermés, et chacun porte un encadré qui
> dit à quelle condition il s'ouvre.
>
> Un runbook qui ment sur son propre état a déjà coûté un incident dans
> `40KT1_HQ` (« le runbook mentait sur son propre script », revue `P34.3`).
> D'où ces encadrés, et d'où cette page.

| Runbook | Ce qu'il fait | Jouable quand |
|---|---|---|
| [`poste-de-commande.md`](poste-de-commande.md) | Préparer WSL sur `AEGIS-TOWER` : Ansible, SSH, tailnet | ✅ **maintenant** |
| [`mise-en-service.md`](mise-en-service.md) | Installer le serveur central et les agents, en observation seule | ✅ **maintenant** — `ADR-003` acceptée, rôles écrits, chaîne répétée |
| [`armement-de-la-reponse.md`](armement-de-la-reponse.md) | Passer de l'observation à l'alerte, puis à la réponse | phases `P1` et `P2` sorties |
| [`mode-a-blanc.md`](mode-a-blanc.md) | Lire le journal de réponse sans laisser jouer de geste | exécuteur installé en dry-run |
| [`desarmement-d-urgence.md`](desarmement-d-urgence.md) | Arrêter le dispositif quand il se trompe | dès que quoi que ce soit est armé |

## L'ordre n'est pas décoratif

**Préparer le poste → regarder → alerter → agir à blanc → agir.** Chaque étape ne s'ouvre que si la
précédente a produit sa preuve. C'est l'ordre du runbook `supervision-croisee.md`
de HQ, et son motif tient encore :

> *Armer un watchdog sans destinataire, c'est reconstruire exactement ce que ce
> chantier corrige.*

## Un runbook lu à 3 h du matin

Ils sont écrits pour ça : phrases courtes, une idée par phrase, et **le motif de
chaque étape** — parce que c'est le motif qui empêche de sauter l'étape quand on
est pressé.

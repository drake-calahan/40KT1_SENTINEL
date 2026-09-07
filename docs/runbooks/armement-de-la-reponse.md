# Armement — de l'observation à la réponse

> ⚠️ **PAS ENCORE JOUABLE.** Devient jouable quand la phase `P1` est sortie
> (critère chiffré atteint) et que
> [`ADR-002`](../adr/ADR-002-catalogue-et-budget-de-reponse.md) est **acceptée**.

## L'ordre, et pourquoi il n'est pas négociable

**1. Prouver que l'alerte arrive → 2. Alerter → 3. Répondre à blanc → 4. Armer.**

Chaque étape ne s'ouvre que si la précédente a produit sa preuve. Ce n'est pas de
la prudence de façade : c'est l'ordre du runbook `supervision-croisee.md` de HQ,
qui existe parce que l'inverse a déjà été construit une fois — un dispositif armé
qui n'alertait personne.

## Étape 1 — Poser les destinataires, et prouver le câblage

Dans le `.env` du nœud :

```bash
SENTINEL_DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
SENTINEL_PUSH_URLS=https://ntfy.sh/<un-sujet-non-devinable>
```

Puis provoquer une alerte de test. **Un message doit arriver sur le téléphone
ET dans Discord.** S'il n'arrive pas, **on s'arrête ici** — armer sans
destinataire est exactement le défaut que ce dépôt corrige.

Les deux variables acceptent des listes séparées par des virgules : un coéquipier
d'astreinte s'ajoute sans toucher au code.

## Étape 2 — Ouvrir l'alerte, garder la réponse fermée

`SENTINEL_RESPONSE_ENABLED` reste à `false`. Les alertes partent, rien n'agit.

Laisser tourner jusqu'à ce qu'une **alerte réelle** ait été traitée de bout en
bout : reçue, comprise, close. Une alerte de test prouve le câblage ; une alerte
réelle prouve qu'on sait quoi en faire.

## Étape 3 — La réponse à blanc

```bash
SENTINEL_RESPONSE_ENABLED=true
SENTINEL_RESPONSE_DRY_RUN=true
```

L'exécuteur journalise ce qu'il **aurait** fait, sans agir. **Deux semaines.**

À relire chaque semaine : chaque geste simulé était-il justifié ? Un seul geste
injustifié suffit à repousser l'armement — et c'est le but de l'étape.

## Étape 4 — Tester le frein AVANT de le desserrer

Jouer [`desarmement-d-urgence.md`](desarmement-d-urgence.md) **en entier, depuis
un téléphone**, avant d'armer.

Un frein qu'on n'a jamais essayé n'est pas un frein. Le jour où on en aura
besoin, on sera en train de gérer autre chose.

## Étape 5 — Armer, catalogue minimal, hors mode tournoi

```bash
SENTINEL_RESPONSE_DRY_RUN=false
```

Sur **un nœud à la fois**. Le catalogue armé se limite à ce que `ADR-002` déclare
armé — les autres gestes restent en alerte.

**Hors mode tournoi d'abord.** Le comportement en mode tournoi (`E4`) s'active
séparément, après un premier event observé.

## Après l'armement — ce qu'il faut lire chaque semaine

- **Le journal des gestes ET des refus.** Un refus fréquent est une information :
  soit la règle est mauvaise, soit le catalogue est trop étroit.
- **Le compteur de budget.** S'il s'approche de trois par heure, quelque chose
  ne va pas — et ce n'est probablement pas le dispositif.

## Deux comportements à connaître avant de s'en étonner

**Le budget gèle tout.** Au troisième geste dans l'heure glissante, une alerte
rouge part et le dispositif **cesse d'agir** jusqu'à intervention humaine.
Ce n'est pas une panne : c'est la garde qui fonctionne. Un dispositif qui répare
quarante fois par heure ne répare pas, il masque.

**Une alerte part à la transition, pas à chaque cycle**, avec un compteur
d'occurrences. Le compteur est l'information ; 143 messages ne le sont pas.

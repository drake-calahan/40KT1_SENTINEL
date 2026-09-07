# Désarmement d'urgence

> ⚠️ **PAS ENCORE JOUABLE** — il n'y a rien à désarmer aujourd'hui.
> Devient jouable dès que **quoi que ce soit** est armé, et il doit être
> **testé avant** le premier armement, pas après.

## Quand utiliser cette procédure

Le dispositif se trompe : il bloque une IP légitime, arrête un conteneur qui
devait tourner, ou part en rafale. On coupe d'abord, on comprend ensuite.

**Il n'y a pas de mauvais moment pour désarmer.** Un dispositif de sécurité à
l'arrêt est un risque connu ; un dispositif qui agit de travers est un risque
qu'on ne mesure pas.

## Les trois chemins, du plus rapide au plus complet

### Chemin 1 — Le témoin, depuis un téléphone

C'est le chemin hors bande, celui qui ne demande que SSH — donc celui qui marche
quand le reste ne marche plus.

```bash
touch ~/security-state/response-disarmed
```

Le fichier est lu **à chaque geste**, avant toute autre vérification. Dès qu'il
existe, plus aucun geste ne s'exécute. Les agents continuent de mesurer et
d'alerter : on perd la réponse, pas la vue.

**À faire sur le nœud concerné.** Si le doute porte sur les deux, le faire sur
les deux — cela ne coûte rien.

### Chemin 2 — Le cockpit ops

Depuis le cockpit de `40KT1_HQ`, la vue « sécurité » porte un bouton de
désarmement. Plus confortable, mais il suppose que le cockpit est joignable —
d'où le chemin 1 en premier.

### Chemin 3 — Couper le service

```bash
sudo systemctl stop sentinel-responder.service
```

Plus radical, et **moins bon** que le chemin 1 : le service arrêté ne journalise
plus rien, donc on perd la trace de ce qui se serait passé. À réserver au cas où
l'exécuteur lui-même est en défaut.

## Après le désarmement

1. **Lire le journal des gestes** — ce qui a été fait, à quelle heure, sur quelle
   règle.
2. **Défaire ce qui doit l'être.** Tous les gestes du catalogue sont réversibles
   par construction ; c'est le critère d'admission d'`ADR-002`.
   - IP bloquée → elle expire seule à 1 h, ou se retire de la chaîne dédiée
   - conteneur arrêté → `docker start`
   - fichier en quarantaine → déplacement inverse, l'empreinte a été conservée
3. **Consigner dans `.agent/DISCOVERY.md`** : date, ce qui s'est passé,
   l'implication. C'est ce qui évite la deuxième occurrence.
4. **Ne pas ré-armer le jour même.** Corriger la règle d'abord, repasser en
   `DRY_RUN` une semaine, puis ré-armer par
   [`armement-de-la-reponse.md`](armement-de-la-reponse.md).

## Retirer le témoin

```bash
rm ~/security-state/response-disarmed
```

⚠️ **Ce geste ré-arme le dispositif.** Il est refusé par le hook shell des agents
(`.cursor/hooks/guard_shell.py`) : seul un humain le fait, et seulement après
avoir corrigé la cause.

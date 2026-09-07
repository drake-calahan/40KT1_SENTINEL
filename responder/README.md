# `responder/` — L'exécuteur de réponse

> **Le composant le plus sensible du dépôt.** Il exécute des gestes privilégiés
> sur des machines de production. À écrire en phase `P3`, après
> [`ADR-002`](../docs/adr/ADR-002-catalogue-et-budget-de-reponse.md).

## Ce qu'il fait, en une phrase

Il reçoit un **ordre** du serveur central, vérifie qu'il a le droit de
l'exécuter, agit, et journalise — **le geste comme le refus**.

## Pourquoi il existe, plutôt que la réponse active du moteur

Le mécanisme de réponse active livré avec Wazuh exécute des commandes `root` sur
l'agent : sans budget, sans notion de mode tournoi, et dans son propre journal.
Il est un bon **transport** — c'est à ce titre qu'on l'utilise. Le script qu'il
appelle est un **relais mince** vers ce module.

Résultat : le catalogue, le budget et le journal restent dans ce dépôt, revus en
pull request. C'est la seule façon de tenir le critère d'`ADR-062` de HQ sans le
déléguer à un tiers.

## Les quatre gardes, dans cet ordre

L'ordre compte : le frein d'urgence passe avant tout le reste, y compris avant
de savoir si le geste est valide.

1. **Le témoin de désarmement** (`response-disarmed`). S'il existe, rien ne
   s'exécute. C'est le chemin hors bande, celui qui ne demande que SSH.
2. **Le catalogue.** Fermé et déclaratif. Un geste absent est refusé, même si
   l'ordre est bien formé. **Jamais** de commande construite depuis une chaîne
   reçue du réseau.
3. **Le budget.** Trois gestes par heure glissante. Le troisième déclenche un
   rouge ; au-delà, plus rien ne s'exécute jusqu'à intervention humaine.
4. **Le mode tournoi.** Lu depuis le fichier témoin de `40KT1_HQ`. Selon `E4`,
   il restreint le catalogue au lieu de l'élargir.

## Où la décision est prise

**Le serveur central corrèle et ordonne ; le nœud vérifie et exécute.**
Les quatre gardes sont évaluées **localement**, jamais côté serveur.
Conséquence voulue : un serveur central compromis peut faire du bruit, pas
n'importe quoi.

## Tests — la partie qu'on oublie

**Tester les refus autant que les gestes.** Un exécuteur dont seuls les succès
sont testés n'est pas testé : ce sont les refus qui portent la sécurité.

Les quatre cas obligatoires :

- geste **hors catalogue** → refusé, journalisé, motif explicite
- **budget épuisé** → refusé, alerte rouge, gel jusqu'à intervention
- **mode tournoi** actif et geste restreint → refusé
- **témoin de désarmement** présent → refusé, avant toute autre vérification

## Journalisation

Chaque geste **et chaque refus**, avec son motif, poussé en orange.
Au matin, on doit pouvoir lire ce que la machine a fait sans nous — **et ce
qu'elle n'a pas fait**. Une réponse invisible est une dérive qui a l'air d'un
miracle.

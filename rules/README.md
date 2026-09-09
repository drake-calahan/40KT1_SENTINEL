# `rules/` — Règles de détection

> **Une règle de détection est du code.** Versionnée ici, revue en PR, jamais
> éditée à la main sur une machine. Une règle modifiée en production et pas dans
> le dépôt est une règle qui disparaîtra au prochain `apply`.

## Structure cible

```
rules/
├── integrite/        fichiers sous scellé (D1) — .env, authorized_keys, unités
├── authentification/ SSH, sudo, sources jamais vues (P01.8)
├── docker/           conteneur privilégié, socket monté, port publié (P01.8)
├── conformite/       dérive de durcissement (règle ufw disparue, service réactivé)
└── agents/           santé des agents — dont l'anti-rafale du standby
```

## Plages d'identifiants

Les règles locales vivent au-dessus de `100000`. Une plage par famille — une règle
nouvelle n'entre jamais en collision avec une autre famille écrite en parallèle :

| Famille | Plage | Lot |
|---|---|---|
| `integrite/` | `100100`–`100199` | `P01.2` |
| `authentification/` | `100200`–`100299` | `P01.8` |
| `docker/` | `100300`–`100399` | `P01.8` |
| `conformite/` | `100400`–`100499` | `P01.9` |
| `agents/` | `100500`–`100599` | `P01.3` |

## Sévérité ↔ niveau moteur

Fixée en `P01.2`, documentée et câblée en `P02.1` — **ne pas la redéfinir ailleurs.**

| Sévérité du dépôt | Niveau moteur | Ce que ça déclenchera en phase 2 |
|---|---|---|
| `info` | 3–5 | rien — retour au vert |
| `orange` | 7–9 | Discord |
| `rouge` | 10–12 | Discord + push |
| `critique` | 13–15 | Discord + push, réservé aux **trois cas** de `F2` |

Les trois cas `critique`, et **aucun autre** : modification d'`authorized_keys` ·
connexion réussie depuis une source jamais vue · gel du budget de réponse.
Dans le lot `P01.2`, seule la règle sur `authorized_keys` porte `critique`.

## Ce que chaque règle porte

| Champ | Pourquoi |
|---|---|
| **Un commentaire en français** disant *ce qu'elle attrape* et *ce qui la ferait crier à tort* | elle sera relue pendant un incident, par quelqu'un sans contexte |
| **Une sévérité** : `critique` · `rouge` · `orange` · `info` | calquée sur `watchdog.py` de `40KT1_HQ` |
| **Le geste du catalogue** si elle déclenche une réponse | jamais une commande : le nœud résout le geste localement (`ADR-002`) |

## Le bruit — trois règles de tenue

**Agréger, ne pas répéter.** Fenêtre de 15 minutes avec compteur. *Le compteur
est l'information ; 143 messages ne le sont pas.*

**Les gestes normaux du parc ne sont pas des alertes.** Déploiement, sauvegarde
de 03:30, ingest, rotation de journaux, `unattended-upgrades`. Toute exclusion
est écrite **avec sa justification** — une exclusion sans motif finit par cacher
une vraie détection.

**La perte de contact avec l'agent de `patator-standby` est agrégée par
construction.** Ce nœud a un défaut IPv4 récidivant : quatre occurrences en trois
semaines. Sans cette règle, la première coupure produit une rafale, et la
réaction naturelle est de couper le bruit — donc de perdre le signal. La règle
s'écrit **avant** la mise sous tension (`P01.3`), pas après le premier week-end.

## Ce qui ne doit jamais entrer dans une règle

Une donnée nominative de joueur. Si une règle en capture, elle est mal écrite.

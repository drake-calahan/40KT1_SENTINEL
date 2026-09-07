# ADR-002 : Catalogue de réponse, budget, et comportement en mode tournoi

- **Statut** : **Proposé** — attend les réponses `E1` à `E7`
- **Date** : 2026-09-07
- **Décideurs** : Thomas (PO) + agent DevSecOps
- **Plan** : [`P01`](../plans/P01-mise-en-service.md) — phase `P3`
- **Prolonge** : `ADR-062` de `40KT1_HQ` (auto-réparation bornée) ·
  `ADR-061` de `40KT1_HQ` (relève en lecture seule, mode tournoi)

> ⚠️ **Cette ADR n'est pas tranchée**, et c'est celle qui porte le plus de risque.
> Deux points demandent un arbitrage explicite du PO : **quels gestes entrent au
> catalogue** (`E2`) et **le comportement en mode tournoi** (`E4`).

## Contexte

La demande porte sur une réponse automatique. Le dépôt frère a déjà tranché la
question voisine — la réparation automatique — et sa décision est directement
transposable.

`ADR-062` de HQ pose un **critère d'admission objectif** :

> Une automatisation n'a le droit de faire que ce qu'un humain peut défaire sans
> arbitrage.

Le critère n'est pas la confiance dans le code, c'est la **réversibilité**, et
elle se vérifie geste par geste. Redémarrer un conteneur se défait tout seul.
Restaurer une base ne se défait pas.

`ADR-062` pose aussi un **budget** : trois gestes automatiques par heure
glissante, le troisième déclenchant un rouge, et au-delà le système cesse
d'agir. Le motif est le mode d'échec classique de tout automatisme : *une machine
qui se répare quarante fois par heure ne se répare pas — elle masque une panne,
et elle la masque d'autant mieux que la réparation marche.*

## Options envisagées

1. **Utiliser la réponse active du moteur telle quelle.** Écartée : elle exécute
   en `root` sans budget, sans mode tournoi, et dans un journal séparé du nôtre.
2. **N'automatiser aucune réponse, alerter seulement.** Défendable, et c'est
   l'état de la phase 2. Écartée comme cible : la demande porte explicitement
   sur la réponse, et une alerte à 3 h du matin sur une rafale
   d'authentification ne réveille personne utilement.
3. **Un catalogue fermé, borné par un budget, évalué localement.** Retenue.

## Décision

### Où la décision est prise

**Le serveur central corrèle et ordonne ; le nœud vérifie et exécute.**
Catalogue, budget, mode tournoi et témoin de désarmement sont évalués
**localement**, jamais côté serveur. Conséquence voulue : un serveur central
compromis peut faire du bruit, pas n'importe quoi.

### Le catalogue — proposition, à trancher (`E2`)

La colonne qui décide n'est pas « est-ce utile » mais **« que faut-il faire pour
le défaire »**.

| Geste | Retour arrière | Proposé | Mode tournoi |
|---|---|---|---|
| Bloquer une IP | expiration automatique à 1 h | **armé** | armé |
| Arrêter un processus | il se relance, ou on le relance | **armé** | armé |
| Arrêter un conteneur | `docker start` — une commande | **armé** | alerte |
| Mettre un fichier en quarantaine | déplacement inverse, empreinte conservée | **armé** | armé |
| Désactiver un compte système | réactivation simple, mais coupe l'accès de secours | alerte | alerte |
| Révoquer les sessions JWT | reconnexion Discord de tous les utilisateurs | alerte | alerte |
| Couper le connecteur cloudflared | une commande — mais le site est hors ligne entre-temps | alerte | **jamais** |
| Passer l'app en lecture seule | réversible, saisies perdues entre-temps | alerte | alerte |
| Isoler le nœud du LAN | réversible *si* le tailnet tient — sinon déplacement physique à 70 km | **jamais** | jamais |

### Le budget

**Trois gestes automatiques par heure glissante**, aligné sur `ADR-062` de HQ.
Le troisième déclenche un rouge ; au-delà, le dispositif **cesse d'agir** et
n'alerte plus que. Le modifier est une décision d'ADR, pas un réglage.

### Le mode tournoi — le point à trancher (`E4`)

`ADR-061` de HQ a inversé l'intuition pour la bascule : l'automatisme n'existe
*que* pendant l'event, parce que c'est le seul moment où personne ne peut
intervenir.

**Pour la sécurité, la proposition est l'inversion inverse : moins agressive en
mode tournoi.** Un samedi de ronde, couper le connecteur public sur une
détection est une panne pour vingt personnes, pas une remédiation. Seuls les
gestes invisibles pour l'équipe s'exécutent ; le reste passe en alerte rouge avec
une action proposée à un clic depuis le téléphone.

**Ce n'est pas une évidence.** Si le scénario redouté est le rançongiciel, se
couper du monde est exactement le bon geste. C'est un arbitrage PO.

### Le désarmement d'urgence

Trois chemins, dont un qui ne demande que SSH :

1. le fichier témoin `security-state/response-disarmed` sur le nœud, lu **à
   chaque geste** ;
2. une commande du cockpit ops ;
3. une note dans le runbook de secours.

### Traçabilité

Chaque geste **et chaque refus** est journalisé, avec son motif, et poussé en
orange. Au matin, on doit pouvoir lire ce que la machine a fait sans nous —
**et ce qu'elle n'a pas fait**. Une réponse invisible est une dérive qui a l'air
d'un miracle.

## Conséquences

- **Positives** : les incidents bénins se traitent sans réveiller personne ; le
  budget garantit qu'un incident réel finit **toujours** par se voir ; aucun
  geste du catalogue ne peut détruire de la donnée.
- **Négatives / dette** : un catalogue fermé ne couvre pas ce qu'on n'a pas
  prévu. C'est le prix, et l'élargir se fait **par amendement de cette ADR**,
  jamais par ajout silencieux dans un script.
- **Réversibilité** : le catalogue est désarmable en bloc par une variable, et
  par le témoin hors bande.

## Ce que cette décision n'autorise pas

Restaurer une base · revenir à une version antérieure · promouvoir le standby en
écriture · supprimer ou modifier une donnée métier · faire tourner un secret ·
poser ou retirer le mode tournoi (il appartient à HQ).

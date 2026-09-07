# Questionnaire de cadrage — Sentinelle

> **Trente questions, huit blocs.** Chacune porte un **défaut proposé** : une
> réponse acceptable si tu n'as pas d'avis, et argumentée.
>
> **Mode rapide** : répondre « défauts sauf C1, E2, E4 » suffit — à condition que
> les quatre questions marquées **STRUCTURANTE** soient tranchées explicitement.
>
> Les réponses se consignent dans
> [`.agent/ACTIVE.md`](../../.agent/ACTIVE.md) § « Réponses au cadrage »,
> avec leur date. Une réponse consignée fait autorité sur le défaut proposé.

---

## Bloc A — Périmètre et objectif

**A1. Quels endpoints portent un agent, et dans quel ordre ?**
Cinq machines candidates : deux serveurs Linux, trois postes ops dont un Windows.
Les postes ne sont pas allumés en permanence — un agent y produit des trous de
télémétrie qu'il faut savoir lire comme normaux.
> **Défaut** — les deux nœuds Linux en phase 1. `AEGIS-TOWER` en phase 4 (il
> porte la clé d'administration : c'est une cible réelle). `pc-devsecops` et
> `bluefin` hors périmètre initial.

**A2. Objectif dominant : voir, ou agir ?**
Un dispositif qui répond avant d'avoir mesuré son bruit de fond répond à des faux
positifs, et le premier arrêt de conteneur injustifié coûte la confiance dans
tout le reste.
> **Défaut** — voir d'abord. La réponse s'arme après la période d'observation
> de `D5`, pas à la mise en service.

**A3. Surveille-t-on l'intérieur des conteneurs, ou seulement l'hôte ?**
La production tourne intégralement en Docker. Un agent hôte voit les appels
système et les événements Docker ; il voit mal ce qui se passe *dans* le
conteneur.
> **Défaut** — hôte + événements Docker en phase 1 ; télémétrie syscall par
> conteneur (Falco eBPF) en phase 4, **seulement si** la phase 1 montre qu'elle
> manque.

**A4. Ce projet est-il aussi un terrain d'apprentissage DevSecOps ?**
Un besoin pur de couverture pousse vers l'outil le plus complet ; un objectif
d'apprentissage pousse vers celui dont on écrit soi-même les règles.
> **Défaut** — oui, assumé. Outil sur étagère pour le moteur, **règles et
> catalogue écrits par nous** et versionnés.

---

## Bloc B — Menaces à couvrir en priorité

**B1. Classe ces six scénarios.**
Compromission de l'application exposée (cloudflared → Caddy → API) · chaîne
d'approvisionnement (pip, npm, images Docker, le scraper qui télécharge du
contenu externe) · vol de la clé SSH d'administration ou d'une session admin ·
rançongiciel sur un nœud · exfiltration de la base (données nominatives) ·
abus interne d'un compte légitime.
> **Défaut** — 1. application exposée · 2. chaîne d'approvisionnement ·
> 3. clé SSH / session admin · 4. rançongiciel · 5. exfiltration · 6. abus interne.

**B2. Les données nominatives imposent-elles une traçabilité formelle ?**
La base porte des identités Discord, des listes d'armée et des résultats
nominatifs. Une exigence RGPD revendiquée ferait de la journalisation des accès
administrateurs un livrable, pas une option — et durcirait le bloc G.
> **Défaut** — pas d'exigence formelle revendiquée, mais on trace les accès
> admin par hygiène. **À confirmer.**

**B3. Surveille-t-on les connexions sortantes des conteneurs ?**
Le scraper sort légitimement vers New Recruit, Google Sheets et Discord. C'est
aussi le chemin qu'emprunterait une exfiltration.
> **Défaut** — oui, en observation seule, sans liste blanche au départ. On
> construit la liste à partir de ce qu'on mesure.

---

## Bloc C — Le serveur central : où il vit

> Bloc le plus structurant. Tout le dimensionnement en dépend.
> Décision associée : [`ADR-003`](../adr/ADR-003-hote-du-serveur-central.md).

**C1. — STRUCTURANTE — Sur quelle machine tourne le serveur central ?**

| | Pour | Contre |
|---|---|---|
| **(a) `patator-standby`** | allumé 24/7 · à 70 km de la tour · ne sert pas le nom public | 16 Go partagés avec le miroir **et** la relève · réseau récidivant |
| **(b) matériel dédié** (mini-PC N100 / 16 Go, ~250 €) | le bon choix d'architecture · aucun domaine de panne partagé | coût |
| **(c) `patator-tower`** | puissance disponible | le serveur surveille son propre hôte — un compromis emporte les preuves |
| **(d) un poste ops** | — | **éliminé** : aucun n'est allumé la nuit (`B1` du plan `P37` de HQ) |

> **Défaut** — **(b) si le budget existe** ; sinon **(a) en profil frugal**, avec
> la sortie écrite dans l'ADR — exactement la forme qu'a prise l'exception
> `P31.7` pour le cockpit dans HQ.

**C2. Quel budget matériel est disponible ?**
Un ordre de grandeur suffit. Il décide entre profil frugal et profil complet.
> **Défaut** — zéro budget supposé. La proposition tient sans achat, et documente
> ce qu'un achat de ~250 € débloquerait.

**C3. Si c'est le standby : le serveur de sécurité s'efface-t-il pendant la relève ?**
Sous mode tournoi, le standby peut prendre le nom public en lecture seule. Il
sert alors l'équipe en salle, et un serveur de sécurité qui consomme 4 Go devient
un risque de disponibilité.
> **Défaut** — oui : bornage `cgroup` permanent et **arrêt automatique** du
> serveur central dès que la relève s'arme. Les agents continuent d'écrire en local.

**C4. Le serveur central est-il joignable autrement que par le tailnet ?**
> **Défaut** — non. Tailnet uniquement. Jamais de Funnel, jamais via cloudflared,
> jamais sur le nom public.

**C5. Chiffre-t-on le stockage du serveur central ?**
Il porte des journaux qui décrivent l'infrastructure entière : un disque volé est
une carte du système.
> **Défaut** — LUKS si matériel dédié. Sur le standby : hors périmètre phase 1,
> **noté comme dette**.

---

## Bloc D — Détection

**D1. Quels chemins sont sous scellé ?**
Trop large, le contrôle d'intégrité produit du bruit à chaque déploiement et on
le désactive. Trop étroit, il ne voit pas la porte dérobée.
> **Défaut** — `/etc` · les fichiers `.env` · `~/.ssh/authorized_keys` des deux
> comptes · les unités et timers systemd du projet · `docker-compose*.yml` ·
> `scripts/` · `/srv/40kt1` hors `backups/` et volumes Docker · les binaires
> `/usr/bin/sudo.ws` et `/usr/bin/tailscale`.

**D2. Temps réel ou balayage périodique ?**
> **Défaut** — temps réel sur la liste courte de `D1` ; balayage complet toutes
> les 12 h sur le reste.

**D3. Veut-on le contrôle de conformité (dérive de durcissement, type CIS) ?**
C'est ce qui détecte qu'une règle `ufw` a disparu, qu'un service s'est réactivé,
qu'un compte a gagné un droit.
> **Défaut** — oui, en lecture seule, rapport hebdomadaire. **Aucune remédiation
> automatique** : c'est le travail d'Ansible, et deux automates qui se corrigent
> l'un l'autre est un mode de panne connu.

**D4. Détection de vulnérabilités des paquets installés ?**
`unattended-upgrades` installe les correctifs de sécurité mais avec une liste
noire (`docker-ce`, `containerd`, `tailscale`) — donc un retard volontaire.
Un inventaire dit *de combien*.
> **Défaut** — oui, rapport hebdomadaire dans Discord. Pas d'alerte temps réel :
> une CVE publiée à 3 h du matin ne justifie pas de réveiller quelqu'un.

**D5. Combien de temps d'observation avant d'armer quoi que ce soit ?**
> **Défaut** — **14 jours**, incluant au moins un déploiement complet et une
> sauvegarde offsite. Critère de sortie chiffré : moins de 3 alertes non
> pertinentes par semaine.

---

## Bloc E — Réponse automatique

> Le cœur de la demande, et l'endroit où ce genre de projet se casse.
> Toutes les questions de ce bloc sont des décisions, pas des réglages.
> Décision associée : [`ADR-002`](../adr/ADR-002-catalogue-et-budget-de-reponse.md).

**E1. Reprend-on le critère d'admission d'`ADR-062` de HQ mot pour mot ?**
« Une automatisation n'a le droit de faire que ce qu'un humain peut défaire sans
arbitrage. » Le critère n'est pas la confiance dans le code, c'est la
**réversibilité**.
> **Défaut** — oui, cité explicitement dans `ADR-002`.

**E2. — STRUCTURANTE — Quels gestes entrent au catalogue ?**
Neuf candidats : bloquer une IP · tuer un processus · arrêter un conteneur ·
mettre un fichier en quarantaine · désactiver un compte système · révoquer les
sessions JWT · **couper le connecteur cloudflared** (= retirer l'exposition
publique) · passer l'application en lecture seule · isoler le nœud du LAN.
Le tableau geste par geste est dans `ADR-002`.
> **Défaut** — les **quatre premiers** armés. Les cinq autres en **alerte
> seulement** : ils touchent au service rendu ou à l'identité, et se défont mal
> sans arbitrage.

**E3. Quel budget de réponse avant gel ?**
La garde qui empêche le pire mode de panne : un dispositif qui « répare »
quarante fois par heure ne répare pas, il **masque**.
> **Défaut** — **3 gestes par heure glissante**, aligné sur `ADR-062` de HQ. Le
> troisième déclenche un rouge ; au-delà, plus aucune action.

**E4. — STRUCTURANTE — En mode tournoi, la réponse est-elle plus ou moins agressive ?**
`ADR-061` de HQ a inversé l'intuition pour la bascule : l'automatisme n'existe
*que* pendant l'event. Pour la sécurité, l'inversion joue peut-être dans l'autre
sens — un samedi de ronde, couper le connecteur public est une panne pour vingt
personnes. Mais si le scénario redouté est le rançongiciel, se couper du monde
est exactement le bon geste.
> **Défaut** — **moins agressive**. En mode tournoi, seuls les gestes invisibles
> pour l'équipe s'exécutent ; le reste passe en alerte rouge avec une action
> proposée à un clic depuis le téléphone.

**E5. Comment désarme-t-on en urgence, hors bande ?**
Le jour où le dispositif se trompe, il faut pouvoir l'arrêter *sans* passer par
lui, depuis un téléphone.
> **Défaut** — fichier `security-state/response-disarmed` lu à chaque geste ·
> une commande du cockpit · une note dans le runbook de secours. **Trois
> chemins, dont un qui ne demande que SSH.**

**E6. Réponse automatique sur le poste Windows : autorisée ?**
Un geste automatique qui tue un processus sur la machine où tu travailles ne se
distingue pas d'une panne.
> **Défaut** — non. Alerte seulement, sur les postes, toujours.

**E7. Le serveur central a-t-il le droit d'agir à distance sur un nœud ?**
Soit il pousse un ordre exécutable (pratique — et il devient la machine la plus
intéressante du réseau), soit chaque nœud décide seul à partir de règles reçues.
> **Défaut** — le serveur central **corrèle et ordonne**, le nœud **vérifie et
> exécute**. Catalogue, budget et mode tournoi sont évalués localement. Un
> serveur central compromis fait du bruit, pas n'importe quoi.

---

## Bloc F — Alerte et exploitation

**F1. Réutilise-t-on `notify.sh`, ou ouvre-t-on un canal dédié ?**
Un canal dédié sépare le bruit d'exploitation du signal de sécurité, mais double
la surface à câbler et à prouver — et un canal non prouvé est un canal muet.
> **Défaut** — même mécanisme (`notify.sh`), **salon Discord distinct**
> (`#securite`) et sujet ntfy distinct. Une preuve de câblage, deux destinations.

**F2. Grille de sévérité : on calque celle du watchdog ?**
Rouge = push + Discord · orange = Discord · info = retour au vert.
> **Défaut** — oui, plus une sévérité **critique** réservée à trois cas :
> modification d'`authorized_keys`, connexion réussie depuis une source jamais
> vue, gel du budget de réponse.

**F3. Alerte à la transition ou à chaque occurrence ?**
Le watchdog alerte aux transitions : « une supervision qui répète la même panne
toutes les dix minutes finit en sourdine ». En sécurité, la répétition porte
pourtant une information.
> **Défaut** — transition, plus agrégation par fenêtre de 15 min **avec
> compteur** (« 143 tentatives depuis 14:02 »). Le compteur est l'information ;
> 143 messages ne le sont pas.

**F4. Faut-il une console web ?**
C'est ce qui distingue le profil frugal du profil complet, et ça coûte ~4 Go.
La vraie question : qui l'ouvrira, à quelle fréquence, pour répondre à quoi ?
> **Défaut** — pas de console en phase 1. Une vue « sécurité » dans le cockpit
> ops en phase 3. Console complète seulement si `C1` débouche sur du matériel dédié.

**F5. Qui exploite, et combien de temps par semaine ?**
> **Défaut** — toi, seul, ~30 min par semaine. **Conséquence assumée** : tout ce
> qui exige une revue quotidienne est hors périmètre.

---

## Bloc G — Rétention et intégrité de la preuve

**G1. Combien de temps garde-t-on les journaux de sécurité ?**
Une rétention de 30 jours signifie qu'on découvre l'intrusion et qu'on n'a plus
le journal de son début.
> **Défaut** — 90 jours en ligne, 12 mois en archive compressée. Quelques Go par
> an pour deux nœuds — négligeable devant le NVMe de 512 Go.

**G2. Les archives partent-elles sur l'offsite existant ?**
`rclone` et une destination offsite sont déjà en place et éprouvés.
> **Défaut** — offsite existant, dossier séparé, archives chiffrées avant envoi.
> ⚠️ Le retex du 04/09 signale une sauvegarde offsite **muette** : la mise en
> service devra **prouver** l'écriture, pas la supposer.

**G3. Protège-t-on les journaux contre l'effacement local ?**
Un attaquant qui obtient `root` efface ses traces avant de partir. Le seul remède
réel est l'envoi immédiat vers une machine qu'il ne contrôle pas — ce qui redonne
son importance à `C1`.
> **Défaut** — envoi immédiat vers le serveur central, sans mise en file locale
> prolongée. Pas de journal en écriture unique côté nœud en phase 1.

---

## Bloc H — Dépôt et livraison

**H1. Nom et visibilité du dépôt ?**
Le nom apparaîtra dans des chemins `/opt`, des unités systemd et des règles
Ansible : il se change mal après coup.
> **Défaut** — `40KT1_SENTINEL`, **privé**, même propriétaire GitHub que HQ.

**H2. Le dépôt reprend-il le harnais `.agent/` de HQ ?**
> **Défaut** — oui, copié et adapté : **Claude Code et Cursor uniquement**, et
> **aucun serveur MCP**. Numérotation d'ADR repartant à `ADR-001`, avec renvois
> explicites vers les ADR de HQ.

**H3. — STRUCTURANTE — Qui possède quoi sur les nœuds ?**
Deux dépôts qui provisionnent les mêmes machines, c'est le risque d'intégration
principal. Si les deux touchent `ufw`, chacun défait l'autre à chaque `apply`, et
le symptôme est une règle qui « disparaît toute seule ».
> **Défaut** — HQ possède la **base** (politique `ufw`, Docker, Tailscale, mises
> à jour, arborescence, unités `40kt1-*`). Sentinelle **ajoute** des règles
> taguées dans une chaîne dédiée et ses propres unités `sentinel-*`, et ne
> réécrit **jamais** une politique. Contrat écrit **dans les deux dépôts** :
> [`contrat-hq.md`](../contrat-hq.md).

**H4. Un playbook Sentinelle peut-il toucher la production sans go explicite ?**
> **Défaut** — non. Mêmes garde-fous que HQ, recopiés dans `.agent/RULES.md`,
> et `--check --diff` obligatoire avant tout `apply`.

**H5. Quelle CI, et sur quel runner ?**
Le quota GitHub-hosted est un sujet ouvert (`P0.14` de HQ, runner auto-hébergé en
cours de réactivation) : un second dépôt le consomme aussi.
> **Défaut** — mêmes workflows (`ansible-lint`, `ruff`/`pytest`, `gitleaks`),
> GitHub-hosted au départ. Bascule vers le runner auto-hébergé quand `P0.14` est clos.

**H6. Où vivent les secrets du dispositif ?**
Trois secrets, pas plus — mais la clé d'enrôlement permet d'inscrire un faux agent.
> **Défaut** — `.env` non versionné + `.env.example` documenté + `gitleaks` en CI.
> Pas de coffre en phase 1 : **dette écrite**, pas oubli.

---

## Récapitulatif des quatre décisions bloquantes

| # | Question | Bloque |
|---|----------|--------|
| **C1** | Où vit le serveur central | toute la phase `P1` |
| **E2** | Quels gestes entrent au catalogue armé | la phase `P3` |
| **E4** | Réponse plus ou moins agressive en mode tournoi | la phase `P3` |
| **H3** | Frontière de propriété avec HQ | le premier rôle Ansible |

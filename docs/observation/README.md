# Observation — protocole de la période `D5`

> **Audience** : PO / ops · **Statut** : jouable dès que des alertes existent ·
> **Rien n'est armé** par ce document.

Instrument de mesure de la phase 1. Sans lui, le critère chiffré de sortie se
juge à l'impression — et l'impression dira toujours « ça a l'air calme ».

## 1. Ce qu'on mesure

Les alertes produites par le dispositif pendant la phase 1 (observation seule).
Chaque alerte reçoit **un** verdict parmi trois :

| Verdict | Sens |
|---------|------|
| `pertinente` | signal utile : il fallait le voir |
| `non pertinente` | faux positif au sens du § 2 |
| `indeterminee` | on n'a pas pu conclure |

Une sonde qui n'a pas mesuré ne rend jamais `ok`. Idem ici : une alerte non
classée n'est pas une alerte « qui passe ».

## 2. Ce qu'est une alerte non pertinente

Trois points, écrits noir sur blanc.

**Non pertinente** — l'alerte décrit un geste normal du parc (déploiement,
sauvegarde de 03:30, ingest du scraper, rotation de journaux,
`unattended-upgrades`) ou un artefact du dispositif lui-même.

**Indéterminée** (`indeterminee`) — on n'a pas pu conclure. Elle **ne compte
pas comme pertinente**, et elle ne compte pas comme non pertinente non plus :
elle a sa colonne. Deux indéterminées de suite sur la **même** règle valent une
tâche. *Une mesure qu'on n'a pas pu prendre ne rend jamais `ok`.*

**Perte de contact avec l'agent de `patator-standby`** — cas nommé. Le défaut
IPv4 récidivant (quatre occurrences en trois semaines) produira des alertes
légitimes sur un incident réseau qui n'est **pas** un incident de sécurité. On
compte **une alerte par épisode** (agrégation), pas une par sonde ni une par
tentative de contact. Sinon une seule coupure suffit à faire échouer le critère
de sortie.

## 3. Quand on regarde

Rythme déclaré en `F5` : **~5 min par jour**, **~1 h de repassage par semaine**.

- Quotidien : ouvrir le journal, poser une ligne par alerte nouvelle, verdict +
  motif en une phrase. Si le verdict n'est pas clair → `indeterminee`, pas
  « on verra ».
- Hebdomadaire : remplir le récapitulatif (voir
  [`journal-faux-positifs.md`](journal-faux-positifs.md)), relire les
  `indeterminee`, ouvrir une tâche si deux de suite sur la même règle.

Si le protocole demande plus que ce budget, il ne sera pas tenu — donc il est
mauvais.

## 4. Comment on compte

- **Semaine calendaire** : lundi → dimanche.
- **Une ligne par alerte** dans le journal.
- Un **compteur d'agrégation** (fenêtre 15 min, anti-rafale, etc.) compte pour
  **une** alerte, pas pour le nombre d'occurrences sous-jacentes.
- Seules les lignes au verdict `non pertinente` alimentent le seuil de sortie.
  Les `indeterminee` ont leur colonne et n'y entrent pas.

## 5. Critère de sortie

Recopié depuis [`P01`](../plans/P01-mise-en-service.md) (phase 1) :

> moins de 3 alertes non pertinentes par semaine, **deux semaines de suite**,
> sur une période couvrant au moins un déploiement complet et une sauvegarde
> offsite.

Durée de référence `D5` : **14 jours**. Une période calme parce qu'il ne s'est
rien passé ne prouve rien — couverture déploiement + sauvegarde offsite
obligatoire.

Le suivi se tient à la main dans
[`journal-faux-positifs.md`](journal-faux-positifs.md). Pas de script de
comptage dans ce lot.

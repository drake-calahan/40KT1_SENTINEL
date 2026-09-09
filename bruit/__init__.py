"""`bruit` — le moteur de bruit : ce qui décide **qu'une alerte parte, ou non**.

Séparé de `responder` délibérément. `ADR-002` trace une frontière entre *alerter*
et *répondre* ; les mélanger dans un même paquet la ferait disparaître à la
première refactorisation. Ici on ne joue aucun geste : on décide si un fait mérite
de réveiller quelqu'un.

── Le problème que ce paquet existe pour résoudre ──────────────────────────
`patator-standby` a perdu son IPv4 **quatre fois en trois semaines** (28/08,
30/08, 05/09, 06/09), cause NetworkManager. Chaque épisode produit une perte de
contact avec l'agent : légitime à voir, mais ce n'est **pas** un incident de
sécurité, et une sonde qui vérifie toutes les minutes en produirait des centaines.

Le plan `P01` dit que cette règle s'écrit **avant le premier week-end bruyant**,
pas après. C'est ce paquet.

── Les trois idées, et elles tiennent ensemble ─────────────────────────────
1. **On alerte à la TRANSITION**, pas à l'état (`F3`). Un nœud injoignable depuis
   six heures est *un* fait, pas trois cent soixante.
2. **On agrège sur une fenêtre**, et **le compteur EST l'information** (`F3`) :
   « 143 fois en 15 minutes » se lit ; 143 messages ne se lisent pas — ils
   apprennent à ignorer le canal, ce qui coûte l'alerte suivante.
3. **`inconnu` n'est pas `ko`**, et surtout pas `ok` (`RULES` § 1). Une sonde qui
   n'a pas pu mesurer ne dit pas que tout va bien, et ne dit pas non plus qu'il y
   a une panne. Le troisième état a ses propres transitions.

── Ce que ce paquet ne fait pas ────────────────────────────────────────────
Il n'envoie rien. Le câblage vers Discord et ntfy est le lot `P02.0`, et sa
première exigence est la **preuve d'arrivée sur le téléphone** — avant tout le
reste. Ce paquet produit des objets `Alerte` ; quelqu'un d'autre les portera.
"""

from bruit.etat import Etat
from bruit.fenetre import Alerte, Episode, Moteur

__all__ = ["Alerte", "Episode", "Etat", "Moteur"]

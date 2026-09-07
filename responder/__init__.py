"""`responder` — l'exécuteur de réponse de Sentinelle.

Le composant le plus sensible du dépôt : il décide si un geste privilégié a le
droit d'être joué sur une machine de production. Il reçoit un **ordre** du
serveur central, vérifie **quatre gardes** localement, agit — et journalise le
geste **comme le refus**.

Où la décision est prise (`ADR-002` § 3) : le serveur central corrèle et ordonne,
le nœud vérifie et exécute. Conséquence voulue : un serveur central compromis
peut faire du bruit, pas n'importe quoi.
"""

from responder.budget import Budget, EtatBudget
from responder.catalogue import CATALOGUE, Etat, Geste
from responder.config import Config
from responder.executeur import Decision, Executeur
from responder.gardes import ModeTournoi
from responder.journal import Journal
from responder.ordre import Ordre, OrdreInvalide

__all__ = [
    "CATALOGUE",
    "Budget",
    "Config",
    "Decision",
    "Etat",
    "EtatBudget",
    "Executeur",
    "Geste",
    "Journal",
    "ModeTournoi",
    "Ordre",
    "OrdreInvalide",
]

"""Le budget de remédiation — une garde à trois états, pas un compteur.

Trois gestes automatiques par heure glissante (`ADR-002` § 5, aligné sur
`ADR-062` de `40KT1_HQ`). Le motif est le mode d'échec classique de tout
automatisme : *une machine qui se répare quarante fois par heure ne se répare pas
— elle masque une panne, et elle la masque d'autant mieux que la réparation
marche.*

**Le dégel est un geste humain.** Une garde qui se relâche toute seule au bout
d'une heure ne garde rien : elle retarde.
"""

import os
from datetime import UTC, datetime
from enum import Enum

from responder.config import Config
from responder.journal import Journal


class EtatBudget(str, Enum):
    """Où en est l'heure glissante."""

    SOUS_BUDGET = "sous_budget"
    """Le geste passe."""

    DERNIER = "dernier_geste"
    """Le geste passe, et il déclenche un rouge : c'est le dernier de l'heure."""

    GELE = "gele"
    """Plus rien ne passe, jusqu'à intervention humaine. Alerte `critique`."""

    INCONNU = "inconnu"
    """Le compte n'a pas pu être établi. Ne rend jamais la main : refus, comme un gel."""


class Budget:
    """Lit l'heure glissante dans le journal, et le témoin de gel sur le disque."""

    def __init__(self, config: Config, journal: Journal) -> None:
        self._config = config
        self._journal = journal

    def est_gele(self) -> bool:
        """Vrai si le témoin de gel existe — ou si on n'a pas pu le vérifier.

        Ne pas pouvoir lire le témoin n'autorise rien : c'est la même règle que
        partout ici, une mesure qu'on n'a pas pu prendre ne rend pas `ok`.
        """
        try:
            os.stat(self._config.fichier_gel)
        except FileNotFoundError:
            return False
        except OSError:
            return True
        return True

    def etat(self) -> EtatBudget:
        """Rend l'état du budget **sans effet de bord**. Geler est un geste explicite."""
        if self.est_gele():
            return EtatBudget.GELE
        compte = self._journal.gestes_dans_la_fenetre()
        if compte is None:
            return EtatBudget.INCONNU
        plafond = self._config.budget_par_heure
        if plafond <= 0:
            return EtatBudget.GELE
        if compte >= plafond:
            return EtatBudget.GELE
        if compte == plafond - 1:
            return EtatBudget.DERNIER
        return EtatBudget.SOUS_BUDGET

    def geler(self, motif: str) -> None:
        """Pose le témoin de gel. Son retrait est un geste humain, décrit par un runbook."""
        self._config.fichier_gel.parent.mkdir(parents=True, exist_ok=True)
        horodatage = datetime.now(UTC).isoformat()
        self._config.fichier_gel.write_text(
            f"{horodatage} — {motif}\n"
            "Le dégel est un geste humain : retirer ce fichier après avoir lu le journal.\n",
            encoding="utf-8",
        )

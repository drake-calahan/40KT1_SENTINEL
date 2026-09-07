"""Les gardes — lues dans l'ordre, et l'ordre fait partie de la décision.

1. **le témoin de désarmement** — s'il existe, rien ne s'exécute, et on ne
   cherche même pas à savoir si l'ordre était valide. C'est le chemin hors bande,
   celui qui ne demande que SSH ;
2. **le catalogue** — fermé et déclaratif. Un geste absent est refusé même si
   l'ordre est bien formé ;
3. **le budget** — trois gestes par heure glissante, gel au-delà ;
4. **le mode tournoi** — lu chez `40KT1_HQ`, il **restreint** le catalogue.

Deux lectures de fichier décident ici de ce qu'une machine a le droit de faire.
Toutes deux appliquent la même règle : **ce qu'on n'a pas pu lire est traité comme
l'état le plus restrictif.** Ne pas savoir si le frein est tiré, c'est considérer
qu'il l'est.
"""

import os
from enum import Enum
from pathlib import Path

from responder.catalogue import Etat, Geste, geste
from responder.config import Config
from responder.ordre import Ordre


class ModeTournoi(str, Enum):
    """Le mode tournoi appartient à HQ. Sentinelle le lit ; elle ne le pose ni ne le retire."""

    INACTIF = "nominal"
    ACTIF = "tournoi"
    INCONNU = "tournoi_inconnu"
    """Illisible ou emplacement introuvable — traité comme actif, jamais comme nominal."""

    @property
    def restreint(self) -> bool:
        """Vrai dès qu'on n'a pas la certitude d'être hors tournoi."""
        return self is not ModeTournoi.INACTIF


def _temoin_present(chemin: Path) -> bool | None:
    """Vrai / faux / `None` quand la question n'a pas de réponse fiable.

    `Path.exists()` ne convient pas : il rend `False` aussi bien pour « absent »
    que pour « je n'ai pas pu regarder ». Ici, la différence décide d'un geste
    privilégié.
    """
    try:
        os.stat(chemin)
    except FileNotFoundError:
        # Le témoin est absent — encore faut-il que son emplacement existe. Un
        # répertoire manquant signifie une installation incomplète, pas un état.
        return False if chemin.parent.is_dir() else None
    except OSError:
        return None
    return True


def desarme(config: Config) -> bool:
    """Le frein est-il tiré ? Un doute vaut un frein tiré."""
    presence = _temoin_present(config.fichier_desarmement)
    return presence is not False


def mode_tournoi(config: Config) -> ModeTournoi:
    """Lit le témoin de mode tournoi de HQ, sans jamais le poser ni le retirer."""
    presence = _temoin_present(config.fichier_mode_tournoi)
    if presence is None:
        return ModeTournoi.INCONNU
    return ModeTournoi.ACTIF if presence else ModeTournoi.INACTIF


def garde_catalogue(ordre: Ordre, config: Config) -> tuple[Geste | None, str | None]:
    """Rend le geste du catalogue, ou le motif de refus.

    Trois refus possibles, et le premier est celui d'`E6` : **aucune réponse
    automatique sur un poste d'administration**, quel que soit le geste demandé.
    """
    if config.role_noeud == "workstation":
        return None, "poste d'administration : alerte seulement (E6)"
    trouve = geste(ordre.geste)
    if trouve is None:
        return None, f"geste hors catalogue : « {ordre.geste} »"
    if trouve.nominal is Etat.JAMAIS:
        return trouve, "geste marqué « jamais » par ADR-002"
    if trouve.nominal is Etat.ALERTE:
        return trouve, "geste en alerte seulement : action proposée à l'humain"
    return trouve, None


def garde_tournoi(trouve: Geste, mode: ModeTournoi) -> str | None:
    """Le mode tournoi restreint le catalogue. Il ne l'élargit jamais."""
    if not mode.restreint:
        return None
    if trouve.tournoi is Etat.ARME:
        return None
    precision = " (état du témoin illisible : traité comme actif)"
    suffixe = precision if mode is ModeTournoi.INCONNU else ""
    return f"mode tournoi : geste visible pour l'équipe, alerte seulement{suffixe}"

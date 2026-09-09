"""Les quatre gestes armables du catalogue — lot `P03.6`.

Ce paquet **câble** ce que `catalogue.py` **déclare**. La séparation est le point :
le catalogue est la transcription d'`ADR-002` et se lit sans lire de code ; ici
vit ce qui touche réellement la machine.

── L'invariant que ce module fait tenir ────────────────────────────────────
Un geste ne peut être câblé que s'il est **armé au catalogue**. Câbler un geste
classé *alerte* le rendrait exécutable sans amender l'ADR — le catalogue cesserait
d'être fermé. `verifier_coherence()` le vérifie, et les tests l'appellent.

── Ce que câbler ne fait PAS ───────────────────────────────────────────────
Câbler n'arme rien. Les quatre gardes de l'exécuteur restent devant, dans l'ordre,
et `SENTINEL_RESPONSE_ENABLED` reste `false` dans le dépôt. Un geste câblé sur un
nœud désarmé se journalise `aurait_execute` — ce qui est l'état de la phase, et
non un succès silencieux.
"""

from collections.abc import Callable

from responder.catalogue import CATALOGUE, Etat
from responder.config import Config
from responder.gestes import arreter_conteneur, arreter_processus, bloquer_ip, quarantaine_fichier
from responder.gestes.base import CibleRefusee, GesteEchoue
from responder.ordre import Ordre

__all__ = [
    "CibleRefusee",
    "GesteEchoue",
    "gestes_du_noeud",
    "verifier_coherence",
]

JoueurDeGeste = Callable[[Ordre, Config], str]
"""Un geste câblé : il joue, et il rend la description de son retour arrière."""


def _bloquer_ip(ordre: Ordre, _config: Config) -> str:
    return bloquer_ip.jouer(ordre.cible)


def _arreter_processus(ordre: Ordre, _config: Config) -> str:
    return arreter_processus.jouer(ordre.cible)


def _arreter_conteneur(ordre: Ordre, _config: Config) -> str:
    return arreter_conteneur.jouer(ordre.cible)


def _quarantaine_fichier(ordre: Ordre, config: Config) -> str:
    return quarantaine_fichier.jouer(
        ordre.cible,
        racine_etat=config.repertoire_etat,
        racines_hq=quarantaine_fichier.racines_hq_par_defaut(),
    )


JOUEURS: dict[str, JoueurDeGeste] = {
    "bloquer_ip": _bloquer_ip,
    "arreter_processus": _arreter_processus,
    "arreter_conteneur": _arreter_conteneur,
    "quarantaine_fichier": _quarantaine_fichier,
}


def verifier_coherence() -> list[str]:
    """Rend les incohérences entre ce qui est câblé et ce que le catalogue autorise.

    Vide = cohérent. Deux sens, et les deux comptent :

    1. **un geste câblé mais non armé au catalogue** — c'est la faute grave :
       il deviendrait exécutable sans amendement d'`ADR-002` ;
    2. **un geste armé au catalogue mais non câblé** — pas une faute en soi
       (l'exécuteur le journalise `aurait_execute`), mais un écart à connaître :
       `ADR-002` a décidé quatre gestes armés, et si le compte ne tombe pas, l'un
       des deux fichiers a bougé sans l'autre.
    """
    fautes: list[str] = []
    for nom in JOUEURS:
        entree = CATALOGUE.get(nom)
        if entree is None:
            fautes.append(f"{nom} : câblé mais absent du catalogue")
        elif entree.nominal is not Etat.ARME:
            fautes.append(
                f"{nom} : câblé alors que le catalogue le classe « {entree.nominal.value} ». "
                "Câbler un geste non armé le rend exécutable sans amender ADR-002."
            )
    for nom, entree in CATALOGUE.items():
        if entree.nominal is Etat.ARME and nom not in JOUEURS:
            fautes.append(f"{nom} : armé au catalogue mais non câblé")
    return fautes


def gestes_du_noeud(config: Config) -> dict[str, Callable[[Ordre], str | None]]:
    """Rend les gestes câblés de ce nœud, prêts pour l'exécuteur.

    **Un poste d'administration ne répond jamais** (`E6`) : le dictionnaire est
    vide, et l'exécuteur journalise alors `aurait_execute` avec « geste non câblé
    sur ce nœud ». C'est refusé par construction, pas par configuration — une
    configuration se change par une faute de frappe.
    """
    if config.role_noeud == "workstation":
        return {}

    def _lier(joueur: JoueurDeGeste) -> Callable[[Ordre], str | None]:
        def _jouer(ordre: Ordre) -> str | None:
            # Le retour arrière remonte tel quel jusqu'au journal : c'est ce que
            # l'exploitant copie-colle à 3 h du matin.
            return joueur(ordre, config)

        return _jouer

    return {nom: _lier(joueur) for nom, joueur in JOUEURS.items()}

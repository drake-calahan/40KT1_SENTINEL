"""Catalogue de réponse — fermé, déclaratif, et le seul endroit où un geste existe.

Un geste absent de ce fichier est refusé, même si l'ordre est bien formé et même
s'il est manifestement utile. L'élargir se fait par **amendement d'`ADR-002`**,
jamais par un ajout ici : le tableau ci-dessous est la transcription de la
décision, pas une configuration.

La colonne qui décide n'est pas « est-ce utile » mais « que faut-il faire pour le
défaire » — c'est le critère d'`ADR-062` de `40KT1_HQ`, repris mot pour mot :
*une automatisation n'a le droit de faire que ce qu'un humain peut défaire sans
arbitrage.*
"""

from dataclasses import dataclass
from enum import Enum


class Etat(str, Enum):
    """Ce qu'un geste a le droit de faire dans un mode donné."""

    ARME = "arme"
    """Il s'exécute, sous réserve des autres gardes."""

    ALERTE = "alerte"
    """Il ne s'exécute pas : il part en alerte, avec l'action proposée à l'humain."""

    JAMAIS = "jamais"
    """Il ne s'exécute dans aucune circonstance. Ni ici, ni par une option."""


@dataclass(frozen=True)
class Geste:
    """Une entrée du catalogue.

    `invisible` dit si le geste est invisible **pour l'équipe en salle** : il ne
    modifie ni le service rendu, ni la session en cours d'un joueur ou d'un
    arbitre. C'est le critère du mode tournoi (`ADR-002` § 4), et le doute
    tranche vers *visible* : un samedi de ronde, se tromper coûte une panne pour
    vingt personnes.
    """

    nom: str
    retour_arriere: str
    nominal: Etat
    tournoi: Etat
    invisible: bool


CATALOGUE: dict[str, Geste] = {
    "bloquer_ip": Geste(
        nom="bloquer_ip",
        retour_arriere="expiration automatique à 1 h dans la chaîne dédiée",
        nominal=Etat.ARME,
        tournoi=Etat.ARME,
        invisible=True,
    ),
    "arreter_processus": Geste(
        nom="arreter_processus",
        retour_arriere="il se relance, ou on le relance",
        nominal=Etat.ARME,
        tournoi=Etat.ARME,
        invisible=True,
    ),
    "arreter_conteneur": Geste(
        nom="arreter_conteneur",
        retour_arriere="`docker start` — une commande",
        nominal=Etat.ARME,
        # Visible immédiatement : un conteneur de la stack sert la salle.
        tournoi=Etat.ALERTE,
        invisible=False,
    ),
    "quarantaine_fichier": Geste(
        nom="quarantaine_fichier",
        retour_arriere="déplacement inverse, empreinte conservée",
        nominal=Etat.ARME,
        tournoi=Etat.ARME,
        invisible=True,
    ),
    "desactiver_compte": Geste(
        nom="desactiver_compte",
        retour_arriere="réactivation simple, mais coupe l'accès de secours",
        nominal=Etat.ALERTE,
        tournoi=Etat.ALERTE,
        invisible=False,
    ),
    "revoquer_sessions": Geste(
        nom="revoquer_sessions",
        retour_arriere="reconnexion Discord de tous les utilisateurs",
        nominal=Etat.ALERTE,
        tournoi=Etat.ALERTE,
        invisible=False,
    ),
    "couper_connecteur": Geste(
        nom="couper_connecteur",
        retour_arriere="une commande — mais le site est hors ligne entre-temps",
        nominal=Etat.ALERTE,
        tournoi=Etat.JAMAIS,
        invisible=False,
    ),
    "app_lecture_seule": Geste(
        nom="app_lecture_seule",
        retour_arriere="réversible, saisies perdues entre-temps",
        nominal=Etat.ALERTE,
        tournoi=Etat.ALERTE,
        invisible=False,
    ),
    "isoler_noeud": Geste(
        nom="isoler_noeud",
        retour_arriere="réversible si le tailnet tient — sinon 70 km en voiture",
        nominal=Etat.JAMAIS,
        tournoi=Etat.JAMAIS,
        invisible=False,
    ),
}


def geste(nom: str) -> Geste | None:
    """Rend le geste du catalogue, ou `None`. Ne lève pas : un nom inconnu est un refus."""
    return CATALOGUE.get(nom)


def incoherences() -> list[str]:
    """Rend la liste des incohérences du catalogue. Vide = catalogue sain.

    Deux invariants, tous deux tirés d'`ADR-002` :

    1. un geste armé en mode tournoi est **invisible** pour l'équipe en salle ;
    2. un geste `jamais` en nominal ne peut pas être plus permissif en tournoi —
       le mode tournoi restreint, il n'élargit pas.

    La fonction existe pour être appelée par les tests : une table écrite à la
    main finit par contredire l'ADR qu'elle transcrit, et c'est le genre d'écart
    qu'on ne voit pas en relecture.
    """
    fautes: list[str] = []
    for g in CATALOGUE.values():
        if g.tournoi is Etat.ARME and not g.invisible:
            fautes.append(f"{g.nom} : armé en tournoi mais visible pour l'équipe")
        if g.nominal is Etat.JAMAIS and g.tournoi is not Etat.JAMAIS:
            fautes.append(f"{g.nom} : « jamais » en nominal mais pas en tournoi")
        if g.nominal is Etat.ALERTE and g.tournoi is Etat.ARME:
            fautes.append(f"{g.nom} : le mode tournoi élargit au lieu de restreindre")
    return fautes

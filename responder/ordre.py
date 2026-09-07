"""L'ordre reçu du serveur central — et sa validation.

Le serveur central **corrèle et ordonne** ; le nœud **vérifie et exécute**
(`ADR-002` § 3). Un ordre est donc une donnée reçue du réseau, et il est traité
comme telle : jamais une commande, jamais une chaîne interpolée dans un shell.

Un ordre ne porte que **le nom d'un geste du catalogue** et une cible. Le nœud
résout le geste localement. Conséquence voulue : un serveur central compromis
peut faire du bruit, pas n'importe quoi.
"""

import re
from dataclasses import dataclass

# Jeu de caractères délibérément étroit : lettres, chiffres, et la ponctuation
# qui apparaît dans une adresse IP, un nom de conteneur, un PID ou un chemin.
# Tout le reste — espace, guillemet, `$`, `;`, `|`, `&`, retour à la ligne — est
# refusé à l'entrée plutôt qu'échappé plus loin. On ne construit pas de commande
# depuis une chaîne reçue du réseau ; on refuse d'en accepter une qui y
# ressemblerait.
_CIBLE_AUTORISEE = re.compile(r"^[A-Za-z0-9_.:/@-]{1,255}$")


class OrdreInvalide(ValueError):
    """L'ordre est mal formé. Il est refusé et journalisé, comme tout refus."""


@dataclass(frozen=True)
class Ordre:
    """Ce que le serveur central a le droit de demander."""

    geste: str
    cible: str
    regle: str
    """Identifiant de la règle de détection qui a déclenché — pour le journal."""

    @staticmethod
    def depuis_dict(brut: dict[str, object]) -> "Ordre":
        """Valide et construit un ordre. Lève `OrdreInvalide` plutôt que de deviner."""
        manquants = [c for c in ("geste", "cible", "regle") if not brut.get(c)]
        if manquants:
            raise OrdreInvalide(f"champs manquants : {', '.join(manquants)}")

        valeurs = {c: brut[c] for c in ("geste", "cible", "regle")}
        for champ, valeur in valeurs.items():
            if not isinstance(valeur, str):
                raise OrdreInvalide(f"champ « {champ} » : chaîne attendue")

        geste = str(valeurs["geste"]).strip()
        cible = str(valeurs["cible"]).strip()
        regle = str(valeurs["regle"]).strip()

        if not _CIBLE_AUTORISEE.match(cible):
            raise OrdreInvalide("cible : caractère hors du jeu autorisé")
        if not _CIBLE_AUTORISEE.match(geste):
            raise OrdreInvalide("geste : caractère hors du jeu autorisé")

        return Ordre(geste=geste, cible=cible, regle=regle)

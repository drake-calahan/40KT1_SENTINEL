"""Les trois états d'une observation, et la sévérité qui va avec.

`RULES` § 1 : *un `ok` n'est pas un `inconnu`.* Ce module rend la règle
structurelle plutôt que morale : il n'existe pas de valeur booléenne dans ce
paquet, donc il n'existe aucun endroit où l'on puisse écrire « pas ko, donc ok ».
"""

from enum import Enum


class Etat(str, Enum):
    """Ce qu'une sonde a constaté. Trois valeurs, jamais deux."""

    OK = "ok"
    """Mesuré, et conforme."""

    KO = "ko"
    """Mesuré, et non conforme. C'est un fait, pas une supposition."""

    INCONNU = "inconnu"
    """**Pas mesuré.** Ni conforme, ni non conforme : non su.

    Le cas qui a coûté deux incidents dans `40KT1_HQ` : un contrôle qui réussit
    sans avoir regardé. Ici il ne peut pas se confondre avec `OK`, parce qu'il
    porte une valeur distincte que le code doit traiter explicitement.
    """

    @property
    def merite_alerte(self) -> bool:
        """`KO` et `INCONNU` méritent d'être vus. `OK` ne réveille personne.

        `INCONNU` alerte parce que ne pas savoir est une information : c'est
        souvent le premier symptôme, et c'est toujours une dette de mesure.
        """
        return self is not Etat.OK


# La grille de sévérité est calquée sur `watchdog.py` de `40KT1_HQ` (`F2`), plus
# la sévérité `critique` et ses trois cas. Elle vit ici sous une forme minimale —
# ce dont le moteur de bruit a besoin pour ordonner. La grille complète, avec la
# correspondance règle ↔ niveau, est le lot `P02.1` (`cursor`) : ce module ne la
# préempte pas, il expose le socle sur lequel elle se posera.
SEVERITES: tuple[str, ...] = ("info", "orange", "rouge", "critique")


def rang(severite: str) -> int:
    """Rend le rang d'une sévérité. Une sévérité inconnue est traitée comme la PLUS haute.

    Le sens de l'erreur est choisi : une sévérité qu'on ne sait pas classer ne
    doit pas se retrouver silencieusement en bas de la pile. Mieux vaut réveiller
    quelqu'un pour rien qu'apprendre trop tard qu'une catégorie n'était pas
    reconnue — et le bruit qui en résulte se corrige, tandis que le silence ne se
    remarque pas.
    """
    try:
        return SEVERITES.index(severite)
    except ValueError:
        return len(SEVERITES) - 1

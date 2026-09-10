"""Configuration de l'exécuteur, lue depuis l'environnement du nœud.

Aucune valeur sensible n'est écrite ici : les noms viennent de `.env.example`,
les valeurs vivent dans le `.env` de la machine, qui n'est jamais committé.

**La règle de lecture, et c'est une règle de sécurité** : une valeur absente,
vide ou incompréhensible ne devient jamais l'état permissif.
`SENTINEL_RESPONSE_ENABLED` n'est vrai que s'il dit clairement oui (`_VRAI` :
`true`, `1`, `oui`, `yes`, casse et espaces indifférents) ;
`SENTINEL_RESPONSE_DRY_RUN` n'est faux que s'il dit clairement non (`_FAUX` :
`false`, `0`, `non`, `no`). Une faute de frappe désarme, elle n'arme pas.
"""

import os
from dataclasses import dataclass
from pathlib import Path

_VRAI = {"true", "1", "oui", "yes"}
_FAUX = {"false", "0", "non", "no"}


def _arme(valeur: str | None) -> bool:
    """Vrai seulement si la valeur dit clairement oui. Tout le reste désarme."""
    return valeur is not None and valeur.strip().lower() in _VRAI


def _a_blanc(valeur: str | None) -> bool:
    """Faux seulement si la valeur dit clairement non. Tout le reste reste à blanc."""
    return not (valeur is not None and valeur.strip().lower() in _FAUX)


def _entier(valeur: str | None, defaut: int) -> int:
    """Rend l'entier lu, ou le défaut. Une valeur illisible ne desserre jamais la garde."""
    if valeur is None:
        return defaut
    try:
        lu = int(valeur.strip())
    except ValueError:
        return defaut
    return lu if lu >= 0 else defaut


@dataclass(frozen=True)
class Config:
    """Ce dont l'exécuteur a besoin pour décider. Rien de plus."""

    role_noeud: str
    """`primary` · `secondary` · `workstation`. Un poste ne répond jamais (`E6`)."""

    repertoire_etat: Path
    fichier_desarmement: Path
    fichier_mode_tournoi: Path
    journal: Path

    reponse_armee: bool
    mode_a_blanc: bool
    budget_par_heure: int

    @staticmethod
    def depuis_environnement(env: dict[str, str] | None = None) -> "Config":
        """Construit la configuration depuis l'environnement, sans jamais deviner."""
        e = dict(os.environ if env is None else env)
        etat = Path(e.get("SENTINEL_STATE_DIR", "/var/lib/sentinel"))
        desarmement = e.get("SENTINEL_DISARM_FILE", "")
        return Config(
            role_noeud=e.get("SENTINEL_NODE_ROLE", "").strip().lower() or "inconnu",
            repertoire_etat=etat,
            # Un chemin relatif est résolu sous le répertoire d'état : le témoin de
            # désarmement doit rester posable par un humain, depuis SSH, sans chercher.
            fichier_desarmement=(
                Path(desarmement)
                if Path(desarmement).is_absolute()
                else etat / (desarmement or "response-disarmed")
            ),
            fichier_mode_tournoi=Path(
                e.get("SENTINEL_TOURNAMENT_MODE_FILE", "/srv/40kt1/node-state/tournament-mode")
            ),
            journal=Path(e.get("SENTINEL_RESPONSE_LOG", str(etat / "reponse.jsonl"))),
            reponse_armee=_arme(e.get("SENTINEL_RESPONSE_ENABLED")),
            mode_a_blanc=_a_blanc(e.get("SENTINEL_RESPONSE_DRY_RUN")),
            budget_par_heure=_entier(e.get("SENTINEL_RESPONSE_BUDGET_PER_HOUR"), 3),
        )

    @property
    def fichier_gel(self) -> Path:
        """Témoin de gel du budget. Son retrait est un geste humain, décrit par un runbook."""
        return self.repertoire_etat / "budget-gele"

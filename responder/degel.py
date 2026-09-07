"""Le dégel du budget — un geste humain, tracé.

`ADR-002` § 5 : *le dégel est un geste humain, jamais l'expiration d'un
compteur*. Il passe par ici plutôt que par un `rm` à la main, pour une raison
simple : **le journal doit porter qui a dégelé, quand, et pourquoi.** Un budget
qui se rouvre sans trace se rouvrira sans qu'on s'en aperçoive.

Retirer le témoin à la main fonctionne aussi — mais le compte de l'heure
glissante, lui, reste. Seule l'entrée `degel` du journal remet le compteur à
zéro. C'est volontaire : le geste qui compte est celui qu'on peut relire.

    python -m responder.degel "faux positif sur la regle 100142, corrige"
"""

import getpass
import sys
from datetime import UTC, datetime

from responder.config import Config
from responder.journal import Journal


def degeler(config: Config, motif: str, par: str) -> dict[str, object]:
    """Retire le témoin de gel et écrit l'entrée `degel` dans le journal."""
    config.fichier_gel.unlink(missing_ok=True)
    journal = Journal(config.journal)
    return journal.ecrire(
        {
            "horodatage": datetime.now(UTC).isoformat(),
            "noeud": config.role_noeud,
            "geste": "-",
            "cible": "-",
            "regle": "-",
            "mode": "nominal",
            "armement": "arme" if config.reponse_armee else "desarme",
            "a_blanc": config.mode_a_blanc,
            "resultat": "degel",
            "motif": f"dégel par {par} : {motif}",
            "severite": "rouge",
        }
    )


def main(argv: list[str] | None = None) -> int:
    """Point d'entrée du runbook. Un motif est **obligatoire** : sans lui, pas de dégel."""
    args = sys.argv[1:] if argv is None else argv
    motif = " ".join(args).strip()
    if not motif:
        sys.stderr.write(
            "Motif obligatoire. Un dégel sans motif est un dégel qu'on ne saura pas relire.\n"
            'Usage : python -m responder.degel "ce qui a été compris et corrigé"\n'
        )
        return 2
    config = Config.depuis_environnement()
    entree = degeler(config, motif, par=getpass.getuser())
    sys.stdout.write(f"Budget dégelé — {entree['horodatage']}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

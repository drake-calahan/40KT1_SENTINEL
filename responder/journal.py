"""Le journal — il porte les gestes **et les refus**.

Au matin, on doit pouvoir lire ce que la machine a fait sans nous — et ce qu'elle
n'a pas fait. Une réponse invisible est une dérive qui a l'air d'un miracle.

Le journal est aussi la **source du budget** : le compte des gestes de l'heure
glissante s'y lit, plutôt que dans un compteur en mémoire qu'un redémarrage
remettrait à zéro. Un budget qui s'oublie au redémarrage n'est pas un budget.
"""

import json
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path

RESULTATS_CONSOMMATEURS = frozenset({"execute", "aurait_execute", "echoue"})
"""Ce qui consomme le budget.

Le mode à blanc consomme comme le mode armé, et c'est délibéré : la période à
blanc doit montrer si le dispositif **aurait** gelé. Un mode à blanc qui ne
compte pas ne prouve rien sur le budget — et le budget est précisément ce qu'on
veut avoir éprouvé avant d'armer.
"""


class Journal:
    """Fichier JSONL, une décision par ligne, ajout seul."""

    def __init__(self, chemin: Path) -> None:
        self.chemin = chemin

    def ecrire(self, entree: dict[str, object]) -> dict[str, object]:
        """Écrit une décision et la rend. Ne masque aucune erreur d'écriture.

        Un journal qui échoue en silence transformerait un geste tracé en geste
        invisible. Si l'écriture est impossible, l'appelant doit le savoir.
        """
        self.chemin.parent.mkdir(parents=True, exist_ok=True)
        ligne = json.dumps(entree, ensure_ascii=False, sort_keys=True)
        with self.chemin.open("a", encoding="utf-8") as f:
            f.write(ligne + "\n")
        # Le journal décrit l'infrastructure : chemins, comptes, horaires.
        # Il se lit comme une donnée sensible, y compris par ses permissions.
        os.chmod(self.chemin, 0o600)
        return entree

    def gestes_dans_la_fenetre(self, secondes: int = 3600) -> int | None:
        """Compte les gestes consommateurs de la fenêtre glissante.

        Rend **`None` quand le compte n'a pas pu être établi** — journal illisible,
        ligne corrompue, horodatage absent. `None` n'est pas `0` : une mesure qu'on
        n'a pas pu prendre ne rend jamais un résultat permissif. Deux incidents de
        `40KT1_HQ` sont venus d'un contrôle qui réussissait sans avoir regardé.
        """
        if not self.chemin.exists():
            return 0
        limite = datetime.now(UTC) - timedelta(seconds=secondes)
        compte = 0
        try:
            contenu = self.chemin.read_text(encoding="utf-8")
        except OSError:
            return None
        for ligne in contenu.splitlines():
            if not ligne.strip():
                continue
            try:
                entree = json.loads(ligne)
                horodatage = datetime.fromisoformat(str(entree["horodatage"]))
                resultat = str(entree["resultat"])
            except (ValueError, KeyError, TypeError):
                # Une ligne illisible pourrait être le geste qui manque au compte.
                return None
            if horodatage.tzinfo is None:
                return None
            if horodatage < limite:
                continue
            if resultat == "degel":
                # Un dégel humain remet le compteur à zéro — et il est tracé,
                # ce qu'un `rm` du témoin ne serait pas. Voir `responder/degel.py`.
                compte = 0
            elif resultat in RESULTATS_CONSOMMATEURS:
                compte += 1
        return compte

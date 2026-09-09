"""Le relais — le mécanisme de réponse active du moteur sert de **transport**.

`E7` et `ADR-002` § 3 : *le serveur central corrèle et ordonne ; le nœud vérifie
et exécute.* Ce module est la couture entre les deux, et son unique vertu est
d'être **mince**.

    python -m responder.relais        # l'ordre arrive sur l'entrée standard

── Ce que le relais fait ───────────────────────────────────────────────────
Il lit l'enveloppe envoyée par le moteur, en **extrait** trois champs — le geste,
la cible, la règle — et les passe à l'exécuteur. Puis il écrit le résultat sur la
sortie d'erreur, où le journal du moteur le ramassera.

── Ce que le relais ne fait PAS, et c'est le point ─────────────────────────
**Il ne décide rien.** Il ne consulte pas le catalogue, ne lit pas le budget, ne
regarde pas le mode tournoi, ne connaît pas le témoin de désarmement. Les quatre
gardes vivent dans l'exécuteur, en un seul endroit, et ce module ne les
contourne pas plus qu'il ne les double.

La raison est une propriété de sécurité, pas un goût d'architecture : le relais
est la surface exposée au serveur central. S'il décidait quoi que ce soit, un
serveur central compromis déciderait avec lui. Comme il n'est qu'un traducteur,
un serveur compromis peut au mieux **demander** — et se faire refuser localement.

**Il n'infère pas non plus le geste depuis la règle.** Le geste est ordonné, ou
il n'y a pas d'ordre. Un relais qui traduirait « règle 100142 » en « bloquer_ip »
prendrait la décision que le catalogue est censé porter, et le ferait dans le
fichier le moins relu du dépôt.

── L'enveloppe, et ce qu'on en sait ────────────────────────────────────────
La forme exacte de l'enveloppe dépend de la version du moteur. Le relais lit donc
un **sous-ensemble documenté** et **refuse tout ce qu'il ne comprend pas** :
mieux vaut un refus tracé qu'un geste joué sur une lecture approximative. Un
`inconnu` n'est pas un `ok` (`RULES` § 1).

⚠️ **À confirmer contre la version réellement installée avant tout armement** —
lot `P03.9`. Tant que ce n'est pas fait, ce module se teste, il ne s'arme pas.
"""

import json
import sys
from typing import Any

from responder.config import Config
from responder.executeur import Decision, Executeur
from responder.gestes import gestes_du_noeud

CODE_OK = 0
"""Le relais a fait son travail — que l'exécuteur ait agi, refusé ou échoué.

Refuser **est** un fonctionnement nominal : ce n'est pas une panne du relais, et
la faire remonter comme telle apprendrait au moteur à considérer les refus comme
des incidents de transport. Le résultat réel est dans le journal de l'exécuteur.
"""

CODE_ENVELOPPE_ILLISIBLE = 2
"""L'enveloppe n'a pas pu être lue. Rien n'a été transmis à l'exécuteur."""


class EnveloppeInvalide(ValueError):
    """L'enveloppe reçue n'est pas exploitable. Refus, jamais interprétation."""


def _chaine(valeur: Any, champ: str) -> str:
    if not isinstance(valeur, str) or not valeur.strip():
        raise EnveloppeInvalide(f"champ « {champ} » : chaîne non vide attendue")
    return valeur.strip()


def extraire(enveloppe: dict[str, Any]) -> dict[str, object]:
    """Extrait l'ordre de l'enveloppe. **Extraire, pas interpréter.**

    Les trois champs sont lus là où le moteur les place, et nulle part ailleurs.
    Aucune valeur par défaut : un champ absent est un refus, pas une occasion de
    deviner. Deviner ici reviendrait à fabriquer un ordre que personne n'a donné.
    """
    if not isinstance(enveloppe, dict):
        raise EnveloppeInvalide("enveloppe : objet JSON attendu")

    commande = enveloppe.get("command")
    if commande is not None and _chaine(commande, "command") not in {"add", "run"}:
        # `delete` est l'annulation d'une réponse active par le moteur. Nos gestes
        # portent leur propre retour arrière (expiration, manifeste, commande
        # rendue) : laisser le moteur « annuler » créerait un second chemin de
        # défaisance, non tracé par notre journal. On refuse, et on le dit.
        raise EnveloppeInvalide(
            f"commande « {commande} » non prise en charge. Le retour arrière de nos "
            "gestes est porté par le geste lui-même et tracé au journal ; une "
            "annulation par le moteur serait un second chemin, invisible du journal."
        )

    parametres = enveloppe.get("parameters")
    if not isinstance(parametres, dict):
        raise EnveloppeInvalide("champ « parameters » : objet attendu")

    alerte = parametres.get("alert")
    if not isinstance(alerte, dict):
        raise EnveloppeInvalide("champ « parameters.alert » : objet attendu")

    # Le geste et la cible sont ORDONNÉS, dans les arguments passés par le
    # serveur central. Ils ne se déduisent pas de l'alerte : déduire, ce serait
    # décider (voir l'en-tête du module).
    arguments = parametres.get("extra_args")
    if not isinstance(arguments, list) or len(arguments) < 2:
        raise EnveloppeInvalide(
            "champ « parameters.extra_args » : deux valeurs attendues — le geste "
            "et la cible. Le geste est ORDONNÉ par le serveur central ; le relais "
            "ne le déduit pas de la règle."
        )

    regle = alerte.get("rule")
    identifiant = ""
    if isinstance(regle, dict):
        brut = regle.get("id")
        identifiant = str(brut).strip() if brut is not None else ""
    if not identifiant:
        raise EnveloppeInvalide(
            "identifiant de règle absent. Sans lui, l'entrée du journal ne dit pas "
            "CE QUI a déclenché le geste — et un journal qu'on ne peut pas relire "
            "ne sert pas au repassage hebdomadaire (D5)."
        )

    return {
        "geste": _chaine(arguments[0], "extra_args[0]"),
        "cible": _chaine(arguments[1], "extra_args[1]"),
        "regle": identifiant,
    }


def traiter_flux(texte: str, config: Config | None = None) -> tuple[int, str]:
    """Traite une enveloppe et rend `(code de sortie, message)`. Sans effet de bord d'affichage.

    Séparé de `main()` pour être testable sans toucher aux flux du processus :
    un composant privilégié dont on ne peut pas éprouver le chemin d'erreur n'est
    pas éprouvé.
    """
    try:
        enveloppe = json.loads(texte)
    except ValueError as erreur:
        return CODE_ENVELOPPE_ILLISIBLE, f"enveloppe illisible : {erreur}. Rien n'a été transmis."

    try:
        brut = extraire(enveloppe)
    except EnveloppeInvalide as erreur:
        return CODE_ENVELOPPE_ILLISIBLE, f"enveloppe refusée : {erreur}. Rien n'a été transmis."

    reglage = config if config is not None else Config.depuis_environnement()
    executeur = Executeur(reglage, gestes_cables=gestes_du_noeud(reglage))
    decision: Decision = executeur.traiter(brut)

    return CODE_OK, f"{decision.resultat} · {decision.motif}"


def main(argv: list[str] | None = None) -> int:
    """Point d'entrée. L'ordre arrive sur l'entrée standard, le compte rendu part sur stderr."""
    _ = argv
    code, message = traiter_flux(sys.stdin.read())
    # stderr et non stdout : le moteur lit stdout dans certains flux de réponse
    # active, et y écrire risquerait de se faire interpréter comme une réponse
    # au protocole. Le compte rendu est pour l'humain qui lira le journal.
    print(message, file=sys.stderr)
    return code


if __name__ == "__main__":
    raise SystemExit(main())

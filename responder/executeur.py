"""L'exécuteur — il décide, il journalise, et il n'agit que si les quatre gardes passent.

Ce module ne contient **aucun geste privilégié**, et n'en contiendra jamais : les
quatre gestes armables vivent dans `responder.gestes` (`P03.6`), derrière
l'interface `GesteCable` ci-dessous. Un nœud sur lequel aucun geste n'est câblé
journalise `aurait_execute` avec son motif — ce qui est un état, et non un succès
silencieux.

Câbler un geste **n'arme rien** : les quatre gardes restent devant, dans l'ordre,
et `SENTINEL_RESPONSE_ENABLED` reste `false` dans le dépôt.

**Le mode à blanc ne change qu'une seule chose : le geste n'est pas exécuté.**
Toutes les gardes, le budget compris, se comportent à l'identique. Un mode à
blanc plus permissif que le mode armé ne prouverait rien de ce qu'on veut avoir
éprouvé avant d'armer.
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime

from responder.budget import Budget, EtatBudget
from responder.config import Config
from responder.gardes import ModeTournoi, desarme, garde_catalogue, garde_tournoi, mode_tournoi
from responder.journal import Journal
from responder.ordre import Ordre, OrdreInvalide

GesteCable = Callable[[Ordre], str | None]
"""Signature d'un geste réellement exécutable — câblé par `responder.gestes` (`P03.6`).

Il rend la description de **son** retour arrière, avec ses valeurs réelles, ou
`None` pour retomber sur la phrase générique du catalogue. Il lève en cas
d'échec : l'exécuteur rattrape et journalise `echoue`.
"""


@dataclass(frozen=True)
class Decision:
    """Ce que l'exécuteur a décidé, et ce qu'il en a écrit."""

    resultat: str
    """`execute` · `aurait_execute` · `refuse`."""

    motif: str
    severite: str
    entree: dict[str, object] = field(default_factory=dict)

    @property
    def a_agi(self) -> bool:
        return self.resultat == "execute"

    @property
    def refuse(self) -> bool:
        return self.resultat == "refuse"


class Executeur:
    """Les quatre gardes, dans l'ordre, puis le journal — geste comme refus."""

    def __init__(
        self,
        config: Config,
        journal: Journal | None = None,
        gestes_cables: dict[str, GesteCable] | None = None,
    ) -> None:
        self.config = config
        self.journal = journal if journal is not None else Journal(config.journal)
        self.budget = Budget(config, self.journal)
        self.gestes_cables = gestes_cables or {}

    def traiter(self, brut: dict[str, object]) -> Decision:
        """Traite un ordre reçu du serveur central. Journalise toujours."""
        mode = ModeTournoi.INACTIF
        try:
            ordre = Ordre.depuis_dict(brut)
        except OrdreInvalide as erreur:
            return self._journaliser(
                geste=str(brut.get("geste", "?")),
                cible=str(brut.get("cible", "?")),
                regle=str(brut.get("regle", "?")),
                mode=mode,
                resultat="refuse",
                motif=f"ordre invalide : {erreur}",
                severite="orange",
            )

        # Garde 1 — le frein d'urgence, avant tout le reste, y compris avant de
        # savoir si le geste est valide. On ne discute pas un ordre quand le
        # frein est tiré : on s'arrête.
        if desarme(self.config):
            return self._journaliser_ordre(ordre, mode, "refuse", "désarmement d'urgence actif")

        # Garde 2 — le catalogue.
        trouve, refus = garde_catalogue(ordre, self.config)
        if refus is not None:
            return self._journaliser_ordre(ordre, mode, "refuse", refus)
        if trouve is None:
            # Inatteignable tant que `garde_catalogue` tient son contrat. On refuse
            # quand même plutôt que d'affirmer l'invariant : un `assert` disparaît
            # sous `python -O`, et ce qui garde un geste privilégié ne s'évapore pas.
            return self._journaliser_ordre(ordre, mode, "refuse", "geste introuvable")

        # Garde 3 — le budget. Le gel est une alerte `critique` (F2).
        etat_budget = self.budget.etat()
        if etat_budget is EtatBudget.GELE:
            return self._journaliser_ordre(
                ordre, mode, "refuse", "budget gelé : dégel humain requis", severite="critique"
            )
        if etat_budget is EtatBudget.INCONNU:
            return self._journaliser_ordre(
                ordre,
                mode,
                "refuse",
                "budget non mesurable : journal illisible — refus par défaut",
                severite="rouge",
            )

        # Garde 4 — le mode tournoi, lu chez HQ.
        mode = mode_tournoi(self.config)
        refus_tournoi = garde_tournoi(trouve, mode)
        if refus_tournoi is not None:
            return self._journaliser_ordre(ordre, mode, "refuse", refus_tournoi)

        severite = "rouge" if etat_budget is EtatBudget.DERNIER else "orange"
        empeche = self._ce_qui_empeche_d_agir(ordre)
        if empeche is not None:
            return self._journaliser_ordre(ordre, mode, "aurait_execute", empeche, severite)

        # Le geste est joué ICI, et son échec est un RÉSULTAT, pas une exception
        # qui remonte. Laisser l'erreur s'échapper laisserait l'ordre sans aucune
        # entrée au journal : ni geste, ni refus, ni trace. On croirait la menace
        # traitée, et le budget ne compterait pas la tentative — ce qui
        # autoriserait à la rejouer sans fin.
        try:
            retour_arriere = self.gestes_cables[ordre.geste](ordre)
        except Exception as erreur:
            decision = self._journaliser_ordre(
                ordre,
                mode,
                "echoue",
                f"{type(erreur).__name__} : {erreur}",
                severite="rouge",
            )
            # Une tentative qui a échoué a quand même consommé une tentative.
            if etat_budget is EtatBudget.DERNIER:
                self.budget.geler("dernier geste du budget horaire consommé (tentative en échec)")
            return decision

        # Le motif journalisé est le retour arrière RÉEL rendu par le geste — avec
        # ses valeurs, prêt à copier-coller — et non la phrase générique du
        # catalogue. À 3 h du matin, retrouver la commande soi-même est de
        # l'arbitrage, et `ADR-062` demande qu'on puisse défaire sans arbitrage.
        decision = self._journaliser_ordre(
            ordre, mode, "execute", retour_arriere or trouve.retour_arriere, severite
        )
        if etat_budget is EtatBudget.DERNIER:
            self.budget.geler("dernier geste du budget horaire consommé")
        return decision

    def _ce_qui_empeche_d_agir(self, ordre: Ordre) -> str | None:
        """Rend le motif pour lequel le geste ne sera pas joué, ou `None` s'il le sera."""
        if not self.config.reponse_armee:
            return "réponse désarmée : le geste est journalisé, pas joué"
        if self.config.mode_a_blanc:
            return "mode à blanc : le geste est journalisé, pas joué"
        if ordre.geste not in self.gestes_cables:
            return "geste non câblé sur ce nœud (P03.6) : rien n'a été joué"
        return None

    def _journaliser_ordre(
        self,
        ordre: Ordre,
        mode: ModeTournoi,
        resultat: str,
        motif: str,
        severite: str = "orange",
    ) -> Decision:
        return self._journaliser(
            geste=ordre.geste,
            cible=ordre.cible,
            regle=ordre.regle,
            mode=mode,
            resultat=resultat,
            motif=motif,
            severite=severite,
        )

    def _journaliser(
        self,
        *,
        geste: str,
        cible: str,
        regle: str,
        mode: ModeTournoi,
        resultat: str,
        motif: str,
        severite: str,
    ) -> Decision:
        entree: dict[str, object] = {
            "horodatage": datetime.now(UTC).isoformat(),
            "noeud": self.config.role_noeud,
            "geste": geste,
            "cible": cible,
            "regle": regle,
            "mode": mode.value,
            "armement": "arme" if self.config.reponse_armee else "desarme",
            "a_blanc": self.config.mode_a_blanc,
            "resultat": resultat,
            "motif": motif,
            "severite": severite,
        }
        self.journal.ecrire(entree)
        return Decision(resultat=resultat, motif=motif, severite=severite, entree=entree)

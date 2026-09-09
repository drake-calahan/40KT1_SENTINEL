"""Le moteur : transition, fenêtre d'agrégation, compteur.

    moteur = Moteur(fenetre=timedelta(minutes=15))
    alerte = moteur.observer("contact-agent", "patator-standby", Etat.KO, instant)

`observer` rend une `Alerte` **ou `None`**. `None` est le cas normal : la plupart
des observations ne méritent pas de réveiller quelqu'un, et c'est exactement ce
qu'on cherche à obtenir.

── Ce que le moteur garantit ───────────────────────────────────────────────
1. **Une transition, une alerte.** Un épisode qui dure six heures produit une
   alerte d'ouverture, d'éventuels rappels agrégés, et une alerte de retour à la
   normale. Pas trois cent soixante.
2. **Le compteur est l'information.** Un rappel dit « 143 observations depuis
   l'ouverture », pas « encore une ».
3. **`inconnu` a ses propres transitions.** Passer de `ko` à `inconnu` n'est pas
   un retour à la normale : c'est une perte de mesure, et elle se dit.
4. **Le retour à la normale s'annonce.** Sans lui, un exploitant réveillé à 3 h ne
   sait pas si c'est fini. Une alerte sans clôture se relit mal au repassage
   hebdomadaire (`D5`), et elle finit classée `indeterminee`.

── Ce qu'il ne fait pas ────────────────────────────────────────────────────
Il n'envoie rien, ne persiste rien, ne connaît ni Discord ni ntfy. Il est pur, et
c'est ce qui le rend éprouvable : ses tests avancent une horloge, pas une machine.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta

from bruit.etat import Etat, rang

FENETRE_PAR_DEFAUT = timedelta(minutes=15)
"""`F3` : agrégation par fenêtre de 15 minutes, avec compteur."""


@dataclass(frozen=True)
class Alerte:
    """Ce qui mérite d'être vu. Produit par le moteur, porté par quelqu'un d'autre."""

    sujet: str
    """Ce qui est observé — l'identifiant de règle ou de sonde."""

    source: str
    """Sur quoi — un nœud, un conteneur, un chemin."""

    etat: Etat
    severite: str
    genre: str
    """`ouverture` · `rappel` · `aggravation` · `retour_normal`."""

    occurrences: int
    """Nombre d'observations depuis l'ouverture de l'épisode. **Le compteur EST l'information.**"""

    depuis: datetime
    instant: datetime

    @property
    def duree(self) -> timedelta:
        return self.instant - self.depuis

    def resume(self) -> str:
        """Une ligne, lisible à 3 h du matin — le seul public qui compte."""
        if self.genre == "retour_normal":
            return (
                f"[{self.severite}] {self.sujet} · {self.source} : RETOUR À LA NORMALE "
                f"après {self._duree_lisible()} et {self.occurrences} observation(s)."
            )
        if self.genre == "ouverture":
            return f"[{self.severite}] {self.sujet} · {self.source} : {self.etat.value.upper()}."
        if self.genre == "aggravation":
            return (
                f"[{self.severite}] {self.sujet} · {self.source} : passe à "
                f"{self.etat.value.upper()} (était en cours depuis {self._duree_lisible()})."
            )
        return (
            f"[{self.severite}] {self.sujet} · {self.source} : toujours "
            f"{self.etat.value.upper()} — {self.occurrences} observations en "
            f"{self._duree_lisible()}."
        )

    def _duree_lisible(self) -> str:
        secondes = int(self.duree.total_seconds())
        if secondes < 60:
            return f"{secondes} s"
        if secondes < 3600:
            return f"{secondes // 60} min"
        return f"{secondes // 3600} h {(secondes % 3600) // 60:02d}"


@dataclass
class Episode:
    """Un état non nominal qui dure. Une perte de contact, ce n'est pas N alertes : c'est un épisode."""

    etat: Etat
    severite: str
    depuis: datetime
    occurrences: int = 1
    dernier_rappel: datetime = field(default=datetime.min)


class Moteur:
    """Décide si une observation mérite une alerte. Sans état persistant, sans horloge propre.

    L'instant est **passé en argument** plutôt que lu de l'horloge : un moteur qui
    lit l'heure lui-même ne se teste qu'en dormant, et un test qui dort ne teste
    pas grand-chose. Ici les tests avancent le temps à la main et couvrent en
    quelques millisecondes ce qu'un week-end produirait.
    """

    def __init__(self, fenetre: timedelta = FENETRE_PAR_DEFAUT) -> None:
        self.fenetre = fenetre
        self._episodes: dict[tuple[str, str], Episode] = {}

    def observer(
        self,
        sujet: str,
        source: str,
        etat: Etat,
        instant: datetime,
        severite: str = "orange",
    ) -> Alerte | None:
        """Enregistre une observation. Rend une `Alerte` si elle mérite d'être vue, sinon `None`."""
        cle = (sujet, source)
        episode = self._episodes.get(cle)

        # ── Retour à la normale ───────────────────────────────────────────
        if not etat.merite_alerte:
            if episode is None:
                # Nominal et rien en cours : le cas de très loin le plus fréquent.
                # Il ne produit rien, et c'est tout l'objet du moteur.
                return None
            del self._episodes[cle]
            return Alerte(
                sujet=sujet,
                source=source,
                etat=etat,
                severite=episode.severite,
                genre="retour_normal",
                occurrences=episode.occurrences,
                depuis=episode.depuis,
                instant=instant,
            )

        # ── Ouverture d'un épisode ────────────────────────────────────────
        if episode is None:
            self._episodes[cle] = Episode(
                etat=etat, severite=severite, depuis=instant, occurrences=1, dernier_rappel=instant
            )
            return Alerte(
                sujet=sujet,
                source=source,
                etat=etat,
                severite=severite,
                genre="ouverture",
                occurrences=1,
                depuis=instant,
                instant=instant,
            )

        episode.occurrences += 1

        # ── Aggravation ───────────────────────────────────────────────────
        # Un changement d'état DANS un épisode se dit tout de suite, sans
        # attendre la fenêtre : passer de `inconnu` à `ko`, c'est apprendre
        # quelque chose. Et passer de `ko` à `inconnu` aussi — on a perdu la
        # mesure, ce n'est pas une amélioration.
        aggrave = etat is not episode.etat or rang(severite) > rang(episode.severite)
        if aggrave:
            episode.etat = etat
            if rang(severite) > rang(episode.severite):
                episode.severite = severite
            episode.dernier_rappel = instant
            return Alerte(
                sujet=sujet,
                source=source,
                etat=etat,
                severite=episode.severite,
                genre="aggravation",
                occurrences=episode.occurrences,
                depuis=episode.depuis,
                instant=instant,
            )

        # ── Rappel agrégé, au plus une fois par fenêtre ───────────────────
        if instant - episode.dernier_rappel >= self.fenetre:
            episode.dernier_rappel = instant
            return Alerte(
                sujet=sujet,
                source=source,
                etat=etat,
                severite=episode.severite,
                genre="rappel",
                occurrences=episode.occurrences,
                depuis=episode.depuis,
                instant=instant,
            )

        # Rien à dire : l'épisode est connu, il n'a pas changé, et la fenêtre
        # n'est pas écoulée. C'est le silence que le moteur existe pour produire.
        return None

    def episodes_ouverts(self) -> dict[tuple[str, str], Episode]:
        """Les épisodes en cours — pour un bilan, jamais pour décider."""
        return dict(self._episodes)

"""Le moteur de bruit — éprouvé sur le cas qui l'a motivé.

Le test qui compte est `test_le_week_end_bruyant_de_patator_standby` : il rejoue
un épisode de six heures, sondé toutes les minutes, et vérifie qu'il produit une
poignée d'alertes au lieu de trois cent soixante. C'est le défaut réseau
récidivant du standby (quatre occurrences en trois semaines), et le plan `P01`
demande que la règle existe **avant** le premier week-end, pas après.
"""

from datetime import UTC, datetime, timedelta

import pytest

from bruit.etat import Etat, rang
from bruit.fenetre import Moteur

T0 = datetime(2026, 9, 12, 22, 0, tzinfo=UTC)
MINUTE = timedelta(minutes=1)


@pytest.fixture
def moteur() -> Moteur:
    return Moteur(fenetre=timedelta(minutes=15))


# ══════════════════════════════════════════════════════════════════════════
# Les trois états — et le fait qu'ils ne se confondent pas
# ══════════════════════════════════════════════════════════════════════════


def test_inconnu_n_est_pas_ok() -> None:
    """`RULES` § 1. Rendu structurel : il n'y a pas de booléen dans ce paquet."""
    assert Etat.INCONNU.merite_alerte
    assert Etat.KO.merite_alerte
    assert not Etat.OK.merite_alerte


def test_une_severite_inconnue_est_traitee_comme_la_plus_haute() -> None:
    """Le sens de l'erreur est choisi : le bruit se corrige, le silence ne se remarque pas."""
    assert rang("catastrophe") == rang("critique")
    assert rang("info") < rang("orange") < rang("rouge") < rang("critique")


# ══════════════════════════════════════════════════════════════════════════
# Le silence, qui est le produit principal du moteur
# ══════════════════════════════════════════════════════════════════════════


def test_le_nominal_ne_produit_rien(moteur: Moteur) -> None:
    """Le cas de très loin le plus fréquent. S'il parlait, plus rien ne se lirait."""
    for i in range(500):
        assert moteur.observer("contact-agent", "patator-tower", Etat.OK, T0 + i * MINUTE) is None


def test_un_episode_connu_et_stable_se_tait_dans_la_fenetre(moteur: Moteur) -> None:
    assert moteur.observer("contact-agent", "patator-standby", Etat.KO, T0) is not None
    for i in range(1, 15):
        assert moteur.observer("contact-agent", "patator-standby", Etat.KO, T0 + i * MINUTE) is None


# ══════════════════════════════════════════════════════════════════════════
# Le cas réel : le week-end bruyant de patator-standby
# ══════════════════════════════════════════════════════════════════════════


def test_le_week_end_bruyant_de_patator_standby(moteur: Moteur) -> None:
    """Six heures d'IPv4 perdue, sondée chaque minute. 360 observations.

    Sans agrégation : 360 messages, la nuit, sur le téléphone de la seule
    personne d'astreinte. Le lendemain, le canal est coupé — et c'est l'alerte
    SUIVANTE qui est perdue, celle qui comptait.
    """
    alertes = []
    for i in range(360):
        alerte = moteur.observer("contact-agent", "patator-standby", Etat.KO, T0 + i * MINUTE)
        if alerte is not None:
            alertes.append(alerte)

    # Puis le lien revient.
    retour = moteur.observer("contact-agent", "patator-standby", Etat.OK, T0 + 360 * MINUTE)
    assert retour is not None
    alertes.append(retour)

    # 1 ouverture + 23 rappels (un par quart d'heure) + 1 retour = 25, pas 360.
    assert len(alertes) == 25
    assert alertes[0].genre == "ouverture"
    assert alertes[-1].genre == "retour_normal"
    assert all(a.genre == "rappel" for a in alertes[1:-1])

    # Le compteur EST l'information : le dernier rappel dit combien, pas « encore une ».
    assert alertes[-2].occurrences > 300
    assert "observations en" in alertes[-2].resume()

    # Et le retour à la normale porte la durée : sans elle, l'exploitant réveillé
    # à 3 h ne sait pas si c'est fini.
    assert retour.occurrences == 360
    assert "RETOUR À LA NORMALE" in retour.resume()
    assert "6 h" in retour.resume()


def test_les_quatre_episodes_connus_font_quatre_ouvertures_pas_une_rafale(
    moteur: Moteur,
) -> None:
    """28/08, 30/08, 05/09, 06/09 — quatre épisodes distincts, séparés par du nominal.

    Chacun doit s'ouvrir et se refermer : agréger ne veut pas dire fondre quatre
    incidents en un seul, sinon on perdrait la récurrence — et la récurrence est
    précisément ce qui a fait ouvrir une tâche sur NetworkManager.
    """
    ouvertures = 0
    retours = 0
    instant = T0
    for _ in range(4):
        for _ in range(30):  # 30 min de panne
            alerte = moteur.observer("contact-agent", "patator-standby", Etat.KO, instant)
            if alerte is not None and alerte.genre == "ouverture":
                ouvertures += 1
            instant += MINUTE
        for _ in range(60):  # une heure de calme
            alerte = moteur.observer("contact-agent", "patator-standby", Etat.OK, instant)
            if alerte is not None and alerte.genre == "retour_normal":
                retours += 1
            instant += MINUTE

    assert ouvertures == 4
    assert retours == 4


# ══════════════════════════════════════════════════════════════════════════
# Les transitions qui ne sont pas des améliorations
# ══════════════════════════════════════════════════════════════════════════


def test_passer_de_ko_a_inconnu_n_est_pas_un_retour_a_la_normale(moteur: Moteur) -> None:
    """On a perdu la mesure. Ce n'est ni une amélioration, ni la fin de l'épisode."""
    moteur.observer("integrite", "patator-tower", Etat.KO, T0)
    alerte = moteur.observer("integrite", "patator-tower", Etat.INCONNU, T0 + MINUTE)
    assert alerte is not None
    assert alerte.genre == "aggravation"
    assert alerte.etat is Etat.INCONNU
    # L'épisode continue : il ne s'est pas refermé en silence.
    assert ("integrite", "patator-tower") in moteur.episodes_ouverts()


def test_une_aggravation_de_severite_parle_tout_de_suite(moteur: Moteur) -> None:
    """Attendre la fin de la fenêtre pour dire qu'on est passé en `critique` serait absurde."""
    moteur.observer("exfiltration", "patator-tower", Etat.KO, T0, severite="orange")
    alerte = moteur.observer(
        "exfiltration", "patator-tower", Etat.KO, T0 + MINUTE, severite="critique"
    )
    assert alerte is not None
    assert alerte.genre == "aggravation"
    assert alerte.severite == "critique"


def test_la_severite_ne_redescend_pas_toute_seule(moteur: Moteur) -> None:
    """Un épisode monté en `critique` ne se reclasse pas `orange` parce qu'une sonde a hésité.

    Il se referme, ou il reste `critique`. Laisser la sévérité redescendre
    permettrait à un épisode grave de finir en `info` sans que personne ne l'ait
    décidé.
    """
    moteur.observer("exfiltration", "patator-tower", Etat.KO, T0, severite="critique")
    moteur.observer("exfiltration", "patator-tower", Etat.KO, T0 + MINUTE, severite="orange")
    rappel = moteur.observer(
        "exfiltration", "patator-tower", Etat.KO, T0 + 20 * MINUTE, severite="orange"
    )
    assert rappel is not None
    assert rappel.severite == "critique"


def test_un_inconnu_isole_alerte_quand_meme(moteur: Moteur) -> None:
    """Ne pas savoir est une information — souvent le premier symptôme."""
    alerte = moteur.observer("conformite", "patator-standby", Etat.INCONNU, T0)
    assert alerte is not None
    assert alerte.etat is Etat.INCONNU


# ══════════════════════════════════════════════════════════════════════════
# Les sources ne se mélangent pas
# ══════════════════════════════════════════════════════════════════════════


def test_deux_noeuds_ont_deux_episodes_distincts(moteur: Moteur) -> None:
    """Agréger par fenêtre ne doit pas agréger entre machines : ce sont deux faits."""
    a = moteur.observer("contact-agent", "patator-tower", Etat.KO, T0)
    b = moteur.observer("contact-agent", "patator-standby", Etat.KO, T0)
    assert a is not None
    assert b is not None
    assert len(moteur.episodes_ouverts()) == 2


def test_deux_sujets_sur_le_meme_noeud_ne_se_masquent_pas(moteur: Moteur) -> None:
    """Une perte de contact ne doit pas faire taire une alerte d'intégrité."""
    moteur.observer("contact-agent", "patator-standby", Etat.KO, T0)
    autre = moteur.observer("integrite", "patator-standby", Etat.KO, T0 + MINUTE)
    assert autre is not None
    assert autre.genre == "ouverture"


def test_un_retour_a_la_normale_sans_episode_ne_dit_rien(moteur: Moteur) -> None:
    """Annoncer que tout va bien alors que rien n'allait mal est du bruit pur."""
    assert moteur.observer("contact-agent", "patator-tower", Etat.OK, T0) is None

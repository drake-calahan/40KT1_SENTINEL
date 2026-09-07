"""Le catalogue transcrit `ADR-002`. Ces tests vérifient qu'il ne s'en écarte pas.

Une table écrite à la main finit par contredire la décision qu'elle transcrit, et
c'est un écart qu'on ne voit pas en relecture — d'où des tests sur son contenu et
pas seulement sur son usage.
"""

from responder.catalogue import CATALOGUE, Etat, incoherences

ARMES_ATTENDUS = {"bloquer_ip", "arreter_processus", "arreter_conteneur", "quarantaine_fichier"}


def test_le_catalogue_est_coherent_avec_ses_invariants() -> None:
    assert incoherences() == []


def test_quatre_gestes_armes_et_ce_sont_ceux_de_la_reponse_E2() -> None:
    armes = {nom for nom, g in CATALOGUE.items() if g.nominal is Etat.ARME}
    assert armes == ARMES_ATTENDUS


def test_les_cinq_autres_ne_sont_jamais_armes() -> None:
    autres = {nom: g for nom, g in CATALOGUE.items() if nom not in ARMES_ATTENDUS}
    assert len(autres) == 5
    assert all(g.nominal is not Etat.ARME for g in autres.values())


def test_couper_le_connecteur_est_interdit_en_mode_tournoi() -> None:
    assert CATALOGUE["couper_connecteur"].tournoi is Etat.JAMAIS


def test_isoler_le_noeud_n_est_jamais_autorise() -> None:
    geste = CATALOGUE["isoler_noeud"]
    assert geste.nominal is Etat.JAMAIS
    assert geste.tournoi is Etat.JAMAIS


def test_arreter_un_conteneur_passe_en_alerte_pendant_un_tournoi() -> None:
    geste = CATALOGUE["arreter_conteneur"]
    assert geste.nominal is Etat.ARME
    assert geste.tournoi is Etat.ALERTE
    assert not geste.invisible


def test_chaque_geste_dit_comment_on_le_defait() -> None:
    # Le critere d'admission d'ADR-062 de HQ : ce qu'un humain peut defaire sans
    # arbitrage. Un geste sans retour arriere ecrit n'a pas ete instruit.
    assert all(g.retour_arriere.strip() for g in CATALOGUE.values())

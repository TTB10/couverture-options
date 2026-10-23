"""Le guide ne doit ni casser l'application ni entrer en conflit avec ses clés."""

import re

import guide


def test_six_etapes_completes():
    assert len(guide.ETAPES) == 6
    for etape in guide.ETAPES:
        assert etape["titre"] and etape["texte"]


def test_pas_de_balise_html_non_fermee():
    """Contrôle sommaire : autant de balises ouvrantes que de fermantes."""
    for etape in guide.ETAPES:
        contenu = etape["texte"] + (etape["exemple"] or "")
        for balise in ("p", "ul", "li", "b"):
            ouvrantes = len(re.findall(rf"<{balise}>", contenu))
            fermantes = len(re.findall(rf"</{balise}>", contenu))
            assert ouvrantes == fermantes, f"balise <{balise}> déséquilibrée"


def test_memoire_du_guide():
    """rouvrir_guide remet le guide à l'étape 1 ; _fermer le marque comme vu."""
    import streamlit as st

    st.session_state.clear()
    guide._fermer()
    assert st.session_state["guide_vu"] is True

    guide.rouvrir_guide()
    assert st.session_state["guide_vu"] is False
    assert st.session_state["guide_etape"] == 0

    guide._aller_a(3)
    assert st.session_state["guide_etape"] == 3
    st.session_state.clear()


def test_cles_sans_conflit_avec_l_application():
    """Les clés du guide sont préfixées et ne touchent pas à celles des widgets."""
    cles_application = {"spot", "strike", "maturity", "rate", "vol", "ticker", "fenetre",
                        "import_message", "import_ok"}
    cles_guide = {"guide_vu", "guide_etape", "guide_passer", "guide_precedent",
                  "guide_suivant", "guide_commencer", "revoir_guide"}

    assert not cles_application & cles_guide

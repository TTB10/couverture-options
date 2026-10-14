"""Vérification des positions, de leurs sensibilités et de la couverture."""

import pytest

from pricer.position import Portfolio, Position

SPOT = 100.0
BASE = dict(quantity=100, strike=100.0, maturity=1.0, rate=0.05, vol=0.20)


def position(sens, option_type):
    return Position(sens=sens, option_type=option_type, **BASE)


def test_valeur_signee_selon_le_sens():
    achat = position("long", "call")
    vente = position("short", "call")

    assert achat.value(SPOT) == pytest.approx(1045.06, abs=0.01)
    assert vente.value(SPOT) == pytest.approx(-achat.value(SPOT))


@pytest.mark.parametrize("sens, option_type, signe_delta, signe_gamma", [
    ("long", "call", +1, +1),
    ("short", "call", -1, -1),
    ("long", "put", -1, +1),
    ("short", "put", +1, -1),
])
def test_signes_des_grecques_des_quatre_positions(sens, option_type, signe_delta, signe_gamma):
    """Toute option achetée est longue en gamma, toute option vendue est courte."""
    pos = position(sens, option_type)

    assert pos.delta(SPOT) * signe_delta > 0
    assert pos.gamma(SPOT) * signe_gamma > 0


def test_couverture_annule_le_delta():
    """Détenir shares_to_hold actions rend le delta total nul."""
    pos = position("short", "call")
    actions = pos.shares_to_hold(SPOT)

    assert pos.delta(SPOT) + actions == pytest.approx(0.0, abs=1e-9)


def test_sens_de_la_couverture_des_quatre_positions():
    assert position("long", "call").shares_to_hold(SPOT) < 0     # vendre des actions
    assert position("short", "call").shares_to_hold(SPOT) > 0    # acheter des actions
    assert position("long", "put").shares_to_hold(SPOT) > 0
    assert position("short", "put").shares_to_hold(SPOT) < 0


def test_instruction_en_clair():
    instruction = position("short", "call").hedge_instruction(SPOT)

    assert instruction.startswith("Acheter")
    assert "64" in instruction          # 100 options x delta 0,6368 -> 64 actions


def test_ajustement_quand_le_cours_monte():
    """Un vendeur de call doit racheter des actions quand le cours monte : short gamma."""
    pos = position("short", "call")

    assert pos.adjustment(100.0, 110.0) > 0
    assert pos.adjustment(100.0, 90.0) < 0
    assert "acheter" in pos.adjustment_instruction(100.0, 110.0).lower()


def test_ajustement_inverse_pour_l_acheteur():
    """L'acheteur est long gamma : il revend quand le cours monte."""
    assert position("long", "call").adjustment(100.0, 110.0) < 0


@pytest.mark.parametrize("parametres, message", [
    (dict(quantity=0), "quantité"),
    (dict(quantity=-50), "quantité"),
    (dict(maturity=0.0), "maturité"),
    (dict(vol=0.0), "volatilité"),
    (dict(sens="acheteur"), "Sens inconnu"),
])
def test_position_invalide_refusee(parametres, message):
    arguments = {**BASE, "sens": "long", "option_type": "call", **parametres}

    with pytest.raises(ValueError, match=message):
        Position(**arguments)


def test_portefeuille_additionne_les_sensibilites():
    """Bonus : delta et gamma agrégés d'un straddle vendu."""
    call_vendu = position("short", "call")
    put_vendu = position("short", "put")
    portefeuille = Portfolio.from_list([call_vendu, put_vendu], name="Straddle vendu")

    assert len(portefeuille) == 2
    assert portefeuille.delta(SPOT) == pytest.approx(call_vendu.delta(SPOT) + put_vendu.delta(SPOT))
    assert portefeuille.gamma(SPOT) < 0                       # vendeur de volatilité
    assert portefeuille.value(SPOT) == pytest.approx(-1602.41, abs=0.1)


def test_portefeuille_couvert_a_un_delta_nul():
    portefeuille = Portfolio.from_list([position("short", "call"), position("long", "put")])
    actions = portefeuille.shares_to_hold(SPOT)

    assert portefeuille.delta(SPOT) + actions == pytest.approx(0.0, abs=1e-9)

"""Vérification des formules de Black-Scholes."""

import numpy as np
import pytest

from pricer import black_scholes as bs

S, K, T, R, VOL = 100.0, 100.0, 1.0, 0.05, 0.20


def test_valeurs_de_reference():
    """Cas classique de la littérature (Hull) : S = K = 100, T = 1, r = 5 %, sigma = 20 %."""
    assert bs.price(S, K, T, R, VOL, "call") == pytest.approx(10.4506, abs=1e-4)
    assert bs.price(S, K, T, R, VOL, "put") == pytest.approx(5.5735, abs=1e-4)
    assert bs.delta(S, K, T, R, VOL, "call") == pytest.approx(0.6368, abs=1e-4)
    assert bs.gamma(S, K, T, R, VOL) == pytest.approx(0.018762, abs=1e-6)


@pytest.mark.parametrize("spot", [60, 80, 100, 130, 160])
@pytest.mark.parametrize("maturity", [0.1, 0.5, 2.0])
def test_parite_call_put(spot, maturity):
    """C - P = S - K e^(-rT) : relation d'arbitrage, indépendante du modèle."""
    call = bs.price(spot, K, maturity, R, VOL, "call")
    put = bs.price(spot, K, maturity, R, VOL, "put")

    assert call - put == pytest.approx(spot - K * np.exp(-R * maturity), abs=1e-10)


@pytest.mark.parametrize("spot", [60, 100, 160])
def test_parite_sur_les_deltas(spot):
    """La parité dérivée une fois en S donne delta_call - delta_put = 1."""
    ecart = bs.delta(spot, K, T, R, VOL, "call") - bs.delta(spot, K, T, R, VOL, "put")
    assert ecart == pytest.approx(1.0, abs=1e-12)


@pytest.mark.parametrize("option_type", ["call", "put"])
def test_gamma_par_differences_finies(option_type):
    """Le gamma analytique est confirmé par une seconde méthode, indépendante."""
    h = 0.5
    seconde_difference = (bs.price(S + h, K, T, R, VOL, option_type)
                          - 2 * bs.price(S, K, T, R, VOL, option_type)
                          + bs.price(S - h, K, T, R, VOL, option_type)) / h**2

    assert seconde_difference == pytest.approx(bs.gamma(S, K, T, R, VOL), rel=1e-4)


def test_bornes_des_deltas():
    for spot in (50, 100, 150):
        assert 0 < bs.delta(spot, K, T, R, VOL, "call") < 1
        assert -1 < bs.delta(spot, K, T, R, VOL, "put") < 0


def test_gamma_positif_et_maximal_pres_de_la_monnaie():
    gammas = {spot: bs.gamma(spot, K, T, R, VOL) for spot in (60, 80, 100, 130, 160)}

    assert all(g > 0 for g in gammas.values())
    assert gammas[100] == max(gammas.values())


def test_prix_croissant_en_volatilite():
    """Le vega est positif : plus d'incertitude, plus de valeur."""
    assert bs.price(S, K, T, R, 0.4, "call") > bs.price(S, K, T, R, 0.2, "call")


def test_fonctions_vectorisees():
    """Un tableau de spots en entrée donne un tableau en sortie, pour tracer les courbes."""
    spots = np.linspace(60, 140, 5)

    assert bs.price(spots, K, T, R, VOL).shape == spots.shape
    assert np.all(np.diff(bs.delta(spots, K, T, R, VOL)) > 0)   # delta croissant en S


@pytest.mark.parametrize("parametres, message", [
    (dict(maturity=0.0), "maturité"),
    (dict(vol=0.0), "volatilité"),
    (dict(vol=-0.2), "volatilité"),
    (dict(strike=0.0), "strike"),
    (dict(option_type="straddle"), "Type d'option"),
])
def test_parametres_invalides_refuses(parametres, message):
    arguments = dict(spot=S, strike=K, maturity=T, rate=R, vol=VOL, option_type="call")
    arguments.update(parametres)

    with pytest.raises(ValueError, match=message):
        bs.price(**arguments)


def test_spot_negatif_refuse():
    with pytest.raises(ValueError, match="cours"):
        bs.price(-10, K, T, R, VOL)

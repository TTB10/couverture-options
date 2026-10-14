"""Les relations de vérification doivent tenir sur tout l'espace des paramètres."""

import itertools

import pytest

from pricer.checks import (gamma_par_differences_finies, parite_call_put,
                           parite_sur_les_deltas, toutes_les_verifications,
                           valeur_de_reference)

GRILLE = list(itertools.product([60, 100, 150], [80, 100, 120], [0.1, 1.0, 2.0],
                                [0.0, 0.05], [0.15, 0.4]))


@pytest.mark.parametrize("spot, strike, maturity, rate, vol", GRILLE)
def test_parite_verifiee_partout(spot, strike, maturity, rate, vol):
    assert parite_call_put(spot, strike, maturity, rate, vol).ok


@pytest.mark.parametrize("spot, strike, maturity, rate, vol", GRILLE)
def test_parite_des_deltas_verifiee_partout(spot, strike, maturity, rate, vol):
    assert parite_sur_les_deltas(spot, strike, maturity, rate, vol).ok


@pytest.mark.parametrize("option_type", ["call", "put"])
def test_gamma_confirme_par_differences_finies(option_type):
    assert gamma_par_differences_finies(100, 100, 1.0, 0.05, 0.2, option_type).ok


@pytest.mark.parametrize("option_type", ["call", "put"])
def test_valeurs_de_reference(option_type):
    assert valeur_de_reference(option_type).ok


def test_tableau_complet_de_verifications():
    verifications = toutes_les_verifications(100, 100, 1.0, 0.05, 0.2)

    assert len(verifications) == 6
    assert all(v.ok for v in verifications)
    assert all(v.explication for v in verifications)      # chaque test est documenté


def test_une_verification_echoue_si_l_ecart_depasse_la_tolerance():
    """Contrôle du mécanisme lui-même : une relation fausse doit être signalée."""
    from pricer.checks import Verification

    assert not Verification("test", "", 1.0, 1.1, 1e-6).ok
    assert Verification("test", "", 1.0, 1.0 + 1e-9, 1e-6).ok

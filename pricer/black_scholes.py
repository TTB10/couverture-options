"""Formules de Black-Scholes : prix, delta et gamma d'une option européenne.

Toutes les fonctions acceptent un spot scalaire ou un tableau NumPy, ce qui permet
de tracer une courbe en un seul appel.

Conventions : taux et volatilité annuels, maturité en années, pas de dividende.
"""

import numpy as np
from scipy.stats import norm

TYPES_AUTORISES = ("call", "put")


def _verifier(strike, maturity, rate, vol, option_type):
    """Refuse les paramètres sans signification, avec un message explicite."""
    if option_type not in TYPES_AUTORISES:
        raise ValueError(f"Type d'option inconnu : {option_type!r} (attendu 'call' ou 'put').")
    if strike <= 0:
        raise ValueError("Le strike doit être strictement positif.")
    if maturity <= 0:
        raise ValueError("La maturité doit être strictement positive.")
    if vol <= 0:
        raise ValueError("La volatilité doit être strictement positive.")
    # Le taux peut être négatif : cela s'est produit en zone euro entre 2014 et 2022.


def d1_d2(spot, strike, maturity, rate, vol):
    """Les deux quantités qui apparaissent dans toutes les formules de Black-Scholes."""
    spot = np.asarray(spot, dtype=float)
    if np.any(spot <= 0):
        raise ValueError("Le cours du sous-jacent doit être strictement positif.")

    d1 = (np.log(spot / strike) + (rate + 0.5 * vol**2) * maturity) / (vol * np.sqrt(maturity))
    return d1, d1 - vol * np.sqrt(maturity)


def price(spot, strike, maturity, rate, vol, option_type="call"):
    """Prix d'une option européenne.

    Call = S·N(d1) − K·e^(−rT)·N(d2)        Put = K·e^(−rT)·N(−d2) − S·N(−d1)
    """
    _verifier(strike, maturity, rate, vol, option_type)
    d1, d2 = d1_d2(spot, strike, maturity, rate, vol)
    strike_actualise = strike * np.exp(-rate * maturity)

    if option_type == "call":
        return np.asarray(spot) * norm.cdf(d1) - strike_actualise * norm.cdf(d2)
    return strike_actualise * norm.cdf(-d2) - np.asarray(spot) * norm.cdf(-d1)


def delta(spot, strike, maturity, rate, vol, option_type="call"):
    """Sensibilité du prix au cours : nombre d'actions équivalentes à une option.

    Δ_call = N(d1) ∈ (0, 1)        Δ_put = N(d1) − 1 ∈ (−1, 0)
    """
    _verifier(strike, maturity, rate, vol, option_type)
    d1, _ = d1_d2(spot, strike, maturity, rate, vol)
    return norm.cdf(d1) if option_type == "call" else norm.cdf(d1) - 1.0


def gamma(spot, strike, maturity, rate, vol, option_type="call"):
    """Sensibilité du delta au cours : la convexité.

    Γ = φ(d1) / (S·σ·√T), identique pour le call et le put (conséquence de la parité).
    """
    _verifier(strike, maturity, rate, vol, option_type)
    d1, _ = d1_d2(spot, strike, maturity, rate, vol)
    return norm.pdf(d1) / (np.asarray(spot) * vol * np.sqrt(maturity))

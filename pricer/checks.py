"""Vérification des formules par des relations indépendantes du modèle.

L'idée : ne pas se contenter de comparer les résultats à des valeurs attendues, mais
les confronter à des relations qui doivent être vraies quelles que soient les formules
utilisées. Si l'une d'elles échoue, c'est qu'il y a une erreur d'implémentation.

Ces fonctions servent à la fois aux tests automatiques et à l'affichage dans l'interface.
"""

from dataclasses import dataclass

import numpy as np

from pricer import black_scholes as bs

# Cas de référence publié dans la littérature (Hull) : call = 10,4506 et put = 5,5735.
REFERENCE = dict(spot=100.0, strike=100.0, maturity=1.0, rate=0.05, vol=0.20)
PRIX_REFERENCE = {"call": 10.450584, "put": 5.573526}


@dataclass(frozen=True)
class Verification:
    """Une relation à vérifier, avec ses deux membres et l'écart constaté."""

    nom: str
    explication: str
    gauche: float
    droite: float
    tolerance: float

    @property
    def ecart(self):
        return abs(self.gauche - self.droite)

    @property
    def ok(self):
        return self.ecart <= self.tolerance


def parite_call_put(spot, strike, maturity, rate, vol):
    """C − P = S − K·e^(−rT).

    Un call acheté et un put vendu paient S − K dans tous les scénarios : ce flux se
    réplique en achetant l'action et en empruntant K·e^(−rT). Deux portefeuilles de
    même flux ont le même prix, sous peine d'arbitrage. Aucune hypothèse de modèle.
    """
    call = bs.price(spot, strike, maturity, rate, vol, "call")
    put = bs.price(spot, strike, maturity, rate, vol, "put")
    return Verification(
        "Parité call-put : C − P = S − K·e^(−rT)",
        "Relation d'arbitrage, vraie quel que soit le modèle. Elle contrôle la cohérence "
        "du call et du put, l'actualisation et les signes.",
        float(call - put), float(spot - strike * np.exp(-rate * maturity)), 1e-10)


def parite_sur_les_deltas(spot, strike, maturity, rate, vol):
    """Δ_call − Δ_put = 1, obtenu en dérivant la parité par rapport au spot."""
    return Verification(
        "Parité dérivée : Δ_call − Δ_put = 1",
        "Le membre de droite de la parité vaut S − K·e^(−rT) : sa dérivée en S vaut 1. "
        "Les deux deltas doivent donc différer exactement de 1.",
        float(bs.delta(spot, strike, maturity, rate, vol, "call")
              - bs.delta(spot, strike, maturity, rate, vol, "put")),
        1.0, 1e-12)


def gamma_par_differences_finies(spot, strike, maturity, rate, vol, option_type="call"):
    """Le gamma analytique confronté à la dérivée seconde du prix, calculée numériquement.

    Ici, la formule du gamma n'est pas utilisée des deux côtés : le test est donc
    réellement indépendant, contrairement à une comparaison Γ_call = Γ_put, vraie par
    construction puisque la même fonction est appelée.
    """
    h = 0.01 * spot
    seconde_difference = (bs.price(spot + h, strike, maturity, rate, vol, option_type)
                          - 2 * bs.price(spot, strike, maturity, rate, vol, option_type)
                          + bs.price(spot - h, strike, maturity, rate, vol, option_type)) / h**2
    return Verification(
        f"Gamma du {option_type} : formule vs différences finies",
        "La dérivée seconde du prix est recalculée numériquement, par une méthode "
        "totalement différente. L'écart résiduel vient de la troncature du schéma.",
        float(bs.gamma(spot, strike, maturity, rate, vol)),
        float(seconde_difference), 1e-4)


def valeur_de_reference(option_type="call"):
    """Comparaison à une valeur publiée : S = K = 100, T = 1 an, r = 5 %, σ = 20 %."""
    return Verification(
        f"Valeur de référence du {option_type} (Hull)",
        "La parité seule ne valide pas d₁, car elle est satisfaite quelles que soient ses "
        "valeurs. Une valeur publiée complète donc le contrôle.",
        float(bs.price(option_type=option_type, **REFERENCE)),
        PRIX_REFERENCE[option_type], 1e-4)


def toutes_les_verifications(spot, strike, maturity, rate, vol):
    """L'ensemble des contrôles, pour les paramètres saisis par l'utilisateur."""
    return [
        parite_call_put(spot, strike, maturity, rate, vol),
        parite_sur_les_deltas(spot, strike, maturity, rate, vol),
        gamma_par_differences_finies(spot, strike, maturity, rate, vol, "call"),
        gamma_par_differences_finies(spot, strike, maturity, rate, vol, "put"),
        valeur_de_reference("call"),
        valeur_de_reference("put"),
    ]

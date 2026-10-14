"""Position d'options et couverture en delta.

Une Position décrit ce que le trader détient : un sens (achat ou vente), un type
d'option, une quantité et les caractéristiques du contrat. Elle sait calculer sa
valeur, ses sensibilités et la couverture à mettre en place.

Convention de signe : une position courte a une quantité signée négative, donc un
delta négatif pour un call vendu. La couverture est l'opposé du delta de la
position : couvrir, c'est annuler le delta total.
"""

from dataclasses import dataclass, replace

from pricer import black_scholes as bs

SENS_AUTORISES = ("long", "short")


@dataclass(frozen=True)
class Position:
    """Une position sur une seule option européenne."""

    sens: str = "long"            # "long" (achat) ou "short" (vente)
    option_type: str = "call"     # "call" ou "put"
    quantity: float = 100.0       # nombre d'options, strictement positif
    strike: float = 100.0
    maturity: float = 0.5         # en années
    rate: float = 0.03
    vol: float = 0.20

    def __post_init__(self):
        """Validation à la création : un objet invalide ne peut pas exister."""
        if self.sens not in SENS_AUTORISES:
            raise ValueError(f"Sens inconnu : {self.sens!r} (attendu 'long' ou 'short').")
        if self.quantity <= 0:
            raise ValueError("La quantité doit être strictement positive ; "
                             "le sens est donné par le champ 'sens'.")
        bs._verifier(self.strike, self.maturity, self.rate, self.vol, self.option_type)

    # ---------------------------------------------------------------- description
    @property
    def signe(self):
        """+1 si la position est achetée, −1 si elle est vendue."""
        return 1.0 if self.sens == "long" else -1.0

    @property
    def quantite_signee(self):
        return self.signe * self.quantity

    @property
    def libelle(self):
        traduction = {"long": "Achat", "short": "Vente"}
        return f"{traduction[self.sens]} de {self.quantity:.0f} {self.option_type}s K={self.strike:.0f}"

    # ---------------------------------------------------------------- valorisation
    def unit_price(self, spot):
        """Prix d'une seule option."""
        return bs.price(spot, self.strike, self.maturity, self.rate, self.vol, self.option_type)

    def value(self, spot):
        """Valeur de la position : négative si l'on est vendeur."""
        return self.quantite_signee * self.unit_price(spot)

    def unit_delta(self, spot):
        return bs.delta(spot, self.strike, self.maturity, self.rate, self.vol, self.option_type)

    def unit_gamma(self, spot):
        return bs.gamma(spot, self.strike, self.maturity, self.rate, self.vol, self.option_type)

    def delta(self, spot):
        """Delta de la position entière, en nombre d'actions équivalentes."""
        return self.quantite_signee * self.unit_delta(spot)

    def gamma(self, spot):
        """Gamma de la position entière. Négatif pour toute option vendue."""
        return self.quantite_signee * self.unit_gamma(spot)

    # ---------------------------------------------------------------- couverture
    def shares_to_hold(self, spot):
        """Nombre d'actions à détenir pour annuler le delta de la position.

        Positif : il faut acheter des actions. Négatif : il faut en vendre.
        """
        return -self.delta(spot)

    def hedge_instruction(self, spot):
        """La couverture énoncée en clair, pour un utilisateur qui ne lit pas le code."""
        return _instruction(self.shares_to_hold(spot))

    def adjustment(self, spot_initial, spot_final):
        """Actions à acheter (+) ou vendre (−) pour rester couvert quand le cours bouge."""
        return self.shares_to_hold(spot_final) - self.shares_to_hold(spot_initial)

    def adjustment_instruction(self, spot_initial, spot_final):
        ajustement = self.adjustment(spot_initial, spot_final)
        if abs(ajustement) < 0.5:
            return "Aucun ajustement significatif (moins d'une action)."
        verbe = "Acheter" if ajustement > 0 else "Vendre"
        return (f"Le cours passe de {spot_initial:.2f} € à {spot_final:.2f} € : "
                f"{verbe.lower()} {abs(ajustement):.0f} actions, "
                f"soit {abs(ajustement) * spot_final:,.0f} €".replace(",", " ") + ".")

    def with_spot_params(self, **modifications):
        """Copie de la position avec certains paramètres modifiés (volatilité, maturité…)."""
        return replace(self, **modifications)


@dataclass(frozen=True)
class Portfolio:
    """Plusieurs positions sur le même sous-jacent (bonus).

    Les sensibilités s'additionnent, par linéarité de la dérivation.
    """

    positions: tuple = ()
    name: str = "Portefeuille"

    @classmethod
    def from_list(cls, positions, name="Portefeuille"):
        return cls(tuple(positions), name)

    def value(self, spot):
        return sum(p.value(spot) for p in self.positions)

    def delta(self, spot):
        return sum(p.delta(spot) for p in self.positions)

    def gamma(self, spot):
        return sum(p.gamma(spot) for p in self.positions)

    def shares_to_hold(self, spot):
        return -self.delta(spot)

    def hedge_instruction(self, spot):
        return _instruction(self.shares_to_hold(spot))

    def adjustment(self, spot_initial, spot_final):
        return self.shares_to_hold(spot_final) - self.shares_to_hold(spot_initial)

    def __len__(self):
        return len(self.positions)


def _instruction(actions):
    """Traduit un nombre d'actions signé en phrase lisible."""
    if abs(actions) < 0.5:
        return "Position déjà neutre : aucune action à traiter."
    verbe = "Acheter" if actions > 0 else "Vendre"
    return f"{verbe} {abs(actions):,.0f} actions".replace(",", " ")

"""Récupération du cours et de la volatilité historique depuis Yahoo Finance.

Le modèle de Black-Scholes a besoin de deux grandeurs que le marché ne fournit pas de
la même façon :

* le **cours** est observable directement ;
* la **volatilité** ne l'est pas. On l'estime ici sur l'historique récent (volatilité
  réalisée), ce qui est une approximation : le marché, lui, cote une volatilité
  *implicite*, qui est son anticipation.

Ce module est isolé du reste : si le réseau est indisponible, seule cette fonctionnalité
est touchée, et l'utilisateur peut toujours saisir ses paramètres à la main.
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd

JOURS_DE_BOURSE = 252


class DonneesIndisponibles(Exception):
    """Ticker inconnu, réseau coupé, ou historique trop court."""


@dataclass(frozen=True)
class SnapshotMarche:
    """Photographie du marché à un instant donné."""

    ticker: str
    spot: float
    vol: float                 # volatilité annualisée, estimée sur l'historique
    fenetre: int               # nombre de jours utilisés pour l'estimation
    historique: pd.Series      # cours de clôture ajustés
    rendements: pd.Series      # rendements logarithmiques quotidiens

    @property
    def date(self):
        return self.historique.index[-1]

    @property
    def vol_journaliere(self):
        return self.vol / np.sqrt(JOURS_DE_BOURSE)

    def vol_glissante(self, fenetre=None):
        """Volatilité annualisée calculée sur une fenêtre glissante, pour voir son évolution."""
        fenetre = fenetre or self.fenetre
        return self.rendements.rolling(fenetre).std() * np.sqrt(JOURS_DE_BOURSE)


def telecharger(ticker, periode="2y", fenetre=60):
    """Télécharge l'historique et estime la volatilité réalisée.

    fenetre : nombre de jours de bourse utilisés pour l'écart-type des rendements.
    """
    if fenetre < 5:
        raise ValueError("La fenêtre d'estimation doit couvrir au moins 5 jours.")

    try:
        import yfinance as yf

        historique = yf.Ticker(ticker).history(period=periode, auto_adjust=True)["Close"]
    except Exception as erreur:                       # réseau, ticker invalide, API modifiée
        raise DonneesIndisponibles(f"téléchargement impossible ({erreur}).") from erreur

    historique = historique.dropna()
    if len(historique) < fenetre + 1:
        raise DonneesIndisponibles(
            f"historique trop court pour {ticker!r} : {len(historique)} séances disponibles, "
            f"{fenetre + 1} nécessaires.")

    # Rendements logarithmiques : ce sont eux qui sont supposés gaussiens dans le modèle.
    rendements = np.log(historique / historique.shift(1)).dropna()
    vol = float(rendements.tail(fenetre).std() * np.sqrt(JOURS_DE_BOURSE))

    if not np.isfinite(vol) or vol <= 0:
        raise DonneesIndisponibles(f"volatilité inexploitable pour {ticker!r}.")

    return SnapshotMarche(ticker=ticker.upper(), spot=float(historique.iloc[-1]), vol=vol,
                          fenetre=fenetre, historique=historique, rendements=rendements)

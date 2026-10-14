"""Outil de gestion du risque d'une position d'options — interface graphique.

Cette couche ne contient aucun calcul financier : elle saisit une position, appelle le
paquet `pricer` et met les résultats en forme.

Lancement :  streamlit run app.py
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from pricer import market_data as md
from pricer.checks import toutes_les_verifications
from pricer.position import Portfolio, Position

# Les quatre positions de base, telles qu'un trader les nomme.
POSITIONS = {
    "Achat de call (long call)": ("long", "call"),
    "Vente de call (short call)": ("short", "call"),
    "Achat de put (long put)": ("long", "put"),
    "Vente de put (short put)": ("short", "put"),
}

VALEURS_PAR_DEFAUT = {"spot": 100.0, "strike": 100.0, "maturity": 0.5,
                      "rate": 3.0, "vol": 20.0, "ticker": "AAPL", "fenetre": 60,
                      "import_message": "", "import_ok": True}

st.set_page_config(page_title="Couverture d'une position d'options", layout="wide",
                   page_icon="🛡️")

for cle, valeur in VALEURS_PAR_DEFAUT.items():
    st.session_state.setdefault(cle, valeur)


@st.cache_data(ttl=300, show_spinner=False)
def charger_marche(ticker, fenetre):
    """Téléchargement mis en cache cinq minutes, pour ne pas solliciter Yahoo à chaque clic."""
    return md.telecharger(ticker, fenetre=fenetre)


def importer_marche():
    """Remplit le cours et la volatilité depuis Yahoo Finance (exécuté avant le rerun)."""
    try:
        snapshot = charger_marche(st.session_state.ticker.strip().upper(),
                                  int(st.session_state.fenetre))
        st.session_state.spot = round(snapshot.spot, 2)
        st.session_state.strike = round(snapshot.spot, 2)   # strike à la monnaie par défaut
        st.session_state.vol = round(snapshot.vol * 100, 1)
        st.session_state.import_ok = True
        st.session_state.import_message = (
            f"{snapshot.ticker} : cours {snapshot.spot:.2f} au {snapshot.date:%d/%m/%Y}, "
            f"volatilité réalisée {snapshot.vol:.1%} sur {snapshot.fenetre} séances.")
    except (md.DonneesIndisponibles, ValueError) as erreur:
        st.session_state.import_ok = False
        st.session_state.import_message = f"Import impossible — {erreur}"


# =====================================================================
# 1. Saisie de la position
# =====================================================================

with st.sidebar:
    st.header("1 · Position")
    libelle = st.selectbox("Type de position", list(POSITIONS))
    sens, option_type = POSITIONS[libelle]
    quantity = st.number_input("Quantité (nombre de contrats)", min_value=1, max_value=100_000,
                               value=100, step=10)
    taille_contrat = st.number_input(
        "Titres par contrat", min_value=1, max_value=1000, value=1, step=1,
        help="1 pour raisonner en options unitaires (1 option = 1 action), "
             "100 pour des contrats boursiers standards.")
    nb_options = quantity * taille_contrat

    st.header("2 · Contrat")
    strike = st.number_input("Strike K (€)", min_value=0.01, max_value=100_000.0,
                             step=1.0, key="strike")
    maturity = st.number_input("Maturité T (années)", min_value=0.01, max_value=10.0,
                               step=0.05, key="maturity")

    st.header("3 · Marché")
    spot_initial = st.number_input("Cours actuel S₀ (€)", min_value=0.01, max_value=100_000.0,
                                   step=1.0, key="spot")
    rate = st.number_input("Taux sans risque r (%)", min_value=-2.0, max_value=15.0,
                           step=0.25, key="rate") / 100
    vol = st.number_input("Volatilité σ (%)", min_value=1.0, max_value=200.0,
                          step=1.0, key="vol") / 100

    with st.expander("Importer depuis Yahoo Finance"):
        st.text_input("Ticker", key="ticker", help="Exemples : AAPL, MSFT, ^GSPC, AIR.PA")
        st.select_slider("Fenêtre d'estimation de la volatilité (séances)",
                         options=[20, 30, 60, 90, 120, 252], key="fenetre")
        st.button("Récupérer cours et volatilité", on_click=importer_marche,
                  use_container_width=True)
        st.caption("Le cours est observable ; la volatilité ne l'est pas. Elle est estimée ici "
                   "sur l'historique récent (volatilité *réalisée*), ce qui diffère de la "
                   "volatilité *implicite* cotée par le marché.")

    if st.session_state.import_message:
        if st.session_state.import_ok:
            st.success(st.session_state.import_message)
        else:
            st.error(st.session_state.import_message)

# La validation vit dans le moteur ; l'interface se contente d'afficher le message.
try:
    position = Position(sens=sens, option_type=option_type, quantity=nb_options,
                        strike=strike, maturity=maturity, rate=rate, vol=vol)
except ValueError as erreur:
    st.error(f"Saisie invalide : {erreur}")
    st.stop()

st.title("Couverture en delta d'une position d'options")
st.caption(f"**{libelle}** · {quantity:.0f} contrats × {taille_contrat:.0f} = "
           f"{nb_options:.0f} options · K = {strike:.2f} € · T = {maturity:.2f} an · "
           f"r = {rate:.2%} · σ = {vol:.1%}")

with st.expander("Mode d'emploi — à lire une fois", expanded=True):
    st.markdown(
        "**1 · Saisir la position** (barre latérale). Choisissez le sens et le type d'option "
        "(achat ou vente, call ou put), la quantité, puis le contrat (strike, maturité) et le "
        "marché (cours, taux, volatilité). Une saisie invalide est refusée avec un message "
        "explicite : l'outil ne plante pas.\n\n"
        "**2 · Importer les données réelles** (facultatif). Dans *Marché → Importer depuis Yahoo "
        "Finance*, saisissez un ticker (AAPL, MSFT, ^GSPC, AIR.PA) et cliquez : le cours, le "
        "strike et la volatilité réalisée se remplissent automatiquement.\n\n"
        "**3 · Lire la couverture.** L'encart donne le prix, le delta unitaire et le gamma par "
        "option, puis la valeur, le delta et le gamma de la position entière, et enfin le nombre "
        "d'actions à traiter, énoncé en clair.\n\n"
        "**4 · Faire bouger le marché.** Le curseur de cours met tout à jour instantanément : "
        "les chiffres, le point noir sur les deux graphiques, et l'ajustement à effectuer pour "
        "rester couvert.\n\n"
        "**5 · Explorer les onglets.** *Données de marché* montre l'historique et la volatilité "
        "glissante ; *Vérification des formules* rejoue en direct les contrôles mathématiques ; "
        "*Portefeuille* agrège plusieurs options.")

onglets = st.tabs(["Couverture", "Données de marché", "Vérification des formules",
                   "Portefeuille (bonus)"])

spots = np.linspace(spot_initial * 0.6, spot_initial * 1.4, 400)


def graphique(abscisses, ordonnees, titre, axe_y, couleur, point_courant, reference):
    """Courbe en fonction du cours, avec le point courant et le cours saisi marqués."""
    figure = go.Figure()
    figure.add_trace(go.Scatter(x=abscisses, y=ordonnees, mode="lines", name=axe_y,
                                line=dict(color=couleur, width=2)))
    figure.add_trace(go.Scatter(x=[point_courant],
                                y=[np.interp(point_courant, abscisses, ordonnees)],
                                mode="markers", name="Position actuelle",
                                marker=dict(color="black", size=12)))
    figure.add_vline(x=reference, line_dash="dot", line_color="grey",
                     annotation_text="S₀", annotation_position="top left")
    figure.add_hline(y=0, line_width=1, line_color="black")
    figure.update_layout(title=titre, height=430, hovermode="x unified",
                         xaxis_title="Cours du sous-jacent S (€)", yaxis_title=axe_y,
                         margin=dict(t=55, b=10), legend=dict(orientation="h", y=-0.2))
    return figure


# =====================================================================
# 2. Onglet couverture
# =====================================================================

with onglets[0]:
    spot = st.slider("Cours simulé S₁ (€) — déplacez le curseur, tout se met à jour",
                     min_value=float(round(spot_initial * 0.6, 2)),
                     max_value=float(round(spot_initial * 1.4, 2)),
                     value=float(spot_initial),
                     step=float(max(round(spot_initial / 200, 2), 0.01)))

    actions = position.shares_to_hold(spot)

    ligne_option = st.columns(3)
    ligne_option[0].metric("Prix unitaire", f"{position.unit_price(spot):.4f} €",
                           help="Prix d'UNE option.")
    ligne_option[1].metric("Delta unitaire", f"{position.unit_delta(spot):+.4f}",
                           help="Dérivée du prix d'une option par rapport au cours : sans "
                                "dimension, entre 0 et 1 pour un call, entre −1 et 0 pour un put.")
    ligne_option[2].metric("Gamma unitaire", f"{position.unit_gamma(spot):.5f}",
                           help="Variation du delta unitaire pour 1 € de variation du cours.")

    ligne_position = st.columns(4)
    ligne_position[0].metric("Valeur de la position",
                             f"{position.value(spot):+,.0f} €".replace(",", " "))
    ligne_position[1].metric("Delta de position",
                             f"{position.delta(spot):+,.1f} actions".replace(",", " "),
                             help="Delta unitaire × quantité signée : le nombre d'actions "
                                  "auquel la position équivaut.")
    ligne_position[2].metric("Gamma de position", f"{position.gamma(spot):+.3f}")
    ligne_position[3].metric("Couverture", f"{actions:+,.0f} actions".replace(",", " "),
                             delta=f"cours {spot / spot_initial - 1:+.1%} vs S₀")

    st.success(f"**{position.hedge_instruction(spot)}**, soit "
               f"{abs(actions * spot):,.0f} € d'actions.".replace(",", " "))

    log_moneyness = float(np.log(spot / strike))
    if abs(log_moneyness) > 0.5:
        dans_la_monnaie = (log_moneyness > 0) == (option_type == "call")
        st.warning(
            f"Le strike ({strike:.2f} €) est très éloigné du cours ({spot:.2f} €) : l'option est "
            + ("profondément dans la monnaie" if dans_la_monnaie else "très hors de la monnaie")
            + ". Son delta est quasi constant et son gamma quasi nul, donc la couverture ne bouge "
            "presque plus : l'option se comporte comme un contrat à terme, ou ne vaut presque "
            "rien. Rapprochez le strike du cours pour observer le comportement typique d'une "
            "option.")

    if abs(spot - spot_initial) > 1e-9:
        st.info(position.adjustment_instruction(spot_initial, spot))
    else:
        st.info("Déplacez le curseur de cours pour voir l'ajustement à effectuer.")

    with st.expander("Comment lire ces chiffres ?"):
        st.markdown(
            "- **Delta unitaire** : dérivée du prix d'une option par rapport au cours. Sans "
            "dimension, entre 0 et 1 pour un call, entre −1 et 0 pour un put. C'est le delta au "
            "sens du cours.\n"
            "- **Delta de position** : delta unitaire × quantité signée. Il s'exprime en nombre "
            "d'actions équivalentes : un delta de position de +64 signifie que la position gagne "
            "environ 64 € si le cours monte de 1 €.\n"
            "- **Couverture** : l'opposé du delta de position, puisque couvrir revient à annuler "
            "le delta total. Le signe donne le sens : positif, on achète des actions ; négatif, "
            "on en vend.\n"
            "- **Gamma** : la vitesse à laquelle le delta change. Positif pour toute option "
            "achetée, négatif pour toute option vendue, il dicte la fréquence des réajustements.\n"
            "- **Conséquence pratique** : un vendeur d'option (gamma négatif) rachète des actions "
            "quand le cours monte et en revend quand il baisse, donc achète haut et vend bas à "
            "chaque réajustement. La prime encaissée le rémunère pour ce désavantage.")

    # Trois lectures de la même information : la couverture est l'opposé du delta de position,
    # lui-même égal au delta unitaire multiplié par la quantité signée.
    COURBES = {
        "Couverture (actions à détenir)":
            (position.shares_to_hold(spots), "Actions à détenir (nombre)"),
        "Delta de la position (actions équivalentes)":
            (position.delta(spots), "Delta de position (actions)"),
        "Delta unitaire (par option)":
            (position.unit_delta(spots), "Delta unitaire (sans dimension)"),
    }
    GAMMAS = {
        "Gamma de la position": (position.gamma(spots),
                                 "Gamma de position (actions par € de cours)"),
        "Gamma unitaire (par option)": (position.unit_gamma(spots), "Gamma unitaire"),
    }

    choix = st.columns(2)
    courbe_choisie = choix[0].selectbox("Graphique de gauche", list(COURBES))
    gamma_choisi = choix[1].selectbox("Graphique de droite", list(GAMMAS))

    gauche, droite = st.columns(2)
    with gauche:
        valeurs, axe_y = COURBES[courbe_choisie]
        st.plotly_chart(graphique(spots, valeurs, f"{courbe_choisie} selon le cours",
                                  axe_y, "#1f77b4", spot, spot_initial),
                        use_container_width=True)
        st.caption("Les trois courbes décrivent la même chose : la couverture est l'opposé du "
                   "delta de position, lui-même égal au delta unitaire multiplié par la "
                   "quantité signée. La **pente** de la courbe est le gamma : c'est elle qui "
                   "impose de réajuster quand le cours bouge. Survolez la courbe pour lire les "
                   "valeurs, cliquez-glissez pour zoomer, double-cliquez pour revenir à "
                   "l'échelle initiale.")
    with droite:
        valeurs, axe_y = GAMMAS[gamma_choisi]
        st.plotly_chart(graphique(spots, valeurs, f"{gamma_choisi} selon le cours",
                                  axe_y, "#d62728", spot, spot_initial),
                        use_container_width=True)
        gammas = GAMMAS["Gamma de la position"][0]
        instable = spots[np.argmax(np.abs(gammas))]
        st.caption(f"Le gamma est extrême vers **{instable:.2f} €** : c'est là que la couverture "
                   "est la plus instable, car le delta y change le plus vite. Loin de ce niveau, "
                   "la courbe s'aplatit et la couverture devient presque statique.")

# =====================================================================
# 3. Onglet données de marché
# =====================================================================

with onglets[1]:
    st.markdown("Le cours et la volatilité peuvent être saisis à la main ou **importés depuis "
                "Yahoo Finance** (barre latérale, section *Marché*).")

    try:
        snapshot = charger_marche(st.session_state.ticker.strip().upper(),
                                  int(st.session_state.fenetre))
    except (md.DonneesIndisponibles, ValueError) as erreur:
        snapshot = None
        st.warning(f"Pas de données affichables : {erreur}")

    if snapshot is not None:
        cols = st.columns(4)
        cols[0].metric("Dernier cours", f"{snapshot.spot:.2f}")
        cols[1].metric(f"Volatilité réalisée ({snapshot.fenetre} séances)", f"{snapshot.vol:.1%}")
        cols[2].metric("Volatilité quotidienne", f"{snapshot.vol_journaliere:.2%}")
        cols[3].metric("Séances disponibles", f"{len(snapshot.historique)}")

        figure = go.Figure()
        figure.add_trace(go.Scatter(x=snapshot.historique.index, y=snapshot.historique.values,
                                    mode="lines", name="Cours de clôture ajusté",
                                    line=dict(color="#1f77b4", width=1.6)))
        figure.update_layout(title=f"{snapshot.ticker} — historique des cours", height=380,
                             xaxis_title="Date", yaxis_title="Cours (devise de cotation)",
                             hovermode="x unified", margin=dict(t=55, b=10),
                             legend=dict(orientation="h", y=-0.2))
        st.plotly_chart(figure, use_container_width=True)

        vol_glissante = snapshot.vol_glissante().dropna() * 100
        figure = go.Figure()
        figure.add_trace(go.Scatter(x=vol_glissante.index, y=vol_glissante.values, mode="lines",
                                    name=f"Volatilité sur {snapshot.fenetre} séances",
                                    line=dict(color="#d62728", width=1.6)))
        figure.add_hline(y=vol * 100, line_dash="dot", line_color="black",
                         annotation_text=f"σ utilisé : {vol:.1%}", annotation_position="top left")
        figure.update_layout(title="Volatilité réalisée, fenêtre glissante", height=380,
                             xaxis_title="Date", yaxis_title="Volatilité annualisée (%)",
                             hovermode="x unified", margin=dict(t=55, b=10),
                             legend=dict(orientation="h", y=-0.2))
        st.plotly_chart(figure, use_container_width=True)

        st.caption("La volatilité n'est pas constante dans le temps, contrairement à ce que "
                   "suppose Black-Scholes : elle se regroupe en périodes calmes et en périodes "
                   "agitées. Le choix de la fenêtre est un arbitrage entre réactivité (fenêtre "
                   "courte, estimation bruitée) et stabilité (fenêtre longue, estimation en "
                   "retard sur le marché).")

    with st.expander("Volatilité réalisée ou implicite ?"):
        st.markdown(
            "- La **volatilité réalisée** se mesure sur les cours passés : écart-type annualisé "
            "des rendements logarithmiques, soit σ_quotidien × √252.\n"
            "- La **volatilité implicite** se déduit du prix d'une option cotée, en inversant "
            "Black-Scholes. C'est l'anticipation du marché, et c'est elle qu'un trader utilise "
            "pour coter.\n"
            "- Les deux diffèrent presque toujours. L'écart entre la volatilité à laquelle une "
            "option est vendue et celle que le marché réalise ensuite constitue l'essentiel du "
            "résultat d'un vendeur d'options couvert en delta.")

# =====================================================================
# 4. Onglet vérification des formules
# =====================================================================

with onglets[2]:
    st.markdown("Les formules ne sont pas seulement comparées à des valeurs attendues : elles "
                "sont confrontées à des **relations qui doivent être vraies quelles que soient "
                "les formules employées**. Si l'une échoue, c'est qu'il y a une erreur.")

    verifications = toutes_les_verifications(spot_initial, strike, maturity, rate, vol)
    tableau = pd.DataFrame([{
        "Relation": v.nom,
        "Membre de gauche": v.gauche,
        "Membre de droite": v.droite,
        "Écart": v.ecart,
        "Tolérance": v.tolerance,
        "Résultat": "vérifiée" if v.ok else "ÉCHEC",
    } for v in verifications]).set_index("Relation")

    st.dataframe(tableau.style.format({"Membre de gauche": "{:.10f}",
                                       "Membre de droite": "{:.10f}",
                                       "Écart": "{:.2e}", "Tolérance": "{:.0e}"}),
                 use_container_width=True)

    if all(v.ok for v in verifications):
        st.success("Toutes les relations sont vérifiées : les formules sont cohérentes pour "
                   "les paramètres saisis.")
    else:
        st.error("Une relation a échoué : les résultats affichés ne sont pas fiables.")

    for verification in verifications[:4]:
        with st.expander(verification.nom):
            st.markdown(verification.explication)

    st.caption("Limite à connaître : la parité est satisfaite quelles que soient les valeurs de "
               "d₁ et d₂, car N(x) + N(−x) = 1. Elle contrôle la cohérence entre le call et le "
               "put, mais pas la justesse de d₁ — d'où les deux autres familles de tests. "
               "L'ensemble est rejoué automatiquement par la commande `python -m pytest`.")

# =====================================================================
# 5. Onglet portefeuille (bonus)
# =====================================================================

with onglets[3]:
    st.markdown("Plusieurs options sur le même sous-jacent : les sensibilités **s'additionnent**, "
                "par linéarité de la dérivation. Modifiez librement le tableau.")

    defaut = pd.DataFrame([
        {"sens": "short", "option_type": "call", "quantity": 100, "strike": strike * 1.05},
        {"sens": "short", "option_type": "put", "quantity": 100, "strike": strike * 0.95},
    ])
    saisie = st.data_editor(
        defaut, num_rows="dynamic", use_container_width=True,
        column_config={
            "sens": st.column_config.SelectboxColumn("Sens", options=["long", "short"]),
            "option_type": st.column_config.SelectboxColumn("Type", options=["call", "put"]),
            "quantity": st.column_config.NumberColumn("Quantité", min_value=1, step=10),
            "strike": st.column_config.NumberColumn("Strike (€)", min_value=0.01, format="%.2f")})

    try:
        jambes = [Position(sens=ligne.sens, option_type=ligne.option_type,
                           quantity=float(ligne.quantity), strike=float(ligne.strike),
                           maturity=maturity, rate=rate, vol=vol)
                  for ligne in saisie.itertuples()]
        if not jambes:
            st.info("Ajoutez au moins une ligne pour composer un portefeuille.")
        else:
            portefeuille = Portfolio.from_list(jambes)
            cols = st.columns(4)
            cols[0].metric("Valeur",
                           f"{portefeuille.value(spot_initial):+,.0f} €".replace(",", " "))
            cols[1].metric("Delta agrégé",
                           f"{portefeuille.delta(spot_initial):+,.1f}".replace(",", " "))
            cols[2].metric("Gamma agrégé", f"{portefeuille.gamma(spot_initial):+.3f}")
            cols[3].metric("Couverture",
                           f"{portefeuille.shares_to_hold(spot_initial):+,.0f} actions"
                           .replace(",", " "))
            st.success(f"**{portefeuille.hedge_instruction(spot_initial)}**")

            courbe = np.array([portefeuille.shares_to_hold(s) for s in spots])
            st.plotly_chart(graphique(spots, courbe,
                                      "Couverture du portefeuille selon le cours",
                                      "Actions à détenir (nombre)", "#2ca02c",
                                      spot_initial, spot_initial),
                            use_container_width=True)
            st.caption("Exemple par défaut : un *straddle* vendu, call et put vendus. Son delta "
                       "est faible, mais son gamma est fortement négatif : la position ne craint "
                       "pas les petits mouvements, seulement les grands.")
    except (ValueError, AttributeError) as erreur:
        st.error(f"Ligne invalide dans le portefeuille : {erreur}")

st.divider()
st.caption("Modèle de Black-Scholes : volatilité constante, pas de dividende, pas de coûts de "
           "transaction, couverture ajustable en continu. En pratique, un réajustement discret "
           "laisse une erreur de réplication qui ne s'annule jamais et ne décroît que comme "
           "1/√N avec le nombre N de réajustements.")

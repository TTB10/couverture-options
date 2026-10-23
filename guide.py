"""Guide de démarrage affiché à l'ouverture de l'application.

Il s'adresse à une personne qui découvre l'outil : chaque étape explique, sans jargon,
une partie de l'interface. Le guide peut être passé à tout moment et rouvert depuis la
barre latérale.

Fonctionnement : une fenêtre Streamlit (st.dialog) de six étapes, affichée une seule fois
par session grâce à st.session_state. Aucune bibliothèque supplémentaire.
"""

import streamlit as st

# Couleurs reprises des graphiques de l'application (bleu Plotly) pour rester cohérent.
ACCENT = "#1f77b4"
ACCENT_CLAIR = "#5fa8dc"
CARTE = "#ffffff"
TEXTE = "#1c1c24"
TEXTE_SECONDAIRE = "#6b6e7b"

# =============================================================================
# 1. CONTENU DES ÉTAPES
# Chaque étape : un titre, un texte (HTML simple) et un encadré facultatif.
# =============================================================================
ETAPES = [
    {
        "titre": "Bienvenue",
        "texte": """
            <p>Cet outil répond à une question simple :
            <b>si je détiens des options, combien d'actions dois-je acheter ou vendre
            pour ne pas être exposé aux mouvements du marché ?</b></p>
            <p>Il calcule cette couverture, montre comment elle évolue quand le cours bouge,
            et vérifie ses propres formules.</p>
        """,
        "exemple": """
            <b>Un peu de vocabulaire</b><br>
            Une <b>option</b> est un contrat qui donne le droit d'acheter (<i>call</i>) ou de
            vendre (<i>put</i>) une action à un prix fixé d'avance, le <b>strike</b>.
            <b>Couvrir</b> une position, c'est prendre une position inverse sur l'action
            pour neutraliser le risque de direction.
        """,
    },
    {
        "titre": "1. Saisir ta position",
        "texte": """
            <p>Tout se règle dans la <b>barre latérale à gauche</b>, en trois blocs :</p>
            <ul>
              <li><b>Position</b> : achat ou vente, call ou put — les quatre cas de base —
                  puis la quantité et le nombre de titres par contrat.</li>
              <li><b>Contrat</b> : le strike K (le prix fixé d'avance) et la maturité T,
                  en années.</li>
              <li><b>Marché</b> : le cours actuel S₀, le taux sans risque r et la
                  volatilité σ, qui mesure l'agitation de l'action.</li>
            </ul>
            <p>Une saisie impossible (volatilité ou maturité nulle, par exemple) est refusée
            avec un message clair : l'outil ne plante pas.</p>
        """,
        "exemple": """
            <b>Données réelles</b> : dans <b>Marché → Importer depuis Yahoo Finance</b>,
            tapez un ticker (AAPL, MSFT, AIR.PA) et cliquez. Le cours, le strike et la
            volatilité se remplissent automatiquement.
        """,
    },
    {
        "titre": "2. Lire les résultats",
        "texte": """
            <p>Deux rangées de chiffres apparaissent sous le curseur de cours :</p>
            <ul>
              <li><b>Par option</b> : le prix, le <b>delta unitaire</b> (entre 0 et 1 pour un
                  call : de combien l'option bouge quand l'action bouge de 1 €) et le gamma.</li>
              <li><b>Pour la position entière</b> : sa valeur, son <b>delta de position</b>
                  en nombre d'actions équivalentes, son gamma, et enfin la
                  <b>couverture</b>.</li>
            </ul>
            <p>La phrase en vert dit quoi faire, en clair : « Acheter 64 actions ».</p>
        """,
        "exemple": """
            <b>À retenir</b> : la couverture est l'opposé du delta de la position.
            Couvrir, c'est annuler le delta total — donc ne plus rien gagner ni perdre
            lorsque le cours varie légèrement.
        """,
    },
    {
        "titre": "3. Faire bouger le marché",
        "texte": """
            <ul>
              <li>Le <b>curseur de cours</b> simule une variation du marché : tous les chiffres
                  et le point noir des graphiques se mettent à jour aussitôt.</li>
              <li>Le bandeau bleu indique l'<b>ajustement</b> à effectuer : combien d'actions
                  acheter ou vendre pour rester couvert.</li>
              <li>Les deux menus au-dessus des graphiques choisissent ce que l'on trace :
                  couverture, delta de position, delta unitaire, gamma.</li>
            </ul>
            <p>Les graphiques sont interactifs : survolez pour lire les valeurs,
            cliquez-glissez pour zoomer, double-cliquez pour revenir à l'échelle initiale.</p>
        """,
        "exemple": """
            <b>Le gamma en une phrase</b> : c'est la pente de la courbe de couverture.
            Là où elle est forte, le delta change vite et la couverture doit être réajustée
            souvent. Un vendeur d'options rachète quand le cours monte et revend quand il
            baisse : il achète haut et vend bas à chaque réajustement.
        """,
    },
    {
        "titre": "4. Explorer les quatre onglets",
        "texte": """
            <ul>
              <li><b>Couverture</b> : les résultats, le curseur de cours et les deux
                  graphiques.</li>
              <li><b>Données de marché</b> : l'historique des cours importé de Yahoo Finance
                  et la volatilité calculée sur une fenêtre glissante.</li>
              <li><b>Vérification des formules</b> : les contrôles mathématiques rejoués en
                  direct — parité call-put, parité dérivée, gamma recalculé par différences
                  finies, valeurs de référence.</li>
              <li><b>Portefeuille</b> : plusieurs options sur le même sous-jacent, avec delta
                  et gamma agrégés.</li>
            </ul>
        """,
        "exemple": """
            <b>Pourquoi un onglet de vérification ?</b> La parité call-put découle de la seule
            absence d'arbitrage : elle est vraie quel que soit le modèle. Si elle échouait,
            c'est que les formules seraient fausses.
        """,
    },
    {
        "titre": "C'est parti !",
        "texte": """
            <p>Tu sais maintenant l'essentiel :</p>
            <ul>
              <li>tu composes ta position à gauche ;</li>
              <li>tu lis la couverture au centre, énoncée en clair ;</li>
              <li>tu fais bouger le cours avec le curseur pour voir l'ajustement ;</li>
              <li>tu explores les onglets pour aller plus loin.</li>
            </ul>
            <p>Tu pourras rouvrir ce guide à tout moment avec le bouton
            <b>Revoir le guide</b> de la barre latérale.</p>
        """,
        "exemple": None,
    },
]

CSS = f"""
<style>
/* ---- Guide de démarrage (fenêtre au-dessus de l'application) ---- */
/* La fenêtre est créée hors de .stApp : on lui redonne des coins arrondis */
[data-testid="stDialog"] [role="dialog"] {{ border-radius: 24px !important; background: {CARTE}; }}
[data-testid="stDialog"] [role="dialog"] h2 {{ font-weight: 400; letter-spacing: -0.01em; }}
.guide-progression {{ display: flex; align-items: center; gap: 6px; margin-bottom: 0.9rem; }}
.guide-point {{ width: 8px; height: 8px; border-radius: 999px; background: #d9dce5; }}
.guide-point.actif {{ width: 26px;
                      background: linear-gradient(135deg, {ACCENT_CLAIR} 0%, {ACCENT} 100%); }}
.guide-compteur {{ margin-left: auto; color: {TEXTE_SECONDAIRE}; font-size: 0.85rem; }}
.guide-titre {{ font-weight: 500 !important; font-size: 1.35rem !important; color: {TEXTE};
                padding: 0 0 0.4rem 0 !important; }}
.guide-texte, .guide-texte li {{ color: {TEXTE}; font-size: 0.98rem; line-height: 1.55; }}
.guide-texte ul {{ padding-left: 1.1rem; }}
.guide-texte li {{ margin-bottom: 0.35rem; }}
.guide-exemple {{ background: #f4f5f9; border-left: 3px solid {ACCENT}; border-radius: 14px;
                  padding: 0.8rem 1rem; margin: 0.4rem 0 1rem 0; color: {TEXTE};
                  font-size: 0.93rem; line-height: 1.5; }}
/* Boutons du guide : pilule avec le dégradé de l'application */
.st-key-guide_suivant button, .st-key-guide_commencer button {{
    background: linear-gradient(135deg, {ACCENT_CLAIR} 0%, {ACCENT} 100%) !important;
    border: none !important; border-radius: 999px !important;
    box-shadow: 0 6px 18px rgba(31, 119, 180, 0.35);
}}
.st-key-guide_precedent button {{ border-radius: 999px !important; }}
.st-key-guide_passer button p {{ color: {TEXTE_SECONDAIRE}; }}
.st-key-revoir_guide button {{ border-radius: 999px !important; }}
</style>
"""


# =============================================================================
# 2. MÉMOIRE DU GUIDE
# st.session_state garde l'étape en cours et le fait que le guide a été vu.
# Les clés sont préfixées « guide_ » pour ne pas entrer en conflit avec celles
# de l'application (spot, strike, vol, ticker…).
# =============================================================================
def _fermer():
    """Marque le guide comme vu : il ne se rouvre plus pendant la session."""
    st.session_state["guide_vu"] = True


def _aller_a(etape):
    st.session_state["guide_etape"] = etape


def rouvrir_guide():
    """Appelée par le bouton « Revoir le guide » de la barre latérale."""
    st.session_state["guide_vu"] = False
    st.session_state["guide_etape"] = 0


# =============================================================================
# 3. FENÊTRE DU GUIDE
# st.dialog ouvre une fenêtre au-dessus de l'application. La fermer (croix,
# touche Échap, clic à côté) appelle _fermer grâce à on_dismiss.
# =============================================================================
def _contenu():
    n = len(ETAPES)
    i = st.session_state.get("guide_etape", 0)
    etape = ETAPES[i]

    # Points de progression : l'étape en cours est allongée.
    points = "".join(f'<span class="guide-point{" actif" if k == i else ""}"></span>'
                     for k in range(n))
    html = (f'<div class="guide-progression">{points}'
            f'<span class="guide-compteur">Étape {i + 1} sur {n}</span></div>'
            f'<h3 class="guide-titre">{etape["titre"]}</h3>'
            f'<div class="guide-texte">{etape["texte"]}</div>')
    if etape["exemple"]:
        html += f'<div class="guide-exemple">{etape["exemple"]}</div>'
    st.markdown(html, unsafe_allow_html=True)

    # Boutons : « Passer » à gauche, navigation à droite. Un clic dans la fenêtre
    # ne relance que la fenêtre ; st.rerun() relance l'application pour la fermer.
    gauche, _, precedent, suivant = st.columns([1.3, 0.5, 1, 1.2], vertical_alignment="center")
    if i < n - 1:
        if gauche.button("Passer le guide", key="guide_passer", type="tertiary"):
            _fermer()
            st.rerun()
    if i > 0:
        precedent.button("Précédent", key="guide_precedent", on_click=_aller_a, args=(i - 1,),
                         width="stretch")
    if i < n - 1:
        suivant.button("Suivant", key="guide_suivant", type="primary", on_click=_aller_a,
                       args=(i + 1,), width="stretch")
    elif suivant.button("Commencer", key="guide_commencer", type="primary", width="stretch"):
        _fermer()
        st.rerun()


# on_dismiss n'existe que depuis Streamlit 1.65 : on retombe proprement sur la
# version sans fermeture automatique si l'environnement est plus ancien.
try:
    _fenetre_guide = st.dialog("Guide de démarrage", width="medium", on_dismiss=_fermer)(_contenu)
except TypeError:                                   # pragma: no cover - versions anciennes
    _fenetre_guide = st.dialog("Guide de démarrage", width="medium")(_contenu)


def afficher_guide():
    """Injecte le style du guide, puis l'ouvre tant qu'il n'a pas été vu ou passé."""
    st.markdown(CSS, unsafe_allow_html=True)
    if not st.session_state.get("guide_vu", False):
        _fenetre_guide()

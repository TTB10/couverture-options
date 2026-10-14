# Outil de gestion du risque d'une position d'options

Pour une position d'options (achat ou vente d'un call ou d'un put), l'outil indique
**combien d'actions détenir pour la couvrir**, et comment cette couverture évolue
quand le cours du sous-jacent bouge.

## Lancement

```bash
pip install -r requirements.txt
streamlit run app.py
```

L'application s'ouvre dans le navigateur sur `http://localhost:8501`.
Testé avec Python 3.12 et 3.14.

Pour rejouer les vérifications de formules :

```bash
python -m pytest -q      # 270 tests
```

## Utilisation en quatre gestes

1. **Barre latérale** : choisir le type de position (achat ou vente, call ou put), la
   quantité et la taille de contrat, puis le contrat (K, T) et le marché (S₀, r, σ).
2. **Curseur de cours** : le déplacer fait bouger le point sur les deux graphiques et
   met à jour tous les chiffres, sans relancer le programme.
3. **Graphiques** : deux menus permettent de choisir ce que l'on trace — couverture en
   actions, delta de la position, delta unitaire, gamma de position ou gamma unitaire.
   Les graphiques sont interactifs : survol pour lire les valeurs, cliquer-glisser pour
   zoomer, double-clic pour revenir à l'échelle initiale.
4. **Encart de résultats** : prix unitaire, valeur de la position, delta, gamma, et la
   couverture énoncée en clair (« Acheter 64 actions »), puis l'ajustement à effectuer
   lorsque le cours passe de S₀ à S₁.
5. **Onglets** : données de marché (import Yahoo Finance), vérification des formules,
   portefeuille de plusieurs options.

## Onglets

| Onglet | Contenu |
|---|---|
| Couverture | Mode d'emploi, résultats, curseur de cours, graphiques au choix (couverture, delta de position, delta unitaire, gamma) |
| Données de marché | Import du cours et de la volatilité réalisée depuis Yahoo Finance, historique et volatilité glissante |
| Vérification des formules | Parité call-put, parité dérivée, gamma par différences finies, valeurs de référence |
| Portefeuille (bonus) | Plusieurs options sur le même sous-jacent, delta et gamma agrégés |

L'outil signale par ailleurs les positions dégénérées : lorsque le strike s'éloigne du
cours de plus de 50 % en log-moneyness, le delta devient quasi constant et le gamma quasi
nul — l'option se comporte alors comme un contrat à terme et la couverture ne bouge plus.

## Organisation du code

```
.
├── app.py                     interface Streamlit — aucun calcul financier
├── pricer/
│   ├── black_scholes.py       prix, delta, gamma ; fonctions vectorisées
│   ├── position.py            Position et Portfolio : valeur, sensibilités, couverture
│   ├── checks.py              relations de vérification, partagées par l'app et les tests
│   └── market_data.py         cours et volatilité réalisée via Yahoo Finance
├── tests/
│   ├── test_black_scholes.py  formules, parité, bornes, vectorisation, saisies invalides
│   ├── test_position.py       signes des quatre positions, couverture, ajustements
│   └── test_checks.py         les relations tiennent sur toute une grille de paramètres
├── requirements.txt
└── README.md
```

Le moteur est séparé de l'interface : les mêmes fonctions sont appelables depuis un
notebook, et les tests ne dépendent pas de Streamlit. Les contrôles affichés dans
l'onglet « Vérification » sont exactement ceux que rejoue `pytest` : une seule source
de vérité.

## Formules

Avec d₁ = [ln(S/K) + (r + σ²/2)T] / (σ√T) et d₂ = d₁ − σ√T :

| Grandeur | Call | Put |
|---|---|---|
| Prix | S·N(d₁) − K·e^(−rT)·N(d₂) | K·e^(−rT)·N(−d₂) − S·N(−d₁) |
| Delta | N(d₁) | N(d₁) − 1 |
| Gamma | φ(d₁) / (S·σ·√T) | identique au call |

**Delta unitaire et delta de position.** Δ est une dérivée, sans dimension : 0,54 par
exemple. Une position de quantité signée **q** (négative si vendue) a pour delta de
position q·Δ, exprimé en **nombre d'actions équivalentes**, et pour gamma q·Γ. La
couverture vaut −q·Δ : couvrir, c'est annuler le delta total. L'interface affiche les
deux niveaux séparément, et un sélecteur permet de tracer les courbes à l'échelle
unitaire ou à l'échelle de la position.

La taille de contrat (1 par défaut, 100 pour des contrats boursiers standards) multiplie
la quantité : 10 contrats de 100 titres correspondent à 1 000 options.

| Position | Delta | Gamma | Couverture |
|---|---|---|---|
| Achat de call | > 0 | > 0 | vendre des actions |
| Vente de call | < 0 | < 0 | acheter des actions |
| Achat de put | < 0 | > 0 | acheter des actions |
| Vente de put | > 0 | < 0 | vendre des actions |

## Vérification des formules

Les résultats ne sont pas seulement comparés à des valeurs attendues : ils sont
confrontés à des relations qui doivent être vraies **quelles que soient les formules
employées**.

| Contrôle | Relation | Tolérance |
|---|---|---|
| Parité call-put | C − P = S − K·e^(−rT) | 1e-10 |
| Parité dérivée | Δ_call − Δ_put = 1 | 1e-12 |
| Gamma, seconde méthode | Γ analytique = dérivée seconde du prix par différences finies | 1e-4 |
| Valeurs de référence (Hull) | call = 10,4506 et put = 5,5735 pour S = K = 100, T = 1, r = 5 %, σ = 20 % | 1e-4 |
| Signes des quatre positions | option achetée → gamma > 0 ; option vendue → gamma < 0 | — |
| Saisies invalides | σ, T ou quantité nuls ou négatifs, type inconnu → erreur explicite | — |

La parité découle de la seule absence d'arbitrage : un call acheté et un put vendu
paient S − K dans tous les scénarios, flux que l'on réplique en achetant l'action et en
empruntant K·e^(−rT). **Limite connue** : elle est satisfaite quelles que soient les
valeurs de d₁ et d₂, puisque N(x) + N(−x) = 1. Elle contrôle donc la cohérence entre le
call et le put, mais pas la justesse de d₁ — d'où les deux autres familles de contrôles.

## Données de marché

Le cours et la volatilité peuvent être importés depuis Yahoo Finance (`yfinance`). Le
cours est observable directement ; la volatilité ne l'est pas et doit être estimée :
l'outil calcule l'écart-type annualisé des rendements logarithmiques sur une fenêtre
réglable (20 à 252 séances). Cette **volatilité réalisée** diffère de la **volatilité
implicite** cotée par le marché, qui est son anticipation.

Le module est isolé : si le réseau est indisponible, seul cet onglet est affecté et la
saisie manuelle reste possible.

## Bonus implémentés

- Portefeuille de plusieurs options sur le même sous-jacent, avec delta et gamma agrégés
  et couverture globale (tableau éditable).
- Curseurs de volatilité et de maturité : les courbes se déforment en direct.
- Import du cours et de la volatilité en direct depuis Yahoo Finance, avec historique et
  volatilité glissante.

## Hypothèses et limites

Modèle de Black-Scholes : volatilité constante, pas de dividende, pas de coûts de
transaction, couverture ajustable en continu. En pratique, un réajustement discret laisse
une erreur de réplication qui ne disparaît jamais et ne décroît que comme 1/√N avec le
nombre N de réajustements. La volatilité estimée sur l'historique est de surcroît une
approximation de celle que cote le marché.

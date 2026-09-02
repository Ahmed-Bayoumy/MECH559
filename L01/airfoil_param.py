import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from dash import Dash, dcc, html, Input, Output


# ============================================================
# CST AIRFOIL FUNCTIONS
# ============================================================

def binomial(n, k):
    """Binomial coefficient."""
    from math import factorial
    return factorial(n) / (factorial(k) * factorial(n - k))


def bernstein_polynomial(x, i, n):
    """
    Bernstein polynomial:
        B_i^n(x) = C(n,i) x^i (1-x)^(n-i)
    """
    return binomial(n, i) * x**i * (1.0 - x)**(n - i)


def class_function(x, N1=0.5, N2=1.0):
    """
    CST class function.

    For a conventional airfoil:
        N1 = 0.5
        N2 = 1.0
    """
    return x**N1 * (1.0 - x)**N2


def shape_function(x, coefficients):
    """CST Bernstein shape function."""
    n = len(coefficients) - 1

    S = np.zeros_like(x)

    for i, Ai in enumerate(coefficients):
        S += Ai * bernstein_polynomial(x, i, n)

    return S


def cst_surface(x, coefficients, delta_te=0.0):
    """
    CST surface:
        y/c = C(x) S(x) + x * Delta_TE
    """
    C = class_function(x)
    S = shape_function(x, coefficients)

    return C * S + x * delta_te


def generate_airfoil(x, Au, Al, delta_te=0.0):
    """
    Generate upper and lower CST surfaces.

    Au = upper-surface CST coefficients
    Al = lower-surface CST coefficients
    """
    yu = cst_surface(
        x,
        Au,
        delta_te=+0.5 * delta_te
    )

    yl = cst_surface(
        x,
        Al,
        delta_te=-0.5 * delta_te
    )

    return yu, yl


# ============================================================
# INITIAL CST PARAMETRIZATION
# ============================================================

# Number of CST coefficients on each surface
N_COEFF = 5

# Example initial airfoil
Au0 = np.array([
    0.20,
    0.20,
    0.18,
    0.14,
    0.10
])

Al0 = np.array([
    -0.16,
    -0.12,
    -0.10,
    -0.08,
    -0.06
])

# Cosine spacing gives better leading-edge resolution
beta = np.linspace(0.0, np.pi, 300)

x = 0.5 * (1.0 - np.cos(beta))


# ============================================================
# DASH APP
# ============================================================

app = Dash(__name__)

app.layout = html.Div(

    [

        # ----------------------------------------------------
        # TITLE
        # ----------------------------------------------------

        html.H2(
            "Interactive CST Airfoil Parametrization",
            style={
                "textAlign": "center",
                "marginBottom": "10px"
            }
        ),

        html.Div(
            [
                "Drag the CST coefficients to dynamically modify "
                "the upper and lower airfoil surfaces."
            ],
            style={
                "textAlign": "center",
                "marginBottom": "20px",
                "color": "#555"
            }
        ),


        # ====================================================
        # MAIN LAYOUT
        # ====================================================

        html.Div(

            [

                # =================================================
                # LEFT: PLOT
                # =================================================

                html.Div(

                    [
                        dcc.Graph(
                            id="airfoil-plot",
                            style={
                                "height": "700px"
                            }
                        )
                    ],

                    style={
                        "width": "68%",
                        "display": "inline-block",
                        "verticalAlign": "top"
                    }

                ),


                # =================================================
                # RIGHT: CST CONTROLS
                # =================================================

                html.Div(

                    [

                        # ------------------------------------------
                        # Upper coefficients
                        # ------------------------------------------

                        html.H4("Upper-surface CST coefficients"),

                        *[
                            html.Div(

                                [

                                    html.Div(
                                        id=f"Au-label-{i}",
                                        style={
                                            "marginBottom": "2px"
                                        }
                                    ),

                                    dcc.Slider(
                                        id=f"Au-{i}",
                                        min=-0.4,
                                        max=0.4,
                                        step=0.005,
                                        value=float(Au0[i]),
                                        marks={
                                            -0.4: "-0.4",
                                            0.0: "0",
                                            0.4: "0.4"
                                        },
                                        tooltip={
                                            "placement": "bottom",
                                            "always_visible": False
                                        }
                                    )

                                ],

                                style={
                                    "marginBottom": "18px"
                                }

                            )

                            for i in range(N_COEFF)
                        ],


                        html.Hr(),


                        # ------------------------------------------
                        # Lower coefficients
                        # ------------------------------------------

                        html.H4("Lower-surface CST coefficients"),

                        *[
                            html.Div(

                                [

                                    html.Div(
                                        id=f"Al-label-{i}",
                                        style={
                                            "marginBottom": "2px"
                                        }
                                    ),

                                    dcc.Slider(
                                        id=f"Al-{i}",
                                        min=-0.4,
                                        max=0.4,
                                        step=0.005,
                                        value=float(Al0[i]),
                                        marks={
                                            -0.4: "-0.4",
                                            0.0: "0",
                                            0.4: "0.4"
                                        },
                                        tooltip={
                                            "placement": "bottom",
                                            "always_visible": False
                                        }
                                    )

                                ],

                                style={
                                    "marginBottom": "18px"
                                }

                            )

                            for i in range(N_COEFF)
                        ],

                    ],

                    style={
                        "width": "30%",
                        "display": "inline-block",
                        "verticalAlign": "top",
                        "padding": "15px",
                        "boxSizing": "border-box"
                    }

                )

            ]

        )

    ],

    style={
        "fontFamily": "Arial",
        "margin": "20px"
    }

)


# ============================================================
# CALLBACK INPUTS
# ============================================================

slider_inputs = (
    [Input(f"Au-{i}", "value") for i in range(N_COEFF)]
    +
    [Input(f"Al-{i}", "value") for i in range(N_COEFF)]
)


# ============================================================
# CALLBACK
# ============================================================

@app.callback(

    [
        Output("airfoil-plot", "figure")
    ]

    +

    [
        Output(f"Au-label-{i}", "children")
        for i in range(N_COEFF)
    ]

    +

    [
        Output(f"Al-label-{i}", "children")
        for i in range(N_COEFF)
    ],

    slider_inputs

)
def update_airfoil(*values):

    # --------------------------------------------------------
    # Extract coefficients
    # --------------------------------------------------------

    Au = np.array(values[:N_COEFF])

    Al = np.array(
        values[N_COEFF:]
    )

    # --------------------------------------------------------
    # Generate airfoil
    # --------------------------------------------------------

    yu, yl = generate_airfoil(
        x,
        Au,
        Al
    )

    # ========================================================
    # CST KNOT LOCATIONS
    # ========================================================

    # Chordwise locations associated with CST coefficients
    x_knots = np.linspace(0.0, 1.0, N_COEFF)

    # Evaluate upper/lower surfaces at knot locations
    yu_knots = cst_surface(
        x_knots,
        Au,
        delta_te=0.0
    )

    yl_knots = cst_surface(
        x_knots,
        Al,
        delta_te=0.0
    )

    # --------------------------------------------------------
    # CST shape functions
    # --------------------------------------------------------

    Su = shape_function(x, Au)
    Sl = shape_function(x, Al)

    C = class_function(x)

    # --------------------------------------------------------
    # Create subplots
    # --------------------------------------------------------

    fig = make_subplots(

        rows=2,
        cols=2,

        specs=[
            [
                {"colspan": 2},
                None
            ],
            [
                {},
                {}
            ]
        ],

        subplot_titles=(

            "CST Airfoil Geometry",

            "CST Shape Functions",

            "Bernstein Basis Functions"

        ),

        vertical_spacing=0.15

    )

    # ========================================================
    # SUBPLOT 1 — AIRFOIL
    # ========================================================

    fig.add_trace(

        go.Scatter(

            x=x,
            y=yu,

            mode="lines",

            name="Upper surface",

            line=dict(
                width=3
            ),

            hovertemplate=
            "x/c = %{x:.4f}<br>"
            "y/c = %{y:.4f}<extra></extra>"

        ),

        row=1,
        col=1

    )


    fig.add_trace(

        go.Scatter(

            x=x,
            y=yl,

            mode="lines",

            name="Lower surface",

            line=dict(
                width=3
            ),

            hovertemplate=
            "x/c = %{x:.4f}<br>"
            "y/c = %{y:.4f}<extra></extra>"

        ),

        row=1,
        col=1

    )

    # ========================================================
    # UPPER CST KNOTS
    # ========================================================

    fig.add_trace(

        go.Scatter(

            x=x_knots,
            y=yu_knots,

            mode="lines+markers",

            name="Upper CST knots",

            line=dict(
                width=1,
                dash="dash"
            ),

            marker=dict(
                size=7,
                symbol="circle",
                line=dict(
                    width=1
                )
            ),

            customdata=np.arange(N_COEFF),

            hovertemplate=(
                "Upper knot Aᵘ%{customdata}<br>"
                "x/c = %{x:.3f}<br>"
                "y/c = %{y:.4f}"
                "<extra></extra>"
            )

        ),

        row=1,
        col=1

    )


    # ========================================================
    # LOWER CST KNOTS
    # ========================================================

    fig.add_trace(

        go.Scatter(

            x=x_knots,
            y=yl_knots,

            mode="lines+markers",

            name="Lower CST knots",

            line=dict(
                width=1,
                dash="dash"
            ),

            marker=dict(
                size=7,
                symbol="circle",
                line=dict(
                    width=1
                )
            ),

            customdata=np.arange(N_COEFF),

            hovertemplate=(
                "Lower knot Aˡ%{customdata}<br>"
                "x/c = %{x:.3f}<br>"
                "y/c = %{y:.4f}"
                "<extra></extra>"
            )

        ),

        row=1,
        col=1

    )


    # Airfoil fill
    x_fill = np.concatenate(
        [x, x[::-1]]
    )

    y_fill = np.concatenate(
        [yu, yl[::-1]]
    )

    fig.add_trace(

        go.Scatter(

            x=x_fill,
            y=y_fill,

            fill="toself",

            fillcolor="rgba(100,100,100,0.12)",

            line=dict(
                color="rgba(0,0,0,0)"
            ),

            hoverinfo="skip",

            showlegend=False

        ),

        row=1,
        col=1

    )


    # ========================================================
    # SUBPLOT 2 — SHAPE FUNCTIONS
    # ========================================================

    fig.add_trace(

        go.Scatter(

            x=x,
            y=Su,

            mode="lines",

            name="Sᵤ(x)",

            line=dict(
                width=2
            )

        ),

        row=2,
        col=1

    )


    fig.add_trace(

        go.Scatter(

            x=x,
            y=Sl,

            mode="lines",

            name="Sₗ(x)",

            line=dict(
                width=2
            )

        ),

        row=2,
        col=1

    )


    # ========================================================
    # SUBPLOT 3 — BERNSTEIN POLYNOMIALS
    # ========================================================

    n = N_COEFF - 1

    for i in range(N_COEFF):

        B = bernstein_polynomial(
            x,
            i,
            n
        )

        fig.add_trace(

            go.Scatter(

                x=x,
                y=B,

                mode="lines",

                name=f"B{i}",

                line=dict(
                    width=1.5
                )

            ),

            row=2,
            col=2

        )


    # ========================================================
    # AXIS FORMATTING
    # ========================================================

    fig.update_xaxes(

        title_text="x/c",

        range=[
            -0.02,
            1.02
        ],

        row=1,
        col=1

    )


    fig.update_yaxes(

        title_text="y/c",

        range=[
            -0.25,
            0.25
        ],

        scaleanchor="x",
        scaleratio=1,

        row=1,
        col=1

    )


    fig.update_xaxes(

        title_text="x/c",

        row=2,
        col=1

    )

    fig.update_yaxes(

        title_text="S(x)",

        row=2,
        col=1

    )


    fig.update_xaxes(

        title_text="x/c",

        row=2,
        col=2

    )

    fig.update_yaxes(

        title_text="Bᵢ(x)",

        row=2,
        col=2

    )


    # ========================================================
    # FIGURE FORMATTING
    # ========================================================

    fig.update_layout(

        height=680,

        margin=dict(
            l=60,
            r=30,
            t=60,
            b=50
        ),

        hovermode="closest",

        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5
        ),

        template="plotly_white"

    )


    # --------------------------------------------------------
    # Slider labels
    # --------------------------------------------------------

    upper_labels = [

        f"Aᵘ{i} = {Au[i]:+.4f}"

        for i in range(N_COEFF)

    ]

    lower_labels = [

        f"Aˡ{i} = {Al[i]:+.4f}"

        for i in range(N_COEFF)

    ]


    return [fig] + upper_labels + lower_labels


# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )
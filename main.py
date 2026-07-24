

!pip install ipywidgets plotly -q

import ipywidgets as widgets
from IPython.display import display, Markdown, clear_output
import plotly.graph_objects as go

# =====================================================================
# THEORY
# =====================================================================
display(Markdown(r"""
# Sabkha Collapse & Ground Aggressivity — screening tool

Sabkha soils form along the UAE's coastal sabkhas — sand, silt and clay deposited alongside
evaporite minerals (gypsum, anhydrite, halite). Those salts **cement the grains together**,
holding an unusually loose, open structure in place. When fresh water reaches that cement — a
rising water table, a leak, irrigation — the bonds dissolve and the soil **collapses into a
denser packing almost immediately**.

The same salts also **attack Portland cement** (sulfates) and **corrode reinforcing steel**
(chlorides) — chemistry problems that need a cement/cover strategy, not a bigger foundation.

**Formulas:**
$$e_L = \frac{LL}{100}\,G_s \qquad\qquad K = \frac{e_L}{e_0} \qquad\qquad \Delta H = \frac{CP}{100}\times H$$

*Methods: Jennings & Knight (1975) collapse-potential classification · Denisov coefficient of
subsidence for index-property screening · sulfate/chloride bands adapted from BRE Special Digest
1–style design-sulfate classification. Screening only — confirm with lab testing (ASTM D5333) and
the governing specification before design use.*
"""))

# =====================================================================
# CLASSIFICATION TABLES  (low, high, label, color)
# One row per severity band — change a number here to move a threshold,
# everywhere else in the notebook picks it up automatically.
# =====================================================================
CP_ZONES = [
    (0, 1, "None", "#3F8F5C"),
    (1, 5, "Moderate", "#D9A441"),
    (5, 10, "Trouble", "#C06A35"),
    (10, 20, "Severe", "#B23A2E"),
    (20, float("inf"), "Very severe", "#7A2020"),
]
K_ZONES = [
    (0, 0.5, "Highly collapsible", "#7A2020"),
    (0.5, 0.75, "Collapsible", "#B23A2E"),
    (0.75, 1.0, "Marginal", "#D9A441"),
    (1.0, float("inf"), "Non-collapsible", "#3F8F5C"),
]
SO4_ZONES = [
    (0, 0.24, "DS-1", "#3F8F5C"),
    (0.24, 0.6, "DS-2", "#D9A441"),
    (0.6, 1.2, "DS-3", "#C06A35"),
    (1.2, 2.3, "DS-4", "#B23A2E"),
    (2.3, float("inf"), "DS-5", "#7A2020"),
]
CL_ZONES = [
    (0, 0.2, "Low", "#3F8F5C"),
    (0.2, 0.5, "Moderate", "#D9A441"),
    (0.5, 1.0, "High", "#C06A35"),
    (1.0, float("inf"), "Severe", "#B23A2E"),
]
SO4_ADVICE = {
    "DS-1": "OPC (CEM I) acceptable with standard cover.",
    "DS-2": "Specify sulfate-resisting cement (SRPC) or CEM I combined with \u226550% GGBS / \u226525% PFA.",
    "DS-3": "SRPC + GGBS/PFA combination recommended, with increased nominal cover.",
    "DS-4": "High GGBS-content combination cement and enhanced protective measures required.",
    "DS-5": "Severe class \u2014 specialist protective measures and specification review required.",
}
CL_ADVICE = {
    "Low": "Standard cover and mix design are typically adequate.",
    "Moderate": "Check cover and w/c ratio against the project exposure class.",
    "High": "Increase nominal cover and consider a corrosion-inhibiting admixture.",
    "Severe": "High corrosion risk \u2014 consider coated bar, increased cover, and a barrier system.",
}


def classify(value, zones):
    for lo, hi, label, color in zones:
        if lo <= value < hi:
            return lo, hi, label, color
    return zones[-1]


def range_lines(zones, fmt):
    lines = []
    for i, (lo, hi, label, color) in enumerate(zones):
        if i == 0:
            rng = f"< {fmt(hi)}"
        elif hi == float("inf"):
            rng = f"\u2265 {fmt(lo)}"
        else:
            rng = f"{fmt(lo)} \u2013 {fmt(hi)}"
        lines.append(f"- **{label}** — {rng}")
    return "\n".join(lines)


def make_gauge(value, zones, axis_max, title, suffix=""):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        number={"suffix": suffix},
        title={"text": title},
        gauge={
            "axis": {"range": [0, axis_max]},
            "bar": {"color": "#333333", "thickness": 0.25},
            "steps": [{"range": [lo, min(hi, axis_max)], "color": color}
                      for lo, hi, label, color in zones],
        },
    ))
    fig.update_layout(height=260, margin=dict(l=25, r=25, t=50, b=10))
    return fig


# =====================================================================
# COLLAPSE POTENTIAL — widgets
# =====================================================================
cp_mode = widgets.RadioButtons(
    options=["Lab collapse data (CP%)", "Screen from index properties"],
    description="Mode:")

cp_val = widgets.FloatText(value=8.0, description="CP (%):")
H_val = widgets.FloatText(value=3.0, description="H (m):")
LL_val = widgets.FloatText(value=35.0, description="LL (%):")
Gs_val = widgets.FloatText(value=2.70, description="Gs:")
e0_val = widgets.FloatText(value=1.10, description="e\u2080:")

lab_box = widgets.VBox([cp_val, H_val])
screen_box = widgets.VBox([LL_val, Gs_val, e0_val])
screen_box.layout.display = "none"  # hidden until "Screen" mode picked

def on_mode_change(change):
    if change["new"].startswith("Lab"):
        lab_box.layout.display = "flex"
        screen_box.layout.display = "none"
    else:
        lab_box.layout.display = "none"
        screen_box.layout.display = "flex"

cp_mode.observe(on_mode_change, names="value")

cp_btn = widgets.Button(description="Calculate", button_style="success")
cp_out = widgets.Output()

def on_cp_click(b):
    with cp_out:
        clear_output()
        if cp_mode.value.startswith("Lab"):
            cp, H = cp_val.value, H_val.value
            lo, hi, label, color = classify(cp, CP_ZONES)
            settlement = (cp / 100) * H * 1000
            display(make_gauge(cp, CP_ZONES, 25, "Collapse severity", "%"))
            display(Markdown(
                f"**{label} — Jennings & Knight**  \n"
                f"CP = {cp:.1f}% over H = {H:.1f} m  \n"
                f"Estimated additional settlement on wetting ≈ **{settlement:.0f} mm**.\n\n"
                + range_lines(CP_ZONES, lambda v: f"{v:.0f}%")
            ))
        else:
            LL, Gs, e0 = LL_val.value, Gs_val.value, e0_val.value
            eL = (LL / 100) * Gs
            K = eL / e0
            lo, hi, label, color = classify(K, K_ZONES)
            display(make_gauge(K, K_ZONES, 2.0, "Denisov coefficient, K"))
            display(Markdown(
                f"**{label} — Denisov screening**  \n"
                f"e_L = (LL/100)\u00b7Gs = {eL:.3f}   K = e_L/e\u2080 = {K:.2f}\n\n"
                + range_lines(K_ZONES, lambda v: f"{v:.2f}")
            ))

cp_btn.on_click(on_cp_click)

print("=" * 70)
print("COLLAPSE POTENTIAL")
display(widgets.VBox([cp_mode, lab_box, screen_box, cp_btn, cp_out]))

# =====================================================================
# GROUND AGGRESSIVITY — widgets
# =====================================================================
so4_val = widgets.FloatText(value=0.9, description="SO\u2084 (g/l):")
cl_val = widgets.FloatText(value=0.6, description="Cl\u207b (%):")
agg_btn = widgets.Button(description="Calculate", button_style="success")
agg_out = widgets.Output()

def on_agg_click(b):
    with agg_out:
        clear_output()
        so4, cl = so4_val.value, cl_val.value

        lo, hi, sLabel, sColor = classify(so4, SO4_ZONES)
        display(make_gauge(so4, SO4_ZONES, 3.5, "Sulfate design class", " g/l"))
        display(Markdown(
            f"**{sLabel} — Design Sulfate Class**  \n"
            f"SO\u2084 = {so4:.2f} g/l (2:1 extract)  \n"
            f"{SO4_ADVICE[sLabel]}\n\n"
            + range_lines(SO4_ZONES, lambda v: f"{v:.2f} g/l")
        ))

        lo, hi, cLabel, cColor = classify(cl, CL_ZONES)
        display(make_gauge(cl, CL_ZONES, 1.5, "Chloride corrosion risk", "%"))
        display(Markdown(
            f"**{cLabel} — Chloride risk**  \n"
            f"Cl\u207b = {cl:.2f}% by dry soil mass  \n"
            f"{CL_ADVICE[cLabel]}\n\n"
            + range_lines(CL_ZONES, lambda v: f"{v:.1f}%")
        ))

agg_btn.on_click(on_agg_click)

print("=" * 70)
print("GROUND AGGRESSIVITY")
display(widgets.VBox([so4_val, cl_val, agg_btn, agg_out]))

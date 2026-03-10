"""
Visualizations for the cohort pricing impact model.
"""
from __future__ import annotations
import plotly.graph_objects as go
import streamlit as st

from ui.cohort_engine import CohortScenario

STD_COLOR = "#1B6AC9"
LTV_COLOR = "#2ECC71"
DELTA_POS = "#27AE60"
DELTA_NEG = "#E74C3C"


def render_break_even_chart(
    std: CohortScenario, ltv: CohortScenario,
) -> None:
    """Cumulative margin over time with crossover point."""
    st.markdown("**Cumulative Margin Timeline**")

    years = [1, 2, 3]
    std_cum = []
    ltv_cum = []
    running_std = 0.0
    running_ltv = 0.0
    crossover_year = None

    for y in years:
        running_std += std.cohort_yearly[y].margin
        running_ltv += ltv.cohort_yearly[y].margin
        std_cum.append(running_std)
        ltv_cum.append(running_ltv)
        if crossover_year is None and running_ltv >= running_std:
            crossover_year = y

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=years, y=std_cum, mode="lines+markers+text",
        name="Standard", line=dict(color=STD_COLOR, width=3),
        text=[f"${v:,.0f}" for v in std_cum],
        textposition="top left", textfont=dict(size=11),
    ))
    fig.add_trace(go.Scatter(
        x=years, y=ltv_cum, mode="lines+markers+text",
        name="LTV Optimized", line=dict(color=LTV_COLOR, width=3),
        text=[f"${v:,.0f}" for v in ltv_cum],
        textposition="top right", textfont=dict(size=11),
    ))

    if crossover_year:
        fig.add_vline(
            x=crossover_year, line_dash="dash", line_color="#888",
            annotation_text=f"Break-even: Year {crossover_year}",
            annotation_position="top right",
        )

    fig.update_layout(
        xaxis_title="Year", yaxis_title="Cumulative Margin ($)",
        xaxis=dict(tickmode="array", tickvals=[1, 2, 3], ticktext=["Year 1", "Year 2", "Year 3"]),
        yaxis=dict(tickformat="$,.0f"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(t=50, b=40), height=400,
    )
    st.plotly_chart(fig, use_container_width=True)


def render_margin_bars(
    std: CohortScenario, ltv: CohortScenario,
) -> None:
    """Side-by-side margin bars per year."""
    st.markdown("**Annual Margin Comparison**")

    years = [1, 2, 3]
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=[f"Year {y}" for y in years],
        y=[std.cohort_yearly[y].margin for y in years],
        name="Standard", marker_color=STD_COLOR,
        text=[f"${std.cohort_yearly[y].margin:,.0f}" for y in years],
        textposition="auto", textfont=dict(color="white"),
    ))
    fig.add_trace(go.Bar(
        x=[f"Year {y}" for y in years],
        y=[ltv.cohort_yearly[y].margin for y in years],
        name="LTV Optimized", marker_color=LTV_COLOR,
        text=[f"${ltv.cohort_yearly[y].margin:,.0f}" for y in years],
        textposition="auto", textfont=dict(color="white"),
    ))
    fig.update_layout(
        barmode="group", yaxis=dict(tickformat="$,.0f"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(t=50, b=40), height=380,
    )
    st.plotly_chart(fig, use_container_width=True)


def render_revenue_composition(
    std: CohortScenario, ltv: CohortScenario,
) -> None:
    """Stacked bar showing revenue mix by year for both scenarios side by side."""
    st.markdown("**Revenue Composition by Year**")

    categories = ["SaaS", "CC", "ACH", "Float", "Impl Fee"]
    colors = ["#3498DB", "#1B6AC9", "#2980B9", "#1ABC9C", "#95A5A6"]

    def _year_vals(s: CohortScenario, y: int) -> list[float]:
        cy = s.cohort_yearly[y]
        return [cy.saas_revenue, cy.cc_revenue, cy.ach_revenue,
                cy.float_income, cy.impl_fee_revenue]

    x_labels = [
        "Std Y1", "LTV Y1",
        "Std Y2", "LTV Y2",
        "Std Y3", "LTV Y3",
    ]

    all_vals: list[list[float]] = []
    for y in (1, 2, 3):
        all_vals.append(_year_vals(std, y))
        all_vals.append(_year_vals(ltv, y))

    fig = go.Figure()
    for i, cat in enumerate(categories):
        y_vals = [bar[i] for bar in all_vals]
        texts = [f"${v:,.0f}" if v > 50_000 else "" for v in y_vals]
        fig.add_trace(go.Bar(
            x=x_labels, y=y_vals,
            name=cat, marker_color=colors[i],
            text=texts, textposition="inside",
            textfont=dict(color="white", size=13),
        ))

    fig.update_layout(
        barmode="stack",
        yaxis=dict(tickformat="$,.0f", tickfont=dict(size=14)),
        xaxis=dict(tickfont=dict(size=14)),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=13)),
        margin=dict(t=50, b=40), height=650,
    )

    for x_pos in [1.5, 3.5]:
        fig.add_vline(x=x_pos, line_dash="dot", line_color="#ccc", line_width=1)

    st.plotly_chart(fig, use_container_width=True)


def render_metric_comparison_bars(
    std: CohortScenario, ltv: CohortScenario,
) -> None:
    """Win Rate, Margin %, Take Rate comparison bars."""

    metrics = [
        ("Win Rate", std.win_rate * 100, ltv.win_rate * 100, "%"),
        ("Margin %", std.three_year_margin_pct * 100, ltv.three_year_margin_pct * 100, "%"),
        ("Take Rate", std.three_year_take_rate * 100, ltv.three_year_take_rate * 100, "%"),
    ]

    cols = st.columns(3)
    for i, (label, std_val, ltv_val, suffix) in enumerate(metrics):
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=["Standard", "LTV Optimized"],
            y=[std_val, ltv_val],
            marker_color=[STD_COLOR, LTV_COLOR],
            text=[f"{std_val:.1f}{suffix}", f"{ltv_val:.1f}{suffix}"],
            textposition="auto", textfont=dict(color="white", size=13),
        ))
        fig.update_layout(
            title=dict(text=label, x=0.5),
            yaxis=dict(range=[0, max(std_val, ltv_val) * 1.25]),
            margin=dict(t=40, b=20, l=30, r=10), height=280,
            showlegend=False,
        )
        cols[i].plotly_chart(fig, use_container_width=True)


def render_insight_callouts(
    std: CohortScenario, ltv: CohortScenario,
) -> None:
    """Key insight messages."""
    deal_delta = ltv.deals_won - std.deals_won
    margin_delta = ltv.three_year_margin - std.three_year_margin

    y1_saas_delta = (
        ltv.cohort_yearly[1].saas_revenue - std.cohort_yearly[1].saas_revenue
    )
    y23_margin_delta = sum(
        ltv.cohort_yearly[y].margin - std.cohort_yearly[y].margin
        for y in [2, 3]
    )

    BOX = (
        '<div style="padding:12px 16px;background:#e8f4fd;border-left:4px solid #1B6AC9;'
        'border-radius:4px;margin-bottom:8px;color:#1B6AC9;font-size:0.95rem;">'
    )
    BOX_GREEN = (
        '<div style="padding:12px 16px;background:#e8f8ef;border-left:4px solid #2ECC71;'
        'border-radius:4px;margin-bottom:8px;color:#1a6e3a;font-size:0.95rem;">'
    )

    if deal_delta > 0:
        st.markdown(
            f'{BOX_GREEN}LTV pricing wins <b>{deal_delta} more deals</b> '
            f'({ltv.deals_won} vs {std.deals_won}) from the same pipeline.</div>',
            unsafe_allow_html=True,
        )

    y1_saas_str = f"{y1_saas_delta:+,.0f}"
    y23_margin_str = f"{y23_margin_delta:+,.0f}"
    net_margin_str = f"{margin_delta:+,.0f}"

    if y1_saas_delta < 0 and y23_margin_delta > 0:
        st.markdown(
            f'{BOX}Year 1 SaaS trade-off: <b>${y1_saas_str}</b> &nbsp;|&nbsp; '
            f'Years 2–3 margin recovery: <b>${y23_margin_str}</b> &nbsp;|&nbsp; '
            f'Net 3-year margin impact: <b>${net_margin_str}</b></div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f'{BOX}Net 3-year margin impact: <b>${net_margin_str}</b></div>',
            unsafe_allow_html=True,
        )

    std_processing_pct = sum(
        std.cohort_yearly[y].cc_revenue + std.cohort_yearly[y].ach_revenue
        for y in [1, 2, 3]
    ) / std.three_year_revenue * 100 if std.three_year_revenue > 0 else 0

    ltv_processing_pct = sum(
        ltv.cohort_yearly[y].cc_revenue + ltv.cohort_yearly[y].ach_revenue
        for y in [1, 2, 3]
    ) / ltv.three_year_revenue * 100 if ltv.three_year_revenue > 0 else 0

    st.markdown(
        f'{BOX}Revenue diversification: Processing makes up <b>{ltv_processing_pct:.0f}%</b> '
        f'of LTV revenue vs <b>{std_processing_pct:.0f}%</b> for Standard</div>',
        unsafe_allow_html=True,
    )

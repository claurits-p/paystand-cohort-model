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
    """Stacked bar showing revenue mix for both scenarios (3-year total)."""
    st.markdown("**3-Year Revenue Composition**")

    categories = ["SaaS", "CC", "ACH", "Float", "Impl Fee"]

    def _totals(s: CohortScenario) -> list[float]:
        return [
            sum(s.cohort_yearly[y].saas_revenue for y in [1, 2, 3]),
            sum(s.cohort_yearly[y].cc_revenue for y in [1, 2, 3]),
            sum(s.cohort_yearly[y].ach_revenue for y in [1, 2, 3]),
            sum(s.cohort_yearly[y].float_income for y in [1, 2, 3]),
            sum(s.cohort_yearly[y].impl_fee_revenue for y in [1, 2, 3]),
        ]

    std_vals = _totals(std)
    ltv_vals = _totals(ltv)
    colors = ["#3498DB", "#1B6AC9", "#2980B9", "#1ABC9C", "#95A5A6"]

    fig = go.Figure()
    for i, cat in enumerate(categories):
        fig.add_trace(go.Bar(
            x=["Standard", "LTV Optimized"],
            y=[std_vals[i], ltv_vals[i]],
            name=cat, marker_color=colors[i],
            text=[f"${std_vals[i]:,.0f}", f"${ltv_vals[i]:,.0f}"],
            textposition="inside", textfont=dict(color="white", size=10),
        ))

    fig.update_layout(
        barmode="stack", yaxis=dict(tickformat="$,.0f"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(t=50, b=40), height=420,
    )
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

    if deal_delta > 0:
        st.success(
            f"LTV pricing wins **{deal_delta} more deals** "
            f"({ltv.deals_won} vs {std.deals_won}) from the same {std.deals_won + deal_delta + (std.deals_won + deal_delta - ltv.deals_won)} pipeline."
        )

    if y1_saas_delta < 0 and y23_margin_delta > 0:
        st.info(
            f"Year 1 SaaS trade-off: **${y1_saas_delta:+,.0f}** | "
            f"Years 2-3 margin recovery: **${y23_margin_delta:+,.0f}** | "
            f"Net 3-year margin impact: **${margin_delta:+,.0f}**"
        )
    else:
        st.info(f"Net 3-year margin impact: **${margin_delta:+,.0f}**")

    std_processing_pct = sum(
        std.cohort_yearly[y].cc_revenue + std.cohort_yearly[y].ach_revenue
        for y in [1, 2, 3]
    ) / std.three_year_revenue * 100 if std.three_year_revenue > 0 else 0

    ltv_processing_pct = sum(
        ltv.cohort_yearly[y].cc_revenue + ltv.cohort_yearly[y].ach_revenue
        for y in [1, 2, 3]
    ) / ltv.three_year_revenue * 100 if ltv.three_year_revenue > 0 else 0

    st.info(
        f"Revenue diversification: Processing makes up **{ltv_processing_pct:.0f}%** "
        f"of LTV revenue vs **{std_processing_pct:.0f}%** for Standard"
    )

"""
Display components for cohort comparison: summary metrics, year-by-year
side-by-side table, delta row, and pricing details.
"""
from __future__ import annotations
import pandas as pd
import streamlit as st

from ui.cohort_engine import CohortScenario


def render_summary_metrics(
    std: CohortScenario, ltv: CohortScenario,
) -> None:
    """Top-level summary cards comparing both scenarios."""

    st.subheader("Cohort Impact Summary")

    deal_delta = ltv.deals_won - std.deals_won
    rev_delta = ltv.three_year_revenue - std.three_year_revenue
    margin_delta = ltv.three_year_margin - std.three_year_margin
    mpct_delta = (ltv.three_year_margin_pct - std.three_year_margin_pct) * 100

    tr_delta = (ltv.three_year_take_rate - std.three_year_take_rate) * 100

    cols = st.columns(5)
    cols[0].metric(
        "Additional Deals Won",
        f"{ltv.deals_won} vs {std.deals_won}",
        delta=f"{deal_delta:+d} deals",
    )
    cols[1].metric(
        "3-Year Revenue Delta",
        f"${ltv.three_year_revenue:,.0f} vs ${std.three_year_revenue:,.0f}",
        delta=f"${rev_delta:+,.0f}",
    )
    cols[2].metric(
        "3-Year Margin Delta",
        f"${ltv.three_year_margin:,.0f} vs ${std.three_year_margin:,.0f}",
        delta=f"${margin_delta:+,.0f}",
    )
    cols[3].metric(
        "Margin % Shift",
        f"{ltv.three_year_margin_pct:.1%} vs {std.three_year_margin_pct:.1%}",
        delta=f"{mpct_delta:+.1f}pp",
    )
    cols[4].metric(
        "Take Rate Shift",
        f"{ltv.three_year_take_rate:.2%} vs {std.three_year_take_rate:.2%}",
        delta=f"{tr_delta:+.2f}pp",
    )


def render_scenario_header(scenario: CohortScenario) -> None:
    """Render a scenario header with key stats."""
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Deals Won", scenario.deals_won)
    c2.metric("Win Rate", f"{scenario.win_rate:.0%}")
    c3.metric("3-Year Revenue", f"${scenario.three_year_revenue:,.0f}")
    c4.metric("3-Year Margin", f"${scenario.three_year_margin:,.0f}")


def _yearly_df(scenario: CohortScenario) -> pd.DataFrame:
    """Build a year-by-year DataFrame for a cohort scenario."""
    rows = []
    for y in [1, 2, 3]:
        cy = scenario.cohort_yearly[y]
        rows.append({
            "Year": str(y),
            "SaaS Rev": f"${cy.saas_revenue:,.0f}",
            "Impl Fee": f"${cy.impl_fee_revenue:,.0f}",
            "CC Rev": f"${cy.cc_revenue:,.0f}",
            "ACH Rev": f"${cy.ach_revenue:,.0f}",
            "Float": f"${cy.float_income:,.0f}",
            "Total Rev": f"${cy.total_revenue:,.0f}",
            "Total Cost": f"${cy.total_cost:,.0f}",
            "Margin": f"${cy.margin:,.0f}",
            "Margin %": f"{cy.margin_pct:.1%}",
            "Take Rate": f"{cy.take_rate:.2%}",
        })

    total_rev = sum(scenario.cohort_yearly[y].total_revenue for y in [1, 2, 3])
    total_cost = sum(scenario.cohort_yearly[y].total_cost for y in [1, 2, 3])
    total_margin = total_rev - total_cost
    total_vol = sum(
        scenario.cohort_yearly[y].total_revenue / scenario.cohort_yearly[y].take_rate
        for y in [1, 2, 3] if scenario.cohort_yearly[y].take_rate > 0
    )
    rows.append({
        "Year": "Total",
        "SaaS Rev": f"${sum(scenario.cohort_yearly[y].saas_revenue for y in [1,2,3]):,.0f}",
        "Impl Fee": f"${sum(scenario.cohort_yearly[y].impl_fee_revenue for y in [1,2,3]):,.0f}",
        "CC Rev": f"${sum(scenario.cohort_yearly[y].cc_revenue for y in [1,2,3]):,.0f}",
        "ACH Rev": f"${sum(scenario.cohort_yearly[y].ach_revenue for y in [1,2,3]):,.0f}",
        "Float": f"${sum(scenario.cohort_yearly[y].float_income for y in [1,2,3]):,.0f}",
        "Total Rev": f"${total_rev:,.0f}",
        "Total Cost": f"${total_cost:,.0f}",
        "Margin": f"${total_margin:,.0f}",
        "Margin %": f"{total_margin / total_rev:.1%}" if total_rev > 0 else "0.0%",
        "Take Rate": f"{total_rev / total_vol:.2%}" if total_vol > 0 else "0.00%",
    })
    return pd.DataFrame(rows)


def render_side_by_side_tables(
    std: CohortScenario, ltv: CohortScenario,
) -> None:
    """Year-by-year tables for each scenario, side by side."""

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"**{std.name}** ({std.deals_won} deals)")
        df_std = _yearly_df(std)
        st.dataframe(df_std, use_container_width=True, hide_index=True)

    with col2:
        st.markdown(f"**{ltv.name}** ({ltv.deals_won} deals)")
        df_ltv = _yearly_df(ltv)
        st.dataframe(df_ltv, use_container_width=True, hide_index=True)


def render_delta_table(
    std: CohortScenario, ltv: CohortScenario,
) -> None:
    """Delta table showing the difference between LTV and Standard per year."""
    st.markdown("**Year-by-Year Delta (LTV Optimized − Standard)**")
    rows = []
    for y in [1, 2, 3]:
        s = std.cohort_yearly[y]
        l = ltv.cohort_yearly[y]
        rows.append({
            "Year": str(y),
            "Δ SaaS": f"${l.saas_revenue - s.saas_revenue:+,.0f}",
            "Δ CC": f"${l.cc_revenue - s.cc_revenue:+,.0f}",
            "Δ ACH": f"${l.ach_revenue - s.ach_revenue:+,.0f}",
            "Δ Float": f"${l.float_income - s.float_income:+,.0f}",
            "Δ Revenue": f"${l.total_revenue - s.total_revenue:+,.0f}",
            "Δ Cost": f"${l.total_cost - s.total_cost:+,.0f}",
            "Δ Margin": f"${l.margin - s.margin:+,.0f}",
            "Δ Margin %": f"{(l.margin_pct - s.margin_pct) * 100:+.1f}pp",
        })

    total_s_rev = sum(std.cohort_yearly[y].total_revenue for y in [1, 2, 3])
    total_l_rev = sum(ltv.cohort_yearly[y].total_revenue for y in [1, 2, 3])
    total_s_cost = sum(std.cohort_yearly[y].total_cost for y in [1, 2, 3])
    total_l_cost = sum(ltv.cohort_yearly[y].total_cost for y in [1, 2, 3])
    total_s_margin = total_s_rev - total_s_cost
    total_l_margin = total_l_rev - total_l_cost

    rows.append({
        "Year": "Total",
        "Δ SaaS": f"${sum(ltv.cohort_yearly[y].saas_revenue - std.cohort_yearly[y].saas_revenue for y in [1,2,3]):+,.0f}",
        "Δ CC": f"${sum(ltv.cohort_yearly[y].cc_revenue - std.cohort_yearly[y].cc_revenue for y in [1,2,3]):+,.0f}",
        "Δ ACH": f"${sum(ltv.cohort_yearly[y].ach_revenue - std.cohort_yearly[y].ach_revenue for y in [1,2,3]):+,.0f}",
        "Δ Float": f"${sum(ltv.cohort_yearly[y].float_income - std.cohort_yearly[y].float_income for y in [1,2,3]):+,.0f}",
        "Δ Revenue": f"${total_l_rev - total_s_rev:+,.0f}",
        "Δ Cost": f"${total_l_cost - total_s_cost:+,.0f}",
        "Δ Margin": f"${total_l_margin - total_s_margin:+,.0f}",
        "Δ Margin %": f"{((total_l_margin / total_l_rev if total_l_rev else 0) - (total_s_margin / total_s_rev if total_s_rev else 0)) * 100:+.1f}pp",
    })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def render_pricing_comparison(
    std: CohortScenario, ltv: CohortScenario,
) -> None:
    """Side-by-side pricing lever comparison."""
    st.markdown("**Pricing Decisions Comparison (Per Deal)**")

    s = std.per_deal_pricing
    l = ltv.per_deal_pricing

    def _ach_desc(p):
        if p.ach_mode == "fixed_fee":
            return f"${p.ach_fixed_fee:.2f} fixed"
        elif p.ach_mode == "capped":
            return f"{p.ach_pct_rate:.2%} capped at ${p.ach_cap:.2f}"
        return f"{p.ach_pct_rate:.2%}"

    rows = [
        {"Lever": "SaaS Discount", "Standard": f"{s.saas_arr_discount_pct:.0%}", "LTV Optimized": f"{l.saas_arr_discount_pct:.0%}"},
        {"Lever": "Impl Fee Discount", "Standard": f"{s.impl_fee_discount_pct:.0%}", "LTV Optimized": f"{l.impl_fee_discount_pct:.0%}"},
        {"Lever": "CC Base Rate", "Standard": f"{s.cc_base_rate:.2%}", "LTV Optimized": f"{l.cc_base_rate:.2%}"},
        {"Lever": "AMEX Rate", "Standard": f"{s.cc_amex_rate:.2%}", "LTV Optimized": f"{l.cc_amex_rate:.2%}"},
        {"Lever": "ACH Pricing", "Standard": _ach_desc(s), "LTV Optimized": _ach_desc(l)},
        {"Lever": "Hold Days (CC/Bank/ACH)", "Standard": f"{s.hold_days_cc}/{s.hold_days_bank}/{s.hold_days_ach}", "LTV Optimized": f"{l.hold_days_cc}/{l.hold_days_bank}/{l.hold_days_ach}"},
        {"Lever": "SaaS ARR (Y1)", "Standard": f"${s.effective_saas_arr:,.0f}", "LTV Optimized": f"${l.effective_saas_arr:,.0f}"},
    ]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def render_per_deal_comparison(
    std: CohortScenario, ltv: CohortScenario,
) -> None:
    """Per-deal economics comparison so the SaaS trade-off is visible."""
    st.markdown("**Per-Deal Economics (Single Average Deal)**")

    rows = []
    for y in [1, 2, 3]:
        sy = std.per_deal_yearly[y]
        ly = ltv.per_deal_yearly[y]
        rows.append({
            "Year": str(y),
            "Std SaaS": f"${sy.saas_revenue:,.0f}",
            "LTV SaaS": f"${ly.saas_revenue:,.0f}",
            "Δ SaaS": f"${ly.saas_revenue - sy.saas_revenue:+,.0f}",
            "Std Revenue": f"${sy.total_revenue:,.0f}",
            "LTV Revenue": f"${ly.total_revenue:,.0f}",
            "Δ Revenue": f"${ly.total_revenue - sy.total_revenue:+,.0f}",
            "Std Margin": f"${sy.margin:,.0f}",
            "LTV Margin": f"${ly.margin:,.0f}",
            "Δ Margin": f"${ly.margin - sy.margin:+,.0f}",
        })

    std_3yr = sum(std.per_deal_yearly[y].total_revenue for y in [1, 2, 3])
    ltv_3yr = sum(ltv.per_deal_yearly[y].total_revenue for y in [1, 2, 3])
    std_3yr_m = sum(std.per_deal_yearly[y].margin for y in [1, 2, 3])
    ltv_3yr_m = sum(ltv.per_deal_yearly[y].margin for y in [1, 2, 3])
    std_3yr_s = sum(std.per_deal_yearly[y].saas_revenue for y in [1, 2, 3])
    ltv_3yr_s = sum(ltv.per_deal_yearly[y].saas_revenue for y in [1, 2, 3])
    rows.append({
        "Year": "Total",
        "Std SaaS": f"${std_3yr_s:,.0f}",
        "LTV SaaS": f"${ltv_3yr_s:,.0f}",
        "Δ SaaS": f"${ltv_3yr_s - std_3yr_s:+,.0f}",
        "Std Revenue": f"${std_3yr:,.0f}",
        "LTV Revenue": f"${ltv_3yr:,.0f}",
        "Δ Revenue": f"${ltv_3yr - std_3yr:+,.0f}",
        "Std Margin": f"${std_3yr_m:,.0f}",
        "LTV Margin": f"${ltv_3yr_m:,.0f}",
        "Δ Margin": f"${ltv_3yr_m - std_3yr_m:+,.0f}",
    })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    y1_saas_loss = ltv.per_deal_yearly[1].saas_revenue - std.per_deal_yearly[1].saas_revenue
    y1_rev_delta = ltv.per_deal_yearly[1].total_revenue - std.per_deal_yearly[1].total_revenue
    direction = "increases" if y1_rev_delta > 0 else "decreases"
    deal_delta = ltv.deals_won - std.deals_won
    st.markdown(
        f'<p style="color:#6c757d;font-size:0.85rem;">'
        f'Per deal, Y1 SaaS drops by <b>${y1_saas_loss:+,.0f}</b> due to higher discount, '
        f'but per-deal total revenue {direction} by '
        f'<b>${y1_rev_delta:+,.0f}</b> from processing/float. '
        f'At cohort scale, LTV wins <b>{deal_delta} more deals</b>, '
        f'multiplying the processing upside.</p>',
        unsafe_allow_html=True,
    )

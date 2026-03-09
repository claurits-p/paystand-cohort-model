"""
Paystand Cohort Pricing Impact Model

Compares Standard pricing vs LTV-Optimized pricing applied to a full
deal cohort, showing 3-year financials, break-even, and revenue impact.
"""
import streamlit as st

st.set_page_config(
    page_title="Paystand Cohort Impact Model",
    page_icon="paystand_logo.png",
    layout="wide",
)

from ui.cohort_inputs import render_cohort_inputs, render_standard_pricing
from ui.cohort_engine import run_cohort_comparison
from ui.cohort_display import (
    render_summary_metrics,
    render_scenario_header,
    render_side_by_side_tables,
    render_delta_table,
    render_pricing_comparison,
    render_per_deal_comparison,
)
from ui.cohort_charts import (
    render_break_even_chart,
    render_margin_bars,
    render_revenue_composition,
    render_metric_comparison_bars,
    render_insight_callouts,
)


def main():
    logo_col, title_col = st.columns([0.06, 0.94], gap="small")
    with logo_col:
        st.image("paystand_logo.png", width=55)
    with title_col:
        st.markdown(
            '<h1 style="color: #1B2A4A; margin-top: -5px;">'
            "Paystand Cohort Pricing Impact Model</h1>",
            unsafe_allow_html=True,
        )

    cohort = render_cohort_inputs()
    std_pricing = render_standard_pricing()

    if st.button("Run Cohort Analysis", type="primary", use_container_width=True):
        with st.spinner("Solving for target win rate and scaling to cohort..."):
            standard, ltv, solver_msg = run_cohort_comparison(
                deals_to_pricing=cohort["deals_to_pricing"],
                current_win_rate=cohort["current_win_rate"],
                avg_saas_arr=cohort["avg_saas_arr"],
                avg_impl_fee=cohort["avg_impl_fee"],
                avg_processing_volume=cohort["avg_processing_volume"],
                cc_pct=cohort["cc_pct"],
                conv_fee_today=cohort["conv_fee_today"],
                conv_fee_with_paystand=cohort["conv_fee_with_paystand"],
                standard_pricing_inputs=std_pricing,
                win_rate_increase=cohort["win_rate_increase"],
                quarterly_churn=cohort["quarterly_churn"],
            )

        _BOX_BLUE = (
            '<div style="padding:12px 16px;background:#e8f4fd;border-left:4px solid #1B6AC9;'
            'border-radius:4px;margin-bottom:8px;color:#1B6AC9;font-size:0.95rem;">'
        )
        _BOX_WARN = (
            '<div style="padding:12px 16px;background:#fff8e1;border-left:4px solid #f0a500;'
            'border-radius:4px;margin-bottom:8px;color:#7a5900;font-size:0.95rem;">'
        )

        if solver_msg:
            st.markdown(f'{_BOX_WARN}{solver_msg}</div>', unsafe_allow_html=True)

        if ltv.lever_changes:
            changes_parts = []
            for k, (old, new) in ltv.lever_changes.items():
                label = k.replace("_", " ").title()
                if "rate" in k or "pct" in k:
                    changes_parts.append(f"{label}: {old:.2%} → {new:.2%}")
                elif "fee" in k or "cap" in k:
                    changes_parts.append(f"{label}: ${old:.2f} → ${new:.2f}")
                else:
                    changes_parts.append(f"{label}: {old} → {new}")
            st.markdown(
                f'{_BOX_BLUE}<b>Pricing adjustments to reach target:</b> '
                + " | ".join(changes_parts) + '</div>',
                unsafe_allow_html=True,
            )

        st.divider()
        render_insight_callouts(standard, ltv)

        st.divider()
        render_summary_metrics(standard, ltv)

        st.divider()
        render_metric_comparison_bars(standard, ltv)

        st.divider()
        render_break_even_chart(standard, ltv)

        st.divider()
        render_margin_bars(standard, ltv)

        st.divider()
        render_revenue_composition(standard, ltv)

        st.divider()
        render_pricing_comparison(standard, ltv)

        st.divider()
        render_per_deal_comparison(standard, ltv)

        st.divider()
        render_side_by_side_tables(standard, ltv)

        st.divider()
        render_delta_table(standard, ltv)


if __name__ == "__main__":
    main()

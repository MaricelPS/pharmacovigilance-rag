"""Explorer tab: static dashboard with cohort overview and signal explorer."""
import polars as pl
import streamlit as st

from src.analytics.signals import compute_signal
from src.app.components.queries import (
    cohort_overview,
    reports_by_quarter,
    drug_distribution,
    demographics,
    signals_for_drug,
    available_glp1_drugs,
)
from src.app.components.plots import (
    forest_plot,
    quarterly_reports_bar,
    drug_distribution_bar,
    demographics_heatmap,
    compare_drugs_bar,
)


def render_explorer_tab():
    """Render the static dashboard with cohort stats and signal explorer."""
    st.header("Cohort explorer")

    # -------------------------------------------------------------------
    # Section 1: Overview metrics
    # -------------------------------------------------------------------
    st.subheader("Cohort overview")
    stats = cohort_overview()
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Reports", f"{stats['total_reports']:,}")
    col2.metric("Drug mentions", f"{stats['total_drug_mentions']:,}")
    col3.metric("Reactions", f"{stats['total_reactions']:,}")
    col4.metric("Unique PTs", f"{stats['unique_events']:,}")
    col5.metric("Serious", f"{stats['serious_reports']:,}")

    # -------------------------------------------------------------------
    # Section 2: Distribution charts
    # -------------------------------------------------------------------
    st.markdown("---")
    st.subheader("Distributions")
    tab_time, tab_drug, tab_demo = st.tabs(
        ["Over time", "By drug", "Demographics"]
    )
    with tab_time:
        st.plotly_chart(
            quarterly_reports_bar(reports_by_quarter()),
            use_container_width=True,
        )
    with tab_drug:
        st.plotly_chart(
            drug_distribution_bar(drug_distribution()),
            use_container_width=True,
        )
    with tab_demo:
        st.plotly_chart(
            demographics_heatmap(demographics()),
            use_container_width=True,
        )

    # -------------------------------------------------------------------
    # Section 3: Signal explorer
    # -------------------------------------------------------------------
    st.markdown("---")
    st.subheader("Signal explorer")

    drugs = available_glp1_drugs()
    col_a, col_b = st.columns([2, 1])
    with col_a:
        drug = st.selectbox("Active ingredient", drugs, index=0)
    with col_b:
        min_cases = st.slider("Minimum cases", 3, 50, 10)

    with st.spinner(f"Scanning signals for {drug}..."):
        signals_df = signals_for_drug(drug, min_cases=min_cases)

    if len(signals_df) == 0:
        st.info("No events meet the minimum-cases threshold.")
        return

    signals_only = signals_df.filter(pl.col("is_signal_ema"))
    st.caption(
        f"Scanned {len(signals_df)} events. "
        f"{len(signals_only)} meet EMA signal criteria (PRR≥2, χ²≥4, N≥3)."
    )

    # Top-signal table
    with st.expander("Top signals table", expanded=True):
        display_df = signals_only.head(30).select([
            "event_pt", "a", "prr", "prr_chi2",
            "ror", "ror_ci_low", "ror_ci_high",
            "ic", "ic_ci_low",
        ]).to_pandas().round(3)
        st.dataframe(display_df, use_container_width=True)

    # Forest plot
    st.plotly_chart(
        forest_plot(signals_only, top_n=20),
        use_container_width=True,
    )

    # -------------------------------------------------------------------
    # Section 4: Head-to-head drug comparison
    # -------------------------------------------------------------------
    st.markdown("---")
    st.subheader("Head-to-head comparison")

    col1, col2 = st.columns(2)
    with col1:
        selected_drugs = st.multiselect(
            "Drugs to compare",
            drugs,
            default=["semaglutide", "liraglutide", "tirzepatide"],
        )
    with col2:
        events_input = st.text_input(
            "MedDRA PTs (comma-separated)",
            value="Pancreatitis, Pancreatitis acute, Nausea, Vomiting",
        )
    events = [e.strip() for e in events_input.split(",") if e.strip()]

    if st.button("Compare") and len(selected_drugs) >= 2 and len(events) >= 1:
        rows = []
        with st.spinner("Computing metrics..."):
            for d in selected_drugs:
                for e in events:
                    m = compute_signal(d, e)
                    rows.append({
                        "drug_key": d, "event_pt": e,
                        "a": m.a, "prr": m.prr, "prr_chi2": m.prr_chi2,
                        "ror": m.ror, "ror_ci_low": m.ror_ci_low,
                        "ror_ci_high": m.ror_ci_high,
                        "ic": m.ic, "ic_ci_low": m.ic_ci_low,
                        "is_signal_ema": m.is_signal_ema,
                    })
        comp_df = pl.DataFrame(rows)
        st.dataframe(comp_df.to_pandas().round(3), use_container_width=True)
        st.plotly_chart(
            compare_drugs_bar(comp_df),
            use_container_width=True,
        )
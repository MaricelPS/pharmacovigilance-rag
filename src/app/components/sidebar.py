"""Sidebar with project info and disclaimers, rendered on every page."""
import streamlit as st


def render_sidebar():
    """Render the persistent sidebar shown on all tabs."""
    with st.sidebar:
        st.title("Pharmacovigilance RAG")
        st.caption("GLP-1 receptor agonists — FAERS 2024")

        st.markdown("---")
        st.subheader("About")
        st.markdown(
            "This dashboard combines classical disproportionality analysis "
            "(PRR, ROR, IC) with an LLM agent (Claude Sonnet 4.5) over the "
            "FDA Adverse Event Reporting System."
        )

        st.markdown("---")
        st.subheader("GLP-1 drugs in scope")
        st.markdown("""
        - Semaglutide (Ozempic, Wegovy, Rybelsus)
        - Liraglutide (Victoza, Saxenda)
        - Tirzepatide (Mounjaro, Zepbound)
        - Dulaglutide (Trulicity)
        - Exenatide (Byetta, Bydureon)
        - Lixisenatide (Adlyxin, Soliqua)
        """)

        st.markdown("---")
        st.warning(
            "**Disclaimer**: Spontaneous reports show association, not "
            "causation. Data is subject to underreporting, notoriety bias, "
            "and absence of a proper denominator. This tool does not "
            "replace clinical judgment or official regulatory guidance."
        )
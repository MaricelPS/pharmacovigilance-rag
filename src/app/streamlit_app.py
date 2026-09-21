"""Streamlit entry point for the Pharmacovigilance RAG dashboard."""
import sys
from pathlib import Path

# Add project root to sys.path so `src.*` imports work when launched via
# `streamlit run`, which does not add the project root by default.
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import streamlit as st

from src.app.components.sidebar import render_sidebar
from src.app.sections.chat import render_chat_tab
from src.app.sections.explorer import render_explorer_tab


st.set_page_config(
    page_title="Pharmacovigilance RAG — GLP-1 / FAERS 2024",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded",
)


def main():
    render_sidebar()

    st.title("Pharmacovigilance RAG Assistant")
    st.caption(
        "GLP-1 receptor agonists — FDA Adverse Event Reporting System, 2024"
    )

    tab_chat, tab_explorer = st.tabs(["💬 Chat with the agent", "📊 Explorer"])
    with tab_chat:
        render_chat_tab()
    with tab_explorer:
        render_explorer_tab()


if __name__ == "__main__":
    main()
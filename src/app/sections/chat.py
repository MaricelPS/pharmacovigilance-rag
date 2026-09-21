"""Chat tab: conversational interface to the pharmacovigilance agent."""
import streamlit as st

from src.rag.agent import ask


EXAMPLE_QUESTIONS = [
    "¿Qué señales de seguridad emergentes aparecen para semaglutida en 2024?",
    "¿Hay reportes de problemas hepáticos con tirzepatida?",
    "Comparame el perfil de pancreatitis entre semaglutida, liraglutida y tirzepatida.",
    "¿Aparece la señal de NAION con semaglutida en estos datos?",
    "¿Qué eventos serios se reportan más para GLP-1 en mayores de 65 años?",
]


def render_chat_tab():
    """Render the chat interface."""
    st.header("Ask the pharmacovigilance agent")
    st.markdown(
        "The agent has access to signal detection (PRR/ROR/IC), semantic "
        "search over MedDRA terms, and demographic filters on the GLP-1 "
        "cohort. Every claim it makes is grounded in FAERS 2024 data."
    )

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Example questions
    with st.expander("Example questions"):
        for q in EXAMPLE_QUESTIONS:
            if st.button(q, key=f"ex_{hash(q)}"):
                st.session_state.pending_question = q
                st.rerun()

    # Render previous messages
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Handle new question (either from input or example click)
    pending = st.session_state.pop("pending_question", None)
    prompt = pending or st.chat_input("Ask a question in Spanish or English...")

    if prompt:
        # Display user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Get agent response
        with st.chat_message("assistant"):
            with st.spinner("Querying FAERS..."):
                try:
                    answer = ask(prompt, verbose=False)
                except Exception as e:
                    answer = f"**Error querying the agent:** {e}"
            st.markdown(answer)
            st.session_state.messages.append(
                {"role": "assistant", "content": answer}
            )

    # Clear history button
    if st.session_state.messages:
        if st.button("Clear conversation"):
            st.session_state.messages = []
            st.rerun()
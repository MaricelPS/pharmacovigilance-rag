---
title: Pharmacovigilance RAG Assistant
emoji: 💊
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
pinned: false
license: mit
---

# Pharmacovigilance RAG Assistant

An LLM-powered assistant for exploring adverse event reports from the FDA
Adverse Event Reporting System (FAERS), focused on GLP-1 receptor agonists
(semaglutide, liraglutide, tirzepatide, dulaglutide, exenatide, lixisenatide).

## Features

- **Signal detection** using classical disproportionality metrics (PRR, ROR
  with 95% CI, Information Component).
- **Semantic search** over MedDRA Preferred Terms via Voyage AI embeddings.
- **Conversational agent** built on Claude Sonnet 4.5 with tool use.
- **Interactive dashboard** with cohort overview, forest plots, and
  head-to-head drug comparisons.

## Tech Stack

- Python 3.11
- PostgreSQL + pgvector (hosted on Supabase)
- Anthropic Claude Sonnet 4.5 (LLM agent)
- Voyage AI voyage-3 (embeddings)
- Streamlit (UI)
- Plotly (visualizations)

## Data

FDA Adverse Event Reporting System (FAERS), quarterly data 2024 Q1–Q4.
Cohort restricted to reports mentioning any GLP-1 receptor agonist:
72,835 unique reports, 5,058 unique MedDRA Preferred Terms.

## Live demo

Try the deployed app: **[https://pharmacovigilance-rag-tb2m67berfdccrlmtxpmep.streamlit.app/](https://pharmacovigilance-rag-tb2m67berfdccrlmtxpmep.streamlit.app/)**

Note: the app may take 30 seconds to wake up if it has been idle.

## Disclaimer

Spontaneous adverse event reports show **association, not causation**.
Data is subject to underreporting, notoriety bias, confounding by
indication, and absence of a proper denominator. This tool does **not**
replace clinical judgment or official regulatory guidance.
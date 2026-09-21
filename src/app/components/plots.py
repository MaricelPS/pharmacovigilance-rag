"""Plotly chart helpers for the pharmacovigilance dashboard."""
import polars as pl
import plotly.express as px
import plotly.graph_objects as go


COLOR_SIGNAL = "#d62728"       # Red for confirmed signals
COLOR_NON_SIGNAL = "#7f7f7f"   # Grey for non-signals


def forest_plot(df: pl.DataFrame, top_n: int = 20) -> go.Figure:
    """Forest plot of ROR with 95% CI for the top signals of a drug.

    Args:
        df: Signal scan results with columns ror, ror_ci_low, ror_ci_high,
            event_pt, a, is_signal_ema.
        top_n: How many events to display, ranked by IC in the caller.
    """
    d = df.head(top_n).sort("ror").to_pandas()

    fig = go.Figure()

    for _, row in d.iterrows():
        color = COLOR_SIGNAL if row["is_signal_ema"] else COLOR_NON_SIGNAL
        # CI whiskers
        fig.add_trace(go.Scatter(
            x=[row["ror_ci_low"], row["ror_ci_high"]],
            y=[row["event_pt"], row["event_pt"]],
            mode="lines",
            line=dict(color=color, width=2),
            showlegend=False,
            hoverinfo="skip",
        ))
        # Point estimate
        fig.add_trace(go.Scatter(
            x=[row["ror"]],
            y=[row["event_pt"]],
            mode="markers",
            marker=dict(color=color, size=10, symbol="diamond"),
            showlegend=False,
            hovertemplate=(
                f"<b>{row['event_pt']}</b><br>"
                f"n={row['a']}<br>"
                f"ROR={row['ror']:.2f} "
                f"(95% CI: {row['ror_ci_low']:.2f}-{row['ror_ci_high']:.2f})<br>"
                f"PRR={row['prr']:.2f}, IC={row['ic']:.2f}"
                "<extra></extra>"
            ),
        ))

    fig.add_vline(x=1, line_dash="dash", line_color="black", opacity=0.5)

    fig.update_layout(
        title=f"Top {top_n} signals — ROR with 95% CI",
        xaxis_title="Reporting Odds Ratio (log scale)",
        xaxis_type="log",
        yaxis_title="",
        height=max(400, 30 * len(d)),
        margin=dict(l=200),
        template="simple_white",
    )
    return fig


def quarterly_reports_bar(df: pl.DataFrame) -> go.Figure:
    """Bar chart of GLP-1 cohort reports per quarter."""
    d = df.to_pandas()
    fig = px.bar(
        d, x="faers_quarter", y="n_reports",
        text="n_reports",
        color_discrete_sequence=["#1f77b4"],
    )
    fig.update_traces(texttemplate="%{text:,}", textposition="outside")
    fig.update_layout(
        title="GLP-1 cohort reports per quarter",
        xaxis_title="Quarter",
        yaxis_title="Reports",
        template="simple_white",
    )
    return fig


def drug_distribution_bar(df: pl.DataFrame) -> go.Figure:
    """Horizontal bar chart of top GLP-1 brand names by report count."""
    d = df.sort("n_reports").to_pandas()
    fig = px.bar(
        d, x="n_reports", y="drugname",
        orientation="h", text="n_reports",
        color_discrete_sequence=["#2ca02c"],
    )
    fig.update_traces(texttemplate="%{text:,}", textposition="outside")
    fig.update_layout(
        title="Top GLP-1 drug names in FAERS 2024",
        xaxis_title="Report count",
        yaxis_title="",
        height=500,
        template="simple_white",
    )
    return fig


def demographics_heatmap(df: pl.DataFrame) -> go.Figure:
    """Heatmap of cohort demographics by age group and sex."""
    d = df.to_pandas().pivot(index="age_group", columns="sex", values="n_reports").fillna(0)
    fig = px.imshow(
        d, text_auto=True,
        color_continuous_scale="Blues",
        aspect="auto",
    )
    fig.update_layout(
        title="Cohort demographics: age group × sex",
        xaxis_title="Sex",
        yaxis_title="Age group",
        template="simple_white",
    )
    return fig


def compare_drugs_bar(df: pl.DataFrame) -> go.Figure:
    """Grouped bar chart comparing ROR across drugs for the same events."""
    d = df.to_pandas()
    fig = px.bar(
        d, x="event_pt", y="ror", color="drug_key",
        barmode="group",
        error_y=d["ror_ci_high"] - d["ror"],
        error_y_minus=d["ror"] - d["ror_ci_low"],
    )
    fig.add_hline(y=1, line_dash="dash", line_color="black", opacity=0.5)
    fig.update_layout(
        title="Head-to-head drug comparison — ROR with 95% CI",
        xaxis_title="",
        yaxis_title="Reporting Odds Ratio",
        yaxis_type="log",
        template="simple_white",
        xaxis_tickangle=-30,
    )
    return fig
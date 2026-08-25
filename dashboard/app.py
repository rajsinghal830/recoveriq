"""
RecoverIQ Dashboard
Streamlit UI for payment recovery analytics.

Displays:
- Recovery KPIs
- Recovery outcome breakdown
- Recovery rate by failure reason
- Recovery by failure type
- Full audit log
- Sidebar filters
- Optional auto-refresh
"""

import sys
import os
import time

import streamlit as st
import plotly.express as px
import pandas as pd


# ============================================================================
# PATH SETUP
# ============================================================================

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


# ============================================================================
# DATABASE IMPORT
# ============================================================================

from tools.audit_tools import (  # noqa: E402
    init_db,
    get_all_runs,
)


# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="RecoverIQ Dashboard",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================================
# INITIALIZE DATABASE
# IMPORTANT FOR STREAMLIT CLOUD
# ============================================================================

try:
    init_db()
except Exception as exc:
    st.error(f"Unable to initialize audit database: {exc}")
    st.stop()


# ============================================================================
# LOAD DATA
# ============================================================================

try:
    raw_runs = get_all_runs()

except Exception as exc:
    st.error(f"Unable to load audit data: {exc}")
    st.stop()


# ============================================================================
# EMPTY DATA STATE
# ============================================================================

if not raw_runs:

    with st.sidebar:
        st.markdown("## 💰 RecoverIQ")
        st.caption("v1.0.0")

    st.title("💰 RecoverIQ Dashboard")

    st.caption(
        "AI-powered payment recovery intelligence — "
        "real-time audit & analytics"
    )

    st.info(
        "🚀 No recovery runs yet.\n\n"
        "Run `python orchestrator.py` first."
    )

    st.stop()


# ============================================================================
# CREATE DATAFRAME
# ============================================================================

df_all = pd.DataFrame(raw_runs)


# ============================================================================
# EXPECTED COLUMNS
# ============================================================================

EXPECTED_COLUMNS = {
    "payment_id": "N/A",
    "customer_name": "Unknown",
    "amount": 0.0,
    "failure_reason": "unknown",
    "outcome": "PENDING",
    "amount_recovered": 0.0,
}


for column, default_value in EXPECTED_COLUMNS.items():

    if column not in df_all.columns:
        df_all[column] = default_value


# ============================================================================
# NORMALIZE DATA TYPES
# ============================================================================

df_all["amount"] = pd.to_numeric(
    df_all["amount"],
    errors="coerce",
).fillna(0.0)


df_all["amount_recovered"] = pd.to_numeric(
    df_all["amount_recovered"],
    errors="coerce",
).fillna(0.0)


df_all["outcome"] = (
    df_all["outcome"]
    .astype(str)
    .str.upper()
    .str.strip()
)


df_all["failure_reason"] = (
    df_all["failure_reason"]
    .astype(str)
    .str.lower()
    .str.strip()
)


# ============================================================================
# SIDEBAR
# ============================================================================

with st.sidebar:

    st.markdown("## 💰 RecoverIQ")
    st.caption("v1.0.0")

    st.divider()

    st.subheader("🔍 Filters")

    # ------------------------------------------------------------------------
    # Failure reason filter
    # ------------------------------------------------------------------------

    all_reasons = sorted(
        df_all["failure_reason"]
        .dropna()
        .unique()
        .tolist()
    )

    selected_reasons = st.multiselect(
        "Filter by Failure Reason",
        options=all_reasons,
        default=[],
        key="failure_reason_filter",
    )

    # ------------------------------------------------------------------------
    # Outcome filter
    # ------------------------------------------------------------------------

    all_outcomes = sorted(
        df_all["outcome"]
        .dropna()
        .unique()
        .tolist()
    )

    selected_outcomes = st.multiselect(
        "Filter by Outcome",
        options=all_outcomes,
        default=[],
        key="outcome_filter",
    )

    st.divider()

    # ------------------------------------------------------------------------
    # Auto refresh
    # ------------------------------------------------------------------------

    auto_refresh = st.checkbox(
        "🔄 Auto-refresh (5 s)",
        value=False,
    )


# ============================================================================
# APPLY FILTERS
# ============================================================================

df = df_all.copy()


if selected_reasons:

    df = df[
        df["failure_reason"].isin(selected_reasons)
    ]


if selected_outcomes:

    df = df[
        df["outcome"].isin(selected_outcomes)
    ]


# ============================================================================
# HEADER
# ============================================================================

st.title("💰 RecoverIQ Dashboard")

st.caption(
    "AI-powered payment recovery intelligence — "
    "real-time audit & analytics"
)


# ============================================================================
# FINAL OUTCOME FUNCTION
# ============================================================================

def get_final_outcome(group: pd.DataFrame) -> str:
    """
    Determine the final status of a payment.

    Priority:

        RECOVERED
        ESCALATED
        FAILED
        PENDING
    """

    outcomes = set(
        group["outcome"]
        .astype(str)
        .str.upper()
    )

    if "RECOVERED" in outcomes:
        return "RECOVERED"

    if "ESCALATED" in outcomes:
        return "ESCALATED"

    if "FAILED" in outcomes and "PENDING" not in outcomes:
        return "FAILED"

    return "PENDING"


# ============================================================================
# PAYMENT-LEVEL DATA
# ============================================================================

payment_df = (
    df.groupby(
        "payment_id",
        as_index=False,
    )
    .agg(
        customer_name=(
            "customer_name",
            "first",
        ),
        amount=(
            "amount",
            "max",
        ),
        failure_reason=(
            "failure_reason",
            "first",
        ),
        amount_recovered=(
            "amount_recovered",
            "max",
        ),
    )
)


# ============================================================================
# FINAL OUTCOME PER PAYMENT
# ============================================================================

final_outcomes = (
    df.groupby("payment_id")
    .apply(
        get_final_outcome,
        include_groups=False,
    )
    .reset_index(
        name="outcome"
    )
)


payment_df = payment_df.merge(
    final_outcomes,
    on="payment_id",
    how="left",
)


# ============================================================================
# KPI CALCULATIONS
# ============================================================================

total_payments = payment_df[
    "payment_id"
].nunique()


recovered_payment_ids = payment_df.loc[
    payment_df["outcome"] == "RECOVERED",
    "payment_id",
].unique()


total_recovered = len(
    recovered_payment_ids
)


recovery_rate = (
    total_recovered
    / total_payments
    * 100
    if total_payments > 0
    else 0.0
)


# ============================================================================
# RECOVERED AMOUNT
# ============================================================================

recovered_amounts = (
    payment_df[
        payment_df["payment_id"].isin(
            recovered_payment_ids
        )
    ]
    .groupby("payment_id")[
        "amount_recovered"
    ]
    .max()
)


total_amount_recovered = (
    recovered_amounts.sum()
)


# ============================================================================
# KPI CARDS
# ============================================================================

col1, col2, col3, col4 = st.columns(4)


with col1:

    st.metric(
        label="💳 Unique Payments",
        value=f"{total_payments:,}",
    )


with col2:

    st.metric(
        label="✅ Total Recovered",
        value=f"{total_recovered:,}",
        delta=f"+{total_recovered}",
    )


with col3:

    st.metric(
        label="📈 Recovery Rate",
        value=f"{recovery_rate:.1f}%",
    )


with col4:

    st.metric(
        label="💰 Amount Recovered (₹)",
        value=f"₹{total_amount_recovered:,.2f}",
    )


st.divider()


# ============================================================================
# CHARTS
# ============================================================================

chart_col1, chart_col2 = st.columns(2)


# ============================================================================
# RECOVERY OUTCOME BREAKDOWN
# ============================================================================

with chart_col1:

    st.subheader("🥧 Recovery Outcome Breakdown")

    outcome_counts = (
        payment_df["outcome"]
        .value_counts()
        .reset_index()
    )

    outcome_counts.columns = [
        "outcome",
        "count",
    ]

    OUTCOME_COLORS = {
        "RECOVERED": "#22c55e",
        "FAILED": "#ef4444",
        "PENDING": "#f59e0b",
        "ESCALATED": "#8b5cf6",
    }

    fig_pie = px.pie(
        outcome_counts,
        names="outcome",
        values="count",
        color="outcome",
        color_discrete_map=OUTCOME_COLORS,
        hole=0.45,
    )

    fig_pie.update_traces(
        textposition="inside",
        textinfo="percent+label",
    )

    fig_pie.update_layout(
        margin=dict(
            t=20,
            b=20,
            l=20,
            r=20,
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.2,
        ),
        showlegend=True,
    )

    st.plotly_chart(
        fig_pie,
        width="stretch",
    )


# ============================================================================
# RECOVERY RATE BY FAILURE REASON
# ============================================================================

with chart_col2:

    st.subheader("📊 Recovery Rate by Failure Reason")

    reason_df = (
        payment_df
        .groupby("failure_reason")
        .agg(
            total=(
                "payment_id",
                "nunique",
            ),
            recovered=(
                "outcome",
                lambda x: (
                    x == "RECOVERED"
                ).sum(),
            ),
        )
        .reset_index()
    )

    reason_df["recovery_rate_pct"] = (
        reason_df["recovered"]
        / reason_df["total"]
        * 100
    ).round(1)

    fig_bar = px.bar(
        reason_df,
        x="failure_reason",
        y="recovery_rate_pct",
        color="recovery_rate_pct",
        color_continuous_scale=[
            "#ef4444",
            "#f59e0b",
            "#22c55e",
        ],
        range_color=[0, 100],
        text="recovery_rate_pct",
        labels={
            "failure_reason": "Failure Reason",
            "recovery_rate_pct": "Recovery Rate (%)",
        },
    )

    fig_bar.update_traces(
        texttemplate="%{text:.1f}%",
        textposition="outside",
    )

    fig_bar.update_layout(
        margin=dict(
            t=20,
            b=20,
            l=20,
            r=20,
        ),
        coloraxis_showscale=False,
        xaxis_tickangle=-30,
        yaxis_range=[
            0,
            max(
                100,
                float(
                    reason_df[
                        "recovery_rate_pct"
                    ].max()
                ) + 10,
            ),
        ],
    )

    st.plotly_chart(
        fig_bar,
        width="stretch",
    )


st.divider()


# ============================================================================
# RECOVERY BY FAILURE TYPE
# ============================================================================

st.subheader("📋 Recovery by Failure Type")


summary_table = reason_df[
    [
        "failure_reason",
        "total",
        "recovered",
        "recovery_rate_pct",
    ]
].copy()


summary_table.columns = [
    "Failure Reason",
    "Unique Payments",
    "Recovered",
    "Recovery Rate (%)",
]


summary_table = (
    summary_table
    .sort_values(
        "Recovery Rate (%)",
        ascending=False,
    )
    .reset_index(drop=True)
)


st.dataframe(
    summary_table,
    width="stretch",
    hide_index=True,
)


st.divider()


# ============================================================================
# FULL AUDIT LOG
# ============================================================================

st.subheader("🗂️ Full Audit Log")


DISPLAY_COLUMNS = [
    "payment_id",
    "customer_name",
    "amount",
    "failure_reason",
    "outcome",
    "amount_recovered",
]


df_display = df[
    DISPLAY_COLUMNS
].copy()


# ============================================================================
# RENAME COLUMNS
# ============================================================================

df_display = df_display.rename(
    columns={
        "payment_id": "Payment ID",
        "customer_name": "Customer",
        "amount": "Amount (₹)",
        "failure_reason": "Failure Reason",
        "outcome": "Outcome",
        "amount_recovered": "Recovered (₹)",
    }
)


# ============================================================================
# CURRENCY FORMAT
# ============================================================================

df_display["Amount (₹)"] = (
    df_display["Amount (₹)"]
    .apply(
        lambda value:
        f"₹{value:,.2f}"
    )
)


df_display["Recovered (₹)"] = (
    df_display["Recovered (₹)"]
    .apply(
        lambda value:
        f"₹{value:,.2f}"
    )
)


# ============================================================================
# OUTCOME CELL STYLING
# ============================================================================

OUTCOME_BG = {

    "RECOVERED":
        "background-color: #d1fae5; "
        "color: #065f46;",

    "FAILED":
        "background-color: #fee2e2; "
        "color: #991b1b;",

    "PENDING":
        "background-color: #fef3c7; "
        "color: #92400e;",

    "ESCALATED":
        "background-color: #ede9fe; "
        "color: #5b21b6;",
}


def style_outcome(value):

    return OUTCOME_BG.get(
        str(value).upper(),
        "",
    )


styled_df = df_display.style.map(
    style_outcome,
    subset=["Outcome"],
)


st.dataframe(
    styled_df,
    width="stretch",
    hide_index=True,
)


# ============================================================================
# AUTO REFRESH
# ============================================================================

if auto_refresh:

    st.caption(
        "⏳ Auto-refreshing every 5 seconds..."
    )

    time.sleep(5)

    st.rerun()
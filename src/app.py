from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st


st.set_page_config(
    page_title="Startie Funnel Dashboard",
    page_icon="F",
    layout="wide",
)

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"

STAGE_CATALOG = {
    "signed_up": "Signed Up",
    "onboarding_started": "Onboarding Started",
    "onboarding_completed": "Onboarding Completed",
    "activated": "Activated (is_activated, 7D lesson_started >= 1)",
    "lesson_started": "Lesson Started",
    "lesson_completed": "Lesson Completed",
    "checkout_started": "Checkout Started",
    "subscribed": "Subscribed (plan_history)",
    "payment_completed": "Payment Completed",
    "retained_30d": "Retained 30D",
}

EVENT_STAGE_MAP = {
    "onboarding_started": "onboarding_started",
    "onboarding_completed": "onboarding_completed",
    "lesson_started": "lesson_started",
    "lesson_completed": "lesson_completed",
    "checkout_started": "checkout_started",
}

FUNNEL_TEMPLATES = {
    "Full Funnel": [
        "signed_up",
        "onboarding_started",
        "onboarding_completed",
        "activated",
        "lesson_completed",
        "checkout_started",
        "payment_completed",
    ],
    "Activation Funnel": [
        "signed_up",
        "onboarding_started",
        "onboarding_completed",
        "activated",
    ],
    "Monetization Funnel": [
        "signed_up",
        "lesson_completed",
        "checkout_started",
        "subscribed",
        "payment_completed",
    ],
}

SEGMENT_LABELS = {
    "acquisition_source": "Channel",
    "device_type": "Device",
    "is_activated": "Activated (is_activated v2)",
    "activation_segment": "Activation Segment",
    "trial_segment": "Trial Segment",
    "gender": "Gender",
    "age_group": "Age Group",
    "job_category": "Job Category",
    "signup_method": "Signup Method",
    "state": "Lifecycle State",
    "current_plan": "Current Plan",
}


@st.cache_data(show_spinner=False)
def load_users() -> pd.DataFrame:
    users = pd.read_csv(
        DATA_DIR / "users.csv",
        usecols=[
            "user_id",
            "signup_date",
            "acquisition_source",
            "device_type",
            "is_activated",
            "gender",
            "age_group",
            "job_category",
            "signup_method",
            "state",
            "current_plan",
            "last_active_date",
        ],
        parse_dates=["signup_date", "last_active_date"],
    )
    users["is_activated"] = users["is_activated"].fillna(False).astype(bool)
    users["gender"] = users["gender"].fillna("unknown")
    users["age_group"] = users["age_group"].fillna("unknown")
    users["job_category"] = users["job_category"].fillna("unknown")
    users["signup_method"] = users["signup_method"].fillna("unknown")
    users["state"] = users["state"].fillna("unknown")
    users["current_plan"] = users["current_plan"].fillna("none")
    users["trial_segment"] = users["state"].eq("trialing").map(
        {True: "trialing", False: "non_trialing"}
    )
    users["activation_segment"] = users["is_activated"].map(
        {True: "activated", False: "not_activated"}
    )
    return users


@st.cache_data(show_spinner=False)
def load_event_flags() -> pd.DataFrame:
    events = pd.read_csv(
        DATA_DIR / "event_logs.csv",
        usecols=["user_id", "event_name"],
        low_memory=False,
    )
    events = events[events["event_name"].isin(EVENT_STAGE_MAP.keys())].drop_duplicates()
    if events.empty:
        return pd.DataFrame(columns=["user_id"] + list(EVENT_STAGE_MAP.values()))

    event_flags = pd.crosstab(events["user_id"], events["event_name"]) > 0
    event_flags = event_flags.rename(columns=EVENT_STAGE_MAP).reset_index()

    for stage_key in EVENT_STAGE_MAP.values():
        if stage_key not in event_flags.columns:
            event_flags[stage_key] = False

    return event_flags[["user_id", *EVENT_STAGE_MAP.values()]]


@st.cache_data(show_spinner=False)
def load_plan_flags() -> pd.DataFrame:
    plan = pd.read_csv(
        DATA_DIR / "plan_history.csv",
        usecols=["user_id", "action"],
    )
    subscribed_users = (
        plan.loc[plan["action"].eq("subscribe"), "user_id"].dropna().drop_duplicates()
    )
    return pd.DataFrame({"user_id": subscribed_users, "subscribed": True})


@st.cache_data(show_spinner=False)
def load_payment_flags() -> pd.DataFrame:
    payment = pd.read_csv(
        DATA_DIR / "payment_transactions.csv",
        usecols=["user_id", "status"],
    )
    paid_users = (
        payment.loc[payment["status"].eq("completed"), "user_id"].dropna().drop_duplicates()
    )
    return pd.DataFrame({"user_id": paid_users, "payment_completed": True})


@st.cache_data(show_spinner=True)
def build_funnel_base() -> pd.DataFrame:
    users = load_users().copy()
    users["signed_up"] = users["signup_date"].notna()
    users["activated"] = users["is_activated"]
    users["retained_30d"] = (
        users["last_active_date"] >= users["signup_date"] + pd.Timedelta(days=30)
    ).fillna(False)

    base = users.merge(load_event_flags(), on="user_id", how="left")
    base = base.merge(load_plan_flags(), on="user_id", how="left")
    base = base.merge(load_payment_flags(), on="user_id", how="left")

    for col in STAGE_CATALOG:
        if col not in base.columns:
            base[col] = False
        base[col] = base[col].fillna(False).astype(bool)

    return base


def compute_funnel(df: pd.DataFrame, stages: list[str]) -> pd.DataFrame:
    rows = []
    cumulative = pd.Series(True, index=df.index)
    start_count = None
    prev_count = None

    for order, stage in enumerate(stages, start=1):
        cumulative = cumulative & df[stage]
        count = int(cumulative.sum())

        if start_count is None:
            start_count = max(count, 1)
        if prev_count is None:
            conv_prev = 1.0
            dropoff = 0
        else:
            conv_prev = count / prev_count if prev_count else 0.0
            dropoff = prev_count - count

        conv_start = count / start_count if start_count else 0.0
        rows.append(
            {
                "order": order,
                "stage_key": stage,
                "stage": STAGE_CATALOG[stage],
                "users": count,
                "conversion_prev": conv_prev,
                "conversion_start": conv_start,
                "dropoff_users": dropoff,
            }
        )
        prev_count = count

    return pd.DataFrame(rows)


def compute_segment_funnel(
    df: pd.DataFrame,
    stages: list[str],
    segment_col: str,
    min_users: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    curve_rows = []
    summary_rows = []

    for segment_value, seg_df in df.groupby(segment_col):
        total = len(seg_df)
        if total < min_users:
            continue

        funnel = compute_funnel(seg_df, stages)
        for _, row in funnel.iterrows():
            curve_rows.append(
                {
                    "segment": str(segment_value),
                    "order": int(row["order"]),
                    "stage": row["stage"],
                    "conversion_start": float(row["conversion_start"]),
                    "users": int(row["users"]),
                }
            )

        summary_rows.append(
            {
                "segment": str(segment_value),
                "base_users": int(funnel.iloc[0]["users"]),
                "final_users": int(funnel.iloc[-1]["users"]),
                "end_to_end_conversion": float(funnel.iloc[-1]["conversion_start"]),
            }
        )

    curve_df = pd.DataFrame(curve_rows)
    summary_df = pd.DataFrame(summary_rows).sort_values(
        "end_to_end_conversion", ascending=False
    )
    return curve_df, summary_df


def compute_cross_segment_heatmap(
    df: pd.DataFrame,
    stages: list[str],
    row_col: str,
    col_col: str,
    min_users: int,
) -> pd.DataFrame:
    rows = []
    for (row_value, col_value), group_df in df.groupby([row_col, col_col]):
        if len(group_df) < min_users:
            continue
        funnel = compute_funnel(group_df, stages)
        rows.append(
            {
                "row_segment": str(row_value),
                "col_segment": str(col_value),
                "users": int(funnel.iloc[0]["users"]),
                "end_to_end_conversion": float(funnel.iloc[-1]["conversion_start"]),
                "final_users": int(funnel.iloc[-1]["users"]),
            }
        )
    return pd.DataFrame(rows)


def fmt_pct(value: float) -> str:
    return f"{value * 100:.1f}%"


def choose_values(df: pd.DataFrame, column: str, label: str) -> list[str]:
    options = sorted(df[column].dropna().astype(str).unique().tolist())
    return st.multiselect(label, options, default=options)


st.title("Startie Funnel Dashboard")
st.caption("Decision support for bottlenecks, segment gaps, and next-quarter actions")

with st.expander("Context Basis", expanded=False):
    st.markdown(
        "- context/02_data_dictionary.md: users, event_logs, payment_transactions, plan_history\n"
        "- context/03_analysis_guide.md: combine event and payment/subscription logs for full funnel\n"
        "- context/05_ceo_questions.md: aligns with Q1 activation, Q2 channel quality, Q5 priority"
    )

base = build_funnel_base()

with st.sidebar:
    st.header("Filters")

    min_signup = base["signup_date"].min().date()
    max_signup = base["signup_date"].max().date()
    date_range = st.date_input(
        "Signup Date Range",
        value=(min_signup, max_signup),
        min_value=min_signup,
        max_value=max_signup,
    )

    if len(date_range) == 2:
        start_date, end_date = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
    else:
        start_date, end_date = pd.Timestamp(min_signup), pd.Timestamp(max_signup)

    channels = sorted(base["acquisition_source"].dropna().unique().tolist())
    selected_channels = st.multiselect("Channel", channels, default=channels)

    devices = sorted(base["device_type"].dropna().unique().tolist())
    selected_devices = st.multiselect("Device", devices, default=devices)

    st.header("User Attributes")
    selected_trials = choose_values(base, "trial_segment", "Trial Segment")
    selected_activations = choose_values(base, "activation_segment", "Activation Segment")
    selected_genders = choose_values(base, "gender", "Gender")
    selected_ages = choose_values(base, "age_group", "Age Group")
    selected_jobs = choose_values(base, "job_category", "Job Category")
    selected_signup_methods = choose_values(base, "signup_method", "Signup Method")
    selected_states = choose_values(base, "state", "Lifecycle State")
    selected_plans = choose_values(base, "current_plan", "Current Plan")

    st.header("Funnel Setup")
    template_name = st.selectbox("Template", list(FUNNEL_TEMPLATES.keys()))
    use_custom = st.toggle("Use Custom Stages", value=False)

    if use_custom:
        default_stages = FUNNEL_TEMPLATES[template_name]
        selected_stages = st.multiselect(
            "Select Stages (ordered)",
            options=list(STAGE_CATALOG.keys()),
            default=default_stages,
            format_func=lambda x: STAGE_CATALOG[x],
        )
    else:
        selected_stages = FUNNEL_TEMPLATES[template_name]

    metric_mode = st.radio(
        "Chart Metric",
        ["Users", "Conversion vs Previous", "Conversion vs Start", "Drop-off Users"],
        index=0,
    )

filtered = base[
    base["signup_date"].between(start_date, end_date)
    & base["acquisition_source"].isin(selected_channels)
    & base["device_type"].isin(selected_devices)
    & base["trial_segment"].isin(selected_trials)
    & base["activation_segment"].isin(selected_activations)
    & base["gender"].isin(selected_genders)
    & base["age_group"].isin(selected_ages)
    & base["job_category"].isin(selected_jobs)
    & base["signup_method"].isin(selected_signup_methods)
    & base["state"].isin(selected_states)
    & base["current_plan"].isin(selected_plans)
].copy()

if len(selected_stages) < 2:
    st.error("Choose at least two funnel stages.")
    st.stop()

if filtered.empty:
    st.warning("No users match current filters.")
    st.stop()

funnel_df = compute_funnel(filtered, selected_stages)

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("Users in Scope", f"{len(filtered):,}")
kpi2.metric("Funnel Start", f"{int(funnel_df.iloc[0]['users']):,}")
kpi3.metric("Funnel End", f"{int(funnel_df.iloc[-1]['users']):,}")
kpi4.metric("End-to-End Conversion", fmt_pct(float(funnel_df.iloc[-1]["conversion_start"])))

chart_data = funnel_df.copy()
chart_data["stage_order"] = chart_data["order"].astype(str) + ". " + chart_data["stage"]

if metric_mode == "Users":
    y_col = "users"
    y_title = "Users"
elif metric_mode == "Conversion vs Previous":
    y_col = "conversion_prev"
    y_title = "Conversion vs Previous"
elif metric_mode == "Conversion vs Start":
    y_col = "conversion_start"
    y_title = "Conversion vs Start"
else:
    y_col = "dropoff_users"
    y_title = "Drop-off Users"

bar = (
    alt.Chart(chart_data)
    .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
    .encode(
        x=alt.X("stage_order:N", sort=list(chart_data["stage_order"])),
        y=alt.Y(f"{y_col}:Q", title=y_title),
        color=alt.Color(
            "conversion_start:Q", title="Start Conversion", scale=alt.Scale(scheme="tealblues")
        ),
        tooltip=[
            alt.Tooltip("stage:N", title="Stage"),
            alt.Tooltip("users:Q", title="Users", format=",d"),
            alt.Tooltip("conversion_prev:Q", title="Conv vs Prev", format=".1%"),
            alt.Tooltip("conversion_start:Q", title="Conv vs Start", format=".1%"),
            alt.Tooltip("dropoff_users:Q", title="Drop-off", format=",d"),
        ],
    )
)

st.altair_chart(bar.properties(height=420), use_container_width=True)

view_df = funnel_df.copy()
view_df["conversion_prev"] = view_df["conversion_prev"].map(fmt_pct)
view_df["conversion_start"] = view_df["conversion_start"].map(fmt_pct)
st.dataframe(
    view_df[["order", "stage", "users", "conversion_prev", "conversion_start", "dropoff_users"]],
    use_container_width=True,
    hide_index=True,
)

st.subheader("Segment Comparison")
seg_col1, seg_col2 = st.columns([2, 1])
with seg_col1:
    segment_mode = st.selectbox(
        "Dimension",
        list(SEGMENT_LABELS.keys()),
        format_func=lambda c: SEGMENT_LABELS[c],
    )
with seg_col2:
    min_users = st.number_input("Min Segment Size", min_value=10, max_value=5000, value=100, step=10)

segment_curve_df, segment_summary_df = compute_segment_funnel(
    filtered,
    selected_stages,
    segment_mode,
    min_users=min_users,
)

if segment_curve_df.empty:
    st.info("No segment passes min sample threshold. Lower the threshold.")
else:
    seg_chart = (
        alt.Chart(segment_curve_df)
        .mark_line(point=True)
        .encode(
            x=alt.X("stage:N", sort=list(funnel_df["stage"]), title="Funnel Stage"),
            y=alt.Y("conversion_start:Q", axis=alt.Axis(format="%"), title="Conversion vs Start"),
            color=alt.Color("segment:N", title="Segment"),
            tooltip=[
                alt.Tooltip("segment:N", title="Segment"),
                alt.Tooltip("stage:N", title="Stage"),
                alt.Tooltip("users:Q", title="Users", format=",d"),
                alt.Tooltip("conversion_start:Q", title="Conversion", format=".1%"),
            ],
        )
    )
    st.altair_chart(seg_chart.properties(height=380), use_container_width=True)

    segment_summary_df["end_to_end_conversion"] = segment_summary_df[
        "end_to_end_conversion"
    ].map(fmt_pct)
    st.dataframe(segment_summary_df, hide_index=True, use_container_width=True)

st.subheader("Cross Segment Heatmap")
heat_col1, heat_col2, heat_col3 = st.columns([2, 2, 1])
with heat_col1:
    heat_row_dim = st.selectbox(
        "Row Dimension",
        list(SEGMENT_LABELS.keys()),
        index=0,
        format_func=lambda c: SEGMENT_LABELS[c],
        key="heat_row_dim",
    )
with heat_col2:
    heat_col_dim = st.selectbox(
        "Column Dimension",
        list(SEGMENT_LABELS.keys()),
        index=2,
        format_func=lambda c: SEGMENT_LABELS[c],
        key="heat_col_dim",
    )
with heat_col3:
    heat_min_users = st.number_input(
        "Min Cell Users",
        min_value=10,
        max_value=5000,
        value=100,
        step=10,
        key="heat_min_users",
    )

if heat_row_dim == heat_col_dim:
    st.info("Choose different row/column dimensions for heatmap.")
else:
    heat_df = compute_cross_segment_heatmap(
        filtered,
        selected_stages,
        row_col=heat_row_dim,
        col_col=heat_col_dim,
        min_users=int(heat_min_users),
    )
    if heat_df.empty:
        st.info("No cells meet the minimum user threshold.")
    else:
        heat_metric = st.radio(
            "Heatmap Metric",
            ["End-to-End Conversion", "Final Users"],
            horizontal=True,
            key="heat_metric",
        )
        metric_col = (
            "end_to_end_conversion" if heat_metric == "End-to-End Conversion" else "final_users"
        )
        metric_title = (
            "End-to-End Conversion" if heat_metric == "End-to-End Conversion" else "Final Users"
        )

        heatmap = (
            alt.Chart(heat_df)
            .mark_rect()
            .encode(
                x=alt.X("col_segment:N", title=SEGMENT_LABELS[heat_col_dim]),
                y=alt.Y("row_segment:N", title=SEGMENT_LABELS[heat_row_dim]),
                color=alt.Color(f"{metric_col}:Q", title=metric_title, scale=alt.Scale(scheme="goldgreen")),
                tooltip=[
                    alt.Tooltip("row_segment:N", title=SEGMENT_LABELS[heat_row_dim]),
                    alt.Tooltip("col_segment:N", title=SEGMENT_LABELS[heat_col_dim]),
                    alt.Tooltip("users:Q", title="Users", format=",d"),
                    alt.Tooltip("final_users:Q", title="Final Users", format=",d"),
                    alt.Tooltip("end_to_end_conversion:Q", title="E2E Conversion", format=".1%"),
                ],
            )
        )

        text = (
            alt.Chart(heat_df)
            .mark_text(fontSize=11)
            .encode(
                x="col_segment:N",
                y="row_segment:N",
                text=alt.Text("end_to_end_conversion:Q", format=".1%"),
                color=alt.value("black"),
            )
        )
        st.altair_chart((heatmap + text).properties(height=420), use_container_width=True)

        heat_view = heat_df.copy().sort_values(["row_segment", "col_segment"])
        heat_view["end_to_end_conversion"] = heat_view["end_to_end_conversion"].map(fmt_pct)
        st.dataframe(heat_view, hide_index=True, use_container_width=True)

st.subheader("Q1-Q5 Decision Frame")
col_a, col_b = st.columns(2)
with col_a:
    st.markdown(
        "### What\n"
        "- Find the biggest drop-off stage and weak segments.\n"
        "### Why\n"
        "- Build hypotheses from channel, device, and activation conversion gaps."
    )
with col_b:
    st.markdown(
        "### So What\n"
        "- Prioritize next-quarter experiments on onboarding, checkout UX, and reminders.\n"
        "### Impact\n"
        "- Estimate paid conversion lift from stage-level conversion improvements."
    )

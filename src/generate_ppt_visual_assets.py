from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "raw"
RESULTS_DIR = ROOT / "deliverables" / "results"

START_DATE = pd.Timestamp("2025-01-06")


def load_data():
    users = pd.read_csv(
        DATA_DIR / "users.csv",
        parse_dates=["signup_date", "churn_date", "activation_date", "last_active_date"],
    )
    events = pd.read_csv(
        DATA_DIR / "event_logs.csv",
        usecols=["user_id", "event_name", "event_timestamp"],
        parse_dates=["event_timestamp"],
        low_memory=False,
    )
    payments = pd.read_csv(
        DATA_DIR / "payment_transactions.csv",
        parse_dates=["transaction_date"],
    )
    chats = pd.read_csv(
        DATA_DIR / "chat_events.csv",
        parse_dates=["chat_date"],
    )
    assignments = pd.read_csv(
        DATA_DIR / "ab_assignment.csv",
        parse_dates=["assigned_date"],
    )
    return users, events, payments, chats, assignments


def prepare_base(users, events, payments):
    users_2025 = users.loc[users["signup_date"] >= START_DATE].copy()
    ev = events.merge(users_2025[["user_id", "signup_date"]], on="user_id", how="inner")
    ev["event_date"] = ev["event_timestamp"].dt.floor("D")
    ev["day_since_signup"] = (ev["event_date"] - ev["signup_date"]).dt.days

    win7 = ev.loc[ev["day_since_signup"].between(0, 6)].copy()
    flags = (
        win7.assign(value=1)
        .pivot_table(index="user_id", columns="event_name", values="value", aggfunc="max", fill_value=0)
        .reset_index()
    )
    for col in ["lesson_completed", "quiz_submitted", "onboarding_completed"]:
        if col not in flags.columns:
            flags[col] = 0

    base = users_2025[["user_id", "signup_date", "churn_date"]].merge(
        flags[["user_id", "lesson_completed", "quiz_submitted", "onboarding_completed"]],
        on="user_id",
        how="left",
    )
    for col in ["lesson_completed", "quiz_submitted", "onboarding_completed"]:
        base[col] = base[col].fillna(0).gt(0)

    base["aha"] = base["lesson_completed"] & base["quiz_submitted"]
    base["segment"] = np.select(
        [
            (~base["lesson_completed"]) & (~base["quiz_submitted"]),
            (base["lesson_completed"]) & (~base["quiz_submitted"]),
            base["aha"],
        ],
        ["Neither", "Lesson only", "Aha"],
        default="Other",
    )
    base["quiz_not_submitted"] = ~base["quiz_submitted"]
    base["churned"] = base["churn_date"].notna()

    paid = (
        payments.loc[payments["status"].eq("completed"), ["user_id", "transaction_date"]]
        .sort_values("transaction_date")
        .drop_duplicates("user_id")
    )
    base = base.merge(paid, on="user_id", how="left")
    base["paid_30d"] = (
        (base["transaction_date"] - base["signup_date"]).dt.days.between(0, 30)
    ).fillna(False)
    return users_2025, ev, base


def savefig(fig, name):
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(RESULTS_DIR / name, dpi=160, bbox_inches="tight")
    plt.close(fig)


def plot_slide03_overview(users, events):
    signups = users.assign(month=users["signup_date"].dt.to_period("M")).groupby("month")["user_id"].nunique()
    mau = events.assign(month=events["event_timestamp"].dt.to_period("M")).groupby("month")["user_id"].nunique()
    chart = (
        pd.concat([signups.rename("signups"), mau.rename("mau")], axis=1)
        .fillna(0)
        .reset_index()
    )
    chart["month_label"] = chart["month"].astype(str)

    fig, ax = plt.subplots(figsize=(10, 5))
    x = np.arange(len(chart))
    ax.bar(x - 0.18, chart["signups"], width=0.36, color="#1f77b4", label="Monthly signups")
    ax.bar(x + 0.18, chart["mau"], width=0.36, color="#ff7f0e", label="Monthly active users")
    ax.set_xticks(x)
    ax.set_xticklabels(chart["month_label"], rotation=45)
    ax.set_title("Slide 03 - Overview Trend")
    ax.set_ylabel("Users")
    ax.legend(frameon=False)
    ax.text(
        0.98,
        0.95,
        f"Cumulative signups: {len(users):,}",
        transform=ax.transAxes,
        ha="right",
        va="top",
        fontsize=11,
        color="#333333",
    )
    savefig(fig, "slide03_overview_trend.png")


def plot_slide07_diagnostics(base):
    quiz_not_submitted = base["quiz_not_submitted"].mean() * 100
    churn_by_aha = base.groupby("aha")["churned"].mean().mul(100)
    churn_ratio = churn_by_aha[False] / churn_by_aha[True]
    churn_hist = base.loc[base["churned"]].copy()
    churn_hist["churn_day"] = (churn_hist["churn_date"] - churn_hist["signup_date"]).dt.days
    churn_hist = churn_hist.loc[churn_hist["churn_day"].between(0, 14)]

    fig, axes = plt.subplots(1, 3, figsize=(15, 4.8))

    axes[0].pie(
        [quiz_not_submitted, 100 - quiz_not_submitted],
        labels=["Quiz not submitted", "Quiz submitted"],
        colors=["#ef4444", "#d1d5db"],
        startangle=90,
        counterclock=False,
        wedgeprops={"width": 0.35},
        autopct="%1.1f%%",
    )
    axes[0].set_title("7-day quiz submission gap")

    axes[1].bar(
        ["Non-Aha", "Aha"],
        [churn_by_aha[False], churn_by_aha[True]],
        color=["#f97316", "#22c55e"],
        width=0.55,
    )
    axes[1].set_title("Churn rate by Aha status")
    axes[1].set_ylabel("Churn rate (%)")
    axes[1].text(
        0.5,
        max(churn_by_aha) + 3,
        f"{churn_ratio:.2f}x higher without Aha",
        ha="center",
        fontsize=11,
    )

    churn_counts = churn_hist["churn_day"].value_counts().sort_index()
    axes[2].bar(churn_counts.index.astype(str), churn_counts.values, color="#94a3b8")
    if 8 in churn_counts.index:
        idx = list(churn_counts.index).index(8)
        axes[2].patches[idx].set_color("#2563eb")
    axes[2].set_title("Churn timing spike")
    axes[2].set_xlabel("Days from signup to churn")
    axes[2].set_ylabel("Users")

    fig.suptitle("Slide 07 - Value Gap Diagnostics", fontsize=15)
    savefig(fig, "slide07_value_gap_diagnostics.png")


def plot_slide08_aha(base):
    dist = (
        base["segment"]
        .value_counts(normalize=True)
        .reindex(["Neither", "Lesson only", "Aha"])
        .mul(100)
    )
    conv = base.groupby("aha")["paid_30d"].mean().mul(100)
    pp_gap = conv[True] - conv[False]
    ratio = conv[True] / conv[False]

    fig, axes = plt.subplots(1, 2, figsize=(13, 4.8))

    left = 0
    colors = {"Neither": "#cbd5e1", "Lesson only": "#93c5fd", "Aha": "#2563eb"}
    for label in ["Neither", "Lesson only", "Aha"]:
        value = dist[label]
        axes[0].barh(["7-day behavior mix"], [value], left=left, color=colors[label], label=f"{label} {value:.1f}%")
        left += value
    axes[0].set_xlim(0, 100)
    axes[0].set_title("7-day Aha distribution")
    axes[0].legend(frameon=False, loc="lower right")

    axes[1].bar(
        ["Non-Aha", "Aha"],
        [conv[False], conv[True]],
        color=["#94a3b8", "#2563eb"],
        width=0.55,
    )
    axes[1].set_ylabel("Paid conversion within 30 days (%)")
    axes[1].set_title("Conversion uplift from Aha")
    axes[1].text(0.5, 0.90, f"+{pp_gap:.1f}%p | {ratio:.2f}x", ha="center", fontsize=11, transform=axes[1].transAxes)

    fig.suptitle("Slide 08 - Aha KPI", fontsize=15)
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    savefig(fig, "slide08_aha_kpi.png")


def plot_slide09_onboarding(base, assignments, events, users):
    exp = assignments.loc[assignments["experiment_id"].eq("exp_onboarding_v2"), ["user_id", "variant"]]
    exp = exp.merge(users[["user_id", "signup_date"]], on="user_id", how="left")

    exp_events = events.loc[events["event_name"].isin(["onboarding_completed", "lesson_completed", "quiz_submitted"])].copy()
    exp_events = exp_events.merge(exp[["user_id", "variant", "signup_date"]], on="user_id", how="inner")
    exp_events["event_date"] = exp_events["event_timestamp"].dt.floor("D")
    exp_events["day_since_signup"] = (exp_events["event_date"] - exp_events["signup_date"]).dt.days
    exp_events = exp_events.loc[exp_events["day_since_signup"].between(0, 6)]

    flags = (
        exp_events.assign(value=1)
        .pivot_table(index=["user_id", "variant"], columns="event_name", values="value", aggfunc="max", fill_value=0)
        .reset_index()
    )
    for col in ["onboarding_completed", "lesson_completed", "quiz_submitted"]:
        if col not in flags.columns:
            flags[col] = 0
        flags[col] = flags[col].gt(0)
    flags["aha"] = flags["lesson_completed"] & flags["quiz_submitted"]

    exp_full = exp[["user_id", "variant"]].merge(
        flags[["user_id", "variant", "onboarding_completed", "aha"]],
        on=["user_id", "variant"],
        how="left",
    )
    exp_full["onboarding_completed"] = exp_full["onboarding_completed"].fillna(False).astype(bool)
    exp_full["aha"] = exp_full["aha"].fillna(False).astype(bool)

    onboard_rate = exp_full.groupby("variant")["onboarding_completed"].mean().mul(100)
    uplift = onboard_rate["treatment"] - onboard_rate["control"]

    aha_by_onboarding = base.groupby("onboarding_completed")["aha"].mean().mul(100)
    pp_gap = aha_by_onboarding[True] - aha_by_onboarding[False]
    ratio = aha_by_onboarding[True] / aha_by_onboarding[False]

    fig, axes = plt.subplots(1, 2, figsize=(13, 4.8))

    axes[0].bar(
        ["Control", "Treatment"],
        [onboard_rate["control"], onboard_rate["treatment"]],
        color=["#94a3b8", "#10b981"],
        width=0.55,
    )
    axes[0].set_title("Onboarding redesign A/B test")
    axes[0].set_ylabel("Onboarding completion rate (%)")
    axes[0].text(0.5, 0.93, f"+{uplift:.1f}%p uplift", ha="center", fontsize=11, transform=axes[0].transAxes)

    axes[1].bar(
        ["Not completed", "Completed"],
        [aha_by_onboarding[False], aha_by_onboarding[True]],
        color=["#cbd5e1", "#2563eb"],
        width=0.55,
    )
    axes[1].set_title("Aha rate by onboarding completion")
    axes[1].set_ylabel("Aha rate (%)")
    axes[1].text(0.5, 0.93, f"+{pp_gap:.1f}%p | {ratio:.2f}x", ha="center", fontsize=11, transform=axes[1].transAxes)

    fig.suptitle("Slide 09 - Onboarding Improvement", fontsize=15)
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    savefig(fig, "slide09_onboarding_improvement.png")


def plot_slide12_payment(events, payments):
    pricing_users = set(events.loc[events["event_name"].eq("pricing_page_viewed"), "user_id"].dropna())
    checkout_users = set(events.loc[events["event_name"].eq("checkout_started"), "user_id"].dropna())
    paid_users = set(payments.loc[payments["status"].eq("completed"), "user_id"].dropna())

    drop1 = 100 * (1 - len(pricing_users & checkout_users) / len(pricing_users))
    drop2 = 100 * (1 - len(checkout_users & paid_users) / len(checkout_users))

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    configs = [
        ("Pricing view -> Checkout start", drop1, "#ef4444"),
        ("Checkout start -> Payment complete", drop2, "#f97316"),
    ]
    for ax, (title, value, color) in zip(axes, configs):
        ax.pie(
            [value, 100 - value],
            colors=[color, "#e5e7eb"],
            startangle=90,
            counterclock=False,
            wedgeprops={"width": 0.32},
        )
        ax.text(0, 0.10, "Drop-off", ha="center", color="#6b7280", fontsize=11)
        ax.text(0, -0.05, f"{value:.2f}%", ha="center", color=color, fontsize=22, fontweight="bold")
        ax.set_title(title)

    fig.suptitle("Slide 12 - Checkout Funnel Drop-off", fontsize=15)
    savefig(fig, "slide12_checkout_dropoff.png")


def plot_slide13_cs(payments, chats, users):
    failed = (
        payments.loc[payments["status"].eq("failed"), ["user_id", "transaction_date"]]
        .sort_values("transaction_date")
        .drop_duplicates("user_id")
    )
    failed = failed.merge(users[["user_id", "churn_date"]], on="user_id", how="left")
    failed["churned"] = failed["churn_date"].notna()

    support = chats.loc[chats["category"].eq("billing"), ["user_id", "chat_date"]].copy()
    tmp = failed[["user_id", "transaction_date"]].merge(support, on="user_id", how="left")
    tmp["delta_days"] = (tmp["chat_date"] - tmp["transaction_date"]).dt.total_seconds() / 86400
    contacted = tmp.groupby("user_id")["delta_days"].apply(lambda s: ((s >= 0) & (s <= 7)).any())

    failed = failed.merge(contacted.rename("contacted"), on="user_id", how="left").fillna({"contacted": False})
    rates = failed.groupby("contacted")["churned"].mean().mul(100)
    gap = rates[False] - rates[True]

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(
        ["No CS contact", "Billing chat within 7d"],
        [rates[False], rates[True]],
        color=["#94a3b8", "#10b981"],
        width=0.55,
    )
    ax.set_ylabel("Churn rate (%)")
    ax.set_title("Slide 13 - CS intervention effect")
    ax.text(0.5, 0.92, f"-{gap:.2f}%p", ha="center", fontsize=12, transform=ax.transAxes)
    fig.tight_layout()
    savefig(fig, "slide13_cs_intervention_effect.png")


def plot_slide14_impact_summary():
    metrics = [
        ("Extra monthly revenue", "+1.54M KRW", "#2563eb"),
        ("Annualized value", "+185M KRW", "#10b981"),
        ("Onboarding completion", "+1.36%p", "#f97316"),
        ("Checkout efficiency", "+3.90%p", "#ef4444"),
        ("Users retained / month", "+7", "#7c3aed"),
        ("7-day Aha reach", "+1.17%p", "#0f766e"),
    ]

    fig, axes = plt.subplots(2, 3, figsize=(13, 7))
    axes = axes.flatten()
    for ax, (label, value, color) in zip(axes, metrics):
        ax.set_facecolor("#f8fafc")
        ax.text(0.5, 0.62, value, ha="center", va="center", fontsize=22, color=color, fontweight="bold")
        ax.text(0.5, 0.35, label, ha="center", va="center", fontsize=11, color="#475569")
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_visible(False)

    fig.suptitle("Slide 14 - Expected Impact Summary (Deck Scenario)", fontsize=16)
    savefig(fig, "slide14_expected_impact_summary.png")


def plot_slide14_mau_forecast(events):
    mau = (
        events.assign(month=events["event_timestamp"].dt.to_period("M"))
        .groupby("month")["user_id"]
        .nunique()
        .sort_index()
    )
    history = mau.reset_index()
    history["idx"] = np.arange(len(history))

    coeff = np.polyfit(history["idx"], history["user_id"], 1)
    future_idx = np.arange(len(history), len(history) + 6)
    baseline = coeff[0] * future_idx + coeff[1]
    uplift = np.arange(1, 7) * 7
    improved = baseline + uplift

    future_periods = pd.period_range(history["month"].iloc[-1] + 1, periods=6, freq="M")

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(history["month"].astype(str), history["user_id"], marker="o", color="#1f77b4", label="Actual MAU")
    ax.plot(future_periods.astype(str), baseline, marker="o", linestyle="--", color="#94a3b8", label="Baseline forecast")
    ax.plot(future_periods.astype(str), improved, marker="o", color="#10b981", label="Improved scenario")
    ax.set_title("Slide 14 - 6M MAU scenario")
    ax.set_ylabel("Monthly active users")
    ax.legend(frameon=False)
    ax.tick_params(axis="x", rotation=45)
    fig.tight_layout()
    savefig(fig, "slide14_mau_forecast_6m.png")


def main():
    users, events, payments, chats, assignments = load_data()
    users_2025, events_2025, base = prepare_base(users, events, payments)

    plot_slide03_overview(users, events)
    plot_slide07_diagnostics(base)
    plot_slide08_aha(base)
    plot_slide09_onboarding(base, assignments, events, users)
    plot_slide12_payment(events, payments)
    plot_slide13_cs(payments, chats, users)
    plot_slide14_impact_summary()
    plot_slide14_mau_forecast(events)


if __name__ == "__main__":
    main()

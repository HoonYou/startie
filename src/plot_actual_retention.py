from pathlib import Path

import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "raw"
OUTPUT_DIR = ROOT / "outputs"
SRC_OUTPUT_DIR = ROOT / "src" / "output"

MAX_DAY = 90
START_DATE = pd.Timestamp("2025-01-06")


def load_users() -> pd.DataFrame:
    users = pd.read_csv(
        DATA_DIR / "users.csv",
        usecols=["user_id", "signup_date", "is_activated"],
        parse_dates=["signup_date"],
    )
    users = users.dropna(subset=["signup_date"]).copy()
    users["is_activated"] = users["is_activated"].fillna(False).astype(bool)
    users = users.loc[users["signup_date"] >= START_DATE].copy()
    users["segment"] = users["is_activated"].map(
        {True: "Activated", False: "Non-activated"}
    )
    return users


def load_activity() -> pd.DataFrame:
    events = pd.read_csv(
        DATA_DIR / "event_logs.csv",
        usecols=["user_id", "event_timestamp"],
        parse_dates=["event_timestamp"],
        low_memory=False,
    )
    events["activity_date"] = events["event_timestamp"].dt.floor("D")
    activity = events[["user_id", "activity_date"]].drop_duplicates()
    return activity


def build_retention(users: pd.DataFrame, activity: pd.DataFrame) -> pd.DataFrame:
    latest_activity_date = activity["activity_date"].max()
    base = users.merge(activity, on="user_id", how="left")
    base["day_since_signup"] = (
        base["activity_date"] - base["signup_date"]
    ).dt.days
    base = base.loc[base["day_since_signup"].between(0, MAX_DAY)].copy()

    curve_rows = []
    segments = {
        "All Users": users["user_id"],
        "Activated": users.loc[users["is_activated"], "user_id"],
        "Non-activated": users.loc[~users["is_activated"], "user_id"],
    }

    for segment_name, user_ids in segments.items():
        seg_users = users.loc[users["user_id"].isin(user_ids)].copy()
        seg_base = base.loc[base["user_id"].isin(user_ids), ["user_id", "day_since_signup"]]

        for day in range(1, MAX_DAY + 1):
            eligible = seg_users.loc[
                seg_users["signup_date"] + pd.Timedelta(days=day) <= latest_activity_date
            ]
            eligible_users = eligible["user_id"].nunique()
            if eligible_users == 0:
                continue

            retained_users = seg_base.loc[seg_base["day_since_signup"].eq(day), "user_id"].nunique()
            curve_rows.append(
                {
                    "segment": segment_name,
                    "day": day,
                    "eligible_users": eligible_users,
                    "retained_users": retained_users,
                    "retention_rate": retained_users / eligible_users,
                }
            )

    return pd.DataFrame(curve_rows)


def plot_retention(curves: pd.DataFrame) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    colors = {
        "All Users": "#1f77b4",
        "Activated": "#2ca02c",
        "Non-activated": "#d62728",
    }

    plt.style.use("seaborn-v0_8-whitegrid")
    fig, ax = plt.subplots(figsize=(13, 7))

    for segment, seg_df in curves.groupby("segment"):
        seg_df = seg_df.sort_values("day")
        ax.plot(
            seg_df["day"],
            seg_df["retention_rate"] * 100,
            label=segment,
            color=colors[segment],
            linewidth=2.5,
        )

        for marker_day in [7, 30, 60, 90]:
            marker = seg_df.loc[seg_df["day"].eq(marker_day)]
            if marker.empty:
                continue
            value = marker.iloc[0]["retention_rate"] * 100
            ax.scatter(marker_day, value, color=colors[segment], s=45, zorder=3)

    ax.axvspan(30, 90, color="#f4d35e", alpha=0.12)
    ax.text(31, 43, "Plateau check zone (D30-D90)", fontsize=11, color="#7a5c00")
    ax.set_title("2025 Signup Cohort Exact Retention (Actual Event Data)", fontsize=18)
    ax.set_xlabel("Days Since Signup", fontsize=12)
    ax.set_ylabel("Exact Retention (%)", fontsize=12)
    ax.set_xlim(1, MAX_DAY)
    ax.set_ylim(0, 50)
    ax.legend(frameon=False)

    summary_days = [7, 30, 60, 90]
    annotation_lines = []
    for segment in ["All Users", "Activated", "Non-activated"]:
        seg_df = curves.loc[curves["segment"].eq(segment)]
        metrics = []
        for day in summary_days:
            row = seg_df.loc[seg_df["day"].eq(day)]
            if row.empty:
                continue
            metrics.append(f"D{day} {row.iloc[0]['retention_rate'] * 100:.1f}%")
        annotation_lines.append(f"{segment}: " + " | ".join(metrics))

    fig.text(
        0.02,
        0.02,
        "\n".join(annotation_lines),
        fontsize=10,
        family="monospace",
    )

    plt.tight_layout(rect=[0, 0.06, 1, 1])
    fig.savefig(OUTPUT_DIR / "actual_exact_retention_flat_curve_2025.png", dpi=160)
    plt.close(fig)


def set_korean_font() -> None:
    font_candidates = [
        ("C:/Windows/Fonts/malgun.ttf", "Malgun Gothic"),
        ("C:/Windows/Fonts/NanumGothic.ttf", "NanumGothic"),
    ]
    for font_path, font_name in font_candidates:
        try:
            if Path(font_path).exists():
                fm.fontManager.addfont(font_path)
            plt.rcParams["font.family"] = font_name
            plt.rcParams["axes.unicode_minus"] = False
            return
        except Exception:
            continue


def plot_retention_kr_all_users(curves: pd.DataFrame) -> None:
    SRC_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    curve = curves.loc[curves["segment"].eq("All Users")].sort_values("day").copy()

    plt.style.use("seaborn-v0_8-whitegrid")
    set_korean_font()
    fig, ax = plt.subplots(figsize=(12, 7))
    ax.plot(
        curve["day"],
        curve["retention_rate"] * 100,
        color="#1f77b4",
        linewidth=3,
    )

    for marker_day in [7, 30, 60, 90]:
        marker = curve.loc[curve["day"].eq(marker_day)]
        if marker.empty:
            continue
        value = marker.iloc[0]["retention_rate"] * 100
        ax.scatter(marker_day, value, color="#1f77b4", s=55, zorder=3)
        ax.text(marker_day + 1, value + 0.5, f"D{marker_day} {value:.1f}%", fontsize=11)

    ax.axvspan(30, 90, color="#f4d35e", alpha=0.14)
    ax.text(32, 12.3, "D30 이후 평탄 구간", fontsize=12, color="#7a5c00")
    ax.set_title("2025 가입 코호트 전체 유저 리텐션", fontsize=20)
    ax.set_xlabel("가입 후 경과일", fontsize=13)
    ax.set_ylabel("Exact Retention (%)", fontsize=13)
    ax.set_xlim(1, MAX_DAY)
    ax.set_ylim(0, 42)

    d30 = curve.loc[curve["day"].eq(30), "retention_rate"]
    d90 = curve.loc[curve["day"].eq(90), "retention_rate"]
    if not d30.empty and not d90.empty:
        summary = (
            f"전체 유저 리텐션은 D30 {d30.iloc[0] * 100:.1f}% 이후 "
            f"D90 {d90.iloc[0] * 100:.1f}%까지 큰 하락 없이 유지됩니다."
        )
        fig.text(0.02, 0.02, summary, fontsize=11)

    plt.tight_layout(rect=[0, 0.05, 1, 1])
    fig.savefig(SRC_OUTPUT_DIR / "전체_유저_리텐션_2025.png", dpi=160)
    plt.close(fig)


def plot_retention_en_all_users(curves: pd.DataFrame) -> None:
    SRC_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    curve = curves.loc[curves["segment"].eq("All Users")].sort_values("day").copy()

    plt.style.use("seaborn-v0_8-whitegrid")
    fig, ax = plt.subplots(figsize=(12, 7))
    ax.plot(
        curve["day"],
        curve["retention_rate"] * 100,
        color="#1f77b4",
        linewidth=3,
    )

    for marker_day in [7, 30, 60, 90]:
        marker = curve.loc[curve["day"].eq(marker_day)]
        if marker.empty:
            continue
        value = marker.iloc[0]["retention_rate"] * 100
        ax.scatter(marker_day, value, color="#1f77b4", s=55, zorder=3)
        ax.text(marker_day + 1, value + 0.5, f"D{marker_day} {value:.1f}%", fontsize=11)

    ax.axvspan(30, 90, color="#f4d35e", alpha=0.14)
    ax.text(32, 12.3, "Plateau zone after D30", fontsize=12, color="#7a5c00")
    ax.set_title("2025 Signup Cohort Retention - All Users", fontsize=20)
    ax.set_xlabel("Days Since Signup", fontsize=13)
    ax.set_ylabel("Exact Retention (%)", fontsize=13)
    ax.set_xlim(1, MAX_DAY)
    ax.set_ylim(0, 42)

    d30 = curve.loc[curve["day"].eq(30), "retention_rate"]
    d90 = curve.loc[curve["day"].eq(90), "retention_rate"]
    if not d30.empty and not d90.empty:
        summary = (
            f"Retention stabilizes after D30: {d30.iloc[0] * 100:.1f}% at D30 "
            f"and {d90.iloc[0] * 100:.1f}% at D90."
        )
        fig.text(0.02, 0.02, summary, fontsize=11)

    plt.tight_layout(rect=[0, 0.05, 1, 1])
    fig.savefig(SRC_OUTPUT_DIR / "all_users_retention_2025.png", dpi=160)
    plt.close(fig)


def save_summary(curves: pd.DataFrame) -> None:
    summary = curves.loc[curves["day"].isin([7, 14, 30, 60, 90])].copy()
    summary["retention_pct"] = (summary["retention_rate"] * 100).round(2)
    summary = summary[
        ["segment", "day", "eligible_users", "retained_users", "retention_pct"]
    ].sort_values(["segment", "day"])
    summary.to_csv(OUTPUT_DIR / "actual_exact_retention_flat_curve_2025_summary.csv", index=False)


def main() -> None:
    users = load_users()
    activity = load_activity()
    curves = build_retention(users, activity)
    plot_retention(curves)
    plot_retention_kr_all_users(curves)
    plot_retention_en_all_users(curves)
    save_summary(curves)
    print(curves.loc[curves["day"].isin([7, 30, 60, 90])].sort_values(["segment", "day"]).to_string(index=False))


if __name__ == "__main__":
    main()

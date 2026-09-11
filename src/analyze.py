"""Check MySQL results against Pandas, summarize statistics, and create EDA charts.

Run after load_and_analyze.py. No models or forecasts are used.
"""

from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/analysis"
REPORTS = ROOT / "reports"


def percentile(series):
    # Match SQL PERCENT_RANK exactly, including ties.
    return (series.rank(method="min") - 1) / (len(series) - 1)


def main():
    REPORTS.mkdir(exist_ok=True)
    charts = REPORTS / "figures"
    charts.mkdir(exist_ok=True)
    raw = pd.read_csv(ROOT / "data/processed/district_quarter.csv")
    state_raw = pd.read_csv(ROOT / "data/processed/state_quarter.csv")
    metrics = pd.read_csv(DATA / "district_metrics.csv")
    opportunities = pd.read_csv(DATA / "district_opportunities.csv")
    shortlist = pd.read_csv(DATA / "investigation_shortlist.csv").sort_values("investigation_rank")
    states = pd.read_csv(DATA / "state_metrics.csv")
    national = pd.read_csv(DATA / "national_metrics.csv").sort_values("period_id")
    latest_period = int(raw.period_id.max())
    latest = metrics[metrics.period_id == latest_period].copy()
    keys = ["state", "district", "period_id"]

    # Validate essential numbers independently using cleaned input, not SQL outputs.
    checks = {}
    checks["unique_district_quarter"] = not raw.duplicated(keys).any()
    checks["latest_core_fields_complete"] = (
        not latest[["transactions", "value_inr", "registered_users", "registered_merchants"]]
        .isna()
        .any()
        .any()
    )
    checks["row_count_preserved_by_sql_joins"] = len(raw) == len(metrics)
    independent = raw.sort_values(keys).copy()
    grouped = independent.groupby(["state", "district"])
    previous = grouped.transactions.shift(1)
    previous_period = grouped.period_id.shift(1)
    independent["expected_qoq"] = (independent.transactions / previous - 1).where(
        independent.period_id - previous_period == 1
    )
    independent["expected_upm"] = independent.registered_users / independent.registered_merchants
    compared = metrics.merge(
        independent[keys + ["expected_qoq", "expected_upm"]], on=keys, validate="one_to_one"
    )
    for actual, expected in [
        ("transaction_qoq", "expected_qoq"),
        ("users_per_merchant", "expected_upm"),
    ]:
        checks[f"{actual}_matches_pandas"] = np.allclose(
            compared[actual], compared[expected], rtol=1e-9, atol=1e-9, equal_nan=True
        )
    year_ago = raw[keys + ["transactions"]].copy()
    year_ago.period_id += 4
    year_ago = year_ago.rename(columns={"transactions": "year_ago_transactions"})
    yoy = metrics.merge(year_ago, on=keys, how="left", validate="one_to_one")
    checks["yoy_matches_same_quarter_last_year"] = np.allclose(
        yoy.transaction_yoy,
        yoy.transactions / yoy.year_ago_transactions - 1,
        rtol=1e-9,
        atol=1e-9,
        equal_nan=True,
    )

    eligible = latest[
        (latest.registered_users >= 100000)
        & (latest.registered_merchants >= 1000)
        & (latest.transactions >= 1000000)
        & latest.transaction_yoy.notna()
        & latest.transaction_qoq.notna()
    ].copy()
    factors = [
        ("transaction_yoy", 0.30),
        ("transactions_per_merchant", 0.25),
        ("users_per_merchant", 0.25),
        ("registered_users", 0.20),
    ]
    eligible["independent_score"] = sum(
        percentile(eligible[col]) * weight * 100 for col, weight in factors
    )
    matched = opportunities.merge(
        eligible[["district_key", "independent_score"]], on="district_key", validate="one_to_one"
    )
    checks["score_matches_independent_pandas"] = len(matched) == len(eligible) and np.allclose(
        matched.opportunity_score, matched.independent_score, atol=1e-8
    )
    checks["state_transaction_contribution_sums_to_one"] = np.allclose(
        states.groupby("period_id").state_contribution.sum(), 1
    )
    checks["district_contribution_sums_to_one_within_state"] = np.allclose(
        metrics.groupby(["state", "period_id"]).district_share_of_state.sum(), 1
    )
    checks["score_in_range_0_to_100"] = opportunities.opportunity_score.between(0, 100).all()
    checks = {name: bool(value) for name, value in checks.items()}
    (DATA / "validation.json").write_text(json.dumps(checks, indent=2))
    assert all(checks.values()), checks

    columns = [
        "transactions",
        "registered_users",
        "registered_merchants",
        "transaction_yoy",
        "users_per_merchant",
        "transactions_per_merchant",
        "merchants_per_1000_users",
    ]
    stats = eligible[columns].describe(percentiles=[0.1, 0.25, 0.5, 0.75, 0.9, 0.95]).T
    stats["iqr"] = stats["75%"] - stats["25%"]
    stats["lower_fence"] = stats["25%"] - 1.5 * stats.iqr
    stats["upper_fence"] = stats["75%"] + 1.5 * stats.iqr
    stats["outlier_count"] = [
        int(
            (
                (eligible[c] < stats.loc[c, "lower_fence"])
                | (eligible[c] > stats.loc[c, "upper_fence"])
            ).sum()
        )
        for c in columns
    ]
    stats.to_csv(DATA / "descriptive_statistics.csv", index_label="metric")
    # Correlation is descriptive, not causal. Two ratios share a merchant denominator.
    corr = eligible[columns].corr(method="spearman")
    corr.to_csv(DATA / "spearman_correlations.csv", index_label="metric")
    correlations = []
    for a, b in [
        ("registered_users", "transactions"),
        ("users_per_merchant", "transactions_per_merchant"),
        ("registered_merchants", "transactions"),
        ("transaction_yoy", "users_per_merchant"),
    ]:
        rho, _ = spearmanr(eligible[a], eligible[b])
        correlations.append({"metric_a": a, "metric_b": b, "spearman_rho": rho, "n": len(eligible)})
    pd.DataFrame(correlations).to_csv(DATA / "selected_correlations.csv", index=False)

    # Compare all scenarios within the same positive-momentum investigation pool.
    top = shortlist.head(10).copy()
    base_keys = set(top.district_key)
    sensitivities = []
    for column in ["opportunity_score", "equal_weight_score", "no_intensity_score"]:
        ranked = shortlist.sort_values([column, "state", "district"], ascending=[False, True, True])
        selected = set(ranked.head(10).district_key)
        sensitivities.append(
            {
                "scenario": column,
                "top10_overlap_with_base": len(base_keys & selected),
                "districts": "; ".join(ranked.head(10).district),
            }
        )
    sensitivity = pd.DataFrame(sensitivities)
    sensitivity.to_csv(DATA / "score_sensitivity.csv", index=False)
    # Threshold sensitivity: rerank all complete markets without size thresholds.
    all_complete = latest.dropna(subset=[c for c, _ in factors] + ["transaction_qoq"]).copy()
    all_complete = all_complete[all_complete.registered_merchants > 0]
    all_complete["broad_score"] = sum(percentile(all_complete[c]) * w * 100 for c, w in factors)
    broad_pool = all_complete[
        (all_complete.transaction_qoq > 0)
        & (all_complete.transaction_yoy > 0)
        & (all_complete.merchant_qoq >= 0)
        & (all_complete.user_qoq >= 0)
    ]
    broad = broad_pool.sort_values(
        ["broad_score", "state", "district"], ascending=[False, True, True]
    ).head(10)
    broad.to_csv(DATA / "no_size_threshold_top10.csv", index=False)

    for alternate, label in [
        ("equal_weight_score", "equal_weight_shortlist_rank"),
        ("no_intensity_score", "no_intensity_shortlist_rank"),
    ]:
        ranks = shortlist.sort_values(
            [alternate, "state", "district"], ascending=[False, True, True]
        ).reset_index(drop=True)
        mapping = dict(zip(ranks.district_key, np.arange(1, len(ranks) + 1)))
        top[label] = top.district_key.map(mapping)
    top["recommendation"] = np.where(
        top.no_intensity_shortlist_rank <= 10,
        "Priority field validation",
        "Investigate; sensitive to intensity weighting",
    )
    top.to_csv(DATA / "top10_recommendations.csv", index=False)
    monitor = opportunities[
        opportunities.market_segment == "Established acceptance / slower growth"
    ].nlargest(10, "registered_users")
    monitor.to_csv(DATA / "monitor_markets.csv", index=False)
    excluded = latest[~latest.district_key.isin(eligible.district_key)].copy()
    excluded["exclusion_reason"] = excluded.apply(
        lambda r: "; ".join(
            reason
            for test, reason in [
                (r.registered_users < 100000, "users below 100,000"),
                (r.registered_merchants < 1000, "merchants below 1,000"),
                (r.transactions < 1000000, "transactions below 1 million"),
                (
                    pd.isna(r.transaction_yoy) or pd.isna(r.transaction_qoq),
                    "missing comparable growth",
                ),
            ]
            if test
        ),
        axis=1,
    )
    excluded.to_csv(DATA / "excluded_districts.csv", index=False)

    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 11,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.titleweight": "bold",
            "figure.facecolor": "white",
        }
    )
    purple = "#5F259F"
    teal = "#087F8C"
    gray = "#697386"

    def save(fig, name):
        fig.savefig(charts / f"{name}.png", dpi=160, bbox_inches="tight")
        plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 4.5))
    x = np.arange(len(national))
    ax.plot(x, national.transactions / 1e9, color=purple, lw=2.5)
    ticks = sorted(set([0, *range(4, len(x), 4), len(x) - 1]))
    ax.set_xticks(ticks, national.period_label.iloc[ticks], rotation=35, ha="right")
    ax.set(
        title="PhonePe quarterly transactions | 2018 Q1–2026 Q2", ylabel="Transactions (billion)"
    )
    ax.grid(axis="y", alpha=0.15)
    save(fig, "01_transaction_trend")
    leaders = (
        states[states.period_id == latest_period]
        .nlargest(10, "transactions")
        .sort_values("transactions")
    )
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.barh(leaders.state.str.title(), leaders.transactions / 1e9, color=purple)
    ax.set(title="Top states by transaction volume | 2026 Q2", xlabel="Transactions (billion)")
    save(fig, "02_state_activity")
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.hist(eligible.users_per_merchant, bins=35, color=purple, edgecolor="white")
    ax.axvline(
        eligible.users_per_merchant.median(),
        color=teal,
        lw=2,
        label=f"Median: {eligible.users_per_merchant.median():.1f}",
    )
    ax.set(
        title=f"Users per registered merchant | {len(eligible)} eligible districts, 2026 Q2",
        xlabel="Registered users per registered merchant",
        ylabel="Districts",
    )
    ax.legend()
    save(fig, "03_penetration_distribution")
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.scatter(
        eligible.users_per_merchant, eligible.transaction_yoy * 100, s=20, alpha=0.35, color=gray
    )
    ax.scatter(
        top.users_per_merchant,
        top.transaction_yoy * 100,
        s=50,
        color=purple,
        label="Top 10 investigation shortlist",
    )
    ax.axvline(eligible.users_per_merchant.quantile(0.75), color=gray, ls="--", lw=1)
    ax.axhline(eligible.transaction_yoy.quantile(0.75) * 100, color=gray, ls="--", lw=1)
    ax.set(
        title="Demand growth and relative merchant penetration | 2026 Q2",
        xlabel="Users per registered merchant (higher = lower relative penetration)",
        ylabel="Transaction growth vs 2025 Q2 (%)",
    )
    ax.legend(loc="lower right")
    save(fig, "04_opportunity_matrix")
    ranked = top.sort_values("opportunity_score")
    fig, ax = plt.subplots(figsize=(11, 6))
    ax.barh(ranked.district.str.title(), ranked.opportunity_score, color=purple)
    ax.set(
        xlim=(0, 100),
        xlabel="Opportunity score / 100",
        title="Top 10 districts to investigate | 2026 Q2",
    )
    for i, value in enumerate(ranked.opportunity_score):
        ax.text(value + 0.6, i, f"{value:.1f}", va="center")
    save(fig, "05_district_shortlist")
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.bar(
        ["Default", "Equal weights", "Without intensity"],
        sensitivity.top10_overlap_with_base,
        color=[purple, teal, gray],
    )
    ax.set(
        ylim=(0, 11),
        ylabel="Districts retained from original top 10",
        title="Does the shortlist survive alternative weights?",
    )
    for i, value in enumerate(sensitivity.top10_overlap_with_base):
        ax.text(i, value + 0.15, str(value), ha="center")
    save(fig, "06_score_sensitivity")

    # Small source preview for audit and a compact set of findings for documentation.
    raw.sort_values(keys).head(5).to_csv(DATA / "source_preview.csv", index=False)
    snapshot = {
        "period": "2026-Q2",
        "national": national.iloc[-1].to_dict(),
        "districts": len(latest),
        "eligible": len(eligible),
        "investigation_pool": len(shortlist),
        "excluded": len(excluded),
        "threshold_sensitivity_top10_overlap": len(base_keys & set(broad.district_key)),
        "top10_state_counts": top.state.value_counts().to_dict(),
        "median_users_per_merchant": float(eligible.users_per_merchant.median()),
        "sensitivity": sensitivities,
        "checks_passed": sum(checks.values()),
        "top10": top[["state", "district", "opportunity_score", "recommendation"]].to_dict(
            "records"
        ),
    }
    (DATA / "findings.json").write_text(json.dumps(snapshot, indent=2, default=str))
    print(json.dumps(snapshot, indent=2, default=str))


if __name__ == "__main__":
    main()

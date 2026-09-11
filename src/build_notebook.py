"""Create the executed portfolio walkthrough from saved, validated outputs."""

from pathlib import Path
import nbformat as nbf
from nbclient import NotebookClient

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "notebooks" / "phonepe_merchant_expansion.ipynb"


def markdown(text):
    return nbf.v4.new_markdown_cell(text)


def code(text):
    return nbf.v4.new_code_cell(text)


def build():
    nb = nbf.v4.new_notebook()
    nb["metadata"]["kernelspec"] = {
        "display_name": "Python 3",
        "language": "python",
        "name": "python3",
    }
    nb["metadata"]["language_info"] = {"name": "python", "version": "3"}
    nb["cells"] = [
        markdown(
            """# PhonePe Merchant Expansion Opportunity Analysis\n\n**Portfolio level:** Data Analyst, 0–1 year experience  \n**Decision:** Which districts should a merchant-growth team investigate first?  \n**Stack:** Python, Pandas, MySQL 8, SQL, Power BI and DAX\n\nThis notebook explains the decision from the saved MySQL outputs. It is deliberately simple enough to discuss in a fresher interview while preserving real analytical controls: defined grain, reconciliation, time-aware comparisons, explicit eligibility rules, sensitivity analysis, and honest limitations."""
        ),
        markdown(
            """## 1. Business framing\n\nThe project treats expansion as a **prioritisation problem**, not a prediction problem. A district becomes interesting when digital-payment demand is growing, activity per registered merchant is high, and the user base is large enough to justify field research. The output is an investigation queue; it is not proof of merchant shortage or expected ROI."""
        ),
        code(
            """from pathlib import Path\nimport json\nimport pandas as pd\nimport matplotlib.pyplot as plt\nfrom IPython.display import display\n\nROOT = Path.cwd().parent if Path.cwd().name == 'notebooks' else Path.cwd()\nDATA = ROOT / 'data' / 'analysis'\nFIGURES = ROOT / 'reports' / 'figures'\n\nperiods = pd.read_csv(DATA / 'dim_period.csv')\nnational = pd.read_csv(DATA / 'national_metrics.csv').sort_values('period_id')\nstates = pd.read_csv(DATA / 'state_metrics.csv')\nopportunities = pd.read_csv(DATA / 'district_opportunities.csv')\nshortlist = pd.read_csv(DATA / 'investigation_shortlist.csv').sort_values('investigation_rank')\nvalidation = json.loads((DATA / 'validation.json').read_text())\nprint(f\"Coverage: {periods.period_label.iloc[0]} to {periods.period_label.iloc[-1]}\")\nprint(f\"Eligible districts: {len(opportunities):,}; positive-momentum shortlist: {len(shortlist):,}\")"""
        ),
        markdown(
            """## 2. Data trust checks\n\nThe raw public JSON was flattened to one row per state-quarter and district-quarter. Transaction counts, values, users, and merchants were checked for duplicate keys, missingness, negative values, and geographic reconciliation. Historical merchant values missing from the source remain null; they are not filled with zero."""
        ),
        code(
            """checks = pd.Series(validation, name='passed').rename_axis('check').reset_index()\ndisplay(checks)\nassert checks['passed'].all()"""
        ),
        markdown(
            """## 3. National payment context\n\nThe latest quarter establishes the size and direction of activity. Registered users and merchants are cumulative ecosystem registrations, so they describe mapped reach rather than active monthly participants."""
        ),
        code(
            """latest = national.iloc[-1]\nsummary = pd.DataFrame({\n    'Metric': ['Transactions', 'Transaction value', 'Registered users', 'Registered merchants', 'QoQ transaction growth'],\n    'Q2 2026': [f\"{latest.transactions/1e9:,.2f}B\", f\"₹{latest.value_inr/1e12:,.2f}T\",\n                f\"{latest.registered_users/1e6:,.2f}M\", f\"{latest.registered_merchants/1e6:,.2f}M\",\n                f\"{latest.transaction_qoq:.2%}\"]\n})\ndisplay(summary)"""
        ),
        code(
            """fig, ax = plt.subplots(figsize=(10, 4))\nax.plot(national['period_label'], national['transactions']/1e9, color='#5F259F', linewidth=2)\nax.set(title='PhonePe transaction volume by quarter', ylabel='Transactions (billions)', xlabel='')\nax.set_xticks(range(0, len(national), 4), national['period_label'].iloc[::4], rotation=45, ha='right')\nax.grid(axis='y', alpha=.25)\nplt.tight_layout(); plt.show()"""
        ),
        markdown(
            """## 4. Opportunity score\n\nComparable districts must have at least 100,000 users, 1,000 merchants, one million quarterly transactions, and enough history for QoQ and same-quarter YoY comparisons. The score combines percentile ranks:\n\n- 30% YoY transaction growth\n- 25% transactions per merchant\n- 25% users per merchant\n- 20% registered user base\n\nThe shortlist also requires positive QoQ and YoY transaction growth and non-declining user and merchant counts. Percentiles reduce domination by large outliers and keep the score easy to explain."""
        ),
        code(
            """cols = ['investigation_rank','district','state','opportunity_score','transaction_yoy',\n        'transaction_qoq','users_per_merchant','registered_merchants']\ntop10 = shortlist.head(10)[cols].copy()\ntop10['transaction_yoy'] = top10['transaction_yoy'].map(lambda x: f'{x:.1%}')\ntop10['transaction_qoq'] = top10['transaction_qoq'].map(lambda x: f'{x:.1%}')\ntop10['opportunity_score'] = top10['opportunity_score'].round(1)\ntop10['users_per_merchant'] = top10['users_per_merchant'].round(1)\ndisplay(top10)"""
        ),
        markdown(
            """## 5. Robustness and decision\n\nA ranking can look precise even when its assumptions are uncertain. The project therefore compares equal weights, a version without transaction intensity, and a version without the size cutoffs. Nine of the default top ten remain under equal weights, while six remain when intensity is removed and six remain when cutoffs are removed. The six districts that also survive the no-intensity top ten form the stronger first field-research group."""
        ),
        code(
            """sensitivity = pd.read_csv(DATA / 'score_sensitivity.csv')\ndisplay(sensitivity[['scenario','top10_overlap_with_base']])\nstronger = shortlist.head(10).query('no_intensity_rank <= 10').sort_values('investigation_rank')\ndisplay(stronger[['district','state','opportunity_score','no_intensity_rank']])"""
        ),
        markdown(
            """## 6. Recommendation\n\nBegin field validation with **West Godavari and Sangareddy**, followed by **Dr BR Ambedkar Konaseema, East Godavari, Sri Potti Sriramulu Nellore, and Alluri Sitharama Raju**. Validate active acceptance, merchant category gaps, competitor coverage, acquisition cost, and travel feasibility before spending. Measure 30-day active merchants and incremental transactions against comparable areas instead of counting sign-ups alone.\n\nThe result is intentionally cautious. PhonePe Pulse represents the PhonePe ecosystem, registrations are not activity, district totals combine categories, and the public data contains no shop universe, population denominator, competitor coverage, cost, revenue, or realized pilot outcome."""
        ),
        markdown(
            """## 7. Portfolio discussion prompts\n\n1. **Why MySQL?** It demonstrates data modelling, joins, window functions, reusable views, and reproducible business queries.\n2. **Why same-quarter YoY?** It compares like seasons and avoids treating Q2 as if it followed Q2 of the prior year directly.\n3. **Why no imputation for historical merchants?** Zero would mean no merchants, which the source does not establish.\n4. **Why no machine learning?** The business needs an explainable research queue; there is no labelled outcome such as campaign conversion or incremental profit.\n5. **What would improve the decision?** Active merchant counts, category-level district demand, merchant universe, population, competitive acceptance, acquisition cost, and pilot results."""
        ),
    ]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    nbf.write(nb, OUT)
    client = NotebookClient(
        nb, timeout=180, kernel_name="python3", resources={"metadata": {"path": str(ROOT)}}
    )
    client.execute()
    nbf.write(nb, OUT)
    print(f"Created and executed {OUT}")


if __name__ == "__main__":
    build()

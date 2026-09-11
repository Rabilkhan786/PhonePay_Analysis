# Setup and execution

This project can be reviewed immediately from the committed CSV outputs, SQL, notebook, and Power BI project. Rebuilding from the source requires Python 3.11+ and MySQL 8.

## 1. Create a Python environment

From the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## 2. Re-extract the pinned public source (optional)

Clone PhonePe Pulse at the recorded commit into any local folder, then run:

```powershell
python src/extract.py --raw "D:\path\to\pulse"
```

The commit, retrieval time, file hashes, row counts, and category labels are recorded in `data/source_manifest.json`. The cleaned CSVs are already included, so reviewers can skip this step.

## 3. Load and analyse in MySQL

Create a MySQL 8 user that can create the `phonepe_portfolio` database. Set credentials only in the current terminal; do not commit them.

```powershell
$env:MYSQL_HOST = "127.0.0.1"
$env:MYSQL_PORT = "3306"
$env:MYSQL_USER = "your_user"
$env:MYSQL_PASSWORD = "your_password"
python src/load_and_analyze.py
```

The loader creates the model, imports the three cleaned tables, executes the KPI and opportunity SQL, and exports result tables to `data/analysis`. It uses parameterised inserts and preserves historical missing merchant values as SQL `NULL`.

The SQL flow is:

1. `sql/01_model.sql` — staging tables, dimensions, and base facts.
2. `sql/02_metrics.sql` — district, state, and national KPIs with QoQ and same-quarter YoY comparisons.
3. `sql/03_opportunity.sql` — eligibility rules, percentile score, sensitivity variants, and positive-momentum shortlist.
4. `sql/04_business_questions.sql` — stakeholder-facing analysis queries.

## 4. Validate and generate analysis outputs

```powershell
python src/analyze.py
```

This independently recomputes key SQL results in Pandas, asserts ten reconciliation checks, writes descriptive statistics and sensitivity tables, and produces the six report figures. A successful run writes `data/analysis/validation.json` with every value set to `true`.

## 5. Review the notebook

Open `notebooks/phonepe_merchant_expansion.ipynb`. It is an executed walkthrough built from the saved outputs, so it does not require a live database connection.

## 6. Open the Power BI report

Open `powerbi/PhonePe.pbip` in Power BI Desktop. The report imports portable CSV copies from `powerbi/data` and contains three pages:

1. Digital Payments Overview
2. Merchant Penetration Analysis
3. Merchant Expansion Opportunities

If Power BI shows stale-data banners, select **Refresh now**, then save. The DAX definitions are also available in `powerbi/measures.dax` for quick review.

## Expected results

- 34 quarters, from 2018 Q1 through 2026 Q2
- 36 states and union territories
- 783 districts
- 26,622 district-quarter rows
- 680 districts eligible for comparable scoring in Q2 2026
- 624 districts in the positive-momentum investigation pool

The expected MySQL engine and row counts are recorded in `data/sql_execution.json`.


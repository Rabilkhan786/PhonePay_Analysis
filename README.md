# PhonePe Merchant Growth & Digital Payment Opportunity Analysis

**Python · Pandas · MySQL 8 · SQL · Matplotlib · Seaborn · Statistics · Power BI**

## Business problem

Identify Indian states and districts with strong digital-payment demand but comparatively low registered-merchant penetration, then determine which markets are most useful to investigate for merchant expansion.

This is a prioritisation analysis, not a prediction model. The final ranking is intended to support field research and business investigation rather than claim that merchant acquisition will automatically increase transactions.

## Data source

The project uses the official [PhonePe Pulse](https://github.com/PhonePe/pulse) public dataset.

- Coverage: 2018 Q1 through 2026 Q2
- Geographic levels: state and district
- Core measures: transaction count, transaction value, registered users, registered merchants
- Transaction categories: state-level counts

The analysis uses one internally consistent PhonePe Pulse release. Historical releases should not be mixed because PhonePe has restated portions of the data.

## Workflow

```text
Official PhonePe Pulse JSON
        ↓
Python extraction
        ↓
Transformation and validation
        ↓
MySQL analytical tables
        ↓
SQL metrics and growth analysis
        ↓
EDA and statistical analysis
        ↓
Merchant opportunity scoring
        ↓
Power BI dashboard
        ↓
Business recommendations
```

## Repository structure

```text
.
├── data/
│   ├── interim/
│   └── processed/
├── notebooks/
│   ├── 01_data_validation.ipynb
│   ├── 02_eda.ipynb
│   ├── 03_statistical_analysis.ipynb
│   └── 04_opportunity_analysis.ipynb
├── powerbi/
├── reports/
│   ├── eda_charts/
│   └── final_findings.md
├── sql/
│   ├── 01_schema.sql
│   ├── 02_data_quality.sql
│   ├── 03_metrics.sql
│   ├── 04_opportunity.sql
│   └── 05_business_questions.sql
├── src/
│   └── phonepe_analytics/
└── tests/
```

## Python pipeline

The reusable project code lives only under `src/phonepe_analytics/`.

- `extract.py` reads the official PhonePe Pulse JSON structure.
- `transform.py` builds clean state- and district-quarter tables.
- `validate.py` checks logical keys, ranges, missing values, signs, and geographic reconciliation.
- `database.py` loads validated data into MySQL and exports analytical views.
- `metrics.py` contains reusable ratio, growth, and opportunity-score calculations.
- `utils.py` contains small shared helpers.

The notebooks are for analysis and communication; reusable transformation logic is kept out of notebook cells.

## SQL organization

The SQL layer is intentionally small and sequential.

1. `01_schema.sql` — MySQL source tables and keys
2. `02_data_quality.sql` — database-level quality summary
3. `03_metrics.sql` — state, district, and national analytical metrics
4. `04_opportunity.sql` — opportunity scoring, sensitivity variants, and shortlist
5. `05_business_questions.sql` — numbered business questions with a query, explanation, and key insight for each task

## Exploratory data analysis

`notebooks/02_eda.ipynb` covers:

- completeness and coverage checks
- descriptive statistics for scale, value, penetration, and growth measures
- univariate distributions and outlier counts
- transaction-category mix
- users vs transactions
- merchants vs transactions
- demand growth vs merchant penetration
- user growth vs merchant growth
- Spearman correlation analysis
- multivariate growth/penetration/scale segmentation
- indexed national growth comparison
- IQR outlier review

Charts produced by EDA belong in `reports/eda_charts/`.

## Core metrics

Important measures include:

- total transactions
- total payment value
- average transaction value
- registered users
- registered merchants
- merchants per 100K registered users
- users per registered merchant
- transactions per registered user
- TPV per registered user
- QoQ transaction, TPV, user, and merchant growth
- same-quarter YoY transaction growth

`transactions_per_merchant` is treated as an ecosystem-intensity proxy, not as a direct count of merchant transactions, because district transaction totals are not merchant-only transactions.

## Opportunity analysis

The opportunity framework combines:

- transaction growth
- transaction intensity
- relative merchant penetration
- registered-user scale

Minimum scale filters reduce unstable rankings from very small districts. The project also calculates an equal-weight score and a score without transaction intensity so the leading districts can be checked under alternative assumptions.

The score is a prioritisation tool, not a causal model or a forecast of business impact.

## Power BI

Power BI uses the cleaned analytical outputs rather than raw PhonePe JSON files. The report is designed to communicate:

- executive payment trends
- merchant landscape and penetration
- district expansion opportunities
- final business recommendations

Power BI assets are stored under `powerbi/`. EDA charts and Power BI screenshots should remain separate.

## Run locally

### 1. Install dependencies

```bash
uv sync
```

### 2. Configure MySQL

Copy `.env.example` to `.env` and set:

```text
MYSQL_HOST=
MYSQL_PORT=
MYSQL_DATABASE=
MYSQL_USER=
MYSQL_PASSWORD=
```

### 3. Extract the official PhonePe source

```bash
uv run python -m phonepe_analytics.extract --raw work/pulse
```

### 4. Transform and validate

```bash
uv run python -m phonepe_analytics.transform
uv run python -m phonepe_analytics.validate
```

### 5. Load MySQL and build analytical views

Create the database named in `MYSQL_DATABASE`, then run:

```bash
uv run python -m phonepe_analytics.database
```

### 6. Run quality checks

```bash
uv run ruff format --check .
uv run ruff check .
uv run pytest
```

### 7. Review notebooks

Run the notebooks in numerical order from `notebooks/`.

## Limitations

- Registered users are cumulative registrations, not active users.
- Registered merchants are registrations, not necessarily active merchants.
- District transaction totals are ecosystem activity and should not be interpreted as merchant-only payments.
- Public data does not include merchant acquisition cost, competitor coverage, active merchant counts, revenue, or realised expansion outcomes.
- Correlation and geographic association do not establish causation.
- Opportunity scores depend on documented thresholds and weights and should be validated through sensitivity analysis and field research.

## Final output

The project is designed to answer one decision clearly: **which states and districts should be investigated first for merchant expansion, and what evidence supports that priority?**

"""Load cleaned CSVs into MySQL 8, execute analysis SQL and export Power BI inputs.

Set MYSQL_HOST, MYSQL_PORT, MYSQL_USER and MYSQL_PASSWORD in your environment.
Run: python src/load_and_analyze.py
Only the three project staging tables in phonepe_portfolio are replaced.
"""
from pathlib import Path
from datetime import datetime, timezone
import json
import os
import mysql.connector
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def run_sql_file(cursor, filename):
    """These project files contain simple statements and no stored procedures."""
    sql = (ROOT / 'sql' / filename).read_text(encoding='utf-8')
    sql = '\n'.join(line for line in sql.splitlines() if not line.lstrip().startswith('--'))
    for statement in sql.split(';'):
        if statement.strip():
            cursor.execute(statement)
            if cursor.with_rows:
                cursor.fetchall()


def main():
    connection = mysql.connector.connect(
        host=os.environ.get('MYSQL_HOST', '127.0.0.1'),
        port=int(os.environ.get('MYSQL_PORT', '3306')),
        user=os.environ['MYSQL_USER'],
        password=os.environ['MYSQL_PASSWORD'],
    )
    try:
        cursor = connection.cursor()
        run_sql_file(cursor, '01_model.sql')
        tables = {'stage_state': 'state_quarter',
                  'stage_district': 'district_quarter',
                  'stage_category': 'category_quarter'}
        # Parameterized batches preserve missing values as SQL NULL.
        # One transaction protects against a partially loaded set of tables.
        for table, filename in tables.items():
            data = pd.read_csv(ROOT / f'data/processed/{filename}.csv')
            rows = data.astype(object).where(pd.notna(data), None).values.tolist()
            cursor.execute(f'DELETE FROM {table}')
            columns = ', '.join(f'`{column}`' for column in data.columns)
            placeholders = ', '.join(['%s'] * len(data.columns))
            query = f'INSERT INTO {table} ({columns}) VALUES ({placeholders})'
            for start in range(0, len(rows), 1000):
                cursor.executemany(query, rows[start:start + 1000])
        connection.commit()
        for filename in ['02_metrics.sql', '03_opportunity.sql', '04_business_questions.sql']:
            run_sql_file(cursor, filename)
        output = ROOT / 'data/analysis'
        output.mkdir(parents=True, exist_ok=True)
        views = ['dim_period', 'dim_state', 'dim_district', 'district_metrics',
                 'state_metrics', 'national_metrics', 'district_opportunities',
                 'investigation_shortlist']
        counts = {}
        for view in views:
            cursor.execute(f'SELECT * FROM {view}')
            data = pd.DataFrame(cursor.fetchall(), columns=cursor.column_names)
            data.to_csv(output / f'{view}.csv', index=False)
            counts[view] = len(data)
        cursor.execute('SELECT VERSION()')
        receipt = {'engine': 'MySQL', 'version': cursor.fetchone()[0], 'rows': counts,
                   'executed_utc': datetime.now(timezone.utc).isoformat()}
        (ROOT / 'data/sql_execution.json').write_text(json.dumps(receipt, indent=2))
        print(json.dumps(receipt, indent=2))
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


if __name__ == '__main__':
    main()

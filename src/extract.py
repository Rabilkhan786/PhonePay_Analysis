"""Extract one pinned Pulse release. Run from repository root; no API credentials."""
from pathlib import Path
import argparse, hashlib, json, re, subprocess
from datetime import datetime, timezone
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
KEY = ['state', 'district', 'period_id']

def clean_name(value):
    # Mechanical formatting only. Never guess equivalence of renamed districts.
    return re.sub(r'\s+', ' ', value.lower().replace('-', ' ')).removesuffix(' district').strip()

def extract(raw):
    out = ROOT / 'data/processed'; out.mkdir(parents=True, exist_ok=True)
    records, categories, manifest = [], [], []
    for family in ['transaction', 'user', 'merchant']:
        base = raw / f'data/map/{family}/hover/country/india'
        for path in sorted(base.rglob('*.json')):
            rel = path.relative_to(base).parts
            if len(rel) == 2: state, level = None, 'state'
            elif len(rel) == 4 and rel[0] == 'state': state, level = clean_name(rel[1]), 'district'
            else: raise ValueError(f'Unexpected path {path}')
            year, quarter = int(rel[-2]), int(path.stem)
            if (year, quarter) > (2026, 2): continue
            assert 2018 <= year <= 2026 and 1 <= quarter <= 4
            payload = path.read_bytes(); obj = json.loads(payload)['data']
            manifest.append({'path':str(path.relative_to(raw)).replace('\\','/'),'sha256':hashlib.sha256(payload).hexdigest()})
            items = obj['hoverDataList'] if family == 'transaction' else [{'name':k, **v} for k,v in obj['hoverData'].items()]
            for item in items:
                name = clean_name(item['name'])
                row = dict(level=level, state=state or name, district=name if state else '', year=year, quarter=quarter, period_id=year*4+quarter-1, family=family, raw_name=item['name'], source_path=manifest[-1]['path'])
                if family == 'transaction':
                    metrics = [m for m in item['metric'] if m['type']=='TOTAL']; assert len(metrics)==1
                    row.update(transactions=metrics[0]['count'], value_inr=metrics[0]['amount'])
                else: row['registered_'+('users' if family=='user' else 'merchants')] = item['registeredCount']
                records.append(row)
    long = pd.DataFrame(records)
    audits, tables = [], {}
    for level in ['state','district']:
        parts=[]
        for family, cols in [('transaction',['transactions','value_inr']),('user',['registered_users']),('merchant',['registered_merchants'])]:
            part=long[(long.level==level)&(long.family==family)]
            duplicates=int(part.duplicated(KEY).sum()); assert duplicates==0, (level,family,'duplicate keys')
            audits.append(dict(check='duplicate keys',table=f'{level}_{family}',count=duplicates))
            parts.append(part[KEY+['year','quarter']+cols])
        joined=parts[0]
        for part in parts[1:]: joined=joined.merge(part,on=KEY+['year','quarter'],how='outer',validate='one_to_one')
        for col in ['transactions','value_inr','registered_users','registered_merchants']:
            for check, count in [('missing',joined[col].isna().sum()),('negative',(joined[col]<0).sum()),('zero',(joined[col]==0).sum())]:
                audits.append(dict(check=check,table=level,column=col,count=int(count)))
            assert not (joined[col]<0).any()
            if col!='value_inr':
                assert ((joined[col].dropna()%1)==0).all(); joined[col]=joined[col].astype('Int64')
        joined=joined.sort_values(KEY).reset_index(drop=True)
        joined.to_csv(out/f'{level}_quarter.csv',index=False)
        tables[level]=joined
    # Category volumes only: this release does not supply category values.
    base=raw/'data/aggregated/transaction/country/india'
    for path in sorted(base.rglob('*.json')):
        rel=path.relative_to(base).parts
        state='india' if len(rel)==2 else clean_name(rel[1])
        year,quarter=int(rel[-2]),int(path.stem)
        if (year,quarter)>(2026,2): continue
        payload=path.read_bytes(); manifest.append({'path':str(path.relative_to(raw)).replace('\\','/'),'sha256':hashlib.sha256(payload).hexdigest()})
        for item in json.loads(payload)['data']['transactionData']:
            m=[m for m in item['paymentInstruments'] if m['type']=='TOTAL']; assert len(m)==1
            categories.append(dict(state=state,year=year,quarter=quarter,period_id=year*4+quarter-1,category_raw=item['name'],transactions=m[0]['count']))
    cat=pd.DataFrame(categories); assert not cat.duplicated(['state','period_id','category_raw']).any()
    cat.to_csv(out/'category_quarter.csv',index=False)
    long[['level','state','district','family','raw_name','source_path','period_id']].to_csv(out/'source_lineage.csv',index=False)
    pd.DataFrame(audits).to_csv(out/'quality_checks.csv',index=False)
    # Reconcile counts, values and registrations independently across geographic cuts.
    measures=['transactions','value_inr','registered_users','registered_merchants']
    d=tables['district'].groupby(['state','period_id'])[measures].sum(min_count=1)
    s=tables['state'].set_index(['state','period_id'])[measures]
    reconciliation=(d-s).add_suffix('_difference').reset_index()
    reconciliation.to_csv(out/'geographic_reconciliation.csv',index=False)
    cc=cat[cat.state!='india'].groupby(['state','period_id']).transactions.sum()
    check=(cc-s.transactions).rename('category_minus_map_count').reset_index()
    check.to_csv(out/'category_reconciliation.csv',index=False)
    coverage=tables['district'].groupby('period_id').agg(rows=('district','size'),states=('state','nunique'))
    coverage.to_csv(out/'period_coverage.csv')
    geo=tables['district'].groupby(['state','district']).period_id.agg(['min','max','count']).reset_index()
    geo['internal_missing_periods']=geo['max']-geo['min']+1-geo['count']
    geo.to_csv(out/'geographic_coverage.csv',index=False)
    git_sha=subprocess.check_output(['git','-C',str(raw),'rev-parse','HEAD'],text=True).strip()
    meta={'repository':'https://github.com/PhonePe/pulse','commit':git_sha,'retrieved_utc':datetime.now(timezone.utc).isoformat(),'analysis_end':'2026-Q2','files':manifest,'rows':{k:len(v) for k,v in tables.items()},'categories':sorted(cat.category_raw.unique())}
    (ROOT/'data/source_manifest.json').write_text(json.dumps(meta,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in meta.items() if k!='files'},indent=2))
    print('Nonzero geographic differences:',(reconciliation.filter(like='_difference').abs()>0.01).sum().to_dict())
    print('Category count mismatches:',int(check.category_minus_map_count.ne(0).sum()))

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--raw',type=Path,required=True)
    extract(p.parse_args().raw.resolve())

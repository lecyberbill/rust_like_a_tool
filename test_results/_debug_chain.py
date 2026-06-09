import asyncio, sys
sys.path.insert(0, '.')
from brain.orchestrator import Orchestrator
from pathlib import Path

async def test():
    o = Orchestrator()
    base = 'test_results/bench_data'
    r = {'plan_id':'test_chain','intent_analysis':'test','steps':[
        {'step':1,'primitive':'io.read_file','args':{'source':f'{base}/data_100000.csv','destination':f'{base}/s01.csv'}},
        {'step':2,'primitive':'data.filter','args':{'column_name':'active','operator':'equals','value':'true','has_headers':True},'depends_on':[1]},
        {'step':3,'primitive':'data.groupby','args':{'groupby_columns':'category','aggregate_column':'price','operation':'mean'},'depends_on':[2]},
    ]}
    for s in r['steps']:
        if not s['args'].get('destination'):
            s['args']['destination'] = f'{base}/s{s["step"]:02d}.csv'
    ok = await o.run_recipe(r)
    print('RESULT:', 'SUCCESS' if ok else 'FAILED')
    for s in r['steps']:
        d=s['args'].get('destination','')
        if d:
            p=Path(d); print(f'  {p.name}: exists={p.exists()}',end='')
            if p.exists(): print(f' size={p.stat().st_size}',end='')
            print()

asyncio.run(test())

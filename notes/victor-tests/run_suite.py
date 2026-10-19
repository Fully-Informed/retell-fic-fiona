"""Run the Victor test suite against baseline (live v15) and candidate (sandbox LLM), then print results.
Usage: python3 -I run_suite.py [repeats] [variants...]
Batch IDs are recorded in batches.txt as they are created; if batches.txt already holds
non-empty IDs, those are reused (resume) instead of launching new batches."""
import json,os,sys,time,urllib.request,urllib.error
KEY=os.environ['RETELL_API']; BASE='https://api.retellai.com/'
def call(path,body=None):
    r=urllib.request.Request(BASE+path,data=json.dumps(body).encode() if body else None,method='POST' if body else 'GET',headers={'Authorization':'Bearer '+KEY,'Content-Type':'application/json'})
    for attempt in range(5):
        try: return json.load(urllib.request.urlopen(r,timeout=60))
        except urllib.error.HTTPError as e:
            msg=e.read().decode(errors='replace')
            if e.code in (429,500,502,503,504) and attempt<4 and body is None: time.sleep(5*(attempt+1)); continue
            raise RuntimeError(f'{e.code} {path}: {msg}')
        except (urllib.error.URLError,TimeoutError) as e:
            if attempt<4 and body is None: time.sleep(5); continue
            raise
here=os.path.dirname(os.path.abspath(__file__))
BFILE=os.path.join(here,'batches.txt'); OUT=os.path.join(here,'test_results'); os.makedirs(OUT,exist_ok=True)
# test case definitions are bound to one llm_id, so each variant has its own copies
IDS={'candidate':[c['id'] for c in json.load(open(os.path.join(here,'test_cases.json')))],
     'baseline':[c['id'] for c in json.load(open(os.path.join(here,'test_cases_baseline.json')))]}
ENGINES={'baseline':{"type":"retell-llm","llm_id":"64c9b371d36eb5ff8f78dfe4c48162d6","version":15},
         'candidate':{"type":"retell-llm","llm_id":"llm_832650def343e246900dffa4c239"}}
reps=int(sys.argv[1]) if len(sys.argv)>1 else 2
variants=sys.argv[2:] or list(ENGINES)
tag=os.environ.get('SUITE_TAG','')  # e.g. "v2" for a re-run; prefixes rep numbers in filenames
# resume
jobs=[]
if os.path.exists(BFILE):
    for line in open(BFILE):
        p=line.split()
        if len(p)>=4 and p[0]==(tag or '-'): jobs.append((p[1],int(p[2]),p[3]))
if not jobs:
    for rep in range(1,reps+1):
        for n in variants:
            j=call('create-batch-test',{"test_case_definition_ids":IDS[n],"response_engine":ENGINES[n]})['test_case_batch_job_id']
            jobs.append((n,rep,j))
            with open(BFILE,'a') as f: f.write(f"{tag or '-'} {n} {rep} {j}\n")
            print('launched',n,rep,j,flush=True)
else: print('resuming',jobs,flush=True)
while True:
    st=[call('get-batch-test/'+j) for _,_,j in jobs]
    print(time.strftime('%H:%M:%S'),[(s['status'],s['pass_count'],s['fail_count'],s['error_count']) for s in st],flush=True)
    if all(s['status']=='complete' for s in st): break
    time.sleep(20)
def list_runs(j):
    items,pk=[],None
    while True:
        r=call(f'v2/list-test-runs/{j}?limit=100'+(f'&pagination_key={pk}' if pk else ''))
        if isinstance(r,list): return r
        items+=r.get('items',[])
        pk=r.get('pagination_key')
        if not r.get('has_more') or not pk: return items
for (n,rep,j),s in zip(jobs,st):
    print(f"\n### {n} rep{rep} {j}: pass {s['pass_count']}/{s['total_count']} fail {s['fail_count']} error {s['error_count']}")
    for r in list_runs(j):
        full=call('get-test-run/'+r['test_case_job_id'])
        name=full['test_case_definition_snapshot']['name']
        json.dump(full,open(os.path.join(OUT,f"{n}_{tag}{rep}_{name}.json"),'w'),indent=1)
        print(f"  [{full['status']}] {name}: {(full.get('result_explanation') or '')[:600]}")

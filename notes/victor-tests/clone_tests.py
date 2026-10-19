import json,os,urllib.request
KEY=os.environ['RETELL_API']
def call(path,body=None):
    r=urllib.request.Request('https://api.retellai.com/'+path,data=json.dumps(body).encode() if body else None,method='POST' if body else 'GET',headers={'Authorization':'Bearer '+KEY,'Content-Type':'application/json'})
    return json.load(urllib.request.urlopen(r))
out=[]
for c in json.load(open('test_cases.json')):
    d=call('get-test-case-definition/'+c['id'])
    body={k:d[k] for k in ('name','user_prompt','metrics','dynamic_variables','tool_mocks','llm_model')}
    body['response_engine']={"type":"retell-llm","llm_id":"64c9b371d36eb5ff8f78dfe4c48162d6","version":15}
    n=call('create-test-case-definition',body)
    out.append({"name":d['name'],"id":n['test_case_definition_id']}); print(out[-1],n['response_engine'])
json.dump(out,open('test_cases_baseline.json','w'),indent=1)

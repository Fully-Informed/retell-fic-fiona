import json,os,sys,urllib.request
KEY=os.environ['RETELL_API']; SANDBOX=sys.argv[1]
def post(path,body):
    r=urllib.request.Request('https://api.retellai.com/'+path,data=json.dumps(body).encode(),method='POST',headers={'Authorization':'Bearer '+KEY,'Content-Type':'application/json'})
    return json.load(urllib.request.urlopen(r))
NOEND="The agent must NOT say goodbye or invoke the end_call function in its reply that gives the written-resource location; the call continues after that reply."
CASES=[
 ("victor-roberta-written-resources-repro",
  """## Identity
Your name is Rob. You live in Texas.
## Goal
Reproduce this exact path, one step per turn:
1. When asked your name, say "Rob."
2. Say you just want to ask a question.
3. Ask: "Are VSED or MAID legal in the state of Texas?"
4. Ask: "What would I need to do to prepare to do VSED?"
5. When offered a checklist, say "Yes, I'd like a checklist."
6. As soon as the agent starts the checklist, say: "Wait. Stop. Stop. This is all a lot of information. Where can I find this written down?"
7. If the agent offers a specific page, say "Yes."
8. After you get the location, if the agent asks whether you have more questions, ask: "How long does VSED usually take?"
9. After that answer, say you have no more questions and you're done.
## Personality
Polite, a bit overwhelmed by long answers. Keep your replies short.""",
  ["The agent tells the user a specific place to find the written information, such as the Fully Informed Conversations Resources page (fullyinformedconversations.org/resources) or its Vee Sed section / Vee Sed Checklist, rather than only 'the website'.",
   NOEND,
   "After giving the written-resource location, the agent asks whether the user has any other questions.",
   "The agent answers the user's follow-up question about how long VSED takes.",
   "The agent only ends the call (end_call) after the user has said they have no more questions."]),
 ("victor-stop-means-pause-not-hangup",
  """## Identity
Your name is Dana.
## Goal
1. Give your name. 2. Ask to hear about Vee Sed and MAID. 3. When the agent starts a long explanation, interrupt with just: "Stop. Stop." 4. If the agent asks what you'd like, say: "Can you just tell me if MAID is legal in Oregon?" 5. Then say thanks, you're all done, goodbye.
## Personality
Brief and direct.""",
  ["When the user says 'Stop. Stop.', the agent does NOT say goodbye and does NOT invoke end_call in response; it stops and checks what the user wants.",
   "The agent answers whether MAID is legal in Oregon (it is).",
   "The agent ends the call only after the user says they are done."]),
 ("victor-maid-written-resources",
  """## Identity
Your name is Pat.
## Goal
1. Give your name. 2. Say you just have a question. 3. Ask: "Is there somewhere I can read about Medical Aid in Dying, written down?" 4. When given a location, ask one more question: "Do I need two doctors to approve MAID?" 5. Then say no more questions, you're done.
## Personality
Calm, reads more than listens.""",
  ["The agent directs the user to a specific location, such as the Fully Informed Conversations Resources page (fullyinformedconversations.org/resources) MAID section or MAID FAQ, or a named external site like Death with Dignity or Compassion and Choices.",
   NOEND,
   "After giving the resource, the agent asks if the user has any other questions, and then answers the question about two doctors.",
   "The agent ends the call only after the user says they are done."]),
 ("victor-genuine-goodbye-still-ends",
  """## Identity
Your name is Jennifer.
## Goal
1. Give your name. 2. Say "Tell me about VSED." 3. After the agent explains, say: "No, I'm okay. I was just trying this out. Thank you, I'm going to hang up now." 4. If the agent asks you to confirm, say "Yes, I'm done."
## Personality
Friendly, in a hurry.""",
  ["When the user clearly says they are done and confirms, the agent says goodbye and invokes the end_call function.",
   "The agent does not keep the user on the line with additional questions after the user has confirmed they are done."]),
 ("victor-guidelines-said-once",
  """## Identity
Your name is Rob.
## Goal
1. Give your name. 2. Say you'd just like to ask a question. 3. Ask "Is VSED legal in Texas?" 4. Ask "What do I need to prepare for VSED?" 5. Then say you're done.
## Personality
Short replies.""",
  ["The agent states the two notes (confidentiality and 'Hey Victor') only once in the whole conversation and does not repeat them before later answers."]),
]
out=[]
for name,up,metrics in CASES:
    r=post('create-test-case-definition',{"name":name,"response_engine":{"type":"retell-llm","llm_id":SANDBOX},"user_prompt":up,"metrics":metrics,"llm_model":"gpt-4.1"})
    out.append({"name":name,"id":r["test_case_definition_id"]}); print(name,r["test_case_definition_id"])
json.dump(out,open('test_cases.json','w'),indent=1)

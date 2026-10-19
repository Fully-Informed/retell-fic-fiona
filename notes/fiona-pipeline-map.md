# Fiona pipeline — master map (as of 2026-10-19)

Sources: Retell API, Zapier export "Fiona Merged Workflow (Retell)" (38 steps), Airtable Meta API (base `apphcWCvUy390h6qv`
"FIC Development"), Documint API (template "FIC Advance Directive" `6601b0ad4d30e7e3b43e2ff4`).
Not readable by API (still needed from a human): Airtable automations (trigger, Documint script, email), any other Zaps
(anonymization, feedback form, Victor logging).

## 1. Stages

| # | Stage | Where | What it does | Notes |
|---|---|---|---|---|
| 0 | Call | Retell agent `12110cf1…` (web v13, phone v12 — identical prompt), LLM claude-4.5-haiku | Scripted interview | Webhook is account-level (not on agent) |
| 1 | Gate | Zap step 2 | Continue if transcript exists, event contains "analyzed", agent = Fiona | Victor calls dropped here |
| 2 | Classify | Zap step 3, gpt-5.4-mini, temp 1.0 | NO_PHONE / PHONE_INCOMPLETE / PHONE_COMPLETE | Keys on the phrase "That's everything I need" |
| 3a | Incomplete | Zap 6–10 | GPT extracts name/phone/pin → find/create record, append transcript | Resume support |
| 3b | Complete, multi-part | Zap 13–27 | Path if transcript contains "Let's continue where we left off"; GPT extracts phone → find record → append → extraction chain → update record | |
| 3c | Complete, one part | Zap 12, 28–38 | Extraction chain → create record | George's call |
| 4 | Extract | Zap 28 (and 17), **Claude Sonnet 4.5, temp 0.8** | Transcript → 21-key JSON | Prompt: `zap_extraction_prompt.txt` |
| 5 | Parse | Zap 29 regex `\{(?:[^{}]|\{[^{}]*\})*\}` → 30 JS `JSON.parse` | | Nested braces >1 level break it; reads a `priorities` key the prompt never asks for |
| 6 | Require email | Zap 31 | Stop if no email | Silent stop — no alert |
| 7 | Transcript rewrite | Zap 32–33 Formatter (Agent→Fiona, User→firstname), 37 gpt-5.4-mini temp 0.8 "copy edit" | Produces the transcript the caller is emailed | 53% textual similarity to raw for George; keeps phone + PIN |
| 8 | Dates | Zap 34–36 | chat-datetime, form-date, pdf_date | |
| 9 | Store | Zap 38 → Airtable "Fiona Calls" `tblXTUkO7ONYj0H3q` | 33 field mappings | Zap labels table "Felicia Chats" (stale label, same id) |
| 10 | Generate | Airtable automation → Documint template | Fills PDF, writes "Documint PDF" attachment | "Delay Hack" formula = {Documint PDF}; automation not visible |
| 11 | Deliver | Airtable automation | Emails PDF + formatted transcript + recording link | Email body/conditions not visible |
| 12 | After | Airtable checkboxes "Sent Feedback Form", "Send to Anon Zap ➡️", "Anonymized ✅" | Other Zaps not in the export | |

## 2. Field contract (transcript → Airtable → template)

| Extractor key | Airtable field | Documint token | In template? |
|---|---|---|---|
| user-fullname | user-fullname | user_fullname | yes |
| firstname | firstname | — | email only |
| values / beliefs | values / beliefs | values / beliefs | yes |
| (priorities — parsed, never extracted) | priorities | — | no |
| primary-rep-fullname / secondary-rep-fullname | same | primary_rep_fullname / secondary_rep_fullname | yes |
| choice-terminal / -functional / -confused / -nonfunctional / -coma | same | choice_* | yes (blank → checkbox list) |
| cpr-hospital / cpr-home | same | cpr_* | yes |
| pain-relief | pain-relief | pain_relief | yes |
| other-wishes | other-wishes | other_wishes | yes (only free-text slot) |
| state | state | state | yes (notary logic: MO, NC/SC/WV; extra forms MI, WI) |
| ready, adform-choice, usa-resident, email, pin | same (pin not mapped) | — | no |
| (Zap dates) | chat-datetime, form-date, pdf_date | chat_datetime, form_date, pdf_date | yes |
| — | current-health, pain-relief-detail, organ-choice, organ-use, funeral-preferences | — | **vestigial**: fields exist, nothing writes or reads them; PDF organ/remains sections are static blanks |

Missing everywhere: feeding tubes / artificial nutrition as a separate choice, "undecided/unresolved" items, test-mode flag,
anything said outside its anchored question, template/prompt version id.

## 3. How George's defects arise

- **F01 feeding tube**: no key exists; `other-wishes` only reads the final "anything else?" answer ("fine for now" → blank);
  template definition of Life Support includes ANH → silent default.
- **F02 test label**: no key, no template slot.
- **F03 signing**: Fiona's prompt says witnesses + notary; template's state logic has no Texas branch (generic "not necessary").
- **F04 MPOA disclosure**: template has no state-specific disclosure except MI/WI.
- **F05 CPR**: extractor "closest general option + quote provisions" glues stock text to the caveat; no reconciliation step.
- **F06 PIN/phone**: carried into the GPT-rewritten transcript that's emailed.
- **F07 version**: nothing records prompt/extractor/template versions.
- Extractor "where to find" anchors quote the script verbatim and have drifted (e.g. CPR intro, "15 to 20 minutes").

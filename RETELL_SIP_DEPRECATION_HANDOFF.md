# Retell SIP Deprecation — Impact Analysis & Handoff

**Date:** 2026-09-09
**Trigger:** Retell AI service notice — "Update your inbound call routing" (deadline **2026-09-30**), affecting workspace **FIC Admin's (`org_lk8qBaLrI8TKo9CK`)**.
**Repos in scope:** `retell-fic-fiona` (this repo) and `retell-fic-victor` (sibling repo, same architecture).

---

## TL;DR

**No code change is required in these frontend repos to survive this deprecation.**

The deprecation is about **SIP / phone-call (PSTN) routing** — the "dial-to-SIP" custom-telephony
path. These repos are **web-call (browser / WebRTC) apps**. They never touch SIP, the deprecated
LiveKit SIP host, or the `Register Phone Call` API. The fix for the actual deprecation lives in the
**Retell dashboard telephony configuration**, not in this code.

This document exists so the same conclusion can be verified quickly for `retell-fic-victor` and so
there is a written record of *why* nothing was changed.

---

## What the deprecation notice is actually about

The notice says calls from the workspace are being routed to the deprecated SIP endpoint:

```
sip:5t4n6j0wnrl.sip.livekit.cloud        (deprecated)
```

and must move to Retell's supported SIP server:

```
sip:sip.retellai.com                     (supported)
sip:{call_id}@sip.retellai.com           (dial-to-SIP destination)
```

This is **custom telephony / dial-to-SIP** — i.e., routing real phone (PSTN) calls into Retell over
SIP. Per Retell's custom-telephony docs, the `sip.retellai.com` change and the CIDR allowlist apply
**exclusively to SIP-based voice infrastructure and phone telephony**. They do **not** apply to web
calls or browser WebRTC.

The old `5t4n6j0wnrl.sip.livekit.cloud` host is a **per-workspace SIP trunk** endpoint — the kind of
thing configured against a phone number / elastic SIP trunk **in the Retell dashboard or your
telephony provider (e.g. Twilio) config**, not in application code.

## Why these frontend repos are not affected

`retell-fic-fiona` is a customized copy of Retell's React/Node web-call demo. The entire call path is
WebRTC, not SIP:

1. **Backend** — `api/create-web-call.js`
   `POST https://api.retellai.com/v2/create-web-call` with `{ agent_id }`, returns `access_token`.
   This is Retell's **current, non-deprecated** web-call endpoint (Call API v2).

2. **Frontend** — `src/App.tsx`
   `retellWebClient.startCall({ accessToken })` using `retell-client-js-sdk`
   (which uses `livekit-client` for WebRTC under the hood).
   This is the **current** web-call SDK usage.

Key points confirming no impact:

- **No SIP anywhere.** A full search of the repo found no `sip`, no `5t4n6j0wnrl`, no
  `livekit.cloud` host, no `Register Phone Call`, no dial-to-SIP, no `from_number` / `to_number`.
- **No hardcoded transport host.** For web calls, the WebRTC/LiveKit connection URL is returned
  dynamically inside the `access_token` at call-registration time. The app never pins the deprecated
  host, so there is nothing here to repoint.
- **Already on the current API/SDK flow.** `/v2/create-web-call` + `startCall({ accessToken })` is
  exactly what Retell documents today. Nothing deprecated is in use.

## Where the real fix lives (action item — outside these repos)

The workspace-level notice was almost certainly triggered by **phone-number / inbound-routing
configuration in the Retell dashboard** (or an elastic SIP trunk in a telephony provider pointing at
the old LiveKit host), independent of these web apps. To resolve the notice:

- In the **Retell dashboard**, review any **phone numbers / SIP trunks / custom-telephony**
  configuration for workspace `org_lk8qBaLrI8TKo9CK` and ensure they route to
  `sip:sip.retellai.com` (dial-to-SIP destination `sip:{call_id}@sip.retellai.com`).
- If a provider (e.g. Twilio) or on-prem PBX routes calls to Retell, update its SIP destination to
  `sip.retellai.com` (TCP recommended: `sip:sip.retellai.com;transport=tcp`) and **allowlist**
  Retell's CIDR ranges from the custom-telephony docs:
  `18.98.16.120/30`, `3.42.144.0/23`, `153.57.128.0/18`, and (certain US traffic)
  `143.223.88.0/21`, `161.115.160.0/19`. Verify against the live docs before applying.
- If the workspace does **not** actually do inbound phone calls, this may simply be a stale/leftover
  number configuration that can be removed — worth confirming with Retell support.

## Handoff: `retell-fic-victor`

`retell-fic-victor` is described as the same kind of customized web-call frontend. To confirm it is
equally unaffected, verify the same three things there:

1. Backend calls `https://api.retellai.com/v2/create-web-call` and returns `access_token`
   (check its `api/` route, e.g. `api/create-web-call.js`).
2. Frontend uses `retellWebClient.startCall({ accessToken })` (check `src/App.tsx`).
3. A repo-wide search for `sip`, `livekit.cloud`, `5t4n6j0wnrl`, `register-phone-call`,
   `from_number`, `to_number` returns **no** telephony/SIP usage.

If all three hold, **no code change is needed in victor either** — same conclusion as fiona. If any
of them differ (e.g. victor registers phone calls or dials to SIP), re-evaluate: that repo would then
need its SIP destination updated to `sip:{call_id}@sip.retellai.com`.

## Optional (NOT required for the deprecation)

- `retell-client-js-sdk` is pinned at `2.0.3`; the latest is `2.0.8`. This is **unrelated** to the
  SIP deprecation and the current pin works with the current API. If you ever choose to bump it, do it
  as a separate, independently-tested change — not as part of this deprecation response.

---

*Prepared as a read-only analysis. No frontend or functional code was changed, so the Vercel
redeploy triggered by this commit is behavior-identical to the previous deploy — safe to test.*

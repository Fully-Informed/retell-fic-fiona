# Retell Deprecations — Impact Analysis & Handoff

**Repos in scope:** `retell-fic-fiona` (this repo, migrated) and `retell-fic-victor` (sibling repo, same architecture — apply the same change).
**Workspace:** FIC Admin's (`org_lk8qBaLrI8TKo9CK`)

Two Retell notices arrived. Only the second needs a code change.

| Notice | Affects these repos? | Action |
| - | - | - |
| 1. Inbound SIP routing (`sip:5t4n6j0wnrl.sip.livekit.cloud` → `sip:sip.retellai.com`) | **No** | Retell dashboard / Retell support (see below) |
| 2. Create Web Call v2 / browser SDK v2 deprecated | **Yes** | Code change — done in fiona, **repeat in victor** |

---

## Notice 2 — Create Web Call v2 → v3 (code change)

Retell deprecated `POST /v2/create-web-call` and `retell-client-js-sdk` 2.x
(migration guide: https://docs.retellai.com/deprecation-notice/2026/09-30_create_web_call_v2).
The notice lists `POST /v2/create-web-call` via **axios**, which is exactly `api/create-web-call.js`.

We used the guide's minimal path, "retain an existing server-created call flow":
keep the server route and `RetellWebClient` (still shipped in SDK 3.x), switch the
endpoint to v3, and forward the new response fields. The API key stays on the
server, and **no new public key or Vercel env var is needed**.

### Changes made in fiona (apply the same to victor)

1. **`package.json`** — `"retell-client-js-sdk": "^2.0.3"` → `"^3.0.1"`, then `npm install` to update `package-lock.json`.

2. **`api/create-web-call.js`** — URL `https://api.retellai.com/v2/create-web-call` → `https://api.retellai.com/v3/create-web-call`. Request body is unchanged.
   The v3 response is `{ call_id, access_token, transport, ice_servers, expires_at }` (connection details only, not the full call object).

3. **`src/App.tsx`**
   - Extend `RegisterCallResponse` with `call_id`, `transport`, `ice_servers`.
   - Forward them to `startCall()`, and turn on audio samples:
     ```ts
     await retellWebClient.startCall({
       callId: registerCallResponse.call_id,
       accessToken: registerCallResponse.access_token,
       transport: registerCallResponse.transport,
       iceServers: registerCallResponse.ice_servers,
       emitRawAudioSamples: true,
     });
     ```
   - **Replace the `agent_start_talking` / `agent_stop_talking` handlers.** v3 calls use the `gateway`
     transport, which does **not** deliver those events (confirmed in the SDK source). The halo is now driven
     continuously by the agent's audio level from the `audio` event: a smoothed 0..1 level is written to a
     `--level` CSS variable on the halo, and the CSS cross-fades a grey layer into a green one that swells with
     volume. Copy fiona's `src/App.tsx` (the `audio` handler, `haloRef`, and the halo markup) and the `.halo`
     rules in `src/App.css` into victor.

4. Verify: `CI=true npm run build` must pass.

### What to test after deploy

- Click/tap → call connects, agent talks, click again → call ends and the "Click or Tap" instructions come back.
- The **green halo** follows the agent's voice: grey while listening, green and brighter/larger as the agent
  speaks louder, fading back to grey shortly after the agent stops. Tuning constants are at the top of
  `src/App.tsx`: `NOISE_FLOOR` (raise if silence shows green), `FULL_SCALE` (lower if the halo rarely gets
  bright), `ATTACK_MS` / `RELEASE_MS` (how fast it rises / fades).
- In Retell's dashboard, new web calls show up normally. Once both fiona and victor are deployed, the weekly
  "Create Web Call v2" notice should stop (it lists the last request time and source IP).

### Notes

- `update` and `metadata` events are also not delivered on v3 calls. The app only logged them, so nothing user-visible changes.
- `RetellWebClient` is marked deprecated in SDK 3.x and is **removed in 4.0**. Migrating to `RetellClient` (browser-side
  call creation with a Retell **public key** + allowed domain) is the longer-term path, but it's a bigger change and not
  required for this deadline.

---

## Notice 1 — Inbound SIP routing (no code change)

These repos are browser web-call apps and never use SIP. The deprecated
`sip:5t4n6j0wnrl.sip.livekit.cloud` endpoint is for phone (PSTN) routing. Our inbound
numbers are **managed inside Retell** and there is no other backend, so the fix is not in code:

- Retell dashboard → Phone Numbers: check each inbound number for any SIP / termination URI still pointing at the
  old `...livekit.cloud` host and change it to `sip:sip.retellai.com`.
- If there is no editable SIP field (typical for Retell-managed numbers), ask Retell support to confirm the numbers
  in `org_lk8qBaLrI8TKo9CK` will be migrated before 2026-09-30.

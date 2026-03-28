# Conversational Voice MVP (Twilio + LiveKit + FastAPI)

This project handles inbound phone calls with this path:

`Caller -> Twilio Number -> FastAPI Webhook (TwiML) -> LiveKit SIP -> LiveKit Room -> Agent (ElevenLabs STT, OpenAI LLM, Deepgram TTS)`

This MVP always uses `TWILIO_PHONE_NUMBER2` as the target number.

## Terms (quick definitions)

- **Trunk (inbound trunk):** a LiveKit SIP configuration that tells LiveKit which phone number(s) it accepts and which SIP username/password must be used.
- **Dispatch rule:** tells LiveKit where to route accepted calls (for this MVP, each call goes to its own room with prefix `call-`).
- **Webhook:** Twilio sends an HTTP request to your FastAPI endpoint when a call arrives.
- **TwiML:** XML returned by your FastAPI webhook, telling Twilio what to do next (here: `<Dial><Sip>...</Sip></Dial>`).

## Where to do each setup step

- **Local terminal (your machine, in `fresh_start`):** install deps, run app, run agent worker, run `lk` CLI commands.
- **Twilio Console:** buy/manage phone number and set voice webhook URL on the number.
- **LiveKit Cloud / LiveKit API via `lk` CLI:** create inbound trunk + dispatch rule.
- **Tunnel provider (ngrok/cloudflared/localtunnel):** expose your local FastAPI server to public HTTPS for Twilio callbacks.

## 0) Prerequisites

- Python 3.10+ installed
- LiveKit CLI installed and authenticated (`lk auth`)
- A Twilio phone number (already in your env as `TWILIO_PHONE_NUMBER2`)
- API keys set for OpenAI, ElevenLabs, Deepgram, LiveKit

## 1) Local install (Terminal: `fresh_start`)

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## 2) Environment values (Terminal + `.env`)

Copy `.env.example` to `.env` and fill values.

Required for this MVP:

- `TWILIO_PHONE_NUMBER2` (target number; this is the number you call)
- `TWILIO_AUTH_TOKEN`
- `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`, `LIVEKIT_SIP_URI`
- `LIVEKIT_INBOUND_TRUNK_USERNAME`, `LIVEKIT_INBOUND_TRUNK_PASSWORD`
- `OPENAI_API_KEY`, `ELEVENLABS_API_KEY`, `DEEPGRAM_API_KEY`
- `PUBLIC_WEBHOOK_BASE_URL` (your public tunnel URL, no trailing slash)

Important:

- If you have two Twilio numbers, this MVP ignores `TWILIO_PHONE_NUMBER1` and uses only `TWILIO_PHONE_NUMBER2`.
- The trunk username/password in `.env` must match what LiveKit inbound trunk expects.

## 3) Start FastAPI locally (Terminal: `fresh_start`)

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Keep this terminal running.

## 4) Create a public HTTPS tunnel (Terminal, separate window)

Twilio must reach your webhook over public HTTPS.

Example with ngrok:

```bash
ngrok http 8000
```

Use the HTTPS URL ngrok prints (example: `https://abc123.ngrok-free.app`) as:

- `PUBLIC_WEBHOOK_BASE_URL` in `.env`

Then restart FastAPI so config reloads.

## 5) Create LiveKit SIP resources (Terminal: `fresh_start`)

Generate config files from your `.env`:

```bash
python scripts/render_livekit_configs.py
```

Create inbound trunk and dispatch rule:

```bash
lk sip inbound create livekit/inbound-trunk.json
lk sip dispatch create livekit/dispatch-rule.json
```

Optional (bind dispatch to one trunk only):

```bash
lk sip dispatch create livekit/dispatch-rule.json --trunks "<trunk-id>"
```

## 6) Configure your Twilio number (Twilio Console)

In Twilio Console:

1. Go to **Phone Numbers -> Manage -> Active numbers**.
2. Open the number that equals `TWILIO_PHONE_NUMBER2`.
3. Under **Voice Configuration**:
  - **A call comes in**: `Webhook`
  - **Method**: `HTTP POST`
  - **URL**: `https://<your-public-url>/twilio/voice`

Optional status callback URL:

- `https://<your-public-url>/twilio/status`

## 7) Start the LiveKit agent worker (Terminal: `fresh_start`)

```bash
python agent_worker.py dev
```

Keep this terminal running too.

## 8) Test call flow

1. Call `TWILIO_PHONE_NUMBER2` from any phone.
2. Twilio hits `/twilio/voice`.
3. FastAPI returns TwiML that dials LiveKit SIP.
4. LiveKit dispatches caller to a `call-*` room.
5. Your agent joins and talks.

## Setup checklist

- FastAPI running on port `9000`
- Public HTTPS tunnel running to port `9000`
- `PUBLIC_WEBHOOK_BASE_URL` matches tunnel URL
- Twilio number webhook points to `/twilio/voice` using `POST`
- LiveKit inbound trunk created for `TWILIO_PHONE_NUMBER2`
- LiveKit dispatch rule created
- Agent worker running
- Test call reaches agent

## Endpoints

- `GET /healthz` health check
- `POST /twilio/voice` inbound Twilio webhook (signature validated)
- `POST /twilio/status` optional Twilio status callback


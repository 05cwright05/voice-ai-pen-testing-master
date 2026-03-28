# Conversational Voice MVP (Twilio + LiveKit + FastAPI)

This is a minimal, clean MVP that connects:

- Twilio inbound phone calls
- LiveKit SIP + room dispatch
- LiveKit voice agent with:
  - ElevenLabs STT
  - OpenAI LLM
  - Deepgram TTS

It is configured to use `TWILIO_PHONE_NUMBER2` as the target number.

## 1) Install

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## 2) Environment

Copy `.env.example` to `.env` and fill values.

Required notes:

- `TWILIO_PHONE_NUMBER2` is the only phone number used by this MVP.
- `LIVEKIT_INBOUND_TRUNK_USERNAME` and `LIVEKIT_INBOUND_TRUNK_PASSWORD` must match in:
  - LiveKit inbound trunk auth
  - TwiML `<Sip username="..." password="...">`
- `PUBLIC_WEBHOOK_BASE_URL` must be your public HTTPS URL that Twilio hits.

## 3) Create LiveKit SIP resources (best-practice flow)

Generate JSON configs from your `.env`:

```bash
python scripts/render_livekit_configs.py
```

Create inbound trunk and dispatch rule:

```bash
lk sip inbound create livekit/inbound-trunk.json
lk sip dispatch create livekit/dispatch-rule.json
```

If you want the dispatch rule bound to a specific trunk:

```bash
lk sip dispatch create livekit/dispatch-rule.json --trunks "<trunk-id>"
```

## 4) Configure Twilio phone number webhook

In Twilio Console, set the voice webhook for your purchased number to:

`POST https://<your-public-url>/twilio/voice`

This FastAPI endpoint returns TwiML that dials:

`sip:<TWILIO_PHONE_NUMBER2>@<LIVEKIT_SIP_HOST>;transport=tcp`

with your inbound trunk username/password.

## 5) Run services

Start FastAPI webhook server:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 9000
```

Start LiveKit agent worker:

```bash
python agent_worker.py dev
```

Then call `TWILIO_PHONE_NUMBER2` from any phone.

## Endpoints

- `GET /healthz` health check
- `POST /twilio/voice` inbound Twilio voice webhook (validated)
- `POST /twilio/status` optional status callback receiver

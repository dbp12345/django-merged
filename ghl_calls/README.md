# GHL Calls Setup

This app receives GoHighLevel call webhooks and stores the call metadata in Django.

## Endpoint

Configure your GoHighLevel webhook target as:

`https://<your-domain>/api/webhooks/ghl-calls/`

The Django view accepts signed webhook requests using either:

- `X-GHL-Signature`
- `X-WH-Signature`

Unsigned requests are rejected unless `GHL_CALLS_ALLOW_UNSIGNED_WEBHOOKS=1` is set. That bypass should only be used for local testing.

## Expected GHL payload shape

The app currently stores call events from `OutboundMessage` webhooks when the payload looks like a phone call, for example:

- `messageType=CALL`
- `callStatus` present
- `callDuration` present

If GHL later sends transcript text in the webhook payload, the app saves it; otherwise transcript fields remain empty and GHL stays the source of truth for transcript playback in the UI.

## Optional environment variables

- `GHL_WEBHOOK_PUBLIC_KEY`
  Default in settings: current GHL Ed25519 public key
- `GHL_WEBHOOK_LEGACY_PUBLIC_KEY`
  Default in settings: legacy GHL RSA public key
- `GHL_CALLS_ALLOW_UNSIGNED_WEBHOOKS`
  Default: `0`

## Deploy checklist

1. Install dependencies:
   `pip install -r requirements.txt`
2. Apply migrations:
   `python manage.py migrate`
3. Point the GoHighLevel webhook to `/api/webhooks/ghl-calls/`.
4. Send a test call with recording enabled.

## Notes

- Calls are stored in the `GHLCall` model and visible in Django admin once migrated.
- Raw webhook payloads are stored in `GHLCallWebhookEvent` for debugging.

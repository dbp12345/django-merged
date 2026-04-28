# Integration Fix Summary

## Context

Production flow is:

```text
VS Code -> GitHub dev -> EC2/Lightsail -> https://prod.vectorops.xyz/admin/
```

After merging Chloe's subproject apps into the main Django project, these production integrations appeared broken:

- `integrations`
- `ghl_calls`
- `learndash`
- `learndash_webhook`

The source subproject is:

```text
C:\Users\cyafei\programmingbiz
```

## What Was Found

The copied app source files match the subproject source for:

- `integrations`
- `ghl_calls`
- `learndash`
- `learndash_webhook`

So the issue was not missing app files.

The main problems were configuration and URL wiring:

1. Chloe's subproject exposed public integration URLs:

```text
/oauth/start/
/oauth/callback/
/api/webhooks/ghl-calls/
/api/webhooks/ghl-calls/transcript/
/api/webhooks/learndash/
```

2. The merged main project only exposed those apps under admin tool paths:

```text
/admin/tools/integrations/oauth/start/
/admin/tools/integrations/oauth/callback/
/admin/tools/ghl-calls/
/admin/tools/ghl-calls/transcript/
/admin/tools/learndash-webhook/
```

3. The merged project expects GHL/LearnDash secrets from environment variables. Chloe's subproject had several GHL defaults embedded in `core/settings.py`; the merged project intentionally blanked those defaults.

4. The old subproject used `GHL_DJANGO_Role_ID`, while the sync code reads `GHL_DJANGO_ROLE_FIELD_ID`.

## Changes Made

Code changes:

- `core/urls.py`
  - Restored the old public OAuth and webhook paths.
  - Kept the existing `/admin/tools/...` paths.

- `core/settings.py`
  - Added compatibility so either `GHL_DJANGO_ROLE_FIELD_ID` or old `GHL_DJANGO_Role_ID` can be used.

- `ghl_calls/services.py`
  - Allows PEM public keys in `.env` to be stored with escaped `\n` line breaks.

Local environment change:

- `.env`
  - Added missing GHL and LearnDash settings.
  - Secret values are intentionally not repeated in this summary.

## Verification

Local verification was run using the project virtualenv:

```text
.\venv\Scripts\python.exe manage.py check
```

Result:

- Django system check completed.
- Only existing warnings appeared for duplicate URL namespaces:
  - `checkin_pwa`
  - `evernote_pwa`
  - `id_scanner`

Route resolution was checked for:

```text
/oauth/start/
/oauth/callback/
/api/webhooks/ghl-calls/
/api/webhooks/ghl-calls/transcript/
/api/webhooks/learndash/
/admin/tools/integrations/oauth/start/
/admin/tools/ghl-calls/
/admin/tools/learndash-webhook/
```

GHL webhook public keys were also parsed successfully.

## Manual Production Steps

These must still be done on EC2/Lightsail or in the relevant external services.

1. Add the same required GHL/LearnDash env vars to the production server environment or production `.env`.

2. Confirm GHL OAuth redirect URI is exactly:

```text
https://prod.vectorops.xyz/oauth/callback/
```

3. Configure GHL call webhook URL:

```text
https://prod.vectorops.xyz/api/webhooks/ghl-calls/
```

4. Configure transcript workflow URL:

```text
https://prod.vectorops.xyz/api/webhooks/ghl-calls/transcript/
```

5. Configure WordPress/LearnDash webhook URL:

```text
https://prod.vectorops.xyz/api/webhooks/learndash/
```

6. WordPress/LearnDash must send this header:

```text
X-LD-Secret: <production LD_WEBHOOK_SECRET>
```

7. Deploy to `dev`, run migrations, and restart the production app service.

## Commit Guidance

Do commit:

```text
core/settings.py
core/urls.py
ghl_calls/services.py
INTEGRATION_FIX_SUMMARY.md
```

Do not commit:

```text
.env
```


# Environment Guide

The merged copy supports two env styles because it combines the main project and the subproject.

## Current reality

- The active local [`.env`](/c:/Users/cyafei/Desktop/Django%20Merge/dbfightfire/.env) is mostly `main project` style.
- The merged code also supports `DJANGO_*` deployment-style variables from the `subproject`.

## Recommended files

- [local.env.example](/c:/Users/cyafei/Desktop/Django%20Merge/dbfightfire/local.env.example)
  Use this as the starting point for local merged-copy development.

- [prod.env.example](/c:/Users/cyafei/Desktop/Django%20Merge/dbfightfire/prod.env.example)
  Use this as the starting point for `prod.vectorops.xyz`.

## Variable groups

### Core / deploy settings

These control Django itself and are mainly used for hosted deployment:

- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG`
- `DJANGO_ALLOWED_HOSTS`
- `DJANGO_CSRF_TRUSTED_ORIGINS`
- `DJANGO_SECURE_SSL_REDIRECT`
- `DJANGO_USE_WHITENOISE`
- `DJANGO_STATIC_ROOT`

### Database settings

The merged copy supports:

- legacy/local names: `DB_ENGINE`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`
- deploy names: `DJANGO_DB_ENGINE`, `DJANGO_DB_NAME`, `DJANGO_DB_USER`, `DJANGO_DB_PASSWORD`, `DJANGO_DB_HOST`, `DJANGO_DB_PORT`

Recommended usage:

- local merged copy: `DB_ENGINE=sqlite`
- hosted deployment: `DJANGO_DB_*`

### Main-project integration settings

These are the original main-project service connections:

- `EXTERNAL_API_TOKEN`
- `MQTT_*`
- `EXCHANGE_*`
- `PRIVSER_*`
- `PAYCHEX_*`
- `FLEXTIME_*`
- `URL_SENT_CHANGED_PARAMETERS`
- `REDIS_URL`

### Subproject integration settings

These came from the subproject apps:

- `GHL_*`
- `LD_WEBHOOK_SECRET`
- `LEARNDASH_*`
- `TESSERACT_CMD`

## Safety recommendation

Unless you are intentionally testing a live integration:

- keep integration secrets blank in local work
- keep integration secrets blank in first deployment
- only enable one integration at a time when validating behavior

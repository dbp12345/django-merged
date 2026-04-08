# Prod VectorOps Deployment Checklist

This checklist is for deploying the merged copy to `https://prod.vectorops.xyz` while:

- keeping subproject data untouched
- keeping migrated apps under `Chloe's Apps`
- not migrating main-project data yet

## 1. Pick the deployment database mode

Recommended for current staging:

- `postgres`
- fresh staging database
- no main-project data import yet

That keeps the deployment isolated from main-project data migration and matches the current plan.

## 2. Set GitHub repository secrets

The workflow at [.github/workflows/deploy-prod.yml](/c:/Users/cyafei/Desktop/Django%20Merge/dbfightfire/.github/workflows/deploy-prod.yml) expects these secrets:

- `LIGHTSAIL_HOST`
- `LIGHTSAIL_USER`
- `LIGHTSAIL_PROJECT_PATH`
- `LIGHTSAIL_SSH_KEY`
- `LIGHTSAIL_KNOWN_HOSTS`
- `LIGHTSAIL_VENV_PATH`
- `LIGHTSAIL_PYTHON_BIN`
- `LIGHTSAIL_PIP_BIN`
- `LIGHTSAIL_RESTART_CMD`

Typical examples:

- `LIGHTSAIL_HOST=prod.vectorops.xyz`
- `LIGHTSAIL_USER=<your ssh user>`
- `LIGHTSAIL_PROJECT_PATH=/var/www/prod.vectorops.xyz/app`
- `LIGHTSAIL_VENV_PATH=/var/www/prod.vectorops.xyz/venv`
- `LIGHTSAIL_PYTHON_BIN=/var/www/prod.vectorops.xyz/venv/bin/python`
- `LIGHTSAIL_PIP_BIN=/var/www/prod.vectorops.xyz/venv/bin/pip`
- `LIGHTSAIL_RESTART_CMD=sudo systemctl restart gunicorn`

Use the actual service restart command from that server.

## 2.5 Likely secret values to confirm

I checked the subproject repo for committed deployment clues.

What I could confirm:

- the deployment host is `prod.vectorops.xyz`
- the repo uses a Lightsail SSH deploy flow
- the repo does not contain the real `LIGHTSAIL_PROJECT_PATH`
- the repo does not contain the real `LIGHTSAIL_VENV_PATH`
- the repo does not contain the real `LIGHTSAIL_RESTART_CMD`

So these are the most likely starting values, but they must be confirmed on the server:

- `LIGHTSAIL_HOST=prod.vectorops.xyz`
- `LIGHTSAIL_USER=<your ssh username>`
- `LIGHTSAIL_PROJECT_PATH=/var/www/prod.vectorops.xyz/app`
- `LIGHTSAIL_VENV_PATH=/var/www/prod.vectorops.xyz/venv`
- `LIGHTSAIL_PYTHON_BIN=/var/www/prod.vectorops.xyz/venv/bin/python`
- `LIGHTSAIL_PIP_BIN=/var/www/prod.vectorops.xyz/venv/bin/pip`

Common restart command patterns:

- `sudo systemctl restart gunicorn`
- `sudo systemctl restart gunicorn-prod-vectorops`
- `sudo supervisorctl restart prod-vectorops`

If you need to confirm them on the server, the most useful checks are:

```bash
pwd
whoami
ls /var/www
systemctl list-units --type=service | grep -i gunicorn
supervisorctl status
find /var/www -maxdepth 3 -name activate
```

From those results you can set the final GitHub secrets exactly.

## 3. Create the deployment server env file

Use [prod.env.example](/c:/Users/cyafei/Desktop/Django%20Merge/dbfightfire/prod.env.example) as the template.

Recommended starting values:

```env
DJANGO_SECRET_KEY=replace-me
DJANGO_DEBUG=0
DJANGO_ALLOWED_HOSTS=prod.vectorops.xyz
DJANGO_CSRF_TRUSTED_ORIGINS=https://prod.vectorops.xyz
DJANGO_SECURE_SSL_REDIRECT=1
DJANGO_USE_WHITENOISE=1

DJANGO_DB_ENGINE=postgres
DJANGO_DB_NAME=vectorops_staging
DJANGO_DB_USER=postgres
DJANGO_DB_PASSWORD=replace-me
DJANGO_DB_HOST=127.0.0.1
DJANGO_DB_PORT=5432

DJANGO_STATIC_ROOT=/var/www/prod.vectorops.xyz/static
```

Keep these blank unless you intentionally want live integrations in staging:

- `PRIVSER_API_KEY`
- `PRIVSER_API2_KEY`
- `EXCHANGE_USERNAME`
- `EXCHANGE_PASSWORD`
- `PAYCHEX_CLIENT_ID`
- `PAYCHEX_CLIENT_SECRET`
- `FLEXTIME_SHARED_KEY`
- `FLEXTIME_WSPASS`
- `GHL_CLIENT_ID`
- `GHL_CLIENT_SECRET`
- `GHL_WEBHOOK_PUBLIC_KEY`
- `GHL_WEBHOOK_LEGACY_PUBLIC_KEY`
- `LD_WEBHOOK_SECRET`
- `LEARNDASH_BASE_URL`
- `LEARNDASH_USERNAME`
- `LEARNDASH_APP_PASSWORD`

## 4. Prepare the staging database

If using PostgreSQL:

1. Create the database.
2. Create the database user.
3. Grant access to the database.
4. Put those values into the staging env file.

No main-project data import is needed for this phase.

## 5. Prepare the project path on the server

The deploy script expects the repo to exist already on the server.

Make sure:

- the project is cloned on the server
- the target branch exists
- the virtualenv exists
- the env file is in place
- the restart command is known

## 6. Trigger the deployment

Either:

1. push to the `dev` branch, or
2. run the GitHub Actions workflow manually

The workflow will:

1. upload [scripts/deploy_lightsail.sh](/c:/Users/cyafei/Desktop/Django%20Merge/dbfightfire/scripts/deploy_lightsail.sh)
2. pull the selected branch
3. install requirements
4. run migrations
5. run Django checks
6. collect static files
7. restart the app service

## 7. First deployment smoke test

After deployment, verify:

- `https://prod.vectorops.xyz/admin/`
- admin login works
- `Chloe's Apps` appears
- grouped sections appear under `Chloe's Apps`
- migrated apps open without server errors

Recommended pages to test:

- `/admin/`
- `/admin/tools/checkin-pwa/`
- `/admin/tools/evernote-pwa/`
- `/admin/tools/pic-pwa/`
- `/admin/tools/id-scanner/`
- `/admin/tools/ghl-calls/bulk-edit/`

## 8. Keep this phase safe

For this deployment phase:

- do not import main-project data yet
- do not point this deployment to main-project production DB
- do not enable live sync credentials unless intentionally testing them
- keep subproject apps inside `Chloe's Apps`

## 9. Current goal

The current goal is:

- main-project UI on `prod.vectorops.xyz`
- subproject apps preserved under `Chloe's Apps`
- no data migration from main project yet

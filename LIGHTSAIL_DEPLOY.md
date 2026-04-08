# Lightsail Staging Deploy Notes

This merged copy can be deployed to `https://prod.vectorops.xyz`.

## Goal

- Keep the subproject data untouched
- Keep the migrated subproject apps grouped under `Chloe's Apps`
- Bring the main-project UI into the staged merged copy before any main-project data migration

## Useful environment variables

The merged copy now understands both its local env names and the subproject-style Lightsail names.

- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG`
- `DJANGO_ALLOWED_HOSTS`
- `DJANGO_CSRF_TRUSTED_ORIGINS`
- `DJANGO_SECURE_SSL_REDIRECT`
- `DJANGO_DB_ENGINE`
- `DJANGO_DB_NAME`
- `DJANGO_DB_USER`
- `DJANGO_DB_PASSWORD`
- `DJANGO_DB_HOST`
- `DJANGO_DB_PORT`
- `DJANGO_STATIC_ROOT`

## Supported database engines

- `sqlite`
- `mysql`
- `postgres` / `postgresql`

This only prepares the merged copy to run against those engines. It does not migrate data by itself.

## Deploy script

Use [scripts/deploy_lightsail.sh](/c:/Users/cyafei/Desktop/Django%20Merge/dbfightfire/scripts/deploy_lightsail.sh) on the staging server or through CI.

The script:

1. Activates the virtualenv when configured
2. Fetches and pulls the target branch
3. Installs Python dependencies
4. Runs `manage.py migrate`
5. Runs `manage.py check`
6. Runs `manage.py collectstatic --noinput`
7. Restarts the app service when `RESTART_CMD` is provided

## GitHub Actions workflow

The merged copy now includes a deployment workflow at [.github/workflows/deploy-prod.yml](/c:/Users/cyafei/Desktop/Django%20Merge/dbfightfire/.github/workflows/deploy-prod.yml).

It expects the standard Lightsail secrets:

- `LIGHTSAIL_HOST`
- `LIGHTSAIL_USER`
- `LIGHTSAIL_PROJECT_PATH`
- `LIGHTSAIL_SSH_KEY`
- `LIGHTSAIL_KNOWN_HOSTS`
- `LIGHTSAIL_VENV_PATH`
- `LIGHTSAIL_PYTHON_BIN`
- `LIGHTSAIL_PIP_BIN`
- `LIGHTSAIL_RESTART_CMD`

## Example deploy env

Use [prod.env.example](/c:/Users/cyafei/Desktop/Django%20Merge/dbfightfire/prod.env.example) as the starting point for `prod.vectorops.xyz`.

For local merged-copy development, use [local.env.example](/c:/Users/cyafei/Desktop/Django%20Merge/dbfightfire/local.env.example).

## Current deployment intent

- Deploy merged UI to `prod.vectorops.xyz`
- Do not migrate main-project data yet
- Keep subproject apps accessible from `Chloe's Apps`

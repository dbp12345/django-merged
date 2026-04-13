# PostgreSQL Data Merge Workflow

This workflow is for loading both datasets into one PostgreSQL database for `https://prod.vectorops.xyz` while keeping main-project and subproject data separate.

## What stays separate

- Main-project data stays in the main tables like `company_*`, `dispatch_*`, `exchange_*`, `privser_*`, and related apps.
- Subproject data stays in the copied subproject tables like `companies_*`, `contacts_*`, `jobs_*`, `invoices_*`, `ghl_calls_*`, `learndash_*`, and related apps.
- No new relations are created between the main-project tables and the copied subproject tables.

## Important shared-table exception

Some Django system tables are shared by the whole merged project.

- `auth_user`
- `auth_group`
- `django_content_type`
- `auth_permission`

Because those are shared, the merge command only imports `auth_user` from the main project.

That means:

- main-project user foreign keys can still resolve
- subproject app data is kept separate
- subproject auth users are intentionally skipped

This is the safest match for the current merged architecture.

## Another important exception

The merged repo uses the main-project `automations` schema.

The original subproject also had an `automations` app, but it used different tables and models.

So for this phase:

- main-project `automations_*` data can be imported
- subproject `automations_*` data is intentionally not imported by the new command

If that data becomes important later, it should be copied under a new app label first so it does not collide with the main-project schema.

## Source databases confirmed in this workspace

Main project source:

- engine: MySQL
- host: `127.0.0.1`
- port: `3307`
- database: `dbfightfire`
- source location: local portable MySQL in `portable-mysql/`

Subproject source:

- engine: SQLite
- file: `C:/Users/cyafei/programmingbiz/db.sqlite3`

Target:

- engine: PostgreSQL
- target example: AWS RDS for `prod.vectorops.xyz`

## New merge command

The repo now includes:

- [merge_separated_project_data.py](/c:/Users/cyafei/Desktop/Django%20Merge/dbfightfire/core/management/commands/merge_separated_project_data.py)

It can:

- inspect both sources
- dump JSON fixtures from both sources
- optionally load them into the current target database
- keep main and subproject app data in separate tables

## Recommended order

1. Point Django `default` to the new PostgreSQL database.
2. Run `python manage.py migrate` against PostgreSQL.
3. Inspect both sources with the merge command.
4. Dump and load the data into PostgreSQL.
5. Run smoke tests on `prod.vectorops.xyz`.

## PowerShell example

This example assumes:

- the target PostgreSQL database is your RDS database
- the main source is the local portable MySQL
- the subproject source is the old SQLite file

```powershell
$env:DJANGO_DB_ENGINE='postgres'
$env:DJANGO_DB_NAME='chloe_db'
$env:DJANGO_DB_USER='postgres'
$env:DJANGO_DB_PASSWORD='replace-with-rds-password'
$env:DJANGO_DB_HOST='replace-with-rds-endpoint'
$env:DJANGO_DB_PORT='5432'

& '.\venv\Scripts\python.exe' manage.py migrate

& '.\venv\Scripts\python.exe' manage.py merge_separated_project_data

& '.\venv\Scripts\python.exe' manage.py merge_separated_project_data --dump --load
```

## Optional source overrides

If your source locations differ, set these env vars before running the command:

Main source:

- `MERGE_MAIN_DB_ENGINE`
- `MERGE_MAIN_DB_NAME`
- `MERGE_MAIN_DB_USER`
- `MERGE_MAIN_DB_PASSWORD`
- `MERGE_MAIN_DB_HOST`
- `MERGE_MAIN_DB_PORT`

Sub source:

- `MERGE_SUB_DB_ENGINE`
- `MERGE_SUB_DB_NAME`
- `MERGE_SUB_DB_USER`
- `MERGE_SUB_DB_PASSWORD`
- `MERGE_SUB_DB_HOST`
- `MERGE_SUB_DB_PORT`

## Safer first run

For the first real run on PostgreSQL, use a fresh empty target database after migrations.

That avoids:

- primary key conflicts
- duplicate imports
- mixed auth rows from previous experiments

## What I would use for your current rollout

For your current goal, the cleanest path is:

1. Keep `prod.vectorops.xyz` on the merged Django project.
2. Point it at the new RDS PostgreSQL database.
3. Run migrations on PostgreSQL.
4. Import main-project data from the portable MySQL.
5. Import copied subproject data from the old SQLite file.
6. Leave the two data families in their own tables, with no new cross-project links.

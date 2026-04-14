# Project Context: Django Merge Migration

## Goal
Merge sub Django project (programmingbiz) into main project (dbfightfire)
using SAFE staged migration approach.

## Migration Strategy (from boss)
1. UI Migration
   - Add sub apps under separate hidden section
   - No data interaction with main models
   - Keep tables separate

2. Data Migration (later)
   - Option A: FK relationships (TabularInline)
   - Option B: Replace duplicate models
   - Option C: Expand access to main datasets

3. UI Refresh (final)
   - Move apps into final structure
   - Clean navigation

## Current Setup
- Main project copied into:
  C:\Users\cyafei\Desktop\Django Merge\dbfightfire
- Sub project:
  C:\Users\cyafei\programmingbiz

## Environment
- Python 3.12
- SQLite (temporary merged-copy staging DB for safe UI testing)
- No production DB connection
- No background sync tasks
- Local merged-copy migrations applied for copied sub apps
- Local merged-copy cache now fails safe when Redis is unavailable
- Deployment target identified: `https://prod.vectorops.xyz`

## Current Progress
- Project runs successfully
- Git initialized
- First app copied: checkin_pwa
- Second app copied: evernote_pwa
- Dependency pair copied: companies + contacts
- Fourth app copied: pic_pwa
- Fifth app copied: id_scanner
- Sixth migration pair copied: jobs + invoices
- Final integration wave copied: integrations + ghl_calls + learndash + learndash_webhook
- Hidden app section added for staged sub-project migration
- Workspace cleanup done: accidental nested `contacts/contacts` copy removed
- Hidden migrated app pages smoke-tested successfully in local merged copy
- Safety lockdown applied in merged copy: live sync credentials blanked, task toggles seeded disabled
- GHL/LearnDash remain unconfigured in merged copy
- `Chloe's Apps` dashboard section regrouped by migrated app instead of one flat link list
- Portable MySQL prepared for later main-project dump import, but data migration is currently paused
- Merged copy settings now support subproject-style Lightsail env vars and optional staging DB engine selection
- Lightsail deploy script/docs added for `prod.vectorops.xyz` rollout
- GitHub Actions deployment workflow and example deploy env template added for `prod.vectorops.xyz`
- Concrete deployment checklist added for GitHub secrets, server env, DB setup, and smoke testing
- Local and deploy env example files added, with a guide splitting main-project, subproject, and deployment settings

## Rules
- Do NOT modify main models yet
- Do NOT switch merged copy to MySQL yet while data migration is paused
- Do NOT merge data yet
- Only UI-level integration first

## Next Task
Continue staged migration of sub-project apps one at a time.
Current order:
1. `checkin_pwa` integrated in migration-safe mode
2. `evernote_pwa` integrated under hidden admin tools
3. `companies` + `contacts` integrated as separate sub-project apps/tables
4. `pic_pwa` integrated under hidden admin tools using copied `contacts`
5. `id_scanner` integrated under hidden admin tools with copied OCR pipeline
6. `jobs` + `invoices` integrated as separate sub-project apps/tables
7. `integrations`, `ghl_calls`, `learndash`, and `learndash_webhook` integrated under hidden admin tools/routes
8. Local merged-copy DB migrated and hidden migrated pages verified
9. Safety pass completed: task toggles resolve `False`, automations inactive, no GHL auth configured
10. Main-project dump import path is prepared via portable MySQL, but paused for now
11. Current UI task is refining the grouped `Chloe's Apps` dashboard experience in the merged copy
12. Next deployment target is `prod.vectorops.xyz` using the subproject deployment flow, with subproject data left untouched
13. Before deployment, set Lightsail secrets/env vars and choose the deployment DB engine for `prod.vectorops.xyz`
14. Preferred current deployment path: fresh PostgreSQL on `prod.vectorops.xyz` with no main-project data import yet
15. Env management is now documented with separate local and deploy examples
#goodluck
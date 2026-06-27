# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

**runningroutes** is a multi-tenant Flask web app for managing and displaying running routes with Google Maps integration (elevation, geocoding). Supports GPX/KML file uploads and icon maps. "Multi-tenant" means multiple named *interests* (user communities) share one deployment.

## Commands

All development runs inside Docker:

```bash
# Start all services (COMPOSE_FILE is set in .env)
docker compose up -d

# Database migrations
docker compose exec app flask db migrate    # generate migration from model changes
docker compose exec app flask db upgrade   # apply pending migrations

# Logs
docker compose logs -f app
```

Deploy to remote servers via Fabric:
```bash
fab -H <host> deploy <qualifier>                        # e.g. prod, sandbox
fab -H <host> deploy sandbox --branchname=develop
```

No automated test suite is configured. `/admin/test-exception` (see `admin/sysinfo.py`) tests error-handling in running deployments.

## Architecture

### Application Factory

`app/src/app.py` and `app/src/app_server.py` are two entry points — `app.py` for Flask CLI (with migrations), `app_server.py` for production WSGI. Both call `create_app(config_obj, configfiles)`.

Config loads from:
1. `config/users.cfg` — users database connection
2. `config/runningroutes.cfg` — app settings (Google Maps key, email, DB)
3. Environment variables prefixed `FLASK_`

Two database *binds*: default (routes/icons/locations) and `users` (Flask-Security-Too auth tables, shared with other apps via loutilities).

### Blueprint Layout

```
app/src/runningroutes/views/
├── admin/        # url_prefix='/admin', requires auth + role check
│   ├── routes.py     # Route CRUD with elevation fetch
│   ├── icons.py      # Icon and icon-location management
│   ├── files.py      # File upload
│   ├── userrole.py   # User/role admin (delegates to loutilities)
│   └── sysinfo.py    # Debug endpoints
└── frontend/     # url_prefix=''
    ├── frontend.py   # Public route listing/search
    └── icons.py      # Public icon map display
```

`__init__.py` in each blueprint registers a `pull_interest()` preprocessor that reads the `<interest>` URL segment and stores the resolved `LocalInterest` in `g.interest`. Every admin view URL starts with `/<interest>/`.

### Models (`app/src/runningroutes/models.py`)

Core: `Route`, `Files`, `Icon`, `Location`, `IconSubtype`, `IconLocation`, `IconMap`  
Auth mirrors: `LocalUser`, `LocalInterest` (synced from loutilities shared DB via `update_local_tables()`)

All main tables include `version_id` for SQLAlchemy optimistic locking. Routes can reference two `Files` records (GPX and processed path).

### CRUD Pattern (loutilities)

Admin views subclass `DbCrudApiRolePermissions` from loutilities. Key methods to override:

- `permission()` — authorization check; return `False` to deny
- `beforequery()` — apply interest-scoped filter: `self.queryparams['interest_id'] = self.linterest.id`
- `createrow()` / `updaterow()` / `deleterow()` — custom business logic

### Roles

Defined as constants in `models.py`:
- `ROLE_SUPER_ADMIN` — bypass interest-scoped access checks
- `ROLE_ROUTES_ADMIN` — edit routes for assigned interests
- `ROLE_ICON_ADMIN` — edit icons/locations for assigned interests

### Geolocation (`app/src/runningroutes/geo.py`)

`GmapsLoc` wraps the Google Maps API. Elevation gain is calculated by sampling path points (≤512 samples, ~60 ft apart). Controlled by `GMAPS_ELEV_API_KEY` in config and `GELEV_MAX_MILES` constant.

### Files (`app/src/runningroutes/files.py`)

Uploaded files stored as "fid" files under `/files/files` (Docker volume). The `Files` model tracks `fileid`, `filename`, `mimetype`, and `route_id` (nullable until assigned).

### Known Quirks

- **`nav.py` monkey-patch**: Python 3.10+ removed `collections.MutableMapping`; the workaround in `nav.py` must stay.
- **`LocalInterest` sync**: `LocalInterest`/`LocalUser` are copies of loutilities central tables, synced via `update_local_tables()` on startup. Allows interest-scoped queries without a cross-database join.
- **Email via msmtp**: Docker container uses `msmtp` (not sendmail). Config at `config/msmtprc`.
- **d3-tip patched for D3 v7**: The live file is `JS_COMMON_HOST/d3-tip-1.1/d3-tip.js` (mounted into the container from `C:\Users\lking\Documents\Lou's Software\operational\js-common`). It is the VACLab fork (v1.1, the latest), locally patched to guard `d3.event.target` which was removed in D3 v7. Do not replace with the upstream file — there is no maintained D3 v7-compatible version of d3-tip.

## Configuration Files

| File | Purpose |
|------|---------|
| `.env` | Docker Compose variable overrides (ports, Python version, paths) |
| `config/runningroutes.cfg` | App settings: DB, Google Maps API key, SMTP |
| `config/users.cfg` | Users DB connection (shared with loutilities apps) |
| `app/cronjobs` | Cron schedule inside container (DB backups) |

In production, DB passwords come from Docker secrets at `/run/secrets/appdb-password` and `/run/secrets/users-password`.

## External Dependencies

- **loutilities** (local package, also in this workspace at `c:\Users\lking\Documents\Lou's Software\projects\loutilities\loutilities`) — shared user/role models, CRUD framework, geolocation utilities
- **Google Maps API** — elevation and geocoding; requires `GMAPS_ELEV_API_KEY`
- **MySQL 8.x** — version pinned in `.env`

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

```bash
pytest
```
Run from the repo root; `pytest.ini` puts `app/src` on `sys.path` so `runningroutes` imports normally without Docker. `test/conftest.py` sets `APP_NAME`/`APP_VER` (normally supplied by Docker Compose's `.env`) since `runningroutes/__init__.py` reads `os.environ['APP_NAME']` at import time. Pattern follows `members`'/`contracts`' `test/` setup (see those repos' `CLAUDE.md`).

`/admin/test-exception` (see `admin/sysinfo.py`) tests error-handling in running deployments.

### Tests

**`create_app(Testing)` fails before any table exists**, same root cause as `members`/`contracts`: it unconditionally queries the `Application` table (for `g.loutility`) while creating the app (`runningroutes/__init__.py`). `test/conftest.py`'s `app` fixture works around this with a bare bootstrap Flask app pointed at the same (file-based, not `:memory:`) database to create tables and seed the `Application` row *before* calling `create_app()`.

**Several modules read `app.config[...]` (and build a real `googlemaps.Client`/`GmapsLoc`) at *module import time*** via `from . import app` / `from ... import app` (the module-level global `create_app()` sets): `locations.py`, `views/admin/routes.py`, `views/admin/icons.py`, `views/frontend/frontend.py`, `views/frontend/icons.py`, and `nav.py` (`thisnav.init_app(current_app)`, needs an active app context). These modules only import successfully once `create_app()` has already run once in the process (they're imported as a side effect of blueprint registration). Because Python only executes a module body on its *first* import, a *second* `create_app()` call would build a second Flask app, but those already-imported modules would stay bound to the *first* call's app/gmaps client forever — so `test/conftest.py`'s `app` fixture is **session-scoped**, calling `create_app()` exactly once per test session, and per-test isolation comes from dropping/recreating tables (`dbapp` fixture) rather than rebuilding the app. Tests that need one of these modules import it lazily via a small fixture that depends on `app` (e.g. `test_locations.py`'s `locations_module` fixture, `test_nav.py`'s `nav_module` fixture) — a top-level `from runningroutes.locations import ...` at the top of a test file would run at collection time, before any fixture (including `app`) has executed, and fail.

**`db.session` is a process-global, hardwired to whichever app last called `create_app()`.** `create_app()` replaces Flask-SQLAlchemy's normal per-app `db.session` proxy with a single `scoped_session(sessionmaker(binds=db.get_binds()))` bound to whatever `db.get_binds()` resolved to *at that moment* — not re-resolved per `current_app` afterward. Interleaving the real `app`/`dbapp` fixtures with the lightweight `bareapp`/`bare_dbapp` fixtures (different tests, same pytest session) would otherwise leave one of them silently querying through a session bound to the *other* fixture's engines (tables created in one sqlite file, queries executed against a session pointed at a different one) — this surfaced as `bare_dbapp`-based tests failing only when run after `dbapp`-based tests, never in isolation. `test/conftest.py`'s `_rebind_session()` helper re-points `db.session` at the right app's engines every time `dbapp` or `bareapp` is set up, regardless of what ran before it in the session.

`bareapp`/`bare_dbapp` use file-based (not `:memory:`) sqlite throughout, sidestepping a `:memory:`-plus-cross-bind-query flush/commit visibility gotcha documented in the `members` repo's `CLAUDE.md` for `update_local_tables()` testing there, rather than adding a separate fixture just for that one function.

**Requirements.txt regression found while adding this suite**: the prior "security fixes" commit (`e1400ac`) replaced `passlib==1.7.4` with `libpass==1.9.3` in `app/requirements.txt`, but `libpass` 1.9.3 only provides a partial `passlib`-namespace shim (`_data`, `_logging.py`, `_protocols.py` — no `context.py`/`CryptContext`), so `flask_security.core`'s `from passlib.context import CryptContext` broke the app import entirely. The `members` repo's precedent is to install `libpass` *alongside* `passlib`, not instead of it (nothing there actually imports `libpass` directly — `pip show libpass` there shows `Required-by:` empty). Restored `passlib==1.7.4` here to match.

#### Coverage

Beyond `helpers.py`'s `Interest`/`LocalInterest` lookups, the suite covers: `geo.py`'s `isLatlng()` and `GmapsLoc` (mocked `googlemaps.Client.geocode`, no real network calls); `models.py`'s `priorityUpdater`, `getmodelitems`/`ModelItem`, and `update_local_tables()`; `files.py`'s `create_fidfile()`/`get_fidfile()` (real temp-directory filesystem I/O); `locations.py`'s `location_validate()`/`get_location()`; `dbinit.py`'s `init_db()`; `nav.py`'s `nav_menu()` role-based menu construction (via `test/fakecurrentuser.py`'s `FakeCurrentUser`, monkeypatching each module's own imported `current_user` name); `views/frontend/frontend.py`'s `check_permission()` and the non-`render_template()` halves of `UserRoutes`/`UserRoute`/`UserTurns` (`permission()`, `beforequery()`, `_retrieverows()`); `views/frontend/icons.py`'s `IconLocations._retrieverows()` (real SVG parsing via a small fixture-created SVG file, mocked `gmaps.get_location()`); and, on the `DbCrudApiRolePermissions`/`loutilities.tables`-based admin views, the override methods that don't themselves call `render_template()` — `views/admin/routes.py`'s `RunningRoutesTable.permission()`/`beforequery()`/`snaploc()`/`set_files_route()`, and `views/admin/icons.py`'s `IconsCrud.permission()`/`beforequery()`/`set_files_icon()` and `IconLocationCrud.editor_method_posthook()` — called directly on the module-level singleton instances (`rrtable`, `icon`, `iconmap`) rather than through the full DataTables server-side request/response protocol.

#### Excluded from this pass — needs more setup

- **`scripts/icons_init.py`/`scripts/routes_init.py`** — one-off, operator-run data-seeding scripts, not safely importable: both call `create_app(Development(configpath), configpath)` against real config files at *module import time* (not inside a function), so merely importing either for a test would attempt to read real config and connect to whatever `Development` config resolves to, plus real `openpyxl` workbook reads and real Google Maps calls. Same category as `members`' `*_init.py` scripts.
- **The `render_template()`-calling halves of the admin/frontend views** (`RunningRoutesTable.render_template()`, `IconsCrud.render_template()`, `UserRoutes._renderpage()`/`UserRoute._renderpage()`/`UserTurns._renderpage()`, `IconLocations._renderpage()`, all of `views/admin/sysinfo.py`) and **the DataTables server-side request/response protocol itself** (`get()`/`post()`/`createrow()`/`updaterow()`/`deleterow()` on the `DbCrudApiRolePermissions` views, beyond the override methods listed under Coverage above) — exercising these needs a live route through the full framework, not just calling an override method directly. Same exclusion `members` documented for its `DbCrudApiInterestsRolePermissions`-based views.
- **`views/admin/login.py`** (Flask-Login signal handlers) and **`views/admin/userrole.py`** (thin wrappers delegating to `loutilities.user.views.userrole`) — mostly logging/delegation with no standalone algorithm worth isolating.
- **`RunningRoutesFiles.upload()`/`IconsFiles.upload()`** (`views/admin/routes.py`/`views/admin/icons.py`) — the real GPX-processing/elevation-gain-calculation algorithm (`loutilities.geo.elevation_gain`, `numpy` smoothing) is worth testing but needs a real GPX fixture file and mocking `googlemaps.elevation.elevation()`; not attempted in this pass.

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
- **`rjsmin` filter**: `assets.py` specifies `filters='rjsmin'` for JS bundles, which requires the `rjsmin` Python package (distinct from `jsmin`). If `rjsmin` is not installed, `ASSETS_DEBUG=False` cannot rebuild bundles and `ASSETS_DEBUG=True` skips the filter entirely (files are concatenated raw, exposing any missing-semicolon issues). The pre-built `gen/admin.js` in the repo was minified with `rjsmin`; keep `rjsmin` in `requirements.txt`.
- **Rebuilding JS/CSS bundles in dev**: with `ASSETS_DEBUG=False` (the default here, per `config/runningroutes.cfg`), editing a source file under `static/frontend/` or `static/*.js` does not reliably trigger an on-request rebuild of its `gen/*.js` output — a bundle can sit stale for years (seen: `gen/frontendroute.js` untouched since 2020 despite its source changing) until something forces it. Run `docker compose exec app flask assets build` to force-rebuild every bundle in `asset_bundles` after editing frontend JS/CSS, then hard-refresh the browser.
- **Each bundle needs a unique `output=` path**: in `assets.py`, every `Bundle(..., output='gen/....js')` must have its own filename. Two bundles sharing one `output` path silently clobber each other on rebuild — whichever bundle gets built (rebuilt on request) last overwrites the file for both, so one page can end up served the other page's JS. (`frontend_locations` used to share `frontend_routes`'s `gen/frontendroutes.js`; fixed to `gen/frontendlocations.js`.)
- **`mutex-promise.js` bundle ordering**: `datatables.js` (from loutilities) uses `MutexPromise` at module scope. `mutex-promise.js` must appear in both `frontend_common_js` and `admin_js` bundles in `assets.py` *before* `datatables.js`. If it's missing, the bundle throws `ReferenceError: MutexPromise is not defined`, halting bundle execution and causing cascading errors (including `editRefresh` button type not being registered). When updating loutilities, check `datatables.js` for new top-level dependencies.
- **Google Maps JS API loads async, gated by `onGmapsReady`**: The Maps script is *not* in an `assets.py` bundle (a bundled `<script>` can't carry the `async` attribute or `loading=async` param cleanly). Instead each of the three map-using templates (`frontend_routes.jinja2`, `frontend_route.jinja2`, `frontend_locations.jinja2`) has, in its `prescripts` block, an inline `<script>` stub defining `window.gmapsCallback`/`window.onGmapsReady(fn)` *followed by* `<script async src="...&loading=async&callback=gmapsCallback">`. The corresponding JS file (`runningroutes.js`, `runningroute-route.js`, `iconmap.js`) registers its map-dependent init via `window.onGmapsReady(fn)` and gates it behind two flags (`_domReady`, `_gmapsReady`) so init runs once, whichever finishes last. **Gotcha 1 (why the stub must be inline, not in the JS bundle):** the shared `frontendcommon.js` bundle is ~2MB and can take longer to download/parse/execute than the tiny async Maps bootstrap script takes to fetch its library and invoke the callback — defining `window.gmapsCallback` directly inside the page's own bundle (which loads after `frontendcommon.js`) lost that race in practice, throwing `InvalidValueError: gmapsCallback is not a function`. The inline stub runs before the async script tag is even requested, so `onGmapsReady` is always ready to queue the page's callback regardless of bundle load time. **Gotcha 2:** `runningroutes.js`/`runningroute-route.js` build `SVGOverlay` by extending `google.maps.OverlayView`; do this with `Object.setPrototypeOf(SVGOverlay.prototype, google.maps.OverlayView.prototype)` inside the gated callback, never `SVGOverlay.prototype = new google.maps.OverlayView()` — the latter, run after the file's own top-level `SVGOverlay.prototype.onIdle = ...`-style assignments (which run unconditionally at parse time), *replaces* the prototype object and silently wipes those methods out.

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

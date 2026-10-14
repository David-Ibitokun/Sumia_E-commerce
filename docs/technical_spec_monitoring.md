# Technical Specification: Admin Audit History & Database Health Check

## 1. Overview

This specification defines two system-monitoring capabilities for the **Sumia**
e-commerce platform (Django 4.2, PostgreSQL/SQLite):

1. **Admin Audit History** — a durable, queryable record of who changed what and
   when, restricted to admin-staff actions and the Django admin interface.
2. **Database Health Check** — a read-only diagnostic that reports live
   connection-pool metrics and flags slow-running queries, exposed through a
   management command and an admin dashboard view.

Both features follow the project's established conventions: thin views, a
service layer for business logic, model-level domain logic, and signal-based
side effects. No third-party audit-log or APM packages are introduced; the
implementation relies only on `Django.contrib`, the standard library, and
`psutil` (new, dev-only).

---

## 2. Conventions Recap

| Concern | Project Convention | Applied here |
|---|---|---|
| App layout | One app per bounded context | New `audit` app for audit history; `monitoring` app for DB health |
| Business logic | Service layer under `app/services/` | `audit/services.py`, `monitoring/services.py` |
| Side effects | Django signals connected in `apps.py` | `audit/signals.py` + `monitoring/signals.py` |
| User model | `AUTH_USER_MODEL = 'authentications.UsersRegistration'` | Referenced via `get_user_model()` |
| Thread safety | Request-scoped context via `contextvars` | `monitoring` uses `contextvars` for per-request query timing |
| Admin UI | `django-jazzmin` registered in `admin` | Audit entries + health-check views in admin |
| Settings | Environment-driven, production-safe defaults | New settings under `AUDIT_*` and `MONITORING_*` prefixes |

---

## 3. Feature 1: Admin Audit History

### 3.1 Purpose

Capture a tamper-evident log of every data modification made through the Django
admin interface by authenticated staff users. Each entry records:

- **Identity** — the staff user who performed the action (and their IP).
- **Change details** — a JSON document describing per-field old/new values
  (for creates and updates) or the full row snapshot (for deletes).
- **Timestamp** — server-side UTC time, captured at the moment the DB write
  occurs.

### 3.2 Data Model

**File:** `audit/models.py`

```
AuditLog
├── id                       BigAutoField, PK
├── timestamp                DateTimeField, auto_now_add=True, indexed
├── user                     ForeignKey(get_user_model()), null=True on_delete=SET_NULL
├──       → related_name = 'audit_logs'
├── model_name               CharField(max_length=100), indexed
├── app_label              CharField(max_length=100)
├── object_id                CharField(max_length=255), indexed
├── object_repr              CharField(max_length=200)   # str(instance) snapshot
├── action                   CharField(max_length=10, choices=ACTION_CHOICES)
├──       values: 'create', 'update', 'delete'
├── changes                  JSONField(default=dict)      # field → {old, new}
├── request_path             CharField(max_length=255, blank=True)
├── ip_address               GenericIPAddressField(null=True, blank=True, unpack_ipv4=True)
├── user_agent               TextField(blank=True)
└── transaction_id           CharField(max_length=64, blank=True, db_index=True)
      → optional correlation ID from middleware
```

**Indexes:**

| Index | Columns | Purpose |
|---|---|---|
| `idx_auditlog_timestamp` | `timestamp DESC` | Recent-activity views |
| `idx_auditlog_model_object` | `app_label, model_name, object_id` | Audit trail for one record |
| `idx_auditlog_user_action` | `user_id, action, timestamp` | User activity report |
| `idx_auditlog_transaction` | `transaction_id` | Correlate all changes in one request |

### 3.3 Capturing the Request Context

Django model signals do not receive the `HttpRequest`. To bind each
`AuditLog` entry to the acting user and request metadata, a
**middleware** stores the request on a thread-local / contextvar that the
signal handler reads:

```
audit/middleware.py
  AuditContextMiddleware
    - process_request: store request in contextvar `current_request`
    - __call__: delegate to get_response, then set the request to None
```

```python
import contextvars

current_request = contextvars.ContextVar('audit_current_request', default=None)
```

> `contextvars.ContextVar` is used instead of `threading.local()` because the
> project may deploy under ASGI (see `sumia/asgi.py`); contextvars is
> concurrency-safe for both WSGI and ASGI.

### 3.4 Signal Handlers

**File:** `audit/signals.py`

Three handlers are connected to `post_save` and `post_delete` on every model
in `INSTALLED_APPS` **except** `audit.AuditLog` itself (to avoid infinite
recursion) and the `sessions` / `admin.LogEntry` models.

| Signal | Handler | Behaviour |
|---|---|---|
| `post_save` (created=True) | `log_create` | Record `changes` = `{field: {old: null, new: value}}` for every field |
| `post_save` (created=False) | `log_update` | Fetch old snapshot from DB (or compare via `pre_save` capture) → record only changed fields |
| `post_delete` | `log_delete` | Record `changes` = full instance snapshot (`{field: {old: value, new: null}}`) |

**Selective tracking** — settings control which apps are audited:

```python
# settings.py additions
AUDIT_TRACKED_APPS = os.environ.get(
    'AUDIT_TRACKED_APPS',
    'pages,shop,authentications'
).split(',')

AUDIT_LOG_RETENTION_DAYS = int(os.environ.get('AUDIT_LOG_RETENTION_DAYS', '90'))
```

Only models whose app label is in `AUDIT_TRACKED_APPS` receive signal
connections. The `audit` app itself is excluded.

### 3.5 Old-Value Capture Strategy

**Challenge:** `post_save` fires after the write; the DB no longer holds the
pre-save values. Two approaches:

- **Approach A (pre_save capture):** A `pre_save` handler stores the fetched
  old instance in a contextvar keyed by `(sender, pk)`. The `post_save`
  handler diffs old vs. new.
- **Approach B (query before write):** Not feasible — the write has already
  happened.

**Selected: Approach A.** The `pre_save` handler is connected for `update`
only (it is skipped for `create` since there is no prior row):

```python
@receiver(pre_save)
def capture_old_instance(sender, instance, **kwargs):
    if should_audit(sender) and instance.pk is not None:
        try:
            old = sender._default_manager.using(instance._state.db).get(pk=instance.pk)
        except sender.DoesNotExist:
            old = None
        _old_instances[instance] = old  # contextvar dict
```

The `post_save` handler then pops the entry, diffs fields, and writes the
`AuditLog`.

### 3.6 Change Diffing

```python
def _diff_fields(old_instance, new_instance):
    changes = {}
    for field in old_instance._meta.fields:
        name = field.name
        old_val = _serializable(getattr(old_instance, name))
        new_val = _serializable(getattr(new_instance, name))
        if old_val != new_val:
            changes[name] = {'old': old_val, 'new': new_val}
    return changes
```

**Serialization rules** (for JSON storage):

- FK → store the PK (or `null`).
- `ImageField` / `FileField` → store the URL string.
- `DecimalField` → cast to `str` to avoid JSON serialization issues.
- Callable / complex objects → `repr()`.

### 3.7 User Identification

```python
def _get_audit_user(request):
    user = getattr(request, 'user', None)
    if user and user.is_authenticated:
        return user
    return None
```

If no user is found (e.g., a data migration), `user` is `null` and
`request_path` is blank — the entry is still written for completeness but
flagged via a `is_system` boolean.

### 3.8 Bulk-Operation Handling

Django's `QuerySet.update()` and `QuerySet.delete()` bypass model `save()`/
`delete()` signals. To cover these paths, two additional hooks are added:

1. A `pre_delete` receiver on `QuerySet` via the model's manager is not
   practical.
2. Instead, admin actions that perform bulk updates/deletes are wrapped with a
   context manager that records a single `AuditLog` entry with
   `action='update'` or `action='delete'` and `object_id='*bulk*'` plus the
   count in `changes`.

For the MVP, bulk operations outside the admin UI are not captured (documented
as a known limitation — see §8).

### 3.9 Admin Integration

**File:** `audit/admin.py`

```
AuditLogAdmin(ModelAdmin)
  - list_display: timestamp, user, action, app_label, model_name, object_repr, short_changes
  - list_filter:  action, app_label, model_name, user, timestamp
  - search_fields: object_repr, model_name, user__username, user__email, ip_address
  - readonly_fields: all fields
  - date_hierarchy: timestamp
  - actions: none (read-only)
  - has_add_permission: False
  - has_change_permission: False
  - has_delete_permission: False
```

Jazzmin is configured to surface the audit log in the sidebar navigation
under a "System" menu group via `JAZZMIN_SETTINGS`.

### 3.10 Data Retention

A management command `purge_old_audit_logs` deletes entries older than
`AUDIT_LOG_RETENTION_DAYS` (default 90). It is intended to be run via cron or
a task scheduler:

```bash
python manage.py purge_old_audit_logs --dry-run
```

### 3.11 Performance Considerations

- **Signal overhead:** Each audited `save()`/`delete()` incurs one extra
  `AuditLog.objects.create()` write. For high-throughput models (e.g.,
  `CartItem`), the app label can be excluded from `AUDIT_TRACKED_APPS`.
- **Async-safe:** The contextvar is cleared in middleware after each request.
- **Transaction awareness:** If the audited write is rolled back, the
  `AuditLog` is also rolled back (same transaction), so no orphan entries are
  created.
- **Indexing:** The four indexes listed above cover all known query patterns.

### 3.12 Settings Summary

```python
# Audit
AUDIT_TRACKED_APPS = ['pages', 'shop', 'authentications']
AUDIT_LOG_RETENTION_DAYS = 90

# Middleware insertion (in MIDDLEWARE, after AuthenticationMiddleware)
AUDIT_MIDDLEWARE = 'audit.middleware.AuditContextMiddleware'
```

---

## 4. Feature 2: Database Health Check

### 4.1 Purpose

Provide real-time visibility into the health of the application's database
layer:

1. **Connection pool metrics** — how many connections are open, how many are
   in use versus idle, connection wait times, and pool pressure indicators.
2. **Slow-running query detection** — queries that exceed a configurable
   duration threshold, logged for investigation and correlation.

### 4.2 Connection Pool Model

The project currently relies on Django's built-in persistent-connection pool
(`conn_max_age=600` set via `dj_database_url.config` in `sumia/settings.py:140`).
Django itself does not expose pool metrics; however:

- **PostgreSQL:** The database exposes `pg_stat_activity` and
  `pg_stat_database`, which report active/idle/closed connection counts,
  transaction states, and wait events.
- **SQLite:** No true connection pool; each connection is independent. Health
  checks degrade to file-existence and basic connectivity tests.

### 4.3 Data Models

**File:** `monitoring/models.py`

```
SlowQueryLog
├── id                       BigAutoField, PK
├── sql                        TextField()
├── duration_ms               FloatField()
├── threshold_ms              FloatField()
├── stack_trace               TextField(blank=True)
├── request_path              CharField(max_length=255, blank=True)
├── user_id                   BigIntegerField(null=True, blank=True)
├── captured_at               DateTimeField(auto_now_add=True)
├── connection_alias          CharField(max_length=50, default='default')
└── hash                      CharField(max_length=64, db_index=True)
      → md5(sql) to group recurring slow queries

HealthCheckResult
├── id                       BigAutoField, PK
├── checked_at               DateTimeField(auto_now_add=True)
├── status                   CharField(max_length=20, choices=STATUS_CHOICES)
│       values: 'healthy', 'warning', 'critical'
├── database_engine          CharField(max_length=50)
├── connections_total        IntegerField()
├── connections_active       IntegerField()
├── connections_idle         IntegerField()
├── slow_query_count         IntegerField(default=0)
│       → count of slow queries logged in the last check window
├── details                  JSONField(default=dict)
│       → backend-specific diagnostic payload
└── error_message            TextField(blank=True)
      → non-empty when status != 'healthy' and a check raised an exception
```

**Indexes:**

| Index | Columns | Purpose |
|---|---|---|
| `idx_slowquery_hash` | `hash` | Group recurring slow queries |
| `idx_slowquery_captured` | `captured_at DESC` | Recent slow queries |
| `idx_healthcheck_checked` | `checked_at DESC` | Health history timeline |

### 4.4 Settings

```python
# settings.py additions
MONITORING_SLOW_QUERY_THRESHOLD_MS = float(
    os.environ.get('MONITORING_SLOW_QUERY_THRESHOLD_MS', '1000')
)
MONITORING_HEALTH_CHECK_INTERVAL_SECONDS = int(
    os.environ.get('MONITORING_HEALTH_CHECK_INTERVAL_SECONDS', '30')
)
MONITORING_RETAIN_SLOW_QUERY_DAYS = int(
    os.environ.get('MONITORING_RETAIN_SLOW_QUERY_DAYS', '30')
)
MONITORING_RETAIN_HEALTH_RESULTS_DAYS = int(
    os.environ.get('MONITORING_RETAIN_HEALTH_RESULTS_DAYS', '30')
)
MONITORING_CAPTURE_SLOW_QUERY_STACK = os.environ.get(
    'MONITORING_CAPTURE_SLOW_QUERY_STACK', 'False'
).lower() == 'true'
```

### 4.5 Slow-Query Detection via Cursor Wrapper

**File:** `monitoring/db.py`

A custom `CursorWrapper` subclass intercepts every `execute()` call, times it,
and writes a `SlowQueryLog` entry if the duration exceeds the threshold.

```python
import time
import hashlib

from django.db import connection  # the default
from django.db.backends.base.base import BaseDatabaseWrapper

_original_cursor = None

class SlowQueryCursorWrapper:
    """Wraps a database cursor to time each query."""

    def __init__(self, cursor, db_wrapper):
        self._cursor = cursor
        self._db_wrapper = db_wrapper

    def execute(self, sql, params=None):
        start = time.monotonic()
        try:
            return self._cursor.execute(sql, params)
        finally:
            elapsed_ms = (time.monotonic() - start) * 1000
            if elapsed_ms >= settings.MONITORING_SLOW_QUERY_THRESHOLD_MS:
                _record_slow_query(
                    db=self._db_wrapperalias,
                    sql=sql,
                    params=params,
                    duration_ms=round(elapsed_ms, 3),
                    threshold_ms=settings.MONITORING_SLOW_QUERY_THRESHOLD_MS,
                )

    # execute, executemany, __getattr__ delegate to self._cursor ...
```

**Installation hook:** Override the connection's cursor class at app startup:

```python
# monitoring/apps.py
def _patch_database_wrapper():
    """Replace CursorWrapper so slow queries are captured."""
    from django.db.backends.base.base import BaseDatabaseWrapper
    from monitoring.db import SlowQueryCursorWrapper

    original_cursor = BaseDatabaseWrapper.make_cursor

    def patched_cursor(self, *args, **kwargs):
        cursor = original_cursor(self, *args, **kwargs)
        return SlowQueryCursorWrapper(cursor, self)

    BaseDatabaseWrapper.make_cursor = patched_cursor
```

> This monkey-patch is applied once in `ReadyMixin.ready()`. It is
> **disabled in testing** (`IS_TESTING`) to avoid polluting test output and
> slowing down the test suite.

### 4.6 Connection-Pool Metrics

**File:** `monitoring/services.py`

```python
def collect_connection_metrics(alias='default'):
    """Return a dict of pool/connection metrics for the given alias."""
    db_engine = settings.DATABASES[alias]['ENGINE']

    if db_engine == 'django.db.backends.postgresql':
        return _collect_postgres_metrics(alias)
    elif db_engine == 'django.db.backends.sqlite3':
        return _collect_sqlite_metrics(alias)
    else:
        return {'engine': db_engine, 'connections_total': 1, 'connections_active': 0}
```

#### PostgreSQL implementation

```python
def _collect_postgres_metrics(alias='default'):
    conn = connections[alias]
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT
                count(*) FILTER (WHERE state = 'active') AS active,
                count(*) FILTER (WHERE state = 'idle')   AS idle,
                count(*)                            AS total
            FROM pg_stat_activity
            WHERE datname = current_database()
        """)
        row = cursor.fetchone()
        cursor.execute("""
            SELECT count(*) FROM pg_stat_activity WHERE wait_event IS NOT NULL
        """)
        waiting = cursor.fetchone()[0]
        cursor.execute("SELECT setting::int FROM pg_settings WHERE name = 'max_connections'")
        max_conn = cursor.fetchone()[0]

    return {
        'engine': 'postgresql',
        'connections_total': row['total'],
        'connections_active': row['active'],
        'connections_idle': row['idle'],
        'connections_waiting': waiting,
        'max_connections': max_conn,
        'pool_utilization_pct': round(row['total'] / max_conn * 100, 2) if max_conn else None,
    }
```

#### SQLite implementation

```python
def _collect_sqlite_metrics(alias='default'):
    conn = connections[alias]
    return {
        'engine': 'sqlite',
        'connections_total': 1,
        'connections_active': 0,
        'connections_idle': 1,
        'database_file': conn.settings_dict['NAME'],
        'reachable': _test_sqlite_connection(conn),
    }
```

### 4.7 Health Check Orchestration

```python
def run_health_check(alias='default'):
    """Execute a full health check and persist a HealthCheckResult."""
    metrics = collect_connection_metrics(alias)
    slow_count = SlowQueryLog.objects.filter(
        captured_at__gte=timezone.now() - timedelta(
            seconds=settings.MONITORING_HEALTH_CHECK_INTERVAL_SECONDS
        )
    ).count()

    metrics['slow_query_count'] = slow_count
    status = _determine_status(metrics)

    return HealthCheckResult.objects.create(
        status=status,
        database_engine=metrics.get('engine', 'unknown'),
        connections_total=metrics.get('connections_total', 0),
        connections_active=metrics.get('connections_active', 0),
        connections_idle=metrics.get('connections_idle', 0),
        slow_query_count=slow_count,
        details=metrics,
    )
```

**Status thresholds:**

| Metric | Warning | Critical |
|---|---|---|
| `pool_utilization_pct` | > 75 % | > 90 % |
| `slow_query_count` (in window) | > 5 | > 20 |
| Connection DB error | — | any exception |

### 4.8 Management Commands

#### `db_health_check`

```bash
python manage.py db_health_check [--alias default] [--json]
```

- Runs `run_health_check()`, prints a human-readable summary to stdout, or
  JSON with `--json`.
- Exit code: `0` healthy, `1` warning, `2` critical.

#### `db_health_check_daemon` (background)

```bash
python manage.py db_health_check_daemon --interval 30 --alias default
```

- Runs `run_health_check()` in a loop every N seconds.
- Intended to be launched as a background process (e.g., via systemd,
  Docker sidecar, or `cron_create`).

#### `purge_old_health_data`

```bash
python manage.py purge_old_health_data [--dry-run]
```

- Deletes `SlowQueryLog` and `HealthCheckResult` entries older than their
  respective retention settings.

### 4.9 Admin Integration

**File:** `monitoring/admin.py`

```
HealthCheckResultAdmin
  - list_display: checked_at, status, database_engine, connections_total,
    connections_active, slow_query_count
  - list_filter: status, database_engine, checked_at
  - readonly_fields: all fields
  - date_hierarchy: checked_at
  - actions: none

SlowQueryLogAdmin
  - list_display: captured_at, duration_ms, threshold_ms, sql_trunc, user_id,
    request_path, connection_alias
  - list_filter: connection_alias, captured_at
  - search_fields: sql
  - readonly_fields: all fields
  - actions: delete_selected (allowed), export_as_json (custom)
```

**Custom admin view — "Run Health Check"**

A top-level admin action button that triggers `run_health_check()` and
redirects to the resulting `HealthCheckResult` detail page.

```python
class MonitoringAdminSite(admin.AdminSite):
    """Custom admin site with a one-click health check."""

    def get_urls(self):
        urls = super().get_urls()
        return [
            path('db-health-check/run/', self.run_check, name='monitoring_run_check'),
        ] + urls

    def run_check(self, request):
        result = run_health_check()
        messages.success(request, f"Health check completed. Status: {result.status}")
        return redirect('admin:monitoring_healthcheckresult_change', result.pk)
```

### 4.10 Per-Request Query Timing (Optional)

When `MONITORING_CAPTURE_SLOW_QUERY_STACK = True`, the cursor wrapper also
captures `traceback.format_stack()` and stores it in the `stack_trace`
field. This is **off by default** in production because it adds measurable
overhead.

A `contextvars`-based request path is attached to slow queries when a
middleware is present:

```
monitoring/middleware.py
  QueryPathMiddleware
    - process_request: store request.path + request.user.id on a contextvar
    - __call__: delegate, then clear
```

The cursor wrapper reads the contextvar to populate `request_path` and
`user_id` on each `SlowQueryLog`.

### 4.11 Dependency

| Package | Version | Purpose |
|---|---|---|
| `psutil` | `>=5.9` | Optional: CPU/memory/disk I/O for extended health diagnostics |

`psutil` is listed as a production dependency because the health check
includes system-level metrics when available. If `psutil` is not installed,
the health check degrades gracefully and skips system metrics.

```python
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
```

The `details` JSON includes a `system` sub-dict when `psutil` is available:

```json
{
  "system": {
    "cpu_percent": 23.4,
    "memory_available_pct": 41.2,
    "disk_usage_pct": 67.0
  }
}
```

### 4.12 Background Process Integration

The daemon management command is designed to be started as a background
process via the platform's existing pattern:

```bash
# systemd / Docker / cron
python manage.py db_health_check_daemon --interval 30
```

This integrates with Kilo's `background_process` tool:

```
background_process.start(
    command: "python manage.py db_health_check_daemon --interval 30",
    description: "Database health check daemon",
    persistent: true,
)
```

---

## 5. App Structure & File Layout

### 5.1 `audit` app

```
audit/
├── __init__.py
├── admin.py              # AuditLogAdmin (read-only)
├── apps.py               # AuditConfig — connects signals, excludes self
├── middleware.py         # AuditContextMiddleware + contextvar
├── models.py             # AuditLog
├── signals.py            # pre_save / post_save / post_delete handlers
├── services.py           # diff logic, user extraction, bulk-op helpers
├── management/
│   └── commands/
│       └── purge_old_audit_logs.py
└── migrations/
    └── 0001_initial.py
```

### 5.2 `monitoring` app

```
monitoring/
├── __init__.py
├── admin.py              # HealthCheckResultAdmin, SlowQueryLogAdmin, custom AdminSite
├── apps.py               # MonitoringConfig — patches CursorWrapper on ready()
├── middleware.py         # QueryPathMiddleware (optional, for request correlation)
├── models.py             # SlowQueryLog, HealthCheckResult
├── db.py                 # SlowQueryCursorWrapper
├── services.py           # collect_*, run_health_check, _determine_status
├── management/
│   └── commands/
│       ├── db_health_check.py
│       ├── db_health_check_daemon.py
│       └── purge_old_health_data.py
└── migrations/
    └── 0001_initial.py
```

---

## 6. Integration Points

### 6.1 `INSTALLED_APPS`

```python
INSTALLED_APPS = [
    # ... existing ...
    'audit',
    'monitoring',
]
```

### 6.2 `MIDDLEWARE`

```python
MIDDLEWARE = [
    # ... existing middleware (order preserved) ...
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    # NEW: after auth middleware so request.user is available
    'audit.middleware.AuditContextMiddleware',
    'monitoring.middleware.QueryPathMiddleware',   # optional for slow-query correlation
    # ... remaining middleware ...
]
```

### 6.3 `sumia/urls.py`

No new public URLs. Admin URLs are auto-discovered. The health-check daemon is
started as a background process, not via HTTP.

### 6.4 Jazzmin sidebar (optional)

```python
JAZZMIN_SETTINGS = {
    # ... existing ...
    "custom_links": {
        "monitoring": [
            {
                "name": "Run DB Health Check",
                "url": "admin:monitoring_run_check",
                "icon": "fas fa-heartbeat",
            },
        ],
    },
    "topmenu": [
        {"app_label": "audit", "label": "Audit"},
        {"app_label": "monitoring", "label": "Monitoring"},
    ],
}
```

---

## 7. Testing Strategy

### 7.1 Audit History Tests

File: `audit/tests.py`

| Test | Validates |
|---|---|
| `test_audit_log_created_on_create` | Creating a Product via admin view writes an `AuditLog` with `action='create'` |
| `test_audit_log_created_on_update` | Editing a Product records only changed fields |
| `test_audit_log_created_on_delete` | Deleting a Product captures full snapshot |
| `test_audit_log_excludes_untracked_app` | Models in apps not in `AUDIT_TRACKED_APPS` produce no entries |
| `test_audit_log_user_is_staff` | Only staff users trigger logging (anonymous / API users do not) |
| `test_audit_log_retention_purge` | `purge_old_audit_logs` removes entries older than N days |
| `test_audit_log_rollback` | If the audited transaction is rolled back, no `AuditLog` is written |

### 7.2 Database Health Check Tests

File: `monitoring/tests.py`

| Test | Validates |
|---|---|
| `test_postgres_metrics_structure` | `collect_connection_metrics` returns the expected keys for PostgreSQL |
| `test_sqlite_metrics_structure` | `_collect_sqlite_metrics` returns engine + reachable |
| `test_slow_query_logging` | A query exceeding the threshold writes a `SlowQueryLog` |
| `test_health_check_status_healthy` | Under thresholds → `status='healthy'` |
| `test_health_check_status_warning` | High pool utilization → `status='warning'` |
| `test_health_check_status_critical` | Connection error → `status='critical'` + error message |
| `test_db_health_check_command_output` | `db_health_check --json` produces valid JSON |
| `test_purge_old_health_data` | Old `SlowQueryLog` / `HealthCheckResult` entries are removed |

Tests use `override_settings` to set thresholds low (e.g., 1 ms) and mock the
PostgreSQL functions when running under SQLite.

---

## 8. Limitations & Known Constraints

| # | Limitation | Mitigation |
|---|---|---|
| 1 | `QuerySet.update()` / `.delete()` bulk operations bypass model signals | Document and add explicit `AuditLog.objects.create()` calls in service-layer bulk paths (future work) |
| 2 | SQLite has no real connection pool; metrics are synthetic | Health check reports `engine='sqlite'` and skips pool stats |
| 3 | Slow-query cursor wrapper adds per-query overhead | Threshold-gated: only writes when query exceeds threshold; can be disabled via env var |
| 4 | `psutil` is an additional dependency | Optional import; degrades gracefully if absent |
| 5 | Stack-trace capture is expensive | Off by default (`MONITORING_CAPTURE_SLOW_QUERY_STACK=False`) |
| 6 | `AuditLog.user` is `null` for data migrations and Celery tasks | `is_system` boolean flags these; documented in admin filter |
| 7 | Contextvar does not propagate across async task boundaries | Slow-query `user_id` / `request_path` will be null for background tasks (acceptable) |

---

## 9. Deployment Checklist

| Step | Owner | Command |
|---|---|---|
| 1 | Backend | `pip install psutil` (add to `requirements.txt` if not present) |
| 2 | Backend | Add `'audit'`, `'monitoring'` to `INSTALLED_APPS` |
| 3 | Backend | Insert `AuditContextMiddleware` after `AuthenticationMiddleware` |
| 4 | Backend | Add `AUDIT_*` and `MONITORING_*` settings to `.env` |
| 5 | Backend | `python manage.py makemigrations audit monitoring` |
| 5 | Backend | `python manage.py migrate` |
| 6 | DevOps | `python manage.py db_health_check` (manual baseline) |
| 7 | DevOps | Start daemon: `python manage.py db_health_check_daemon --interval 30` |
| 8 | DevOps | Schedule `purge_old_audit_logs` and `purge_old_health_data` via cron |
| 9 | DBA | Enable `pg_stat_statements` on PostgreSQL for additional query insights |
| 10 | DevOps | Configure `MONITORING_HEALTH_CHECK_CRITICAL` alert routing (future) |

---

## 10. Migration Plan

### Phase 1: Schema & Core Logic

1. Create `audit` and `monitoring` apps with models, signals, services, and
   middleware.
2. Write and run migrations.
3. Add to `INSTALLED_APPS` and `MIDDLEWARE`.
4. Run unit tests.

### Phase 2: Admin Integration

1. Register `AuditLog`, `HealthCheckResult`, and `SlowQueryLog` in admin.
2. Add Jazzmin custom links for the health-check trigger.
3. Apply read-only enforcement for `AuditLog`.

### Phase 3: Operationalization

1. Deploy health-check daemon as a background process.
2. Schedule retention purges.
3. Configure alerting thresholds based on baseline metrics.

---

## 11. API Reference (Summary)

### 11.1 `audit/services.py`

```
get_audit_user(request) -> User | None
_diff_fields(old_instance, new_instance) -> dict[str, dict]
_serializable(value) -> Any
capture_audit_entry(sender, instance, action, request) -> AuditLog
```

### 11.2 `monitoring/services.py`

```
collect_connection_metrics(alias='default') -> dict
_collect_postgres_metrics(alias='default') -> dict
_collect_sqlite_metrics(alias='default') -> dict
run_health_check(alias='default') -> HealthCheckResult
_determine_status(metrics: dict) -> str  # 'healthy' | 'warning' | 'critical'
```

### 11.3 `monitoring/management/commands/db_health_check.py`

```
Command.handle(*args, **options)
  options: --alias, --json
```

### 11.4 `monitoring/management/commands/db_health_check_daemon.py`

```
Command.handle(*args, **options)
  options: --alias, --interval
```

---

## 12. Backwards Compatibility

- **No existing model changes.** All audit/history is stored in new models in
  separate apps.
- **No view or URL changes.** Both features are admin-only; no customer-facing
  endpoints are affected.
- **Middleware is additive.** Inserting middleware after `AuthenticationMiddleware`
  does not affect existing request flow.
- **Cursor wrapper patch is isolated.** It only wraps `make_cursor` and
  delegates all other `BaseDatabaseWrapper` behavior unchanged.
- **`DEBUG` / test mode safety.** Both features check `IS_TESTING` and
  `DEBUG` flags to avoid slowing down or polluting test output and local
  development.

---

## 13. References

- Django Signals: https://docs.djangoproject.com/en/4.2/topics/signals/
- Django Middleware: https://docs.djangoproject.com/en/4.2/topics/http/middleware/
- Django Custom Management Commands: https://docs.djangoproject.com/en/4.2/howto/custom-management-commands/
- Django Database Instrumentation: https://docs.djangoproject.com/en/4.2/topics/db/instrumentation/
- PostgreSQL `pg_stat_activity`: https://www.postgresql.org/docs/current/monitoring-stats.html
- `contextvars` (PEP 567): https://docs.python.org/3/library/contextvars.html
- Existing project conventions: `docs/project_structure.md`

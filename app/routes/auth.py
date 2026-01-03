"""Compatibility shim so `from app.routes import auth` works.

Legacy code expected auth to live under `app.routes.auth` but the
implementations were moved to `app.auths.routes`. Re-export the router
here to keep imports stable.
"""
from app.auths.routes import router  # re-export for backwards compat

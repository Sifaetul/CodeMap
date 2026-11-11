import pytest
from apps.api.main import limiter
from apps.api.routes.auth import limiter as auth_limiter

limiter.enabled = False
auth_limiter.enabled = False

from datetime import datetime, timedelta, timezone
from pathlib import Path
import importlib.util
import sys
import types

import jwt

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_DIR = ROOT / "plugins" / "authentication" / "templates"


def load_auth_module(monkeypatch):
    """Load auth.py with lightweight stubs instead of a real database."""
    config = types.ModuleType("config")
    config.JWT_SECRET = "test-only-secret-for-jwt-tests-32-bytes-minimum"
    config.ACCESS_TOKEN_EXPIRE_MINUTES = 30

    models = types.ModuleType("models")

    class User:
        def __init__(self, user_id, username="test_user"):
            self.id = user_id
            self.username = username
            self.password_hash = "unused"

    models.User = User

    database = types.ModuleType("app.core.database")
    database.get_db = lambda: None

    package = types.ModuleType("test_auth_package")
    package.__path__ = [str(TEMPLATE_DIR)]

    monkeypatch.setitem(sys.modules, "test_auth_package", package)
    monkeypatch.setitem(sys.modules, "test_auth_package.config", config)
    monkeypatch.setitem(sys.modules, "test_auth_package.models", models)
    monkeypatch.setitem(sys.modules, "app.core.database", database)

    spec = importlib.util.spec_from_file_location(
        "test_auth_package.auth",
        TEMPLATE_DIR / "auth.py",
    )
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, spec.name, module)
    spec.loader.exec_module(module)

    return module, User


def test_access_token_contains_expected_claims(monkeypatch):
    auth, User = load_auth_module(monkeypatch)

    token = auth.create_access_token(User(123))
    payload = jwt.decode(
        token,
        auth.JWT_SECRET,
        algorithms=["HS256"],
    )

    assert payload["sub"] == "123"
    assert payload["type"] == "access"
    assert "iat" in payload
    assert "exp" in payload


def test_expired_token_is_rejected():
    secret = "test-only-secret-for-jwt-tests-32-bytes-minimum"
    now = datetime.now(timezone.utc)

    token = jwt.encode(
        {
            "sub": "123",
            "type": "access",
            "iat": now - timedelta(minutes=10),
            "exp": now - timedelta(minutes=1),
        },
        secret,
        algorithm="HS256",
    )

    try:
        jwt.decode(token, secret, algorithms=["HS256"])
        assert False, "Expected expired token to be rejected"
    except jwt.ExpiredSignatureError:
        pass


def test_tampered_token_signature_is_rejected():
    secret = "test-only-secret-for-jwt-tests-32-bytes-minimum"
    token = jwt.encode(
        {
            "sub": "123",
            "type": "access",
            "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
        },
        secret,
        algorithm="HS256",
    )

    tampered_token = token[:-1] + ("a" if token[-1] != "a" else "b")

    try:
        jwt.decode(tampered_token, secret, algorithms=["HS256"])
        assert False, "Expected tampered token to be rejected"
    except jwt.InvalidTokenError:
        pass

def test_get_current_user_rejects_expired_token(monkeypatch):
    from fastapi import HTTPException

    auth, _ = load_auth_module(monkeypatch)
    now = datetime.now(timezone.utc)

    token = jwt.encode(
        {
            "sub": "123",
            "type": "access",
            "iat": now - timedelta(minutes=10),
            "exp": now - timedelta(minutes=1),
        },
        auth.JWT_SECRET,
        algorithm="HS256",
    )

    try:
        auth.get_current_user(token=token, db=None)
        assert False, "Expected expired token to be rejected"
    except HTTPException as exc:
        assert exc.status_code == 401
        assert exc.detail == "Invalid or expired access token"

def test_get_current_user_rejects_tampered_token(monkeypatch):
    from fastapi import HTTPException

    auth, _ = load_auth_module(monkeypatch)

    token = jwt.encode(
        {
            "sub": "123",
            "type": "access",
            "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
        },
        auth.JWT_SECRET,
        algorithm="HS256",
    )

    tampered_token = token[:-1] + (
        "a" if token[-1] != "a" else "b"
    )

    try:
        auth.get_current_user(token=tampered_token, db=None)
        assert False, "Expected tampered token to be rejected"
    except HTTPException as exc:
        assert exc.status_code == 401
        assert exc.detail == "Invalid or expired access token"

def test_get_current_user_rejects_wrong_token_type(monkeypatch):
    from fastapi import HTTPException

    auth, _ = load_auth_module(monkeypatch)

    token = jwt.encode(
        {
            "sub": "123",
            "type": "refresh",
            "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
        },
        auth.JWT_SECRET,
        algorithm="HS256",
    )

    try:
        auth.get_current_user(token=token, db=None)
        assert False, "Expected wrong token type to be rejected"
    except HTTPException as exc:
        assert exc.status_code == 401
        assert exc.detail == "Invalid or expired access token"

def test_get_current_user_rejects_nonexistent_user(monkeypatch):
    from fastapi import HTTPException

    auth, _ = load_auth_module(monkeypatch)

    token = jwt.encode(
        {
            "sub": "999999",
            "type": "access",
            "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
        },
        auth.JWT_SECRET,
        algorithm="HS256",
    )

    class FakeDB:
        def get(self, model, user_id):
            assert user_id == 999999
            return None

    try:
        auth.get_current_user(token=token, db=FakeDB())
        assert False, "Expected nonexistent user to be rejected"
    except HTTPException as exc:
        assert exc.status_code == 401
        assert exc.detail == "Invalid or expired access token"





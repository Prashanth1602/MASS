from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

AUTH_TEMPLATE = (ROOT / "plugins" / "authentication" / "templates" / "auth.py")
ROUTER_TEMPLATE = (ROOT / "plugins" / "authentication" / "templates" / "router.py")

def test_auth_template_generates_and_validates_access_tokens():
    content = AUTH_TEMPLATE.read_text(encoding="utf-8")

    assert "def create_access_token(" in content
    assert "jwt.encode(" in content
    assert '"sub"' in content
    assert '"exp"' in content
    assert "def get_current_user(" in content
    assert "jwt.decode(" in content
    assert 'algorithms=["HS256"]' in content


def test_auth_template_rejects_invalid_credentials():
    content = ROUTER_TEMPLATE.read_text(encoding="utf-8")

    assert 'router.post("/authenticate"' in content
    assert "status.HTTP_401_UNAUTHORIZED" in content
    assert "Invalid username or password" in content


def test_auth_router_protects_current_user_endpoint():
    content = ROUTER_TEMPLATE.read_text(encoding="utf-8")

    assert 'router.get("/me"' in content
    assert "Depends(get_current_user)" in content

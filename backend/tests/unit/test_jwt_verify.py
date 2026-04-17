from jose import jwt
from jwt_verify import create_access_token, get_current_user_id_cookie
import os
import sys
from fastapi import HTTPException

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))


class DummyRequest:
    def __init__(self, token=None):
        self.cookies = {}
        if token is not None:
            self.cookies["access_token"] = token


def test_create_access_token_has_sub_and_type_claims():
    token = create_access_token(user_id=123)
    payload = jwt.get_unverified_claims(token)
    assert payload["sub"] == "123"
    assert payload["type"] == "access"
    assert "iat" in payload
    assert "exp" in payload


def test_get_current_user_id_cookie_valid_token_returns_int():
    token = create_access_token(user_id=42)
    request = DummyRequest(token)
    assert get_current_user_id_cookie(request) == 42


def test_get_current_user_id_cookie_missing_token_raises_401():
    request = DummyRequest()
    try:
        get_current_user_id_cookie(request)
        assert False, "Expected HTTPException"
    except HTTPException as exc:
        assert exc.status_code == 401
        assert exc.detail == "Access token required"


def test_get_current_user_id_cookie_invalid_token_raises_401():
    request = DummyRequest("not-a-token")
    try:
        get_current_user_id_cookie(request)
        assert False, "Expected HTTPException"
    except HTTPException as exc:
        assert exc.status_code == 401
        assert exc.detail == "Invalid access token"


def test_get_current_user_id_cookie_non_int_sub_raises_401():
    bad_token = jwt.encode({"sub": "abc", "type": "access"}, os.getenv("JWT_SECRET"), algorithm="HS256")
    request = DummyRequest(bad_token)
    try:
        get_current_user_id_cookie(request)
        assert False, "Expected HTTPException"
    except HTTPException as exc:
        assert exc.status_code == 401
        assert exc.detail == "Invalid access token"

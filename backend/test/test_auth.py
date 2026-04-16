import os
import sys
from unittest.mock import MagicMock, patch

from fastapi import HTTPException
from fastapi.testclient import TestClient
import mysql.connector

# Ensure the backend directory is in the path for local runs and CI.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import app
from auth import parse_json_column, ensure_user_planner_state_table, DEFAULT_PLANNER_STATE

client = TestClient(app)


def _mock_db():
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    return mock_conn, mock_cursor

@patch("auth.get_db_connection")
def test_register_success_returns_user_id(mock_get_db):
    mock_conn, mock_cursor = _mock_db()
    mock_get_db.return_value = mock_conn
    mock_cursor.lastrowid = 77

    payload = {"username": "newuser", "password": "pw12345", "email": "new@x.com"}
    response = client.post("/auth/register", json=payload)

    assert response.status_code == 200
    assert response.json()["message"] == "User registered successfully"
    assert response.json()["user_id"] == 77


@patch("auth.get_db_connection")
def test_register_missing_username_returns_400(mock_get_db):
    response = client.post(
        "/auth/register",
        json={"password": "pw12345", "email": "new@x.com"},
    )
    assert response.status_code == 400
    mock_get_db.assert_not_called()


@patch("auth.get_db_connection")
def test_register_missing_password_returns_400(mock_get_db):
    response = client.post(
        "/auth/register",
        json={"username": "newuser", "email": "new@x.com"},
    )
    assert response.status_code == 400
    mock_get_db.assert_not_called()


@patch("auth.get_db_connection")
def test_register_missing_email_returns_400(mock_get_db):
    response = client.post(
        "/auth/register",
        json={"username": "newuser", "password": "pw12345"},
    )
    assert response.status_code == 400
    mock_get_db.assert_not_called()


@patch("auth.get_db_connection")
def test_register_empty_required_fields_returns_400(mock_get_db):
    response = client.post(
        "/auth/register",
        json={"username": "", "password": "", "email": ""},
    )
    assert response.status_code == 400
    mock_get_db.assert_not_called()


@patch("auth.get_db_connection")
def test_register_duplicate_conflict_returns_409(mock_get_db):
    mock_conn, mock_cursor = _mock_db()
    mock_get_db.return_value = mock_conn
    mock_cursor.execute.side_effect = mysql.connector.IntegrityError("duplicate entry")

    payload = {"username": "existing", "password": "pw12345", "email": "old@x.com"}
    response = client.post("/auth/register", json=payload)

    assert response.status_code == 409
    assert response.json()["detail"] == "Username or email already exists"


@patch("auth.get_db_connection")
def test_register_db_error_returns_500(mock_get_db):
    mock_conn, mock_cursor = _mock_db()
    mock_get_db.return_value = mock_conn
    mock_cursor.execute.side_effect = RuntimeError("database unavailable")

    payload = {"username": "u1", "password": "pw12345", "email": "u1@x.com"}
    response = client.post("/auth/register", json=payload)

    assert response.status_code == 500
    assert "Registration failed" in response.json()["detail"]


@patch("auth.get_db_connection")
def test_register_hashes_password_before_insert(mock_get_db):
    mock_conn, mock_cursor = _mock_db()
    mock_get_db.return_value = mock_conn

    raw_password = "my-plain-password"
    payload = {"username": "hashuser", "password": raw_password, "email": "hash@x.com"}
    response = client.post("/auth/register", json=payload)

    assert response.status_code == 200
    inserted_values = mock_cursor.execute.call_args[0][1]
    inserted_password = inserted_values[1]
    assert inserted_password != raw_password
    assert inserted_password.startswith("$2")

@patch("auth.bcrypt.checkpw", return_value=True)
@patch("auth.get_db_connection")
def test_login_success_sets_cookie_and_tokens(mock_get_db, _mock_checkpw):
    mock_conn, mock_cursor = _mock_db()
    mock_get_db.return_value = mock_conn
    mock_cursor.fetchone.return_value = {
        "user_id": 1,
        "password_hash": "$2b$12$KIX0.vjH.O8E.O7v/8oI8uL1.W5.Z5.Z5.Z5.Z5.Z5.Z5.Z5.Z5.",
    }

    response = client.post(
        "/auth/login",
        json={"username": "testuser", "password": "pass123"},
    )

    assert response.status_code == 200
    assert "access_token" in response.json()
    assert "refresh_token" in response.json()
    assert "access_token" in response.cookies


@patch("auth.get_db_connection")
def test_login_unknown_user_returns_401(mock_get_db):
    mock_conn, mock_cursor = _mock_db()
    mock_get_db.return_value = mock_conn
    mock_cursor.fetchone.return_value = None

    response = client.post(
        "/auth/login",
        json={"username": "missing-user", "password": "wrong-pass"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid username or password"


@patch("auth.bcrypt.checkpw", return_value=False)
@patch("auth.get_db_connection")
def test_login_wrong_password_returns_401(mock_get_db, _mock_checkpw):
    mock_conn, mock_cursor = _mock_db()
    mock_get_db.return_value = mock_conn
    mock_cursor.fetchone.return_value = {
        "user_id": 1,
        "password_hash": "$2b$12$KIX0.vjH.O8E.O7v/8oI8uL1.W5.Z5.Z5.Z5.Z5.Z5.Z5.Z5.Z5.",
    }

    response = client.post(
        "/auth/login",
        json={"username": "testuser", "password": "bad-pass"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid username or password"


@patch("auth.get_db_connection")
def test_login_missing_username_returns_400(mock_get_db):
    response = client.post("/auth/login", json={"password": "pass123"})
    assert response.status_code == 400
    assert response.json()["detail"] == "Username and password required"
    mock_get_db.assert_not_called()


@patch("auth.get_db_connection")
def test_login_missing_password_returns_400(mock_get_db):
    response = client.post("/auth/login", json={"username": "testuser"})
    assert response.status_code == 400
    assert response.json()["detail"] == "Username and password required"
    mock_get_db.assert_not_called()


@patch("auth.get_db_connection")
def test_login_empty_username_password_returns_400(mock_get_db):
    response = client.post("/auth/login", json={"username": "", "password": ""})
    assert response.status_code == 400
    mock_get_db.assert_not_called()


@patch("auth.get_db_connection")
def test_login_db_failure_returns_500(mock_get_db):
    mock_conn, mock_cursor = _mock_db()
    mock_get_db.return_value = mock_conn
    mock_cursor.execute.side_effect = RuntimeError("db down")

    response = client.post(
        "/auth/login",
        json={"username": "testuser", "password": "pass123"},
    )

    assert response.status_code == 500
    assert "Login failed" in response.json()["detail"]


@patch("auth.get_db_connection")
def test_login_malformed_password_hash_returns_500(mock_get_db):
    mock_conn, mock_cursor = _mock_db()
    mock_get_db.return_value = mock_conn
    mock_cursor.fetchone.return_value = {"user_id": 1, "password_hash": None}

    response = client.post(
        "/auth/login",
        json={"username": "testuser", "password": "pass123"},
    )

    assert response.status_code == 500
    assert "Login failed" in response.json()["detail"]

def test_logout_success_clears_cookie():
    response = client.post("/auth/logout")
    assert response.status_code == 200
    assert response.json()["ok"] is True
    set_cookie_header = response.headers.get("set-cookie", "")
    assert "access_token=" in set_cookie_header


def test_logout_without_cookie_still_returns_200():
    response = client.post("/auth/logout")
    assert response.status_code == 200
    assert response.json() == {"ok": True}

@patch("auth.get_db_connection")
@patch("auth.get_current_user_id_cookie", return_value=1)
def test_profile_get_success_returns_user(
    _mock_user_id,
    mock_get_db,
):
    mock_conn, mock_cursor = _mock_db()
    mock_get_db.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = {
        "user_id": 1,
        "username": "testuser",
        "email": "test@example.com",
        "created_at": "2026-04-15T00:00:00Z",
    }

    response = client.get("/auth/profile")
    assert response.status_code == 200
    assert response.json()["username"] == "testuser"


@patch("auth.get_current_user_id_cookie", return_value=1)
def test_profile_update_with_no_fields_returns_400(_mock_user_id):
    response = client.put("/auth/profile", json={})
    assert response.status_code == 400
    assert response.json()["detail"] == "At least username or email must be provided"


@patch("auth.get_db_connection")
@patch("auth.get_current_user_id_cookie", return_value=1)
def test_profile_get_not_found_returns_404(_mock_user_id, mock_get_db):
    mock_conn, mock_cursor = _mock_db()
    mock_get_db.return_value = mock_conn
    mock_cursor.fetchone.return_value = None

    response = client.get("/auth/profile")
    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"


@patch("auth.get_db_connection")
@patch("auth.get_current_user_id_cookie", return_value=1)
def test_profile_update_success(_mock_user_id, mock_get_db):
    mock_conn, mock_cursor = _mock_db()
    mock_get_db.return_value = mock_conn
    mock_cursor.rowcount = 1

    response = client.put(
        "/auth/profile",
        json={"username": "newname", "email": "new@example.com"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Profile updated successfully"


@patch("auth.get_db_connection")
@patch("auth.get_current_user_id_cookie", return_value=1)
def test_profile_update_user_not_found_returns_404(_mock_user_id, mock_get_db):
    mock_conn, mock_cursor = _mock_db()
    mock_get_db.return_value = mock_conn
    mock_cursor.rowcount = 0

    response = client.put("/auth/profile", json={"username": "newname"})
    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"


@patch("auth.get_db_connection")
@patch("auth.get_current_user_id_cookie", return_value=1)
def test_profile_update_username_conflict_returns_409(_mock_user_id, mock_get_db):
    mock_conn, mock_cursor = _mock_db()
    mock_get_db.return_value = mock_conn
    mock_cursor.execute.side_effect = mysql.connector.IntegrityError("username duplicate")

    response = client.put("/auth/profile", json={"username": "taken"})
    assert response.status_code == 409
    assert response.json()["detail"] == "Username already exists"


@patch("auth.get_db_connection")
@patch("auth.get_current_user_id_cookie", return_value=1)
def test_profile_update_email_conflict_returns_409(_mock_user_id, mock_get_db):
    mock_conn, mock_cursor = _mock_db()
    mock_get_db.return_value = mock_conn
    mock_cursor.execute.side_effect = mysql.connector.IntegrityError("email duplicate")

    response = client.put("/auth/profile", json={"email": "taken@example.com"})
    assert response.status_code == 409
    assert response.json()["detail"] == "Email already exists"


@patch("auth.get_db_connection")
@patch("auth.get_current_user_id_cookie", return_value=1)
def test_get_planner_state_default_when_missing(_mock_user_id, mock_get_db):
    mock_conn, mock_cursor = _mock_db()
    mock_get_db.return_value = mock_conn
    mock_cursor.fetchone.return_value = None

    response = client.get("/auth/planner-state")
    assert response.status_code == 200
    assert response.json() == DEFAULT_PLANNER_STATE


@patch("auth.get_db_connection")
@patch("auth.get_current_user_id_cookie", return_value=1)
def test_get_planner_state_parses_json_columns(_mock_user_id, mock_get_db):
    mock_conn, mock_cursor = _mock_db()
    mock_get_db.return_value = mock_conn
    mock_cursor.fetchone.return_value = {
        "major_data": '{"selectedMajor":"CS","completedCourses":["CS 146"],"submitted":true}',
        "roadmap_data": '[{"semester":"Fall"}]',
        "schedule_data": '{"schedules":[],"professorFreqs":{},"selectedScheduleIndex":0}',
    }

    response = client.get("/auth/planner-state")
    assert response.status_code == 200
    data = response.json()
    assert data["major"]["selectedMajor"] == "CS"
    assert data["roadmap"][0]["semester"] == "Fall"


@patch("auth.get_db_connection")
@patch("auth.get_current_user_id_cookie", return_value=1)
def test_get_planner_state_invalid_json_uses_fallback(_mock_user_id, mock_get_db):
    mock_conn, mock_cursor = _mock_db()
    mock_get_db.return_value = mock_conn
    mock_cursor.fetchone.return_value = {
        "major_data": "not-json",
        "roadmap_data": "also-not-json",
        "schedule_data": "bad-json",
    }

    response = client.get("/auth/planner-state")
    assert response.status_code == 200
    assert response.json() == DEFAULT_PLANNER_STATE


@patch("auth.get_db_connection")
@patch("auth.get_current_user_id_cookie", return_value=1)
def test_update_planner_state_success(_mock_user_id, mock_get_db):
    mock_conn, _mock_cursor = _mock_db()
    mock_get_db.return_value = mock_conn

    payload = {
        "major": {"selectedMajor": "SE", "completedCourses": [], "submitted": True},
        "roadmap": [{"semester": "Spring"}],
        "schedule": {"schedules": [], "professorFreqs": {}, "selectedScheduleIndex": 0},
    }
    response = client.put("/auth/planner-state", json=payload)
    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_parse_json_column_fallback_cases():
    assert parse_json_column(None, {"x": 1}) == {"x": 1}
    assert parse_json_column("", {"x": 1}) == {"x": 1}
    assert parse_json_column("not-json", {"x": 1}) == {"x": 1}


def test_parse_json_column_with_valid_json_string():
    value = parse_json_column('{"a": 1}', {})
    assert value == {"a": 1}


def test_ensure_user_planner_state_table_executes_sql():
    mock_conn, mock_cursor = _mock_db()
    ensure_user_planner_state_table(mock_conn)
    mock_cursor.execute.assert_called_once()
    mock_conn.commit.assert_called_once()

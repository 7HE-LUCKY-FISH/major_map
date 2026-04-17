import os
import sys
from unittest.mock import MagicMock, patch

import mysql.connector
import pytest

# Ensure backend directory is importable.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import db_module


@patch("db_module.mysql.connector.connect")
def test_get_db_connection_success_uses_env_values(mock_connect):
    fake_conn = MagicMock()
    mock_connect.return_value = fake_conn

    with patch.dict(
        os.environ,
        {
            "DB_HOST": "db-host",
            "DB_USER": "db-user",
            "DB_PASSWORD": "db-pass",
            "DB_NAME": "db-name",
            "DB_PORT": "3307",
        },
        clear=False,
    ):
        conn = db_module.get_db_connection()

    assert conn == fake_conn
    mock_connect.assert_called_once_with(
        host="db-host",
        user="db-user",
        password="db-pass",
        database="db-name",
        port=3307,
        auth_plugin="mysql_native_password",
    )


@patch("db_module.mysql.connector.connect")
def test_get_db_connection_error_returns_none(mock_connect):
    mock_connect.side_effect = mysql.connector.Error("cannot connect")
    conn = db_module.get_db_connection()
    assert conn is None


@patch("db_module.mysql.connector.connect")
def test_get_server_connection_success(mock_connect):
    fake_conn = MagicMock()
    mock_connect.return_value = fake_conn
    conn = db_module.get_server_connection()
    assert conn == fake_conn
    called = mock_connect.call_args.kwargs
    assert called["auth_plugin"] == "mysql_native_password"
    assert "database" not in called


@patch("db_module.mysql.connector.connect")
def test_get_server_connection_error_returns_none(mock_connect):
    mock_connect.side_effect = mysql.connector.Error("server down")
    conn = db_module.get_server_connection()
    assert conn is None


@patch("db_module.time.sleep")
@patch("db_module.get_db_connection")
def test_get_db_connection_with_retry_eventual_success(mock_get_db, mock_sleep):
    fake_conn = MagicMock()
    mock_get_db.side_effect = [None, None, fake_conn]

    conn = db_module.get_db_connection_with_retry(max_attempts=5, sleep_seconds=0)

    assert conn == fake_conn
    assert mock_get_db.call_count == 3
    assert mock_sleep.call_count == 2


@patch("db_module.sys.exit")
@patch("db_module.time.sleep")
@patch("db_module.get_db_connection")
def test_get_db_connection_with_retry_exits_after_max_attempts(
    mock_get_db,
    mock_sleep,
    mock_exit,
):
    mock_get_db.return_value = None
    mock_exit.side_effect = SystemExit(1)

    with pytest.raises(SystemExit):
        db_module.get_db_connection_with_retry(max_attempts=3, sleep_seconds=0)

    assert mock_get_db.call_count == 3
    assert mock_sleep.call_count == 3
    mock_exit.assert_called_once_with(1)


@patch("db_module.time.sleep")
@patch("db_module.get_server_connection")
def test_get_server_connection_with_retry_eventual_success(
    mock_get_server,
    mock_sleep,
):
    fake_conn = MagicMock()
    mock_get_server.side_effect = [None, fake_conn]

    conn = db_module.get_server_connection_with_retry(max_attempts=4, sleep_seconds=0)

    assert conn == fake_conn
    assert mock_get_server.call_count == 2
    assert mock_sleep.call_count == 1


@patch("db_module.sys.exit")
@patch("db_module.time.sleep")
@patch("db_module.get_server_connection")
def test_get_server_connection_with_retry_exits_after_max_attempts(
    mock_get_server,
    mock_sleep,
    mock_exit,
):
    mock_get_server.return_value = None
    mock_exit.side_effect = SystemExit(1)

    with pytest.raises(SystemExit):
        db_module.get_server_connection_with_retry(max_attempts=2, sleep_seconds=0)

    assert mock_get_server.call_count == 2
    assert mock_sleep.call_count == 2
    mock_exit.assert_called_once_with(1)

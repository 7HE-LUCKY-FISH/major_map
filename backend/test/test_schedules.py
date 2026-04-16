import json
import os
import sys
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

# Ensure backend directory is importable in local runs and CI.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import app

client = TestClient(app)


def _mock_db():
    conn = MagicMock()
    cursor = MagicMock()
    conn.cursor.return_value = cursor
    return conn, cursor


def _candidate(name, slot, prob):
    return {
        "instructor_name": name,
        "slot_label": slot,
        "prob_scheduled": prob,
    }


# 1
@patch("schedules.get_current_user_id_cookie")
def test_generate_v2_requires_auth_when_not_bypassed(mock_user):
    mock_user.return_value = None
    with patch.dict(os.environ, {"DEV_BYPASS": "0"}, clear=False):
        response = client.post("/schedules/generate_v2", json={"courses": ["CS 146"]})
    assert response.status_code == 401
    assert response.json()["detail"] == "Access token required"


# 2
def test_generate_v2_requires_courses_list():
    with patch.dict(os.environ, {"DEV_BYPASS": "1"}, clear=False):
        response = client.post("/schedules/generate_v2", json={"courses": []})
    assert response.status_code == 400
    assert response.json()["detail"] == "courses list is required"


# 3
@patch("schedules.load_svm_artifact")
def test_generate_v2_svm_missing_returns_503(mock_load):
    mock_load.side_effect = FileNotFoundError("model missing")
    with patch.dict(os.environ, {"DEV_BYPASS": "1"}, clear=False):
        response = client.post("/schedules/generate_v2", json={"courses": ["CS 146"]})
    assert response.status_code == 503
    assert "model missing" in response.json()["detail"]


# 4
@patch("schedules.load_svm_artifact")
@patch("schedules.generate_professor_slot_candidates")
def test_generate_v2_candidate_db_error_returns_500(mock_candidates, mock_load):
    mock_load.return_value = {"model": MagicMock()}
    mock_candidates.side_effect = RuntimeError("db exploded")
    with patch.dict(os.environ, {"DEV_BYPASS": "1"}, clear=False):
        response = client.post("/schedules/generate_v2", json={"courses": ["CS 146"]})
    assert response.status_code == 500
    assert "DB error for CS 146" in response.json()["detail"]


# 5
@patch("schedules.load_svm_artifact")
@patch("schedules.generate_professor_slot_candidates")
def test_generate_v2_no_candidates_returns_empty_sections(mock_candidates, mock_load):
    mock_load.return_value = {"model": MagicMock()}
    mock_candidates.return_value = []
    with patch.dict(os.environ, {"DEV_BYPASS": "1"}, clear=False):
        response = client.post("/schedules/generate_v2", json={"courses": ["CS 146"]})
    assert response.status_code == 200
    data = response.json()
    assert data["total_schedules"] == 1
    assert data["schedules"][0]["sections"] == []


# 6
@patch("schedules.load_svm_artifact")
@patch("schedules.generate_professor_slot_candidates")
@patch("schedules.score_candidates")
def test_generate_v2_filters_by_probability_threshold(mock_score, mock_candidates, mock_load):
    mock_load.return_value = {"model": MagicMock()}
    mock_candidates.return_value = [{"slot_label": "MW 09:00AM-10:15AM"}]
    mock_score.return_value = [
        _candidate("A", "MW 09:00AM-10:15AM", 0.90),
        _candidate("B", "MW 11:00AM-12:15PM", 0.65),
    ]
    with patch.dict(os.environ, {"DEV_BYPASS": "1"}, clear=False):
        response = client.post("/schedules/generate_v2", json={"courses": ["CS 146"]})
    assert response.status_code == 200
    sections = response.json()["schedules"][0]["sections"]
    assert len(sections) == 1
    assert sections[0]["instructor_name"] == "A"


# 7
@patch("schedules.load_svm_artifact")
@patch("schedules.generate_professor_slot_candidates")
@patch("schedules.score_candidates")
def test_generate_v2_fallback_to_top3_when_no_threshold_hits(mock_score, mock_candidates, mock_load):
    mock_load.return_value = {"model": MagicMock()}
    mock_candidates.return_value = [{"slot_label": "MW 09:00AM-10:15AM"}]
    mock_score.return_value = [
        _candidate("A", "MW 09:00AM-10:15AM", 0.61),
        _candidate("B", "MW 10:30AM-11:45AM", 0.62),
        _candidate("C", "TR 09:00AM-10:15AM", 0.63),
        _candidate("D", "TR 01:00PM-02:15PM", 0.64),
    ]
    with patch.dict(os.environ, {"DEV_BYPASS": "1"}, clear=False):
        response = client.post("/schedules/generate_v2", json={"courses": ["CS 146"]})
    assert response.status_code == 200
    sections = response.json()["schedules"][0]["sections"]
    assert 1 <= len(sections) <= 3


# 8
@patch("schedules.load_svm_artifact")
@patch("schedules.generate_professor_slot_candidates")
@patch("schedules.score_candidates")
def test_generate_v2_conflict_pruning_keeps_conflict_free_options(mock_score, mock_candidates, mock_load):
    mock_load.return_value = {"model": MagicMock()}
    # two courses in request => called twice
    mock_candidates.side_effect = [
        [{"slot_label": "MW 09:00AM-10:15AM"}],
        [{"slot_label": "MW 09:30AM-10:45AM"}],
    ]
    mock_score.side_effect = [
        [
            _candidate("A1", "MW 09:00AM-10:15AM", 0.9),
            _candidate("A2", "TR 01:00PM-02:15PM", 0.8),
        ],
        [_candidate("B1", "MW 09:30AM-10:45AM", 0.9)],
    ]
    with patch.dict(os.environ, {"DEV_BYPASS": "1"}, clear=False):
        response = client.post(
            "/schedules/generate_v2", json={"courses": ["CS 146", "CS 151"]}
        )
    assert response.status_code == 200
    schedule_sections = response.json()["schedules"][0]["sections"]
    # Should include the non-conflicting choice A2 with B1.
    names = {s["instructor_name"] for s in schedule_sections}
    assert "A2" in names
    assert "B1" in names


# 9
@patch("schedules.load_svm_artifact")
@patch("schedules.generate_professor_slot_candidates")
@patch("schedules.score_candidates")
def test_generate_v2_dev_bypass_skips_db_save(mock_score, mock_candidates, mock_load):
    mock_load.return_value = {"model": MagicMock()}
    mock_candidates.return_value = [{"slot_label": "MW 09:00AM-10:15AM"}]
    mock_score.return_value = [_candidate("A", "MW 09:00AM-10:15AM", 0.9)]
    with patch.dict(os.environ, {"DEV_BYPASS": "1"}, clear=False):
        response = client.post("/schedules/generate_v2", json={"courses": ["CS 146"]})
    assert response.status_code == 200
    assert response.json()["schedule_id"] is None


# 10
@patch("schedules.get_db_connection")
@patch("schedules.get_current_user_id_cookie", return_value=123)
@patch("schedules.load_svm_artifact")
@patch("schedules.generate_professor_slot_candidates")
@patch("schedules.score_candidates")
def test_generate_v2_non_bypass_persists_schedule(
    mock_score,
    mock_candidates,
    mock_load,
    _mock_user,
    mock_get_db,
):
    conn, cursor = _mock_db()
    cursor.lastrowid = 501
    mock_get_db.return_value = conn
    mock_load.return_value = {"model": MagicMock()}
    mock_candidates.return_value = [{"slot_label": "MW 09:00AM-10:15AM"}]
    mock_score.return_value = [_candidate("A", "MW 09:00AM-10:15AM", 0.9)]
    with patch.dict(os.environ, {"DEV_BYPASS": "0"}, clear=False):
        response = client.post(
            "/schedules/generate_v2",
            json={"courses": ["CS 146"], "term_id": 1, "name": "N"},
        )
    assert response.status_code == 200
    assert response.json()["schedule_id"] == 501


# 11
@patch("schedules.get_db_connection")
@patch("schedules.get_current_user_id_cookie", return_value=123)
@patch("schedules.load_svm_artifact")
@patch("schedules.generate_professor_slot_candidates")
@patch("schedules.score_candidates")
def test_generate_v2_save_failure_returns_500(
    mock_score,
    mock_candidates,
    mock_load,
    _mock_user,
    mock_get_db,
):
    conn, cursor = _mock_db()
    cursor.execute.side_effect = RuntimeError("insert failed")
    mock_get_db.return_value = conn
    mock_load.return_value = {"model": MagicMock()}
    mock_candidates.return_value = [{"slot_label": "MW 09:00AM-10:15AM"}]
    mock_score.return_value = [_candidate("A", "MW 09:00AM-10:15AM", 0.9)]
    with patch.dict(os.environ, {"DEV_BYPASS": "0"}, clear=False):
        response = client.post(
            "/schedules/generate_v2",
            json={"courses": ["CS 146"], "term_id": 1},
        )
    assert response.status_code == 500
    assert "Failed to save schedules" in response.json()["detail"]


# 12
@patch("schedules.top_instructors_last4_semesters")
@patch("schedules.load_svm_artifact")
@patch("schedules.generate_professor_slot_candidates")
@patch("schedules.score_candidates")
def test_generate_v2_professor_frequency_failure_is_non_fatal(
    mock_score,
    mock_candidates,
    mock_load,
    mock_top,
):
    mock_top.side_effect = RuntimeError("stats failure")
    mock_load.return_value = {"model": MagicMock()}
    mock_candidates.return_value = [{"slot_label": "MW 09:00AM-10:15AM"}]
    mock_score.return_value = [_candidate("A", "MW 09:00AM-10:15AM", 0.9)]
    with patch.dict(os.environ, {"DEV_BYPASS": "1"}, clear=False):
        response = client.post("/schedules/generate_v2", json={"courses": ["CS 146"]})
    assert response.status_code == 200
    assert response.json()["professor_frequencies"] == {}


# 13
@patch("schedules.get_current_user_id_cookie", return_value=None)
def test_list_schedules_unauthorized_returns_401(_mock_user):
    response = client.get("/schedules")
    assert response.status_code == 401
    assert response.json()["detail"] == "Access token required"


# 14
@patch("schedules.get_db_connection")
@patch("schedules.get_current_user_id_cookie", return_value=1)
def test_list_schedules_success_parses_sections(_mock_user, mock_get_db):
    conn, cursor = _mock_db()
    mock_get_db.return_value = conn
    cursor.fetchall.return_value = [
        {
            "schedule_id": 1,
            "name": "Test",
            "description": "",
            "term_id": 1,
            "sections": json.dumps([{"course": "CS 146"}]),
            "created_at": "x",
            "updated_at": "y",
        }
    ]
    response = client.get("/schedules")
    assert response.status_code == 200
    assert response.json()[0]["sections"][0]["course"] == "CS 146"


# 15
@patch("schedules.get_db_connection")
@patch("schedules.get_current_user_id_cookie", return_value=1)
def test_list_schedules_db_error_returns_500(_mock_user, mock_get_db):
    conn, cursor = _mock_db()
    mock_get_db.return_value = conn
    cursor.execute.side_effect = RuntimeError("select failed")
    response = client.get("/schedules")
    assert response.status_code == 500
    assert "Failed to retrieve schedules" in response.json()["detail"]


# 16
@patch("schedules.get_current_user_id_cookie", return_value=1)
def test_save_schedule_requires_name(_mock_user):
    response = client.post("/schedules", json={"sections": []})
    assert response.status_code == 400
    assert response.json()["detail"] == "Schedule name is required"


# 17
@patch("schedules.get_current_user_id_cookie", return_value=1)
def test_save_schedule_requires_sections_list(_mock_user):
    response = client.post("/schedules", json={"name": "X", "sections": "not-a-list"})
    assert response.status_code == 400
    assert response.json()["detail"] == "Sections must be a list"


# 18
@patch("schedules.get_db_connection")
@patch("schedules.get_current_user_id_cookie", return_value=1)
def test_save_schedule_success(_mock_user, mock_get_db):
    conn, cursor = _mock_db()
    cursor.lastrowid = 700
    mock_get_db.return_value = conn
    response = client.post(
        "/schedules",
        json={
            "name": "My Schedule",
            "description": "desc",
            "term_id": 1,
            "sections": [{"course": "CS 146"}],
        },
    )
    assert response.status_code == 200
    assert response.json()["schedule_id"] == 700


# 19
@patch("schedules.get_db_connection")
@patch("schedules.get_current_user_id_cookie", return_value=1)
def test_save_schedule_db_error_returns_500(_mock_user, mock_get_db):
    conn, cursor = _mock_db()
    cursor.execute.side_effect = RuntimeError("insert failed")
    mock_get_db.return_value = conn
    response = client.post(
        "/schedules",
        json={"name": "My Schedule", "sections": []},
    )
    assert response.status_code == 500
    assert "Failed to save schedule" in response.json()["detail"]


# 20
def test_split_slot_prediction_and_conflict_helpers():
    from schedules import split_slot_prediction, is_time_conflict

    d, t = split_slot_prediction("MW 09:00AM-10:15AM")
    assert d == "MW"
    assert t == "09:00AM-10:15AM"
    assert is_time_conflict("MW", "09:00AM-10:15AM", "W", "09:30AM-10:45AM") is True
    assert is_time_conflict("MW", "09:00AM-10:15AM", "TR", "09:30AM-10:45AM") is False

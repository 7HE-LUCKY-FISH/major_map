from main import app
import os
import sys
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

# Ensure backend directory is importable.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))


client = TestClient(app)


def make_mock_conn(*, all_rows=None, one_row=None):
    cursor = MagicMock()
    cursor.fetchall.return_value = all_rows if all_rows is not None else []
    cursor.fetchone.return_value = one_row
    conn = MagicMock()
    conn.cursor.return_value = cursor
    return conn, cursor


@patch("course.get_db_connection")
def test_list_courses_returns_data(mock_get_db):
    courses = [{"course_id": 1, "dept_id": "CS", "code": "146", "name": "DSA"}]
    conn, _cursor = make_mock_conn(all_rows=courses)
    mock_get_db.return_value = conn

    response = client.get("/courses/")
    assert response.status_code == 200
    assert response.json() == courses


@patch("course.get_db_connection")
def test_list_courses_returns_empty_list(mock_get_db):
    conn, _cursor = make_mock_conn(all_rows=[])
    mock_get_db.return_value = conn

    response = client.get("/courses/")
    assert response.status_code == 200
    assert response.json() == []


def test_list_sections_stub_returns_empty_list():
    response = client.get("/courses/1/sections")
    assert response.status_code == 200
    assert response.json() == []


@patch("course.get_db_connection")
def test_get_course_found(mock_get_db):
    course_row = {"course_id": 1, "dept_id": "CS", "code": "146", "name": "DSA"}
    conn, _cursor = make_mock_conn(one_row=course_row)
    mock_get_db.return_value = conn

    response = client.get("/courses/1")
    assert response.status_code == 200
    assert response.json() == course_row


@patch("course.get_db_connection")
def test_get_course_not_found_returns_404(mock_get_db):
    conn, _cursor = make_mock_conn(one_row=None)
    mock_get_db.return_value = conn

    response = client.get("/courses/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Course not found"


@patch("course.top_instructors_last4_semesters")
def test_instructors_test_success(mock_top):
    mock_top.return_value = [{"instructor_name": "Prof A", "teach_count": 4}]
    response = client.get("/courses/instructors/test?course_number=CS146")

    assert response.status_code == 200
    data = response.json()
    assert data["course_number"] == "CS146"
    assert len(data["results"]) == 1


@patch("course.top_instructors_last4_semesters")
def test_instructors_test_not_found_returns_404(mock_top):
    mock_top.return_value = []
    response = client.get("/courses/instructors/test?course_number=CS999")

    assert response.status_code == 404
    assert response.json()["detail"] == "No instructors found for this course"


@patch("course.unique_time_slots_last4_semesters")
def test_slots_test_success(mock_slots):
    mock_slots.return_value = [{"days": "TR", "times": "09:00AM-10:15AM"}]
    response = client.get("/courses/slots/test?course_number=CS146")

    assert response.status_code == 200
    data = response.json()
    assert data["course_number"] == "CS146"
    assert len(data["unique_slots"]) == 1


@patch("course.unique_time_slots_last4_semesters")
def test_slots_test_not_found_returns_404(mock_slots):
    mock_slots.return_value = []
    response = client.get("/courses/slots/test?course_number=CS999")

    assert response.status_code == 404
    assert response.json()["detail"] == "No time slots found for this course"


@patch("course.generate_professor_slot_candidates")
def test_candidates_test_success(mock_candidates):
    mock_candidates.return_value = [{"instructor_name": "Prof A", "slot_label": "TR 09:00AM-10:15AM"}]
    response = client.get("/courses/candidates/test?course_number=CS146")

    assert response.status_code == 200
    data = response.json()
    assert data["course_number"] == "CS146"
    assert data["count"] == 1


@patch("course.generate_professor_slot_candidates")
def test_candidates_test_not_found_returns_404(mock_candidates):
    mock_candidates.return_value = []
    response = client.get("/courses/candidates/test?course_number=CS999")

    assert response.status_code == 404
    assert response.json()["detail"] == "No candidates found for this course"

import os
import sys
from unittest.mock import MagicMock, patch

# Ensure backend directory is importable.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from stats import (
    top_instructors_last4_semesters,
    unique_time_slots_last4_semesters,
    generate_professor_slot_candidates,
)


def _mock_conn_with_rows(rows):
    conn = MagicMock()
    cur = MagicMock()
    cur.fetchall.return_value = rows
    conn.cursor.return_value = cur
    return conn, cur


@patch("stats.get_db_connection")
def test_top_instructors_last4_semesters_success(mock_get_db):
    rows = [
        {"instructor_name": "Prof A", "teach_count": 4, "probability": 0.5},
        {"instructor_name": "Prof B", "teach_count": 4, "probability": 0.5},
    ]
    conn, cur = _mock_conn_with_rows(rows)
    mock_get_db.return_value = conn

    result = top_instructors_last4_semesters("CS146", limit=2)

    assert result == rows
    cur.execute.assert_called_once()
    conn.close.assert_called_once()


@patch("stats.get_db_connection")
def test_top_instructors_last4_semesters_empty(mock_get_db):
    conn, _cur = _mock_conn_with_rows([])
    mock_get_db.return_value = conn

    result = top_instructors_last4_semesters("CS999")

    assert result == []


@patch("stats.get_db_connection")
def test_unique_time_slots_last4_semesters_success(mock_get_db):
    rows = [
        {
            "days_text": "TR",
            "start_time": "09:00AM",
            "end_time": "10:15AM",
            "slot_label": "TR 09:00AM-10:15AM",
        }
    ]
    conn, cur = _mock_conn_with_rows(rows)
    mock_get_db.return_value = conn

    result = unique_time_slots_last4_semesters("CS146")

    assert result == rows
    cur.execute.assert_called_once()
    conn.close.assert_called_once()


@patch("stats.get_db_connection")
def test_unique_time_slots_last4_semesters_empty(mock_get_db):
    conn, _cur = _mock_conn_with_rows([])
    mock_get_db.return_value = conn

    result = unique_time_slots_last4_semesters("CS999")

    assert result == []


@patch("stats.top_instructors_last4_semesters")
@patch("stats.unique_time_slots_last4_semesters")
def test_generate_professor_slot_candidates_cross_product(mock_slots, mock_top):
    mock_top.return_value = [
        {"instructor_name": "Prof A", "teach_count": 3, "probability": 0.75},
        {"instructor_name": "Prof B", "teach_count": 1, "probability": 0.25},
    ]
    mock_slots.return_value = [
        {
            "days_text": "TR",
            "start_time": "09:00AM",
            "end_time": "10:15AM",
            "slot_label": "TR 09:00AM-10:15AM",
        },
        {
            "days_text": "MW",
            "start_time": "01:30PM",
            "end_time": "02:45PM",
            "slot_label": "MW 01:30PM-02:45PM",
        },
    ]

    result = generate_professor_slot_candidates("CS146")

    # 2 professors x 2 slots
    assert len(result) == 4
    assert result[0]["course_number"] == "CS146"
    assert "instructor_probability" in result[0]
    assert isinstance(result[0]["instructor_probability"], float)


@patch("stats.top_instructors_last4_semesters")
@patch("stats.unique_time_slots_last4_semesters")
def test_generate_professor_slot_candidates_no_professors(mock_slots, mock_top):
    mock_top.return_value = []
    mock_slots.return_value = [
        {
            "days_text": "TR",
            "start_time": "09:00AM",
            "end_time": "10:15AM",
            "slot_label": "TR 09:00AM-10:15AM",
        }
    ]

    result = generate_professor_slot_candidates("CS146")
    assert result == []


@patch("stats.top_instructors_last4_semesters")
@patch("stats.unique_time_slots_last4_semesters")
def test_generate_professor_slot_candidates_no_slots(mock_slots, mock_top):
    mock_top.return_value = [
        {"instructor_name": "Prof A", "teach_count": 3, "probability": 0.75}
    ]
    mock_slots.return_value = []

    result = generate_professor_slot_candidates("CS146")
    assert result == []


@patch("stats.top_instructors_last4_semesters")
@patch("stats.unique_time_slots_last4_semesters")
def test_generate_professor_slot_candidates_probability_cast_to_float(
    mock_slots,
    mock_top,
):
    mock_top.return_value = [
        {"instructor_name": "Prof A", "teach_count": 3, "probability": "0.75"}
    ]
    mock_slots.return_value = [
        {
            "days_text": "TR",
            "start_time": "09:00AM",
            "end_time": "10:15AM",
            "slot_label": "TR 09:00AM-10:15AM",
        }
    ]

    result = generate_professor_slot_candidates("CS146")
    assert len(result) == 1
    assert isinstance(result[0]["instructor_probability"], float)
    assert result[0]["instructor_probability"] == 0.75

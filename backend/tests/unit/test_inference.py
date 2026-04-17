import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd

# Ensure backend directory is importable.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from ml import inference


def _sample_lookups():
    return {
        "instr_prior_count": pd.DataFrame(
            [{"Instructor": "Prof A", "SemesterIndex": 1, "instr_prior_count": 2}]
        ),
        "course_prior_count": pd.DataFrame(
            [{"CourseCode": "CS 146", "SemesterIndex": 1, "course_prior_count": 3}]
        ),
        "slot_prior_count": pd.DataFrame(
            [{"Slot": "TR_540_615", "SemesterIndex": 1, "slot_prior_count": 1}]
        ),
        "course_type_prior_count": pd.DataFrame(
            [
                {
                    "CourseCode": "CS 146",
                    "Type": "LEC",
                    "SemesterIndex": 1,
                    "course_type_prior_count": 1,
                }
            ]
        ),
        "instr_dept_prior_count": pd.DataFrame(
            [
                {
                    "Instructor": "Prof A",
                    "Dept": "CS",
                    "SemesterIndex": 1,
                    "instr_dept_prior_count": 1,
                }
            ]
        ),
        "instr_course_prior_count": pd.DataFrame(
            [
                {
                    "Instructor": "Prof A",
                    "CourseCode": "CS 146",
                    "SemesterIndex": 1,
                    "instr_course_prior_count": 1,
                }
            ]
        ),
        "course_slot_prior_count": pd.DataFrame(
            [
                {
                    "CourseCode": "CS 146",
                    "Slot": "TR_540_615",
                    "SemesterIndex": 1,
                    "course_slot_prior_count": 1,
                }
            ]
        ),
        "course_type_slot_prior_count": pd.DataFrame(
            [
                {
                    "CourseCode": "CS 146",
                    "Type": "LEC",
                    "Slot": "TR_540_615",
                    "SemesterIndex": 1,
                    "course_type_slot_prior_count": 1,
                }
            ]
        ),
        "combo_prior_count": pd.DataFrame(
            [
                {
                    "CourseCode": "CS 146",
                    "Instructor": "Prof A",
                    "Slot": "TR_540_615",
                    "Type": "LEC",
                    "SemesterIndex": 1,
                    "combo_prior_count": 1,
                }
            ]
        ),
        "instr_last_term": pd.DataFrame(
            [{"Instructor": "Prof A", "SemesterIndex": 1, "instr_last_term": 1}]
        ),
        "course_last_term": pd.DataFrame(
            [{"CourseCode": "CS 146", "SemesterIndex": 1, "course_last_term": 1}]
        ),
        "instr_course_last_term": pd.DataFrame(
            [
                {
                    "Instructor": "Prof A",
                    "CourseCode": "CS 146",
                    "SemesterIndex": 1,
                    "instr_course_last_term": 1,
                }
            ]
        ),
        "combo_last_term": pd.DataFrame(
            [
                {
                    "CourseCode": "CS 146",
                    "Instructor": "Prof A",
                    "Slot": "TR_540_615",
                    "Type": "LEC",
                    "SemesterIndex": 1,
                    "combo_last_term": 1,
                }
            ]
        ),
    }


def _sample_artifact():
    model = MagicMock()
    model.predict_proba.return_value = np.array([[0.2, 0.8], [0.7, 0.3]])
    return {
        "lookups": _sample_lookups(),
        "max_train_term": 2,
        "cat_cols": ["CourseCode", "Instructor", "Slot", "Type"],
        "num_cols": [
            "instr_prior_count_log1p",
            "course_prior_count_log1p",
            "slot_prior_count_log1p",
            "course_type_prior_count_log1p",
            "instr_dept_prior_count_log1p",
            "instr_course_prior_count_log1p",
            "course_slot_prior_count_log1p",
            "course_type_slot_prior_count_log1p",
            "combo_prior_count_log1p",
            "instr_terms_since",
            "course_terms_since",
            "instr_course_terms_since",
            "combo_terms_since",
        ],
        "model": model,
    }


def _candidate():
    return {
        "course_number": "CS 146",
        "instructor_name": "Prof A",
        "days_text": "TR",
        "start_time": "09:00AM",
        "end_time": "10:15AM",
        "type": "LEC",
    }


@patch("ml.inference.joblib.load")
def test_load_artifact_success(mock_load):
    expected = {"model": "ok"}
    mock_load.return_value = expected
    with patch("ml.inference.ART_DIR", Path("fake_art_dir")):
        with patch("pathlib.Path.exists", return_value=True):
            result = inference.load_artifact("x.joblib")
    assert result == expected


def test_load_artifact_missing_file_raises():
    with patch("ml.inference.ART_DIR", Path("fake_art_dir")):
        with patch("pathlib.Path.exists", return_value=False):
            try:
                inference.load_artifact("missing.joblib")
                assert False, "Expected FileNotFoundError"
            except FileNotFoundError as exc:
                assert "Missing model artifact" in str(exc)


@patch("ml.inference.load_artifact")
def test_load_svm_artifact_uses_cache(mock_load):
    inference._SVM_CACHE = None
    mock_load.return_value = {"model": "m"}
    first = inference.load_svm_artifact()
    second = inference.load_svm_artifact()
    assert first == second
    assert mock_load.call_count == 1
    inference._SVM_CACHE = None


def test_parse_time_to_minutes_valid_and_invalid():
    assert inference._parse_time_to_minutes("09:00AM") == 540
    assert inference._parse_time_to_minutes("09:00 AM") == 540
    assert inference._parse_time_to_minutes("TBA") == -1
    assert inference._parse_time_to_minutes("bad-time") == -1


def test_build_svm_row_with_regular_time_slot():
    art = _sample_artifact()
    row = inference.build_svm_row(_candidate(), art)
    assert row["CourseCode"] == "CS 146"
    assert row["Instructor"] == "Prof A"
    assert row["Slot"].startswith("TR_")
    assert "instr_prior_count_log1p" in row


def test_build_svm_row_with_tba_slot():
    art = _sample_artifact()
    candidate = _candidate()
    candidate["start_time"] = "TBA"
    candidate["end_time"] = "TBA"
    row = inference.build_svm_row(candidate, art)
    assert row["Slot"].endswith("_TBA")


def test_score_candidates_empty_input_returns_empty_list():
    art = _sample_artifact()
    assert inference.score_candidates([], art) == []


def test_score_candidates_adds_probabilities():
    art = _sample_artifact()
    candidates = [_candidate(), {**_candidate(), "instructor_name": "Prof B"}]
    result = inference.score_candidates(candidates, art)
    assert len(result) == 2
    assert "prob_scheduled" in result[0]
    assert result[0]["prob_scheduled"] == 0.8
    assert result[1]["prob_scheduled"] == 0.3

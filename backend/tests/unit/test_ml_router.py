import os
import sys
from unittest.mock import patch

import pandas as pd

# Ensure backend directory is importable.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from ml import ml_router
from ml.features import SemesterIndexConfig
from ml.ml_router import (
    CourseContext,
    ScheduledCandidateContext,
    _lookup_count,
    _lookup_last_term,
    build_features_AB,
    build_features_svm,
)


def _sample_lookups():
    return {
        "instr_prior_count": pd.DataFrame(
            [
                {"Instructor": "A", "SemesterIndex": 1, "instr_prior_count": 2},
                {"Instructor": "A", "SemesterIndex": 3, "instr_prior_count": 4},
            ]
        ),
        "course_prior_count": pd.DataFrame(
            [
                {"CourseCode": "146", "SemesterIndex": 2, "course_prior_count": 3},
            ]
        ),
        "slot_prior_count": pd.DataFrame(
            [
                {"Slot": "TR_540_615", "SemesterIndex": 2, "slot_prior_count": 1},
            ]
        ),
        "course_type_prior_count": pd.DataFrame(
            [
                {
                    "CourseCode": "146",
                    "Type": "LEC",
                    "SemesterIndex": 2,
                    "course_type_prior_count": 5,
                }
            ]
        ),
        "instr_dept_prior_count": pd.DataFrame(
            [
                {
                    "Instructor": "A",
                    "Dept": "CS",
                    "SemesterIndex": 2,
                    "instr_dept_prior_count": 2,
                }
            ]
        ),
        "instr_course_prior_count": pd.DataFrame(
            [
                {
                    "Instructor": "A",
                    "CourseCode": "146",
                    "SemesterIndex": 2,
                    "instr_course_prior_count": 2,
                }
            ]
        ),
        "course_slot_prior_count": pd.DataFrame(
            [
                {
                    "CourseCode": "146",
                    "Slot": "TR_540_615",
                    "SemesterIndex": 2,
                    "course_slot_prior_count": 1,
                }
            ]
        ),
        "course_type_slot_prior_count": pd.DataFrame(
            [
                {
                    "CourseCode": "146",
                    "Type": "LEC",
                    "Slot": "TR_540_615",
                    "SemesterIndex": 2,
                    "course_type_slot_prior_count": 1,
                }
            ]
        ),
        "combo_prior_count": pd.DataFrame(
            [
                {
                    "CourseCode": "146",
                    "Instructor": "A",
                    "Slot": "TR_540_615",
                    "Type": "LEC",
                    "SemesterIndex": 2,
                    "combo_prior_count": 1,
                }
            ]
        ),
        "instr_last_term": pd.DataFrame(
            [{"Instructor": "A", "SemesterIndex": 3, "instr_last_term": 3}]
        ),
        "course_last_term": pd.DataFrame(
            [{"CourseCode": "146", "SemesterIndex": 3, "course_last_term": 3}]
        ),
        "instr_course_last_term": pd.DataFrame(
            [
                {
                    "Instructor": "A",
                    "CourseCode": "146",
                    "SemesterIndex": 3,
                    "instr_course_last_term": 3,
                }
            ]
        ),
        "combo_last_term": pd.DataFrame(
            [
                {
                    "CourseCode": "146",
                    "Instructor": "A",
                    "Slot": "TR_540_615",
                    "Type": "LEC",
                    "SemesterIndex": 3,
                    "combo_last_term": 3,
                }
            ]
        ),
    }


def test_lookup_count_missing_table_returns_zero():
    lookups = {}
    value = _lookup_count(lookups, "missing_col", {"Instructor": "A"}, 10)
    assert value == 0.0


def test_lookup_count_no_matching_rows_returns_zero():
    lookups = _sample_lookups()
    value = _lookup_count(lookups, "instr_prior_count", {"Instructor": "Z"}, 10)
    assert value == 0.0


def test_lookup_count_uses_latest_row_before_target_term():
    lookups = _sample_lookups()
    value = _lookup_count(lookups, "instr_prior_count", {"Instructor": "A"}, 10)
    assert value == 4.0


def test_lookup_last_term_missing_table_returns_negative_one():
    lookups = {}
    value = _lookup_last_term(lookups, "missing_col", {"Instructor": "A"}, 10)
    assert value == -1


def test_lookup_last_term_returns_latest_term():
    lookups = _sample_lookups()
    value = _lookup_last_term(lookups, "instr_last_term", {"Instructor": "A"}, 10)
    assert value == 3


def test_build_features_ab_generates_expected_keys():
    payload = CourseContext(
        section="CS 146 (Section 01)",
        mode="In Person",
        unit=3,
        type="LEC",
        days="TR",
        times="09:00AM-10:15AM",
        satifies="GE: B2",
        location="ENG 305",
        year=2026,
        semester="Fall",
    )
    sem_cfg = SemesterIndexConfig(base=2000)
    row = build_features_AB(payload, sem_cfg)

    assert row["Dept"] == "CS"
    assert row["CourseCode"] == "CS 146"
    assert row["HasGE"] in (0, 1)
    assert "DurationMinutes" in row
    assert "SemesterIndex" in row


@patch("ml.ml_router._get_svm")
def test_build_features_svm_happy_path(mock_get_svm):
    cat_cols = ["CourseCode", "Instructor", "Slot", "Type"]
    num_cols = [
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
    ]
    mock_get_svm.return_value = {
        "lookups": _sample_lookups(),
        "max_train_term": 4,
        "cat_cols": cat_cols,
        "num_cols": num_cols,
    }

    payload = ScheduledCandidateContext(
        section="CS 146",
        instructor="A",
        days="TR",
        times="09:00AM-10:15AM",
        type="LEC",
        year=2026,
        semester="Fall",
    )
    df = build_features_svm(payload)
    assert list(df.columns) == cat_cols + num_cols
    assert df.iloc[0]["CourseCode"] == "CS 146"
    assert df.iloc[0]["Instructor"] == "A"
    assert df.iloc[0]["Type"] == "LEC"


@patch("ml.ml_router._get_svm")
def test_build_features_svm_handles_missing_times(mock_get_svm):
    cat_cols = ["CourseCode", "Instructor", "Slot", "Type"]
    num_cols = [
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
    ]
    mock_get_svm.return_value = {
        "lookups": _sample_lookups(),
        "max_train_term": 4,
        "cat_cols": cat_cols,
        "num_cols": num_cols,
    }

    payload = ScheduledCandidateContext(
        section="CS 146",
        instructor="A",
        days=None,
        times=None,
        type="LEC",
        year=2026,
        semester="Fall",
    )
    df = build_features_svm(payload)
    assert "Slot" in df.columns
    assert isinstance(df.iloc[0]["Slot"], str)


@patch("ml.ml_router.load_artifact")
def test_get_svm_caches_artifact(mock_load_artifact):
    mock_load_artifact.return_value = {"model": object()}
    ml_router._SVM = None

    first = ml_router._get_svm()
    second = ml_router._get_svm()

    assert first == second
    assert mock_load_artifact.call_count == 1

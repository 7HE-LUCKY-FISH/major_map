from __future__ import annotations
import math
import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

from ml.features import (
    compute_semester_index,
    has_ge,
    parse_time_range,
    section_to_course_code,
    SemesterIndexConfig,
    get_building,
)
from ml.inference import load_artifact


router = APIRouter(prefix="/ml", tags=["ml"])


# Artifact filenames used when loading model artifacts.  The original
# training script generates three files:
# ``scenario_A_instructor.joblib``, ``scenario_B_slot.joblib`` and
# ``scenario_C_course.joblib``.  To experiment with the new
# logistic-regression models built by ``train2.py`` simply change the
# constants below (e.g. ``ARTIFACT_A = "train2_logreg.joblib"``).
# ARTIFACT_A   = "scenario_A_instructor.joblib"
# ARTIFACT_B   = "scenario_B_slot.joblib"
# ARTIFACT_C   = "scenario_C_course.joblib"
ARTIFACT_SVM = "train2_anthony_svm.joblib"


# Load artifacts once at import time; the operation is fast and the
# objects are immutable, so this avoids repeated I/O on every request.
# A = load_artifact(ARTIFACT_A)
# B = load_artifact(ARTIFACT_B)
# C = load_artifact(ARTIFACT_C)

# SVM artifact is loaded lazily to avoid crashing the router if training
# has not been run yet.  The first request to /predict/scheduled will load it.
_SVM: dict | None = None


def _get_svm() -> dict:
    """Return the cached SVM artifact, loading it on first call."""
    global _SVM
    if _SVM is None:
        _SVM = load_artifact(ARTIFACT_SVM)
    return _SVM


# simple Pydantic models used for request validation; they will be
# extended as the API evolves.
class CourseContext(BaseModel):
    section: str = Field(..., examples=["CS 146 (Section 01)"])
    mode: str = Field(..., examples=["In Person"])
    unit: int = Field(..., examples=[3])
    type: str = Field(..., examples=["LEC"])
    days: Optional[str] = Field(None, examples=["TR"])
    times: Optional[str] = Field(None, examples=["09:00AM-10:15AM"])
    satifies: Optional[str] = Field("Unknown", examples=["GE: B2", "MajorOnly"])
    location: Optional[str] = Field(
        "Unknown",
        examples=["ENG305", "ONLINE", "Unknown"],
    )
    year: int = Field(..., examples=[2025])
    semester: str = Field(..., examples=["Spring", "Fall"])


class ScheduledCandidateContext(BaseModel):
    """A candidate (course, instructor, slot, type) for the upcoming term."""

    section:   str = Field(..., examples=["CS 146"])
    instructor: str = Field(..., examples=["Richard Low"])
    days:      Optional[str] = Field(None, examples=["TR"])
    times:     Optional[str] = Field(None, examples=["09:00AM-10:15AM"])
    type:      str = Field(..., examples=["LEC"])
    year:      int = Field(..., examples=[2026])
    semester:  str = Field(..., examples=["Fall"])


class InstructorContext(BaseModel):
    instructor: str = Field(..., examples=["Richard Low"])
    mode: str = Field(..., examples=["In Person"])
    type: str = Field(..., examples=["LEC"])
    semester: str = Field(..., examples=["Fall"])
    building: str = Field(..., examples=["ENG", "ONLINE", "SCI"])
    year: int = Field(..., examples=[2024])

# ---------------------------------------------------------------------------
# SVM feature hydration
# ---------------------------------------------------------------------------


def _lookup_count(lookups: dict, out_col: str, group_vals: dict, target_term: int) -> float:
    """Return the cumulative prior count for a group up to (but not including) target_term.

    Looks up the latest row in the lookup table where term < target_term.
    Falls back to 0.0 when the group has never been seen before.
    """
    tbl: pd.DataFrame = lookups.get(out_col)
    if tbl is None:
        return 0.0
    mask = tbl["SemesterIndex"] < target_term
    for col, val in group_vals.items():
        mask = mask & (tbl[col] == val)
    rows = tbl[mask]
    if rows.empty:
        return 0.0
    return float(rows.sort_values("SemesterIndex").iloc[-1][out_col])


def _lookup_last_term(lookups: dict, out_col: str, group_vals: dict, target_term: int) -> int:
    """Return the most recent term the group was seen before target_term, or -1."""
    tbl: pd.DataFrame = lookups.get(out_col)
    if tbl is None:
        return -1
    mask = tbl["SemesterIndex"] < target_term
    for col, val in group_vals.items():
        mask = mask & (tbl[col] == val)
    rows = tbl[mask]
    if rows.empty:
        return -1
    return int(rows.sort_values("SemesterIndex").iloc[-1][out_col])


def build_features_svm(p: ScheduledCandidateContext) -> pd.DataFrame:
    """Build the 17-column feature row (4 cat + 13 num) for the SVM model.

    Categorical columns are passed through as strings (the pipeline's
    OneHotEncoder handles encoding).  Numerical history columns are hydrated
    from the precomputed lookup tables baked into the artifact.
    """
    art = _get_svm()
    lookups: dict = art["lookups"]
    max_train_term: int = art["max_train_term"]

    # --- Derive base fields ---
    dept, course_code = section_to_course_code(p.section)
    safe_times = p.times if p.times else "12:00AM-12:00AM"
    start_m, _end_m, _dur_m = parse_time_range(safe_times)
    safe_days = p.days if p.days else ""

    # Slot: "DAYS_startMinutes_endMinutes" (e.g. "TR_540_690") — must match
    # the make_slot format used in train_ant.py during training.
    if start_m == -1 or _end_m == -1:
        slot = f"{safe_days}_TBA"
    else:
        slot = f"{safe_days}_{start_m}_{_end_m}"

    # SemesterIndex is unknown at inference time (future term) so we use
    # max_train_term + 1 as the target term.  This means "strictly after all
    # training data", which is the correct production scenario.
    target_term = max_train_term + 1

    # --- Hydrate 9 count features ---
    counts = {
        "instr_prior_count":            _lookup_count(lookups, "instr_prior_count",            {"Instructor": p.instructor},                                     target_term),
        "course_prior_count":           _lookup_count(lookups, "course_prior_count",           {"CourseCode": course_code},                                      target_term),
        "slot_prior_count":             _lookup_count(lookups, "slot_prior_count",             {"Slot": slot},                                                   target_term),
        "course_type_prior_count":      _lookup_count(lookups, "course_type_prior_count",      {"CourseCode": course_code, "Type": p.type},                      target_term),
        "instr_dept_prior_count":       _lookup_count(lookups, "instr_dept_prior_count",       {"Instructor": p.instructor, "Dept": dept},                       target_term),
        "instr_course_prior_count":     _lookup_count(lookups, "instr_course_prior_count",     {"Instructor": p.instructor, "CourseCode": course_code},           target_term),
        "course_slot_prior_count":      _lookup_count(lookups, "course_slot_prior_count",      {"CourseCode": course_code, "Slot": slot},                         target_term),
        "course_type_slot_prior_count": _lookup_count(lookups, "course_type_slot_prior_count", {"CourseCode": course_code, "Type": p.type, "Slot": slot},         target_term),
        "combo_prior_count":            _lookup_count(lookups, "combo_prior_count",            {"CourseCode": course_code, "Instructor": p.instructor, "Slot": slot, "Type": p.type}, target_term),
    }

    # --- Hydrate 4 recency features ---
    recency_pairs = [
        ("instr_last_term",       {"Instructor": p.instructor}),
        ("course_last_term",      {"CourseCode": course_code}),
        ("instr_course_last_term", {"Instructor": p.instructor, "CourseCode": course_code}),
        ("combo_last_term",       {"CourseCode": course_code, "Instructor": p.instructor, "Slot": slot, "Type": p.type}),
    ]
    recency: dict = {}
    for out_col, grp in recency_pairs:
        last = _lookup_last_term(lookups, out_col, grp, target_term)
        gap_col = out_col.replace("last_term", "terms_since")
        recency[gap_col] = (target_term + 1) if last == -1 else (target_term - last)

    row = {
        # categorical
        "CourseCode":  course_code,
        "Instructor":  p.instructor,
        "Slot":        slot,
        "Type":        p.type,
        # numerical (log1p-transformed counts)
        "instr_prior_count_log1p":            math.log1p(counts["instr_prior_count"]),
        "course_prior_count_log1p":           math.log1p(counts["course_prior_count"]),
        "slot_prior_count_log1p":             math.log1p(counts["slot_prior_count"]),
        "course_type_prior_count_log1p":      math.log1p(counts["course_type_prior_count"]),
        "instr_dept_prior_count_log1p":       math.log1p(counts["instr_dept_prior_count"]),
        "instr_course_prior_count_log1p":     math.log1p(counts["instr_course_prior_count"]),
        "course_slot_prior_count_log1p":      math.log1p(counts["course_slot_prior_count"]),
        "course_type_slot_prior_count_log1p": math.log1p(counts["course_type_slot_prior_count"]),
        "combo_prior_count_log1p":            math.log1p(counts["combo_prior_count"]),
        # recency
        **recency,
    }
    features = art["cat_cols"] + art["num_cols"]
    return pd.DataFrame([row])[features]


def build_features_AB(p: CourseContext, sem_cfg: SemesterIndexConfig) -> dict:
    dept, course_code = section_to_course_code(p.section)
    safe_times = p.times if p.times else "12:00AM-12:00AM"
    start_m, end_m, dur_m = parse_time_range(safe_times)
    safe_location = p.location if p.location else "Unknown"
    building = get_building(safe_location)
    safe_satisfies = p.satifies if p.satifies else "Unknown"
    return {
        "Dept": dept,
        "CourseCode": course_code,
        "Mode": p.mode,
        "Type": p.type,
        "Semester": p.semester,
        "Building": building,
        "Unit": p.unit,
        "Year": p.year,
        "SemesterIndex": compute_semester_index(p.year, p.semester, sem_cfg),
        "DurationMinutes": dur_m,
        "HasGE": has_ge(safe_satisfies),
    }

# @router.post("/predict/instructor")
# def predict_instructor(
#     payload: CourseContext, k: int = 3
# ) -> dict:
#     """Return the top-*k* instructor predictions for a course context."""

#     row = build_features_AB(payload, A["sem_cfg"])
#     X = pd.DataFrame([row])[A["cat"] + A["num"]]
#     preds = topk(A["pipeline"], X, k=k)
#     return {"best": preds[0], "topk": preds}


# @router.post("/predict/slot")
# def predict_slot(
#     payload: CourseContext, k: int = 3
# ) -> dict:
#     """Return the top-*k* slot predictions for a course context."""

#     row = build_features_AB(payload, B["sem_cfg"])
#     X = pd.DataFrame([row])[B["cat"] + B["num"]]
#     preds = topk(B["pipeline"], X, k=k)
#     return {"best": preds[0], "topk": preds}


# @router.post("/predict/scheduled")
# def predict_scheduled(payload: ScheduledCandidateContext) -> dict:
#     """Score a candidate (course, instructor, slot, type) for the upcoming term.

#     Returns the probability that this combination would be scheduled,
#     based on historical co-occurrence patterns learned by the Linear SVM.

#     Input fields
#     ------------
#     section    : course section string, e.g. "CS 146"
#     instructor : instructor name, e.g. "Richard Low"
#     days       : day pattern, e.g. "TR", "MWF" (optional)
#     times      : time range string, e.g. "09:00AM-10:15AM" (optional)
#     type       : section type, e.g. "LEC" or "LAB"
#     year       : upcoming year, e.g. 2026
#     semester   : "Spring" or "Fall"
#     """
#     try:
#         X = build_features_svm(payload)
#     except FileNotFoundError as exc:
#         raise HTTPException(status_code=503, detail=str(exc))
#     art = _get_svm()
#     model = art["model"]
#     proba = float(model.predict_proba(X)[0, 1])
#     return {
#         "course_code": X["CourseCode"].iloc[0],
#         "instructor":  payload.instructor,
#         "slot":        X["Slot"].iloc[0],
#         "type":        payload.type,
#         "prob_scheduled": round(proba, 4),
#     }


# @router.post("/predict/course")
# def predict_course(payload: InstructorContext, k: int = 3) -> dict:
#     """Return the top-*k* course predictions for an instructor context.
#     The input dictionary matches the features used during training of
#     scenario C artifacts.
#     """

#     # Scenario C inputs match training features.
#     sem_index = compute_semester_index(
#         payload.year, payload.semester, C["sem_cfg"]
#     )
#     row = {
#         "Instructor": payload.instructor,
#         "Mode": payload.mode,
#         "Type": payload.type,
#         "Semester": payload.semester,
#         "Building": payload.building,
#         "Year": payload.year,
#         "SemesterIndex": sem_index,
#     }
#     X = pd.DataFrame([row])[C["cat"] + C["num"]]
#     preds = topk(C["pipeline"], X, k=k)
#     return {"best": preds[0], "topk": preds}

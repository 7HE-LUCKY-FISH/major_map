from __future__ import annotations

import pandas as pd
from fastapi import APIRouter
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
from ml.inference import load_artifact, topk


router = APIRouter(prefix="/ml", tags=["ml"])


# Artifact filenames used when loading model artifacts.  The original
# training script generates three files:
# ``scenario_A_instructor.joblib``, ``scenario_B_slot.joblib`` and
# ``scenario_C_course.joblib``.  To experiment with the new
# logistic-regression models built by ``train2.py`` simply change the
# constants below (e.g. ``ARTIFACT_A = "train2_logreg.joblib"``).
ARTIFACT_A = "scenario_A_instructor.joblib"
ARTIFACT_B = "scenario_B_slot.joblib"
ARTIFACT_C = "scenario_C_course.joblib"


# Load artifacts once at import time; the operation is fast and the
# objects are immutable, so this avoids repeated I/O on every request.
A = load_artifact(ARTIFACT_A)
B = load_artifact(ARTIFACT_B)
C = load_artifact(ARTIFACT_C)


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


class InstructorContext(BaseModel):
    instructor: str = Field(..., examples=["Richard Low"])
    mode: str = Field(..., examples=["In Person"])
    type: str = Field(..., examples=["LEC"])
    semester: str = Field(..., examples=["Fall"])
    building: str = Field(..., examples=["ENG", "ONLINE", "SCI"])
    year: int = Field(..., examples=[2024])

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

@router.post("/predict/instructor")
def predict_instructor(
    payload: CourseContext, k: int = 3
) -> dict:
    """Return the top-*k* instructor predictions for a course context."""

    row = build_features_AB(payload, A["sem_cfg"])
    X = pd.DataFrame([row])[A["cat"] + A["num"]]
    preds = topk(A["pipeline"], X, k=k)
    return {"best": preds[0], "topk": preds}


@router.post("/predict/slot")
def predict_slot(
    payload: CourseContext, k: int = 3
) -> dict:
    """Return the top-*k* slot predictions for a course context."""

    row = build_features_AB(payload, B["sem_cfg"])
    X = pd.DataFrame([row])[B["cat"] + B["num"]]
    preds = topk(B["pipeline"], X, k=k)
    return {"best": preds[0], "topk": preds}


@router.post("/predict/course")
def predict_course(payload: InstructorContext, k: int = 3) -> dict:
    """Return the top-*k* course predictions for an instructor context.
    The input dictionary matches the features used during training of
    scenario C artifacts.
    """

    # Scenario C inputs match training features.
    sem_index = compute_semester_index(
        payload.year, payload.semester, C["sem_cfg"]
    )
    row = {
        "Instructor": payload.instructor,
        "Mode": payload.mode,
        "Type": payload.type,
        "Semester": payload.semester,
        "Building": payload.building,
        "Year": payload.year,
        "SemesterIndex": sem_index,
    }
    X = pd.DataFrame([row])[C["cat"] + C["num"]]
    preds = topk(C["pipeline"], X, k=k)
    return {"best": preds[0], "topk": preds}

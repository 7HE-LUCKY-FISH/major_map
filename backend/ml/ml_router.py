from __future__ import annotations
from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional
import pandas as pd


from ml.features import (
    compute_semester_index, SemesterIndexConfig,
    parse_time_range, get_building, section_to_course_code, make_slot, has_ge
)
from ml.inference import load_artifact, topk

router = APIRouter(prefix="/ml", tags=["ml"])

# Artifact filenames (change these to test different trained artifacts)
# By default the original training script writes: scenario_A_instructor.joblib,
# scenario_B_slot.joblib, scenario_C_course.joblib
# If you want to test the new logistic-regression artifact produced by
# `train2.py`, set these constants to "train2_logreg.joblib" (or other file).
# Example to test train2 for A/B/C: set ARTIFACT_A = "train2_logreg.joblib"
ARTIFACT_A = "scenario_A_instructor.joblib"
ARTIFACT_B = "scenario_B_slot.joblib"
ARTIFACT_C = "scenario_C_course.joblib"

# Load once at import (fast + stable)
A = load_artifact(ARTIFACT_A)
B = load_artifact(ARTIFACT_B)
C = load_artifact(ARTIFACT_C)


#kinda just hard coded tests
#This base model will need to change later 

class CourseContext(BaseModel):
    section: str = Field(..., examples=["CS 146 (Section 01)"])
    mode: str = Field(..., examples=["In Person"])
    unit: int = Field(..., examples=[3])
    type: str = Field(..., examples=["LEC"])
    days: Optional[str] = Field(None, examples=["TR"])
    times: Optional[str] = Field(None, examples=["09:00AM-10:15AM"])
    satifies: Optional[str] = Field("Unknown", examples=["GE: B2", "MajorOnly"])
    location: Optional[str] = Field("Unknown", examples=["ENG305", "ONLINE", "Unknown"])
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
def predict_instructor(payload: CourseContext, k: int = 3):
    row = build_features_AB(payload, A["sem_cfg"])
    X = pd.DataFrame([row])[A["cat"] + A["num"]]
    preds = topk(A["pipeline"], X, k=k)
    return {"best": preds[0], "topk": preds}

@router.post("/predict/slot")
def predict_slot(payload: CourseContext, k: int = 3):
    row = build_features_AB(payload, B["sem_cfg"])
    X = pd.DataFrame([row])[B["cat"] + B["num"]]
    preds = topk(B["pipeline"], X, k=k)
    return {"best": preds[0], "topk": preds}

@router.post("/predict/course")
def predict_course(payload: InstructorContext, k: int = 3):
    # Scenario C inputs match training features
    sem_index = compute_semester_index(payload.year, payload.semester, C["sem_cfg"])
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

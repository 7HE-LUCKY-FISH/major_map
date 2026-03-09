from __future__ import annotations
from datetime import datetime as _dt
from pathlib import Path
import math
import joblib
import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
ART_DIR = REPO_ROOT / "backend" / "ml_artifacts"


def load_artifact(filename: str):
    path = ART_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Missing model artifact: {path}. Run training first.")
    return joblib.load(path)


def topk(pipeline, X: pd.DataFrame, k: int = 3):
    proba = pipeline.predict_proba(X)
    classes = pipeline.classes_
    idx = np.argsort(proba, axis=1)[:, -k:][:, ::-1]
    row = []
    for j in idx[0]:
        row.append({"label": str(classes[j]), "prob": float(proba[0, j])})
    return row


# ---------------------------------------------------------------------------
# SVM artifact cache
# ---------------------------------------------------------------------------

_SVM_CACHE: dict | None = None


def load_svm_artifact() -> dict:
    """Load and cache the SVM artifact.  Safe to call from multiple modules."""
    global _SVM_CACHE
    if _SVM_CACHE is None:
        _SVM_CACHE = load_artifact("train2_anthony_svm.joblib")
    return _SVM_CACHE


# ---------------------------------------------------------------------------
# Lookup helpers (shared by build_svm_row and ml_router)
# ---------------------------------------------------------------------------

def _parse_time_to_minutes(t: str) -> int:
    """Parse a time string like '09:00AM' into minutes since midnight.
    Returns -1 on TBA or parse failure.
    """
    t = str(t).strip()
    if t in ("TBA", "TBD", ""):
        return -1
    for fmt in ("%I:%M%p", "%I:%M %p"):
        try:
            dt = _dt.strptime(t, fmt)
            return dt.hour * 60 + dt.minute
        except ValueError:
            continue
    return -1


def _lookup_count(
    lookups: dict, out_col: str, group_vals: dict, target_term: int
) -> float:
    """Cumulative prior count for a group strictly before target_term."""
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


def _lookup_last_term(
    lookups: dict, out_col: str, group_vals: dict, target_term: int
) -> int:
    """Return the most recent term this group was seen before target_term.
    Falls back to target_term + 1 (→ terms_since = -1 after subtraction,
    clipped to 0 downstream) when the combo is unknown or data is missing.
    """
    default = target_term + 1
    if out_col not in lookups:
        return default

    df = lookups[out_col]

    # Build filter mask for each group key
    mask = pd.Series([True] * len(df), index=df.index)
    for col, val in group_vals.items():
        if col not in df.columns:
            return default
        mask &= df[col] == val

    rows = df[mask & (df["SemesterIndex"] < target_term)]

    if rows.empty:
        return default

    val = rows.sort_values("SemesterIndex").iloc[-1][out_col]

    # Guard against NaN stored in the lookup table
    if pd.isna(val):
        return default

    return int(val)


# ---------------------------------------------------------------------------
# Feature builder for one candidate dict
# ---------------------------------------------------------------------------

def build_svm_row(candidate: dict, art: dict) -> dict:
    """Convert one candidate dict (from generate_professor_slot_candidates) into
    the 17-column feature row expected by the SVM pipeline.

    Candidate keys used:
      course_number   : e.g. 'CS 146'
      instructor_name : e.g. 'Richard Low'
      days_text       : e.g. 'TR'
      start_time      : e.g. '09:00AM' or 'TBA'
      end_time        : e.g. '10:15AM' or 'TBA'
      type            : optional, defaults to 'LEC'

    Slot format matches training: '{days}_{start_m}_{end_m}' or '{days}_TBA'.
    """
    lookups        = art["lookups"]
    max_train_term = art["max_train_term"]
    # All production scoring uses max_train_term + 1 as the prediction target term.
    target_term    = max_train_term + 1

    course_code    = str(candidate.get("course_number", "")).strip()
    dept           = course_code.split()[0] if course_code else "Unknown"
    instructor     = str(candidate.get("instructor_name", "")).strip()
    days           = str(candidate.get("days_text", "")).strip()
    start_m        = _parse_time_to_minutes(candidate.get("start_time", "TBA"))
    end_m          = _parse_time_to_minutes(candidate.get("end_time",   "TBA"))
    section_type   = str(candidate.get("type", "LEC")).strip()

    # Slot must match the training format used in train_ant.py's make_slot:
    # '{days}_{start}_{end}' or '{days}_TBA'
    if start_m == -1 or end_m == -1:
        slot = f"{days}_TBA"
    else:
        slot = f"{days}_{start_m}_{end_m}"

    counts = {
        "instr_prior_count":            _lookup_count(lookups, "instr_prior_count",            {"Instructor": instructor},                                              target_term),
        "course_prior_count":           _lookup_count(lookups, "course_prior_count",           {"CourseCode": course_code},                                             target_term),
        "slot_prior_count":             _lookup_count(lookups, "slot_prior_count",             {"Slot": slot},                                                          target_term),
        "course_type_prior_count":      _lookup_count(lookups, "course_type_prior_count",      {"CourseCode": course_code, "Type": section_type},                       target_term),
        "instr_dept_prior_count":       _lookup_count(lookups, "instr_dept_prior_count",       {"Instructor": instructor, "Dept": dept},                                target_term),
        "instr_course_prior_count":     _lookup_count(lookups, "instr_course_prior_count",     {"Instructor": instructor, "CourseCode": course_code},                    target_term),
        "course_slot_prior_count":      _lookup_count(lookups, "course_slot_prior_count",      {"CourseCode": course_code, "Slot": slot},                                target_term),
        "course_type_slot_prior_count": _lookup_count(lookups, "course_type_slot_prior_count", {"CourseCode": course_code, "Type": section_type, "Slot": slot},          target_term),
        "combo_prior_count":            _lookup_count(lookups, "combo_prior_count",            {"CourseCode": course_code, "Instructor": instructor, "Slot": slot, "Type": section_type}, target_term),
    }

    recency_pairs = [
        ("instr_last_term",        {"Instructor": instructor}),
        ("course_last_term",       {"CourseCode": course_code}),
        ("instr_course_last_term", {"Instructor": instructor, "CourseCode": course_code}),
        ("combo_last_term",        {"CourseCode": course_code, "Instructor": instructor, "Slot": slot, "Type": section_type}),
    ]
    recency: dict = {}
    for out_col, grp in recency_pairs:
        last    = _lookup_last_term(lookups, out_col, grp, target_term)
        gap_col = out_col.replace("last_term", "terms_since")
        recency[gap_col] = (target_term + 1) if last == -1 else (target_term - last)

    return {
        "CourseCode": course_code,
        "Instructor": instructor,
        "Slot":       slot,
        "Type":       section_type,
        "instr_prior_count_log1p":            math.log1p(counts["instr_prior_count"]),
        "course_prior_count_log1p":           math.log1p(counts["course_prior_count"]),
        "slot_prior_count_log1p":             math.log1p(counts["slot_prior_count"]),
        "course_type_prior_count_log1p":      math.log1p(counts["course_type_prior_count"]),
        "instr_dept_prior_count_log1p":       math.log1p(counts["instr_dept_prior_count"]),
        "instr_course_prior_count_log1p":     math.log1p(counts["instr_course_prior_count"]),
        "course_slot_prior_count_log1p":      math.log1p(counts["course_slot_prior_count"]),
        "course_type_slot_prior_count_log1p": math.log1p(counts["course_type_slot_prior_count"]),
        "combo_prior_count_log1p":            math.log1p(counts["combo_prior_count"]),
        **recency,
    }


# ---------------------------------------------------------------------------
# Batch scorer
# ---------------------------------------------------------------------------

def score_candidates(candidates: list[dict], art: dict) -> list[dict]:
    """Score a list of candidate dicts in one batch model call.

    Returns a new list of dicts, each with 'prob_scheduled' (float 0-1) added.
    Candidates are scored relative to max_train_term + 1 (next unseen term).
    """
    if not candidates:
        return []
    feature_cols = art["cat_cols"] + art["num_cols"]
    rows = [build_svm_row(c, art) for c in candidates]
    X    = pd.DataFrame(rows)[feature_cols]
    proba = art["model"].predict_proba(X)[:, 1]
    result = []
    for c, p in zip(candidates, proba):
        item = dict(c)
        item["prob_scheduled"] = round(float(p), 4)
        result.append(item)
    return result

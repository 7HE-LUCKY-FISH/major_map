import dotenv

dotenv.load_dotenv()

import re
import math
from fastapi import APIRouter, HTTPException, Request

import hashlib
import json
from datetime import datetime
from db_module import get_db_connection
from jwt_verify import get_current_user_id_cookie

# ML helpers for schedule generation
import pandas as pd
from ml.features import compute_semester_index
from ml.inference import load_svm_artifact, score_candidates
from ml.ml_router import (
    A, B, C,
    CourseContext, InstructorContext,
    build_features_AB,
    topk,
)
from stats import generate_professor_slot_candidates

# TODO: This generate focuses on calling the ml_router
# Update: It got really ugly fast

router = APIRouter(prefix="/schedules", tags=["schedules"])


@router.post("/generate_v2")
async def generate_schedule_v2(request: Request, payload: dict):
    """Generate all conflict-free candidate schedules for a list of courses.

    Input JSON:
      {
        "courses": ["CS 146", "CS 151", "CS 166"],
        "year": 2026,
        "semester": "Fall",
        "name": "My Schedule",
        "description": "",
        "term_id": 1
      }

    Pipeline per course:
      1. generate_professor_slot_candidates  → (instructor x slot) pairs from DB
      2. score_candidates                   → batch SVM scoring
      3. filter at prob_scheduled >= 0.7    → fallback to top-3 if nothing passes

    Incremental-pruning product loop builds all conflict-free schedule combinations.
    Each schedule is annotated with schedule_score = sum(log(prob_scheduled)),
    a log-joint-probability proxy for how historically likely the combination is.
    All valid schedules are returned sorted best-first; the user picks from them.
    """
    user_id = get_current_user_id_cookie(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="Access token required")

    courses = payload.get("courses", [])
    if not courses:
        raise HTTPException(status_code=400, detail="courses list is required")

    # ---- Load SVM artifact (cached after first call) ----
    try:
        svm_art = load_svm_artifact()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    # ---- Generate and score candidates per course ----
    PROB_THRESHOLD = 0.7
    per_course: list[list[dict]] = []

    for course in courses:
        # 1. Pull (instructor x slot) candidates from DB history
        try:
            candidates = generate_professor_slot_candidates(course)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"DB error for {course}: {exc}")

        if not candidates:
            # No historical data for this course — skip gracefully
            per_course.append([])
            continue

        # 2. Score all candidates in one batch (one predict_proba call)
        scored = score_candidates(candidates, svm_art)

        # 3. Keep high-confidence candidates; fall back to top-3 if none qualify
        filtered = [c for c in scored if c["prob_scheduled"] >= PROB_THRESHOLD]
        if not filtered:
            filtered = sorted(scored, key=lambda c: c["prob_scheduled"], reverse=True)[:3]

        per_course.append(filtered)

    # ---- Build conflict-free schedules (incremental pruning) ----
    # Start with one empty partial schedule.  For each course we try to extend
    # every existing partial with every candidate for that course, keeping only
    # combinations that have no time conflict.  Pruning happens immediately, so
    # we never enumerate combinations that can't work.
    partials: list[list[dict]] = [[]]

    for course_candidates in per_course:
        if not course_candidates:
            continue  # no candidates for this course — skip it
        next_partials: list[list[dict]] = []
        for partial in partials:
            for cand in course_candidates:
                c_days, c_times = split_slot_prediction(cand.get("slot_label", "TBD TBD"))
                conflict = any(
                    is_time_conflict(
                        c_days, c_times,
                        *split_slot_prediction(assigned.get("slot_label", "TBD TBD")),
                    )
                    for assigned in partial
                )
                if not conflict:
                    next_partials.append(partial + [cand])
        # If all candidates conflict with every partial, preserve existing
        # partials so the remaining courses can still be scheduled.
        partials = next_partials if next_partials else partials

    # ---- Annotate each schedule with a confidence score ----
    # schedule_score = sum(log(prob_scheduled)).
    # This is the log-joint-probability under independence (higher = more likely).
    # Stored here so the frontend can display / sort by it later.
    schedules_out = []
    for sections in partials:
        score = sum(math.log(max(s["prob_scheduled"], 1e-9)) for s in sections)
        schedules_out.append({
            "sections": sections,
            "schedule_score": round(score, 4),
        })

    # Best schedules first
    schedules_out.sort(key=lambda s: s["schedule_score"], reverse=True)

    # ---- Persist to DB and return all options ----
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(
            "INSERT INTO schedules (user_id, name, description, term_id, sections, input_hash) VALUES (%s,%s,%s,%s,%s,%s)",
            (
                user_id,
                payload.get("name", "Generated Schedule"),
                payload.get("description", ""),
                payload.get("term_id"),
                json.dumps(schedules_out),
                hashlib.sha256(
                    json.dumps({"courses": sorted(courses)}, sort_keys=True).encode()
                ).hexdigest(),
            ),
        )
        schedule_id = cursor.lastrowid
        connection.commit()
        return {
            "schedule_id":     schedule_id,
            "total_schedules": len(schedules_out),
            "schedules":       schedules_out,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to save schedules: {exc}")
    finally:
        cursor.close()
        connection.close()

def split_slot_prediction(slot_str: str):
    """Safely splits a model prediction like 'MW 09:00AM-10:15AM' into days and times."""
    parts = str(slot_str).strip().split(" ", 1)
    if len(parts) == 2:
        return parts[0], parts[1]
    return "TBD", "TBD"

def is_time_conflict(days1: str, times1: str, days2: str, times2: str) -> bool:
    """
    Checks for day and time overlaps using individual days and times fields.
    """
    if not days1 or not days2 or days1 in ["TBD", "TBA"] or days2 in ["TBD", "TBA"]:
        return False
    if not times1 or not times2 or times1 in ["TBD", "TBA"] or times2 in ["TBD", "TBA"]:
        return False

    days1_set = set(days1.upper())
    days2_set = set(days2.upper())
    if not days1_set.intersection(days2_set):
        return False # No shared days, so no conflict

    def parse_times(t_str):
        match = re.search(r"(\d{1,2}:\d{2}[A-Za-z]+)-(\d{1,2}:\d{2}[A-Za-z]+)", t_str.replace(" ", ""))
        if not match:
            return 0, 0
        
        start_str, end_str = match.groups()
        try:
            start_dt = datetime.strptime(start_str, "%I:%M%p")
            end_dt = datetime.strptime(end_str, "%I:%M%p")
            return (start_dt.hour * 60 + start_dt.minute), (end_dt.hour * 60 + end_dt.minute)
        except ValueError:
            return 0, 0

    start1, end1 = parse_times(times1)
    start2, end2 = parse_times(times2)

    if start1 == 0 or start2 == 0:
        return False # Parsing failed

    if start1 < end2 and start2 < end1:
        return True
        
    return False

def hydrate_course_context(course_code: str = "Unknown", section_num: str = "01") -> CourseContext:
    return CourseContext(
        section=f"{course_code} (Section {section_num})",
        mode="In Person", 
        unit=3,
        type="LEC",
        days="TBD",
        times="TBD",
        satifies="Unknown",
        location="Unknown",
        year=2026,        # (these will need to change)
        semester="Spring"
    )


def hydrate_instructor_context(instructor_name: str) -> InstructorContext:
    return InstructorContext(
        instructor=instructor_name,
        mode="In Person",
        type="LEC",
        semester="Spring",
        building="Unknown",
        year=2026 #(these will need to change)
    )


@router.post("/generate")
async def generate_schedule(request: Request, payload: dict):
    user_id = get_current_user_id_cookie(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="Access token required")

    input_str = json.dumps(payload, sort_keys=True)
    input_hash = hashlib.sha256(input_str.encode()).hexdigest()

    # Expecting: {"items": [{"type": "course", "value": "CS 146"}, {"type": "instructor", "value": "Richard Low"}]}
    user_selections = payload.get("items", [])
    predictions: list[dict] = []
    
    # This now holds dictionaries of {"days": ..., "times": ...}
    assigned_slots: list[dict] = []

    for item in user_selections:
        item_type = item.get("type")
        item_value = item.get("value")

        predicted_course = None
        predicted_instructor = None
        slot_preds = []
        instr_preds = []

        try:
            if item_type == "course":
                ctx = hydrate_course_context(course_code=item_value)
                
                row_A = build_features_AB(ctx, A["sem_cfg"])
                X_A = pd.DataFrame([row_A])[A["cat"] + A["num"]]
                instr_preds = topk(A["pipeline"], X_A, k=3)
                predicted_instructor = instr_preds[0] if instr_preds else None

                row_B = build_features_AB(ctx, B["sem_cfg"])
                X_B = pd.DataFrame([row_B])[B["cat"] + B["num"]]
                slot_preds = topk(B["pipeline"], X_B, k=3)
                predicted_course = item_value

            elif item_type == "instructor":
                instr_ctx = hydrate_instructor_context(instructor_name=item_value)
                
                sem_index = compute_semester_index(instr_ctx.year, instr_ctx.semester, C["sem_cfg"])
                row_C = {
                    "Instructor": instr_ctx.instructor, "Mode": instr_ctx.mode,
                    "Type": instr_ctx.type, "Semester": instr_ctx.semester,
                    "Building": instr_ctx.building, "Year": instr_ctx.year,
                    "SemesterIndex": sem_index
                }
                X_C = pd.DataFrame([row_C])[C["cat"] + C["num"]]
                course_preds = topk(C["pipeline"], X_C, k=3)
                predicted_course = course_preds[0] if course_preds else "Unknown"
                predicted_instructor = item_value

                ctx = hydrate_course_context(course_code=predicted_course)
                row_B = build_features_AB(ctx, B["sem_cfg"])
                X_B = pd.DataFrame([row_B])[B["cat"] + B["num"]]
                slot_preds = topk(B["pipeline"], X_B, k=3)

            else:
                continue

            chosen_days = "TBD"
            chosen_times = "TBD"
            conflict_warning = False
            
            for pred_slot in slot_preds:
                p_days, p_times = split_slot_prediction(pred_slot)
                
                has_conflict = any(
                    is_time_conflict(p_days, p_times, assigned["days"], assigned["times"])
                    for assigned in assigned_slots
                )
                
                if not has_conflict:
                    chosen_days = p_days
                    chosen_times = p_times
                    break

            if chosen_days == "TBD":
                fallback_days, fallback_times = split_slot_prediction(slot_preds[0]) if slot_preds else ("TBD", "TBD")
                chosen_days = fallback_days
                chosen_times = fallback_times
                conflict_warning = True
            
            assigned_slots.append({"days": chosen_days, "times": chosen_times})

            predictions.append({
                "requested_input": item_value,
                "input_type": item_type,
                "predicted_course": predicted_course,
                "predicted_instructor": predicted_instructor,
                "predicted_days": chosen_days,
                "predicted_times": chosen_times,
                "conflict_warning": conflict_warning,
                "options_instructors": instr_preds if item_type == "course" else [predicted_instructor],
                "options_slots": slot_preds,
            })

        except Exception as err:
            raise HTTPException(status_code=400, detail=f"Failed processing {item_value}: {err}")

    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(
            "INSERT INTO schedules (user_id, name, description, term_id, sections, input_hash) VALUES (%s,%s,%s,%s,%s,%s)",
            (
                user_id,
                payload.get("name"),
                payload.get("description", ""),
                payload.get("term_id"),
                json.dumps(predictions),
                input_hash,
            ),
        )
        schedule_id = cursor.lastrowid
        connection.commit()
        return {
            "schedule_id": schedule_id,
            "message": "Schedule created successfully",
            "predictions": predictions,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create schedule: {str(e)}")
    finally:
        cursor.close()
        connection.close()


@router.get("")
async def list_schedules(request: Request):
    """List all schedules for the current user."""
    user_id = get_current_user_id_cookie(request)

    if not user_id:
        raise HTTPException(status_code=401, detail="Access token required")
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            "SELECT schedule_id, name, description, term_id, sections, created_at, updated_at FROM schedules WHERE user_id = %s",
            (user_id,)
        )
        schedules = cursor.fetchall()

        for schedule in schedules:
            schedule["sections"] = json.loads(schedule["sections"]) if schedule["sections"] else []
        
        cursor.close()
        connection.close()
        return schedules
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve schedules: {str(e)}")


@router.post("")
async def save_schedule(request: Request, payload: dict):
    """Save a new schedule for the current user."""
    user_id = get_current_user_id_cookie(request)

    name = payload.get("name")
    description = payload.get("description", "")
    term_id = payload.get("term_id")
    sections = payload.get("sections", [])

    if not name:
        raise HTTPException(status_code=400, detail="Schedule name is required")
    if not isinstance(sections, list):
        raise HTTPException(status_code=400, detail="Sections must be a list")

    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO schedules (user_id, name, description, term_id, sections)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (user_id, name, description, term_id, json.dumps(sections))
        )
        schedule_id = cursor.lastrowid
        connection.commit()

        return {"schedule_id": schedule_id, "message": "Schedule saved successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save schedule: {str(e)}")
    finally:
        cursor.close()
        connection.close()

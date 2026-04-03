from fastapi import APIRouter, HTTPException
from db_module import get_db_connection
from stats import (top_instructors_last4_semesters, unique_time_slots_last4_semesters, generate_professor_slot_candidates)

# course endpoints which query the database
router = APIRouter(prefix="/courses", tags=["courses"])


@router.get("/")
def list_courses():
    """Return all rows from the courses table."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT course_id, dept_id, code, name FROM courses")
        return cursor.fetchall()
    finally:
        conn.close()


@router.get("/{course_id}/sections")
async def list_sections(course_id: int):
    """Return an empty list of sections for the given course id (stub)."""
    return []


@router.get("/{course_id}")
def get_course(course_id: int):
    """Return a single course row by ID from the database."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT course_id, dept_id, code, name FROM courses "
            "WHERE course_id = %s",
            (course_id,)
        )
        row = cursor.fetchone()
    finally:
        conn.close()

    if row is None:
        raise HTTPException(status_code=404, detail="Course not found")
    
    return row

@router.get("/instructors/test")
def instructors_test(course_number: str):
    """Return top 3 instructors for a course (by recent 4 semesters)."""
    rows = top_instructors_last4_semesters(course_number)
    if not rows:
        raise HTTPException(status_code=404, detail="No instructors found for this course")
    return {"course_number": course_number, "results": rows}

@router.get("/slots/test")
def stats_unique_slots(course_number: str):
    rows = unique_time_slots_last4_semesters(course_number)
    if not rows:
        raise HTTPException(status_code=404, detail="No time slots found for this course")
    return {"course_number": course_number, "unique_slots": rows}


@router.get("/candidates/test")
def stats_candidates(course_number: str):
    rows = generate_professor_slot_candidates(course_number)
    if not rows:
        raise HTTPException(status_code=404, detail="No candidates found for this course")
    return {"course_number": course_number, "candidates": rows, "count": len(rows)}
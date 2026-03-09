from fastapi import APIRouter, HTTPException
from db_module import get_db_connection

# course endpoints which query the database
router = APIRouter(prefix="/courses", tags=["courses"])


@router.get("")
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

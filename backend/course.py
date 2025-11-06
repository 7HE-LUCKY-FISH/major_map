from fastapi import APIRouter

# Simplified/stubbed course endpoints to avoid requiring DB/session.
router = APIRouter(prefix="/courses", tags=["courses"])


@router.get("")
async def list_courses():
    """Return an empty list (stub)."""
    return []


@router.get("/{course_id}/sections")
async def list_sections(course_id: int):
    """Return an empty list of sections for the given course id (stub)."""
    return []
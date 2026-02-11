from fastapi import APIRouter, HTTPException, Request
import dotenv
import hashlib
import json
from datetime import datetime
from db_module import get_db_connection
from jwt_verify import get_current_user_id_cookie


dotenv.load_dotenv()

# TODO: This is a very basic implementation of the schedules endpoints. 
# In a real application, you would want to add more robust error handling, 
# input validation, and authentication/authorization checks.

router = APIRouter(prefix="/schedules", tags=["schedules"])

@router.post("/generate")
async def generate_schedule(request: Request, payload: dict):
    """Generate a schedule using ML models based on user preferences."""
    user_id = get_current_user_id_cookie(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="Access token required")
    
    input_str = json.dumps(payload, sort_keys=True)
    input_hash = hashlib.sha256(input_str.encode()).hexdigest()
    
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            "SELECT schedule_id, name, description, term_id, sections, created_at, updated_at FROM schedules WHERE user_id = %s AND input_hash = %s",
            (user_id, input_hash)
        )
        existing_schedule = cursor.fetchone()
        
        if existing_schedule:
            schedule_id, name, description, term_id, sections, created_at, updated_at = existing_schedule
            return {
                "schedule_id": schedule_id,
                "name": name,
                "description": description,
                "term_id": term_id,
                "sections": json.loads(sections) if sections else [],
                "created_at": created_at,
                "updated_at": updated_at,
                "message": "Schedule already exists"
            }
        
        cursor.execute(
            "INSERT INTO schedules (user_id, name, description, term_id, sections, input_hash) VALUES (%s, %s, %s, %s, %s, %s)",
            (user_id, payload.get("name"), payload.get("description", ""), payload.get("term_id"), json.dumps(payload.get("sections", [])), input_hash)
        )
        schedule_id = cursor.lastrowid
        
        connection.commit()
        cursor.close()
        connection.close()
        return {
            "schedule_id": schedule_id,
            "message": "Schedule created successfully"
        }


    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create schedule: {str(e)}")



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
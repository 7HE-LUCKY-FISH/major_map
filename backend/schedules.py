from fastapi import APIRouter, HTTPException, Request
import mysql.connector
from mysql.connector import Error
import os
import dotenv
import hashlib
import json
from datetime import datetime
from db_module import get_db_connection
dotenv.load_dotenv()

# TODO: This is a very basic implementation of the schedules endpoints. 
# In a real application, you would want to add more robust error handling, 
# input validation, and authentication/authorization checks.

router = APIRouter(prefix="/schedules", tags=["schedules"])

@router.post("/generate")
async def generate_schedule(request: Request, payload: dict):
    """Generate a schedule using ML models based on user preferences."""
    access_token = request.cookies.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Access token required")
    
    # Mock token validation (replace with real JWT validation)
    if not access_token.startswith("mock_access_token_"):
        raise HTTPException(status_code=401, detail="Invalid access token")
    
    try:
        user_id = int(access_token.split("_")[-1])
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid access token")
    
    input_str = json.dumps(payload, sort_keys=True)
    input_hash = hashlib.sha256(input_str.encode()).hexdigest()
    
    connection = get_db_connection()
    cursor = connection.cursor()
    
    try:
        cursor.execute(
            "SELECT job_id, status FROM generation_jobs WHERE input_hash = %s",
            (input_hash,)
        )
        existing_job = cursor.fetchone()
        
        if existing_job:
            job_id, status = existing_job
            return {
                "job_id": job_id,
                "status": status,
                "message": "Job already exists"
            }
        
        cursor.execute(
            "INSERT INTO generation_jobs (input_hash, status) VALUES (%s, %s)",
            (input_hash, "queued")
        )
        job_id = cursor.lastrowid
        
        connection.commit()
        
        # TODO: Actually trigger ML generation process here
        # For now, just return the job_id
        
        return {
            "job_id": job_id,
            "status": "queued",
            "message": "Schedule generation started"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start generation: {str(e)}")
    finally:
        cursor.close()
        connection.close()


@router.get("")
async def list_schedules(request: Request):
    """List all schedules for the current user."""
    access_token = request.cookies.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Access token required")
    
    # Mock token validation (replace with real JWT validation)
    if not access_token.startswith("mock_access_token_"):
        raise HTTPException(status_code=401, detail="Invalid access token")
    
    try:
        user_id = int(access_token.split("_")[-1])
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid access token")
    
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        cursor.execute(
            "SELECT schedule_id, name, description, term_id, sections, created_at, updated_at FROM schedules WHERE user_id = %s ORDER BY updated_at DESC",
            (user_id,)
        )
        schedules = cursor.fetchall()
        
        for schedule in schedules:
            schedule["sections"] = json.loads(schedule["sections"]) if schedule["sections"] else []
        
        return schedules
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list schedules: {str(e)}")
    finally:
        cursor.close()
        connection.close()


@router.post("")
async def save_schedule(request: Request, payload: dict):
    """Save a new schedule for the current user."""
    access_token = request.cookies.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Access token required")
    
    # Mock token validation (replace with real JWT validation)
    if not access_token.startswith("mock_access_token_"):
        raise HTTPException(status_code=401, detail="Invalid access token")
    
    try:
        user_id = int(access_token.split("_")[-1])
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid access token")
    
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
            "INSERT INTO schedules (user_id, name, description, term_id, sections) VALUES (%s, %s, %s, %s, %s)",
            (user_id, name, description, term_id, json.dumps(sections))
        )
        schedule_id = cursor.lastrowid
        
        connection.commit()
        
        return {
            "schedule_id": schedule_id,
            "message": "Schedule saved successfully"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save schedule: {str(e)}")
    finally:
        cursor.close()
        connection.close()
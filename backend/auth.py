import json

from fastapi import APIRouter, HTTPException, Request, Response
import bcrypt
import mysql.connector

from jwt_verify import get_current_user_id_cookie, create_access_token
from db_module import get_db_connection


router = APIRouter(prefix="/auth", tags=["auth"])

DEFAULT_PLANNER_STATE = {
    "major": {
        "completedCourses": [],
        "selectedMajor": "",
        "submitted": False,
    },
    "roadmap": [],
    "schedule": {
        "schedules": [],
        "professorFreqs": {},
        "selectedScheduleIndex": 0,
    },
}


def ensure_user_planner_state_table(connection) -> None:
    cursor = connection.cursor()
    try:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS user_planner_state (
                user_id INT PRIMARY KEY,
                major_data JSON NOT NULL,
                roadmap_data JSON NOT NULL,
                schedule_data JSON NOT NULL,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
                    ON DELETE CASCADE
            ) ENGINE=InnoDB
            """
        )
        connection.commit()
    finally:
        cursor.close()


def parse_json_column(value, fallback):
    if value in (None, ""):
        return fallback

    if isinstance(value, (dict, list)):
        return value

    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return fallback


@router.post("/register")
async def register(payload: dict):
    """Register a new user in the database."""

    username = payload.get("username")
    password = payload.get("password")
    email = payload.get("email")

    if not username or not password or not email:
        raise HTTPException(
            status_code=400,
            detail="Username, password, and email required",
        )

    # hash the password
    hashed_password = (
        bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
        .decode("utf-8")
    )

    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            "INSERT INTO users (username, password_hash, email) VALUES (%s, %s, %s)",
            (username, hashed_password, email),
        )
        connection.commit()
        return {
            "message": "User registered successfully",
            "user_id": cursor.lastrowid,
        }
    except mysql.connector.IntegrityError:  # pragma: no cover - handled by caller
        raise HTTPException(
            status_code=409,
            detail="Username or email already exists",
        )
    except Exception as e:  # pragma: no cover - unexpected
        raise HTTPException(
            status_code=500,
            detail=f"Registration failed: {str(e)}",
        )
    finally:
        cursor.close()
        connection.close()


@router.post("/login")
async def login(resp: Response, payload: dict):
    """Authenticate user against database."""

    username = payload.get("username")
    password = payload.get("password")
    if not username or not password:
        raise HTTPException(status_code=400, detail="Username and password required")

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            "SELECT user_id, password_hash FROM users WHERE username = %s", (username,)
        )
        user = cursor.fetchone()
        if not user:
            raise HTTPException(
                status_code=401, detail="Invalid username or password"
            )

        if not bcrypt.checkpw(
            password.encode("utf-8"), user["password_hash"].encode("utf-8")
        ):
            raise HTTPException(
                status_code=401, detail="Invalid username or password"
            )

        access_token = create_access_token(user_id=user["user_id"])
        refresh_token = create_access_token(user_id=user["user_id"])

        resp.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            samesite="lax",
            secure=False,  # set to True in production with HTTPS
            max_age=3600,  # 1 hour
        )
        return {"access_token": access_token, "refresh_token": refresh_token}
    except HTTPException:  # re-raise
        raise
    except Exception as e:  # pragma: no cover - unexpected
        raise HTTPException(
            status_code=500, detail=f"Login failed: {str(e)}"
        )
    finally:
        cursor.close()
        connection.close()


@router.post("/logout")
async def logout(resp: Response):
    resp.delete_cookie("access_token")
    return {"ok": True}


@router.get("/profile")
async def get_profile(request: Request):
    user_id = get_current_user_id_cookie(request)

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            "SELECT user_id, username, email, created_at FROM users WHERE user_id = %s",
            (user_id,),
        )
        user = cursor.fetchone()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return user
    finally:
        cursor.close()
        connection.close()


@router.put("/profile")
async def update_profile(request: Request, payload: dict):
    """Update the current user's profile information."""

    user_id = get_current_user_id_cookie(request)

    username = payload.get("username")
    email = payload.get("email")
    if not username and not email:
        raise HTTPException(
            status_code=400,
            detail="At least username or email must be provided",
        )

    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        update_fields: list[str] = []
        update_values: list[str] = []

        if username:
            update_fields.append("username = %s")
            update_values.append(username)
        if email:
            update_fields.append("email = %s")
            update_values.append(email)

        update_values.append(user_id)

        cursor.execute(
            f"UPDATE users SET {', '.join(update_fields)} WHERE user_id = %s",
            update_values,
        )

        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="User not found")

        connection.commit()
        return {"message": "Profile updated successfully"}
    except mysql.connector.IntegrityError as e:  # pragma: no cover - handled
        if "username" in str(e):
            raise HTTPException(status_code=409, detail="Username already exists")
        if "email" in str(e):
            raise HTTPException(status_code=409, detail="Email already exists")
        raise HTTPException(
            status_code=409,
            detail="Update conflicts with existing data",
        )
    except HTTPException:
        raise
    except Exception as e:  # pragma: no cover - unexpected
        raise HTTPException(
            status_code=500, detail=f"Failed to update profile: {str(e)}"
        )
    finally:
        cursor.close()
        connection.close()


@router.get("/planner-state")
async def get_planner_state(request: Request):
    user_id = get_current_user_id_cookie(request)

    connection = get_db_connection()
    ensure_user_planner_state_table(connection)
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT major_data, roadmap_data, schedule_data
            FROM user_planner_state
            WHERE user_id = %s
            """,
            (user_id,),
        )
        planner_state = cursor.fetchone()

        if not planner_state:
            return DEFAULT_PLANNER_STATE

        return {
            "major": parse_json_column(
                planner_state.get("major_data"),
                DEFAULT_PLANNER_STATE["major"],
            ),
            "roadmap": parse_json_column(
                planner_state.get("roadmap_data"),
                DEFAULT_PLANNER_STATE["roadmap"],
            ),
            "schedule": parse_json_column(
                planner_state.get("schedule_data"),
                DEFAULT_PLANNER_STATE["schedule"],
            ),
        }
    finally:
        cursor.close()
        connection.close()


@router.put("/planner-state")
async def update_planner_state(request: Request, payload: dict):
    user_id = get_current_user_id_cookie(request)

    planner_state = {
        "major": payload.get("major", DEFAULT_PLANNER_STATE["major"]),
        "roadmap": payload.get("roadmap", DEFAULT_PLANNER_STATE["roadmap"]),
        "schedule": payload.get("schedule", DEFAULT_PLANNER_STATE["schedule"]),
    }

    connection = get_db_connection()
    ensure_user_planner_state_table(connection)
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO user_planner_state (
                user_id,
                major_data,
                roadmap_data,
                schedule_data
            )
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                major_data = VALUES(major_data),
                roadmap_data = VALUES(roadmap_data),
                schedule_data = VALUES(schedule_data)
            """,
            (
                user_id,
                json.dumps(planner_state["major"]),
                json.dumps(planner_state["roadmap"]),
                json.dumps(planner_state["schedule"]),
            ),
        )
        connection.commit()
        return {"ok": True}
    finally:
        cursor.close()
        connection.close()

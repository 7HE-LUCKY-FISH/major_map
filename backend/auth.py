from fastapi import APIRouter, Response, HTTPException
import mysql.connector
from mysql.connector import Error
import bcrypt
import os
import dotenv

dotenv.load_dotenv()

# Database connection function
def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', 'adminpass'),
            database='major_map_db',
            auth_plugin='mysql_native_password'
        )
        return connection
    except Error as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register")
async def register(payload: dict):
    """Register a new user in the database."""
    username = payload.get("username")
    password = payload.get("password")
    email = payload.get("email")
    
    if not username or not password or not email:
        raise HTTPException(status_code=400, detail="Username, password, and email required")
    
    # Hash the password
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    connection = get_db_connection()
    cursor = connection.cursor()
    
    try:
        cursor.execute(
            "INSERT INTO users (username, password_hash, email) VALUES (%s, %s, %s)",
            (username, hashed_password, email)
        )
        connection.commit()
        return {"message": "User registered successfully", "user_id": cursor.lastrowid}
    except mysql.connector.IntegrityError:
        raise HTTPException(status_code=409, detail="Username or email already exists")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")
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
        cursor.execute("SELECT user_id, password_hash FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        
        if not user:
            raise HTTPException(status_code=401, detail="Invalid username or password")
        
        # Check password
        if not bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
            raise HTTPException(status_code=401, detail="Invalid username or password")
        
        # Mock tokens (replace with real JWT implementation)
        access = f"mock_access_token_{user['user_id']}"
        refresh = f"mock_refresh_token_{user['user_id']}"
        
        resp.set_cookie(key="access_token", value=access, httponly=True)
        return {"access_token": access, "refresh_token": refresh}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")
    finally:
        cursor.close()
        connection.close()


@router.post("/logout")
async def logout(resp: Response):
    resp.delete_cookie("access_token")
    return {"ok": True}
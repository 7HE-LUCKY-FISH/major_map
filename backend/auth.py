from fastapi import APIRouter, Response, HTTPException, Request
import mysql.connector
from mysql.connector import Error
import bcrypt
import os
import dotenv

dotenv.load_dotenv()

from jwt_verify import get_current_user_id_cookie, create_access_token
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
        
        access_token = create_access_token(user_id=user['user_id'])
        refresh_token = create_access_token(user_id=user['user_id'])  # You can create a separate function for refresh tokens if needed
        
        resp.set_cookie(  #mess around this if there are other issues
            key="access_token", 
            value=access_token, 
            httponly=True,
            samesite ="lax",
            secure=False # set to True in production with HTTPS
            )
        return {"access_token": access_token, "refresh_token": refresh_token}
    
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


@router.get("/profile")
async def get_profile(request: Request):
    """Get the current user's profile information."""
    access_token = request.cookies.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Access token required")
    
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
            "SELECT user_id, username, email, created_at FROM users WHERE user_id = %s",(user_id,))
        user = cursor.fetchone()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {
            "user_id": user["user_id"],
            "username": user["username"],
            "email": user["email"],
            "created_at": user["created_at"]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get profile: {str(e)}")
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
        raise HTTPException(status_code=400, detail="At least username or email must be provided")
    
    connection = get_db_connection()
    cursor = connection.cursor()
    
    try:
        update_fields = []
        update_values = []
        
        if username:
            update_fields.append("username = %s")
            update_values.append(username)
        if email:
            update_fields.append("email = %s")
            update_values.append(email)
        
        update_values.append(user_id)
        
        cursor.execute(
            f"UPDATE users SET {', '.join(update_fields)} WHERE user_id = %s",
            update_values
        )
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="User not found")
        
        connection.commit()
        return {"message": "Profile updated successfully"}
    
    except mysql.connector.IntegrityError as e:
        if "username" in str(e):
            raise HTTPException(status_code=409, detail="Username already exists")
        elif "email" in str(e):
            raise HTTPException(status_code=409, detail="Email already exists")
        else:
            raise HTTPException(status_code=409, detail="Update conflicts with existing data")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update profile: {str(e)}")
    finally:
        cursor.close()
        connection.close()
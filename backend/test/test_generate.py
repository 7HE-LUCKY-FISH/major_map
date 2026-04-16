import sys
import os
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch

# Ensure the backend directory is in the path for CI
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import app

client = TestClient(app)

# ---------------------------------------------------------------------------
# 1. AUTHENTICATION TESTS (/auth)
# ---------------------------------------------------------------------------

@patch("auth.get_db_connection")
def test_user_registration(mock_get_db):
    """Test the registration endpoint with a mocked database."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_get_db.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.lastrowid = 1

    payload = {
        "username": "testuser",
        "password": "testpassword",
        "email": "test@example.com"
    }
    response = client.post("/auth/register", json=payload)
    
    assert response.status_code == 200
    assert response.json()["message"] == "User registered successfully"
    assert response.json()["user_id"] == 1

@patch("auth.get_db_connection")
def test_user_login(mock_get_db):
    """Test login and cookie setting."""
    # Mocking a user record with a pre-hashed 'testpassword'
    hashed_pw = "$2b$12$KIX0.vjH.O8E.O7v/8oI8uL1.W5.Z5.Z5.Z5.Z5.Z5.Z5.Z5.Z5." 
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_get_db.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = {"user_id": 1, "password_hash": hashed_pw}

    # Use a dummy JWT_SECRET for the test
    with patch.dict(os.environ, {"JWT_SECRET": "testsecret"}):
        payload = {"username": "testuser", "password": "testpassword"}
        # We must bypass the bcrypt check in mock or provide a real hash
        with patch("bcrypt.checkpw", return_value=True):
            response = client.post("/auth/login", json=payload)

    assert response.status_code == 200
    assert "access_token" in response.cookies

# ---------------------------------------------------------------------------
# 2. COURSE TESTS (/courses)
# ---------------------------------------------------------------------------

@patch("course.get_db_connection")
def test_list_courses(mock_get_db):
    """Verify course listing functionality."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_get_db.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchall.return_value = [
        {"course_id": 1, "dept_id": "CS", "code": "146", "name": "Data Structures"}
    ]

    response = client.get("/courses/")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["code"] == "146"

# ---------------------------------------------------------------------------
# 3. ML PREDICTION TESTS (/ml)
# ---------------------------------------------------------------------------

def test_predict_instructor_endpoint_not_enabled():
    """The legacy /ml/predict/instructor endpoint is currently disabled."""
    payload = {
        "section": "CS 146 (Section 01)",
        "mode": "In Person",
        "unit": 3,
        "type": "LEC",
        "year": 2025,
        "semester": "Spring"
    }
    response = client.post("/ml/predict/instructor", json=payload)
    assert response.status_code == 404

# ---------------------------------------------------------------------------
# 4. SCHEDULE GENERATION TESTS (/schedules/generate_v2)
# ---------------------------------------------------------------------------

@patch("schedules.get_db_connection")
@patch("schedules.load_svm_artifact")
@patch("schedules.generate_professor_slot_candidates")
@patch("schedules.score_candidates")
def test_generate_schedule_v2_success(mock_score, mock_candidates, mock_load_svm, mock_get_db):
    """
    FIX: Replaces test_predict_scheduled_probability to test the actual /generate_v2 endpoint.
    """
    # 1. Setup environment to bypass auth for easier testing
    with patch.dict(os.environ, {"DEV_BYPASS": "1"}):
        
        # 2. Mock ML Artifact
        mock_load_svm.return_value = {"model": MagicMock()}

        # 3. Mock DB candidates for the course
        mock_candidates.return_value = [
            {"instructor_name": "Richard Low", "slot_label": "MW 09:00AM-10:15AM"}
        ]

        # 4. Mock ML Scoring Output
        mock_score.return_value = [
            {
                "instructor_name": "Richard Low", 
                "slot_label": "MW 09:00AM-10:15AM", 
                "prob_scheduled": 0.85
            }
        ]

        # 5. Mock DB Connection for saving
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.lastrowid = 100

        payload = {
            "courses": ["CS 146"],
            "year": 2026,
            "semester": "Fall",
            "term_id": 1
        }

        response = client.post("/schedules/generate_v2", json=payload)

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["total_schedules"] > 0
        assert data["schedules"][0]["sections"][0]["instructor_name"] == "Richard Low"
        assert data["schedules"][0]["sections"][0]["prob_scheduled"] == 0.85

# ---------------------------------------------------------------------------
# 5. ERROR HANDLING TESTS
# ---------------------------------------------------------------------------

@patch("schedules.get_current_user_id_cookie")
def test_unauthorized_schedule_access(mock_get_user):
    """
    FIX: Verify that accessing schedules without a cookie fails when DEV_BYPASS is off.
    """
    # Ensure bypass is disabled for this test
    with patch.dict(os.environ, {"DEV_BYPASS": "0"}):
        mock_get_user.return_value = None  # Simulate no valid session cookie
        
        payload = {"courses": ["CS 146"]}
        response = client.post("/schedules/generate_v2", json=payload)
        
        assert response.status_code == 401
        assert response.json()["detail"] == "Access token required"
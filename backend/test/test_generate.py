import sys
import os
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch

# Ensure the backend directory is in the path for CI
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import app
from jwt_verify import create_access_token

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

@patch("ml.ml_router.topk")
def test_predict_instructor(mock_topk):
    """Test instructor prediction endpoint with mocked model output."""
    mock_topk.return_value = ["Richard Low", "Dummy Prof 1", "Dummy Prof 2"]
    
    payload = {
        "section": "CS 146 (Section 01)",
        "mode": "In Person",
        "unit": 3,
        "type": "LEC",
        "year": 2025,
        "semester": "Spring"
    }
    response = client.post("/ml/predict/instructor", json=payload)
    
    assert response.status_code == 200
    assert response.json()["best"] == "Richard Low"
    assert len(response.json()["topk"]) == 3

@patch("ml.ml_router._get_svm")
def test_predict_scheduled_probability(mock_get_svm):
    """Test the Linear SVM probability scoring endpoint."""
    # Mock the SVM artifact and model
    mock_model = MagicMock()
    mock_model.predict_proba.return_value = [[0.2, 0.8]] # 80% chance of being scheduled
    
    mock_art = {
        "model": mock_model,
        "cat_cols": ["CourseCode", "Instructor", "Slot", "Type"],
        "num_cols": [],
        "lookups": {},
        "max_train_term": 10
    }
    mock_get_svm.return_value = mock_art

    payload = {
        "section": "CS 146",
        "instructor": "Richard Low",
        "type": "LEC",
        "year": 2026,
        "semester": "Fall"
    }
    
    # Patch the feature hydration to avoid complex DB/Lookup logic
    with patch("ml.ml_router.build_features_svm", return_value=MagicMock()):
        response = client.post("/ml/predict/scheduled", json=payload)
    
    assert response.status_code == 200
    assert response.json()["prob_scheduled"] == 0.8

# ---------------------------------------------------------------------------
# 4. ERROR HANDLING TESTS
# ---------------------------------------------------------------------------

def test_unauthorized_profile_access():
    """Verify that accessing protected routes without a cookie fails."""
    response = client.get("/auth/profile")
    assert response.status_code == 401
    assert response.json()["detail"] == "Access token required"
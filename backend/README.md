## Backend Setup

1) Create + activate a Python virtual environment (venv)
2) Install dependencies: ```pip install -r requirements.txt```
3) Create .env (only if you don’t have one): add JWT_SECRET=dev-secret-change-me
4) Generate ML artifacts: ```python3 -m ml.train_hoang``` or ```python3 -m ml.train_anthony```
5) Run the backend: python3 main.py
6) Open in browser to check: http://localhost:8000/docs or http://localhost:8000/health
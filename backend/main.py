from fastapi.middleware.cors import CORSMiddleware
from schedules import router as schedules_router
from ml.ml_router import router as ml_router
from course import router as course_router
from auth import router as auth_router
from fastapi import FastAPI
import dotenv
import uvicorn
from dotenv import load_dotenv

load_dotenv()

dotenv.load_dotenv()


app = FastAPI(title="major_map backend")

app.include_router(auth_router)
app.include_router(course_router)
app.include_router(schedules_router)
app.include_router(ml_router)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://main.dy0gxxub1du5m.amplifyapp.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    # http://localhost:8000/docs#/
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

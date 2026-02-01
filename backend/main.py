from fastapi import FastAPI

from auth import router as auth_router
from course import router as course_router
from ml.ml_router import router as ml_router

import uvicorn

app = FastAPI(title="major_map backend")

app.include_router(auth_router)
app.include_router(course_router)
app.include_router(ml_router)

@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    #http://localhost:8000/docs#/
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

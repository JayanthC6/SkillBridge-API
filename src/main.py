from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from src.routers import attendance, auth, batches, sessions, summaries
from src.database import engine
from src import models

app = FastAPI(title="SkillBridge API")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def health_check():
    return {"status": "ok"}


def register_routers() -> None:
    app.include_router(auth.router, prefix="/auth", tags=["auth"])
    app.include_router(batches.router, tags=["batches"])
    app.include_router(sessions.router, tags=["sessions"])
    app.include_router(attendance.router, tags=["attendance"])
    app.include_router(summaries.router, tags=["summaries"])


register_routers()

if __name__ == "__main__":
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=False)
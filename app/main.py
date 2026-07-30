import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.attendances import router as attendances_router
from app.routers.events import router as events_router
from app.routers.groups import router as groups_router
from app.routers.members import router as members_router
from app.routers.reports import router as reports_router
from app.routers.uploads import router as uploads_router

app = FastAPI(title="Member Management API")

cors_origins = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "").split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins or ["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(members_router)
app.include_router(groups_router)
app.include_router(events_router)
app.include_router(attendances_router)
app.include_router(reports_router)
app.include_router(uploads_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}

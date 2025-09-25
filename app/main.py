from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .core.config import settings
from .core.database import Base, engine
from .routers import health, auth

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create metadata tables on startup (migrations will take over later)
Base.metadata.create_all(bind=engine)

app.include_router(health.router)
app.include_router(auth.router)

@app.get("/")
def root():
    return {"service": "easy-estates-api", "status": "ready"}

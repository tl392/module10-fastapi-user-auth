from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
import time

from app.database import engine, Base
from app.routes import router

# Resolve static directory relative to this file — works both locally and in Docker
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "app", "static")


@asynccontextmanager
async def lifespan(app: FastAPI):
    from sqlalchemy import text
    from sqlalchemy.exc import OperationalError

    for attempt in range(1, 16):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print(f"[startup] DB connected on attempt {attempt}.")
            break
        except OperationalError as e:
            print(f"[startup] DB not ready (attempt {attempt}/15): {e} — retrying in 3s…")
            time.sleep(3)
    else:
        raise RuntimeError("Could not connect to the database after 15 attempts.")

    Base.metadata.create_all(bind=engine)
    print("[startup] Tables created / verified OK.")
    yield


app = FastAPI(
    title="User Management API",
    description="Secure user management with FastAPI, SQLAlchemy, and bcrypt",
    version="1.0.0",
    lifespan=lifespan,
)

# Allow browser fetch() calls from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes BEFORE mounting static files
app.include_router(router)

# Serve static assets
if os.path.isdir(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def serve_ui():
    index = os.path.join(STATIC_DIR, "index.html")
    return FileResponse(index)


@app.get("/health")
def health():
    return {"status": "ok"}

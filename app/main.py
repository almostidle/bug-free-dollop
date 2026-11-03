from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from app.api.documents import router as documents_router
from app.api.config import router as config_router
from app.api.demo import router as demo_router
from app.db.session import init_db, SessionLocal
from app.models.document import Document
from app.services.demo_service import seed_reference_corpus
from app.exceptions import AppException


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    with SessionLocal() as db:
        if db.query(Document).count() == 0:
            seed_reference_corpus(db, reset=False)
    yield


app = FastAPI(
    title="Plagiarism & AI Content Detector",
    version="1.2.0",
    lifespan=lifespan,
)

app.include_router(documents_router)
app.include_router(config_router)
app.include_router(demo_router)

static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(static_dir), html=True), name="static")


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.get("/api/health")
def health():
    return {"status": "ok", "version": app.version}


@app.get("/")
async def root():
    return RedirectResponse(url="/static/index.html")

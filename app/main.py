from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from app.config import settings
from app.database import Base, engine
from app.routers import auth, categories, transactions, budgets, analytics, reports, recurring

Base.metadata.create_all(bind=engine)
app = FastAPI(title=settings.app_name, version="1.0.0", description="Personal finance and expense management API")
app.add_middleware(CORSMiddleware, allow_origins=settings.allowed_origins or ["*"],
                   allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
for router in [auth.router, categories.router, transactions.router, budgets.router,
               analytics.router, reports.router, recurring.router]:
    app.include_router(router)

@app.get("/api/health", tags=["System"])
def health():
    return {"status": "healthy"}

frontend = Path(__file__).resolve().parent.parent / "frontend"
app.mount("/", StaticFiles(directory=str(frontend), html=True), name="frontend")

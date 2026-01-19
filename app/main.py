from fastapi import FastAPI, BackgroundTasks
from app.core.config import settings
from app.core.scheduler import start_scheduler
from app.core.workflow import run_discovery_cycle

app = FastAPI(title="OpsPilot Lead MCP")

@app.on_event("startup")
async def startup_event():
    start_scheduler()

@app.get("/health")
async def health_check():
    return {
        "status": "active",
        "service": "OpsPilot Lead MCP",
        "config": {
            "reddit_enabled": bool(settings.REDDIT_CLIENT_ID),
            "linkedin_enabled": bool(settings.LINKEDIN_USERNAME and settings.LINKEDIN_PASSWORD)
        }
    }

@app.post("/run-now")
async def run_discovery_verified(background_tasks: BackgroundTasks):
    background_tasks.add_task(run_discovery_cycle)
    return {"status": "Discovery job triggered in background"}

@app.get("/stats")
async def get_stats():
    # In a real app we'd query the DB or Sheet for stats.
    # For now return placeholder or global counters if we added them.
    return {
        "message": "Stats implementation requires persistent storage reading (future)"
    }

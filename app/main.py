from fastapi import FastAPI, Depends
from app.deps.timing import timing_dependency
from app.routes import election, candidate, test, auth
from app.routes import vote, results
from app.database.base import Base
from app.database.session import engine
import uvicorn
from app.models import user, election, candidate, vote, otp, email_job  # import all models (including OTP and EmailJob)
from app.utils.logger import logger as base_logger
from app.tasks.scheduler import start_scheduler, stop_scheduler

logger = base_logger.bind(context="app")

app = FastAPI(dependencies=[Depends(timing_dependency)])

# Register request timing middleware to log latency & processing time
from app.middleware.request_timing import request_timing_middleware
app.middleware('http')(request_timing_middleware)

# CORS
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings

origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Metrics endpoint
from fastapi.responses import Response
from app.metrics import metrics_response, METRICS_ENABLED


@app.get('/metrics')
def metrics():
    if not METRICS_ENABLED:
        return Response('metrics disabled', status_code=503)
    resp = metrics_response()
    return Response(content=resp, media_type="text/plain; version=0.0.4; charset=utf-8")

app.include_router(auth.router)
app.include_router(election.router)
app.include_router(candidate.router)
app.include_router(test.router)
app.include_router(vote.router)
app.include_router(results.router)


def init_db():
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created")


@app.on_event("startup")
def _startup():
    init_db()
    start_scheduler(app)
    logger.info("Application startup complete")


@app.on_event("shutdown")
def _shutdown():
    stop_scheduler(app)
    logger.info("Application shutdown complete")


if __name__ == "__main__":
    init_db()
    print("Database tables created!")
    uvicorn.run(app, host="0.0.0.0", port=8000)
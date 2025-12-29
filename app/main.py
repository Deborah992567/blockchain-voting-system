from fastapi import FastAPI
from app.routes import election, candidate, test, auth
from app.routes import vote, results
from app.database.base import Base
from app.database.session import engine
import uvicorn
from app.models import user, election, candidate, vote, otp, email_job  # import all models (including OTP and EmailJob)
from app.utils.logger import logger as base_logger
from app.tasks.scheduler import start_scheduler, stop_scheduler

logger = base_logger.bind(context="app")

app = FastAPI()

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
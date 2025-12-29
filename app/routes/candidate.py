from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.candidate import Candidate
from app.models.election import Election
from app.schemas.candidate import CandidateCreate, CandidateOut
from app.utils.security import admin_only
from app.utils.logger import logger as base_logger

logger = base_logger.bind(context="routes.candidate")

router = APIRouter(prefix="/candidates", tags=["Candidates"])


@router.post("/", response_model=CandidateOut)
def add_candidate(candidate: CandidateCreate, db: Session = Depends(get_db), admin=Depends(admin_only)):
    election = db.query(Election).get(candidate.election_id)
    if not election:
        logger.warning("Add candidate failed: election not found", election_id=candidate.election_id)
        raise HTTPException(status_code=404, detail="Election not found")

    new_candidate = Candidate(
        name=candidate.name,
        election_id=candidate.election_id
    )
    db.add(new_candidate)
    db.commit()
    db.refresh(new_candidate)
    logger.info("Candidate added", candidate_id=new_candidate.id, election_id=new_candidate.election_id)
    return new_candidate



@router.get("/election/{election_id}", response_model=list[CandidateOut])
def list_candidates(election_id: int, db: Session = Depends(get_db)):
    logger.info("List candidates", election_id=election_id)
    candidates = db.query(Candidate).filter(Candidate.election_id == election_id).all()
    return candidates

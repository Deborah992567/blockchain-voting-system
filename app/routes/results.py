from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database.session import get_db
from app.models.vote import Vote
from app.models.candidate import Candidate
from backend.app.blockchain.vote import cast_vote
from backend.app.models.election import Election
from backend.app.utils.security import get_current_user
from app.utils.logger import logger as base_logger

logger = base_logger.bind(context="routes.results")

router = APIRouter(prefix="/results", tags=["Results"])

@router.get("/{election_id}")
def get_results(election_id: int, db: Session = Depends(get_db)):
    logger.info("Get results requested", election_id=election_id)
    results = (
        db.query(
            Candidate.name,
            func.count(Vote.id).label("votes")
        )
        .join(Vote, Vote.candidate_id == Candidate.id)
        .filter(Vote.election_id == election_id)
        .group_by(Candidate.name)
        .all()
    )

    return results

@router.post("/vote/blockchain")
def blockchain_vote(
    election_id: int,
    candidate_id: int,
    user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    logger.info("Send vote to blockchain", election_id=election_id, candidate_id=candidate_id, user_id=user.id)
    election = db.query(Election).get(election_id)

    tx_hash = cast_vote(
        election.contract_address,
        user.wallet_private_key,  # temp
        candidate_id
    )

    return {
        "message": "Vote sent to blockchain",
        "tx_hash": tx_hash
    }

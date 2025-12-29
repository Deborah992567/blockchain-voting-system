from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database.session import get_db
from app.models.vote import Vote
from app.models.election import Election
from app.models.candidate import Candidate
from app.models.user import User
from app.utils.security import get_current_user
from app.utils.logger import logger as base_logger

logger = base_logger.bind(context="routes.vote")

router = APIRouter(prefix="/votes", tags=["Votes"])

# ---------------- Helper Functions ----------------
def get_election_or_404(db: Session, election_id: int):
    election = db.query(Election).get(election_id)
    if not election:
        raise HTTPException(status_code=404, detail="Election not found")
    return election

def get_candidate_or_404(db: Session, candidate_id: int, election_id: int = None):
    candidate = db.query(Candidate).get(candidate_id)
    if not candidate or (election_id and candidate.election_id != election_id):
        raise HTTPException(status_code=404, detail="Candidate not found in this election")
    return candidate

def admin_required(user):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

# ---------------- Voting Endpoints ----------------
@router.post("/cast-vote/{election_id}/{candidate_id}")
def cast_vote(election_id: int, candidate_id: int, db: Session = Depends(get_db), user = Depends(get_current_user)):
    logger.info("Cast vote attempt", user_id=user.id, election_id=election_id, candidate_id=candidate_id)
    election = get_election_or_404(db, election_id)
    candidate = get_candidate_or_404(db, candidate_id, election_id)

    existing_vote = db.query(Vote).filter(
        Vote.user_id == user.id,
        Vote.election_id == election.id
    ).first()
    if existing_vote:
        logger.warning("User already voted", user_id=user.id, election_id=election_id)
        raise HTTPException(status_code=400, detail="User has already voted in this election")

    vote = Vote(user_id=user.id, election_id=election.id, candidate_id=candidate.id)
    db.add(vote)
    db.commit()
    db.refresh(vote)
    logger.info("Vote cast", vote_id=vote.id, user_id=user.id)
    return {"message": "Vote cast successfully", "vote_id": vote.id}

@router.delete("/retract-vote/{vote_id}")
def retract_vote(vote_id: int, db: Session = Depends(get_db), user = Depends(get_current_user)):
    vote = db.query(Vote).get(vote_id)
    if not vote:
        logger.warning("Retract vote failed: not found", vote_id=vote_id)
        raise HTTPException(status_code=404, detail="Vote not found")
    if vote.user_id != user.id:
        logger.warning("Retract vote denied: different user", vote_id=vote_id, user_id=user.id)
        raise HTTPException(status_code=403, detail="Cannot retract others' votes")
    db.delete(vote)
    db.commit()
    logger.info("Vote retracted", vote_id=vote_id, user_id=user.id)
    return {"message": "Vote retracted successfully"}

# ---------------- Election Results ----------------
@router.get("/election/{election_id}/results")
def election_results(election_id: int, db: Session = Depends(get_db), user = Depends(get_current_user)):
    election = get_election_or_404(db, election_id)
    logger.info("Fetching election results", election_id=election_id)
    results = db.query(
        Candidate.id,
        Candidate.name,
        func.count(Vote.id).label("vote_count")
    ).join(Vote, Vote.candidate_id == Candidate.id).filter(
        Candidate.election_id == election.id
    ).group_by(Candidate.id).all()

    return {
        "election_id": election.id,
        "election_title": election.title,
        "results": [{"candidate_id": c.id, "candidate_name": c.name, "vote_count": c.vote_count} for c in results]
    }

@router.get("/election/{election_id}/total-votes")
def total_votes_in_election(election_id: int, db: Session = Depends(get_db), user = Depends(get_current_user)):
    total = db.query(Vote).filter(Vote.election_id == election_id).count()
    logger.info("Total votes in election", election_id=election_id, total=total)
    return {"total_votes": total}

@router.get("/candidate/{candidate_id}/total-votes")
def total_votes_for_candidate(candidate_id: int, db: Session = Depends(get_db), user = Depends(get_current_user)):
    total = db.query(Vote).filter(Vote.candidate_id == candidate_id).count()
    logger.info("Total votes for candidate", candidate_id=candidate_id, total=total)
    return {"total_votes": total}

@router.get("/election/{election_id}/leading-candidate")
def leading_candidate(election_id: int, db: Session = Depends(get_db), user = Depends(get_current_user)):
    results = db.query(
        Candidate.id,
        Candidate.name,
        func.count(Vote.id).label("vote_count")
    ).join(Vote, Vote.candidate_id == Candidate.id).filter(
        Candidate.election_id == election_id
    ).group_by(Candidate.id).order_by(func.count(Vote.id).desc()).first()

    if not results:
        logger.warning("Leading candidate lookup: no votes", election_id=election_id)
        raise HTTPException(status_code=404, detail="No votes found for this election")

    return {"candidate_id": results.id, "candidate_name": results.name, "vote_count": results.vote_count}

# ---------------- User Votes ----------------
@router.get("/user/{user_id}/votes")
def votes_by_user(user_id: int, db: Session = Depends(get_db), user = Depends(get_current_user)):
    votes = db.query(Vote).filter(Vote.user_id == user_id).all()
    logger.info("Listing votes by user", user_id=user_id, count=len(votes))
    return [{"vote_id": v.id, "election_id": v.election_id, "candidate_id": v.candidate_id} for v in votes]

@router.get("/election/{election_id}/voters")
def voters_in_election(election_id: int, db: Session = Depends(get_db), user = Depends(get_current_user)):
    votes = db.query(Vote).filter(Vote.election_id == election_id).all()
    logger.info("Listing voters in election", election_id=election_id, count=len(votes))
    return {"voter_ids": [v.user_id for v in votes]}

@router.get("/candidate/{candidate_id}/voters")
def voters_for_candidate(candidate_id: int, db: Session = Depends(get_db), user = Depends(get_current_user)):
    votes = db.query(Vote).filter(Vote.candidate_id == candidate_id).all()
    logger.info("Listing voters for candidate", candidate_id=candidate_id, count=len(votes))
    return {"voter_ids": [v.user_id for v in votes]}

# ---------------- Admin Endpoints ----------------
@router.delete("/admin/retract-vote/{vote_id}")
def admin_retract_vote(vote_id: int, db: Session = Depends(get_db), user = Depends(get_current_user)):
    admin_required(user)
    vote = db.query(Vote).get(vote_id)
    if not vote:
        logger.warning("Admin retract vote failed: not found", vote_id=vote_id)
        raise HTTPException(status_code=404, detail="Vote not found")
    db.delete(vote)
    db.commit()
    logger.info("Admin retracted vote", vote_id=vote_id, admin_id=user.id)
    return {"message": "Vote retracted by admin successfully"}

@router.get("/admin/all-votes-with-details")
def admin_all_votes_with_details(db: Session = Depends(get_db), user = Depends(get_current_user)):
    admin_required(user)
    votes = db.query(Vote).all()
    logger.info("Admin requested all votes", count=len(votes), admin_id=user.id)
    detailed = []
    for v in votes:
        voter = db.query(User).get(v.user_id)
        election = db.query(Election).get(v.election_id)
        candidate = db.query(Candidate).get(v.candidate_id)
        detailed.append({
            "vote_id": v.id,
            "user_id": voter.id if voter else None,
            "user_email": voter.email if voter else None,
            "election_id": election.id if election else None,
            "election_title": election.title if election else None,
            "candidate_id": candidate.id if candidate else None,
            "candidate_name": candidate.name if candidate else None,
            "timestamp": v.created_at
        })
    return detailed

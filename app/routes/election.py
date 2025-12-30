from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.election import Election
from app.schemas.election import ElectionCreate, ElectionOut
from app.utils.security import get_current_user, admin_only
from app.blockchain.deploy import deploy_election
from app.models.candidate import Candidate
from app.utils.logger import logger as base_logger

logger = base_logger.bind(context="routes.election")

router = APIRouter(prefix="/elections", tags=["Elections"])



@router.post("/", response_model=ElectionOut)
def create_election(election: ElectionCreate, db: Session = Depends(get_db), admin=Depends(admin_only)):
    logger.info("Create election requested", name=(election.name or election.title))

    # Deploy blockchain contract with candidate names if provided
    candidate_names = election.candidate_names or []
    contract_address = None
    if candidate_names:
        try:
            contract_address = deploy_election(candidate_names)
        except Exception:
            logger.exception("Failed to deploy election contract; continuing without contract")

    new_election = Election(
        name=(election.name or election.title),
        is_active=False,
        contract_address=contract_address
    )
    db.add(new_election)
    db.commit()
    db.refresh(new_election)

    # Create candidate records (preserve order -> index)
    for cname in candidate_names:
        c = Candidate(name=cname, election_id=new_election.id)
        db.add(c)
    db.commit()
    logger.info("Election created", election_id=new_election.id, contract_address=contract_address)
    return new_election


@router.post("/{election_id}/start")
def start_election(election_id: int, db: Session = Depends(get_db), admin=Depends(admin_only)):
    election = db.query(Election).get(election_id)
    if not election:
        logger.warning("Start election failed: not found", election_id=election_id)
        raise HTTPException(status_code=404, detail="Election not found")
    election.is_active = True
    db.commit()
    logger.info("Election started", election_id=election_id)
    return {"message": "Election started"}


@router.post("/{election_id}/end")
def end_election(election_id: int, db: Session = Depends(get_db), admin=Depends(admin_only)):
    election = db.query(Election).get(election_id)
    if not election:
        logger.warning("End election failed: not found", election_id=election_id)
        raise HTTPException(status_code=404, detail="Election not found")
    election.is_active = False
    db.commit()
    logger.info("Election ended", election_id=election_id)
    return {"message": "Election ended"}


@router.get("/", response_model=list[ElectionOut])
def list_elections(db: Session = Depends(get_db)):
    elections = db.query(Election).all()
    return elections


@router.get("/{election_id}/details")
def election_details(election_id: int, db: Session = Depends(get_db)):
    election = db.query(Election).get(election_id)
    if not election:
        logger.warning("Election details not found", election_id=election_id)
        raise HTTPException(status_code=404, detail="Election not found")

    candidates = db.query(Candidate).filter(Candidate.election_id == election_id).order_by(Candidate.id).all()
    # map candidates to an index order that corresponds to the deployed contract
    payload_candidates = []
    for idx, c in enumerate(candidates):
        payload_candidates.append({"id": c.id, "name": c.name, "index": idx})

    return {
        "id": election.id,
        "name": election.name or election.title,
        "is_active": election.is_active,
        "contract_address": getattr(election, 'contract_address', None),
        "candidates": payload_candidates
    }

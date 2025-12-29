from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.election import Election
from app.schemas.election import ElectionCreate, ElectionOut
from app.utils.security import get_current_user, admin_only
from app.blockchain.deploy import deploy_election
from app.utils.logger import logger as base_logger

logger = base_logger.bind(context="routes.election")

router = APIRouter(prefix="/elections", tags=["Elections"])



@router.post("/", response_model=ElectionOut)
def create_election(election: ElectionCreate, db: Session = Depends(get_db), admin=Depends(admin_only)):
    logger.info("Create election requested", name=election.name)
    # Deploy blockchain contract
    contract_address = deploy_election(election.candidate_names)

    new_election = Election(
        name=election.name,
        is_active=False,
        contract_address=contract_address
    )
    db.add(new_election)
    db.commit()
    db.refresh(new_election)
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

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.database.session import SessionLocal
from app.auths.jwt import create_access_token
from app.models.user import User
from app.models.election import Election
from app.models.candidate import Candidate
from app.models.vote import Vote


client = TestClient(app)


def create_user(db: Session, email: str, role: str = 'voter', verified: bool = True):
    u = User(email=email, password_hash='hash', role=role, is_verified=verified)
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


def auth_header_for(user: User):
    token = create_access_token({'sub': user.email})
    return {'Authorization': f'Bearer {token}'}


@pytest.fixture(scope='function')
def db():
    db = SessionLocal()
    try:
        yield db
    finally:
        # cleanup
        db.query(Vote).delete()
        db.query(Candidate).delete()
        db.query(Election).delete()
        db.query(User).delete()
        db.commit()
        db.close()


def test_create_election_with_candidates(db: Session):
    admin = create_user(db, 'admin@example.com', role='admin')
    headers = auth_header_for(admin)

    payload = {
        'name': 'Test Election',
        'candidate_names': ['Alice', 'Bob']
    }

    r = client.post('/elections/', json=payload, headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert 'id' in data

    # verify candidates created
    election_id = data['id']
    cands = db.query(Candidate).filter(Candidate.election_id == election_id).order_by(Candidate.id).all()
    names = [c.name for c in cands]
    assert names == ['Alice', 'Bob']


def test_cast_vote_and_prevent_double_vote(db: Session):
    admin = create_user(db, 'admin2@example.com', role='admin')
    headers_admin = auth_header_for(admin)

    # create election
    payload = {'name': 'Elect 2', 'candidate_names': ['X', 'Y']}
    r = client.post('/elections/', json=payload, headers=headers_admin)
    election_id = r.json()['id']
    c = db.query(Candidate).filter(Candidate.election_id == election_id).first()

    voter = create_user(db, 'voter@example.com', role='voter')
    headers_voter = auth_header_for(voter)

    # cast vote
    r = client.post(f'/votes/cast-vote/{election_id}/{c.id}', headers=headers_voter)
    assert r.status_code == 200
    assert 'vote_id' in r.json()

    # second vote should be rejected
    r2 = client.post(f'/votes/cast-vote/{election_id}/{c.id}', headers=headers_voter)
    assert r2.status_code == 400


def test_submit_signed_vote_records_vote_and_recovers_signer(db: Session, monkeypatch):
    # create election & candidate
    admin = create_user(db, 'admin3@example.com', role='admin')
    headers_admin = auth_header_for(admin)
    payload = {'name': 'Elect 3', 'candidate_names': ['C1']}
    r = client.post('/elections/', json=payload, headers=headers_admin)
    election_id = r.json()['id']
    cand = db.query(Candidate).filter(Candidate.election_id == election_id).first()

    # create voter
    voter = create_user(db, 'voter2@example.com')
    headers_voter = auth_header_for(voter)

    # mock w3 recover_message to simulate signature recovery
    fake_addr = '0xdeadbeef000000000000000000000000deadbeef'

    class FakeAccount:
        @staticmethod
        def recover_message(msg, signature=None):
            return fake_addr

    class FakeW3:
        eth = type('Eth', (), {'account': FakeAccount})

    monkeypatch.setattr('app.routes.vote.w3', FakeW3())

    payload = {
        'election_id': election_id,
        'candidate_id': cand.id,
        'message': 'Vote:1:1:0xabc:123',
        'signature': '0xsig'
    }

    r = client.post('/votes/submit-signature', json=payload, headers=headers_voter)
    assert r.status_code == 200
    data = r.json()
    assert data['wallet'] == fake_addr

    # ensure vote persisted
    v = db.query(Vote).filter(Vote.user_id == voter.id, Vote.election_id == election_id).first()
    assert v is not None
    assert v.signature == '0xsig'

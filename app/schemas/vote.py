from pydantic import BaseModel

class VoteCreate(BaseModel):
    election_id: int
    candidate_id: int
class VoteResponse(BaseModel):
    id: int
    user_id: int
    election_id: int
    candidate_id: int

    class Config:
        orm_mode = True
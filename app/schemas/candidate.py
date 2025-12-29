from pydantic import BaseModel

class CandidateCreate(BaseModel):
    name: str
    election_id: int

class CandidateOut(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True
class CandidateDetail(BaseModel):
    id: int
    name: str
    election_id: int
    photo_url: str | None = None
    manifesto: str | None = None
    party: str | None = None
    bio: str | None = None

    class Config:
        from_attributes = True  
        
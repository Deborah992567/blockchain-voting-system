from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class ElectionCreate(BaseModel):
    # Use 'name' as primary label; keep 'title' compatibility by allowing either in requests
    name: str
    title: Optional[str] = None
    candidate_names: Optional[List[str]] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

class ElectionOut(BaseModel):
    id: int
    name: Optional[str]
    contract_address: Optional[str]
    is_active: bool

    class Config:
        from_attributes = True
       
        
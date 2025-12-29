from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ElectionCreate(BaseModel):
    title: str
    start_time: Optional[datetime]
    end_time: Optional[datetime]

class ElectionOut(BaseModel):
    id: int
    title: str
    is_active: bool

    class Config:
        from_attributes = True
       
        
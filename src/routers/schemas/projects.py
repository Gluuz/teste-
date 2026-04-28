
from pydantic import BaseModel

class ProjectCreate(BaseModel):
    name: str
    description: str

class ProjectCreateResponse(BaseModel):
    id: int
    name: str
    description: str
    created_at: str
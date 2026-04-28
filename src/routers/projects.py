
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.post("", response_model=ProjectCreateResponse, status_code=201)
def create_project(body: ProjectsCreate, db: Session = Depends(get_db)):
    g = Goal(
        **body.model_dump(),
        created_at=datetime.utcnow().isoformat(),
    )
    db.add(g)
    db.commit()
    db.refresh(g)
    return _to_out(g, db)
from datetime import datetime

from sqlalchemy import Column, Float, ForeignKey, Index, Integer, Text
from sqlalchemy.orm import relationship

from src.infra.database import Base



class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(Text, nullable=False, default=lambda: datetime.utcnow().isoformat())

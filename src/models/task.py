from sqlalchemy import Boolean, Column, Date, ForeignKey, Index, Integer, Text
from sqlalchemy.orm import relationship

from src.infra.database import Base



class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="SET NULL"), nullable=True)
    title = Column(Text, nullable=False)
    priority = Column(Integer, nullable=True)
    completed = Column(Boolean, nullable=True, default=False)
    due_date = Column(Date, nullable=False)
   
from sqlalchemy import Column, Integer, String, Boolean, Enum
from ..core.database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(Enum("owner", "manager", "caretaker", "viewer", name="user_roles"), nullable=False, default="owner")
    active = Column(Boolean, default=True)

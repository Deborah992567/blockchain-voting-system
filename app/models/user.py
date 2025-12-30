from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
from app.database.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="voter")  # "admin" or "voter"
    is_verified = Column(Boolean, default=False)
    wallet_private_key = Column(String, nullable=True)  # TEMP for testing
    google_id = Column(String, nullable=True, unique=True)
    github_id = Column(String, nullable=True, unique=True)

    # Relationships
    votes = relationship('Vote', back_populates='user')
    otps = relationship('OTP', back_populates='user')
    administered_elections = relationship('Election', secondary='election_admins', back_populates='admins')

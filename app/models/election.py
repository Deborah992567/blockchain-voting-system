from sqlalchemy import Column, Integer, String, DateTime, Boolean, Table, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.base import Base

# Many-to-many association table between elections and admins (users)
election_admins = Table(
    'election_admins',
    Base.metadata,
    Column('election_id', Integer, ForeignKey('elections.id'), primary_key=True),
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    # allow re-definition in test/import scenarios
    extend_existing=True,
)

class Election(Base):
    __tablename__ = "elections"
    id = Column(Integer, primary_key=True, index=True)
    # keep existing title for compatibility
    title = Column(String, nullable=True)
    # legacy name used in some places — keep both for safety
    name = Column(String, nullable=True)
    # contract address when deployed
    contract_address = Column(String, nullable=True)

    # Relationships
    candidates = relationship('Candidate', back_populates='election', cascade='all, delete-orphan')
    votes = relationship('Vote', back_populates='election')
    admins = relationship('User', secondary=election_admins, back_populates='administered_elections')
    is_active = Column(Boolean, default=False)
    start_time = Column(DateTime(timezone=True), nullable=True)
    end_time = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
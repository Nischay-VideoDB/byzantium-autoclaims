import os
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, JSON, Text, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from database_url import normalize_database_url


_default_database_url = (
    "sqlite:////tmp/byzantium-autoclaims.db"
    if os.getenv("VERCEL")
    else "sqlite:///./byzantium_autoclaims.db"
)
DATABASE_URL = normalize_database_url(os.getenv("DATABASE_URL", _default_database_url))

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class ClaimRecord(Base):
    __tablename__ = "claims"

    id = Column(Integer, primary_key=True, index=True)
    claim_id = Column(String, unique=True, index=True, nullable=False)
    claimant_name = Column(String, nullable=True)
    claimant_id_number = Column(String, nullable=True)
    policy_number = Column(String, nullable=True)
    video_path = Column(String, nullable=True)
    video_filename = Column(String, nullable=True)
    nric = Column(String, nullable=True)
    vehicle_plate = Column(String, nullable=True)
    status = Column(String, default="pending")  # pending | analyzing | complete | error

    # Analysis results (stored as JSON)
    video_analysis = Column(JSON, nullable=True)
    identity_result = Column(JSON, nullable=True)
    myinfo_result = Column(JSON, nullable=True)
    kimi_result = Column(JSON, nullable=True)
    nosana_job = Column(JSON, nullable=True)

    # Decision
    trust_score = Column(Integer, nullable=True)
    risk_level = Column(String, nullable=True)
    decision = Column(String, nullable=True)
    reason = Column(Text, nullable=True)
    payout_amount = Column(Float, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    decided_at = Column(DateTime, nullable=True)


def init_db():
    Base.metadata.create_all(bind=engine)
    # Safe migration: add columns that may be missing from existing DBs
    with engine.connect() as conn:
        for col_sql in [
            "ALTER TABLE claims ADD COLUMN vehicle_plate VARCHAR",
        ]:
            try:
                conn.execute(text(col_sql))
                conn.commit()
            except Exception:
                pass  # Column already exists


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

from sqlalchemy import Column, Integer, String, Float, Text, DateTime, Boolean
from sqlalchemy.sql import func
from .database import Base

class Canton(Base):
    __tablename__ = "cantons"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(2), unique=True, index=True, nullable=False)
    name = Column(String(120), nullable=False)
    geoportal_url = Column(String(500), nullable=False)
    cadastral_info_url = Column(String(500), nullable=False)
    owner_info_availability = Column(String(120), nullable=False)
    grundbuch_contact = Column(String(500), nullable=True)
    notes = Column(Text, nullable=True)
    status = Column(String(30), default="not checked", nullable=False)

class ParcelCandidate(Base):
    __tablename__ = "parcel_candidates"

    id = Column(Integer, primary_key=True, index=True)
    canton = Column(String(2), index=True, nullable=False)
    municipality = Column(String(120), index=True, nullable=False)
    parcel_number = Column(String(120), index=True, nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    area_sqm = Column(Float, nullable=True)
    land_type = Column(String(120), nullable=True)
    public_owner_text = Column(Text, nullable=True)
    source_url = Column(String(500), nullable=False)
    date_checked = Column(DateTime(timezone=True), server_default=func.now())
    candidate_signals = Column(Text, nullable=False)
    confidence_score = Column(Integer, default=0, nullable=False)
    risk_score = Column(Integer, default=0, nullable=False)
    verification_status = Column(String(30), default="new", nullable=False)
    ai_explanation = Column(Text, nullable=True)
    is_protected_land = Column(Boolean, default=False)


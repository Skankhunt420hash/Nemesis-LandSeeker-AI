from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class CantonBase(BaseModel):
    code: str
    name: str
    geoportal_url: str
    cadastral_info_url: str
    owner_info_availability: str
    grundbuch_contact: Optional[str] = None
    notes: Optional[str] = None
    status: str

class CantonOut(CantonBase):
    id: int
    class Config:
        from_attributes = True

class ParcelIngest(BaseModel):
    canton: str
    municipality: str
    parcel_number: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    area_sqm: Optional[float] = None
    land_type: Optional[str] = None
    public_owner_text: Optional[str] = None
    source_url: str
    is_protected_land: bool = False

class ParcelUpdateStatus(BaseModel):
    verification_status: str = Field(pattern="^(new|contacted|verified|rejected)$")

class WfsImportRequest(BaseModel):
    url: str
    type_name: str
    limit: int = Field(default=200, ge=1, le=5000)

class ServiceMetadataRequest(BaseModel):
    url: str

class CandidateDossierOut(BaseModel):
    candidate_id: int
    practical_score: int
    caution_level: str
    summary: str
    registry_readiness: str
    red_flags: List[str]
    next_steps: List[str]
    evidence_checklist: List[str]
    registry_questions: List[str]
    source_provenance: List[str]
    legal_guardrail: str

class ParcelOut(BaseModel):
    id: int
    canton: str
    municipality: str
    parcel_number: str
    latitude: Optional[float]
    longitude: Optional[float]
    area_sqm: Optional[float]
    land_type: Optional[str]
    public_owner_text: Optional[str]
    source_url: str
    date_checked: datetime
    candidate_signals: List[str]
    confidence_score: int
    risk_score: int
    verification_status: str
    ai_explanation: Optional[str]
    is_protected_land: bool

    class Config:
        from_attributes = True

"""
Pydantic models for NoFeesApts.
All data models and input models used across routes.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime, timezone
import uuid


# ============ DATA MODELS ============

class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    name: str
    picture: Optional[str] = None
    password_hash: Optional[str] = None
    is_admin: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class UserSession(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    session_token: str
    expires_at: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Building(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    address: str
    neighborhood: str
    city: str
    state: str
    zip_code: str
    source_url: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    last_crawled: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Unit(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    building_id: str
    unit_number: str
    rent: float
    bedrooms: int
    bathrooms: float
    square_feet: Optional[int] = None
    available_date: Optional[str] = None
    amenities: List[str] = []
    images: List[str] = []
    description: Optional[str] = None
    is_available: bool = True
    is_featured: bool = False
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    lifecycle_status: str = Field(default="available")
    stale_since: Optional[datetime] = None
    rented_at: Optional[datetime] = None
    rented_notes: Optional[str] = None
    lifecycle_updated_at: Optional[datetime] = None
    is_verified: bool = False
    verified_at: Optional[datetime] = None
    verified_by: Optional[str] = None
    crawler_source: Optional[str] = None
    crawler_batch_id: Optional[str] = None
    original_staging_id: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ReviewStatus:
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class BuildingStaging(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    address: str
    normalized_address: Optional[str] = None
    neighborhood: str
    city: str
    normalized_city: Optional[str] = None
    state: str
    normalized_state: Optional[str] = None
    zip_code: str
    normalized_zip: Optional[str] = None
    address_hash: Optional[str] = None
    source_url: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    last_crawled: Optional[datetime] = None
    review_status: str = Field(default="pending")
    crawler_source: str = Field(default="")
    crawler_batch_id: str = Field(default="")
    validation_flags: List[str] = Field(default_factory=list)
    duplicate_score: float = Field(default=0.0)
    matched_production_id: Optional[str] = None
    raw_data: Optional[dict] = None
    reviewer_notes: Optional[str] = None
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class UnitStaging(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    building_id: str
    unit_number: str
    normalized_unit_number: Optional[str] = None
    rent: float
    bedrooms: int
    bathrooms: float
    square_feet: Optional[int] = None
    available_date: Optional[str] = None
    amenities: List[str] = []
    images: List[str] = []
    original_images: List[str] = []
    description: Optional[str] = None
    is_available: bool = True
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    review_status: str = Field(default="pending")
    crawler_source: str = Field(default="")
    crawler_batch_id: str = Field(default="")
    validation_flags: List[str] = Field(default_factory=list)
    duplicate_score: float = Field(default=0.0)
    matched_production_id: Optional[str] = None
    raw_data: Optional[str] = None
    reviewer_notes: Optional[str] = None
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Favorite(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    unit_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SavedSearch(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    user_email: str
    user_phone: Optional[str] = None
    name: str
    bedrooms: Optional[int] = None
    min_rent: Optional[float] = None
    max_rent: Optional[float] = None
    bathrooms: Optional[float] = None
    state: Optional[str] = None
    neighborhood: Optional[str] = None
    alert_frequency: str = "daily"
    notify_email: bool = True
    notify_sms: bool = False
    is_active: bool = True
    last_alert_sent: Optional[datetime] = None
    last_checked_at: Optional[datetime] = None
    notified_unit_ids: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ContactRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    unit_id: str
    message: str
    name: str
    email: str
    phone: Optional[str] = None
    preferred_date: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AISearchHistory(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    query: str
    response: str
    units_found: int = 0
    neighborhoods_mentioned: List[str] = []
    price_range: Optional[dict] = None
    bedrooms_requested: Optional[int] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    preferred_time: Optional[str] = None
    alternative_date: Optional[str] = None
    alternative_time: Optional[str] = None


# ============ INPUT MODELS ============

class AISearchRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class SignupInput(BaseModel):
    email: str
    password: str
    name: str


class LoginInput(BaseModel):
    email: str
    password: str


class ForgotPasswordInput(BaseModel):
    email: str


class ResetPasswordInput(BaseModel):
    token: str
    new_password: str


class AdminResetPasswordInput(BaseModel):
    user_id: str
    new_password: str


class ShareUnitInput(BaseModel):
    unit_id: str
    recipient_email: str
    message: Optional[str] = None


class EmailSubscribeInput(BaseModel):
    email: str


class BuildingInput(BaseModel):
    name: str
    address: str
    neighborhood: str
    city: str
    state: str
    zip_code: str
    source_url: str


class UnitInput(BaseModel):
    building_id: str
    unit_number: str
    rent: float
    bedrooms: int
    bathrooms: float
    square_feet: Optional[int] = None
    available_date: Optional[str] = None
    amenities: List[str] = []
    images: List[str] = []
    description: Optional[str] = None
    is_available: bool = True
    is_featured: bool = False


class ContactInput(BaseModel):
    unit_id: str
    message: str
    name: str
    email: str
    phone: Optional[str] = None
    preferred_date: Optional[str] = None
    preferred_time: Optional[str] = None
    alternative_date: Optional[str] = None
    alternative_time: Optional[str] = None


class BuildingStagingInput(BaseModel):
    name: str
    address: str
    neighborhood: str
    city: str
    state: str
    zip_code: str
    source_url: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    crawler_source: str = ""
    crawler_batch_id: str = ""
    validation_flags: List[str] = []
    duplicate_score: float = 0.0


class UnitStagingInput(BaseModel):
    building_id: str
    unit_number: str
    rent: float
    bedrooms: int
    bathrooms: float
    square_feet: Optional[int] = None
    available_date: Optional[str] = None
    amenities: List[str] = []
    images: List[str] = []
    description: Optional[str] = None
    is_available: bool = True
    crawler_source: str = ""
    crawler_batch_id: str = ""
    validation_flags: List[str] = []
    duplicate_score: float = 0.0


class StagingReviewInput(BaseModel):
    review_status: str
    reviewer_notes: Optional[str] = None


class StagingUnitEditInput(BaseModel):
    building_id: Optional[str] = None
    unit_number: Optional[str] = None
    rent: Optional[float] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[float] = None
    square_feet: Optional[int] = None
    available_date: Optional[str] = None
    description: Optional[str] = None
    images: Optional[List[str]] = None


class StagingBulkReviewInput(BaseModel):
    ids: List[str]
    review_status: str
    reviewer_notes: Optional[str] = None


class SavedSearchInput(BaseModel):
    name: str
    bedrooms: Optional[int] = None
    min_rent: Optional[float] = None
    max_rent: Optional[float] = None
    bathrooms: Optional[float] = None
    state: Optional[str] = None
    neighborhood: Optional[str] = None
    alert_frequency: str = "daily"
    phone_number: Optional[str] = None
    notify_email: bool = True
    notify_sms: bool = False


class ScheduleViewingInput(BaseModel):
    unit_id: str
    viewing_date: str
    viewing_time: str
    notes: Optional[str] = None


class UnavailabilityReviewInput(BaseModel):
    review_status: str
    reviewer_notes: Optional[str] = None


class BulkUnavailabilityReviewInput(BaseModel):
    review_ids: List[str]
    review_status: str
    reviewer_notes: Optional[str] = None


class BulkRelistInput(BaseModel):
    unit_ids: List[str]
    notes: Optional[str] = None


class ApproveRejectedInput(BaseModel):
    rent: Optional[int] = None


class BulkDeleteInput(BaseModel):
    ids: List[str]


class PropertySearchRequest(BaseModel):
    query: str
    search_type: str = "all"


class PropertyCrawlRequest(BaseModel):
    url: str
    building_name: Optional[str] = None


class PropertyImportRequest(BaseModel):
    building: dict
    units: List[dict]


class DiscoverySearchRequest(BaseModel):
    area: str = "all"
    search_new_construction: bool = True
    search_net_effective: bool = True


class LifecycleStatusInput(BaseModel):
    status: str
    rent: Optional[float] = None
    available_date: Optional[str] = None
    notes: Optional[str] = None


class BulkLifecycleInput(BaseModel):
    unit_ids: List[str]
    notes: Optional[str] = None

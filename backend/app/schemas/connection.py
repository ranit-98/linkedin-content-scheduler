import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class LinkedInConnectionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    linkedin_member_id: str
    display_name: str | None
    token_expires_at: datetime
    scopes: str
    created_at: datetime


class OAuthUrlResponse(BaseModel):
    authorization_url: str

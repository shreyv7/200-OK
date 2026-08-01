"""Schemas for integrations API endpoints. Owner: Person D."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class IntegrationStatusItem(BaseModel):
    provider: str
    connected_at: datetime = Field(alias="connectedAt")
    expires_at: Optional[datetime] = Field(default=None, alias="expiresAt")
    revoked_at: Optional[datetime] = Field(default=None, alias="revokedAt")
    is_active: bool = Field(alias="isActive")
    scopes: List[str] = Field(default_factory=list)

    model_config = {"populate_by_name": True}


class ConnectResponse(BaseModel):
    auth_url: str = Field(alias="authUrl")

    model_config = {"populate_by_name": True}


class CallbackResponse(BaseModel):
    provider: str
    connected: bool
    scopes: List[str] = Field(default_factory=list)

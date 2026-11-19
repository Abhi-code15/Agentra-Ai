"""Pydantic schemas for multi-tenant organizations, departments, and members."""
import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class OrganizationCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255, description="Organization legal or business name")
    slug: str = Field(..., min_length=2, max_length=100, pattern=r"^[a-z0-9-]+$", description="Unique tenant slug")
    domain: Optional[str] = Field(default=None, max_length=255, description="Primary email domain")


class OrganizationResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    domain: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DepartmentCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    code: Optional[str] = Field(default=None, max_length=50)


class DepartmentResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    code: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class MemberAdd(BaseModel):
    email: str = Field(..., description="User email address")
    role: str = Field(default="EMPLOYEE", description="Role within the organization")
    department_id: Optional[uuid.UUID] = None
    employee_code: Optional[str] = None


class MemberResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    user_id: uuid.UUID
    department_id: Optional[uuid.UUID] = None
    role: str
    employee_code: Optional[str] = None
    status: str
    joined_at: datetime
    user_email: Optional[str] = None
    user_full_name: Optional[str] = None

    class Config:
        from_attributes = True

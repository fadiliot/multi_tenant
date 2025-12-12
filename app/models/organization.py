from pydantic import BaseModel, EmailStr
from typing import Optional

class OrganizationCreate(BaseModel):
    organization_name: str
    email: EmailStr
    password: str

class OrganizationOut(BaseModel):
    organization_name: str
    collection_name: str
    is_active: bool
    
    # Pydantic V2 Configuration
    model_config = {
        "populate_by_name": True, # Replaces allow_population_by_field_name
        "json_schema_extra": {
            # Since _id is an ObjectId, we represent it as a string
            "example": {
                "organization_name": "AcmeCorp",
                "collection_name": "org_AcmeCorp",
                "is_active": True
            }
        }
    }
    
    # NOTE: In a robust Pydantic V2 setup, you would use a Pydantic base class 
    # to handle ObjectId serialization, but this minimal fix solves the immediate warning.

# app/models/auth.py (Content below)
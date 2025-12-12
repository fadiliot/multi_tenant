from fastapi import APIRouter, HTTPException, Depends, status, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from bson import ObjectId
from datetime import datetime
from typing import Optional
from pydantic import EmailStr # <--- FIX: Added missing import

from app.db.mongo_client import db_client
from app.models.organization import OrganizationCreate, OrganizationOut
from app.models.auth import AdminLogin, Token
from app.core.security import hash_password, verify_password, create_access_token, decode_access_token
from app.core.config import settings

router = APIRouter()

# Initialize the security scheme
oauth2_scheme = HTTPBearer()

# Dependency function to get current admin (from token)
def get_current_admin(credentials: HTTPAuthorizationCredentials = Security(oauth2_scheme)):
    # Extract the token string from the credentials object
    token = credentials.credentials
    payload = decode_access_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # Returns the admin's ObjectId and Org ObjectId
    return {"admin_id": payload.get("sub"), "org_id": payload.get("org_id")}


## 1. Create Organization
@router.post("/create", response_model=OrganizationOut, status_code=status.HTTP_201_CREATED)
async def create_organization(org_data: OrganizationCreate):
    # 1. Validate that the organization name does not already exist.
    if db_client.org_collection.find_one({"organization_name": org_data.organization_name}):
        raise HTTPException(status_code=400, detail="Organization name already exists.")

    collection_name = db_client.get_tenant_collection_name(org_data.organization_name)
    hashed_password = hash_password(org_data.password)

    # 2. Create the admin user (without organization_id yet)
    admin_user = {
        "email": org_data.email,
        "password_hash": hashed_password,
        "organization_id": None # Placeholder, to be updated
    }
    try:
        admin_result = db_client.admin_collection.insert_one(admin_user)
    except Exception:
        # Check for duplicate email index error specifically (optional but better)
        raise HTTPException(status_code=400, detail="Admin email already exists.")

    admin_user_id = admin_result.inserted_id

    # 3. Store the organization in the Master Database
    organization = {
        "organization_name": org_data.organization_name,
        "collection_name": collection_name,
        "admin_user_id": admin_user_id,
        "is_active": True,
        "created_at": datetime.now()
    }
    org_result = db_client.org_collection.insert_one(organization)
    org_id = org_result.inserted_id
    
    # 4. Update admin user with organization_id reference
    db_client.admin_collection.update_one(
        {"_id": admin_user_id},
        {"$set": {"organization_id": org_id}}
    )

    # 5. Dynamically create a new Mongo collection
    db_client.create_tenant_collection(collection_name)

    # 6. Return a success response
    return OrganizationOut(**organization)


## 2. Get Organization by Name
@router.get("/get", response_model=OrganizationOut)
async def get_organization(organization_name: str):
    organization = db_client.org_collection.find_one({"organization_name": organization_name})
    
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found.")
        
    return OrganizationOut(**organization)


## 5. Admin Login
@router.post("/login", response_model=Token)
async def admin_login(admin_data: AdminLogin):
    # 1. Find the admin user
    user = db_client.admin_collection.find_one({"email": admin_data.email})
    
    if not user or not user.get("password_hash"):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
        
    # 2. Validate the admin credentials
    if not verify_password(admin_data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
        
    # 3. On success, return a JWT token
    from datetime import timedelta # Imported here for cleaner scope
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Ensure IDs are strings for the token payload
    org_id_str = str(user.get("organization_id"))
    
    token_data = {
        "sub": str(user["_id"]), 
        "org_id": org_id_str 
    }
    
    access_token = create_access_token(data=token_data, expires_delta=access_token_expires)
    
    return {"access_token": access_token, "token_type": "bearer"}


## 4. Delete Organization (Protected Route)
@router.delete("/delete", status_code=status.HTTP_204_NO_CONTENT)
async def delete_organization(
    organization_name: str, 
    current_admin: dict = Depends(get_current_admin)
):
    # Fetch organization details
    organization = db_client.org_collection.find_one({"organization_name": organization_name})
    
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found.")
        
    # 1. Allow deletion for respective authenticated user only
    if str(organization["_id"]) != current_admin["org_id"]:
        raise HTTPException(status_code=403, detail="Not authorized to delete this organization.")
        
    admin_id = organization["admin_user_id"]
    collection_name = organization["collection_name"]
    
    # 2. Handle deletion of the relevant collections
    db_client.drop_tenant_collection(collection_name)
    
    # 3. Delete Master records
    db_client.admin_collection.delete_one({"_id": admin_id})
    db_client.org_collection.delete_one({"_id": organization["_id"]})
    
    return 


## 3. Update Organization (Simplified to Admin/Password Update)
@router.put("/update", status_code=status.HTTP_200_OK)
async def update_organization(
    organization_name: str,
    new_password: Optional[str] = None,
    new_email: Optional[EmailStr] = None, # EmailStr is now recognized
    current_admin: dict = Depends(get_current_admin)
):
    organization = db_client.org_collection.find_one({"organization_name": organization_name})
    
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found.")
        
    if str(organization["_id"]) != current_admin["org_id"]:
        raise HTTPException(status_code=403, detail="Not authorized to update this organization.")
        
    update_data = {}
    if new_password:
        update_data["password_hash"] = hash_password(new_password)
        
    if new_email:
        # Validate unique email (excluding the current admin)
        if db_client.admin_collection.find_one({"email": new_email, "_id": {"$ne": ObjectId(current_admin["admin_id"])}}):
            raise HTTPException(status_code=400, detail="New email already in use by another organization.")
        update_data["email"] = new_email
        
    if update_data:
        db_client.admin_collection.update_one(
            {"_id": ObjectId(current_admin["admin_id"])},
            {"$set": update_data}
        )
        return {"message": "Organization admin details updated successfully."}
    
    return {"message": "No data provided for update."}
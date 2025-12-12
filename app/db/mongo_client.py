from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database # <--- FIX: Corrected import location
from app.core.config import settings

class MongoDB:
    def __init__(self):
        self.client: MongoClient = None
        self.db: Database = None
        self.org_collection: Collection = None
        self.admin_collection: Collection = None

    def connect(self):
        """Initializes the MongoDB connection and Master DB collections."""
        try:
            self.client = MongoClient(settings.MONGO_URL)
            self.db = self.client[settings.MASTER_DB_NAME]
            
            # Master Collections
            self.org_collection = self.db[settings.ORG_COLLECTION_NAME]
            self.admin_collection = self.db[settings.ADMIN_COLLECTION_NAME]
            
            # Ensure unique indexes on key fields
            self.org_collection.create_index("organization_name", unique=True)
            self.org_collection.create_index("collection_name", unique=True)
            self.admin_collection.create_index("email", unique=True)
            
            print("MongoDB connection successful.")
        except Exception as e:
            # Note: In a production app, this should raise an error to stop startup
            print(f"MongoDB connection failed: {e}") 
            
    def close(self):
        """Closes the MongoDB connection."""
        if self.client:
            self.client.close()
            print("MongoDB connection closed.")
            
    # --- Tenant Management Utilities ---
    
    def get_tenant_collection_name(self, org_name: str) -> str:
        """Generates the standardized tenant collection name."""
        return f"org_{org_name}"
        
    def create_tenant_collection(self, collection_name: str):
        """Dynamically creates a new collection for the organization."""
        self.db.create_collection(collection_name)
        print(f"Dynamically created collection: {collection_name}")
        
    def drop_tenant_collection(self, collection_name: str):
        """Handles deletion of the relevant organization collection."""
        self.db.drop_collection(collection_name)
        print(f"Dropped collection: {collection_name}")

db_client = MongoDB()
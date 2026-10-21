import pymongo
from typing import Optional
from app.core.config import settings
from app.core.logging import logger

class DatabaseManager:
    client: Optional[pymongo.MongoClient] = None
    db = None
    is_mock: bool = False

    def connect(self):
        try:
            logger.info(f"Attempting connection to MongoDB at {settings.MONGODB_URI}...")
            real_client = pymongo.MongoClient(
                settings.MONGODB_URI,
                serverSelectionTimeoutMS=2000
            )
            # Verify server is actually reachable
            real_client.server_info()
            self.client = real_client
            self.db = self.client[settings.MONGODB_DB_NAME]
            self.is_mock = False
            logger.info(f"Connected successfully to live MongoDB: {settings.MONGODB_DB_NAME}")
        except Exception as e:
            if settings.USE_MOCK_DB_IF_UNAVAILABLE:
                import mongomock
                logger.warning(f"Live MongoDB unreachable ({e}). Initializing embedded database engine for development...")
                self.client = mongomock.MongoClient()
                self.db = self.client[settings.MONGODB_DB_NAME]
                self.is_mock = True
                logger.info("Connected to embedded database engine (mongomock). All MongoDB operations active.")
            else:
                logger.error(f"Failed to connect to MongoDB: {e}")
                raise e

    def close(self):
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed.")

db_manager = DatabaseManager()

def get_database():
    if db_manager.db is None:
        db_manager.connect()
    return db_manager.db

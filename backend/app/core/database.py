import logging
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class Database:
    client: AsyncIOMotorClient = None
    db = None

db_instance = Database()

import certifi

async def connect_to_mongo():
    logger.info("Connecting to MongoDB...")
    try:
        # Create an async connection to the database URI from our config
        db_instance.client = AsyncIOMotorClient(settings.MONGODB_URI, tlsCAFile=certifi.where())
        # Select our specific database named "deep_research_db"
        db_instance.db = db_instance.client["deep_research_db"]
        logger.info("Successfully connected to MongoDB!")
    except Exception as e:
        logger.error(f"Error connecting to MongoDB: {e}")
        raise e

async def close_mongo_connection():
    logger.info("Closing MongoDB connection...")
    if db_instance.client:
        db_instance.client.close()
        logger.info("MongoDB connection closed.")

def get_database():
    """Helper function to get the DB instance anywhere in the app"""
    return db_instance.db

import ssl
import logging
import certifi
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class Database:
    client: AsyncIOMotorClient = None
    db = None

db_instance = Database()


def _make_ssl_context() -> ssl.SSLContext:
    """
    Build an SSLContext compatible with Python 3.13 + MongoDB Atlas.
    Python 3.13 tightened TLS defaults which causes TLSV1_ALERT_INTERNAL_ERROR
    against some Atlas clusters. We explicitly allow TLS 1.2+ and load the
    certifi CA bundle to keep certificate validation intact.
    """
    ctx = ssl.create_default_context(cafile=certifi.where())
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2
    ctx.check_hostname = True
    ctx.verify_mode = ssl.CERT_REQUIRED
    return ctx


async def connect_to_mongo():
    logger.info("Connecting to MongoDB...")
    try:
        db_instance.client = AsyncIOMotorClient(
            settings.MONGODB_URI,
            tls=True,
            tlsAllowInvalidCertificates=True,
            serverSelectionTimeoutMS=30000,
        )
        # Select our specific database named "deep_research_db"
        db_instance.db = db_instance.client["deep_research_db"]
        # Eagerly ping to surface connection errors at startup
        await db_instance.client.admin.command("ping")
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

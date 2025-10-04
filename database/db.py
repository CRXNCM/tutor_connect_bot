import os
from pymongo import MongoClient
from pymongo.database import Database
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class DatabaseManager:
    _instance = None
    _client: Optional[MongoClient] = None
    _db: Optional[Database] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance._initialize_db()
        return cls._instance

    def _initialize_db(self):
        """Initialize the MongoDB connection and database."""
        mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
        db_name = os.getenv('DB_NAME', 'tutor_connect')
        
        try:
            self._client = MongoClient(mongo_uri)
            self._db = self._client[db_name]
            # Test the connection
            self._client.admin.command('ping')
            print("Successfully connected to MongoDB!")
        except Exception as e:
            print(f"Error connecting to MongoDB: {e}")
            raise

    @property
    def db(self) -> Database:
        """Get the database instance."""
        if self._db is None:
            self._initialize_db()
        return self._db

    @property
    def tutors(self):
        """Get the tutors collection."""
        return self.db['tutors']

    def close_connection(self):
        """Close the MongoDB connection."""
        if self._client:
            self._client.close()
            self._client = None
            self._db = None

# Create a singleton instance
db_manager = DatabaseManager()

def get_db() -> Database:
    """Get the database instance."""
    return db_manager.db

def get_tutors_collection():
    """Get the tutors collection."""
    return get_db().tutors

def get_users_collection():
    """Get the users collection."""
    return get_db().users

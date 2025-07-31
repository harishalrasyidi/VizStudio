from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import Engine
from app.core.config import settings
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Membuat URL koneksi database
SQLALCHEMY_DATABASE_URL = (
    f"postgresql://{settings.DB_USER}:{settings.DB_PASSWORD}@"
    f"{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
)

# Membuat engine database dengan logging
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    echo=settings.DEBUG,  # Log SQL statements when in debug mode
    pool_pre_ping=True,   # Enable connection health checks
)

@event.listens_for(Engine, "connect")
def connect(dbapi_connection, connection_record):
    logger.info("Database connection established")

# Membuat session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class untuk model SQLAlchemy
Base = declarative_base()

def get_db():
    """
    Generator fungsi untuk mendapatkan database session.
    Memastikan session selalu ditutup setelah digunakan.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_db_connection():
    """
    Fungsi untuk mendapatkan koneksi database langsung.
    Berguna untuk eksekusi raw SQL query.
    """
    try:
        connection = engine.connect()
        logger.info("Database connection created successfully")
        return connection
    except Exception as e:
        logger.error(f"Error connecting to database: {str(e)}")
        raise
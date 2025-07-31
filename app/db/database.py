from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Membuat URL koneksi database
SQLALCHEMY_DATABASE_URL = (
    f"postgresql://{settings.DB_USER}:{settings.DB_PASSWORD}@"
    f"{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
)

# Membuat engine database
engine = create_engine(SQLALCHEMY_DATABASE_URL)

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
    return engine.connect()
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
import os
import sys

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("\n❌ FATAL: DATABASE_URL environment variable is not set!")
    print("   Please copy .env.example to .env and fill in your database URL.")
    print("   Example: DATABASE_URL=postgresql://user:pass@host/dbname?sslmode=require")
    sys.exit(1)

engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"sslmode": "require"},
    pool_pre_ping=True,
    pool_recycle=300
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

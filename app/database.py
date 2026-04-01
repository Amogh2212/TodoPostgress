from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(
    DATABASE_URL,
    echo=True,
<<<<<<< HEAD
    connect_args={"sslmode": "require"},
    pool_pre_ping=True,      # Checks connection before every task
    pool_recycle=300
=======
    connect_args={"sslmode": "require"}
>>>>>>> dfd5a49fb15b43d667bf82569aa7f651b770411b
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

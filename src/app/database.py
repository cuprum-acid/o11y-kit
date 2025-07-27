import os
import time
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

load_dotenv()

DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
DB_NAME = os.getenv("POSTGRES_DB")
DB_HOST = os.getenv("POSTGRES_HOST")
DB_PORT = os.getenv("POSTGRES_PORT")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


# Connection retry logic
def create_db_engine():
    retries = 5
    for i in range(retries):
        try:
            engine = create_engine(DATABASE_URL)
            with engine.connect() as conn:
                print("Database connection successful")
                return engine
        except OperationalError as e:
            if i < retries - 1:
                print(f"Database connection failed ({e}). Retrying in 2 seconds...")
                time.sleep(2)
                continue
            raise RuntimeError(
                f"Failed to connect to database after {retries} attempts: {e}"
            )


engine = create_db_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

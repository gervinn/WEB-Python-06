from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker


DATABASE_URL = "postgresql+psycopg2://user:password@localhost:5432/my_lab_db"

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  
    echo=False, 
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

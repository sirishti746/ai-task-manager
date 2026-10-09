from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

from app.config import settings

# pool_pre_ping checks a connection is alive before using it,
# which avoids errors after the database has been idle.
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)

# A factory that creates new sessions bound to our engine.
# autocommit=False: nothing is saved until we call db.commit().
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_db():
    """Give each request its own session, and close it when the request ends."""
    db = SessionLocal()
    try:
        yield db
    except SQLAlchemyError:
        # A database error escaped the route: undo the unfinished transaction,
        # then re-raise so the global handler in main.py returns the 500.
        db.rollback()
        raise
    finally:
        db.close()
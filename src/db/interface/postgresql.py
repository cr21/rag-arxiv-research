import logging
from contextlib import contextmanager
from typing import Generator, Optional

from pydantic import Field
from pydantic_settings import BaseSettings
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker
from src.db.interface.base import IBaseDatabase

logger = logging.getLogger(__name__)

class PostgresqlSettings(BaseSettings):
    """
    postgresql settings.
    """
    database_url: str = Field(default="postgresql://rag_user:rag_password@localhost:5432/rag_db"
    , description="The URL of the postgresql database.")
    echo_sql: bool = Field(default=False, description="Whether to echo the sql statements.")
    pool_size: int = Field(default=20, description="The number of connections to keep in the pool.")
    max_overflow: int = Field(default=0, description="The maximum number of connections to create beyond the pool size.")


    class Config:
        env_prefix = "POSTGRES_"


Base = declarative_base()


class PostgresqlDatabase(IBaseDatabase):
    """
    postgresql database.
    """
    def __init__(self, settings: PostgresqlSettings):
        self.settings = settings
        self.engine :Optional[Engine] = None
        self.session_factory :Optional[sessionmaker] = None

    def startup(self) -> None:
        """
        Startup the postgresql database.
        """
        try:    
            logger.info(f"""starting up postgresql database... at 
            {self.settings.database_url.split('@')[1] if '@' in self.settings.database_url else 'localhost'}""")

            self.engine = create_engine(self.settings.database_url,
                echo=self.settings.echo_sql,
                pool_size=self.settings.pool_size,
                max_overflow=self.settings.max_overflow,
                pool_pre_ping=True # verify connection before use
            )

            self.session_factory = sessionmaker(bind=self.engine, expire_on_commit=False)

            # Test the connection
            assert self.engine is not None
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                logger.info("Connection successful")
            
            # check with inspect for tables before creating
            insepector = inspect(self.engine)
            existing_tables = insepector.get_table_names()

            # create table if not exists idempotent operations
            Base.metadata.create_all(bind=self.engine)
            # check if new tables were created
            insepector = inspect(self.engine)
            new_tables = set(insepector.get_table_names()) - set(existing_tables)
            logger.info(f"Existing tables: {existing_tables}")
            logger.info(f"New tables: {new_tables}")
            if new_tables:
                logger.info(f"Created new tables: {new_tables}")
            else:
                logger.info("No new tables were created")

            logger.info("Postgresql database startup successful")
            assert self.engine is not None
            logger.info(f"Database : {self.engine.url.database}")
            logger.info(f"Total tables: {', '.join(new_tables) if new_tables else 'None'}")
            logger.info("Database connection established")
        except Exception as e:
            logger.error(f"Error starting up postgresql database: {e}")
            raise e
    
    def teardown(self) -> None:
        """
        Teardown the postgresql database.
        """
        if self.engine:
            self.engine.dispose()
            logger.info("Engine Disposed")

    @contextmanager
    def get_session(self)-> Generator[Session, None, None]:
        """
        Get a new session.
        """
        if not self.session_factory:
            raise RuntimeError("Session factory not initialized call startup first")
        if self.session_factory:
            session = self.session_factory()
            try:
                yield session
            except Exception as e:
                session.rollback()
                raise e
            finally:
                session.close()

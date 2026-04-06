from src.config import get_settings
from src.db.interface.postgresql import PostgresqlDatabase, PostgresqlSettings
from src.db.interface.base import IBaseDatabase

def make_database() -> IBaseDatabase:
    """
    Factory function for creating a new database instance.

    """
    settings = get_settings()
    config = PostgresqlSettings(
        database_url=settings.postgres_database_url,
        echo_sql=settings.postgres_echo_sql,
        pool_size=settings.postgres_pool_size,
        max_overflow=settings.postgres_max_overflow,
    )

    database = PostgresqlDatabase(config)
    database.startup()
    return database
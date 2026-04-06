from abc import ABC, abstractmethod
from re import A
from typing import Any, ContextManager, Dict, List, Optional, Union

from sqlalchemy.orm import Session


class IBaseDatabase(ABC):
    """
    Base interface for all databases.
    """
    @abstractmethod
    def get_session(self) -> ContextManager[Session]:
        """
        Get a new session.
        """
        pass
    
    @abstractmethod
    def teardown(self) -> None:
        """
        Teardown the database.
        """
        pass

    @abstractmethod
    def startup(self) -> None:
        """
        Startup the database.
        """
        pass


class IBaseRepository(ABC):
    """
    Base repository pattern for data access.
    """
    
    def __init__(self, session: Session):
        self.session = session

    @abstractmethod
    def create(self, data:Dict[str, Any]) -> Any:
        """
        Create a new record in the database.
        """
        pass
    
    @abstractmethod
    def get_by_id(self, record_id:Any) -> Optional[Any]:
        """
        Get a record from the database by its id.
        """
        pass
    
    
    
    @abstractmethod
    def update(self, record_id:Any, data:Dict[str, Any]) -> Any:
        """
        Update a record in the database by its id.
        """
        pass
    
    @abstractmethod
    def delete(self, record_id:Any) -> None:
        """
        Delete a record from the database by its id.
        """
        pass
    
    @abstractmethod
    def list(self, limit:int=10, offset:int = 0) -> List[Any]:
        """
        List all records from the database with pagination.
        """
        pass
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from .health import ServiceStatus

class ServiceStatus(BaseModel):
    """
    Individual service status.
    """
    status:str=Field(..., description="The status of the service.", example='ok')
    message:Optional[str]=Field(None, description="The message of the service.", example='Service is running')


class HealthResponse(BaseModel):
    """
    Health response.
    """
    status:str=Field(..., description="overall health status.", example='ok')
    version:str=Field(..., description="The version of the application.", example='0.1.0')
    environment:str=Field(..., description="The environment of the application.", example='development')
    service_name:str=Field(..., description="service identifier.", example='rag-api')
    services:Dict[str, ServiceStatus]=Field(..., description="The status of the  Individual services.")


    class Config:
        """
        Pydantic configurations


        """

        json_schema_extra = {
            "example": 
                {
                    "status": "ok",
                    "version": "0.1.0",
                    "environment": "development",
                    "service_name": "rag-api",
                    "services": {
                        "ollama": {"status": "ok", "message": "Service is running"}, 
                        "opensearch": {"status": "ok", "message": "Service is running"}, 
                        "pdf_parser": {"status": "ok", "message": "Service is running"}, 
                        "database": {"status": "ok", "message": "Service is running"}
                },
            
        }
        }
from fastapi import APIRouter
from sqlalchemy import text

from ..services.ollama import OllamaClient
from ..dependencies import DatabaseDep, SettingsDep
from ..schemas.health import HealthResponse, SearviceStatus

router = APIRouter()


@router.get("/ping",tags=["Health"])
async def ping():
    """
    simple ping command to test the connectivity test
    """
    return  {'status':'ok', 'message':'pong'}


@router.get("/health",
tags=["Health"],
response_model=HealthResponse,
summary="Health check endpoint",
description="Check the health and status of the API service including database connectivity.",
response_description="Service health information",
)
async def health_check(settings:SettingsDep, database:DatabaseDep):
    """
    Comprehensive health check endpoint for monitoring and load balancer probes.

    This endpoint provides information about the service health, version,
    environment, and checks connectivity to dependent services like database.

    Returns:
        HealthResponse: Contains service status, version, environment, and service checks

    Example:
    ```json
    {
        "status": "ok",
        "version": "0.1.0",
        "environment": "development",
        "service_name": "rag-api",
        "services": {"ollama": {"status": "ok", "message": "Service is running"},
         "opensearch": {"status": "ok", "message": "Service is running"},
          "pdf_parser": {"status": "ok", "message": "Service is running"}, 
          "database": {"status": "ok", "message": "Service is running"}}
    }
    ```
    """
    services = {

    }
    overall_status='ok'

    # Test database connectivity
    try:
        with database.get_session() as session:
            session.execute(text('SELECT 1'))
            services['database'] = {'status': 'ok', 'message': 'Database connectivity successful'}
    except Exception as e:
        overall_status='degraded'
        services['database'] = {'status': 'unhealthy', 'message': f'Database connectivity failed: {e}'}

    #Test ollama connectivity
    try:
        ollam_client = OllamaClient(settings)
        ollama_health = await ollam_client.health_check()
        services['ollama'] = ollama_health
        if ollama_health['status'] == 'ok':
            services['ollama'] = SearviceStatus(status=ollama_health['status'], message=ollama_health['message'])
        else:
            overall_status='degraded'
            services['ollama'] = SearviceStatus(status='unhealthy', message= f"Ollama connectivity failed: {ollama_health['message']}")
    except Exception as e:
        overall_status='degraded'
        services['ollama'] = SearviceStatus(status='unhealthy', message= f"Ollama connectivity failed: {e}")
    return HealthResponse(
        status=overall_status,
        version=settings.app_version,
        environment=settings.environment,
        service_name=settings.service_name,
        services=services
    )